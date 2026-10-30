"""Extracted LT03 trials; coordinator fixtures never count as model runs."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from build_linux_trial import build
from prepare_agent_trials import archive_bytes,sha


class LinuxTrialTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix='Linux 中文 trial space ')
        self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name)
        skill=ROOT/'skill/deterministic-pixel-art'
        self.files={'deterministic-pixel-art/'+p.relative_to(skill).as_posix():p.read_bytes()
                    for p in skill.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
        self.skill_zip=self.root/'skill.zip';self.skill_zip.write_bytes(archive_bytes(self.files))
        self.digest=sha(self.skill_zip.read_bytes())
        self.out=self.root/'package'
        self.record=build(self.skill_zip,self.out,self.digest)
        with zipfile.ZipFile(self.out/'LT03-Linux.zip') as bundle:
            bundle.extractall(self.root/'中文 extracted space')
        self.work=self.root/'中文 extracted space/LT03'

    def recorder(self,*args,expected=0):
        env=os.environ.copy();env.pop('PYTHONPATH',None)
        result=subprocess.run([sys.executable,'-B',str(self.work/'run.py'),*map(str,args)],cwd=self.root,
                              env=env,capture_output=True,text=True,encoding='utf-8',timeout=45)
        self.assertEqual(result.returncode,expected,result.stdout+result.stderr)
        return result

    def start(self):
        self.recorder('start','--platform','coordinator fixture','--model','not external AI')
        for name in ('environment-notes.md','feedback.md'):
            (self.work/'RUN'/name).write_text('Local engineering fixture, not external-model feedback.',encoding='utf-8')

    def roundtrips(self):
        for name in ('rgba','rgb','indexed'):
            self.recorder('tool','import','--image',f'inputs/{name}.png','--out',f'RUN/roundtrip/{name}.json')
            self.recorder('tool','render','--spec',f'RUN/roundtrip/{name}.json','--out',f'RUN/roundtrip/{name}.png')

    def outputs(self):
        self.recorder('tool','render','--spec','inputs/panel.json','--out','RUN/native/panel.png',
                      '--preview','RUN/native/preview.png','--preview-background','E9EDF2')
        self.recorder('tool','render','--spec','inputs/panel.json','--out','RUN/portable/panel.png',
                      '--preview','RUN/portable/preview.png','--preview-background','E9EDF2','--portable-output')
        before=(self.work/'RUN/portable/panel.png').read_bytes()
        self.recorder('tool','render','--spec','inputs/panel.json','--out','RUN/portable/panel.png',
                      '--portable-output',expected=2)
        self.assertEqual(before,(self.work/'RUN/portable/panel.png').read_bytes())
        self.recorder('tool','review','--image','RUN/portable/panel.png','--out-dir','RUN/review',
                      '--context','inputs/panel-context.json','--portable-output')

    def test_frozen_package_reproducible_and_no_coordinator_leak(self):
        build(self.skill_zip,self.root/'repeat',self.digest)
        self.assertEqual((self.out/'LT03-Linux.zip').read_bytes(),(self.root/'repeat/LT03-Linux.zip').read_bytes())
        with zipfile.ZipFile(self.out/'LT03-Linux.zip') as bundle:
            config=json.loads(bundle.read('LT03/task.json'))
            self.assertEqual(set(config),{'id','skill_zip_sha256'})
            self.assertFalse(any('/coordinator/' in n or '/evaluation/' in n for n in bundle.namelist()))
            for name,data in self.files.items():self.assertEqual(bundle.read('LT03/'+name),data)
            prompt=bundle.read('LT03/START_HERE.md').decode('utf-8')
            for coordinator_phrase in ('Gemini','DeepSeek','32会话','验收后删除','github.com/Chenamel'):
                self.assertNotIn(coordinator_phrase,prompt)
        with self.assertRaisesRegex(ValueError,'SHA-256'):
            build(self.skill_zip,self.root/'wrong','0'*64)
        self.assertFalse((self.root/'wrong').exists())
        with self.assertRaises(FileExistsError):build(self.skill_zip,self.out,self.digest)

    def test_real_roundtrip_hidden_rgb_palette_many_colors_and_no_clobber(self):
        self.start();self.roundtrips();self.outputs()
        for name,kind in [('rgba','grid'),('rgb','draw'),('indexed','grid')]:
            self.assertEqual(json.loads((self.work/f'RUN/roundtrip/{name}.json').read_text(encoding='utf-8'))['kind'],kind)
        from PIL import Image
        with Image.open(self.work/'RUN/roundtrip/rgba.png') as image:
            self.assertEqual(image.convert('RGBA').getpixel((0,0)),(17,31,47,0))
        with Image.open(self.work/'RUN/roundtrip/indexed.png') as image:
            self.assertEqual(image.convert('RGBA').getpixel((0,0)),(19,43,61,0))
        self.recorder('check');self.recorder('finish','--status','complete')
        checks=json.loads((self.work/'RUN/checks.json').read_text(encoding='utf-8'))
        self.assertTrue(checks['passed']);self.assertEqual(len(checks['checks']),22)
        records=[json.loads(line) for line in (self.work/'RUN/commands.jsonl').read_text(encoding='utf-8').splitlines()]
        self.assertEqual(len(records),10);self.assertEqual([r['exit_code'] for r in records].count(2),1)
        self.assertEqual(json.loads((self.work/'RUN/session.json').read_text(encoding='utf-8'))['cohort'],'linux-portable-rc6')
        with zipfile.ZipFile(self.work/'submission-LT03.zip') as bundle:
            self.assertIn('RUN/roundtrip/rgba.png',bundle.namelist())
            self.assertFalse(any('deterministic-pixel-art/' in n or '.venv/' in n for n in bundle.namelist()))

    def test_checker_rejects_corrupted_pixels_even_with_editable_spec_present(self):
        self.start();self.roundtrips();self.outputs()
        from PIL import Image
        path=self.work/'RUN/roundtrip/rgba.png'
        with Image.open(path) as opened:image=opened.convert('RGBA')
        image.putpixel((0,0),(0,0,0,0));image.save(path)
        self.recorder('check',expected=1)
        failed={c['check'] for c in json.loads((self.work/'RUN/checks.json').read_text(encoding='utf-8'))['checks'] if not c['passed']}
        self.assertEqual(failed,{'rgba-lossless-rgba','rgba-editable-rerenders'})

    def test_frozen_inputs_fail_and_blocked_submission_remains_available(self):
        self.start()
        self.recorder('tool','inspect','--image','missing.png',expected=2)
        self.recorder('finish','--status','blocked',expected=1)
        payload=(self.work/'submission-LT03.zip').read_bytes()
        self.recorder('finish','--status','blocked',expected=2)
        self.assertEqual((self.work/'submission-LT03.zip').read_bytes(),payload)
        (self.work/'inputs/panel.json').write_text('{}',encoding='utf-8')
        self.recorder('check',expected=2)


if __name__=='__main__':unittest.main()
