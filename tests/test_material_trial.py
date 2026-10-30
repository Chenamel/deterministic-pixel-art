"""LT06 packet and artifact-check contracts; fixtures never enter the packet."""
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
from build_material_trial import build
from prepare_agent_trials import archive_bytes, sha

AUTHOR = '''from pathlib import Path
import json
RUN = Path(__file__).resolve().parent
def rect(x,y,w,h,color): return dict(op='rect',x=x,y=y,w=w,h=h,color=color)
def polygon(points,color): return dict(op='polygon',points=points,color=color)
cells=[]
for name,base,light,shadow,edge in [
    ('wood','8C5935','C58A52','5C3D30','322824'),
    ('metal','8197A8','D7E8ED','445B72','202F42'),
    ('stone','7B827D','A1ADA4','4E5955','34383D')]:
    operations=[
        polygon([[5,9],[11,4],[28,4],[28,24],[23,28],[5,28]],edge),
        polygon([[6,9],[12,5],[27,5],[22,9]],light),
        rect(6,10,16,17,base),
        polygon([[23,10],[27,6],[27,23],[23,27]],shadow)]
    if name=='wood':
        operations += [rect(7,y,13,1,shadow) for y in (18,22,25)]
        operations += [rect(8,16,4,1,light),rect(15,20,5,1,light)]
    elif name=='metal':
        operations += [rect(8,15,2,11,light),rect(10,16,1,10,'A9BFCC'),rect(19,17,1,8,shadow)]
    else:
        operations += [polygon([[7,17],[12,17],[11,21],[7,20]],light),
                       polygon([[14,19],[20,18],[20,23],[16,24]],shadow),rect(9,25,5,1,light)]
    operations += [rect(6,13,16,1,edge),rect(13,12,3,4,edge),rect(14,13,1,2,light)]
    cells.append(dict(name=name,spec=dict(version=1,kind='draw',size=[32,32],operations=operations)))
spec=dict(version=1,kind='atlas',columns=3,cells=cells)
(RUN/'materials.json').write_text(json.dumps(spec),encoding='utf-8')
'''


def complete_fixture(work, run):
    run('start', '--platform', 'coordinator fixture', '--model', 'not external AI')
    (work/'RUN/author.py').write_text(AUTHOR, encoding='utf-8')
    run('script', 'RUN/author.py')
    run('tool', 'render', '--spec', 'RUN/materials.json', '--out', 'RUN/materials.png', '--metadata', 'RUN/layout.json')
    for theme, background in [('dark', '182637'), ('light', 'E9EDF2')]:
        for scale in (1, 8):
            run('tool', 'preview', '--image', 'RUN/materials.png', '--out', f'RUN/views/{theme}-{scale}x.png',
                '--background', background, '--scale', str(scale))
    (work/'RUN/feedback.md').write_text('Local engineering fixture; not an external usability or material-quality result.', encoding='utf-8')


class MaterialTrialTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='材质 trial space ')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        folder = ROOT/'skill/deterministic-pixel-art'
        files = {'deterministic-pixel-art/'+p.relative_to(folder).as_posix(): p.read_bytes()
                 for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
        self.skill_zip = self.root/'skill.zip'
        self.skill_zip.write_bytes(archive_bytes(files))
        self.digest = sha(self.skill_zip.read_bytes())
        self.out = self.root/'packet'
        self.record = build(self.skill_zip, self.out, self.digest)
        with zipfile.ZipFile(self.out/'LT06-Materials.zip') as bundle:
            bundle.extractall(self.root/'中文 extracted space')
        self.work = self.root/'中文 extracted space/LT06'

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
        self.assertEqual((self.out/'LT06-Materials.zip').read_bytes(), (self.root/'second/LT06-Materials.zip').read_bytes())
        with zipfile.ZipFile(self.out/'LT06-Materials.zip') as bundle, zipfile.ZipFile(self.skill_zip) as skill:
            expected = {'LT06/'+name for name in skill.namelist()} | {
                'LT06/'+name for name in ('START_HERE.md', 'run.py', 'recorder.py', 'task.json', 'checksums.json', 'inputs/brief.json')}
            self.assertEqual(set(bundle.namelist()), expected)
            for name in skill.namelist():
                self.assertEqual(skill.read(name), bundle.read('LT06/'+name))
            prompt = bundle.read('LT06/START_HERE.md').decode('utf-8')
            for phrase in ('MiMo', 'WorkBuddy', '协调', '32会话', '参考答案', 'GitHub', 'token'):
                self.assertNotIn(phrase, prompt)
            self.assertFalse(any('/coordinator/' in name or name.endswith('/author.py') for name in bundle.namelist()))
        with self.assertRaises(FileExistsError):
            build(self.skill_zip, self.out, self.digest)
        with self.assertRaisesRegex(ValueError, 'SHA-256'):
            build(self.skill_zip, self.root/'bad', '0'*64)
        self.assertFalse((self.root/'bad').exists())

    def test_recorded_chain_overwrite_refusal_and_submission(self):
        complete_fixture(self.work, self.run_recorder)
        self.run_recorder('check')
        self.assertTrue(self.checks()['passed'])
        self.assertEqual(len(self.checks()['checks']), 19)
        targets = [self.work/'RUN'/name for name in ('materials.png', 'layout.json')]
        digests = [sha(path.read_bytes()) for path in targets]
        self.run_recorder('tool', 'render', '--spec', 'RUN/materials.json', '--out', 'RUN/materials.png',
                          '--metadata', 'RUN/layout.json', expected=2)
        self.assertEqual([sha(path.read_bytes()) for path in targets], digests)
        records = [json.loads(line) for line in (self.work/'RUN/commands.jsonl').read_text(encoding='utf-8').splitlines()]
        self.assertEqual(len(records), 7)
        self.assertEqual(records[-1]['outputs_before'], records[-1]['outputs_after'])
        self.run_recorder('finish', '--status', 'complete')
        with zipfile.ZipFile(self.work/'submission-LT06.zip') as bundle:
            self.assertIn('RUN/author.py', bundle.namelist())
            self.assertIn('RUN/layout.json', bundle.namelist())
            self.assertNotIn('LT06/deterministic-pixel-art/SKILL.md', bundle.namelist())

    def test_alpha_drift_duplicate_cells_bad_layout_and_preview_are_detected(self):
        complete_fixture(self.work, self.run_recorder)
        target = self.work/'RUN/materials.png'
        original = target.read_bytes()
        with Image.open(target) as opened:
            image = opened.convert('RGBA')
        image.putpixel((32+15, 18), (1, 2, 3, 128))
        image.save(target)
        self.run_recorder('check', expected=1)
        failures = {item['check'] for item in self.checks()['checks'] if not item['passed']}
        self.assertIn('shared-pixel-alpha', failures)
        self.assertIn('editable-rerenders', failures)
        target.write_bytes(original)
        with Image.open(target) as opened:
            image = opened.convert('RGBA')
        for column in (1, 2):
            image.paste(image.crop((0, 0, 32, 32)), (column*32, 0))
        image.putpixel((32, 0), (17, 23, 31, 0))
        image.putpixel((64, 0), (50, 60, 70, 0))
        image.save(target)
        self.run_recorder('check', expected=1)
        failures = {item['check'] for item in self.checks()['checks'] if not item['passed']}
        self.assertIn('distinct-visible-materials', failures)
        self.assertNotIn('shared-pixel-alpha', failures)
        target.write_bytes(original)
        layout = self.work/'RUN/layout.json'
        original_layout = layout.read_bytes()
        record = json.loads(original_layout)
        record['atlas']['cells'][0]['name'] = 'incorrect'
        layout.write_text(json.dumps(record), encoding='utf-8')
        self.run_recorder('check', expected=1)
        self.assertIn('fresh-layout', {item['check'] for item in self.checks()['checks'] if not item['passed']})
        layout.write_bytes(original_layout)
        source = self.work/'RUN/materials.json'
        original_source = source.read_bytes()
        spec = json.loads(original_source)
        spec['cells'][0]['name'] = 'timber'
        source.write_text(json.dumps(spec), encoding='utf-8')
        self.run_recorder('check', expected=1)
        self.assertIn('named-native-cells', {item['check'] for item in self.checks()['checks'] if not item['passed']})
        source.write_bytes(original_source)
        preview = self.work/'RUN/views/dark-8x.png'
        original_preview = preview.read_bytes()
        with Image.open(preview) as opened:
            image = opened.convert('RGBA')
        image.putpixel((0, 0), (255, 0, 0, 255))
        image.save(preview)
        self.run_recorder('check', expected=1)
        self.assertIn('views/dark-8x.png-exact-preview', {item['check'] for item in self.checks()['checks'] if not item['passed']})
        preview.write_bytes(original_preview)
        log = self.work/'RUN/commands.jsonl'
        original_log = log.read_bytes()
        rows = [json.loads(line) for line in original_log.decode('utf-8').splitlines()]
        rows[0]['environment']['executable'] = 'other-interpreter'
        log.write_text(''.join(json.dumps(row)+'\n' for row in rows), encoding='utf-8')
        self.run_recorder('check', expected=1)
        self.assertIn('consistent-recorded-interpreter', {item['check'] for item in self.checks()['checks'] if not item['passed']})
        log.write_bytes(original_log)
        log.write_text(''.join(json.dumps(row)+'\n' for row in rows if row['arguments'][1:2] != ['preview']), encoding='utf-8')
        self.run_recorder('check', expected=1)
        self.assertIn('final-previews-recorded', {item['check'] for item in self.checks()['checks'] if not item['passed']})
        log.write_bytes(original_log)
        self.run_recorder('check')

    def test_incomplete_archival_and_frozen_inputs(self):
        self.run_recorder('start', '--platform', 'fixture', '--model', 'unknown')
        self.run_recorder('finish', '--status', 'quota_limited', expected=1)
        self.assertTrue((self.work/'submission-LT06.zip').is_file())
        self.assertFalse(self.checks()['passed'])
        (self.work/'inputs/brief.json').write_text('{}', encoding='utf-8')
        result = self.run_recorder('check', expected=2)
        self.assertIn('Frozen task/Skill changed', result.stderr)


if __name__ == '__main__':
    unittest.main()
