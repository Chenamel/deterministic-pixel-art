import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from PIL import Image
from pixelart import PixelArtError
from pixelart.review import contrast, review

CLI=Path(__file__).resolve().parents[1]/'src/pixel_art.py'


def layout():
    return dict(cell_size=[2,2],columns=2,rows=1,cells=[
        dict(name='left',x=0,y=0,w=2,h=2),dict(name='right',x=2,y=0,w=2,h=2)])


class ReviewTests(unittest.TestCase):
    def test_native_input_unchanged_partial_alpha_and_intentional_specks(self):
        image=Image.new('RGBA',(5,5));image.putpixel((1,1),(255,0,0,128));image.putpixel((4,4),(0,255,0,255))
        before=image.tobytes()
        report,sheet,diff=review(image,dict(asset_type='sprite',allowed_specks=[[4,4]]))
        self.assertEqual(image.tobytes(),before)
        self.assertTrue(report['advisory']);self.assertIsNone(diff)
        isolated=[w for w in report['warnings'] if w['rule']=='isolated_pixel']
        self.assertEqual([w['at'] for w in isolated],[[1,1]])
        self.assertGreater(sheet.width,image.width)

    def test_eight_neighbors_and_cell_boundaries(self):
        im=Image.new('RGBA',(4,2)); im.putpixel((1,0),(0,0,0,255));im.putpixel((2,0),(0,0,0,255))
        plain_report=review(im)[0]
        self.assertEqual(plain_report['facts']['isolated_pixels'],0)
        self.assertFalse(any(w['rule']=='disconnected_components' for w in plain_report['warnings']))
        self.assertEqual(review(im,{'atlas':layout()})[0]['facts']['isolated_pixels'],2)
        diagonal=Image.new('RGBA',(3,3));diagonal.putpixel((0,0),(1,2,3,1));diagonal.putpixel((1,1),(1,2,3,128))
        diagonal_report=review(diagonal)[0]
        self.assertEqual(diagonal_report['facts']['isolated_pixels'],0)
        self.assertFalse(any(w['rule']=='disconnected_components' for w in diagonal_report['warnings']))

    def test_review_warns_with_disconnected_component_sizes_and_bboxes(self):
        image=Image.new('RGBA',(48,48))
        for y in range(12,27):
            for x in range(5,21):
                image.putpixel((x,y),(200,150,50,255))
        for y, start, end in ((4,22,25),(5,21,26),(6,21,26),(7,22,26)):
            for x in range(start,end):
                image.putpixel((x,y),(20,30,40,255))

        report,_,_=review(image)

        warnings=[w for w in report['warnings'] if w['rule']=='disconnected_components']
        self.assertEqual(len(warnings),1)
        self.assertEqual(warnings[0]['components_8conn_count'],2)
        self.assertEqual(warnings[0]['component_sizes'],[240,17])
        self.assertEqual(warnings[0]['component_bboxes'],[[5,12,16,15],[21,4,5,4]])
        self.assertIn('may be intentional',warnings[0]['message'])

    def test_review_checks_disconnected_components_per_atlas_cell(self):
        image=Image.new('RGBA',(6,3))
        image.putpixel((0,0),(0,0,0,255))
        image.putpixel((2,2),(0,0,0,255))
        image.putpixel((3,0),(0,0,0,255))
        atlas=dict(cell_size=[3,3],columns=2,rows=1,cells=[
            dict(name='image',x=0,y=0,w=3,h=3),dict(name='right',x=3,y=0,w=3,h=3)])

        report,_,_=review(image,{'atlas':atlas})

        warnings=[w for w in report['warnings'] if w['rule']=='disconnected_components']
        self.assertEqual([(w['cell'],w['components_8conn_count']) for w in warnings],[('image',2)])
        self.assertEqual(warnings[0]['component_bboxes'],[[0,0,1,1],[2,2,1,1]])

    def test_duplicate_states_ignore_invisible_rgb(self):
        im=Image.new('RGBA',(4,2));im.putpixel((0,0),(10,20,30,255));im.putpixel((2,0),(10,20,30,255))
        im.putpixel((3,1),(255,0,0,0))
        report,_,_=review(im,{'atlas':layout()})
        self.assertEqual([w['cells'] for w in report['warnings'] if w['rule']=='duplicate_state'],[['left','right']])
        im.putpixel((2,0),(10,20,30,128))
        self.assertFalse(any(w['rule']=='duplicate_state' for w in review(im,{'atlas':layout()})[0]['warnings']))

    def test_contrast_only_explicit_pairs_with_alpha_compositing(self):
        self.assertAlmostEqual(contrast((0,0,0,255),(255,255,255,255)),21)
        self.assertEqual(contrast((0,0,0,0),(255,255,255,255)),1)
        im=Image.new('RGBA',(2,2),'#AAAAAA')
        self.assertFalse(review(im)[0]['warnings'])
        report,_,_=review(im,dict(contrast_pairs=[dict(name='indicator',foreground='AAAAAA',background='FFFFFF')]))
        self.assertEqual(report['warnings'][0]['rule'],'declared_contrast')
        self.assertLess(report['warnings'][0]['ratio'],3)
        self.assertNotIn('score',report)

    def test_difference_visible_pixels_bbox_and_size_mismatch(self):
        a=Image.new('RGBA',(3,3));b=a.copy();b.putpixel((0,0),(255,0,0,0));b.putpixel((2,1),(0,255,0,128))
        report,_,diff=review(a,comparison=b)
        self.assertEqual(report['comparison']['changed_visible_pixels'],1)
        self.assertEqual(report['comparison']['bbox'],(2,1,3,2))
        self.assertEqual(diff.getpixel((2,1)),(255,104,133,255))
        with self.assertRaises(PixelArtError):review(a,comparison=Image.new('RGB',(1,1)))

    def test_invalid_contexts(self):
        invalid=[[],{'version':True},{'unknown':1},{'asset_type':'painting'},
          {'allowed_specks':[[3,0]]},{'backgrounds':[dict(name='target',color=None)]},
          {'regions':[dict(name='text',rect=[0,0,4,2],role='reserved_text')]},
          {'contrast_pairs':[dict(name='x',foreground='FFFFFF',background='000000',min_ratio=float('nan'))]},
          {'atlas':layout()}]
        for context in invalid:
            with self.subTest(context=context),self.assertRaises(PixelArtError):review(Image.new('RGBA',(3,3)),context)
        duplicate=layout();duplicate['cells'][1]['x']=0
        with self.assertRaises(PixelArtError):review(Image.new('RGBA',(4,2)),{'atlas':duplicate})

    def test_fully_transparent_rgb_and_reserved_regions(self):
        im=Image.new('RGBA',(4,4),(255,30,60,0))
        report,_,_=review(im,dict(regions=[dict(name='标题',rect=[0,0,4,2],role='reserved_text')]))
        self.assertEqual(report['facts']['isolated_pixels'],0)
        self.assertEqual(report['facts']['regions'][0]['name'],'标题')


