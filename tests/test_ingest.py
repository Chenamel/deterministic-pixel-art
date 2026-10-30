import json
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image
from pixelart import image_to_spec, inspect_image, PixelArtError, render
from pixelart.ingest import spec_bytes
from pixelart.metadata import encode_png,layout_record

ROOT=Path(__file__).resolve().parents[1]
CLI=ROOT/'src/pixel_art.py'


class IngestTests(unittest.TestCase):
    def named_image(self):
        image=Image.new('RGBA',(8,4),(91,82,73,0))
        image.info['pixelart']=dict(cell_size=[2,2],columns=4,rows=2,cells=[
            dict(name='first',x=0,y=0,w=2,h=2),dict(name='target',x=6,y=2,w=2,h=2)])
        for x,y,rgba in [(6,2,(11,22,33,0)),(7,2,(44,55,66,128)),
                         (6,3,(77,88,99,255)),(7,3,(10,20,30,1))]:image.putpixel((x,y),rgba)
        return image

    def test_named_cell_preserves_exact_sparse_pixels_and_default_atlas_import(self):
        image=self.named_image();metadata=layout_record(image)
        selected=image_to_spec(image,metadata=metadata,cell='target')
        self.assertEqual(selected['kind'],'grid')
        self.assertEqual(selected['size'],[2,2])
        self.assertEqual(render(selected).tobytes(),image.crop((6,2,8,4)).tobytes())
        self.assertEqual(render(selected).getpixel((0,0)),(11,22,33,0))
        whole=image_to_spec(image,metadata=metadata)
        self.assertEqual(whole['kind'],'atlas')
        self.assertEqual(render(whole).tobytes(),image.tobytes())
        self.assertEqual([c['name'] for c in whole['cells']],['first','target'])

    def test_named_cell_with_many_colors_uses_lossless_runs(self):
        image=Image.new('RGBA',(20,7))
        image.info['pixelart']=dict(cell_size=[10,7],columns=2,rows=1,cells=[dict(name='target',x=10,y=0,w=10,h=7)])
        for i in range(70):image.putpixel((10+i%10,i//10),(i,i*2,i*3,i))
        result=image_to_spec(image,cell='target')
        self.assertEqual(result['kind'],'draw')
        self.assertEqual(render(result).tobytes(),image.crop((10,0,20,7)).tobytes())

    def test_named_cell_uses_embedded_layout_and_rejects_conflicts_or_stale_digest(self):
        from io import BytesIO
        image=self.named_image();metadata=layout_record(image)
        with Image.open(BytesIO(encode_png(image,metadata))) as embedded:
            self.assertEqual(render(image_to_spec(embedded,cell='target')).tobytes(),image.crop((6,2,8,4)).tobytes())
            conflict=json.loads(json.dumps(metadata));conflict['atlas']['cells'][1]['name']='renamed'
            with self.assertRaisesRegex(PixelArtError,'conflicts'):image_to_spec(embedded,metadata=conflict,cell='target')
        image.putpixel((0,0),(1,2,3,255))
        with self.assertRaisesRegex(PixelArtError,'digest'):image_to_spec(image,metadata=metadata,cell='target')

    def test_named_cell_requires_valid_name_layout_and_exclusive_scope(self):
        image=self.named_image()
        with self.assertRaisesRegex(PixelArtError,'choose region or cell'):
            image_to_spec(image,cell='target',region=[6,2,2,2])
        with self.assertRaisesRegex(PixelArtError,'unknown name'):image_to_spec(image,cell='missing')
        with self.assertRaisesRegex(PixelArtError,'named atlas metadata'):
            image_to_spec(Image.new('RGBA',(2,2)),cell='target')
        for name in ('',3,False):
            with self.subTest(name=name),self.assertRaises(PixelArtError):image_to_spec(image,cell=name)

    def test_exact_grid_rgb_rgba_palette_and_hidden_bytes(self):
        images=[Image.new('RGB',(3,2),(1,2,3)),Image.new('RGBA',(3,2),(99,88,77,0))]
        palette=Image.new('P',(3,2));palette.putpalette([255,0,0,0,255,0]+[0]*762)
        palette.putdata([0,1,0,1,0,1]);palette.info['transparency']=bytes([0,128]);images.append(palette)
        for image in images:
            with self.subTest(mode=image.mode):
                spec=image_to_spec(image)
                self.assertEqual(spec['kind'],'grid')
                self.assertEqual(render(spec).tobytes(),image.convert('RGBA').tobytes())
                self.assertEqual(spec_bytes(spec),spec_bytes(image_to_spec(image)))

    def test_more_than_62_colors_uses_exact_row_runs(self):
        rng=random.Random(20261021)
        image=Image.new('RGBA',(80,3));image.putdata([tuple(rng.randrange(256) for _ in range(4)) for _ in range(240)])
        image.putpixel((0,0),(9,8,7,0));image.putpixel((1,0),(0,0,0,0))
        spec=image_to_spec(image)
        self.assertEqual(spec['kind'],'draw')
        self.assertEqual(render(spec).tobytes(),image.tobytes())

    def test_region_limit_and_unsupported_modes(self):
        image=Image.new('RGBA',(5,5),(1,2,3,128))
        self.assertEqual(render(image_to_spec(image,region=[1,2,3,2])).tobytes(),image.crop((1,2,4,4)).tobytes())
        with self.assertRaises(PixelArtError):image_to_spec(image,region=[4,4,2,2])
        with self.assertRaises(PixelArtError):image_to_spec(Image.new('I;16',(2,2)))
        with patch('pixelart.ingest.MAX_SPEC_BYTES',100),self.assertRaisesRegex(PixelArtError,'crop'):
            image_to_spec(image)


class NewCliTests(unittest.TestCase):
    def test_named_cell_cli_size_roundtrip_and_invalid_outputs_in_unicode_cwd(self):
        with tempfile.TemporaryDirectory(prefix='命名单格 中文 space ') as directory:
            root=Path(directory);source=root/'atlas.png';metadata=root/'layout.json';out=root/'cell.json'
            image=IngestTests().named_image();image.save(source)
            metadata.write_text(json.dumps(layout_record(image)),encoding='utf-8')
            def run(*args):
                return subprocess.run([sys.executable,'-B',str(CLI),*map(str,args)],cwd=root,
                    capture_output=True,text=True,encoding='utf-8',timeout=30)
            result=run('import','--image',source,'--metadata',metadata,'--cell','target','--out',out)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(json.loads(result.stdout)['size'],[2,2])
            self.assertEqual(render(json.loads(out.read_text(encoding='utf-8'))).tobytes(),image.crop((6,2,8,4)).tobytes())
            previous=out.read_bytes()
            self.assertEqual(run('import','--image',source,'--metadata',metadata,'--cell','target','--out',out).returncode,2)
            self.assertEqual(out.read_bytes(),previous)
            for extra in [('--cell','missing'),('--cell','target','--region','0','0','2','2')]:
                rejected=root/'rejected.json'
                self.assertEqual(run('import','--image',source,'--metadata',metadata,*extra,'--out',rejected).returncode,2)
                self.assertFalse(rejected.exists())

    def test_real_commands_roundtrip_metadata_and_no_clobber(self):
        with tempfile.TemporaryDirectory(prefix='导入 中文 space ') as directory:
            root=Path(directory);source=root/'原图.png';spec=root/'editable.json';out=root/'out.png'
            image=Image.new('RGBA',(4,4),(99,88,77,0));image.putpixel((2,1),(1,2,3,128));image.save(source)
            def run(*args):
                return subprocess.run([sys.executable,'-B',str(CLI),*map(str,args)],cwd=root,
                    capture_output=True,text=True,encoding='utf-8',env={**os.environ,'PYTHONIOENCODING':'utf-8'},timeout=30)
            self.assertEqual(run('import','--image',source,'--out',spec).returncode,0)
            self.assertEqual(run('import','--image',source,'--out',spec).returncode,2)
            self.assertEqual(run('render','--spec',spec,'--out',out,'--embed-metadata').returncode,0)
            with Image.open(out) as opened:self.assertEqual(opened.tobytes(),image.tobytes())
            report=run('inspect','--image',out,'--grid')
            self.assertEqual(report.returncode,0,report.stderr)
            self.assertEqual(json.loads(report.stdout)['facts']['bbox'],[2,1,1,1])
            self.assertEqual(run('inspect','--image',out,'--out',out,'--force').returncode,2)
            self.assertEqual(run('import','--image',source,'--out',source,'--force').returncode,2)

    def test_embedded_atlas_reuse_and_conflict(self):
        image=render(dict(kind='atlas',columns=2,cells=[dict(name=n,spec=dict(kind='draw',size=[2,2],
            background=c,operations=[])) for n,c in [('left','123456'),('right','654321')]]))
        record=layout_record(image)
        from io import BytesIO
        png=encode_png(image,record)
        self.assertEqual(png,encode_png(image,record))
        with Image.open(BytesIO(png)) as opened:
            result=inspect_image(opened)
            self.assertEqual([c['name'] for c in result['cells']],['left','right'])
            wrong=json.loads(json.dumps(record['atlas']));wrong['cells'][0]['name']='renamed'
            with self.assertRaisesRegex(PixelArtError,'conflicts'):
                inspect_image(opened,{'atlas':wrong})
        self.assertNotIn(b'pixelart:layout',encode_png(image))

    def test_cli_rejects_16bit_animation_and_non_png_without_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            high=root/'16.png';Image.new('I;16',(2,2)).save(high)
            animation=root/'animation.png'
            Image.new('RGBA',(2,2),'red').save(animation,save_all=True,append_images=[Image.new('RGBA',(2,2),'blue')],duration=100)
            jpeg=root/'photo.jpg';Image.new('RGB',(2,2)).save(jpeg)
            for source in (high,animation,jpeg):
                out=root/(source.stem+'.json')
                result=subprocess.run([sys.executable,'-B',str(CLI),'import','--image',str(source),'--out',str(out)],
                    capture_output=True,text=True,timeout=30)
                self.assertEqual(result.returncode,2,result.stderr);self.assertFalse(out.exists())
