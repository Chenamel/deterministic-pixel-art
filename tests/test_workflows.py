"""Contracts arising from real agent tasks; no aesthetic score assertions."""
import errno
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
import threading
import unittest
from unittest.mock import patch

from PIL import Image
from pixelart import PixelArtError,render,image_to_spec,replace_cell,verify_edit
from pixelart.metadata import layout_record
from pixelart.output import publish
from pixelart.review import review

CLI=Path(__file__).resolve().parents[1]/'src/pixel_art.py'


class UsabilityTests(unittest.TestCase):
    def test_sprite_silhouette_visible_on_every_background_and_preserves_alpha(self):
        image=Image.new('RGBA',(4,3));image.putpixel((1,1),(12,34,56,255));image.putpixel((2,1),(20,30,40,128))
        original=image.tobytes()
        for background in ('000000','FFFFFF','E9EDF2','172033','777777'):
            context=dict(asset_type='sprite',backgrounds=[dict(name='target',color=background)])
            report,sheet,_=review(image,context)
            view=next(v for v in report['facts']['review_views'] if v['label']=='alpha silhouette')
            x,y,w,h=view['sheet_rect'];card=sheet.crop((x,y,x+w,y+h))
            self.assertGreater(len(card.getcolors(w*h)),1)
            self.assertEqual(image.tobytes(),original)
            self.assertTrue(any(v['scale']==1 and 'light' in v['label'] for v in report['facts']['review_views']))
            self.assertTrue(any(v['scale']==1 and 'dark' in v['label'] for v in report['facts']['review_views']))

    def test_builtin_background_restatement_is_idempotent_but_conflicts_rejected(self):
        im=Image.new('RGBA',(2,2))
        base=review(im,dict(primary_background='light'))[1]
        repeated=review(im,dict(primary_background='light',backgrounds=[dict(name='light',color='E9EDF2')]))[1]
        self.assertEqual(base.tobytes(),repeated.tobytes())
        with self.assertRaisesRegex(PixelArtError,'fixed'):
            review(im,dict(backgrounds=[dict(name='light',color='000000')]))

    def test_render_target_background_preview_needs_no_python_helper(self):
        with tempfile.TemporaryDirectory(prefix='预览 space ') as directory:
            root=Path(directory);spec=root/'spec.json';out=root/'image.png';preview=root/'preview.png'
            spec.write_text(json.dumps(dict(kind='grid',rows=['.x'],palette={'.':None,'x':'FFFFFF'})),encoding='utf-8')
            result=subprocess.run([sys.executable,'-B',str(CLI),'render','--spec',str(spec),'--out',str(out),
                '--preview',str(preview),'--preview-background','172033','--scale','3'],capture_output=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stderr)
            with Image.open(preview) as im:self.assertEqual(im.getpixel((0,0)),(23,32,51,255))
            with Image.open(out) as im:self.assertEqual(im.getpixel((0,0)),(0,0,0,0))

    def test_portable_mode_works_without_links_and_still_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'image.png'
            with patch('pixelart.output.os.link',side_effect=OSError(errno.EPERM,'no links')):
                with self.assertRaisesRegex(PixelArtError,'portable-output'):
                    publish({path:b'original'})
                publish({path:b'original'},portable=True)
                with self.assertRaises(PixelArtError):publish({path:b'overwritten'},portable=True)
            self.assertEqual(path.read_bytes(),b'original')
            self.assertEqual([p.name for p in path.parent.iterdir()],['image.png'])