class ReviewCliTests(unittest.TestCase):
    def test_disconnected_components_are_written_to_review_report(self):
        with tempfile.TemporaryDirectory(prefix='review components ') as folder:
            root=Path(folder);source=root/'source.png';out=root/'review'
            image=Image.new('RGBA',(8,5))
            image.putpixel((0,0),(255,255,255,255))
            image.putpixel((7,4),(255,255,255,255))
            image.save(source)
            result=subprocess.run([sys.executable,'-B',str(CLI),'review','--image',str(source),
                '--out-dir',str(out)],cwd=root,capture_output=True,timeout=30)

            self.assertEqual(result.returncode,0,result.stderr)
            report=json.loads((out/'report.json').read_text(encoding='utf-8'))
            warning=next(w for w in report['warnings'] if w['rule']=='disconnected_components')
            self.assertEqual(warning['components_8conn_count'],2)
            self.assertEqual(warning['component_sizes'],[1,1])
            self.assertEqual(warning['component_bboxes'],[[0,0,1,1],[7,4,1,1]])

    def test_execution_overwrite_invalid_context_alias_and_bad_compare(self):
        with tempfile.TemporaryDirectory(prefix='review 中文 space ') as folder:
            root=Path(folder);source=root/'source.png';Image.new('RGBA',(4,4),'white').save(source)
            original=hashlib.sha256(source.read_bytes()).hexdigest()
            out=root/'审阅';ctx=root/'context.json'
            def run(*args):
                return subprocess.run([sys.executable,'-B',str(CLI),'review','--image',str(source),
                    '--out-dir',str(out),*map(str,args)],cwd=root,capture_output=True,timeout=30)
            self.assertEqual(run().returncode,0)
            self.assertTrue((out/'review.png').is_file())
            before=(out/'review.png').read_bytes()
            self.assertEqual(run().returncode,2);self.assertEqual((out/'review.png').read_bytes(),before)
            self.assertEqual(run('--force').returncode,0)
            ctx.write_text('{"regions": [{}]}',encoding='utf-8')
            fresh=root/'invalid'
            self.assertEqual(run('--out-dir',fresh,'--context',ctx).returncode,2)
            self.assertFalse(fresh.exists())
            tiny=root/'tiny.png';Image.new('RGB',(1,1)).save(tiny)
            self.assertEqual(run('--out-dir',fresh,'--compare',tiny).returncode,2);self.assertFalse(fresh.exists())
            # Source named like a managed review output cannot be overwritten even with force.
            aliased=root/'review.png';Image.open(source).save(aliased)
            self.assertEqual(run('--image',aliased,'--out-dir',root,'--force').returncode,2)
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),original)


if __name__=='__main__':unittest.main()
