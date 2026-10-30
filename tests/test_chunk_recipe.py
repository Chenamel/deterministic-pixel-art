"""Portable chunk authoring: global phase, exact edits and isolated owner sources."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from PIL import Image
from pixelart import render, verify_edit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'recipes'))
import chunk_left
import chunk_right
import chunk_pair


class MinimalChunkRecipeTests(unittest.TestCase):
    def test_local_sources_assemble_with_one_owner_per_pixel(self):
        files = chunk_pair.make_files()
        self.assertEqual(files['asset.png'].size, (64, 32))
        self.assertEqual(files['assembly.json']['covered_pixels'], 2048)
        self.assertEqual(files['assembly.json']['uncovered_pixels'], 0)
        self.assertEqual(files['assembly.json']['intended_overlaps'], [])
        self.assertEqual(files['assembly.json']['seam_count'], 1)
        self.assertNotIn('asset.json', files)
        for name, source in [('left', chunk_left.make_spec()), ('right', chunk_right.make_spec())]:
            expected = render(source)
            self.assertEqual(files[f'{name}/asset.png'].tobytes(), expected.tobytes())
            self.assertEqual(render(files[f'{name}/asset.json']).tobytes(), expected.tobytes())

    def test_six_pixel_texture_phase_does_not_restart_at_32(self):
        image = chunk_pair.make_files()['asset.png']
        # Frozen global anchors, independent of the shared deck helper.
        expected = {30: '4F4942FF', 31: 'D2B27CFF', 32: '9B7950FF',
                    33: '9B7950FF', 35: '9B7950FF', 36: '4F4942FF', 37: 'D2B27CFF'}
        for x, rgba in expected.items():
            with self.subTest(x=x):
                self.assertEqual(image.getpixel((x, 18)), tuple(bytes.fromhex(rgba)))
        for y, rgba in [(5, '72A4ADFF'), (12, 'D2B27CFF'), (13, '4F4942FF'),
                        (22, 'D2B27CFF'), (23, '4F4942FF')]:
            for x in (31, 32):
                self.assertEqual(image.getpixel((x, y)), tuple(bytes.fromhex(rgba)))

    def test_flag_edit_changes_exactly_24_pixels_and_preserves_other_owner(self):
        before = chunk_pair.make_files()
        after = chunk_pair.make_files('73A5AA')
        result = verify_edit(after['asset.png'], before['asset.png'], regions=[[51, 5, 6, 4]])
        self.assertTrue(result['valid'])
        self.assertEqual(result['changed_rgba_pixels'], 24)
        self.assertEqual(result['changed_outside'], 0)
        self.assertEqual(before['left/asset.png'].tobytes(), after['left/asset.png'].tobytes())
        self.assertNotEqual(before['layout.json']['rgba_sha256'], after['layout.json']['rgba_sha256'])

    def test_each_owner_runs_without_other_source_or_full_image(self):
        with tempfile.TemporaryDirectory(prefix='最小分块 source space ') as directory:
            root = Path(directory)
            for name, source in [('left', chunk_left.make_spec()), ('right', chunk_right.make_spec())]:
                task = root / name
                recipe = task / 'scripts/recipes'
                runtime = task / 'scripts/pixelart'
                recipe.mkdir(parents=True)
                runtime.mkdir(parents=True)
                for path in (ROOT / 'src/pixelart').glob('*.py'):
                    shutil.copyfile(path, runtime / path.name)
                for filename in [f'chunk_{name}.py', '_chunk_contract.py', '_common.py']:
                    shutil.copyfile(ROOT / 'recipes' / filename, recipe / filename)
                result = subprocess.run([sys.executable, '-B', str(recipe / f'chunk_{name}.py'),
                    '--out-dir', str(task / 'output')], cwd=root, capture_output=True,
                    text=True, encoding='utf-8', timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)
                with Image.open(task / 'output/asset.png') as actual:
                    self.assertEqual(actual.tobytes(), render(source).tobytes())
                self.assertEqual(len(list(recipe.glob('chunk_*.py'))), 1)
