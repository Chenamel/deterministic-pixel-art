"""Lossless edit inputs and readable layout records at publication boundaries."""

from io import BytesIO
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

from PIL import Image

from pixelart import PixelArtError, inspect_image, recolor_image, render, verify_edit
from pixelart.ingest import image_to_spec
from pixelart.metadata import encode_png, layout_record, merge_layout, PNG_KEY

ROOT = Path(__file__).resolve().parents[1]
LAYOUT_LIMIT = 262144


def named_pixel(name):
    return {
        'kind': 'atlas',
        'columns': 1,
        'cells': [
            {
                'name': name,
                'spec': {
                    'kind': 'grid',
                    'palette': {'a': '112233'},
                    'rows': ['a'],
                },
            }
        ],
    }


def serialized(record):
    return json.dumps(
        record, ensure_ascii=True, sort_keys=True, separators=(',', ':')
    ).encode('utf-8')


def layout_at_size(size):
    overhead = len(serialized(layout_record(render(named_pixel('x'))))) - 1
    name = 'x' * (size - overhead)
    image = render(named_pixel(name))
    record = layout_record(image)
    if len(serialized(record)) != size:
        raise AssertionError('Fixture does not reach the requested serialized size')
    return image, record, name


def animated_png(mode='RGBA'):
    first = Image.new(mode, (2, 1), 0)
    second = Image.new(mode, (2, 1), 255)
    stream = BytesIO()
    first.save(
        stream,
        format='PNG',
        save_all=True,
        append_images=[second],
        duration=[100, 100],
        loop=0,
    )
    return stream.getvalue()


def rgb16_png():
    def chunk(kind, data):
        checksum = zlib.crc32(kind + data) & 0xFFFFFFFF
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', checksum)

    header = struct.pack('>IIBBBBB', 2, 1, 16, 2, 0, 0, 0)
    row = b'\0' + struct.pack('>6H', 1000, 1000, 1000, 2000, 2000, 2000)
    return (
        b'\x89PNG\r\n\x1a\n'
        + chunk(b'IHDR', header)
        + chunk(b'IDAT', zlib.compress(row))
        + chunk(b'IEND', b'')
    )


def run_cli(root, *arguments):
    return subprocess.run(
        [sys.executable, '-B', str(ROOT / 'src/pixel_art.py'), *arguments],
        cwd=root,
        capture_output=True,
        text=True,
        encoding='utf-8',
        timeout=30,
    )


