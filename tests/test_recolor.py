"""Explicit-scope color variants; assertions concern RGBA, not art quality."""
from io import BytesIO
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from PIL import Image

from pixelart import PixelArtError, recolor_image, render, verify_edit
from pixelart.compat import pixels
from pixelart.metadata import PNG_KEY, encode_png, layout_record, rgba_digest


CLI = Path(__file__).resolve().parents[1] / 'src/pixel_art.py'


class RecolorTests(unittest.TestCase):
    def test_simultaneous_mapping_uses_original_pixels_and_leaves_input_unchanged(self):
        source = Image.new('RGB', (4, 1))
        source.putdata([(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 0, 0)])
        original = source.tobytes()
        mappings = [('FF0000', '00FF00'), ('00FF00', '0000FF')]
        candidate, report = recolor_image(source, mappings, regions=[[0, 0, 3, 1]])
        self.assertEqual(candidate.mode, 'RGBA')
        self.assertEqual(list(pixels(candidate)), [
            (0, 255, 0, 255), (0, 0, 255, 255),
            (0, 0, 255, 255), (255, 0, 0, 255)])
        self.assertEqual(source.tobytes(), original)
        self.assertEqual(source.mode, 'RGB')
        self.assertEqual(mappings, [('FF0000', '00FF00'), ('00FF00', '0000FF')])
        self.assertEqual(report['matched_pixels'], 2)
        self.assertEqual(report['changed_rgba_pixels'], 2)
        self.assertFalse(report['no_op'])

    def test_hollow_mask_and_rectangles_are_a_union_without_filling_the_hole(self):
        source = Image.new('RGBA', (7, 5), (12, 34, 56, 255))
        allowed = {(x, y) for y in range(5) for x in range(5)
                   if x in (0, 4) or y in (0, 4)}
        mask = Image.new('L', source.size)
        for point in allowed:
            mask.putpixel(point, 1)
        allowed.update({(6, 1), (6, 2)})
        candidate, report = recolor_image(
            source, {'0C2238': 'FEDCBA80'}, regions=[[6, 1, 1, 2]], mask=mask)
        for y in range(5):
            for x in range(7):
                expected = (254, 220, 186, 128) if (x, y) in allowed else (12, 34, 56, 255)
                self.assertEqual(candidate.getpixel((x, y)), expected, (x, y))
        self.assertEqual(report['allowed_pixels'], 18)
        self.assertEqual(report['changed_rgba_pixels'], 18)
        self.assertEqual(verify_edit(candidate, source, regions=[[6, 1, 1, 2]], mask=mask)['changed_outside'], 0)

    def test_full_rgba_matching_preserves_hidden_rgb_and_other_alpha_values(self):
        source = Image.new('RGBA', (5, 1))
        original = [(1, 2, 3, 0), (1, 2, 3, 128), (1, 2, 3, 255),
                    (0, 0, 0, 0), (1, 2, 3, 0)]
        source.putdata(original)
        candidate, report = recolor_image(source, [
            ('01020300', '0A141E00'), ('01020380', 'FFFFFF7F'), (None, '11223300')
        ], regions=[[0, 0, 4, 1]])
        self.assertEqual(list(pixels(candidate)), [
            (10, 20, 30, 0), (255, 255, 255, 127), (1, 2, 3, 255),
            (17, 34, 51, 0), (1, 2, 3, 0)])
        self.assertEqual(list(pixels(source)), original)
        self.assertEqual(report['changed_rgba_pixels'], 3)

    def test_unmatched_and_identity_mappings_report_no_op_honestly(self):
        source = Image.new('RGBA', (2, 1), (17, 34, 51, 255))
        candidate, report = recolor_image(
            source, [('112233', '112233FF'), ('FFFFFF', '000000')], regions=[[0, 0, 1, 1]])
        self.assertEqual(candidate.tobytes(), source.tobytes())
        self.assertIsNot(candidate, source)
        self.assertTrue(report['no_op'])
        self.assertEqual(report['matched_pixels'], 1)
        self.assertEqual(report['changed_rgba_pixels'], 0)
        self.assertEqual(report['unmatched_sources'], ['FFFFFFFF'])
        self.assertEqual(report['mappings'][0]['matched_pixels'], 1)
        self.assertEqual(report['mappings'][0]['changed_rgba_pixels'], 0)

    def test_mask_modes_use_alpha_or_intensity_without_mutating_the_mask(self):
        source = Image.new('RGBA', (2, 1), (255, 255, 255, 255))
        for mode, values in [('1', [0, 1]), ('L', [0, 1]),
                             ('LA', [(255, 0), (0, 1)]),
                             ('RGBA', [(255, 255, 255, 0), (0, 0, 0, 1)])]:
            with self.subTest(mode=mode):
                mask = Image.new(mode, source.size)
                mask.putdata(values)
                before = mask.tobytes()
                candidate, report = recolor_image(source, {'FFFFFF': '010203'}, mask=mask)
                self.assertEqual(candidate.getpixel((0, 0)), (255, 255, 255, 255))
                self.assertEqual(candidate.getpixel((1, 0)), (1, 2, 3, 255))
                self.assertEqual(report['changed_rgba_pixels'], 1)
                self.assertEqual(mask.tobytes(), before)

    def test_palette_image_is_decoded_and_old_metadata_is_not_copied(self):
        source = Image.new('P', (2, 1))
        source.putpalette([1, 2, 3, 4, 5, 6] + [0] * 762)
        source.putdata([0, 1])
        source.info['transparency'] = 0
        source.info['pixelart:layout'] = 'old record must not be copied'
        candidate, _ = recolor_image(source, {'01020300': '10203040'}, regions=[[0, 0, 2, 1]])
        self.assertEqual(list(pixels(candidate)), [(16, 32, 48, 64), (4, 5, 6, 255)])
        self.assertNotIn('pixelart:layout', candidate.info)
        self.assertEqual(source.info['pixelart:layout'], 'old record must not be copied')

    def test_invalid_mapping_or_scope_is_rejected_before_input_changes(self):
        source = Image.new('RGBA', (2, 2), (10, 20, 30, 255))
        original = source.tobytes()
        bad_mappings = [None, {}, [], 'FFFFFF', [('FFFFFF',)],
                        [('FFFFFF', '000000'), ('ffffffff', '111111')],
                        [('not-a-color', '000000')], [('FFFFFF', [256, 0, 0])]]
        for mapping in bad_mappings:
            with self.subTest(mapping=mapping), self.assertRaises(PixelArtError):
                recolor_image(source, mapping, regions=[[0, 0, 2, 2]])
        for options in [{}, {'regions': []}, {'regions': 'all'},
                        {'regions': [[0, 0, 3, 1]]},
                        {'mask': Image.new('RGB', source.size)},
                        {'mask': Image.new('L', (1, 1))}]:
            with self.subTest(options=options), self.assertRaises(PixelArtError):
                recolor_image(source, {'0A141E': 'FFFFFF'}, **options)
        self.assertEqual(source.tobytes(), original)

    def test_multiframe_and_high_depth_images_are_not_silently_flattened(self):
        with self.assertRaises(PixelArtError):
            recolor_image(Image.new('I;16', (1, 1)), {'000000': 'FFFFFF'}, regions=[[0, 0, 1, 1]])
        buffer = BytesIO()
        Image.new('RGBA', (1, 1), 'red').save(
            buffer, format='PNG', save_all=True, append_images=[Image.new('RGBA', (1, 1), 'blue')])
        buffer.seek(0)
        with Image.open(buffer) as animated:
            self.assertEqual(animated.n_frames, 2)
            with self.assertRaises(PixelArtError):
                recolor_image(animated, {'FF0000': 'FFFFFF'}, regions=[[0, 0, 1, 1]])


