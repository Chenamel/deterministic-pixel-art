import unittest
from PIL import Image
from pixelart import Canvas, PixelArtError, color, make_preview, outline, validate


class CoreTests(unittest.TestCase):
    def test_rectangle_extent_and_explicit_clipping(self):
        for x, y, w, h, clip in [(0, 0, 1, 1, False), (2, 3, 5, 4, False),
                                  (-2, 1, 5, 4, True), (7, 7, 4, 4, True)]:
            with self.subTest(box=(x, y, w, h)):
                canvas = Canvas(8, 8)
                canvas.rect(x, y, w, h, '123456', clip=clip)
                visible = {(xx, yy) for yy in range(8) for xx in range(8)
                           if canvas.image.getpixel((xx, yy))[3]}
                self.assertEqual(visible, {(xx, yy) for yy in range(y, y + h)
                    for xx in range(x, x + w) if 0 <= xx < 8 and 0 <= yy < 8})
        with self.assertRaisesRegex(PixelArtError, 'bounds'):
            Canvas(8, 8).rect(-1, 0, 2, 2, '123456')

    def test_invalid_sizes_and_colors(self):
        for value in ['FF0000XYZ', '#ABC', [256, 0, 0], [True, 0, 0], [0, 0], 'transparent']:
            with self.subTest(value=value), self.assertRaises(PixelArtError):
                color(value)
        for size in [(0, 2), (True, 2), (2.5, 2), (8193, 1), (8192, 8192)]:
            with self.subTest(size=size), self.assertRaises(PixelArtError):
                Canvas(*size)
        self.assertEqual(color('#01020380'), (1, 2, 3, 128))
        self.assertEqual(color(None), (0, 0, 0, 0))

    def test_bevel_overwrite_order_matches_independent_legacy_loop(self):
        for thickness in (1, 2, 3):
            reference = Image.new('RGBA', (11, 9))
            a, b = color('ABCDEF'), color('123456')
            for i in range(thickness):
                for x in range(1, 10):
                    reference.putpixel((x, 1 + i), a)
                    reference.putpixel((x, 7 - i), b)
                for y in range(1, 8):
                    reference.putpixel((1 + i, y), a)
                    reference.putpixel((9 - i, y), b)
            cv = Canvas(11, 9)
            cv.bevel(1, 1, 9, 7, a, b, thickness)
            self.assertEqual(cv.image.tobytes(), reference.tobytes())

    def test_outline_neighborhoods_and_radius(self):
        self.assertEqual(outline({(2, 2)}, neighborhood=4), {(1, 2), (3, 2), (2, 1), (2, 3)})
        self.assertEqual(len(outline({(2, 2)}, neighborhood=8)), 8)
        self.assertEqual(len(outline({(2, 2)}, neighborhood=4, thickness=2)), 12)
        with self.assertRaises(PixelArtError):
            Canvas(4, 4).mask([(0, 0)], 'FFFFFF', '000000')
        cv = Canvas(4, 4)
        cv.mask([(0, 0)], 'FFFFFF', '000000', clip=True)
        self.assertEqual(cv.image.getpixel((1, 1)), color('000000'))

    def test_semialpha_is_composited_once(self):
        cv = Canvas(3, 3)
        source = Image.new('RGBA', (2, 2), (200, 100, 50, 128))
        cv.composite(source, 1, 1)
        self.assertEqual(cv.image.getpixel((1, 1)), (200, 100, 50, 128))
        clipped = Canvas(2, 2)
        clipped.composite(source, -1, -1, clip=True)
        self.assertEqual(clipped.image.getpixel((0, 0)), (200, 100, 50, 128))
        self.assertEqual(clipped.image.getpixel((1, 1))[3], 0)

    def test_preview_preserves_source_and_integer_blocks(self):
        source = Image.new('RGBA', (2, 1))
        source.putpixel((0, 0), color('F7B955'))
        before = source.tobytes()
        enlarged = make_preview(source, 4, None)
        self.assertEqual(enlarged.size, (8, 4))
        self.assertEqual(enlarged.crop((0, 0, 4, 4)).getcolors(), [(16, color('F7B955'))])
        self.assertEqual(enlarged.getpixel((7, 3))[3], 0)
        self.assertEqual(source.tobytes(), before)
        self.assertEqual(make_preview(source, 4).getchannel('A').getextrema(), (255, 255))

    def test_validation_applies_margin_to_every_cell(self):
        image = Image.new('RGBA', (8, 4))
        image.putpixel((6, 1), color('123456'))
        rules = dict(size=[8, 4], mode='RGBA', alpha=[0, 255], cell_size=[4, 4], transparent_margin=1)
        self.assertTrue(validate(image, rules)['valid'])
        image.putpixel((7, 1), color('123456'))
        report = validate(image, rules)
        self.assertFalse(report['valid'])
        self.assertIn('(4, 0)', report['errors'][0]['message'])
        # Opaque button backgrounds are valid when no margin rule was requested.
        self.assertTrue(validate(Image.new('RGB', (4, 4)), {'alpha': [255]})['valid'])

    def test_validation_rules_and_failures(self):
        image = Image.new('RGBA', (3, 2), color('123456'))
        for rules in [{'siz': [3, 2]}, {'alpha': [256]}, {'max_colors': True},
                      {'expected_pixels': [{'at': [3, 0], 'color': 'FFFFFF'}]},
                      {'transparent_margin': 3}, {'nonempty': 1}]:
            with self.subTest(rules=rules), self.assertRaises(PixelArtError):
                validate(image, rules)
        for rules in [{'size': [2, 2]}, {'mode': 'RGB'}, {'palette': ['FFFFFF']},
                      {'cell_size': [2, 2]}, {'expected_pixels': [{'at': [0, 0], 'color': 'FFFFFF'}]}]:
            with self.subTest(rules=rules):
                self.assertFalse(validate(image, rules)['valid'])


if __name__ == '__main__':
    unittest.main()
