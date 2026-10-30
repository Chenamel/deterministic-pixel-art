"""Exercise explicit process output selection without changing publication semantics."""
from contextlib import redirect_stderr, redirect_stdout
import errno
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from PIL import Image
from pixelart import PixelArtError
from pixelart.cli import main
from pixelart.output import publish

ROOT = Path(__file__).resolve().parents[1]
KEY = 'PIXELART_PORTABLE_OUTPUT'
REJECTED = OSError(errno.EPERM, 'simulated mount rejects hard links')


class OutputSelectionTests(unittest.TestCase):
    def setUp(self):
        environment = patch.dict(os.environ)
        environment.start()
        self.addCleanup(environment.stop)
        os.environ.pop(KEY, None)
        temporary = tempfile.TemporaryDirectory(prefix='便携 output space ')
        self.addCleanup(temporary.cleanup)
        self.folder = Path(temporary.name)
        self.spec = self.folder/'input.json'
        self.spec.write_text(json.dumps(dict(kind='grid', rows=['ab'],
            palette={'a': '12345678', 'b': 'ABCDEF00'})), encoding='utf-8')

    def cli(self, *args, expected=0):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(list(map(str, args)))
        self.assertEqual(code, expected, stderr.getvalue())
        return stdout.getvalue(), stderr.getvalue()

    def test_environment_applies_to_every_cli_writer_without_hard_links(self):
        os.environ[KEY] = '1'
        image = self.folder/'asset.png'
        with patch('pixelart.output.os.link', side_effect=REJECTED) as link:
            self.cli('render', '--spec', self.spec, '--out', image,
                     '--preview', self.folder/'preview.png', '--metadata', self.folder/'layout.json')
            self.cli('preview', '--image', image, '--out', self.folder/'larger.png')
            self.cli('import', '--image', image, '--out', self.folder/'editable.json')
            self.cli('inspect', '--image', image, '--grid', '--out', self.folder/'inspect.json')
            self.cli('verify', '--image', image, '--compare', image, '--allow-region', 0, 0, 2, 1,
                     '--out', self.folder/'verify.json')
            self.cli('review', '--image', image, '--out-dir', self.folder/'review')
            self.cli('replace-cell', '--spec', ROOT/'examples/workflows/atlas-final.json',
                     '--cell', 'transfer', '--replacement', ROOT/'examples/workflows/atlas-replacement.json',
                     '--out', self.folder/'candidate.json', '--image-out', self.folder/'candidate.png',
                     '--metadata', self.folder/'candidate-layout.json')
            project = self.folder/'project.json'
            project.write_text(json.dumps(dict(version=1, size=[2, 1], require_coverage=True,
                parts=[dict(name='part', image='asset.png', at=[0, 0], mode='copy')])), encoding='utf-8')
            self.cli('assemble', '--project', project, '--out', self.folder/'assembled.png',
                     '--report', self.folder/'assembly.json', '--seams', self.folder/'seams.png')
            link.assert_not_called()
        with Image.open(image) as source, Image.open(self.folder/'assembled.png') as assembled:
            self.assertEqual(source.tobytes(), assembled.tobytes())
        self.assertTrue(json.loads((self.folder/'verify.json').read_text())['valid'])

    def test_default_and_zero_keep_hard_links_and_do_not_fallback(self):
        for setting in (None, '0'):
            with self.subTest(setting=setting):
                if setting is not None:
                    os.environ[KEY] = setting
                out = self.folder/'rejected'/'output.png'
                with patch('pixelart.output.os.link', side_effect=REJECTED) as link:
                    _, stderr = self.cli('render', '--spec', self.spec, '--out', out, expected=2)
                    link.assert_called_once()
                detail = json.loads(json.loads(stderr)['error'].split(': ', 1)[1])
                self.assertEqual(detail['remaining_outputs'], [])
                self.assertEqual(detail['rollback_errors'], [])
                self.assertFalse(out.exists())
                self.assertEqual(list(out.parent.iterdir()), [])

    def test_flags_override_environment_and_bad_settings_fail_before_writing(self):
        for setting in ('1', 'invalid'):
            os.environ[KEY] = setting
            with patch('pixelart.output.os.link', side_effect=REJECTED) as link:
                self.cli('render', '--spec', self.spec, '--out', self.folder/'default.png',
                         '--no-portable-output', expected=2)
                link.assert_called_once()
        for setting in ('0', 'invalid'):
            os.environ[KEY] = setting
            out = self.folder/f'portable-{setting}.png'
            with patch('pixelart.output.os.link', side_effect=REJECTED) as link:
                self.cli('render', '--spec', self.spec, '--out', out, '--portable-output')
                link.assert_not_called()
        for setting in ('', 'true', 'false', '2', ' 1 '):
            os.environ[KEY] = setting
            out = self.folder/'invalid'/'output.png'
            _, stderr = self.cli('render', '--spec', self.spec, '--out', out, '--force', expected=2)
            self.assertIn(KEY, json.loads(stderr)['error'])
            self.assertFalse(out.parent.exists())

    def test_read_only_commands_ignore_output_setting_and_api_is_environment_free(self):
        image = self.folder/'input.png'
        Image.new('RGBA', (1, 1), 'red').save(image)
        os.environ[KEY] = 'invalid'
        self.cli('validate', '--image', image)
        self.cli('inspect', '--image', image, '--grid')
        self.cli('verify', '--image', image, '--compare', image, '--allow-region', 0, 0, 1, 1)
        os.environ[KEY] = '1'
        out = self.folder/'api.txt'
        with patch('pixelart.output.os.link', side_effect=REJECTED) as link:
            with self.assertRaises(PixelArtError):
                publish({out: b'original API default'})
            link.assert_called_once()
            publish({out: b'explicit API choice'}, portable=True)
        self.assertEqual(out.read_bytes(), b'explicit API choice')

    def test_environment_does_not_imply_force_or_leave_partial_outputs(self):
        os.environ[KEY] = '1'
        out = self.folder/'output.png'
        self.cli('render', '--spec', self.spec, '--out', out)
        original = out.read_bytes()
        metadata = self.folder/'missing-layout.json'
        self.cli('render', '--spec', self.spec, '--out', out, '--metadata', metadata, expected=2)
        self.assertEqual(out.read_bytes(), original)
        self.assertFalse(metadata.exists())
        with patch('pixelart.output.os.link', side_effect=REJECTED):
            self.cli('render', '--spec', self.spec, '--out', out, '--force')
        self.assertEqual(out.read_bytes(), original)
        a, b = self.folder/'first.txt', self.folder/'second.txt'
        real_open = os.open

        def fail_second(path, flags, *args, **kwargs):
            # Publication resolves paths; Windows temp roots may use an 8.3 alias.
            if Path(path).resolve() == b.resolve():
                raise OSError(errno.EIO, 'injected portable commit failure')
            return real_open(path, flags, *args, **kwargs)

        with patch('pixelart.output.os.open', side_effect=fail_second):
            with self.assertRaisesRegex(PixelArtError, 'rollback_errors'):
                publish({a: b'first', b: b'second'}, portable=True)
        self.assertFalse(a.exists())
        self.assertFalse(b.exists())
        self.assertFalse(list(self.folder.glob('.*.pixelart.lock')))
        self.assertFalse(list(self.folder.glob('*.tmp')))

    def test_child_cli_and_recipe_inherit_choice_with_explicit_override(self):
        os.environ[KEY] = '1'
        # Simulate the failing primitive in child processes; task commands have no flag.
        driver = '''import errno, os, runpy, sys
def reject(*args): raise OSError(errno.EPERM, 'hard links rejected')
os.link = reject
script = sys.argv.pop(1)
sys.argv[0] = script
sys.path.insert(0, os.path.dirname(script))
runpy.run_path(script, run_name='__main__')
'''
        for script, args in (
            (ROOT/'src/pixel_art.py', ['render', '--spec', self.spec, '--out', self.folder/'child.png']),
            (ROOT/'recipes/icons.py', ['--out-dir', self.folder/'icons']),
            (ROOT/'recipes/chunk_pair.py', ['--out-dir', self.folder/'chunks'])):
            command = [sys.executable, '-B', '-c', driver, str(script), *map(str, args)]
            first = subprocess.run(command, cwd=self.folder, capture_output=True, timeout=30)
            self.assertEqual(first.returncode, 0, first.stderr)
            again = subprocess.run(command, cwd=self.folder, capture_output=True, timeout=30)
            self.assertEqual(again.returncode, 2, again.stderr)
        command = [sys.executable, '-B', '-c', driver, str(ROOT/'recipes/icons.py'),
                   '--out-dir', str(self.folder/'default-recipe'), '--no-portable-output']
        result = subprocess.run(command, cwd=self.folder, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertFalse((self.folder/'default-recipe/asset.png').exists())

    def test_concurrent_inherited_portable_writers_keep_one_success(self):
        os.environ[KEY] = '1'
        out, ready = self.folder/'race.png', self.folder/'ready'
        driver = '''import os, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from pixelart.cli import main
real_open = os.open
def hold(path, flags, *args, **kwargs):
    if Path(path).resolve() == Path(sys.argv[2]).resolve():
        Path(sys.argv[3]).touch()
        sys.stdin.readline()
    return real_open(path, flags, *args, **kwargs)
os.open = hold
raise SystemExit(main(sys.argv[4:]))
'''
        args = ['render', '--spec', str(self.spec), '--out', str(out)]
        first = subprocess.Popen([sys.executable, '-B', '-c', driver, str(ROOT/'src'),
            str(out), str(ready), *args], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, encoding='utf-8', cwd=self.folder)
        try:
            deadline = time.monotonic() + 10
            while not ready.exists() and time.monotonic() < deadline and first.poll() is None:
                time.sleep(.01)
            self.assertTrue(ready.exists())
            second = subprocess.run([sys.executable, '-B', str(ROOT/'src/pixel_art.py'), *args],
                cwd=self.folder, capture_output=True, text=True, encoding='utf-8', timeout=15)
            self.assertEqual(second.returncode, 2, second.stderr)
            self.assertIn('reserved by another writer', second.stderr)
            _, stderr = first.communicate('\n', timeout=15)
            self.assertEqual(first.returncode, 0, stderr)
        finally:
            if first.poll() is None:
                first.kill()
            # Drain and close the pipes even when the child exited before the barrier.
            first.communicate()
        with Image.open(out) as image:
            self.assertEqual(image.getpixel((0, 0)), (18, 52, 86, 120))


if __name__ == '__main__':
    unittest.main()
