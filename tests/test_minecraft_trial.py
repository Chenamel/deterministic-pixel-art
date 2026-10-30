"""Exercise LT07 packet integrity, actual commands and failed artifact contracts."""
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
from build_minecraft_trial import build
from prepare_agent_trials import archive_bytes,sha

AUTHOR='''from pathlib import Path
import json
RUN=Path(__file__).resolve().parent
def save(name,value):
 p=RUN/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value),encoding='utf-8')
def rect(x,y,w,h,c):return dict(op='rect',x=x,y=y,w=w,h=h,color=c)
def draw(size,operations,**kw):return dict(version=1,kind='draw',size=size,operations=operations,**kw)
body=[rect(0,0,176,2,'373737'),rect(0,0,2,80,'373737'),rect(174,0,2,80,'373737'),
 rect(2,2,172,1,'FFFFFF'),rect(2,3,1,77,'FFFFFF'),rect(173,3,1,77,'555555')]
for y in (22,40,58):
 for x in (8,26,44):body.append(dict(op='slot',x=x,y=y))
save('panel/body.json',draw([176,80],body,background='C6C6C6',preset='minecraft'))
footer=[rect(0,0,2,32,'373737'),rect(174,0,2,32,'373737'),rect(2,0,1,30,'FFFFFF'),
 rect(173,0,1,30,'555555'),rect(0,30,176,2,'373737'),rect(2,29,172,1,'555555')]
save('panel/footer.json',draw([176,32],footer,background='C6C6C6'))
cells=[]
for state in ('normal','hover','pressed','disabled'):
 shift=int(state=='pressed');ink='ADADAD' if state=='disabled' else 'FFFFFF'
 operations=[dict(op='button',x=0,y=0,w=40,h=16,state=state.upper()),
  rect(12,7+shift,12,2,ink),dict(op='polygon',points=[[22,4+shift],[27,8+shift],[22,11+shift]],color=ink)]
 cells.append(dict(name=state,spec=draw([40,16],operations,preset='minecraft')))
save('buttons.json',dict(version=1,kind='atlas',columns=4,cells=cells))
brief=json.loads((RUN.parent/'inputs/brief.json').read_text(encoding='utf-8'))
save('scene.json',dict(version=1,size=brief['scene_size'],require_coverage=True,parts=brief['parts']))
'''


def complete_fixture(work,run):
    run('start','--platform','coordinator fixture','--model','not external AI')
    (work/'RUN/author.py').write_text(AUTHOR,encoding='utf-8')
    run('script','RUN/author.py')
    for name in ('panel/body','panel/footer','buttons'):
        args=['tool','render','--spec',f'RUN/{name}.json','--out',f'RUN/{name}.png']
        if name=='buttons':args+=['--metadata','RUN/layout.json']
        run(*args)
    run('tool','assemble','--project','RUN/scene.json','--out','RUN/scene.png',
        '--report','RUN/assembly.json','--seams','RUN/seams.png')
    for name in ('scene','buttons'):
        for theme,bg in [('dark','182637'),('light','E9EDF2')]:
            for scale in (1,4):
                run('tool','preview','--image',f'RUN/{name}.png',
                    '--out',f'RUN/views/{name}-{theme}-{scale}x.png','--background',bg,'--scale',str(scale))
    (work/'RUN/feedback.md').write_text('Local command fixture only. No external usability or in-game acceptance.',encoding='utf-8')


class MinecraftTrialTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory(prefix='界面 trial space ')
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
        with zipfile.ZipFile(self.out/'LT07-Minecraft.zip') as bundle:
            bundle.extractall(self.root/'中文 extracted space')
        self.work=self.root/'中文 extracted space/LT07'

    def run_recorder(self,*args,expected=0):
        env={k:v for k,v in os.environ.items() if k not in ('PYTHONPATH','PYTHONHOME')}
        env.update(PIXELART_PORTABLE_OUTPUT='1',PYTHONIOENCODING='utf-8')
        result=subprocess.run([sys.executable,'-B',str(self.work/'run.py'),*map(str,args)],cwd=self.root,
            env=env,capture_output=True,text=True,encoding='utf-8',timeout=30)
        self.assertEqual(result.returncode,expected,result.stdout+result.stderr)
        return result

    def checks(self):return json.loads((self.work/'RUN/checks.json').read_text(encoding='utf-8'))
    def failures(self):return {c['check'] for c in self.checks()['checks'] if not c['passed']}

    def test_exact_reproducible_packet_and_reject_existing_or_wrong_hash(self):
        self.assertEqual(build(self.skill_zip,self.root/'again',self.digest),self.record)
        self.assertEqual((self.out/'LT07-Minecraft.zip').read_bytes(),(self.root/'again/LT07-Minecraft.zip').read_bytes())
        with zipfile.ZipFile(self.out/'LT07-Minecraft.zip') as packet,zipfile.ZipFile(self.skill_zip) as skill:
            self.assertEqual(set(packet.namelist()),{'LT07/'+n for n in skill.namelist()}|{
                'LT07/'+n for n in ('START_HERE.md','run.py','recorder.py','task.json','checksums.json','inputs/brief.json')})
            for n in skill.namelist():self.assertEqual(packet.read('LT07/'+n),skill.read(n))
            self.assertEqual(packet.read('LT07/recorder.py'),(ROOT/'benchmarks/long-term/runner.py').read_bytes())
        with self.assertRaises(FileExistsError):build(self.skill_zip,self.out,self.digest)
        with self.assertRaisesRegex(ValueError,'SHA-256'):build(self.skill_zip,self.root/'bad','0'*64)
        self.assertFalse((self.root/'bad').exists())

    def test_recorded_chain_refusal_and_submission(self):
        complete_fixture(self.work,self.run_recorder)
        self.run_recorder('check')
        self.assertTrue(self.checks()['passed'])
        self.assertEqual(len(self.checks()['checks']),35)
        paths=[self.work/'RUN'/p for p in ('scene.png','assembly.json','seams.png')]
        old=[sha(p.read_bytes()) for p in paths]
        self.run_recorder('tool','assemble','--project','RUN/scene.json','--out','RUN/scene.png',
            '--report','RUN/assembly.json','--seams','RUN/seams.png',expected=2)
        self.assertEqual([sha(p.read_bytes()) for p in paths],old)
        rows=[json.loads(l) for l in (self.work/'RUN/commands.jsonl').read_text(encoding='utf-8').splitlines()]
        self.assertEqual(len(rows),14)
        self.assertEqual(rows[-1]['outputs_before'],rows[-1]['outputs_after'])
        self.run_recorder('finish','--status','complete')
        with zipfile.ZipFile(self.work/'submission-LT07.zip') as bundle:
            self.assertIn('RUN/author.py',bundle.namelist())
            self.assertIn('RUN/scene.json',bundle.namelist())
            self.assertFalse(any('/deterministic-pixel-art/' in n for n in bundle.namelist()))

    def test_pixel_layout_placement_views_and_recording_drift(self):
        complete_fixture(self.work,self.run_recorder)
        targets=[('scene.png','scene-assembled-exactly'),('seams.png','seam-view-exact'),
                 ('views/buttons-light-4x.png','views/buttons-light-4x.png-exact-preview')]
        for filename,failure in targets:
            with self.subTest(filename=filename):
                p=self.work/'RUN'/filename;old=p.read_bytes()
                with Image.open(p) as opened:im=opened.convert('RGBA')
                im.putpixel((0,0),(255,0,0,128));im.save(p)
                self.run_recorder('check',expected=1);self.assertIn(failure,self.failures());p.write_bytes(old)
        p=self.work/'RUN/panel/footer.png';old=p.read_bytes()
        with Image.open(p) as opened:im=opened.convert('RGBA')
        im.putpixel((80,0),(0,0,0,0));im.save(p)
        self.run_recorder('check',expected=1);self.assertIn('panel/footer-alpha',self.failures());p.write_bytes(old)
        p=self.work/'RUN/layout.json';old=p.read_bytes();data=json.loads(old)
        data['atlas']['cells'][0]['name']='wrong';p.write_text(json.dumps(data),encoding='utf-8')
        self.run_recorder('check',expected=1);self.assertIn('fresh-layout',self.failures());p.write_bytes(old)
        p=self.work/'RUN/scene.json';old=p.read_bytes();data=json.loads(old)
        data['parts'][-1]['at'][0]+=1;p.write_text(json.dumps(data),encoding='utf-8')
        self.run_recorder('check',expected=1);self.assertIn('consumer-project',self.failures());p.write_bytes(old)
        p=self.work/'RUN/buttons.json';old=p.read_bytes();data=json.loads(old)
        data['cells'][1]['name']='highlight';p.write_text(json.dumps(data),encoding='utf-8')
        self.run_recorder('check',expected=1);self.assertIn('named-states',self.failures());p.write_bytes(old)
        p=self.work/'RUN/buttons.png';old=p.read_bytes()
        with Image.open(p) as opened:im=opened.convert('RGBA')
        for x in (40,80,120):im.paste(im.crop((0,0,40,16)),(x,0))
        im.save(p);self.run_recorder('check',expected=1)
        self.assertIn('distinct-visible-states',self.failures());p.write_bytes(old)
        p=self.work/'RUN/commands.jsonl';old=p.read_bytes()
        rows=[json.loads(line) for line in old.decode('utf-8').splitlines()]
        rows[0]['environment']['executable']='another interpreter'
        p.write_text(''.join(json.dumps(row)+'\n' for row in rows),encoding='utf-8')
        self.run_recorder('check',expected=1);self.assertIn('consistent-recorded-interpreter',self.failures())
        p.write_text(''.join(json.dumps(row)+'\n' for row in rows if row['arguments'][1:2]!=['assemble']),encoding='utf-8')
        self.run_recorder('check',expected=1);self.assertIn('assembly-recorded',self.failures());p.write_bytes(old)
        self.run_recorder('check')

    def test_incomplete_archive_and_frozen_input(self):
        self.run_recorder('start','--platform','fixture','--model','undisclosed')
        self.run_recorder('finish','--status','quota_limited',expected=1)
        self.assertTrue((self.work/'submission-LT07.zip').is_file())
        self.assertFalse(self.checks()['passed'])
        (self.work/'inputs/brief.json').write_text('{}',encoding='utf-8')
        result=self.run_recorder('check',expected=2)
        self.assertIn('Frozen task/Skill changed',result.stderr)


if __name__=='__main__':unittest.main()
