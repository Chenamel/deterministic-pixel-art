import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from PIL import Image
from pixelart import assemble,PixelArtError
from pixelart.assembly import seam_sheet,load_project

CLI=Path(__file__).resolve().parents[1]/'src/pixel_art.py'


class AssemblyTests(unittest.TestCase):
    def test_crop_and_reassemble_is_exact_including_hidden_and_half_alpha(self):
        image=Image.new('RGBA',(16,12))
        image.putdata([(x*10,y*12,(x+y)*8,(x+y)%3*127) for y in range(12) for x in range(16)])
        parts=[];sources={}
        for i,(x,y) in enumerate(((0,0),(8,0),(0,6),(8,6))):
            name=f'tile-{i}.png';sources[name]=image.crop((x,y,x+8,y+6))
            parts.append(dict(name=name,image=name,at=[x,y],mode='copy'))
        project=dict(size=[16,12],require_coverage=True,parts=parts)
        rebuilt,report=assemble(project,sources)
        self.assertEqual(rebuilt.tobytes(),image.tobytes());self.assertEqual(report['uncovered_pixels'],0)
        self.assertEqual(report['seam_count'],4)
        sheet=seam_sheet(rebuilt,report)
        self.assertEqual(len(report['seam_views']),4)
        self.assertLess(sheet.width*sheet.height,16_777_216)
        project['parts'].reverse()
        self.assertEqual(assemble(project,sources)[0].tobytes(),image.tobytes())

    def test_gap_overlap_crop_bounds_and_explicit_source_over(self):
        source=Image.new('RGBA',(2,2),(255,0,0,128));sources={'a.png':source}
        part=dict(name='a',image='a.png',at=[0,0],mode='copy')
        with self.assertRaisesRegex(PixelArtError,'lack'):assemble(dict(size=[3,2],parts=[part],require_coverage=True),sources)
        with self.assertRaisesRegex(PixelArtError,'overlap'):
            assemble(dict(size=[2,2],parts=[part,{**part,'name':'b'}]),sources)
        project=dict(size=[2,2],parts=[part,{**part,'name':'b','mode':'over','allow_overlap':True}])
        image,report=assemble(project,sources)
        expected=Image.alpha_composite(source,source)
        self.assertEqual(image.tobytes(),expected.tobytes());self.assertEqual(len(report['intended_overlaps']),1)
        for change in ({'at':[1,0]},{'crop':[1,1,2,2]},{'mode':'resize'},{'allow_overlap':1}):
            with self.subTest(change=change),self.assertRaises(PixelArtError):
                assemble(dict(size=[2,2],parts=[{**part,**change}]),sources)

    def test_context_crop_has_one_owner_and_no_automatic_resizing(self):
        source=Image.new('RGBA',(10,10),'red');source.paste('blue',(2,2,8,8))
        project=dict(size=[6,6],require_coverage=True,parts=[dict(name='owned interior',image='context.png',
            crop=[2,2,6,6],at=[0,0],mode='copy')])
        image,_=assemble(project,{'context.png':source})
        self.assertEqual(image.tobytes(),Image.new('RGBA',(6,6),'blue').tobytes())

    def test_file_project_portability_alias_guard_and_directory_scope(self):
        with tempfile.TemporaryDirectory(prefix='拼装 中文 space ') as directory:
            root=Path(directory);assets=root/'部件';assets.mkdir()
            Image.new('RGBA',(3,2),(11,22,33,0)).save(assets/'a.png')
            project=dict(size=[3,2],require_coverage=True,parts=[dict(name='背景',image='部件/a.png',at=[0,0],mode='copy')])
            path=root/'project.json';path.write_text(json.dumps(project,ensure_ascii=False),encoding='utf-8')
            def run(*args):
                return subprocess.run([sys.executable,'-B',str(CLI),'assemble','--project',str(path),*map(str,args)],
                    cwd=root,capture_output=True,timeout=20)
            result=run('--out','final.png','--report','report.json','--seams','seams.png')
            self.assertEqual(result.returncode,0,result.stderr)
            with Image.open(root/'final.png') as image:self.assertEqual(image.getpixel((1,1)),(11,22,33,0))
            self.assertEqual(run('--out','final.png').returncode,2)
            self.assertEqual(run('--out',assets/'a.png','--force').returncode,2)
            project['parts'][0]['image']='../outside.png'
            path.write_text(json.dumps(project),encoding='utf-8')
            with self.assertRaisesRegex(PixelArtError,'escapes'):load_project(path)