class ExactEditingTests(unittest.TestCase):
    def test_named_import_preserves_sparse_order_partial_alpha_and_hidden_rgb(self):
        image=Image.new('RGBA',(6,4),(91,82,73,0))
        image.putpixel((4,0),(2,3,4,128));image.putpixel((0,3),(90,80,70,255))
        atlas=dict(cell_size=[2,2],columns=3,rows=2,cells=[
            dict(name='last-first',x=4,y=2,w=2,h=2),dict(name='top',x=4,y=0,w=2,h=2)])
        image.info['pixelart']=atlas;record=layout_record(image)
        spec=image_to_spec(image,metadata=record);rebuilt=render(spec)
        self.assertEqual(rebuilt.tobytes(),image.tobytes())
        self.assertEqual(rebuilt.info['pixelart'],atlas)
        replacement=dict(kind='grid',rows=['aa','aa'],palette={'a':'11223380'})
        edited=replace_cell(spec,'top',replacement);candidate=render(edited)
        self.assertTrue(verify_edit(candidate,image,regions=[[4,0,2,2]])['valid'])
        self.assertEqual(candidate.getpixel((4,0)),(17,34,51,128))
        self.assertEqual(spec['cells'][1]['spec']['kind'],'grid')
        self.assertEqual(render(spec).tobytes(),image.tobytes())
        self.assertEqual(candidate.info['pixelart'],atlas)

    def test_named_import_rejects_stale_conflicting_and_invalid_layouts(self):
        image=render(dict(kind='atlas',columns=1,cells=[dict(name='one',spec=dict(kind='grid',rows=['a'],palette={'a':'FFFFFF'}))]))
        record=layout_record(image);image.putpixel((0,0),(0,0,0,0))
        with self.assertRaisesRegex(PixelArtError,'digest'):image_to_spec(image,metadata=record)
        image=Image.new('RGBA',(4,4))
        invalid=dict(version=1,size=[4,4],mode='RGBA',atlas=dict(cell_size=[2,2],columns=2,rows=2,
            cells=[dict(name='one',x=0,y=0,w=2,h=2),dict(name='one',x=2,y=0,w=2,h=2)]))
        with self.assertRaisesRegex(PixelArtError,'duplicate'):image_to_spec(image,metadata=invalid)
        with self.assertRaisesRegex(PixelArtError,'mutually exclusive'):
            image_to_spec(image,metadata=invalid,region=[0,0,1,1])

    def test_atlas_source_over_default_is_unchanged_and_copy_is_explicit(self):
        child=dict(kind='grid',rows=['a'],palette={'a':'11223300'})
        spec=dict(kind='atlas',columns=1,cells=[dict(name='one',spec=child)])
        self.assertEqual(render(spec).getpixel((0,0)),(0,0,0,0))
        self.assertEqual(render({**spec,'assembly':'copy'}).getpixel((0,0)),(17,34,51,0))

    def test_verify_hollow_ring_detects_inside_error_and_invisible_rgb_changes(self):
        old=Image.new('RGBA',(5,5));new=old.copy()
        mask=Image.new('L',(5,5))
        for x in range(5):
            for y in range(5):
                if x in (0,4) or y in (0,4):
                    mask.putpixel((x,y),255);new.putpixel((x,y),(245,194,107,255))
        good=verify_edit(new,old,mask=mask)
        self.assertTrue(good['valid']);self.assertEqual(good['changed_rgba_pixels'],16)
        new.putpixel((2,2),(1,2,3,0))
        report=verify_edit(new,old,mask=mask)
        self.assertFalse(report['valid']);self.assertEqual(report['changed_outside'],1)
        self.assertEqual(report['outside_bbox'],[2,2,1,1])
        with self.assertRaisesRegex(PixelArtError,'L/1'):verify_edit(new,old,mask=mask.convert('RGB'))
        with self.assertRaisesRegex(PixelArtError,'declare'):verify_edit(new,old)

    def test_actual_named_import_replace_render_and_verify_commands(self):
        with tempfile.TemporaryDirectory(prefix='单格 中文 space ') as directory:
            root=Path(directory)
            source=render(dict(kind='atlas',columns=2,cells=[dict(name=n,spec=dict(kind='grid',rows=['a'],
                palette={'a':color})) for n,color in [('left','123456'),('right','ABCDEF')]]))
            source.save(root/'source.png');(root/'layout.json').write_text(json.dumps(layout_record(source)),encoding='utf-8')
            (root/'new.json').write_text(json.dumps(dict(kind='grid',rows=['a'],palette={'a':'F5C26B80'})),encoding='utf-8')
            def run(*args):
                return subprocess.run([sys.executable,'-B',str(CLI),*map(str,args)],cwd=root,capture_output=True,timeout=20)
            self.assertEqual(run('import','--image','source.png','--metadata','layout.json','--out','editable.json').returncode,0)
            result=run('replace-cell','--spec','editable.json','--cell','right','--replacement','new.json',
                '--out','final.json','--image-out','final.png','--metadata','final-layout.json')
            self.assertEqual(result.returncode,0,result.stderr)
            final=Image.open(root/'final.png')
            self.assertEqual(final.getpixel((1,0)),(245,194,107,128))
            self.assertEqual(final.getpixel((0,0)),source.getpixel((0,0)));final.close()
            report=run('verify','--image','final.png','--compare','source.png','--allow-region','1','0','1','1')
            self.assertEqual(report.returncode,0,report.stderr)
            self.assertEqual(run('verify','--image','final.png','--compare','source.png','--allow-region','0','0','1','1').returncode,1)

    def test_portable_partial_write_failure_rolls_back_only_owned_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);a=root/'a';b=root/'b';fdopen=os.fdopen
            class BrokenWriter:
                def __init__(self,fd):self.handle=fdopen(fd,'wb')
                def __enter__(self):return self
                def write(self,data):
                    self.handle.write(data[:2]);self.handle.flush()
                    raise OSError('injected write failure')
                def __exit__(self,*args):self.handle.close()
            with patch('pixelart.output.os.fdopen',side_effect=lambda fd,mode:BrokenWriter(fd)):
                with self.assertRaisesRegex(PixelArtError,'injected write failure'):
                    publish({a:b'abcdef',b:b'ghi'},portable=True)
            self.assertEqual(list(root.iterdir()),[])

    def test_portable_concurrent_writers_only_one_wins(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'image.png';barrier=threading.Barrier(2)
            def writer(data):
                barrier.wait()
                try:
                    publish({path:data},portable=True)
                    return True
                except PixelArtError:return False
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures=[pool.submit(writer,data) for data in (b'first',b'second')]
                self.assertEqual(sum(f.result() for f in futures),1)
            self.assertIn(path.read_bytes(),(b'first',b'second'))
            self.assertEqual([p.name for p in path.parent.iterdir()],['image.png'])
