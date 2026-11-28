import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / 'src/pixel_art.py'


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='像素 art ')
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.spec = self.folder / '输入 spec.json'
        self.spec.write_text(json.dumps({'kind': 'grid', 'rows': ['ab'],
            'palette': {'a': '123456', 'b': None}}), encoding='utf-8')
        self.out = self.folder / '子目录' / '输出 image.png'

    def run_cli(self, *args):
        return subprocess.run([sys.executable, '-B', str(CLI), *map(str, args)], cwd=self.folder,
                              capture_output=True, text=True, encoding='utf-8',
                              env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}, timeout=30)

    def test_render_validate_preview_from_unicode_working_directory(self):
        metadata = self.folder / '布局.json'
        enlarged = self.folder / '预览.png'
        result = self.run_cli('render', '--spec', self.spec, '--out', self.out,
                              '--preview', enlarged, '--metadata', metadata, '--scale', 3)
        self.assertEqual(result.returncode, 0, result.stderr)
        with Image.open(self.out) as image:
            self.assertEqual((image.mode, image.size), ('RGBA', (2, 1)))
        with Image.open(enlarged) as image:
            self.assertEqual(image.size, (6, 3))
        self.assertEqual(json.loads(metadata.read_text(encoding='utf-8'))['size'], [2, 1])
        render_report = json.loads(result.stdout)
        self.assertEqual(render_report['advisory']['isolated_pixels_4conn'], 1)
        self.assertEqual(render_report['advisory']['components_8conn_count'], 1)
        self.assertEqual(render_report['advisory']['components_8conn_sizes'], [1])
        self.assertEqual(render_report['advisory']['components_8conn_bboxes'], [[0, 0, 1, 1]])
        self.assertIn('hints', render_report['advisory'])
        self.assertEqual(self.run_cli('validate', '--image', self.out).returncode, 0)
        self.assertEqual(self.run_cli('preview', '--image', self.out, '--out', self.folder / '另一个.png').returncode, 0)

    def test_reject_overwrite_and_input_output_alias(self):
        self.assertEqual(self.run_cli('render', '--spec', self.spec, '--out', self.out).returncode, 0)
        before = self.out.read_bytes()
        self.assertEqual(self.run_cli('render', '--spec', self.spec, '--out', self.out).returncode, 2)
        self.assertEqual(self.out.read_bytes(), before)
        self.assertEqual(self.run_cli('render', '--spec', self.spec, '--out', self.spec, '--force').returncode, 2)
        self.assertEqual(self.run_cli('render', '--spec', self.spec, '--out', self.out, '--force').returncode, 0)

    def test_invalid_spec_or_rules_does_not_create_any_output(self):
        self.spec.write_text('{"kind":"grid","rows":["?"],"palette":{}}', encoding='utf-8')
        result = self.run_cli('render', '--spec', self.spec, '--out', self.out)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(self.out.parent.exists())
        self.spec.write_text('{"kind":"draw","size":[2,2],"operations":[]}', encoding='utf-8')
        rules = self.folder / 'rules.json'
        rules.write_text('{"nonempty":true}', encoding='utf-8')
        result = self.run_cli('render', '--spec', self.spec, '--out', self.out, '--rules', rules)
        self.assertEqual(result.returncode, 1)
        self.assertFalse(self.out.exists())

    def test_duplicate_json_key_is_rejected(self):
        self.spec.write_text('{"kind":"draw","kind":"grid"}', encoding='utf-8')
        self.assertEqual(self.run_cli('render', '--spec', self.spec, '--out', self.out).returncode, 2)

    def test_import_creates_no_files(self):
        code = 'import sys; sys.path.insert(0, sys.argv[1]); import pixelart; import pixelart.cli; import pixel_art'
        before = sorted(str(p.relative_to(self.folder)) for p in self.folder.rglob('*'))
        result = subprocess.run([sys.executable, '-B', '-c', code, str(ROOT / 'src')], cwd=self.folder,
                                capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(before, sorted(str(p.relative_to(self.folder)) for p in self.folder.rglob('*')))

    def test_cli_without_B_creates_no_pycache(self):
        tree = self.folder / 'skill_scripts'
        shutil.copytree(ROOT / 'src/pixelart', tree / 'pixelart', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        shutil.copytree(ROOT / 'recipes', tree / 'recipes', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        shutil.copyfile(ROOT / 'src/pixel_art.py', tree / 'pixel_art.py')
        for cli_path in (tree / 'pixel_art.py', tree / 'recipes/asset_toolkit.py'):
            result = subprocess.run([sys.executable, str(cli_path), '--help'], cwd=self.folder,
                                    capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
        leftovers = [str(p.relative_to(tree)) for p in tree.rglob('*') if '__pycache__' in p.parts or p.suffix in ('.pyc', '.pyo')]
        self.assertEqual(leftovers, [])

    def test_pixel_art_entrypoint_reexports_public_api(self):
        code = (
            'import sys; sys.path.insert(0, sys.argv[1]); '
            'import pixelart, pixel_art; '
            'assert pixel_art.__all__ == pixelart.__all__; '
            'assert all(getattr(pixel_art, name) is getattr(pixelart, name) for name in pixelart.__all__)'
        )
        result = subprocess.run([sys.executable, '-B', '-c', code, str(ROOT / 'src')], cwd=self.folder,
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
