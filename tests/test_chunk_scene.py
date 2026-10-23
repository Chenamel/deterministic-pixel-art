"""Independent local authoring, edge drift detection and a non-target-safe edit."""
from io import BytesIO
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from PIL import Image,ImageChops
from pixelart import render,verify_edit,assemble

ROOT=Path(__file__).resolve().parents[1]
DEMO=ROOT/'demos/chunk-scene'
MODULE=importlib.util.spec_from_file_location('chunk_scene_builder',ROOT/'tools/build_chunk_scene.py')
builder=importlib.util.module_from_spec(MODULE);MODULE.loader.exec_module(builder)


class ChunkSceneTests(unittest.TestCase):
    def agreement(self):return json.loads((DEMO/'contract.json').read_text(encoding='utf-8'))
    def images(self):return {name:render(module.make_spec(self.agreement())) for name,module in builder.AUTHORS.items()}

    def test_frozen_contract_and_full_ownership_without_overlap(self):
        self.assertEqual(hashlib.sha256((DEMO/'contract.json').read_bytes()).hexdigest(),
            'f2bf1e01d6d466f83dbaa62465808cde7c55494abe799875099e85973889745a')
        files=builder.build_files(self.agreement());report=json.loads(files['assembly.json'])
        self.assertEqual(report['covered_pixels'],256*256);self.assertEqual(report['uncovered_pixels'],0)
        self.assertEqual(report['intended_overlaps'],[]);self.assertEqual(report['seam_count'],4)
        images=self.images()
        for name,image in images.items():
            self.assertEqual(image.size,(128,128));self.assertEqual(image.getchannel('A').getextrema(),(255,255))
            with Image.open(BytesIO(files[f'chunks/{name}.png'])) as stored:
                self.assertEqual(stored.tobytes(),image.tobytes())
        project=json.loads(files['project.json'])
        project['parts'].reverse()
        merged,_=assemble(project,{f'chunks/{k}.png':v for k,v in images.items()})
        with Image.open(BytesIO(files['scene.png'])) as expected:self.assertEqual(merged.tobytes(),expected.tobytes())

    def test_each_cli_runs_with_only_its_own_source_helper_contract_and_runtime(self):
        with tempfile.TemporaryDirectory(prefix='独立分块 space ') as directory:
            for name,expected in self.images().items():
                with self.subTest(chunk=name):
                    root=Path(directory)/name;task=root/'demos/chunk-scene';task.mkdir(parents=True)
                    (root/'src/pixelart').mkdir(parents=True)
                    for path in (ROOT/'src/pixelart').glob('*.py'):shutil.copyfile(path,root/'src/pixelart'/path.name)
                    for filename in (f'chunk_{name}.py','chunk_common.py','contract.json'):
                        shutil.copyfile(DEMO/filename,task/filename)
                    result=subprocess.run([sys.executable,'-B',str(task/f'chunk_{name}.py'),'--out-dir',str(root/'out')],
                        cwd=Path(directory),capture_output=True,text=True,encoding='utf-8',timeout=30)
                    self.assertEqual(result.returncode,0,result.stderr)
                    with Image.open(root/f'out/{name}.png') as actual:self.assertEqual(actual.tobytes(),expected.tobytes())
                    self.assertEqual(len(list(task.glob('chunk_??.py'))),1)
                    self.assertFalse((task/'assets').exists(),'No full-scene image is supplied')

    def test_material_shift_and_same_palette_phase_drift_are_both_detected(self):
        images=self.images();self.assertTrue(builder.check_edges(images,self.agreement())['valid'])
        shifted={**images,'ne':ImageChops.offset(images['ne'],1,0)}
        self.assertFalse(builder.check_edges(shifted,self.agreement())['valid'])
        phase={k:v.copy() for k,v in images.items()}
        phase['sw'].putpixel((32,0),tuple(bytes.fromhex(self.agreement()['palette']['stone']))+(255,))
        report=builder.check_edges(phase,self.agreement())
        self.assertFalse(report['valid']);self.assertIn([32,128],[item['at'] for item in report['issues']])

    def test_depot_flag_edit_preserves_other_chunks_and_all_other_rgba(self):
        agreement=self.agreement();before=self.images()
        after={**before,'ne':render(builder.AUTHORS['ne'].make_spec(agreement,flag='73A5AA'))}
        local=verify_edit(after['ne'],before['ne'],regions=[[82,11,16,9]])
        self.assertTrue(local['valid']);self.assertEqual(local['changed_inside'],84)
        self.assertTrue(builder.check_edges(after,agreement)['valid'])
        project=dict(size=[256,256],require_coverage=True,parts=[dict(name=k,image=k,at=agreement['chunks'][k][:2],mode='copy') for k in before])
        merged_before,_=assemble(project,before);merged_after,_=assemble(project,after)
        global_change=verify_edit(merged_after,merged_before,regions=[[210,11,16,9]])
        self.assertTrue(global_change['valid']);self.assertEqual(global_change['changed_outside'],0)
        self.assertEqual(global_change['changed_inside'],84)
        for name in ('nw','sw','se'):self.assertEqual(before[name].tobytes(),after[name].tobytes())
        batch=builder.build_files(agreement,flag='73A5AA')
        with Image.open(BytesIO(batch['scene.png'])) as regenerated:self.assertEqual(regenerated.tobytes(),merged_after.tobytes())
        self.assertEqual(json.loads(batch['manifest.json'])['parameters']['depot_flag'],'73A5AA')

    def test_unrelated_cwd_no_clobber_and_missing_chunk_errors(self):
        with tempfile.TemporaryDirectory(prefix='运河 task space ') as directory:
            root=Path(directory);out=root/'中文 output'
            def run(*args):
                return subprocess.run([sys.executable,'-B',str(ROOT/'tools/build_chunk_scene.py'),*map(str,args)],
                    cwd=root,capture_output=True,text=True,encoding='utf-8',timeout=30)
            result=run('--out-dir',out);self.assertEqual(result.returncode,0,result.stderr)
            before=(out/'scene.png').read_bytes();(out/'chunks/ne.json').unlink()
            result=run('--out-dir',out);self.assertEqual(result.returncode,2,result.stderr)
            self.assertIn('already exists',result.stderr);self.assertFalse((out/'chunks/ne.json').exists())
            self.assertEqual((out/'scene.png').read_bytes(),before)
            result=run('--check-chunks',out/'chunks');self.assertEqual(result.returncode,0,result.stderr)
            (out/'chunks/se.png').unlink()
            result=run('--check-chunks',out/'chunks');self.assertEqual(result.returncode,2,result.stderr)
            self.assertNotIn('Traceback',result.stderr);self.assertEqual((out/'scene.png').read_bytes(),before)
