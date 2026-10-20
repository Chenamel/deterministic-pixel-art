import json
import os
from pathlib import Path
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
        code = 'import sys; sys.path.insert(0, sys.argv[1]); import pixelart; import pixelart.cli'
        before = sorted(str(p.relative_to(self.folder)) for p in self.folder.rglob('*'))
        result = subprocess.run([sys.executable, '-B', '-c', code, str(ROOT / 'src')], cwd=self.folder,
                                capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(before, sorted(str(p.relative_to(self.folder)) for p in self.folder.rglob('*')))


if __name__ == '__main__':
    unittest.main()
