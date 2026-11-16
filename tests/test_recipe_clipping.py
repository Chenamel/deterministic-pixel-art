"""Surface clipping must preserve paint order, holes and pixel values."""

from copy import deepcopy
from pathlib import Path
import sys
import unittest

from PIL import Image
from pixelart import PixelArtError, render

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'recipes'))

from _common import clipped_ops, line, poly, rect, spec


class RecipeClippingTests(unittest.TestCase):
    def test_primitives_match_coordinate_reference_inside_surface_with_holes(self):
        size = [7, 7]
        body = {(x, y) for y in range(7) for x in range(7) if x + y <= 8}
        body -= {(2, 2), (3, 2)}
        operations = [
            rect(1, 1, 5, 4, 'B04020'),
            poly([[0, 0], [4, 0], [0, 4]], 'B04020'),
            line([[0, 0], [6, 6]], '2070C0'),
            dict(op='points', points=[[6, 0], [0, 6]], color='2070C0'),
        ]
        expected = Image.new('RGBA', tuple(size))
        for x, y in body:
            if (1 <= x < 6 and 1 <= y < 5) or x + y <= 4:
                expected.putpixel((x, y), (176, 64, 32, 255))
            if x == y or (x, y) in {(6, 0), (0, 6)}:
                expected.putpixel((x, y), (32, 112, 192, 255))
        actual = render(spec(size, clipped_ops(size, operations, body)))
        self.assertEqual(actual.tobytes(), expected.tobytes())

    def test_separated_color_runs_preserve_overlap_order(self):
        operations = [
            rect(0, 0, 4, 1, 'FF0000'),
            rect(1, 0, 3, 1, '0000FF'),
            rect(2, 0, 1, 1, 'FF0000'),
        ]
        body = {(x, 0) for x in range(4)}
        actual = render(spec([4, 1], clipped_ops([4, 1], operations, body)))
        expected = Image.new('RGBA', (4, 1), (255, 0, 0, 255))
        for x in (1, 3):
            expected.putpixel((x, 0), (0, 0, 255, 255))
        self.assertEqual(actual.tobytes(), expected.tobytes())

    def test_equal_color_spellings_and_partial_alpha_do_not_accumulate(self):
        operations = [
            rect(0, 0, 2, 1, '#abcdef80'),
            rect(1, 0, 2, 1, [171, 205, 239, 128]),
            rect(2, 0, 2, 1, (171, 205, 239, 128)),
        ]
        body = {(x, 0) for x in range(4)}
        result = clipped_ops([4, 1], operations, body)
        self.assertEqual(len(result), 1)
        image = render(spec([4, 1], result))
        self.assertEqual(image.tobytes(), bytes((171, 205, 239, 128)) * 4)

    def test_transparent_fills_select_nothing_and_leave_existing_pixels(self):
        operations = [
            rect(0, 0, 2, 1, 'ABCDEF00'),
            rect(0, 0, 2, 1, None),
        ]
        result = clipped_ops([2, 1], operations, {(0, 0), (1, 0)})
        self.assertEqual(result, [])
        image = render(spec([2, 1], [rect(0, 0, 2, 1, '105030'), *result]))
        self.assertEqual(image.tobytes(), bytes((16, 80, 48, 255)) * 2)

    def test_current_surface_is_used_without_mutating_inputs(self):
        operations = [rect(0, 0, 3, 1, [10, 20, 30, 255])]
        before = deepcopy(operations)
        body = {(0, 0)}
        first = clipped_ops([3, 1], iter(operations), body)
        body.clear()
        body.add((2, 0))
        second = clipped_ops([3, 1], iter(operations), body)
        self.assertEqual(first[0]['points'], [[0, 0]])
        self.assertEqual(second[0]['points'], [[2, 0]])
        self.assertEqual(operations, before)
        self.assertEqual(body, {(2, 0)})
        first[0]['color'][0] = 255
        self.assertEqual(operations, before)

    def test_bounds_require_explicit_canvas_clipping(self):
        body = {(0, 0), (1, 0), (-1, 0), (2, 0)}
        operation = rect(-1, 0, 4, 1, 'FFFFFF')
        with self.assertRaisesRegex(PixelArtError, 'bounds'):
            clipped_ops([2, 1], [operation], body)
        operation['clip'] = True
        result = clipped_ops([2, 1], [operation], body)
        self.assertEqual(result[0]['points'], [[0, 0], [1, 0]])

    def test_empty_surface_does_not_hide_invalid_geometry_or_fields(self):
        for operation in (
            rect(0, 0, 0, 1, 'FFFFFF'),
            dict(rect(0, 0, 1, 1, 'FFFFFF'), typo=True),
            rect(0, 0, 1, 1, 'invalid'),
            dict(op='rect', x=0, y=0, w=1, h=1),
        ):
            with self.subTest(operation=operation):
                with self.assertRaises(PixelArtError):
                    clipped_ops([2, 1], [operation], set())

    def test_outlined_and_multicolor_operations_are_rejected(self):
        for operation in (
            dict(op='mask', points=[[0, 0]], color='FFFFFF', outline='000000'),
            dict(op='bevel', x=0, y=0, w=3, h=3, tl='FFFFFF', br='000000'),
            dict(op='blit', x=0, y=0, source=spec([1, 1], [])),
        ):
            with self.subTest(operation=operation):
                with self.assertRaisesRegex(PixelArtError, 'clipped_ops'):
                    clipped_ops([3, 3], [operation], {(0, 0)})

    def test_empty_operations_and_surface_produce_no_drawing(self):
        self.assertEqual(clipped_ops([2, 1], [], {(0, 0)}), [])
        self.assertEqual(clipped_ops([2, 1], [rect(0, 0, 1, 1, 'FFFFFF')], set()), [])
        with self.assertRaises(PixelArtError):
            clipped_ops([True, 1], [], set())


if __name__ == '__main__':
    unittest.main()