class LayoutEncodingTests(unittest.TestCase):
    def test_exact_limit_roundtrips_and_one_byte_over_is_rejected(self):
        image, record, name = layout_at_size(LAYOUT_LIMIT)
        with Image.open(BytesIO(encode_png(image, record))) as reopened:
            self.assertEqual(len(reopened.info[PNG_KEY].encode('utf-8')), LAYOUT_LIMIT)
            self.assertEqual(
                inspect_image(reopened, cell=name)['facts']['rect'], [0, 0, 1, 1]
            )
            self.assertEqual(
                render(image_to_spec(reopened, cell=name)).tobytes(), image.tobytes()
            )

        image, record, _ = layout_at_size(LAYOUT_LIMIT + 1)
        with self.assertRaisesRegex(PixelArtError, 'embedded metadata exceeds 256 KiB'):
            encode_png(image, record)

    def test_unicode_budget_counts_the_actual_escaped_record(self):
        image = render(named_pixel('地' * 45000))
        record = layout_record(image)
        unescaped = json.dumps(record, ensure_ascii=False).encode('utf-8')
        self.assertLess(len(unescaped), LAYOUT_LIMIT)
        self.assertGreater(len(serialized(record)), LAYOUT_LIMIT)
        with self.assertRaisesRegex(PixelArtError, '256 KiB'):
            encode_png(image, record)

    def test_large_sidecar_and_memory_layouts_remain_usable(self):
        image, record, name = layout_at_size(LAYOUT_LIMIT + 1)
        plain = Image.frombytes('RGBA', image.size, image.tobytes())
        for source, sidecar in ((image, None), (plain, record)):
            with self.subTest(sidecar=sidecar is not None):
                context, _ = merge_layout(source, metadata=sidecar)
                self.assertEqual(context['atlas']['cells'][0]['name'], name)
                selected = image_to_spec(source, metadata=sidecar, cell=name)
                self.assertEqual(render(selected).tobytes(), image.tobytes())

    def test_rejected_render_and_recolor_preserve_all_outputs_and_inputs(self):
        image, record, name = layout_at_size(LAYOUT_LIMIT + 1)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'source.json').write_text(
                json.dumps(named_pixel(name)), encoding='utf-8'
            )
            image.save(root / 'source.png')
            (root / 'layout.json').write_text(json.dumps(record), encoding='utf-8')
            inputs = {path.name: path.read_bytes() for path in root.iterdir()}
            outputs = [
                'candidate.png',
                'candidate-layout.json',
                'report.json',
                'preview.png',
            ]
            commands = (
                (
                    'render',
                    '--spec',
                    'source.json',
                    '--out',
                    outputs[0],
                    '--metadata',
                    outputs[1],
                    '--preview',
                    outputs[3],
                    '--embed-metadata',
                ),
                (
                    'recolor',
                    '--image',
                    'source.png',
                    '--metadata',
                    'layout.json',
                    '--map',
                    '112233',
                    '445566',
                    '--allow-region',
                    '0',
                    '0',
                    '1',
                    '1',
                    '--out',
                    outputs[0],
                    '--metadata-out',
                    outputs[1],
                    '--report',
                    outputs[2],
                ),
            )
            for overwrite in (False, True):
                if overwrite:
                    for filename in outputs:
                        (root / filename).write_bytes(b'accepted output')
                for command in commands:
                    with self.subTest(command=command[0], overwrite=overwrite):
                        result = run_cli(
                            root, *command, *(['--force'] if overwrite else [])
                        )
                        self.assertEqual(result.returncode, 2, result.stderr)
                        self.assertIn(
                            'embedded metadata exceeds 256 KiB', result.stderr
                        )
                        for filename in outputs:
                            path = root / filename
                            if overwrite:
                                self.assertEqual(path.read_bytes(), b'accepted output')
                            else:
                                self.assertFalse(path.exists())
                        for filename, data in inputs.items():
                            self.assertEqual((root / filename).read_bytes(), data)
                self.assertEqual(
                    {path.name for path in root.iterdir()},
                    set(inputs) | (set(outputs) if overwrite else set()),
                )


