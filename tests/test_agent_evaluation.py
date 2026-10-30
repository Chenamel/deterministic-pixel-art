import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from PIL import Image
from pixelart import image_to_spec
from tools.build_agent_eval import fixtures
from tools.evaluate_agent_results import evaluate

ROOT=Path(__file__).resolve().parents[1]


def save(path,data):path.write_text(json.dumps(data),encoding='utf-8')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


class EvaluationTests(unittest.TestCase):
    def test_eight_controlled_fixtures_only_change_the_declared_region(self):
        cases=fixtures();self.assertEqual(len(cases),8)
        for case in cases:
            x,y,w,h=case['box'];changed=[]
            for yy in range(case['image'].height):
                for xx in range(case['image'].width):
                    if case['image'].getpixel((xx,yy))!=case['expected'].getpixel((xx,yy)):
                        changed.append((xx,yy));self.assertTrue(x<=xx<x+w and y<=yy<y+h)
            self.assertTrue(changed,case['id'])

    def test_empty_evidence_cannot_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);manifest=root/'manifest.json'
            save(manifest,dict(tasks=[],key={}))
            result=evaluate(manifest,root/'missing')
            self.assertFalse(result['stable_release_gate_passed']);self.assertEqual(result['external_runs'],0)

    def test_gate_requires_complete_pairs_reviews_and_frozen_artifacts(self):
        # Synthetic unit data only; never included in release evidence.
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);truth=root/'expected';truth.mkdir();runs=root/'runs';runs.mkdir()
            image=Image.new('RGBA',(3,3));image.putpixel((1,1),(1,2,3,255))
            tasks=[];reviews=[]
            for n in range(8):
                task=f'task-{n}';expected=truth/f'{task}.png';image.save(expected)
                tasks.append(dict(id=task,localization_rect=[1,1,1,1],expected_sha256=sha(expected)))
                for mode in ('text_only','multimodal'):
                    for candidate in (False,True):
                        folder=runs/f'{mode}-{task}-{candidate}';folder.mkdir()
                        image.save(folder/'final.png');save(folder/'final.json',image_to_spec(image))
                        save(folder/'localization.json',dict(regions=[[1,1,1,1]]))
                        command=dict(seconds=.01,localization_sha256=sha(folder/'localization.json'))
                        (folder/'commands.jsonl').write_text(json.dumps(command)+'\n')
                        artifacts={p.name:sha(p) for p in folder.iterdir()}
                        save(folder/'run.json',dict(task=task,package='B' if candidate else 'A',
                            package_sha256='new' if candidate else 'old',environment=mode,mode=mode,model='synthetic',
                            python='3',pillow='12.3',platform='synthetic',shim=False,finished_at='unit-test',
                            candidates=1,revisions=0 if candidate else 1,artifacts=artifacts))
                        if candidate:reviews.append(dict(task=task,environment=mode,final_sha256=sha(folder/'final.png'),
                            critical_regression=False,notes='synthetic unit fixture'))
            manifest=root/'manifest.json';save(manifest,dict(tasks=tasks,key=dict(candidate_label='B',baseline_label='A',
                candidate_sha256='new',baseline_sha256='old')))
            visual=root/'visual.json';save(visual,dict(reviewer='synthetic-test',type='independent_agent',cases=reviews))
            self.assertFalse(evaluate(manifest,runs)['stable_release_gate_passed'])
            self.assertTrue(evaluate(manifest,runs,visual)['stable_release_gate_passed'])
            victim=next(runs.glob('*/final.png'));victim.write_bytes(b'tampered')
            self.assertFalse(evaluate(manifest,runs,visual)['stable_release_gate_passed'])

    def test_runner_records_an_actual_child_command(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);package=root/'package.zip';package.write_bytes(b'unit-package');out=root/'run'
            runner=ROOT/'benchmarks/runner.py'
            def run(*args):return subprocess.run([sys.executable,'-B',str(runner),*map(str,args)],capture_output=True,timeout=15)
            self.assertEqual(run('start','--out',out,'--task','test','--package','A','--package-zip',package,
                '--environment','unit','--mode','text_only','--model','synthetic').returncode,0)
            save(out/'localization.json',dict(regions=[]))
            self.assertEqual(run('run','--out',out,'--',sys.executable,'-c','print("actual child output")').returncode,0)
            self.assertEqual(run('finish','--out',out,'--candidates',1,'--revisions',0,'--failure-stage','repair').returncode,0)
            data=json.loads((out/'run.json').read_text());self.assertIsNone(data['tokens_total'])
            self.assertIn('commands.jsonl',data['artifacts'])
            self.assertIn('actual child output',(out/'001.stdout.txt').read_text())
