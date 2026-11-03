"""Producer-to-reader atlas compatibility and content-bound label requirements."""
import copy
from io import BytesIO
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from PIL import Image

from pixelart import PixelArtError, image_to_spec, inspect_image, render
from pixelart.metadata import encode_png, layout_record, merge_layout
from pixelart.review import review

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'recipes'))
import buttons
from label_atlas import compose_labels


def atlas_spec(count, last_name=None):
    return dict(kind='atlas', columns=min(16, count), cells=[dict(
        name=last_name if i == count - 1 and last_name is not None else f'cell-{i}',
        spec=dict(kind='grid', rows=['ab', 'cd'], palette={
            'a': f'{i % 256:02x}112200', 'b': '33445580', 'c': '667788FF', 'd': '99AABB01'}))
        for i in range(count)])


class LabelLayoutContractTests(unittest.TestCase):
    def setUp(self):
        self.files = buttons.make_files(width=88, content=[23, 4, 63, 10])
        self.image = Image.frombytes('RGBA', self.files['asset.png'].size,
                                     self.files['asset.png'].tobytes())
        self.options = dict(font_path=ROOT / 'demos/pixel-ui/fonts/Silkscreen-Regular.ttf',
                            font_size=8, font_mode='monochrome', labels=['START'])

    def compose(self, image=None, metadata=None, context=None):
        return compose_labels(self.image if image is None else image,
                              self.files['context.json'] if context is None else context,
                              metadata=metadata, **self.options)

    def test_context_only_is_not_a_content_bound_layout(self):
        context = copy.deepcopy(self.files['context.json'])
        context['atlas'] = self.files['layout.json']['atlas']
        with self.assertRaisesRegex(PixelArtError, 'content-bound'):
            self.compose(context=context)
        # Ordinary inspection continues to accept an explicit Context layout.
        merged, provenance = merge_layout(self.image, context)
        self.assertEqual(merged['atlas'], context['atlas'])
        self.assertEqual(provenance['sources'], ['context'])
        self.assertEqual(provenance['unverified_records'], [])
        self.assertEqual(len(inspect_image(self.image, context)['cells']), 6)

    def test_pixel_digest_without_layout_cannot_bind_context(self):
        context = copy.deepcopy(self.files['context.json'])
        context['atlas'] = self.files['layout.json']['atlas']
        for missing in ('absent', 'null'):
            record = copy.deepcopy(self.files['layout.json'])
            record.pop('atlas')
            if missing == 'null': record['atlas'] = None
            with self.subTest(missing=missing), self.assertRaisesRegex(PixelArtError, 'content-bound'):
                self.compose(metadata=record, context=context)

    def test_valid_sidecar_embedded_and_memory_layouts_preserve_pixels(self):
        sidecar = self.compose(metadata=self.files['layout.json'])
        with Image.open(BytesIO(encode_png(self.image, self.files['layout.json']))) as image:
            embedded = self.compose(image=image)
        memory = self.compose(image=self.files['asset.png'])
        for result in (embedded, memory):
            self.assertEqual(result['consumer.png'].tobytes(), sidecar['consumer.png'].tobytes())
        self.assertEqual(sidecar['text-fit.json']['metadata']['content_bound_atlas_sources'], ['sidecar'])
        self.assertEqual(embedded['text-fit.json']['metadata']['content_bound_atlas_sources'], ['embedded'])
        self.assertEqual(memory['text-fit.json']['metadata']['content_bound_atlas_sources'], ['memory'])

    def test_stale_conflicting_and_legacy_records_still_fail(self):
        for problem in ('stale', 'conflict', 'legacy'):
            record = copy.deepcopy(self.files['layout.json'])
            if problem == 'stale': record['rgba_sha256'] = '0' * 64
            if problem == 'conflict': record['atlas']['cells'][0]['name'] = 'renamed'
            if problem == 'legacy': record.pop('rgba_sha256')
            with self.subTest(problem=problem), self.assertRaises(PixelArtError):
                self.compose(image=self.files['asset.png'], metadata=record)

    def test_cli_missing_bound_layout_publishes_nothing(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.image.save(root / 'atlas.png')
            context = copy.deepcopy(self.files['context.json'])
            context['atlas'] = self.files['layout.json']['atlas']
            (root / 'context.json').write_text(json.dumps(context), encoding='utf-8')
            result = subprocess.run([sys.executable, '-B', str(ROOT / 'recipes/label_atlas.py'),
                '--image', str(root / 'atlas.png'), '--context', str(root / 'context.json'),
                '--font', str(self.options['font_path']), '--font-size', '8', '--font-mode', 'monochrome',
                '--labels', 'START', '--out-dir', str(root / 'consumer')],
                capture_output=True, text=True, encoding='utf-8', timeout=30)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn('content-bound', result.stderr)
            self.assertFalse((root / 'consumer').exists())


class AtlasReaderContractTests(unittest.TestCase):
    def test_256_cell_control_whole_import_and_inspection(self):
        image = render(atlas_spec(256))
        self.assertEqual(len(inspect_image(image)['cells']), 256)
        self.assertEqual(render(image_to_spec(image, metadata=layout_record(image))).tobytes(), image.tobytes())

    def test_large_atlas_selected_cell_with_all_metadata_sources(self):
        for count in (257, 272):
            image = render(atlas_spec(count))
            record = layout_record(image)
            target = f'cell-{count - 1}'
            x = (count - 1) % 16 * 2; y = (count - 1) // 16 * 2
            with Image.open(BytesIO(encode_png(image, record))) as embedded:
                plain = Image.frombytes('RGBA', image.size, image.tobytes())
                for source, metadata in ((image, None), (embedded, None), (plain, record)):
                    with self.subTest(count=count, metadata=metadata is not None, memory=source is image):
                        result = inspect_image(source, cell=target, metadata=metadata, grid=True)
                        self.assertEqual(result['facts']['rect'], [x, y, 2, 2])
                        self.assertEqual(result['cells'], [])
                        selected = image_to_spec(source, cell=target, metadata=metadata)
                        self.assertEqual(render(selected).tobytes(), image.crop((x, y, x+2, y+2)).tobytes())

    def test_whole_large_atlas_keeps_explicit_resource_boundary(self):
        image = render(atlas_spec(272))
        for consume in (lambda: inspect_image(image), lambda: review(image),
                        lambda: image_to_spec(image, metadata=layout_record(image))):
            with self.subTest(consume=consume), self.assertRaisesRegex(PixelArtError, '256.*--cell'):
                consume()

    def test_atlas_names_match_existing_renderer_without_changing_other_names(self):
        for name in ('x' * 160, '长' * 161, ' '):
            image = render(atlas_spec(1, name))
            with self.subTest(name=name):
                self.assertEqual(inspect_image(image)['cells'][0]['name'], name)
                self.assertEqual(render(image_to_spec(image, cell=name)).tobytes(), image.crop((0, 0, 2, 2)).tobytes())
                self.assertEqual(image_to_spec(image, metadata=layout_record(image))['cells'][0]['name'], name)
                self.assertEqual(review(image)[0]['facts']['cells'][0]['name'], name)
        with self.assertRaisesRegex(PixelArtError, '160'):
            inspect_image(Image.new('RGBA', (2, 2)), {'regions': [
                dict(name='x' * 161, rect=[0, 0, 1, 1], role='content')]})

    def test_selection_validates_entire_layout_and_digest(self):
        image = render(atlas_spec(272))
        record = layout_record(image)
        plain = Image.frombytes('RGBA', image.size, image.tobytes())
        for problem in ('duplicate-name', 'duplicate-position', 'unaligned', 'out-of-bounds',
                        'empty-name', 'wrong-grid', 'stale'):
            broken = copy.deepcopy(record)
            cell = broken['atlas']['cells'][-1]
            if problem == 'duplicate-name': cell['name'] = 'cell-0'
            if problem == 'duplicate-position': cell.update(x=0, y=0)
            if problem == 'unaligned': cell['x'] -= 1
            if problem == 'out-of-bounds': cell['x'] = image.width
            if problem == 'empty-name': cell['name'] = ''
            if problem == 'wrong-grid': broken['atlas']['rows'] += 1
            if problem == 'stale': broken['rgba_sha256'] = '0' * 64
            for consume in (inspect_image, image_to_spec):
                with self.subTest(problem=problem, consume=consume), self.assertRaises(PixelArtError):
                    consume(plain, metadata=broken, cell='cell-0')
        for consume in (inspect_image, image_to_spec):
            with self.assertRaisesRegex(PixelArtError, 'unknown name'):
                consume(image, cell='missing')

    def test_cli_generated_large_long_named_cell_exact_roundtrip(self):
        with tempfile.TemporaryDirectory(prefix='图集 中文 space ') as folder:
            root = Path(folder); name = 'last-' + 'x' * 161
            spec = atlas_spec(272, name)
            (root / 'atlas.json').write_text(json.dumps(spec), encoding='utf-8')
            def run(*args):
                return subprocess.run([sys.executable, '-B', str(ROOT / 'src/pixel_art.py'), *args],
                    cwd=root, capture_output=True, text=True, encoding='utf-8', timeout=30)
            for args in (
                ('render', '--spec', 'atlas.json', '--out', 'atlas.png', '--metadata', 'layout.json', '--embed-metadata'),
                ('inspect', '--image', 'atlas.png', '--cell', name, '--grid', '--out', 'facts.json'),
                ('import', '--image', 'atlas.png', '--metadata', 'layout.json', '--cell', name, '--out', 'cell.json'),
                ('render', '--spec', 'cell.json', '--out', 'cell.png')):
                result = run(*args)
                self.assertEqual(result.returncode, 0, result.stderr)
            facts = json.loads((root / 'facts.json').read_text(encoding='utf-8'))
            self.assertEqual(facts['facts']['rect'], [30, 32, 2, 2])
            with Image.open(root / 'atlas.png') as whole, Image.open(root / 'cell.png') as cell:
                self.assertEqual(cell.tobytes(), whole.crop((30, 32, 32, 34)).tobytes())
            result = run('inspect', '--image', 'atlas.png', '--out', 'rejected.json')
            self.assertEqual(result.returncode, 2)
            self.assertIn('--cell', result.stderr)
            self.assertFalse((root / 'rejected.json').exists())
