"""Flat single-asset delivery and its guarded source boundaries."""

from io import BytesIO
from pathlib import Path
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))


def png_bytes(image):
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    return buffer.getvalue()


class SingleAssetTests(unittest.TestCase):
    def run_cli(self, source, output, *options):
        env = dict(os.environ)
        env.pop('PIXELART_PORTABLE_OUTPUT', None)
        return subprocess.run(
            [
                sys.executable,
                '-B',
                str(ROOT / 'recipes/single_asset.py'),
                '--source',
                str(source),
                '--out-dir',
                str(output),
                *map(str, options),
            ],
            cwd=source.parent,
            env=env,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=30,
        )

    def test_png_delivery_rebuilds_after_relocation_and_zip_matches_directory(self):
        with tempfile.TemporaryDirectory(prefix='single asset ') as directory:
            root = Path(directory)
            source = root / 'input.png'
            image = Image.new('RGBA', (3, 2))
            image.putdata(
                [
                    (8, 9, 10, 0),
                    (40, 50, 60, 128),
                    (70, 80, 90, 255),
                    (100, 110, 120, 1),
                    (130, 140, 150, 254),
                    (160, 170, 180, 0),
                ]
            )
            original = png_bytes(image)
            source.write_bytes(original)
            output = root / 'delivery'
            archive = root / 'delivery.zip'
            result = self.run_cli(source, output, '--scale', 3, '--pack-zip', archive)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(source.read_bytes(), original)
            self.assertEqual(
                set(path.name for path in output.iterdir()),
                {'asset.png', 'asset.json', 'native.png', 'nearest.png', 'REBUILD.md'},
            )
            with Image.open(output / 'asset.png') as delivered:
                self.assertEqual(delivered.convert('RGBA').tobytes(), image.tobytes())
            with Image.open(output / 'nearest.png') as nearest:
                self.assertEqual(nearest.size, (9, 6))
                self.assertEqual(nearest.getpixel((1, 1))[3], 255)
                self.assertEqual(nearest.getpixel((7, 1)), image.getpixel((2, 0)))
            moved = root / 'moved elsewhere'
            moved.mkdir()
            shutil.move(output, moved / 'delivery')
            with zipfile.ZipFile(archive) as bundle:
                self.assertIsNone(bundle.testzip())
                self.assertEqual(
                    set(bundle.namelist()),
                    {
                        'asset.png',
                        'asset.json',
                        'native.png',
                        'nearest.png',
                        'REBUILD.md',
                    },
                )
                for name in bundle.namelist():
                    self.assertEqual(
                        bundle.read(name), (moved / 'delivery' / name).read_bytes()
                    )
            script = ROOT / 'skill/deterministic-pixel-art/scripts/pixel_art.py'
            rebuilt = moved / 'delivery' / 'rebuilt.png'
            command = subprocess.run(
                [
                    sys.executable,
                    '-B',
                    str(script),
                    'render',
                    '--spec',
                    'asset.json',
                    '--out',
                    str(rebuilt),
                ],
                cwd=moved / 'delivery',
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=30,
            )
            self.assertEqual(command.returncode, 0, command.stderr)
            with Image.open(rebuilt) as actual:
                self.assertEqual(actual.convert('RGBA').tobytes(), image.tobytes())

    def test_json_input_and_existing_outputs_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source.json'
            spec = {
                'version': 1,
                'kind': 'grid',
                'size': [2, 1],
                'palette': {'.': None, 'X': '123456'},
                'rows': ['X.'],
            }
            source.write_text(json.dumps(spec), encoding='utf-8')
            output = root / 'delivery'
            self.assertEqual(self.run_cli(source, output).returncode, 0)
            before = {path.name: path.read_bytes() for path in output.iterdir()}
            refused = self.run_cli(source, output)
            self.assertEqual(refused.returncode, 2)
            self.assertEqual(
                {path.name: path.read_bytes() for path in output.iterdir()}, before
            )
            self.assertEqual(self.run_cli(source, output, '--force').returncode, 0)

    def test_alias_and_named_atlas_are_rejected_without_touching_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source.png'
            original = png_bytes(Image.new('RGBA', (2, 1), (1, 2, 3, 255)))
            source.write_bytes(original)
            alias = self.run_cli(
                source, root / 'delivery', '--pack-zip', source, '--force'
            )
            self.assertEqual(alias.returncode, 2)
            self.assertEqual(source.read_bytes(), original)
            metadata = {
                'version': 1,
                'size': [2, 1],
                'mode': 'RGBA',
                'atlas': {
                    'columns': 2,
                    'rows': 1,
                    'cells': [
                        {'name': 'idle', 'at': [0, 0], 'size': [1, 1]},
                        {'name': 'run', 'at': [1, 0], 'size': [1, 1]},
                    ],
                },
                'rgba_sha256': None,
            }
            from pixelart.metadata import rgba_digest

            with Image.open(BytesIO(original)) as image:
                metadata['rgba_sha256'] = rgba_digest(image)
            sidecar = root / 'layout.json'
            sidecar.write_text(json.dumps(metadata), encoding='utf-8')
            rejected = self.run_cli(source, root / 'named', '--metadata', sidecar)
            self.assertEqual(rejected.returncode, 2)
            self.assertIn('named atlas', rejected.stderr)
            self.assertFalse((root / 'named').exists())

    def test_zip_output_alias_and_reserved_output_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source.png'
            original = png_bytes(Image.new('RGBA', (2, 1), (10, 20, 30, 255)))
            source.write_bytes(original)
            output = root / 'delivery'
            output.mkdir()
            locked = output / '.asset.png.pixelart.lock'
            locked.write_text('another writer', encoding='utf-8')
            failed = self.run_cli(source, output)
            self.assertEqual(failed.returncode, 2)
            self.assertEqual(source.read_bytes(), original)
            self.assertEqual(list(output.iterdir()), [locked])
            locked.unlink()
            self.assertEqual(self.run_cli(source, output).returncode, 0)
            collision = self.run_cli(
                source, root / 'other', '--pack-zip', output / 'asset.png'
            )
            self.assertEqual(collision.returncode, 2)

    def test_json_source_errors_are_structured_and_publish_nothing(self):
        grid = {'kind': 'grid', 'rows': ['X'], 'palette': {'X': '123456'}}
        atlas = {
            'kind': 'atlas',
            'columns': 1,
            'cells': [{'name': 'transfer', 'spec': grid}],
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'input.json'
            cases = (
                ('CANVAS 1 1\nBG FF0000', (), 'JSON object'),
                ([], (), 'JSON object'),
                (None, (), 'JSON object'),
                (atlas, (), 'named atlas'),
                ({'kind': 'preview', 'source': grid}, (), 'underlying source'),
                ({'kind': 'preview', 'source': atlas}, (), 'underlying source'),
                (grid, ('--metadata', root / 'missing.json'), 'only applies to PNG'),
            )
            for index, (data, options, diagnostic) in enumerate(cases):
                with self.subTest(data=data, options=options):
                    output = root / f'delivery-{index}'
                    source.write_text(json.dumps(data), encoding='utf-8')
                    result = self.run_cli(source, output, *options)
                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertIn(diagnostic, json.loads(result.stderr)['error'])
                    self.assertFalse(output.exists())

    def test_grid_and_draw_accept_optional_legacy_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source.json'
            for spec in (
                {'kind': 'grid', 'rows': ['X'], 'palette': {'X': '123456'}},
                {
                    'kind': 'draw',
                    'size': [1, 1],
                    'operations': [
                        {
                            'op': 'rect',
                            'x': 0,
                            'y': 0,
                            'w': 1,
                            'h': 1,
                            'color': '123456',
                        }
                    ],
                },
            ):
                with self.subTest(kind=spec['kind']):
                    source.write_text(json.dumps(spec), encoding='utf-8-sig')
                    output = root / spec['kind']
                    result = self.run_cli(source, output)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(
                        json.loads((output / 'asset.json').read_bytes()), spec
                    )
                    with Image.open(output / 'asset.png') as image:
                        self.assertEqual(image.getpixel((0, 0)), (18, 52, 86, 255))

    def test_png_header_limits_precede_pillow_open(self):
        from pixelart.core import MAX_SIDE, PixelArtError

        sys.path.insert(0, str(ROOT / 'recipes'))
        try:
            from single_asset import make_files
        finally:
            sys.path.pop(0)

        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'source.png'
            header = png_bytes(Image.new('RGBA', (1, 1)))[:33]
            for width, depth, diagnostic in (
                (MAX_SIDE + 1, 8, 'size: limit'),
                (1, 16, 'bit depth'),
                (MAX_SIDE // 4 + 1, 8, 'use --scale 3'),
            ):
                with self.subTest(width=width, depth=depth):
                    source.write_bytes(
                        header[:16] + struct.pack('>IIB', width, 1, depth) + header[25:]
                    )
                    with patch('single_asset.Image.open') as open_image:
                        with self.assertRaisesRegex(PixelArtError, diagnostic):
                            make_files(source)
                        open_image.assert_not_called()

    def test_repeated_zip_is_identical_with_fixed_entry_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source.png'
            source.write_bytes(png_bytes(Image.new('RGBA', (2, 1), 'red')))
            archives = [root / f'{index}.zip' for index in range(2)]
            for archive in archives:
                result = self.run_cli(
                    source, archive.with_suffix(''), '--pack-zip', archive
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                with zipfile.ZipFile(archive) as bundle:
                    for info in bundle.infolist():
                        self.assertEqual(info.date_time, (1980, 1, 1, 0, 0, 0))
                        self.assertEqual(info.compress_type, zipfile.ZIP_DEFLATED)
            self.assertEqual(archives[0].read_bytes(), archives[1].read_bytes())


if __name__ == '__main__':
    unittest.main()
