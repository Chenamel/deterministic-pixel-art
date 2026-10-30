"""Consumer artifacts must stay reproducible, content-bound and safely rebuildable."""
from io import BytesIO
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from PIL import Image
from pixelart import PixelArtError, render
from pixelart.metadata import rgba_digest

ROOT = Path(__file__).resolve().parents[1]
MODULE = importlib.util.spec_from_file_location('consumer_demo', ROOT/'tools/build_consumer_demo.py')
demo = importlib.util.module_from_spec(MODULE)
MODULE.loader.exec_module(demo)


class ConsumerDemoTests(unittest.TestCase):
    def config(self):
        return json.loads((ROOT/'demos/pixel-ui/demo.json').read_text(encoding='utf-8'))

    def test_specs_layouts_and_reserved_regions_survive_width_edit(self):
        config = self.config()
        config['button_width'] = 112
        files = demo.build(config)
        manifest = json.loads(files['manifest.json'])
        for name, record in manifest['assets'].items():
            self.assertEqual(record['sha256'], hashlib.sha256(files[name]).hexdigest())
        self.assertEqual(manifest['variants']['revised']['width'], 112)
        for variant, width in [('baseline', config['baseline_width']), ('revised', 112)]:
            with self.subTest(variant=variant):
                image = Image.open(BytesIO(files[f'{variant}/buttons.png'])).convert('RGBA')
                spec = json.loads(files[f'{variant}/buttons.json'])
                layout = json.loads(files[f'{variant}/layout.json'])
                context = json.loads(files[f'{variant}/context.json'])
                self.assertEqual(image.size, (3*width, 36))
                self.assertEqual(render(spec).tobytes(), image.tobytes())
                self.assertEqual(layout['rgba_sha256'], rgba_digest(image))
                for cell, region in zip(layout['atlas']['cells'], context['regions'], strict=True):
                    self.assertEqual(region['name'], cell['name']+'-text')
                    self.assertEqual(region['rect'], [cell['x']+28, cell['y']+4, width-34, 10])
                    x, y, w, h = region['rect']
                    self.assertEqual(len(image.crop((x, y, x+w, y+h)).getcolors()), 1)

    def test_rebuild_from_unrelated_unicode_cwd_and_partial_overwrite_refusal(self):
        with tempfile.TemporaryDirectory(prefix='界面 consumer space ') as directory:
            cwd = Path(directory)
            target = cwd/'独立 output'
            def run(*args):
                return subprocess.run([sys.executable, '-B', str(ROOT/'tools/build_consumer_demo.py'),
                    '--out-dir', str(target), *args], cwd=cwd, capture_output=True,
                    text=True, encoding='utf-8', timeout=30)
            result = run()
            self.assertEqual(result.returncode, 0, result.stderr)
            before = {p.relative_to(target): p.read_bytes() for p in target.rglob('*') if p.is_file()}
            (target/'revised/layout.json').unlink()
            result = run()
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn('already exists', result.stderr)
            self.assertFalse((target/'revised/layout.json').exists())
            self.assertEqual((target/'revised/buttons.png').read_bytes(), before[Path('revised/buttons.png')])
            result = run('--force')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(before, {p.relative_to(target): p.read_bytes() for p in target.rglob('*') if p.is_file()})

    def test_invalid_configuration_is_rejected_before_output(self):
        with tempfile.TemporaryDirectory(prefix='consumer invalid ') as directory:
            cwd = Path(directory)
            for edit in ({'button_width': True}, {'hover': 'not-a-color'},
                         {'labels': {'run': '运行', 'loop': 'LOOP', 'export': 'EXPORT MAP'}}):
                with self.subTest(edit=edit):
                    config = self.config()
                    config.update(edit)
                    with self.assertRaises(PixelArtError):
                        demo.build(config)
                    config_path = cwd/'bad.json'
                    config_path.write_text(json.dumps(config), encoding='utf-8')
                    result = subprocess.run([sys.executable, '-B', str(ROOT/'tools/build_consumer_demo.py'),
                        '--config', str(config_path), '--out-dir', str(cwd/'out')],
                        cwd=cwd, capture_output=True, text=True, encoding='utf-8', timeout=30)
                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertFalse((cwd/'out').exists())
                    self.assertNotIn('Traceback', result.stderr)
