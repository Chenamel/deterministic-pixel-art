"""Test draw operation patches against the shipped toolkit CLI contract."""

from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from PIL import Image

from pixelart.spec import render


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / 'recipes/asset_toolkit.py'


class DrawPatchTests(unittest.TestCase):
    def setUp(self):
        workspace = tempfile.TemporaryDirectory(prefix='draw patch ')
        self.addCleanup(workspace.cleanup)
        self.root = Path(workspace.name)
        self.source = self.root / 'source.json'
        self.patch = self.root / 'patch.json'
        self.out = self.root / 'revised.json'
        self.spec = {
            'version': 1,
            'kind': 'draw',
            'size': [6, 5],
            'background': '343B4A',
            'palette': {'gold': 'FFCC00', 'blue': '0066FF'},
            'operations': [
                {'op': 'rect', 'x': 1, 'y': 1, 'w': 3, 'h': 2, 'color': 'gold'},
                {'op': 'line', 'points': [[0, 4], [3, 4]], 'color': 'gold'},
                {'op': 'blit', 'x': 5, 'y': 0, 'source': {
                    'kind': 'grid', 'rows': ['x'], 'palette': {'x': 'FFFFFF'},
                }},
            ],
        }
        self.write_source()

    def write_source(self):
        self.source.write_bytes(json.dumps(self.spec).encode('utf-8-sig') + b'\r\n')
        self.source_bytes = self.source.read_bytes()
        self.digest = sha256(self.source_bytes).hexdigest()

    def write_patch(self, **entries):
        document = {
            'version': 1, 'base_sha256': self.digest, 'at': 0, 'remove': 1,
            'insert': [{**self.spec['operations'][0], 'color': 'blue'}],
        }
        document.update(entries)
        self.patch.write_text(json.dumps(document), encoding='utf-8')

    def run_cli(self, *args, expected=0):
        env = dict(os.environ, PYTHONIOENCODING='utf-8')
        env.pop('PIXELART_PORTABLE_OUTPUT', None)
        result = subprocess.run(
            [sys.executable, '-B', str(CLI), *map(str, args)], cwd=self.root,
            env=env, capture_output=True, encoding='utf-8', timeout=20,
        )
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return json.loads(result.stderr if expected else result.stdout)

    def apply(self, *args, expected=0, out=None):
        return self.run_cli(
            'patch-draw', '--source', self.source, '--patch', self.patch,
            '--out', self.out if out is None else out, *args, expected=expected,
        )

    def test_inspection_replacement_and_delivery_round_trip(self):
        report = self.run_cli('patch-draw', '--source', self.source, '--inspect-ops', '--limit', 1)
        self.assertEqual(report['file_sha256'], self.digest)
        self.assertEqual(report['operation_count'], 3)
        self.assertEqual(report['next_offset'], 1)
        self.assertEqual(report['operations'], [{'index': 0, **self.spec['operations'][0]}])
        second = self.run_cli(
            'patch-draw', '--source', self.source, '--inspect-ops', '--offset', report['next_offset'],
        )
        self.assertEqual(second['operations'][0]['points_sample'], [[0, 4], [3, 4]])
        self.assertEqual(second['operations'][0]['index'], 1)
        self.assertEqual(second['operations'][1], {'index': 2, 'op': 'blit', 'x': 5, 'y': 0})
        self.assertIsNone(second['next_offset'])
        self.assertEqual(set(self.root.iterdir()), {self.source})

        self.write_patch(base_sha256=report['file_sha256'])
        result = self.apply('--allow-region', 1, 1, 3, 2)
        self.assertEqual(result['changed_rgba_pixels'], 6)
        self.assertEqual(result['alpha_changed_pixels'], 0)
        revised = json.loads(self.out.read_bytes())
        self.assertEqual(revised, {
            **self.spec, 'operations': [
                {**self.spec['operations'][0], 'color': 'blue'}, *self.spec['operations'][1:],
            ],
        })
        self.run_cli('deliver', '--source', self.out, '--mode', 'grid',
                     '--out-dir', 'delivery', '--pack-zip', 'result.zip')
        self.run_cli('rebuild', '--input', 'result.zip', '--out-dir', 'rebuilt')
        with Image.open(self.root / 'rebuilt/asset.png') as image:
            self.assertEqual(image.tobytes(), render(revised).tobytes())
        self.assertEqual(self.source.read_bytes(), self.source_bytes)

    def test_insert_remove_append_and_visual_noop_keep_operation_order(self):
        for at, remove, insert in [
            (1, 0, [{'op': 'rect', 'x': 0, 'y': 4, 'w': 1, 'h': 1, 'color': 'blue'}]),
            (0, 1, []),
            (3, 0, [
                {'op': 'points', 'points': [[5, 3]], 'color': 'blue'},
                {'op': 'points', 'points': [[5, 3]], 'color': 'gold'},
            ]),
        ]:
            with self.subTest(at=at, remove=remove):
                self.write_patch(at=at, remove=remove, insert=insert)
                result = self.apply('--allow-region', 0, 0, 6, 5, '--force')
                self.assertEqual(result['changed_rgba_pixels'] == 0, at == 1)
                self.assertEqual(result['inserted'], len(insert))
                self.assertEqual(result['removed'], remove)
                operations = self.spec['operations']
                self.assertEqual(json.loads(self.out.read_bytes())['operations'],
                                 operations[:at] + insert + operations[at + remove:])

    def test_rgba_mask_and_regions_union_and_hidden_rgb(self):
        self.spec['background'] = '10101000'
        self.write_source()
        self.write_patch(at=3, remove=0, insert=[
            {'op': 'points', 'points': [[0, 0], [0, 1]], 'color': '22222200'},
        ])
        mask = self.root / 'scope.png'
        image = Image.new('RGBA', (6, 5), (255, 255, 255, 0))
        image.putpixel((0, 0), (0, 0, 0, 1))
        image.save(mask)
        error = self.apply('--mask', mask, expected=1)
        self.assertEqual(error['details']['boundary']['outside_samples'], [[0, 1]])
        self.assertFalse(self.out.exists())
        report = self.apply('--mask', mask, '--allow-region', 0, 1, 1, 1)
        self.assertEqual(report['changed_rgba_pixels'], 2)
        self.assertEqual(report['alpha_changed_pixels'], 0)
        self.assertEqual(report['boundary']['allowed_pixels'], 2)

    def test_alpha_lock_and_mask_outline(self):
        self.spec.pop('background')
        self.write_source()
        self.write_patch(at=3, remove=0, insert=[
            {'op': 'mask', 'points': [[4, 2]], 'color': 'blue', 'outline': 'gold'},
        ])
        mask = self.root / 'scope.png'
        image = Image.new('L', (6, 5))
        image.putpixel((4, 2), 1)
        image.save(mask)
        error = self.apply('--mask', mask, '--allow-alpha-change', expected=1)
        self.assertEqual(error['details']['boundary']['changed_outside'], 6)
        error = self.apply('--allow-region', 3, 1, 3, 3, expected=1)
        self.assertIn('alpha lock', error['error'])
        self.assertFalse(self.out.exists())
        report = self.apply('--allow-region', 3, 1, 3, 3, '--allow-alpha-change')
        self.assertEqual(report['alpha_changed_pixels'], 7)

    def test_deletion_exposing_paint_outside_scope_is_rejected(self):
        # The upper rectangle hides a wider rectangle in the original drawing.
        self.spec['operations'].insert(0, {
            'op': 'rect', 'x': 0, 'y': 1, 'w': 4, 'h': 2, 'color': 'blue',
        })
        self.spec['operations'][1].update(x=0, w=4)
        self.write_source()
        self.write_patch(at=1, remove=1, insert=[])
        before = self.patch.read_bytes()
        error = self.apply('--allow-region', 1, 1, 3, 2, expected=1)
        self.assertEqual(error['details']['boundary']['outside_samples'], [[0, 1], [0, 2]])
        self.assertFalse(self.out.exists())
        self.assertEqual(self.source.read_bytes(), self.source_bytes)
        self.assertEqual(self.patch.read_bytes(), before)

    def test_mask_validation_and_hard_link_alias(self):
        self.write_patch()
        mask = self.root / 'scope.png'
        Image.new('RGB', (6, 5), 'white').save(mask)
        self.assertIn('L/1 intensity', self.apply('--mask', mask, expected=2)['error'])
        Image.new('L', (5, 5), 255).save(mask)
        self.assertIn('dimensions must match', self.apply('--mask', mask, expected=2)['error'])
        self.assertFalse(self.out.exists())
        Image.new('L', (6, 5), 255).save(mask)
        mask_before = mask.read_bytes()
        self.assertIn('aliases input path', self.apply(
            '--mask', mask, '--force', out=mask, expected=2,
        )['error'])
        self.assertEqual(mask.read_bytes(), mask_before)
        os.link(self.source, self.out)
        self.assertIn('aliases input path', self.apply('--mask', mask, '--force', expected=2)['error'])
        self.assertEqual(self.source.read_bytes(), self.source_bytes)

    def test_rejections_leave_outputs_and_inputs_intact(self):
        self.out.write_bytes(b'sentinel')
        for update, message in [
            ({'base_sha256': '0' * 64}, 'base_sha256 mismatch'),
            ({'at': True}, 'expected an integer'),
            ({'at': -1}, 'expected an integer'),
            ({'remove': -1}, 'expected an integer'),
            ({'at': 3, 'remove': 1}, 'slice exceeds'),
            ({'at': 4, 'remove': 0}, 'slice exceeds'),
            ({'remove': 0, 'insert': []}, 'insertion or removal'),
            ({'unexpected': 0}, 'unknown fields'),
            ({'insert': [{'op': 'blit'}]}, 'must be a rect'),
            ({'insert': [{**self.spec['operations'][0], 'oops': 1}]}, 'unknown fields'),
            ({'insert': [{**self.spec['operations'][0], 'x': -1}]}, 'bounds'),
        ]:
            with self.subTest(update=update):
                self.write_patch(**update)
                error = self.apply('--allow-region', 0, 0, 6, 5, '--force', expected=2)
                self.assertIn(message, error['error'])
                self.assertEqual(self.out.read_bytes(), b'sentinel')
                self.assertEqual(self.source.read_bytes(), self.source_bytes)

        self.write_patch(insert=[{**self.spec['operations'][0], 'x': -1, 'clip': True}])
        self.assertIn('already exists', self.apply('--allow-region', 0, 0, 6, 5, expected=2)['error'])
        for protected in (self.source, self.patch):
            before = protected.read_bytes()
            self.assertIn('aliases input path', self.apply(
                '--allow-region', 0, 0, 6, 5, '--force', out=protected, expected=2,
            )['error'])
            self.assertEqual(protected.read_bytes(), before)
        self.apply('--allow-region', 0, 0, 6, 5, '--force', '--portable-output')
        self.assertEqual(json.loads(self.out.read_bytes())['operations'][0]['x'], -1)

    def test_strict_json_read_only_mode_and_scope_requirement(self):
        self.patch.write_text('{"at": 0, "at": 1}', encoding='utf-8')
        self.assertIn('duplicate JSON key', self.apply('--allow-region', 0, 0, 6, 5, expected=2)['error'])
        self.patch.write_text('{"at": NaN}', encoding='utf-8')
        self.assertIn('invalid JSON constant', self.apply('--allow-region', 0, 0, 6, 5, expected=2)['error'])
        self.write_patch()
        self.assertIn('declare --allow-region or --mask', self.apply(expected=2)['error'])
        self.run_cli('patch-draw', '--source', self.source, '--inspect-ops', '--out', self.out, expected=2)
        self.run_cli('patch-draw', '--source', self.source, '--inspect-ops', '--limit', 201, expected=2)
        self.run_cli('patch-draw', '--source', self.source, '--inspect-ops', '--offset', 4, expected=2)
        self.assertFalse(self.out.exists())
