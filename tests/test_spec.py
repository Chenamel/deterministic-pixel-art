import unittest
from pixelart import PixelArtError, color, render


class SpecificationTests(unittest.TestCase):
    def test_grid_and_odd_even_mirrors(self):
        base = {'kind': 'grid', 'palette': {'a': 'FF0000', 'b': '00FF00', 'c': None}, 'rows': ['ab', 'ca']}
        even = render({**base, 'mirror': 'xy'})
        self.assertEqual(even.size, (4, 4))
        for x in range(4):
            for y in range(4):
                self.assertEqual(even.getpixel((x, y)), even.getpixel((3 - x, 3 - y)))
        odd = render({**base, 'mirror': 'xy', 'center_x': True, 'center_y': True})
        self.assertEqual(odd.size, (3, 3))
        self.assertEqual([odd.getpixel((x, 0)) for x in range(3)],
                         [color('FF0000'), color('00FF00'), color('FF0000')])
        single = render({**base, 'rows': ['a'], 'mirror': 'xy', 'center_x': True, 'center_y': True})
        self.assertEqual(single.size, (1, 1))

    def test_grid_errors(self):
        base = {'kind': 'grid', 'rows': ['aa'], 'palette': {'a': 'FFFFFF'}}
        for patch in [{'rows': []}, {'rows': ['a', 'aa']}, {'rows': ['?a']},
                      {'palette': {'aa': 'FFFFFF'}}, {'palette': {'a': 'FFFFFFextra'}},
                      {'size': [1, 1]}, {'center_x': True}, {'version': True},
                      {'mirror': 'horizontal'}, {'oops': 1}]:
            with self.subTest(patch=patch), self.assertRaises(PixelArtError):
                render({**base, **patch})

    def test_dsl_rect_is_actually_rendered(self):
        image = render('CANVAS 4 3\nRECT 1 1 2 1 FF0000\n')
        self.assertEqual(sum(p[3] > 0 for p in image.get_flattened_data()), 2)
        self.assertEqual(image.getpixel((2, 1)), color('FF0000'))

    def test_dsl_errors_include_locations(self):
        cases = [('CANVAS 2 2\nMISTYPED 1', 'line 2'),
                 ('CANVAS 2 2\nBG FF0000XYZ', 'line 2'),
                 ('CANVAS 2 2\nCANVAS 3 3', 'line 2'),
                 ('BG FFFFFF', 'line 1'), ('CANVAS 2 2\nRECT -1 0 2 2 FF0000', 'line 2'),
                 ('CANVAS 2 2\nBG', 'line 2'), ('', 'CANVAS'),
                 ('CANVAS 2 2\nBTN 0 0 2 2 WRONG', 'line 2')]
        for text, error in cases:
            with self.subTest(text=text), self.assertRaisesRegex(PixelArtError, error):
                render(text)

    def test_geometry_color_alias_and_crop(self):
        image = render({'kind': 'draw', 'size': [4, 4], 'palette': {'ink': '123456'}, 'operations': [
            {'op': 'polygon', 'points': [[0, 0], [3, 0], [0, 3]], 'color': 'ink'},
            {'op': 'line', 'points': [[0, 3], [3, 3]], 'color': 'FFFFFF'},
            {'op': 'blit', 'x': 3, 'y': 1, 'crop': [1, 0, 1, 1],
             'source': {'kind': 'grid', 'rows': ['ab'], 'palette': {'a': None, 'b': 'FF0000'}}}]})
        self.assertEqual(image.getpixel((3, 1)), color('FF0000'))
        self.assertEqual(image.getpixel((3, 3)), color('FFFFFF'))

    def test_bad_operations_fail_instead_of_partial_success(self):
        for op in [{'op': 'RECT'}, {'op': 'rect', 'x': 0},
                   {'op': 'line', 'points': [[0, 0]], 'color': 'FFFFFF'},
                   {'op': 'points', 'points': [[0.5, 1]], 'color': 'FFFFFF'},
                   {'op': 'points', 'points': [[4, 1]], 'color': 'FFFFFF'},
                   {'op': 'rect', 'x': 0, 'y': 0, 'w': 1, 'h': 1, 'color': 'FFFFFF', 'clip': 'yes'},
                   {'op': 'slot', 'x': 0, 'y': 0}]:
            with self.subTest(op=op), self.assertRaisesRegex(PixelArtError, r'operations\[0\]'):
                render({'kind': 'draw', 'size': [4, 4], 'operations': [op]})

    def test_atlas_order_and_metadata(self):
        cells = [dict(name=name, spec=dict(kind='draw', size=[2, 3], operations=[], background=fill))
                 for name, fill in [('red', 'FF0000'), ('green', '00FF00'), ('blue', '0000FF')]]
        for columns, expected in [(1, (2, 9)), (2, (4, 6)), (3, (6, 3))]:
            with self.subTest(columns=columns):
                image = render(dict(kind='atlas', columns=columns, cells=cells))
                self.assertEqual(image.size, expected)
                for i, fill in enumerate(['FF0000', '00FF00', '0000FF']):
                    self.assertEqual(image.getpixel((i % columns * 2, i // columns * 3)), color(fill))
                self.assertEqual([c['name'] for c in image.info['pixelart']['cells']], ['red', 'green', 'blue'])
        with self.assertRaises(PixelArtError):
            render(dict(kind='atlas', columns=1, cells=[cells[0], cells[0]]))

    def test_nested_limits_and_semialpha_atlas(self):
        source = dict(kind='grid', rows=['x'], palette={'x': '12345680'})
        image = render(dict(kind='atlas', columns=1, cells=[dict(name='half', spec=source)]))
        self.assertEqual(image.getpixel((0, 0)), color('12345680'))
        for _ in range(26):
            source = dict(kind='preview', source=source, scale=1)
        with self.assertRaisesRegex(PixelArtError, 'depth'):
            render(source)


if __name__ == '__main__':
    unittest.main()