class EditInputTests(unittest.TestCase):
    def test_api_rejects_unsupported_modes_in_each_comparison_input(self):
        supported = Image.new('RGBA', (2, 1))
        for mode in ('I;16', 'I', 'F', 'CMYK', 'RGBa'):
            unsupported = Image.new(mode, (2, 1))
            for candidate, baseline in (
                (unsupported, supported),
                (supported, unsupported),
            ):
                with self.subTest(mode=mode, candidate=candidate.mode):
                    with self.assertRaisesRegex(PixelArtError, 'decoded 8-bit'):
                        verify_edit(candidate, baseline, regions=[[0, 0, 1, 1]])

    def test_api_rejects_animated_images_and_masks_without_mutating_inputs(self):
        source = Image.new('RGBA', (2, 1), '#112233')
        before = source.tobytes()
        with Image.open(BytesIO(animated_png())) as animation:
            self.assertEqual(animation.n_frames, 2)
            for candidate, baseline in ((animation, source), (source, animation)):
                with self.assertRaisesRegex(PixelArtError, 'animated/multiframe'):
                    verify_edit(candidate, baseline, regions=[[0, 0, 1, 1]])
        for mode in ('RGBA', 'L'):
            with (
                self.subTest(mode=mode),
                Image.open(BytesIO(animated_png(mode))) as mask,
            ):
                self.assertEqual(mask.n_frames, 2)
                with self.assertRaisesRegex(PixelArtError, 'mask: animated/multiframe'):
                    verify_edit(source, source, mask=mask)
                with self.assertRaisesRegex(PixelArtError, 'mask: animated/multiframe'):
                    recolor_image(source, {'112233': '445566'}, mask=mask)
                self.assertEqual(mask.tell(), 0)
        self.assertEqual(source.tobytes(), before)

    def test_supported_modes_and_mask_channels_still_detect_outside_changes(self):
        for mode in ('1', 'L', 'LA', 'P', 'RGB', 'RGBA'):
            source = Image.new(mode, (2, 1))
            candidate = source.copy()
            if mode == 'P':
                source.putpalette([0, 0, 0, 255, 255, 255] + [0] * 762)
                candidate.putpalette(source.getpalette())
            candidate.paste(
                Image.new(mode, (1, 1), 1 if mode == 'P' else 'white'), (1, 0)
            )
            for mask_mode in ('1', 'L', 'LA', 'RGBA'):
                mask = Image.new(mask_mode, (2, 1))
                mask.paste(Image.new(mask_mode, (1, 1), 'white'), (0, 0))
                with self.subTest(mode=mode, mask=mask_mode):
                    report = verify_edit(candidate, source, mask=mask)
                    self.assertFalse(report['valid'])
                    self.assertEqual(report['changed_outside'], 1)
                    self.assertEqual(report['allowed_pixels'], 1)

    def test_cli_rejects_unsupported_inputs_before_creating_or_replacing_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            Image.new('RGBA', (2, 1)).save(root / 'plain.png')
            Image.new('L', (2, 1)).save(root / 'mask.png')
            Image.new('I;16', (2, 1), 1000).save(root / 'gray16.png')
            Image.new('RGB', (2, 1)).save(root / 'photo.jpg')
            (root / 'rgb16.png').write_bytes(rgb16_png())
            (root / 'animated.png').write_bytes(animated_png())
            (root / 'animated-mask.png').write_bytes(animated_png('L'))
            with Image.open(root / 'rgb16.png') as decoded:
                self.assertEqual(decoded.mode, 'RGB')
                decoded.load()
            inputs = {path.name: path.read_bytes() for path in root.iterdir()}
            for flag in ('--image', '--compare', '--allow-mask'):
                for filename, error in (
                    ('gray16.png', 'bit depth above 8'),
                    ('rgb16.png', 'bit depth above 8'),
                    (
                        'animated-mask.png'
                        if flag == '--allow-mask'
                        else 'animated.png',
                        'animated/multiframe',
                    ),
                    ('photo.jpg', 'expected a PNG'),
                ):
                    arguments = {
                        '--image': 'plain.png',
                        '--compare': 'plain.png',
                        '--allow-mask': 'mask.png',
                    }
                    arguments[flag] = filename
                    command = ['verify']
                    for key, value in arguments.items():
                        command.extend([key, value])
                    command.extend(['--out', 'report.json'])
                    for overwrite in (False, True):
                        report = root / 'report.json'
                        if overwrite:
                            report.write_bytes(b'accepted report')
                        with self.subTest(
                            flag=flag, file=filename, overwrite=overwrite
                        ):
                            result = run_cli(
                                root, *command, *(['--force'] if overwrite else [])
                            )
                            self.assertEqual(result.returncode, 2, result.stderr)
                            self.assertIn(error, result.stderr)
                            if overwrite:
                                self.assertEqual(
                                    report.read_bytes(), b'accepted report'
                                )
                                report.unlink()
                            else:
                                self.assertFalse(report.exists())
            for filename, data in inputs.items():
                self.assertEqual((root / filename).read_bytes(), data)
            self.assertEqual({path.name for path in root.iterdir()}, set(inputs))


if __name__ == '__main__':
    unittest.main()
