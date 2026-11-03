"""Bounded native review crops must show actual changes and declared targets."""
import copy
import unittest

from PIL import Image

from pixelart.context import _context
from pixelart.review import _sheet, review


def sheet_only(size=(1536, 1536), points=(), regions=(), context=None, compared=True):
    image = Image.new('RGBA', size, '#345678')
    mask = Image.new('L', size)
    for point in points:
        image.putpixel(point, (239, 18, 67, 255))
        mask.putpixel(point, 255)
    ctx = _context(context or {'regions': list(regions)}, size)
    report = dict(facts={}, warnings=[], comparison=None)
    difference = Image.new('RGBA', size, '#172033') if compared else None
    if compared: difference.paste('#FF6885', (0, 0, *size), mask)
    sheet = _sheet(image, ctx, report, difference, change_mask=mask if compared else None)
    return image, report, sheet


def assert_shown(test, image, report, sheet, point):
    for view in report['facts']['review_views']:
        if view.get('downsampled') or view.get('scale') != 1: continue
        if not (view['label'].startswith('native 1:1') or
                view['label'].startswith('focus ') and view.get('focus_kind') == 'source'):
            continue
        x, y, w, h = view['source_rect']
        if x <= point[0] < x+w and y <= point[1] < y+h:
            sx, sy, _, _ = view['sheet_rect']
            actual = sheet.getpixel((sx+point[0]-x, sy+point[1]-y))
            test.assertEqual(actual, image.getpixel(point)[:3])
            return
    test.fail(f'{point} has no native source view')


