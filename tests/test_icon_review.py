"""Review payload pixels and source isolation, without expecting a specific creative answer."""
from io import BytesIO
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from build_icon_review import build


class IconReviewTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='图标 review space ')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.run = self.root / 'RUN'
        (self.run / 'v1').mkdir(parents=True)
        (self.run / 'v2').mkdir()
        (self.run / 'views').mkdir()
        for group, stage, unit in [('directions', 'v1', 12), ('actions', 'v2', 16)]:
            image = Image.new('RGBA', (unit * 4, unit))
            image.putpixel((1, 1), (80, 40, 20, 128))
            image.putpixel((2, 2), (9, 8, 7, 0))
            image.save(self.run / stage / (group + '.png'))
            for background, color in [('dark', '182637'), ('light', 'E9EDF2')]:
                view = Image.alpha_composite(Image.new('RGBA', image.size, '#' + color), image)
                for scale in (1, 8):
                    view.resize((view.width * scale, view.height * scale), Image.Resampling.NEAREST).save(
                        self.run / 'views' / f'{group}-{background}-{scale}x.png')
        (self.run / 'feedback.md').write_text('PRIVATE PRODUCER VERDICT', encoding='utf-8')
        (self.run / 'session.json').write_text('PRIVATE MODEL AND LOCAL PATH', encoding='utf-8')

    def test_exact_sources_deterministic_archive_and_reader_isolation(self):
        record = build(self.run, self.root / 'one')
        build(self.run, self.root / 'two')
        first = (self.root / 'one/LT04-review.zip').read_bytes()
        self.assertEqual(first, (self.root / 'two/LT04-review.zip').read_bytes())
        self.assertEqual(record['image_count'], 10)
        with zipfile.ZipFile(BytesIO(first)) as bundle:
            self.assertEqual(len(bundle.namelist()), 12)
            for group, stage in [('directions', 'v1'), ('actions', 'v2')]:
                self.assertEqual(bundle.read('LT04-review/images/' + group + '.png'),
                                 (self.run / stage / (group + '.png')).read_bytes())
            self.assertTrue(all(name.startswith('LT04-review/images/') or name in
                ('LT04-review/START_HERE.md', 'LT04-review/TASK.md') for name in bundle.namelist()))
            for value in ('PRIVATE PRODUCER VERDICT', 'PRIVATE MODEL AND LOCAL PATH', 'Hy3', '55项', '左右反'):
                self.assertFalse(any(value.encode() in bundle.read(name) for name in bundle.namelist()))

    def test_stale_or_wrong_background_preview_refuses_partial_packet(self):
        Image.new('RGBA', (384, 96), '#E9EDF2').save(self.run / 'views/directions-dark-8x.png')
        with self.assertRaisesRegex(ValueError, 'Preview must exactly match'):
            build(self.run, self.root / 'bad')
        self.assertFalse((self.root / 'bad').exists())

    def test_existing_packet_is_preserved_and_wrong_native_size_rejected(self):
        out = self.root / 'out'
        build(self.run, out)
        original = (out / 'LT04-review.zip').read_bytes()
        with self.assertRaises(FileExistsError):
            build(self.run, out)
        self.assertEqual((out / 'LT04-review.zip').read_bytes(), original)
        Image.new('RGBA', (64, 16)).save(self.run / 'v1/directions.png')
        with self.assertRaisesRegex(ValueError, 'Unexpected native size'):
            build(self.run, self.root / 'wrong')
        self.assertFalse((self.root / 'wrong').exists())


if __name__ == '__main__':
    unittest.main()
