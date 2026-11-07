"""Verify complete native atlas coverage, bounded output and safe delivery."""
from copy import deepcopy
from io import BytesIO
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image, ImageDraw
from pixelart import PixelArtError
from pixelart.context import _context
from pixelart.metadata import encode_png, layout_record, rgba_digest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'recipes'))
import review_atlas


def fixture(count=272, cell_size=(3, 2), columns=17, positions=None):
    positions = positions or [(i % columns, i // columns) for i in range(count)]
    columns = max(columns, max(x for x, _ in positions) + 1)
    rows = max(y for _, y in positions) + 1
    w, h = cell_size
    image = Image.new('RGBA', (w * columns, h * rows))
    draw = ImageDraw.Draw(image)
    cells = []
    for i, (x, y) in enumerate(positions):
        draw.rectangle((x*w, y*h, x*w+w-1, y*h+h-1), fill=(i % 256, (i*31) % 256, (i*7) % 256, (0, 1, 128, 255)[i % 4]))
        cells.append(dict(name=f'cell {i}', x=x*w, y=y*h, w=w, h=h))
    image.info['pixelart'] = dict(cell_size=[w, h], columns=columns, rows=rows, cells=cells)
    return image, layout_record(image)


def index_and_files(image, record, **kwargs):
    files = review_atlas.make_files(encode_png(image), record, **kwargs)
    return json.loads(files['index.json']), files


def verify_coverage(test, image, record, index, files):
    test.assertEqual([c['name'] for c in index['cells']], [c['name'] for c in record['atlas']['cells']])
    test.assertEqual(len(index['pages']), index['page_count'])
    test.assertEqual(index['coverage']['omitted_declared_pixels'], 0)
    all_ids = []
    for page in index['pages']:
        test.assertLessEqual(page['size'][0] * page['size'][1], review_atlas.MAX_PAGE_PIXELS)
        all_ids += page['blocks']
        with Image.open(BytesIO(files[page['file']])) as sheet:
            test.assertEqual(list(sheet.size), page['size'])
            for ident in page['blocks']:
                block = index['blocks'][ident - 1]
                x, y, w, h = block['source_rect']
                tile = image.crop((x, y, x+w, y+h)).convert('RGBA')
                for view, (_, rgba) in zip(block['views'], review_atlas.BACKGROUNDS):
                    sx, sy, sw, sh = view['sheet_rect']
                    test.assertEqual([sw, sh], [w, h])
                    expected = Image.alpha_composite(Image.new('RGBA', tile.size, rgba), tile).convert('RGB')
                    test.assertEqual(sheet.crop((sx, sy, sx+sw, sy+sh)).tobytes(), expected.tobytes())
    test.assertEqual(all_ids, list(range(1, len(index['blocks']) + 1)))
    for cell in index['cells']:
        x, y, w, h = cell['source_rect']
        mask = Image.new('L', (w, h))
        draw = ImageDraw.Draw(mask)
        area = 0
        for ident in cell['blocks']:
            block = index['blocks'][ident-1]
            bx, by, bw, bh = block['source_rect']
            test.assertTrue(x <= bx < bx+bw <= x+w and y <= by < by+bh <= y+h)
            local = (bx-x, by-y, bx-x+bw, by-y+bh)
            test.assertIsNone(mask.crop(local).getbbox())  # No duplicate pixels.
            draw.rectangle((local[0], local[1], local[2]-1, local[3]-1), fill=255)
            area += bw*bh
        test.assertEqual(mask.histogram()[255], w*h)
        test.assertEqual(area, w*h)


class AtlasReviewTests(unittest.TestCase):
    def cli(self, source, output, *options):
        env = {k: v for k, v in os.environ.items() if k not in ('PYTHONPATH', 'PIXELART_PORTABLE_OUTPUT')}
        return subprocess.run([sys.executable, '-B', str(ROOT/'recipes/review_atlas.py'), '--image', str(source),
                               '--out-dir', str(output), *map(str, options)], capture_output=True,
                              encoding='utf-8', timeout=30, env=env, cwd=source.parent)

    def test_256_257_272_cells_cover_exactly_on_both_backgrounds(self):
        for count in (256, 257, 272):
            with self.subTest(count=count):
                image, record = fixture(count)
                raw = image.tobytes()
                saved = deepcopy(record)
                index, files = index_and_files(image, record)
                verify_coverage(self, image, record, index, files)
                self.assertEqual(image.tobytes(), raw)
                self.assertEqual(record, saved)
                self.assertEqual(len(files), index['page_count'] + 1)

    def test_sparse_layout_long_unicode_and_whitespace_names_keep_exact_order(self):
        image, record = fixture(3, positions=[(0, 0), (16, 15), (3, 7)])
        names = [' ' * 170, '右下角图标', 'unique-' + 'z' * 400]
        for cell, name in zip(record['atlas']['cells'], names): cell['name'] = name
        index, files = index_and_files(image, record, blocks_per_page=2)
        verify_coverage(self, image, record, index, files)
        self.assertEqual([c['name'] for c in index['cells']], names)
        self.assertIn('unnamed grid positions are excluded', index['coverage']['scope'])

    def test_large_single_cell_is_fully_tiled_across_pages(self):
        image, record = fixture(1, cell_size=(260, 257), columns=1)
        for n, point in enumerate(((0, 0), (127, 127), (128, 128), (259, 0), (0, 256), (259, 256))):
            image.putpixel(point, (200, n*30, 70, 255))
        record['rgba_sha256'] = rgba_digest(image)
        index, files = index_and_files(image, record, blocks_per_page=4)
        self.assertEqual(index['page_count'], 3)
        self.assertEqual(index['cells'][0]['pages'], [1, 2, 3])
        self.assertEqual(len(index['blocks']), 9)
        verify_coverage(self, image, record, index, files)

    def test_maximum_cell_layout_plans_without_expanding_default_context_limit(self):
        image, record = fixture(4096, cell_size=(1, 1), columns=64)
        plan = review_atlas._plan(image, record, 64)
        self.assertEqual(plan['page_count'], 64)
        self.assertEqual(len(plan['cells']), 4096)
        with self.assertRaisesRegex(PixelArtError, 'at most 256'):
            _context({'atlas': record['atlas']}, image.size)

    def test_full_layout_validation_checks_last_and_unselected_entries(self):
        image, record = fixture()
        for change in (dict(x=9999), dict(name='cell 0'), dict(w=1)):
            bad = deepcopy(record)
            bad['atlas']['cells'][-1].update(change)
            with self.subTest(change=change), self.assertRaises(PixelArtError):
                index_and_files(image, bad)

    def test_missing_hash_empty_layout_stale_and_conflicting_records_fail(self):
        image, record = fixture(2)
        legacy = deepcopy(record); legacy.pop('rgba_sha256')
        empty = deepcopy(record); empty['atlas']['cells'] = []
        no_atlas = deepcopy(record); no_atlas.pop('atlas')
        stale = deepcopy(record); stale['rgba_sha256'] = '0' * 64
        for candidate in (None, legacy, empty, no_atlas, stale):
            with self.subTest(candidate=candidate), self.assertRaises(PixelArtError):
                index_and_files(image, candidate)
        embedded = deepcopy(record); embedded['atlas']['cells'][0]['name'] = 'different'
        with self.assertRaisesRegex(PixelArtError, 'conflicts'):
            review_atlas.make_files(encode_png(image, embedded), record)

    def test_embedded_and_sidecar_produce_same_visual_pages(self):
        image, record = fixture(17)
        sidecar = review_atlas.make_files(encode_png(image), record)
        embedded = review_atlas.make_files(encode_png(image, record))
        self.assertEqual(sidecar['page-0001.png'], embedded['page-0001.png'])
        self.assertEqual(json.loads(embedded['index.json'])['provenance']['content_bound_atlas_sources'], ['embedded'])

    def test_repeated_delivery_is_byte_identical_and_has_no_host_paths(self):
        image, record = fixture(17)
        first = review_atlas.make_files(encode_png(image), record)
        self.assertEqual(first, review_atlas.make_files(encode_png(image), record))
        text = first['index.json'].decode('utf-8')
        self.assertNotIn(str(ROOT), text)
        self.assertNotIn('C:\\', text)

    def test_budget_failures_happen_before_page_rendering(self):
        image, record = fixture(65)
        with patch.object(review_atlas, '_page') as render:
            for value in (0, 65, True, 1.5):
                with self.subTest(value=value), self.assertRaises(PixelArtError):
                    index_and_files(image, record, blocks_per_page=value)
            with self.assertRaisesRegex(PixelArtError, 'more than 64 pages'):
                index_and_files(image, record, blocks_per_page=1)
            with patch.object(review_atlas, 'MAX_TOTAL_PIXELS', 10), self.assertRaises(PixelArtError):
                index_and_files(image, record)
            with patch.object(review_atlas, 'MAX_TILES', 1), self.assertRaises(PixelArtError):
                index_and_files(image, record)
            with patch.object(review_atlas, 'MAX_PAGE_PIXELS', 1), self.assertRaises(PixelArtError):
                index_and_files(image, record)
            with patch.object(review_atlas, 'MAX_CELLS', 2), self.assertRaises(PixelArtError):
                index_and_files(image, record)
            render.assert_not_called()
        with patch.object(review_atlas, 'MAX_OUTPUT_BYTES', 1), self.assertRaises(PixelArtError):
            index_and_files(image, record)

    def test_png_formats_and_metadata_budgets_are_rejected(self):
        image, record = fixture(1)
        with self.assertRaises(PixelArtError): review_atlas.make_files(b'no png', record)
        sixteen = Image.new('I;16', (2, 2))
        with self.assertRaisesRegex(PixelArtError, 'bit depth'):
            review_atlas.make_files(encode_png(sixteen), record)
        stream = BytesIO()
        Image.new('RGBA', (3, 3)).save(stream, format='PNG', save_all=True,
                                     append_images=[Image.new('RGBA', (3, 3), 'red')], duration=10)
        with self.assertRaisesRegex(PixelArtError, 'multiframe'):
            review_atlas.make_files(stream.getvalue(), record)
        with patch.object(review_atlas, 'MAX_METADATA_BYTES', 1), self.assertRaises(PixelArtError):
            index_and_files(image, record)
        with patch.object(review_atlas, 'MAX_PNG_BYTES', 1), self.assertRaises(PixelArtError):
            index_and_files(image, record)

    def test_palette_transparency_and_one_bit_modes_are_preserved(self):
        image, _ = fixture(2, cell_size=(2, 1), columns=2)
        for mode in ('P', '1', 'RGB'):
            candidate = image.convert(mode)
            candidate.info['pixelart'] = image.info['pixelart']
            if mode == 'P': candidate.info['transparency'] = bytes([0, 128] + [255]*254)
            record = layout_record(candidate)
            index, files = index_and_files(candidate, record)
            verify_coverage(self, candidate, record, index, files)

    def test_cli_new_directory_portable_and_existing_outputs_are_safe(self):
        image, record = fixture(17)
        with tempfile.TemporaryDirectory(prefix='atlas review 空间 ') as directory:
            root = Path(directory); source = root/'source.png'; meta = root/'layout.json'
            source.write_bytes(encode_png(image)); meta.write_text(json.dumps(record), encoding='utf-8')
            before = source.read_bytes(); out = root/'review'
            result = self.cli(source, out, '--metadata', meta, '--portable-output')
            self.assertEqual(result.returncode, 0, result.stderr)
            index = json.loads((out/'index.json').read_text(encoding='utf-8'))
            self.assertEqual(index['coverage']['declared_cells'], 17)
            existing = {p.name: p.read_bytes() for p in out.iterdir()}
            result = self.cli(source, out, '--metadata', meta)
            self.assertEqual(result.returncode, 2)
            result = self.cli(source, out, '--metadata', meta, '--force')
            self.assertEqual(result.returncode, 2)
            self.assertEqual(existing, {p.name: p.read_bytes() for p in out.iterdir()})
            self.assertEqual(source.read_bytes(), before)

    def test_cli_invalid_input_publishes_no_directory(self):
        image, record = fixture()
        record['atlas']['cells'][-1]['x'] = -1
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root/'source.png'; meta = root/'layout.json'
            source.write_bytes(encode_png(image)); meta.write_text(json.dumps(record), encoding='utf-8')
            out = root/'invalid'
            result = self.cli(source, out, '--metadata', meta)
            self.assertEqual(result.returncode, 2)
            self.assertFalse(out.exists())
            meta.write_text('{"version":1,"version":1}', encoding='utf-8')
            self.assertEqual(self.cli(source, out, '--metadata', meta).returncode, 2)
            self.assertFalse(out.exists())

    def test_ordinary_publish_failure_removes_only_our_empty_directory(self):
        image, record = fixture(1)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root/'source.png'; out = root/'candidate'
            source.write_bytes(encode_png(image, record))
            args = ['review_atlas.py', '--image', str(source), '--out-dir', str(out)]
            with patch.object(sys, 'argv', args), patch.object(review_atlas, 'publish', side_effect=OSError('injected')):
                with self.assertRaisesRegex(OSError, 'injected'): review_atlas.main()
            self.assertFalse(out.exists())
            def competing_writer(*args, **kwargs):
                (out/'other.txt').write_bytes(b'keep me')
                raise OSError('injected')
            with patch.object(sys, 'argv', args), patch.object(review_atlas, 'publish', side_effect=competing_writer):
                with self.assertRaisesRegex(PixelArtError, 'incomplete directory retained'): review_atlas.main()
            self.assertEqual((out/'other.txt').read_bytes(), b'keep me')


if __name__ == '__main__': unittest.main()
