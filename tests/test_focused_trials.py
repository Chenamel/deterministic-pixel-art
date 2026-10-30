"""Exercise the distributed trial recorder with actual packaged CLI calls."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile
from PIL import Image
from pixelart import image_to_spec,render,replace_cell

ROOT=Path(__file__).resolve().parents[1]


def read(path):return json.loads(path.read_text(encoding='utf-8'))
def write(path,data):path.write_text(json.dumps(data),encoding='utf-8')


class FocusedTrialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='三平台 rehearsal space ')
        cls.root=Path(cls.temp.name);cls.skill_zip=cls.root/'skill.zip'
        with zipfile.ZipFile(cls.skill_zip,'w',compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted((ROOT/'skill/deterministic-pixel-art').rglob('*')):
                if path.is_file() and '__pycache__' not in path.parts:
                    archive.write(path,'deterministic-pixel-art/'+path.relative_to(ROOT/'skill/deterministic-pixel-art').as_posix())
        cls.digest=hashlib.sha256(cls.skill_zip.read_bytes()).hexdigest();cls.bundles=cls.root/'bundles'
        cls.build(cls.bundles)

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    @classmethod
    def build(cls,out,digest=None):
        result=subprocess.run([sys.executable,'-B',str(ROOT/'tools/build_focused_trials.py'),
            '--skill-zip',str(cls.skill_zip),'--sha256',digest or cls.digest,'--out',str(out)],
            capture_output=True,text=True,encoding='utf-8',timeout=30)
        if result.returncode:raise AssertionError(result.stderr)
        return result

    def extract(self,task,label,suffix=''):
        directory=self.root/(task+suffix);directory.mkdir()
        with zipfile.ZipFile(self.bundles/f'{task}-{label}.zip') as archive:archive.extractall(directory)
        return directory/task

    def run_recorder(self,root,*args,expected=0,without_site=False):
        command=[sys.executable,'-B',*(['-S'] if without_site else []),str(root/'run.py'),*map(str,args)]
        result=subprocess.run(command,cwd=self.root,capture_output=True,text=True,encoding='utf-8',timeout=30)
        self.assertEqual(result.returncode,expected,result.stderr+'\n'+result.stdout)
        return result

    def test_deterministic_archives_and_rejected_wrong_hash(self):
        other=self.root/'other-bundles';self.build(other)
        for path in self.bundles.glob('*.zip'):self.assertEqual(path.read_bytes(),(other/path.name).read_bytes())
        result=subprocess.run([sys.executable,'-B',str(ROOT/'tools/build_focused_trials.py'),
            '--skill-zip',str(self.skill_zip),'--sha256','0'*64,'--out',str(self.root/'bad')],capture_output=True,timeout=30)
        self.assertEqual(result.returncode,2);self.assertFalse((self.root/'bad').exists())

    def test_windows_task_single_cell_hollow_ring_and_failure_collection(self):
        root=self.extract('P1-W','DeepSeek');run=root/'RUN'
        self.run_recorder(root,'start','--model','local scripted rehearsal; not an external agent')
        self.run_recorder(root,'tool','import','--image','inputs/atlas.png','--metadata','inputs/layout.json','--out','RUN/editable.json')
        self.run_recorder(root,'tool','replace-cell','--spec','RUN/editable.json','--cell','transfer',
            '--replacement','deterministic-pixel-art/assets/workflows/atlas-replacement.json',
            '--out','RUN/final.json','--image-out','RUN/final.png','--metadata','RUN/final-layout.json')
        with Image.open(root/'inputs/hover.png') as source,Image.open(root/'inputs/allowed-ring.png') as mask:
            image=source.convert('RGBA');image.paste((245,194,107,255),(0,0,*image.size),mask)
        write(run/'hover.json',image_to_spec(image))
        self.run_recorder(root,'tool','render','--spec','RUN/hover.json','--out','RUN/hover.png')
        (run/'feedback.md').write_text('Local engineering rehearsal only.',encoding='utf-8')
        self.run_recorder(root,'check')
        self.run_recorder(root,'finish')
        output=root/'submission-P1-W.zip';before=output.read_bytes()
        self.run_recorder(root,'finish',expected=2);self.assertEqual(output.read_bytes(),before)
        with zipfile.ZipFile(output) as archive:self.assertIn('RUN/commands.jsonl',archive.namelist())
        image.putpixel((40,8),(1,2,3,0));image.save(run/'hover.png');write(run/'hover.json',image_to_spec(image))
        self.run_recorder(root,'check',expected=1)
        boundary=next(c for c in read(run/'checks.json')['checks'] if c['check']=='hover-edit-boundary')
        self.assertEqual(boundary['changed_outside'],1)

    def test_cloud_task_records_refusal_and_preserves_hashes(self):
        root=self.extract('P1-C','Qwen')
        self.run_recorder(root,'start','--model','local scripted rehearsal; mount unverified')
        self.run_recorder(root,'tool','render','--spec','inputs/panel.json','--out','RUN/native.png')
        args=['tool','render','--spec','inputs/panel.json','--out','RUN/portable.png','--portable-output']
        self.run_recorder(root,*args,'--preview','RUN/portable-preview.png')
        self.run_recorder(root,*args,expected=2)
        self.run_recorder(root,'tool','review','--image','RUN/portable.png','--out-dir','RUN/review','--portable-output')
        (root/'RUN/environment-notes.md').write_text('Local Windows; original FUSE mount not tested.',encoding='utf-8')
        (root/'RUN/feedback.md').write_text('Local rehearsal.',encoding='utf-8')
        self.run_recorder(root,'finish')
        self.assertTrue(read(root/'RUN/checks.json')['passed'])

    def test_visual_task_and_missing_dependency_can_be_archived(self):
        root=self.extract('P1-V','Gemini');run=root/'RUN'
        self.run_recorder(root,'start','--model','local scripted engineering rehearsal; no external visual rating')
        self.run_recorder(root,'tool','review','--image','inputs/materials.png','--metadata','inputs/layout.json',
            '--context','inputs/context.json','--out-dir','RUN/before-review')
        with Image.open(root/'inputs/materials.png') as source:
            spec=image_to_spec(source,metadata=read(root/'inputs/layout.json'))
        replacement=render(spec['cells'][1]['spec']);replacement.putpixel((15,15),(200,210,220,255))
        final=replace_cell(spec,'metal',image_to_spec(replacement));write(run/'final.json',final)
        self.run_recorder(root,'tool','render','--spec','RUN/final.json','--out','RUN/final.png','--metadata','RUN/final-layout.json')
        self.run_recorder(root,'tool','review','--image','RUN/final.png','--metadata','RUN/final-layout.json',
            '--context','inputs/context.json','--compare','inputs/materials.png','--out-dir','RUN/review')
        for name in ('feedback.md','visual-notes.md'):(run/name).write_text('Local rehearsal; not aesthetic evidence.',encoding='utf-8')
        self.run_recorder(root,'finish')
        incomplete=self.extract('P1-C','Qwen','-incomplete')
        self.run_recorder(incomplete,'start','--model','local missing-dependency probe',without_site=True)
        self.run_recorder(incomplete,'finish',expected=1,without_site=True)
        self.assertTrue((incomplete/'submission-P1-C.zip').is_file())