class RecolorCliTests(unittest.TestCase):
    def run_cli(self, root, *arguments, env=None):
        return subprocess.run([sys.executable, '-B', str(CLI), *map(str, arguments)],
                              cwd=root, env=env, capture_output=True, text=True,
                              encoding='utf-8', timeout=30)

    def test_sparse_atlas_keeps_names_positions_and_fresh_verified_metadata(self):
        with tempfile.TemporaryDirectory(prefix='换色 中文 space ') as directory:
            root = Path(directory)
            source = render(dict(kind='atlas', columns=3, rows=2, assembly='copy', cells=[
                dict(name='other', at=[0, 0], spec=dict(kind='grid', rows=['aa', 'aa'], palette={'a': '11223380'})),
                dict(name='target', at=[4, 2], spec=dict(kind='grid', rows=['aa', 'aa'], palette={'a': '11223380'}))]))
            layout = layout_record(source)
            (root/'source.png').write_bytes(encode_png(source, layout))
            (root/'layout.json').write_text(json.dumps(layout), encoding='utf-8')
            original = (root/'source.png').read_bytes()
            result = self.run_cli(root, 'recolor', '--image', 'source.png', '--metadata', 'layout.json',
                                  '--map', '11223380', 'F5C26B80', '--allow-region', 4, 2, 2, 2,
                                  '--out', 'candidate.png', '--report', 'report.json',
                                  '--metadata-out', 'candidate-layout.json')
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report, json.loads((root/'report.json').read_text(encoding='utf-8')))
            self.assertEqual(report['verification']['changed_outside'], 0)
            self.assertEqual(report['changed_rgba_pixels'], 4)
            with Image.open(root/'candidate.png') as image:
                self.assertEqual(image.getpixel((0, 0)), (17, 34, 51, 128))
                self.assertEqual(image.getpixel((4, 2)), (245, 194, 107, 128))
                fresh = json.loads(image.info[PNG_KEY])
                self.assertEqual(fresh['atlas'], layout['atlas'])
                self.assertEqual(fresh['rgba_sha256'], rgba_digest(image))
                self.assertNotEqual(fresh['rgba_sha256'], layout['rgba_sha256'])
                expected = image.tobytes()
            self.assertEqual(fresh, json.loads((root/'candidate-layout.json').read_text(encoding='utf-8')))
            imported = self.run_cli(root, 'import', '--image', 'candidate.png', '--metadata',
                                    'candidate-layout.json', '--out', 'editable.json')
            self.assertEqual(imported.returncode, 0, imported.stderr)
            spec = json.loads((root/'editable.json').read_text(encoding='utf-8'))
            self.assertEqual([cell['name'] for cell in spec['cells']], ['other', 'target'])
            self.assertEqual(render(spec).tobytes(), expected)
            self.assertEqual((root/'source.png').read_bytes(), original)

    def test_cli_union_and_simultaneous_swaps_use_actual_png_masks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = Image.new('RGBA', (3, 1))
            image.putdata([(255, 0, 0, 255), (0, 255, 0, 255), (255, 0, 0, 255)])
            image.save(root/'source.png')
            mask = Image.new('L', image.size)
            mask.putpixel((1, 0), 1)
            mask.save(root/'mask.png')
            result = self.run_cli(root, 'recolor', '--image', 'source.png', '--map', 'FF0000', '00FF00',
                                  '--map', '00FF00', 'FF0000', '--allow-region', 0, 0, 1, 1,
                                  '--allow-mask', 'mask.png', '--out', 'candidate.png')
            self.assertEqual(result.returncode, 0, result.stderr)
            with Image.open(root/'candidate.png') as candidate:
                self.assertEqual(list(pixels(candidate)), [(0, 255, 0, 255), (255, 0, 0, 255), (255, 0, 0, 255)])

    def test_noop_and_palette_input_have_explicit_rgba_reports(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = Image.new('P', (1, 1))
            image.putpalette([1, 2, 3] + [0]*765)
            image.info['transparency'] = 0
            (root/'source.png').write_bytes(encode_png(image, layout_record(image)))
            result = self.run_cli(root, 'recolor', '--image', 'source.png', '--map', 'FFFFFF', '000000',
                                  '--allow-region', 0, 0, 1, 1, '--out', 'candidate.png')
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertTrue(report['no_op'])
            self.assertEqual(report['unmatched_sources'], ['FFFFFFFF'])
            with Image.open(root/'candidate.png') as candidate:
                self.assertEqual(candidate.mode, 'RGBA')
                self.assertEqual(candidate.getpixel((0, 0)), (1, 2, 3, 0))
                record = json.loads(candidate.info[PNG_KEY])
                self.assertEqual(record['mode'], 'RGBA')
                self.assertEqual(record['rgba_sha256'], rgba_digest(candidate))

    def test_output_aliases_and_occupied_paths_never_overwrite_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = Image.new('RGBA', (2, 1), 'red')
            source.save(root/'source.png')
            Image.new('L', source.size, 255).save(root/'mask.png')
            (root/'layout.json').write_text(json.dumps(layout_record(source)), encoding='utf-8')
            before = {name: (root/name).read_bytes() for name in ['source.png', 'mask.png', 'layout.json']}
            base = ['recolor', '--image', 'source.png', '--metadata', 'layout.json', '--map', 'FF0000', '00FF00',
                    '--allow-mask', 'mask.png']
            cases = [('--out', 'source.png'), ('--out', 'mask.png'), ('--out', 'layout.json'),
                     ('--out', 'candidate.png', '--report', 'source.png'),
                     ('--out', 'candidate.png', '--metadata-out', 'layout.json'),
                     ('--out', 'candidate.png', '--report', 'candidate.png'),
                     ('--out', 'candidate.png', '--metadata-out', 'candidate.png')]
            for extra in cases:
                with self.subTest(extra=extra):
                    result = self.run_cli(root, *base, *extra, '--force')
                    self.assertEqual(result.returncode, 2, result.stdout+result.stderr)
                    self.assertFalse((root/'candidate.png').exists())
                    for name, data in before.items():
                        self.assertEqual((root/name).read_bytes(), data)
            (root/'report.json').write_text('keep this', encoding='utf-8')
            result = self.run_cli(root, *base, '--out', 'candidate.png', '--report', 'report.json')
            self.assertEqual(result.returncode, 2)
            self.assertFalse((root/'candidate.png').exists())
            self.assertEqual((root/'report.json').read_text(encoding='utf-8'), 'keep this')
            result = self.run_cli(root, *base, '--out', 'candidate.png', '--report', 'report.json', '--force')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads((root/'report.json').read_text(encoding='utf-8'))['changed_rgba_pixels'], 2)
            for name, data in before.items():
                self.assertEqual((root/name).read_bytes(), data)

    def test_stale_conflicting_and_invalid_layouts_fail_before_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = render(dict(kind='atlas', columns=1, cells=[
                dict(name='one', spec=dict(kind='grid', rows=['a'], palette={'a': 'FF0000'}))]))
            layout = layout_record(image)
            (root/'source.png').write_bytes(encode_png(image, layout))
            stale = json.loads(json.dumps(layout));stale['rgba_sha256'] = '0'*64
            conflict = json.loads(json.dumps(layout));conflict['atlas']['cells'][0]['name'] = 'renamed'
            for declaration in [stale, conflict]:
                (root/'layout.json').write_text(json.dumps(declaration), encoding='utf-8')
                result = self.run_cli(root, 'recolor', '--image', 'source.png', '--metadata', 'layout.json',
                                      '--map', 'FF0000', '00FF00', '--allow-region', 0, 0, 1, 1,
                                      '--out', 'candidate.png', '--report', 'report.json')
                self.assertEqual(result.returncode, 2)
                self.assertFalse((root/'candidate.png').exists())
                self.assertFalse((root/'report.json').exists())
            bad = json.loads(json.dumps(layout));bad['atlas']['cells'][0]['w'] = 2
            (root/'bad.png').write_bytes(encode_png(image, bad))
            result = self.run_cli(root, 'recolor', '--image', 'bad.png', '--map', 'FF0000', '00FF00',
                                  '--allow-region', 0, 0, 1, 1, '--out', 'candidate.png')
            self.assertEqual(result.returncode, 2)
            self.assertFalse((root/'candidate.png').exists())

    def test_unsupported_inputs_and_invalid_mapping_or_scope_make_no_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            Image.new('I;16', (1, 1)).save(root/'deep.png')
            Image.new('RGB', (1, 1)).save(root/'jpeg.png', format='JPEG')
            Image.new('RGBA', (1, 1), 'red').save(root/'source.png')
            Image.new('RGBA', (1, 1), 'red').save(root/'animated.png', save_all=True,
                append_images=[Image.new('RGBA', (1, 1), 'blue')])
            Image.new('RGB', (1, 1)).save(root/'rgb-mask.png')
            cases = [('--image', name) for name in ['deep.png', 'jpeg.png', 'animated.png']]
            cases += [('--image', 'source.png', '--allow-mask', 'animated.png'),
                      ('--image', 'source.png', '--allow-mask', 'rgb-mask.png'),
                      ('--image', 'source.png', '--map', 'ff0000ff', 'FFFFFF')]
            for extra in cases:
                result = self.run_cli(root, 'recolor', '--map', 'FF0000', '00FF00', '--allow-region',
                                      0, 0, 1, 1, '--out', 'candidate.png', *extra)
                self.assertEqual(result.returncode, 2, (extra, result.stdout, result.stderr))
                self.assertFalse((root/'candidate.png').exists())
            result = self.run_cli(root, 'recolor', '--image', 'source.png', '--map', 'FF0000', '00FF00',
                                  '--out', 'candidate.png')
            self.assertEqual(result.returncode, 2)
            self.assertFalse((root/'candidate.png').exists())

    def test_portable_output_uses_the_existing_cli_precedence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            Image.new('RGB', (1, 1), 'red').save(root/'source.png')
            env = dict(os.environ, PIXELART_PORTABLE_OUTPUT='bad')
            args = ('recolor', '--image', 'source.png', '--map', 'FF0000', '00FF00',
                    '--allow-region', 0, 0, 1, 1, '--out', 'candidate.png')
            result = self.run_cli(root, *args, env=env)
            self.assertEqual(result.returncode, 2)
            self.assertFalse((root/'candidate.png').exists())
            result = self.run_cli(root, *args, '--portable-output', env=env)
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
