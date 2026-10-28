"""Review payloads retain exact source images and exclude producer/coordinator narratives."""
from io import BytesIO
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from build_ui_review import build


class ReviewPackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='审阅 packet space ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.run = self.root/'RUN'
        (self.run/'consumer').mkdir(parents=True);(self.run/'buttons').mkdir()
        self.consumer = Image.new('RGBA',(288,108),(80,40,20,128))
        self.consumer.putpixel((1,1),(9,8,7,0))
        self.consumer.save(self.run/'consumer/consumer.png')
        self.consumer.resize((864,324),Image.Resampling.NEAREST).save(self.run/'consumer/consumer-3x.png')
        Image.new('RGBA',(288,36)).save(self.run/'buttons/asset.png')
        (self.run/'feedback.md').write_text('PRIVATE PRODUCER CONCLUSION',encoding='utf-8')

    def test_exact_source_copy_background_composition_and_reader_isolation(self):
        out=self.root/'out';record=build(self.run,out)
        self.assertEqual(record['image_count'],6)
        self.assertTrue((out/'coordinator/manifest.json').exists())
        with zipfile.ZipFile(out/'UI-review.zip') as z:
            self.assertEqual(set(z.namelist()),{'UI-review/START_HERE.md','UI-review/TASK.md',
                *('UI-review/images/'+name for name in ('consumer.png','consumer-3x.png','atlas.png',
                   'consumer-target.png','consumer-target-3x.png','consumer-light-3x.png'))})
            self.assertEqual(z.read('UI-review/images/consumer.png'),(self.run/'consumer/consumer.png').read_bytes())
            expected=Image.alpha_composite(Image.new('RGBA',self.consumer.size,'#1D293D'),self.consumer)
            with Image.open(BytesIO(z.read('UI-review/images/consumer-target.png'))) as actual:
                self.assertEqual(actual.tobytes(),expected.tobytes())
            self.assertFalse(any(b'PRIVATE PRODUCER CONCLUSION' in z.read(n) for n in z.namelist()))
            self.assertNotIn('{{',z.read('UI-review/TASK.md').decode('utf-8'))

    def test_comparison_and_deterministic_archive_and_no_overwrite(self):
        other=self.root/'other';other.mkdir()
        Image.new('RGBA',(264,108),(20,40,80,255)).save(other/'consumer.png')
        first=self.root/'a';second=self.root/'b'
        build(self.run,first,other);build(self.run,second,other)
        data=(first/'UI-review.zip').read_bytes()
        self.assertEqual(data,(second/'UI-review.zip').read_bytes())
        with zipfile.ZipFile(first/'UI-review.zip') as z:
            self.assertEqual(z.read('UI-review/images/width-88.png'),(other/'consumer.png').read_bytes())
        with self.assertRaises(FileExistsError):build(self.run,first,other)
        self.assertEqual(data,(first/'UI-review.zip').read_bytes())

    def test_invalid_view_does_not_publish_partial_packet(self):
        Image.new('RGBA',(3,3)).save(self.run/'consumer/consumer-3x.png')
        with self.assertRaisesRegex(ValueError,'nearest-neighbor'):build(self.run,self.root/'bad')
        self.assertFalse((self.root/'bad').exists())
