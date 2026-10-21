import json
from pathlib import Path
import unittest

from PIL import Image
from pixelart import PixelArtError, inspect_image, render
from pixelart.metadata import layout_record
from pixelart.review import review

ROOT=Path(__file__).resolve().parents[1]


class AnalysisTests(unittest.TestCase):
    def test_empty_partial_bbox_centroid_and_global_region(self):
        im=Image.new('RGBA',(6,5),(100,50,10,0))
        empty=inspect_image(im)['facts']
        self.assertIsNone(empty['bbox']);self.assertIsNone(empty['centroid']);self.assertIsNone(empty['margins'])
        im.putpixel((3,2),(10,20,30,128));im.putpixel((4,3),(10,20,30,255))
        f=inspect_image(im,region=[2,1,4,4])['facts']
        self.assertEqual(f['bbox'],[3,2,2,2]);self.assertEqual(f['centroid'],[4,3])
        self.assertEqual(f['margins'],dict(left=1,right=1,top=1,bottom=1))
        self.assertEqual(f['alpha']['partial_coordinates'],[[3,2]])
        self.assertEqual(f['occupancy'],2/16)
        self.assertEqual(f['components']['4']['count'],2)
        self.assertEqual(f['components']['8']['count'],1)

    def test_background_exclusion_is_explicit(self):
        im=Image.new('RGBA',(5,3),'#C6C6C6');im.putpixel((1,1),(10,20,30,255))
        self.assertEqual(inspect_image(im)['facts']['bbox'],[0,0,5,3])
        f=inspect_image(im,{'analysis':{'exclude_colors':['C6C6C6']}})['facts']
        self.assertEqual(f['bbox'],[1,1,1,1]);self.assertEqual(f['visible_pixels'],1)

    def test_shape_and_color_symmetry_are_distinct(self):
        im=Image.new('RGBA',(3,1));im.putpixel((0,0),(255,0,0,255));im.putpixel((2,0),(0,255,0,255))
        sym=inspect_image(im)['facts']['symmetry']
        self.assertEqual(sym['x']['silhouette_mismatched_pairs'],0)
        self.assertEqual(sym['x']['color_mismatched_pairs'],1)
        self.assertEqual(sym['y']['compared_pairs'],0)

    def test_output_caps_preserve_counts(self):
        im=Image.new('RGBA',(70,1));im.putdata([(i,1,2,128) for i in range(70)])
        f=inspect_image(im)['facts']
        self.assertEqual(f['colors']['count'],70);self.assertEqual(len(f['colors']['top']),32)
        self.assertEqual(f['colors']['omitted'],38)
        self.assertEqual(f['alpha']['partial_pixels'],70);self.assertEqual(f['alpha']['omitted_coordinates'],6)
        particles=Image.new('RGBA',(40,1))
        for x in range(0,40,2):particles.putpixel((x,0),(1,2,3,255))
        comps=inspect_image(particles)['facts']['components']['8']
        self.assertEqual(comps['count'],20);self.assertEqual(len(comps['largest']),16);self.assertEqual(comps['omitted'],4)

    def test_grid_is_exact_and_bounded(self):
        im=Image.new('RGBA',(2,2),(99,88,77,0));im.putpixel((1,0),(1,2,3,128))
        result=inspect_image(im,grid=True)
        grid=result['grid']
        self.assertEqual(render(dict(kind='grid',palette=grid['palette'],rows=grid['rows'])).tobytes(),im.tobytes())
        with self.assertRaisesRegex(PixelArtError,'64x64'):inspect_image(Image.new('RGBA',(65,1)),grid=True)
        with self.assertRaisesRegex(PixelArtError,'62 exact colors'):
            colors=Image.new('RGBA',(8,8));colors.putdata([(i,0,0,255) for i in range(64)])
            inspect_image(colors,grid=True)

    def test_named_cell_and_comparison_coordinates(self):
        atlas=render(dict(kind='atlas',columns=2,cells=[dict(name=name,spec=dict(kind='draw',size=[2,2],
            background=fill,operations=[])) for name,fill in [('a','123456'),('b','654321')]]))
        result=inspect_image(atlas,cell='b',grid=True)
        self.assertEqual(result['facts']['rect'],[2,0,2,2]);self.assertEqual(result['grid']['origin'],[2,0])
        before=atlas.copy();atlas.putpixel((3,1),(1,2,3,128))
        # In-memory layout is content-bound at call time, not a persisted stale digest.
        diff=inspect_image(atlas,cell='b',comparison=before)['comparison']
        self.assertEqual(diff['bbox'],[3,1,1,1]);self.assertEqual(diff['changed_rgba_pixels'],1)
        with self.assertRaises(PixelArtError):inspect_image(atlas,cell='missing')
        with self.assertRaises(PixelArtError):inspect_image(atlas,cell='a',region=[0,0,1,1])

    def test_hidden_rgb_hashes_and_raw_difference(self):
        a=Image.new('RGBA',(1,1),(1,2,3,0));b=Image.new('RGBA',(1,1),(9,8,7,0))
        result=inspect_image(a,comparison=b)
        self.assertEqual(result['comparison']['changed_visible_pixels'],0)
        self.assertEqual(result['comparison']['changed_rgba_pixels'],1)
        self.assertEqual(result['facts']['visible_sha256'],inspect_image(b)['facts']['visible_sha256'])
        self.assertNotEqual(result['facts']['rgba_sha256'],inspect_image(b)['facts']['rgba_sha256'])

    def test_review_now_exposes_frozen_ship_changes(self):
        old=render(json.loads((ROOT/'quality/revisions/ship-32-round0.json').read_text()))
        new=render(json.loads((ROOT/'examples/quality/ship-32.json').read_text()))
        a=review(old)[0]['analysis']['facts'];b=review(new)[0]['analysis']['facts']
        self.assertNotEqual(a,b)
        self.assertNotEqual(a['components'],b['components'])

    def test_legacy_metadata_and_conflicts(self):
        im=Image.new('RGBA',(2,2),'white');record=layout_record(im)
        self.assertFalse(inspect_image(im,metadata=record)['metadata']['unverified_records'])
        old={k:record[k] for k in ('size','mode','atlas')}
        self.assertEqual(inspect_image(im,metadata=old)['metadata']['unverified_records'],['sidecar'])
        record['rgba_sha256']='0'*64
        with self.assertRaisesRegex(PixelArtError,'digest'):inspect_image(im,metadata=record)
