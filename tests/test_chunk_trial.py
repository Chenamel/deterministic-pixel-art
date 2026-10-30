"""LT08 engineering fixtures are never shipped to the evaluated model."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from build_chunk_trial import build
from prepare_agent_trials import archive_bytes,sha

COMMON='''from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
C=json.loads((ROOT/'contract.json').read_text(encoding='utf-8'))
P=C['palette']
def rect(s,x,y,w,h,c):
 x0=max(0,x);y0=max(0,y);x1=min(128,x+w);y1=min(128,y+h)
 if x1>x0 and y1>y0:s['operations'].append(dict(op='rect',x=x0,y=y0,w=x1-x0,h=y1-y0,color=c))
def water(s,ox,oy):
 rect(s,104-ox,-oy,48,256,P['water'])
 for y in range(0,256,10):rect(s,104-ox,y-oy,48,1,P['wave'])
def walkway(s,ox,oy):
 rect(s,-ox,112-oy,256,24,P['rail']);rect(s,-ox,113-oy,256,22,P['plank'])
 for x in range(0,256,6):rect(s,x-ox,113-oy,1,22,P['joint'])
def create(name):
 owner=next(o for o in C['owners'] if o['name']==name);ox,oy=owner['rect'][:2]
 s=dict(version=1,kind='draw',size=[128,128],background='567F55',operations=[])
 for y in range(7,128,19):
  for x in range(6,128,23):rect(s,x,y,3,1,'6F945F')
 water(s,ox,oy);walkway(s,ox,oy)
 return s
'''
DETAILS={
'nw':"rect(s,22,48,42,32,'B18B65');rect(s,18,30,50,20,'704942');rect(s,38,64,10,16,'463D3A');rect(s,28,55,6,6,'9DC4CA')",
'ne':"rect(s,70,28,3,30,P['joint']);rect(s,62,24,20,12,P['plank']);rect(s,65,29,12,2,P['rail'])",
'sw':"rect(s,23,37,17,11,'A4A59A');rect(s,26,35,12,3,'C4C5B5');rect(s,45,50,8,6,'858D84')",
'se':"rect(s,66,38,2,23,P['rail']);rect(s,68,40,8,5,args.flag);rect(s,62,60,12,2,P['joint'])"}

def setup_sources(work):
    run=work/'RUN';src=run/'src';src.mkdir()
    brief=json.loads((work/'inputs/brief.json').read_text(encoding='utf-8'))
    contract=dict(version=1,size=brief['size'],owners=brief['owners'],palette=dict(water='3F8195',wave='92CED6',plank='D4B07B',joint='805A38',rail='493C33'))
    (run/'contract.json').write_text(json.dumps(contract),encoding='utf-8')
    (src/'common.py').write_text(COMMON,encoding='utf-8')
    for name,detail in DETAILS.items():
        source="from common import create,rect,P\nimport argparse,json\nfrom pathlib import Path\np=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--flag',default='F5C26B');args=p.parse_args()\ns=create("+repr(name)+")\n"+detail+"\nout=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(s),encoding='utf-8')\n"
        (src/(name+'.py')).write_text(source,encoding='utf-8')
    project=dict(version=1,size=brief['size'],require_coverage=True,parts=[dict(name=o['name'],image='chunks/'+o['name']+'.png',at=o['rect'][:2],mode='copy') for o in brief['owners']])
    (run/'v1').mkdir();(run/'v1/project.json').write_text(json.dumps(project),encoding='utf-8')
    (run/'snapshot.py').write_text("from pathlib import Path\nimport shutil\nr=Path(__file__).resolve().parent\nshutil.copytree(r/'src',r/'v1/source')\n",encoding='utf-8')
    (run/'copy_v2.py').write_text("from pathlib import Path\nimport shutil\nr=Path(__file__).resolve().parent\n(r/'v2/chunks').mkdir(parents=True)\nfor n in ('nw','ne','sw'):\n for ext in ('.json','.png'):shutil.copyfile(r/'v1/chunks'/(n+ext),r/'v2/chunks'/(n+ext))\nshutil.copyfile(r/'v1/project.json',r/'v2/project.json')\n",encoding='utf-8')

def assemble(run,version):
    run('tool','assemble','--project',f'RUN/{version}/project.json','--out',f'RUN/{version}/scene.png',
        '--report',f'RUN/{version}/assembly.json','--seams',f'RUN/{version}/seams.png','--preview',f'RUN/{version}/scene-2x.png','--scale','2')

def complete_fixture(work,run):
    run('start','--platform','coordinator fixture','--model','not external AI')
    setup_sources(work)
    for name in ('nw','ne','sw','se'):
        run('script',f'RUN/src/{name}.py','--out',f'RUN/v1/chunks/{name}.json')
        run('tool','render','--spec',f'RUN/v1/chunks/{name}.json','--out',f'RUN/v1/chunks/{name}.png')
    assemble(run,'v1');run('script','RUN/snapshot.py');run('script','RUN/copy_v2.py')
    run('script','RUN/src/se.py','--out','RUN/v2/chunks/se.json','--flag','62D8E8')
    run('tool','render','--spec','RUN/v2/chunks/se.json','--out','RUN/v2/chunks/se.png')
    assemble(run,'v2')
    run('tool','verify','--image','RUN/v2/scene.png','--compare','RUN/v1/scene.png','--allow-region','196','168','8','5','--out','RUN/change.json')
    (work/'RUN/feedback.md').write_text('Local final-ZIP engineering fixture. No external, multi-agent or aesthetic acceptance.',encoding='utf-8')

class ChunkTrialTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory(prefix='分块 trial space ');self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name)
        folder=ROOT/'skill/deterministic-pixel-art'
        files={'deterministic-pixel-art/'+p.relative_to(folder).as_posix():p.read_bytes()
               for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
        self.skill_zip=self.root/'skill.zip';self.skill_zip.write_bytes(archive_bytes(files))
        self.digest=sha(self.skill_zip.read_bytes());self.out=self.root/'packet'
        self.record=build(self.skill_zip,self.out,self.digest)
        with zipfile.ZipFile(self.out/'LT08-Chunks.zip') as z:z.extractall(self.root/'中文 extracted space')
        self.work=self.root/'中文 extracted space/LT08'
    def run_recorder(self,*args,expected=0):
        env={k:v for k,v in os.environ.items() if k not in ('PYTHONPATH','PYTHONHOME')};env.update(PIXELART_PORTABLE_OUTPUT='1',PYTHONIOENCODING='utf-8')
        result=subprocess.run([sys.executable,'-B',str(self.work/'run.py'),*map(str,args)],cwd=self.root,env=env,capture_output=True,text=True,encoding='utf-8',timeout=45)
        self.assertEqual(result.returncode,expected,result.stdout+result.stderr);return result
    def checks(self):return json.loads((self.work/'RUN/checks.json').read_text(encoding='utf-8'))
    def failures(self):return {x['check'] for x in self.checks()['checks'] if not x['passed']}
    def test_exact_reproducible_packet(self):
        self.assertEqual(build(self.skill_zip,self.root/'second',self.digest),self.record)
        self.assertEqual((self.out/'LT08-Chunks.zip').read_bytes(),(self.root/'second/LT08-Chunks.zip').read_bytes())
        with zipfile.ZipFile(self.out/'LT08-Chunks.zip') as packet,zipfile.ZipFile(self.skill_zip) as skill:
            self.assertEqual(set(packet.namelist()),{'LT08/'+n for n in skill.namelist()}|{'LT08/'+n for n in ('START_HERE.md','run.py','recorder.py','task.json','checksums.json','inputs/brief.json')})
            for n in skill.namelist():self.assertEqual(packet.read('LT08/'+n),skill.read(n))
            self.assertEqual(packet.read('LT08/recorder.py'),(ROOT/'benchmarks/long-term/runner.py').read_bytes())
        with self.assertRaises(FileExistsError):build(self.skill_zip,self.out,self.digest)
        with self.assertRaisesRegex(ValueError,'SHA-256'):build(self.skill_zip,self.root/'bad','0'*64)
        self.assertFalse((self.root/'bad').exists())
    def test_full_chain_boundary_refusal_and_archive(self):
        complete_fixture(self.work,self.run_recorder);self.run_recorder('check')
        self.assertTrue(self.checks()['passed']);self.assertEqual(len(self.checks()['checks']),63)
        change=json.loads((self.work/'RUN/change.json').read_text(encoding='utf-8'));self.assertEqual(change['changed_rgba_pixels'],40);self.assertEqual(change['changed_outside'],0)
        files=[self.work/'RUN/v2'/n for n in ('scene.png','assembly.json','seams.png','scene-2x.png')];old=[sha(p.read_bytes()) for p in files]
        self.run_recorder('tool','assemble','--project','RUN/v2/project.json','--out','RUN/v2/scene.png','--report','RUN/v2/assembly.json','--seams','RUN/v2/seams.png','--preview','RUN/v2/scene-2x.png',expected=2)
        self.assertEqual(old,[sha(p.read_bytes()) for p in files]);self.run_recorder('finish','--status','complete')
        with zipfile.ZipFile(self.work/'submission-LT08.zip') as z:
            self.assertIn('RUN/v1/source/nw.py',z.namelist());self.assertIn('RUN/src/se.py',z.namelist());self.assertFalse(any('/deterministic-pixel-art/' in n for n in z.namelist()))
    def test_phase_edit_source_and_freeze_failures(self):
        complete_fixture(self.work,self.run_recorder)
        for filename,at,ink,failure in [
            ('v1/scene.png',(128,127),(128,90,56,255),'v1-plank-phase'),
            ('v1/scene.png',(120,140),(63,129,149,255),'v1-water-phase'),
            ('v1/scene.png',(127,112),(1,2,3,255),'v1-rail-crossings'),
            ('v2/scene.png',(10,10),(255,0,0,255),'only-flag-changed'),
            ('v2/scene-2x.png',(0,0),(1,2,3,255),'v2-preview')]:
            with self.subTest(filename=filename,failure=failure):
                p=self.work/'RUN'/filename;old=p.read_bytes()
                with Image.open(p) as opened:im=opened.convert('RGBA')
                im.putpixel(at,ink);im.save(p);self.run_recorder('check',expected=1);self.assertIn(failure,self.failures());p.write_bytes(old)
        p=self.work/'RUN/v2/chunks/nw.json';old=p.read_bytes();p.write_bytes(old+b'\n');self.run_recorder('check',expected=1);self.assertIn('unchanged-nw.json',self.failures());p.write_bytes(old)
        p=self.work/'RUN/contract.json';old=p.read_bytes();data=json.loads(old);data['palette']['wave']=data['palette']['water'];p.write_text(json.dumps(data),encoding='utf-8');self.run_recorder('check',expected=1);self.assertIn('shared-contract',self.failures());p.write_bytes(old)
        p=self.work/'RUN/v1/source/nw.py';old=p.read_bytes();p.write_text('# replaced source',encoding='utf-8');self.run_recorder('check',expected=1);self.assertIn('owner-source-nw',self.failures());p.write_bytes(old)
        p=self.work/'RUN/commands.jsonl';old=p.read_bytes();rows=[json.loads(l) for l in old.decode('utf-8').splitlines()]
        first=next(r for r in rows if any(n.startswith('v2/') for n in r['outputs_after']))
        first['outputs_before'].pop('v1/scene.png');p.write_text(''.join(json.dumps(r)+'\n' for r in rows),encoding='utf-8')
        self.run_recorder('check',expected=1);self.assertIn('v1-frozen-before-v2',self.failures());p.write_bytes(old)
        p.write_text(''.join(json.dumps(r)+'\n' for r in rows if r['arguments'][1:2]!=['verify']),encoding='utf-8');self.run_recorder('check',expected=1);self.assertIn('verify-recorded',self.failures());p.write_bytes(old)
        self.run_recorder('check')
    def test_incomplete_and_frozen_input(self):
        self.run_recorder('start','--platform','fixture','--model','unknown');self.run_recorder('finish','--status','quota_limited',expected=1)
        self.assertTrue((self.work/'submission-LT08.zip').is_file());self.assertFalse(self.checks()['passed'])
        (self.work/'inputs/brief.json').write_text('{}',encoding='utf-8');result=self.run_recorder('check',expected=2);self.assertIn('Frozen task/Skill changed',result.stderr)

if __name__=='__main__':unittest.main()
