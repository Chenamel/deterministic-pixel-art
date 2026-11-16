"""Recipe point scans must preserve nontransparent canvas coordinates."""

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'recipes'))

from _common import points_for, rect


class PointsForTests(unittest.TestCase):
    def test_sparse_and_partial_alpha_pixels_keep_canvas_coordinates(self):
        points = points_for(
            [9, 6],
            [
                rect(2, 1, 3, 2, '#C0804020'),
                rect(7, 4, 1, 1, '#FFFFFF01'),
            ],
        )

        self.assertEqual(
            points,
            {
                (2, 1),
                (3, 1),
                (4, 1),
                (2, 2),
                (3, 2),
                (4, 2),
                (7, 4),
            },
        )

    def test_empty_and_fully_transparent_surfaces_return_no_points(self):
        self.assertEqual(points_for([4, 3], []), set())
        self.assertEqual(
            points_for([4, 3], [rect(1, 1, 2, 1, '#FFFFFF00')]),
            set(),
        )

    def test_full_canvas_includes_top_left_and_bottom_right_pixels(self):
        self.assertEqual(
            points_for([3, 2], [rect(0, 0, 3, 2, 'FFFFFF')]),
            {(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1)},
        )


if __name__ == '__main__':
    unittest.main()
