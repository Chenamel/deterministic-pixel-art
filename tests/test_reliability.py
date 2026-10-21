import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
import venv
from unittest.mock import patch

from PIL import Image
from pixelart import PixelArtError, render
from pixelart.output import publish
from pixelart.review import review

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / 'src/pixel_art.py'


class ReliabilityTests(unittest.TestCase):
    def test_interpreter_invocation_retains_virtualenv_prefix(self):
        from tools.test_skill import invocation_path
        with tempfile.TemporaryDirectory(prefix='venv space ') as directory:
            folder=Path(directory)/'isolated'
            venv.EnvBuilder(with_pip=False).create(folder)
            executable=folder/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
            result=subprocess.check_output([str(invocation_path(executable)),'-c',
                'import sys;print(sys.prefix)'],text=True).strip()
            self.assertEqual(Path(result),folder)

    def test_missing_and_unsupported_pillow_are_actionable(self):
        result=subprocess.run([sys.executable,'-B','-S',str(CLI),'--help'],capture_output=True,text=True,timeout=15)
        self.assertEqual(result.returncode,2,result.stderr)
        self.assertIn('install requirements.txt',json.loads(result.stderr)['error'])
        from pixelart.compat import require_pillow
        with patch('PIL.__version__','9.4.0'),self.assertRaisesRegex(ValueError,'Pillow >=10.4'):
            require_pillow()

    def test_null_outline_is_omitted_but_explicit_transparency_erases(self):
        op = dict(op='mask', points=[[2, 2]], color='FFFFFF')
        spec = dict(kind='draw', size=[5, 5], background='FF0000', operations=[op])
        expected = render(spec)
        op['outline'] = None
        self.assertEqual(render(spec).tobytes(), expected.tobytes())
        op['outline'] = '00000000'
        self.assertEqual(render(spec).getpixel((2, 1)), (0, 0, 0, 0))
        self.assertEqual(expected.getpixel((2, 1)), (255, 0, 0, 255))

    def test_background_selection_and_invalid_primary(self):
        im = Image.new('RGBA', (2, 2))
        context = dict(backgrounds=[dict(name='target', color='C6C6C6')])
        report, sheet, _ = review(im, context)
        self.assertEqual(report['facts']['primary_background'], 'target')
        self.assertEqual(sheet.getpixel((8, 62)), (198, 198, 198))
        context['primary_background'] = 'light'
        self.assertEqual(review(im, context)[1].getpixel((8, 62)), (233, 237, 242))
        context['primary_background'] = 'missing'
        with self.assertRaisesRegex(PixelArtError, 'primary_background'):
            review(im, context)

    def test_large_review_keeps_input_and_labels_bounded_views(self):
        for size in [(2800, 100), (8192, 1)]:
            im = Image.new('RGBA', size, (10, 20, 30, 128))
            before = im.tobytes()
            report, sheet, _ = review(im)
            self.assertLessEqual(max(sheet.size), 8192)
            self.assertLessEqual(sheet.width * sheet.height, 16_777_216)
            self.assertTrue(report['facts']['review_views'])
            self.assertEqual(im.tobytes(), before)
        self.assertTrue(any(v.get('cropped') for v in report['facts']['review_views']))

    def test_precise_point_outline_and_dsl_errors(self):
        bad = dict(kind='draw', size=[4, 4], operations=[
            dict(op='mask', points=[[0, 0]], color='FFFFFF', outline='000000')])
        with self.assertRaisesRegex(PixelArtError, r'operations\[0\].*mask outline.*\(-1, -1\).*\(4, 4\)'):
            render(bad)
        with self.assertRaises(PixelArtError) as raised:
            render('CANVAS 8 8\nRECT 6 0 4 4 FF0000')
        self.assertIn('line 2', str(raised.exception))
        self.assertNotIn('use clip=true explicitly', str(raised.exception))

    def test_preflight_and_commit_failure_preserve_existing_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            a, b = root/'a.png', root/'b.json'
            b.mkdir()
            with self.assertRaises(PixelArtError):
                publish({a: b'new', b: b'metadata'}, force=True)
            self.assertFalse(a.exists())
            b.rmdir()
            a.write_bytes(b'old-a'); b.write_bytes(b'old-b')
            replace = os.replace
            def fail_second(source, target):
                if Path(target) == b and str(source).endswith('.tmp'):
                    raise OSError('injected second commit failure')
                return replace(source, target)
            with patch('pixelart.output.os.replace', side_effect=fail_second):
                with self.assertRaisesRegex(PixelArtError, 'rollback_errors'):
                    publish({a:b'new-a', b:b'new-b'}, force=True)
            self.assertEqual(a.read_bytes(), b'old-a')
            self.assertEqual(b.read_bytes(), b'old-b')
            self.assertEqual(sorted(p.name for p in root.iterdir()), ['a.png', 'b.json'])

    def test_no_force_controlled_concurrent_cli_writers(self):
        with tempfile.TemporaryDirectory(prefix='并发 space ') as directory:
            root=Path(directory);spec=root/'spec.json';out=root/'out.png';ready=root/'ready'
            spec.write_text(json.dumps(dict(kind='grid', rows=['a'], palette={'a':'123456'})))
            code = '''import os,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from pixelart.cli import main
link=os.link
def hold(a,b):
    Path(sys.argv[2]).touch()
    sys.stdin.readline()
    return link(a,b)
os.link=hold
raise SystemExit(main(sys.argv[3:]))
'''
            arguments=['render','--spec',str(spec),'--out',str(out)]
            first=subprocess.Popen([sys.executable,'-B','-c',code,str(ROOT/'src'),str(ready),*arguments],
                stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            try:
                deadline=time.monotonic()+10
                while not ready.exists() and time.monotonic()<deadline and first.poll() is None:
                    time.sleep(.01)
                self.assertTrue(ready.exists())
                second=subprocess.run([sys.executable,'-B',str(CLI),*arguments],capture_output=True,text=True,timeout=15)
                self.assertEqual(second.returncode,2,second.stderr)
                stdout,stderr=first.communicate('\n',timeout=15)
                self.assertEqual(first.returncode,0,stderr)
            finally:
                if first.poll() is None:
                    first.kill();first.communicate()
            with Image.open(out) as image:
                self.assertEqual(image.getpixel((0,0)),(18,52,86,255))

    def test_deep_json_is_structured_error(self):
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'deep.json';out=source.with_suffix('.png')
            source.write_text('{"a":'*20000+'0'+'}'*20000)
            result=subprocess.run([sys.executable,'-B',str(CLI),'render','--spec',str(source),'--out',str(out)],
                capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,2,result.stderr)
            self.assertIn('error',json.loads(result.stderr))
            self.assertFalse(out.exists())
