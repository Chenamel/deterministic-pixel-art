"""LT05-only distribution/recording contracts; local fixture is never shipped."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from build_sprite_trial import build
from prepare_agent_trials import archive_bytes, sha

AUTHOR = '''from pathlib import Path
import json, sys
RUN = Path(__file__).resolve().parents[2]/'RUN'
def rect(x,y,w,h,color): return dict(op='rect',x=x,y=y,w=w,h=h,color=color)
if sys.argv[1]=='v1':
    spec=dict(version=1,kind='draw',size=[32,32],operations=[
        dict(op='polygon',points=[[3,13],[17,9],[26,12],[29,17],[24,21],[10,21],[4,18]],color='26364B'),
        dict(op='polygon',points=[[6,14],[17,11],[25,14],[27,17],[23,19],[10,19],[6,17]],color='6A8BA0'),
        rect(18,12,6,4,'C8DFE8'),rect(2,14,3,4,'EAB45F'),rect(11,21,8,4,'26364B'),
        rect(12,3,8,5,'26364B'),rect(14,4,4,2,'F5C26B'),
        rect(23,19,2,1,'F5C26B'),rect(0,0,1,1,'13253500'),rect(1,24,1,1,'669EB580')])
else:
    spec=json.loads((RUN/'v1/sprite.json').read_text(encoding='utf-8'))
    for op in spec['operations']:
        if op.get('x')==14 and op.get('y')==4: op['color']='62D8E8'
(RUN/sys.argv[1]/'sprite.json').write_text(json.dumps(spec),encoding='utf-8')
'''


def complete_fixture(work, run):
    run('start', '--platform', 'coordinator fixture', '--model', 'not external AI')
    (work/'RUN/v1').mkdir()
    (work/'RUN/v1/author.py').write_text(AUTHOR, encoding='utf-8')
    run('script', 'RUN/v1/author.py', 'v1')
    run('tool', 'render', '--spec', 'RUN/v1/sprite.json', '--out', 'RUN/v1/sprite.png')
    (work/'RUN/v2').mkdir()
    (work/'RUN/v2/author.py').write_text(AUTHOR, encoding='utf-8')
    run('script', 'RUN/v2/author.py', 'v2')
    run('tool', 'render', '--spec', 'RUN/v2/sprite.json', '--out', 'RUN/v2/sprite.png')
    run('tool', 'verify', '--image', 'RUN/v2/sprite.png', '--compare', 'RUN/v1/sprite.png',
        '--allow-region', '12', '2', '8', '6', '--out', 'RUN/change.json')
    for theme, color in [('dark', '182637'), ('light', 'E9EDF2')]:
        for scale in (1, 8):
            run('tool', 'preview', '--image', 'RUN/v2/sprite.png', '--out', f'RUN/views/{theme}-{scale}x.png',
                '--background', color, '--scale', str(scale))
    (work/'RUN/feedback.md').write_text('Local engineering fixture; not an external usability or aesthetic result.', encoding='utf-8')


class SpriteTrialTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='精灵 trial space ')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        folder = ROOT/'skill/deterministic-pixel-art'
        files = {'deterministic-pixel-art/'+path.relative_to(folder).as_posix(): path.read_bytes()
                 for path in folder.rglob('*') if path.is_file() and '__pycache__' not in path.parts}
        self.skill_zip = self.root/'skill.zip'
        self.skill_zip.write_bytes(archive_bytes(files))
        self.digest = sha(self.skill_zip.read_bytes())
        self.out = self.root/'packet'
        self.record = build(self.skill_zip, self.out, self.digest)
        with zipfile.ZipFile(self.out/'LT05-Sprite.zip') as bundle:
            bundle.extractall(self.root/'中文 extracted space')
        self.work = self.root/'中文 extracted space/LT05'

    def run_recorder(self, *args, expected=0):
        environment = {key: value for key, value in os.environ.items() if key not in ('PYTHONPATH', 'PYTHONHOME')}
        environment.update(PIXELART_PORTABLE_OUTPUT='1', PYTHONIOENCODING='utf-8')
        result = subprocess.run([sys.executable, '-B', str(self.work/'run.py'), *map(str, args)],
                                cwd=self.root, env=environment, capture_output=True, text=True, encoding='utf-8', timeout=30)
        self.assertEqual(result.returncode, expected, result.stdout+result.stderr)
        return result

    def checks(self):
        return json.loads((self.work/'RUN/checks.json').read_text(encoding='utf-8'))

    def test_exact_reproducible_packet_without_assignment_or_fixture(self):
        self.assertEqual(build(self.skill_zip, self.root/'second', self.digest), self.record)
        self.assertEqual((self.out/'LT05-Sprite.zip').read_bytes(), (self.root/'second/LT05-Sprite.zip').read_bytes())
        with zipfile.ZipFile(self.out/'LT05-Sprite.zip') as bundle, zipfile.ZipFile(self.skill_zip) as skill:
            expected = {'LT05/'+name for name in skill.namelist()} | {
                'LT05/'+name for name in ('START_HERE.md', 'run.py', 'recorder.py', 'task.json', 'checksums.json', 'inputs/brief.json')}
            self.assertEqual(set(bundle.namelist()), expected)
            for name in skill.namelist():
                self.assertEqual(skill.read(name), bundle.read('LT05/'+name))
            prompt = bundle.read('LT05/START_HERE.md').decode('utf-8')
            for phrase in ('GLM', 'WorkBuddy', '协调', '32会话', '参考答案', 'GitHub', 'token'):
                self.assertNotIn(phrase, prompt)
            self.assertFalse(any('/coordinator/' in name or name.endswith('/author.py') for name in bundle.namelist()))
        with self.assertRaises(FileExistsError):
            build(self.skill_zip, self.out, self.digest)
        with self.assertRaisesRegex(ValueError, 'SHA-256'):
            build(self.skill_zip, self.root/'bad', '0'*64)
        self.assertFalse((self.root/'bad').exists())

    def test_recorded_chain_tamper_detection_and_submission(self):
        complete_fixture(self.work, self.run_recorder)
        self.run_recorder('check')
        self.assertTrue(self.checks()['passed'])
        self.assertEqual(len(self.checks()['checks']), 22)
        target = self.work/'RUN/v2/sprite.png'
        original = target.read_bytes()
        with Image.open(target) as opened:
            image = opened.copy()
        image.putpixel((25, 25), (255, 0, 0, 255))
        image.save(target)
        self.run_recorder('check', expected=1)
        failures = {item['check'] for item in self.checks()['checks'] if not item['passed']}
        self.assertIn('only-indicator-changed', failures)
        self.assertIn('v2-editable-rerenders', failures)
        target.write_bytes(original)
        self.run_recorder('tool', 'render', '--spec', 'RUN/v2/sprite.json', '--out', 'RUN/v2/sprite.png', expected=2)
        self.assertEqual(target.read_bytes(), original)
        records = [json.loads(line) for line in (self.work/'RUN/commands.jsonl').read_text(encoding='utf-8').splitlines()]
        self.assertEqual(len(records), 10)
        self.assertEqual(records[-1]['outputs_before'], records[-1]['outputs_after'])
        self.run_recorder('finish', '--status', 'complete')
        with zipfile.ZipFile(self.work/'submission-LT05.zip') as bundle:
            self.assertIn('RUN/v1/author.py', bundle.namelist())
            self.assertIn('RUN/v2/author.py', bundle.namelist())
            self.assertNotIn('LT05/deterministic-pixel-art/SKILL.md', bundle.namelist())

    def test_reviewed_v1_source_changes_are_detected(self):
        complete_fixture(self.work, self.run_recorder)
        self.run_recorder('check')
        source = self.work/'RUN/v1/author.py'
        source.write_text(AUTHOR+'\n# changed after v1 was ready\n', encoding='utf-8')
        self.run_recorder('check', expected=1)
        failures = {item['check'] for item in self.checks()['checks'] if not item['passed']}
        self.assertEqual(failures, {'v1-ready-files-preserved'})

    def test_incomplete_archival_and_frozen_inputs(self):
        self.run_recorder('start', '--platform', 'fixture', '--model', 'unknown')
        self.run_recorder('finish', '--status', 'quota_limited', expected=1)
        self.assertTrue((self.work/'submission-LT05.zip').is_file())
        self.assertFalse(self.checks()['passed'])
        (self.work/'inputs/brief.json').write_text('{}', encoding='utf-8')
        result = self.run_recorder('check', expected=2)
        self.assertIn('Frozen task/Skill changed', result.stderr)


if __name__ == '__main__':
    unittest.main()
