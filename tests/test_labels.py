"""Actual font bounds, consistent state motion and standalone label-helper failures."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'recipes'))
import buttons
from label_atlas import compose_labels
from pixelart import PixelArtError, render
from pixelart.compat import pixels
from pixelart.metadata import PNG_KEY

FONT = ROOT / 'demos/pixel-ui/fonts/Silkscreen-Regular.ttf'
LABELS = ['START', 'LOOP', 'EXPORT MAP']


class LabelTests(unittest.TestCase):
    def setUp(self):
        self.files = buttons.make_files(width=88, content=[23, 4, 63, 10])

    def compose(self, **kwargs):
        options = dict(font_path=FONT, font_size=8, labels=LABELS, font_mode='monochrome',
                       metadata=self.files['layout.json'], state_offsets={'pressed': [0, 1]})
        options.update(kwargs)
        return compose_labels(self.files['asset.png'], self.files['context.json'], **options)

    def test_fit_reconstruction_and_shared_state_origin(self):
        before = self.files['asset.png'].tobytes()
        context = copy.deepcopy(self.files['context.json'])
        files = self.compose(state_colors={'disabled': '8997A5'})
        report = files['text-fit.json']
        self.assertEqual(report['consumer_size'], [264, 108])
        self.assertEqual(len(report['instances']), 18)
        self.assertEqual(report['labels'][-1]['font_bbox'], [0, 4, 58, 9])
        font = ImageFont.truetype(str(FONT), 8)
        expected = Image.new('RGBA', (264, 108))
        for row, cell in enumerate(self.files['layout.json']['atlas']['cells']):
            sx, sy, w, h = (cell[k] for k in ('x', 'y', 'w', 'h'))
            patch = self.files['asset.png'].crop((sx, sy, sx+w, sy+h))
            for col in range(3):
                expected.paste(patch, (col * w, row * h))
        # Reconstruct from the exported global origins, using the explicit font mode.
        layer = Image.new('RGBA', expected.size)
        draw = ImageDraw.Draw(layer)
        draw.fontmode = '1'
        for item in report['instances']:
            draw.text(item['origin'], item['label'], font=font, fill=tuple(bytes.fromhex(item['color'])))
            x, y, w, h = item['ink_rect']
            rx, ry, rw, rh = item['reserved_rect']
            self.assertGreaterEqual(x, rx + 2); self.assertGreaterEqual(y, ry + 2)
            self.assertLessEqual(x + w, rx + rw - 2); self.assertLessEqual(y + h, ry + rh - 2)
        self.assertEqual(Image.alpha_composite(expected, layer).tobytes(), files['consumer.png'].tobytes())
        normal = report['instances'][:3]
        for row in range(6):
            for col in range(3):
                item = report['instances'][row*3+col]
                self.assertEqual(item['origin'][0], normal[col]['origin'][0])
                self.assertEqual(item['origin'][1] - row * 18,
                                 normal[col]['origin'][1] + (row == 3))
        self.assertEqual(files['consumer-3x.png'].tobytes(),
                         files['consumer.png'].resize((792, 324), Image.Resampling.NEAREST).tobytes())
        self.assertEqual(before, self.files['asset.png'].tobytes())
        self.assertEqual(context, self.files['context.json'])

    def test_explicit_raster_modes_differ_and_binary_font_preserves_colors(self):
        mono = self.compose()['consumer.png']
        gray = self.compose(font_mode='grayscale')['consumer.png']
        self.assertNotEqual(mono.tobytes(), gray.tobytes())
        # Only native texture colors and the explicitly selected ink appear in mono mode.
        base_colors = set(pixels(self.files['asset.png']))
        self.assertTrue(set(pixels(mono)) <= base_colors | {(255, 255, 255, 255)})
        self.assertGreater(len(set(pixels(gray)) - base_colors - {(255, 255, 255, 255)}), 0)
        with self.assertRaisesRegex(PixelArtError, 'explicitly'):
            self.compose(font_mode='auto')

    def test_long_label_and_state_offset_fit_failures(self):
        self.files = buttons.make_files(width=64, content=[28, 4, 30, 10])
        with self.assertRaisesRegex(PixelArtError, 'EXPORT MAP.*58x5.*cannot fit'):
            self.compose(labels=['EXPORT MAP'])
        self.files = buttons.make_files(width=88, content=[23, 4, 63, 10])
        with self.assertRaisesRegex(PixelArtError, 'cannot fit'):
            self.compose(state_offsets={'pressed': [0, 2]})

    def test_context_and_digest_are_checked_before_composition(self):
        stale = copy.deepcopy(self.files['layout.json']); stale['rgba_sha256'] = '0' * 64
        with self.assertRaisesRegex(PixelArtError, 'digest'):
            self.compose(metadata=stale)
        legacy = {k: self.files['layout.json'][k] for k in ('size', 'mode', 'atlas')}
        with self.assertRaisesRegex(PixelArtError, 'content-bound'):
            self.compose(metadata=legacy)
        for change in ('missing', 'duplicate'):
            with self.subTest(change=change):
                previous = copy.deepcopy(self.files['context.json'])
                if change == 'missing': self.files['context.json']['regions'].pop()
                else:
                    extra = dict(self.files['context.json']['regions'][0], name='extra')
                    self.files['context.json']['regions'].append(extra)
                with self.assertRaisesRegex(PixelArtError, 'one.*region'):
                    self.compose()
                self.files['context.json'] = previous
        embedded = self.files['asset.png'].copy()
        embedded.info.pop('pixelart', None)
        embedded.info[PNG_KEY] = json.dumps(self.files['layout.json'])
        result = compose_labels(embedded, self.files['context.json'], font_path=FONT,
            font_size=8, labels=LABELS, font_mode='monochrome', state_offsets={'pressed': [0, 1]})
        self.assertEqual(result['consumer.png'].tobytes(), self.compose()['consumer.png'].tobytes())

    def test_invalid_font_labels_and_unknown_states(self):
        with self.assertRaises(OSError): self.compose(font_path=FONT.with_name('absent.ttf'))
        for labels in ([], [''], ['line\nbreak'], [' ']):
            with self.assertRaises(PixelArtError): self.compose(labels=labels)
        with self.assertRaisesRegex(PixelArtError, 'unknown state'):
            self.compose(state_offsets={'presed': [0, 1]})
        with self.assertRaisesRegex(PixelArtError, 'two integers'):
            self.compose(state_offsets={'pressed': [1]})

    def test_generic_atlas_uses_declared_regions_and_named_offsets(self):
        image = render(dict(kind='atlas', columns=1, cells=[dict(name=name,
            spec=dict(kind='draw', size=[50, 24], background='203040', operations=[]))
            for name in ('idle', 'active')]))
        context = dict(regions=[dict(name='caption-a', rect=[4, 3, 40, 16], role='reserved_text'),
                               dict(name='caption-b', rect=[5, 28, 40, 16], role='reserved_text')])
        files = compose_labels(image, context, font_path=FONT, font_size=8, labels=['OK'],
                               font_mode='monochrome', state_offsets={'active': [-1, 2]})
        a, b = files['text-fit.json']['instances']
        self.assertEqual(b['origin'][0] - a['origin'][0], -1)
        self.assertEqual(b['origin'][1] - a['origin'][1] - 24, 2)

    def test_cli_unrelated_directory_no_overwrite_and_input_alias(self):
        with tempfile.TemporaryDirectory(prefix='文字 space ') as directory:
            root = Path(directory)
            image = root / 'atlas.png'; self.files['asset.png'].save(image)
            context = root / 'context.json'; context.write_text(json.dumps(self.files['context.json']))
            meta = root / 'layout.json'; meta.write_text(json.dumps(self.files['layout.json']))
            args = [sys.executable, '-B', str(ROOT / 'recipes/label_atlas.py'), '--image', str(image),
                '--context', str(context), '--metadata', str(meta), '--font', str(FONT), '--font-size', '8',
                '--font-mode', 'monochrome', '--labels', *LABELS, '--state-offset', 'pressed', '0', '1']
            def run(out, extra=(), expected=0):
                result = subprocess.run([*args, '--out-dir', str(out), *extra], cwd=root,
                    capture_output=True, text=True, encoding='utf-8', timeout=30)
                self.assertEqual(result.returncode, expected, result.stderr)
                return result
            out = root / 'consumer'; run(out)
            before = (out / 'consumer.png').read_bytes()
            (out / 'text-fit.json').unlink()
            run(out, expected=2)
            self.assertEqual(before, (out / 'consumer.png').read_bytes())
            self.assertFalse((out / 'text-fit.json').exists())
            run(out, ['--force'])
            run(root / 'invalid', ['--state-offset', 'pressed', '0', '2'], expected=2)
            self.assertFalse((root / 'invalid').exists())
            image.rename(root / 'consumer.png')
            args[args.index(str(image))] = str(root / 'consumer.png')
            run(root, ['--force'], expected=2)
