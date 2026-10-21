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
