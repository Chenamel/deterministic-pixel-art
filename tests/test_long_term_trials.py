"""Real extracted-trial tests; these are recorder checks, never external model results."""
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from build_long_term_trials import build
from prepare_agent_trials import archive_bytes,sha


class LongTermTrialsTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix='长期 中文 trial space ')
        self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name)
        skill=ROOT/'skill/deterministic-pixel-art'
        self.files={'deterministic-pixel-art/'+p.relative_to(skill).as_posix():p.read_bytes()
                    for p in skill.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
        self.skill_zip=self.root/'skill.zip';self.skill_zip.write_bytes(archive_bytes(self.files))
        self.digest=sha(self.skill_zip.read_bytes())
        self.out=self.root/'packages'
        with redirect_stdout(StringIO()):build(self.skill_zip,self.out,self.digest)

    def extract(self,task):
        filename={'LT01':'LT01-AtlasEdit.zip','LT02':'LT02-Buttons.zip'}[task]
        work=self.root/(task+' isolated')
        with zipfile.ZipFile(self.out/filename) as bundle:bundle.extractall(work)
        return work/task

    def run_recorder(self,work,*args,expected=0):
        result=subprocess.run([sys.executable,'-B',str(work/'run.py'),*map(str,args)],cwd=self.root,
                              capture_output=True,text=True,encoding='utf-8',timeout=45)
        self.assertEqual(result.returncode,expected,result.stdout+result.stderr)
        return result

    def notes(self,work):
        for name in ('initial-notes.md','feedback.md'):
            (work/'RUN'/name).write_text('Coordinator fixture; not a model trial.',encoding='utf-8')

    def test_reproducible_frozen_inputs_font_license_and_refuse_reuse_or_wrong_digest(self):
        with redirect_stdout(StringIO()):build(self.skill_zip,self.root/'repeat',self.digest)
        for filename in ('LT01-AtlasEdit.zip','LT02-Buttons.zip'):
            self.assertEqual((self.out/filename).read_bytes(),(self.root/'repeat'/filename).read_bytes())
            with zipfile.ZipFile(self.out/filename) as bundle:
                task=filename.split('-')[0]
                for name,data in self.files.items():self.assertEqual(bundle.read(task+'/'+name),data)
                if task=='LT02':
                    self.assertEqual(bundle.read(task+'/inputs/OFL.txt'),(ROOT/'demos/pixel-ui/fonts/OFL.txt').read_bytes())
        with self.assertRaises(FileExistsError):build(self.skill_zip,self.out,self.digest)
        with self.assertRaisesRegex(ValueError,'SHA-256'):build(self.skill_zip,self.root/'wrong','0'*64)
        self.assertFalse((self.root/'wrong').exists())

    def test_named_cell_actual_commands_boundary_and_no_overwrite(self):
        work=self.extract('LT01');self.run_recorder(work,'start','--platform','test','--model','fixture')
        self.notes(work)
        self.run_recorder(work,'tool','import','--image','inputs/atlas.png','--metadata','inputs/layout.json','--out','RUN/base.json')
        self.run_recorder(work,'tool','import','--image','inputs/atlas.png','--metadata','inputs/layout.json',
                          '--cell','transfer','--out','RUN/cell.json')
        path=work/'RUN/cell.json';cell=json.loads(path.read_text(encoding='utf-8'))
        visible=next(key for key,value in cell['palette'].items() if value[-2:]!='00')
        row=list(cell['rows'][0]);row[0]=visible;cell['rows'][0]=''.join(row)
        path.write_text(json.dumps(cell),encoding='utf-8')
        self.run_recorder(work,'tool','replace-cell','--spec','RUN/base.json','--cell','transfer',
                          '--replacement','RUN/cell.json','--out','RUN/final.json',
                          '--image-out','RUN/final.png','--metadata','RUN/final-layout.json')
        before=(work/'RUN/final.png').read_bytes()
        self.run_recorder(work,'tool','render','--spec','RUN/final.json','--out','RUN/final.png',expected=2)
        self.assertEqual((work/'RUN/final.png').read_bytes(),before)
        self.run_recorder(work,'check')
        self.run_recorder(work,'finish','--status','complete')
        self.assertTrue((work/'submission-LT01.zip').is_file())
        records=[json.loads(line) for line in (work/'RUN/commands.jsonl').read_text(encoding='utf-8').splitlines()]
        self.assertEqual(len(records),4);self.assertEqual(records[-1]['exit_code'],2)
        self.assertEqual(json.loads((work/'RUN/checks.json').read_text(encoding='utf-8'))['checks'][2]['changed_outside'],0)

    def test_quota_limited_failure_archives_evidence_and_frozen_inputs_rejected(self):
        work=self.extract('LT01');self.run_recorder(work,'start','--platform','test','--model','fixture')
        self.run_recorder(work,'tool','inspect','--image','missing.png',expected=2)
        self.run_recorder(work,'finish','--status','quota_limited',expected=1)
        before=(work/'submission-LT01.zip').read_bytes()
        self.run_recorder(work,'finish','--status','quota_limited',expected=2)
        self.assertEqual((work/'submission-LT01.zip').read_bytes(),before)
        session=json.loads((work/'RUN/session.json').read_text(encoding='utf-8'))
        self.assertEqual(session['submitted_status'],'quota_limited');self.assertFalse(session['engineering_checks_passed'])
        (work/'inputs/layout.json').write_text('{}',encoding='utf-8')
        self.run_recorder(work,'check',expected=2)

    def test_real_font_capacity_and_reject_context_over_icon(self):
        work=self.extract('LT02');self.run_recorder(work,'start','--platform','test','--model','fixture')
        self.notes(work)
        self.run_recorder(work,'script','deterministic-pixel-art/scripts/recipes/buttons.py','--out-dir',
                          'RUN/build','--width','96','--content','24','4','68','10')
        import shutil
        for source,target in [('asset.json','final.json'),('asset.png','final.png'),
                              ('layout.json','final-layout.json'),('context.json','context.json')]:
            shutil.copyfile(work/'RUN/build'/source,work/'RUN'/target)
        from PIL import Image,ImageDraw,ImageFont
        with Image.open(work/'RUN/final.png') as opened:atlas=opened.convert('RGBA')
        cells=json.loads((work/'RUN/final-layout.json').read_text(encoding='utf-8'))['atlas']['cells']
        font=ImageFont.truetype(str(work/'inputs/Silkscreen-Regular.ttf'),8)
        consumer=Image.new('RGBA',(96*3,18*6));instances=[]
        for row,cell in enumerate(cells):
            for col,label in enumerate(['START','LOOP','EXPORT MAP']):
                consumer.paste(atlas.crop((cell['x'],cell['y'],cell['x']+96,cell['y']+18)),(col*96,row*18))
                box=font.getbbox(label);origin=[col*96+26-box[0],row*18+6-box[1]]
                ink='#8997A5' if cell['name']=='disabled' else '#E5ECEE'
                ImageDraw.Draw(consumer).text(origin,label,font=font,fill=ink)
                instances.append(dict(state=cell['name'],label=label,origin=origin))
        consumer.save(work/'RUN/consumer.png')
        consumer.resize((consumer.width*3,consumer.height*3),Image.Resampling.NEAREST).save(work/'RUN/consumer-3x.png')
        (work/'RUN/text-fit.json').write_text(json.dumps(dict(font_size=8,instances=instances)),encoding='utf-8')
        self.run_recorder(work,'check')
        Image.new('RGBA',(2,2)).save(work/'RUN/consumer.png')
        self.run_recorder(work,'check',expected=1)
        consumer.save(work/'RUN/consumer.png')
        context=json.loads((work/'RUN/context.json').read_text(encoding='utf-8'))
        context['regions'][0]['rect'][0]=0
        (work/'RUN/context.json').write_text(json.dumps(context),encoding='utf-8')
        self.run_recorder(work,'check',expected=1)


if __name__=='__main__':unittest.main()