class ReviewFocusTests(unittest.TestCase):
    def test_real_review_shows_bottom_right_change_without_mutating_inputs(self):
        before = Image.new('RGBA', (1536, 1536), '#345678')
        image = before.copy(); image.putpixel((1500, 1500), (239, 18, 67, 255))
        original, previous = image.tobytes(), before.tobytes()
        context = {'asset_type': 'general'}; saved_context = copy.deepcopy(context)
        report, sheet, difference = review(image, context, before)
        self.assertEqual(report['comparison']['changed_visible_pixels'], 1)
        assert_shown(self, image, report, sheet, (1500, 1500))
        self.assertEqual(report['facts']['review_focus']['omitted_changed_visible_pixels'], 0)
        self.assertEqual(difference.getpixel((1500, 1500)), (255, 104, 133, 255))
        self.assertEqual(image.tobytes(), original)
        self.assertEqual(before.tobytes(), previous)
        self.assertEqual(context, saved_context)

    def test_changes_on_all_corners_and_middle_have_native_views(self):
        points = [(0, 0), (1535, 0), (0, 1535), (1535, 1535), (700, 700)]
        image, report, sheet = sheet_only(points=points)
        for point in points: assert_shown(self, image, report, sheet, point)
        focus = report['facts']['review_focus']
        self.assertEqual(focus['displayed_changed_visible_pixels'], len(points))
        self.assertEqual(focus['omitted_changed_visible_pixels'], 0)
        self.assertIsNone(focus['omitted_changed_bbox'])
        self.assertTrue(report['facts']['review_views'][0]['downsampled'])

    def test_distributed_changes_are_sampled_with_exact_omission_counts(self):
        points = [(128*i+17, 128*i+17) for i in range(12)]
        image, report, sheet = sheet_only(points=points)
        focus = report['facts']['review_focus']
        self.assertEqual(focus['window_limit'], 8)
        self.assertEqual(len(focus['windows']), 8)
        self.assertEqual(focus['changed_tiles'], 12)
        self.assertEqual(focus['displayed_changed_visible_pixels'], 8)
        self.assertEqual(focus['omitted_changed_visible_pixels'], 4)
        self.assertIsNotNone(focus['omitted_changed_bbox'])
        for point in (points[0], points[-1]): assert_shown(self, image, report, sheet, point)
        displayed = sum(any(x <= px < x+w and y <= py < y+h
            for x, y, w, h in (window['source_rect'] for window in focus['windows'])) for px, py in points)
        self.assertEqual(displayed, focus['displayed_changed_visible_pixels'])

    def test_declared_region_is_shown_without_comparison(self):
        region = dict(name='右下目标', rect=[1470, 1470, 8, 8], role='content')
        image, report, sheet = sheet_only(points=[(1474, 1474)], regions=[region], compared=False)
        assert_shown(self, image, report, sheet, (1474, 1474))
        focus = report['facts']['review_focus']
        self.assertIsNone(focus['changed_visible_pixels'])
        self.assertEqual(focus['target_regions'][0]['displayed_area'], 64)
        self.assertEqual(focus['target_regions'][0]['omitted_area'], 0)
        self.assertGreater(focus['native_source_pixels_omitted'], 0)

    def test_empty_comparison_and_large_regions_report_partial_coverage(self):
        region = dict(name='whole target', rect=[0, 0, 1536, 1536], role='content')
        _, report, _ = sheet_only(regions=[region])
        focus = report['facts']['review_focus']
        self.assertEqual(focus['changed_visible_pixels'], 0)
        self.assertEqual(focus['omitted_changed_visible_pixels'], 0)
        self.assertGreater(focus['target_regions'][0]['omitted_area'], 0)
        self.assertEqual(focus['target_regions'][0]['displayed_area'] +
                         focus['target_regions'][0]['omitted_area'], 1536*1536)

    def test_narrow_canvas_and_source_rectangles_stay_inside_bounds(self):
        for size, point in (((8192, 1), (8191, 0)), ((1, 8192), (0, 8191))):
            image, report, sheet = sheet_only(size, [point])
            assert_shown(self, image, report, sheet, point)
            self.assertLessEqual(max(sheet.size), 8192)
            self.assertLessEqual(sheet.width*sheet.height, 16_777_216)
            for window in report['facts']['review_focus']['windows']:
                x, y, w, h = window['source_rect']
                self.assertGreater(w*h, 0)
                self.assertTrue(0 <= x < x+w <= size[0] and 0 <= y < y+h <= size[1])

    def test_maximum_existing_atlas_and_backgrounds_fit_the_sheet_budget(self):
        context = dict(backgrounds=[dict(name=f'bg-{i}', color=f'{i:02x}3456') for i in range(8)],
            atlas=dict(cell_size=[96, 96], columns=16, rows=16, cells=[
                dict(name=f'cell-{i}', x=i % 16 * 96, y=i // 16 * 96, w=96, h=96) for i in range(256)]))
        _, report, sheet = sheet_only(points=[(128*i+17, 128*i+17) for i in range(12)], context=context)
        self.assertLessEqual(max(sheet.size), 8192)
        self.assertLessEqual(sheet.width*sheet.height, 16_777_216)
        self.assertLessEqual(len(report['facts']['review_views']), 300)
        final_cell = next(view for view in report['facts']['review_views'] if view['label'].startswith('cell 256:'))
        self.assertEqual(final_cell['source_rect'], [1440, 1440, 96, 96])

    def test_small_views_keep_full_size_and_global_cell_coordinates(self):
        context = dict(atlas=dict(cell_size=[2, 2], columns=2, rows=1, cells=[
            dict(name='a', x=0, y=0, w=2, h=2), dict(name='b', x=2, y=0, w=2, h=2)]))
        _, report, _ = sheet_only((4, 2), context=context)
        self.assertNotIn('review_focus', report['facts'])
        cell = next(view for view in report['facts']['review_views'] if view['label'].startswith('cell 2:'))
        self.assertEqual(cell['source_rect'], [2, 0, 2, 2])
        self.assertFalse(cell['cropped'])

    def test_focus_selection_and_pixels_are_reproducible(self):
        args = dict(points=[(7, 7), (1500, 1500)])
        _, first, sheet1 = sheet_only(**args)
        _, second, sheet2 = sheet_only(**args)
        self.assertEqual(first, second)
        self.assertEqual(sheet1.tobytes(), sheet2.tobytes())

    def test_native_crop_captions_do_not_spill_into_adjacent_cards(self):
        _, report, sheet = sheet_only(points=[(1500, 1500)])
        views = report['facts']['review_views']
        first_row = [view for view in views if view['sheet_rect'][1] == views[0]['sheet_rect'][1]]
        for view in first_row[1:]:
            x, y, _, _ = view['sheet_rect']
            for py in range(y-22, y-2):
                for px in range(x-8, x):
                    self.assertEqual(sheet.getpixel((px, py)), (16, 24, 39))
