"""Exact tile repeats, diagnostic previews and portable project delivery."""
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image
from pixelart import PixelArtError
from pixelart.assembly import assemble, load_project
from pixelart.metadata import rgba_digest
from pixelart.output import encoded

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'recipes'))
import tile_preview


def png(image, **options):
    output = BytesIO()
    image.save(output, format='PNG', **options)
    return output.getvalue()


def tile():
    # Non-square input includes invisible RGB and partial alpha.
    image = Image.new('RGBA', (3, 2))
    image.putdata([(10, 20, 30, 0), (40, 50, 60, 128), (70, 80, 90, 255),
                   (100, 110, 120, 1), (130, 140, 150, 254), (160, 170, 180, 0)])
    return image


class TilePreviewTests(unittest.TestCase):
    def run_cli(self, source, output, *options, env=None):
        task_env = dict(os.environ)
        task_env.pop('PIXELART_PORTABLE_OUTPUT', None)
        if env:
            task_env.update(env)
        return subprocess.run([sys.executable, '-B', str(ROOT / 'recipes/tile_preview.py'),
            '--image', str(source), '--out-dir', str(output), *options],
            cwd=source.parent, env=task_env, capture_output=True, text=True,
            encoding='utf-8', timeout=30)

    def test_axes_preserve_every_rgba_copy_and_source_bytes(self):
        image = tile()
        original = png(image)
        for axis, repeats in [('x', (3, 1)), ('y', (1, 3)), ('xy', (3, 3))]:
            with self.subTest(axis=axis):
                files = tile_preview.make_files(original, axis)
                repeated = files['repeated.png']
                self.assertEqual(repeated.size, (3 * repeats[0], 2 * repeats[1]))
                for row in range(repeats[1]):
                    for column in range(repeats[0]):
                        self.assertEqual(repeated.crop((column * 3, row * 2,
                            column * 3 + 3, row * 2 + 2)).tobytes(), image.tobytes())
                with Image.open(BytesIO(encoded(repeated))) as decoded:
                    self.assertEqual(decoded.tobytes(), repeated.tobytes())
                self.assertEqual(files['source.png'], original)
                self.assertEqual(files['report.json']['input']['sha256'], hashlib.sha256(original).hexdigest())
                self.assertEqual(files['report.json']['input']['rgba_sha256'], rgba_digest(image))
                self.assertEqual(image.tobytes(), tile().tobytes())

    def test_report_placements_and_seam_coordinates(self):
        for axis, repeats in [('x', (3, 1)), ('y', (1, 3)), ('xy', (3, 3))]:
            with self.subTest(axis=axis):
                files = tile_preview.make_files(png(tile()), axis)
                report = files['report.json']
                nx, ny = repeats
                self.assertEqual(report['axis'], axis)
                self.assertEqual(report['repeats'], list(repeats))
                self.assertEqual([p['at'] for p in files['project.json']['parts']],
                                 [[x * 3, y * 2] for y in range(ny) for x in range(nx)])
                expected = ([dict(axis='x', at=x, span=[0, ny * 2]) for x in (3, 6)] if nx > 1 else [])
                expected += ([dict(axis='y', at=y, span=[0, nx * 3]) for y in (2, 4)] if ny > 1 else [])
                self.assertEqual(report['seam_lines'], expected)
                self.assertEqual(report['assembly']['seam_count'], (nx - 1) * ny + (ny - 1) * nx)
                self.assertEqual(report['assembly']['uncovered_pixels'], 0)
                self.assertEqual(report['assembly']['rgba_sha256'], rgba_digest(files['repeated.png']))

    def test_preview_is_nearest_and_background_is_diagnostic(self):
        image = Image.new('RGB', (2, 1))
        image.putdata([(12, 34, 56), (210, 190, 170)])
        files = tile_preview.make_files(png(image), 'x', scale=3)
        for y in range(3):
            for x in range(18):
                self.assertEqual(files['preview.png'].getpixel((x, y)),
                                 (*image.getpixel(((x // 3) % 2, 0)), 255))
        transparent = png(tile())
        black = tile_preview.make_files(transparent, 'y', background='000000')
        white = tile_preview.make_files(transparent, 'y', background='FFFFFF')
        self.assertNotEqual(black['preview.png'].tobytes(), white['preview.png'].tobytes())
        self.assertEqual(black['repeated.png'].tobytes(), white['repeated.png'].tobytes())

    def test_palette_transparency_and_one_bit_png(self):
        palette = Image.new('P', (2, 1))
        palette.putpalette([10, 20, 30, 40, 50, 60] + [0] * 762)
        palette.putdata([0, 1])
        for image, options in [(palette, dict(transparency=bytes([0, 128]))),
                               (Image.new('1', (1, 2), 1), {})]:
            original = png(image, **options)
            with Image.open(BytesIO(original)) as decoded:
                expected = decoded.convert('RGBA').tobytes()
            files = tile_preview.make_files(original, 'xy')
            self.assertEqual(files['repeated.png'].crop((0, 0, image.width, image.height)).tobytes(), expected)

    def test_invalid_axis_and_scale(self):
        for axis in ('', 'yx', 'z', None):
            with self.subTest(axis=axis), self.assertRaises(PixelArtError):
                tile_preview.make_files(png(tile()), axis)
        for scale in (0, -1, True, 1.5):
            with self.subTest(scale=scale), self.assertRaises(PixelArtError):
                tile_preview.make_files(png(tile()), 'x', scale)

    def test_rejects_non_png_high_bit_depth_and_animation(self):
        gif = BytesIO()
        Image.new('RGB', (2, 2)).save(gif, format='GIF')
        animated = png(Image.new('RGBA', (2, 2), 'red'), save_all=True,
                       append_images=[Image.new('RGBA', (2, 2), 'blue')], duration=100, loop=0)
        for source in (b'', gif.getvalue(), png(Image.new('I;16', (2, 2))), animated):
            with self.subTest(header=source[:16]), self.assertRaises(PixelArtError):
                tile_preview.make_files(source, 'xy')

    def test_size_limits_precede_assembly_and_preview_allocation(self):
        # Actual PNGs; these are ordinary size-limit checks, not huge decodes.
        for size, axis, scale, message in [((8193, 1), 'y', 1, 'source'),
                ((3000, 1), 'x', 1, 'repeat'), ((1500, 1500), 'xy', 1, 'repeat'),
                ((700, 1), 'x', 4, 'use --scale 3'), ((400, 400), 'xy', 4, 'use --scale 3')]:
            with self.subTest(size=size, scale=scale), patch.object(tile_preview, 'assemble') as assembly:
                with self.assertRaisesRegex(PixelArtError, message):
                    tile_preview.make_files(png(Image.new('RGBA', size)), axis, scale)
                assembly.assert_not_called()

    def test_preview_error_suggests_the_largest_working_integer_scale(self):
        for size, axis, requested, expected in [((512, 512), 'xy', 4, 2),
                ((700, 1), 'x', 4, 3), ((400, 400), 'xy', 4, 3),
                ((8192, 1), 'y', 2, 1)]:
            with self.subTest(size=size, axis=axis):
                source = png(Image.new('RGBA', size))
                with self.assertRaises(PixelArtError) as error:
                    tile_preview.make_files(source, axis, requested)
                suggested = int(re.search(r'use --scale (\d+)', str(error.exception)).group(1))
                self.assertEqual(suggested, expected)
                recovered = tile_preview.make_files(source, axis, suggested)
                self.assertEqual(recovered['preview.png'].size,
                    tuple(n * suggested for n in recovered['repeated.png'].size))
                with self.assertRaises(PixelArtError):
                    tile_preview.make_files(source, axis, suggested + 1)

    def test_bounded_seam_sheet_reports_omitted_closeups(self):
        files = tile_preview.make_files(png(Image.new('RGBA', (1, 1100))), 'x', scale=1)
        report = files['report.json']['assembly']
        self.assertEqual(len(report['seam_views']), 32)
        self.assertEqual(report['omitted_seam_views'], 4)

    def test_cli_outputs_migrate_and_reassemble_in_unicode_space_path(self):
        with tempfile.TemporaryDirectory(prefix='重复 贴图 ') as directory:
            root = Path(directory)
            source = root / '原图.png'
            source.write_bytes(png(tile()))
            output = root / 'candidate'
            result = self.run_cli(source, output, '--axis', 'xy')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(set(p.name for p in output.iterdir()), set(tile_preview.OUTPUT_NAMES))
            moved = root / '中文 空格' / '迁移'
            shutil.move(str(output), moved)
            source.unlink()
            project, sources, _ = load_project(moved / 'project.json')
            image, _ = assemble(project, sources)
            with Image.open(moved / 'repeated.png') as expected:
                self.assertEqual(image.tobytes(), expected.tobytes())
            report = json.loads((moved / 'report.json').read_text(encoding='utf-8'))
            self.assertEqual(report['assembly']['rgba_sha256'], rgba_digest(image))

    def test_cli_requires_axis_and_preserves_outputs_until_force(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'tile.png'
            source.write_bytes(png(tile()))
            output = root / 'candidate'
            self.assertEqual(self.run_cli(source, output).returncode, 2)
            self.assertFalse(output.exists())
            self.assertEqual(self.run_cli(source, output, '--axis', 'x').returncode, 0)
            before = {p.name: p.read_bytes() for p in output.iterdir()}
            refused = self.run_cli(source, output, '--axis', 'y')
            self.assertEqual(refused.returncode, 2, refused.stderr)
            self.assertEqual({p.name: p.read_bytes() for p in output.iterdir()}, before)
            rebuilt = self.run_cli(source, output, '--axis', 'y', '--force')
            self.assertEqual(rebuilt.returncode, 0, rebuilt.stderr)
            with Image.open(output / 'repeated.png') as image:
                self.assertEqual(image.size, (3, 6))

    def test_cli_does_not_overwrite_source_even_with_force(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source.png'
            original = png(tile())
            source.write_bytes(original)
            result = self.run_cli(source, root, '--axis', 'x', '--force')
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertEqual(source.read_bytes(), original)
            self.assertEqual(list(root.iterdir()), [source])

    def test_cli_invalid_preview_creates_no_outputs_and_explicit_portable_wins(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'tile.png'
            source.write_bytes(png(tile()))
            output = root / 'candidate'
            invalid = self.run_cli(source, output, '--axis', 'x', '--background', 'invalid')
            self.assertEqual(invalid.returncode, 2, invalid.stderr)
            self.assertFalse(output.exists())
            invalid_env = dict(PIXELART_PORTABLE_OUTPUT='invalid')
            self.assertEqual(self.run_cli(source, output, '--axis', 'x', env=invalid_env).returncode, 2)
            self.assertFalse(output.exists())
            for flag in ('--portable-output', '--no-portable-output'):
                result = self.run_cli(source, root / flag[2:], '--axis', 'x', flag, env=invalid_env)
                self.assertEqual(result.returncode, 0, result.stderr)
