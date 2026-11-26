import unittest
from PIL import Image
from pixelart import Canvas, PixelArtError, color, make_preview, outline, render, validate


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

    def test_pixel_helper_bounds_and_clipping(self):
        cv = Canvas(4, 4)
        cv.pixel(1, 2, 'FF0000')
        self.assertEqual(cv.image.getpixel((1, 2)), (255, 0, 0, 255))
        cv.pixel(-1, 0, '00FF00', clip=True)
        self.assertEqual(cv.image.getpixel((0, 0))[3], 0)
        with self.assertRaisesRegex(PixelArtError, 'bounds'):
            cv.pixel(4, 0, '00FF00')
        with self.assertRaises(PixelArtError):
            cv.pixel(True, 0, '00FF00')

    def test_ellipse_fill_outline_hollow_and_clip(self):
        # 3x3 cross, 5x5 symmetric disk, and bounded interior outline.
        c3 = Canvas(3, 3)
        c3.ellipse(0, 0, 3, 3, 'FFFFFF')
        self.assertEqual(
            {(x, y) for y in range(3) for x in range(3) if c3.image.getpixel((x, y))[3]},
            {(1, 0), (0, 1), (1, 1), (2, 1), (1, 2)},
        )
        c5 = Canvas(5, 5)
        c5.ellipse(0, 0, 5, 5, '36CFC9', outline_color='16223D')
        for y in range(5):
            for x in range(5):
                px = c5.image.getpixel((x, y))
                if (x in (0, 4) and y in (0, 4)):
                    self.assertEqual(px[3], 0)
                elif (x in (1, 2, 3) and y in (1, 2, 3)):
                    self.assertEqual(px, color('36CFC9'))
                else:
                    self.assertEqual(px, color('16223D'))

        # Hollow ring preserves interior pixels and rejects outline_color combination.
        ring = Canvas(7, 7, '102030')
        ring.ellipse(1, 1, 5, 5, 'F7B955', hollow=True)
        self.assertEqual(ring.image.getpixel((3, 3)), color('102030'))
        self.assertEqual(ring.image.getpixel((3, 1)), color('F7B955'))
        self.assertEqual(ring.image.getpixel((0, 0)), color('102030'))
        with self.assertRaisesRegex(PixelArtError, 'hollow'):
            ring.ellipse(1, 1, 5, 5, 'F7B955', outline_color='FFFFFF', hollow=True)
        with self.assertRaisesRegex(PixelArtError, 'bounds'):
            Canvas(4, 4).ellipse(0, 0, 5, 4, 'FFFFFF')
        clipped = Canvas(4, 4)
        clipped.ellipse(-1, 0, 5, 4, 'FFFFFF', clip=True)
        self.assertEqual(clipped.image.getpixel((0, 0)), color('FFFFFF'))

    def test_mirror_flip_and_to_spec_round_trip(self):
        cv = Canvas(5, 4)
        cv.pixel(0, 1, 'FF0000')
        cv.pixel(2, 1, '00FF00')
        cv.pixel(4, 1, '0000FF')
        cv.mirror('x')
        self.assertEqual(cv.image.getpixel((4, 1)), color('FF0000'))
        self.assertEqual(cv.image.getpixel((2, 1)), color('00FF00'))

        # Sub-region flip preserves surrounding pixels verbatim.
        cv.pixel(0, 0, 'FFFFFF')
        cv.flip('x', region=[0, 1, 5, 2])
        self.assertEqual(cv.image.getpixel((0, 0)), color('FFFFFF'))
        with self.assertRaisesRegex(PixelArtError, 'axis'):
            cv.mirror('z')
        with self.assertRaisesRegex(PixelArtError, 'bounds'):
            cv.flip('x', region=[-1, 0, 3, 2])

        # Continuous drawing + lossless JSON v1 export round-trip.
        cv.ellipse(0, 0, 4, 4, '62D8E8', outline_color='16223D')
        spec = cv.to_spec()
        self.assertEqual(spec['kind'], 'grid')
        self.assertEqual(render(spec).tobytes(), cv.image.tobytes())
        sub = cv.to_spec(region=[0, 0, 3, 3])
        self.assertEqual(sub['size'], [3, 3])
        self.assertEqual(render(sub).tobytes(), cv.image.crop((0, 0, 3, 3)).tobytes())


if __name__ == '__main__':
    unittest.main()
