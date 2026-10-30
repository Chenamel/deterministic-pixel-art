"""Task-only distribution and real recorded execution; no external AI results."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from build_icon_trial import build
from prepare_agent_trials import archive_bytes,sha

# Coordinator-only fixture: never packaged or shown as the expected creative answer.
AUTHOR = '''import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'RUN'
def save(name,value):
    path=RUN/name;path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value),encoding='utf-8')
def line(points,color='DCE6EE'):return dict(op='line',points=points,color=color)
def rect(x,y,w,h,color='DCE6EE'):return dict(op='rect',x=x,y=y,w=w,h=h,color=color)
def draw(size,ops):return dict(kind='draw',size=[size,size],operations=ops)
if sys.argv[1]=='v1':
    up=[(3,5),(5,3),(6,3),(8,5)]
    ops=[line(up),rect(5,4,2,5)]
    cells=[]
    transforms=[lambda x,y:(x,y),lambda x,y:(x,11-y),lambda x,y:(y,x),lambda x,y:(11-y,x)]
    for name,transform in zip(('up','down','left','right'),transforms):
        points=set()
        # Convert the local reference arrow to explicit native-grid points.
        from PIL import Image,ImageDraw
        image=Image.new('RGBA',(12,12));pen=ImageDraw.Draw(image)
        pen.line(up,fill='#DCE6EE');pen.rectangle((5,4,6,8),fill='#DCE6EE')
        points=[list(transform(x,y)) for y in range(12) for x in range(12) if image.getpixel((x,y))[3]]
        cells.append(dict(name=name,spec=draw(12,[dict(op='points',points=points,color='DCE6EE')])))
    save('v1/directions.json',dict(kind='atlas',columns=4,cells=cells))
    bag=[rect(4,5,8,8),rect(6,3,4,2),rect(6,8,4,3,'4BAEBE')]
    map_ops=[line([(3,4),(6,3),(9,4),(12,3),(12,11),(9,12),(6,11),(3,12),(3,4)]),
             line([(6,4),(6,10)]),line([(9,5),(9,11)])]
    settings=[rect(6,2,4,12),rect(2,6,12,4),rect(4,4,8,8),rect(6,6,4,4,'4BAEBE')]
    close=[line([(4,4),(11,11)]),line([(11,4),(4,11)])]
    cells=[dict(name=name,spec=draw(16,ops)) for name,ops in
           [('bag',bag),('map',map_ops),('settings',settings),('close',close)]]
    save('v1/actions.json',dict(kind='atlas',columns=4,cells=cells))
else:
    spec=json.loads((RUN/'v1/actions.json').read_text(encoding='utf-8'))
    spec['cells'][1]['spec']['operations'] += [rect(8,5,3,3,'E4BB6B'),
        dict(op='points',points=[[9,8],[9,9]],color='E4BB6B')]
    save('v2/actions.json',spec)
'''


def complete_fixture(work,run):
    run('start','--platform','coordinator fixture','--model','not external AI')
    (work/'RUN/author.py').write_text(AUTHOR,encoding='utf-8')
    (work/'RUN/feedback.md').write_text('Local engineering fixture, not external feedback or aesthetic acceptance.',encoding='utf-8')
    run('script','RUN/author.py','v1')
    for group in ('directions','actions'):
        run('tool','render','--spec',f'RUN/v1/{group}.json','--out',f'RUN/v1/{group}.png',
            '--metadata',f'RUN/v1/{group}-layout.json')
    run('script','RUN/author.py','v2')
    run('tool','render','--spec','RUN/v2/actions.json','--out','RUN/v2/actions.png','--metadata','RUN/v2/actions-layout.json')
    run('tool','verify','--image','RUN/v2/actions.png','--compare','RUN/v1/actions.png',
        '--allow-region','16','0','16','16','--out','RUN/change.json')
    for group,stage in [('directions','v1'),('actions','v2')]:
        for background,color in [('dark','182637'),('light','E9EDF2')]:
            for scale in (1,8):
                run('tool','preview','--image',f'RUN/{stage}/{group}.png',
                    '--out',f'RUN/views/{group}-{background}-{scale}x.png',
                    '--background',color,'--scale',str(scale))


class IconTrialTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory(prefix='图标 trial space ')
        self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name)
        folder=ROOT/'skill/deterministic-pixel-art'
        files={'deterministic-pixel-art/'+p.relative_to(folder).as_posix():p.read_bytes()
               for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
        self.skill_zip=self.root/'skill.zip'
        self.skill_zip.write_bytes(archive_bytes(files))
        self.digest=sha(self.skill_zip.read_bytes())
        self.out=self.root/'packet'
        self.record=build(self.skill_zip,self.out,self.digest)
        with zipfile.ZipFile(self.out/'LT04-Icons.zip') as bundle:
            bundle.extractall(self.root/'中文 extracted space')
        self.work=self.root/'中文 extracted space/LT04'

    def run_recorder(self,*args,expected=0):
        env={k:v for k,v in os.environ.items() if k not in ('PYTHONPATH','PYTHONHOME')}
        env.update(PIXELART_PORTABLE_OUTPUT='1',PYTHONIOENCODING='utf-8')
        result=subprocess.run([sys.executable,'-B',str(self.work/'run.py'),*map(str,args)],cwd=self.root,
            env=env,capture_output=True,text=True,encoding='utf-8',timeout=30)
        self.assertEqual(result.returncode,expected,result.stdout+result.stderr)
        return result

    def checks(self):return json.loads((self.work/'RUN/checks.json').read_text(encoding='utf-8'))

    def test_packet_reproducible_exact_skill_and_no_solution_or_coordinator_leak(self):
        record=build(self.skill_zip,self.root/'second',self.digest)
        self.assertEqual(record,self.record)
        self.assertEqual((self.out/'LT04-Icons.zip').read_bytes(),(self.root/'second/LT04-Icons.zip').read_bytes())
        with zipfile.ZipFile(self.out/'LT04-Icons.zip') as bundle,zipfile.ZipFile(self.skill_zip) as skill:
            expected={f'LT04/{name}' for name in skill.namelist()}|{
                f'LT04/{name}' for name in ('START_HERE.md','run.py','recorder.py','task.json','checksums.json','inputs/brief.json')}
            self.assertEqual(set(bundle.namelist()),expected)
            for name in skill.namelist():self.assertEqual(skill.read(name),bundle.read('LT04/'+name))
            prompt=bundle.read('LT04/START_HERE.md').decode('utf-8')
            for private in ('Hy3','Space-Bunny','131','32会话','GitHub','验收后删除','参考答案'):
                self.assertNotIn(private,prompt)
            self.assertFalse(any('author.py' in n or '/coordinator/' in n for n in bundle.namelist()))
        with self.assertRaises(FileExistsError):build(self.skill_zip,self.out,self.digest)
        with self.assertRaisesRegex(ValueError,'SHA-256'):
            build(self.skill_zip,self.root/'bad','0'*64)
        self.assertFalse((self.root/'bad').exists())

    def test_real_recorded_chain_preserves_stage_then_rejects_corrupt_artifacts(self):
        complete_fixture(self.work,self.run_recorder)
        self.run_recorder('check')
        self.assertTrue(self.checks()['passed'])
        records=[json.loads(line) for line in (self.work/'RUN/commands.jsonl').read_text(encoding='utf-8').splitlines()]
        self.assertEqual(len(records),14)
        self.assertTrue(all(r['environment']['portable_output_setting']=='1' for r in records))
        source=self.work/'RUN/v2/actions.png';original=source.read_bytes()
        with Image.open(source) as opened:image=opened.copy()
        image.putpixel((5,5),(255,0,0,255));image.save(source)
        self.run_recorder('check',expected=1)
        failed={c['check'] for c in self.checks()['checks'] if not c['passed']}
        self.assertIn('only-map-changed',failed)
        self.assertIn('v2/actions-editable-rerenders',failed)
        source.write_bytes(original)
        layout=self.work/'RUN/v2/actions-layout.json';original_layout=layout.read_bytes()
        record=json.loads(original_layout);record['rgba_sha256']='0'*64
        layout.write_text(json.dumps(record),encoding='utf-8')
        self.run_recorder('check',expected=1)
        self.assertIn('v2/actions-fresh-layout',{c['check'] for c in self.checks()['checks'] if not c['passed']})
        layout.write_bytes(original_layout)
        self.run_recorder('tool','render','--spec','RUN/v2/actions.json','--out','RUN/v2/actions.png',expected=2)
        self.assertEqual(source.read_bytes(),original)
        self.run_recorder('finish','--status','complete')
        with zipfile.ZipFile(self.work/'submission-LT04.zip') as bundle:
            self.assertIn('RUN/author.py',bundle.namelist())
            self.assertNotIn('LT04/deterministic-pixel-art/SKILL.md',bundle.namelist())

    def test_incomplete_run_can_be_archived_but_cannot_pass_or_modify_frozen_files(self):
        self.run_recorder('start','--platform','fixture','--model','unknown')
        self.run_recorder('finish','--status','quota_limited',expected=1)
        self.assertTrue((self.work/'submission-LT04.zip').exists())
        self.assertFalse(self.checks()['passed'])
        self.run_recorder('check',expected=2)
        brief=self.work/'inputs/brief.json'
        brief.write_text('{}',encoding='utf-8')
        result=self.run_recorder('check',expected=2)
        self.assertIn('Frozen task/Skill changed',result.stderr)


if __name__=='__main__':unittest.main()
