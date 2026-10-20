import json
from pathlib import Path
import unittest

from PIL import Image
from pixelart import render

ROOT = Path(__file__).resolve().parents[1]


class MigrationTests(unittest.TestCase):
    def test_43_outputs_have_only_three_declared_changes(self):
        entries = json.loads((ROOT / 'specs/manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(len(entries), 43)
        changed = []
        for entry in entries:
            with self.subTest(output=entry['output']):
                image = render(json.loads((ROOT / entry['spec']).read_text(encoding='utf-8')))
                with Image.open(ROOT / 'baselines/rendered' / entry['output']) as original:
                    same = image.size == original.size and image.tobytes() == original.convert('RGBA').tobytes()
                self.assertEqual(same, not bool(entry['intended_change']))
                if entry['intended_change']:
                    changed.append(Path(entry['output']).name)
                if 'footer-v4.png' in entry['output']:
                    with Image.open(ROOT / 'baselines/snapshot' / entry['output']) as current:
                        self.assertEqual(image.tobytes(), current.convert('RGBA').tobytes())
        self.assertEqual(sorted(changed), ['bidirectional_settings_footer-v4.png',
            'redstone_on_buttons_1to1.png', 'redstone_on_buttons_preview.png'])

    def test_all_three_composed_buttons_have_complete_borders(self):
        from tools.migrate_assets import redstone_composition
        image = render(redstone_composition())
        self.assertEqual(image.size, (68, 20))
        for x in (0, 23, 46):
            for xx in range(x, x + 22):
                self.assertEqual(image.getpixel((xx, 19)), (55, 55, 55, 255))
            self.assertEqual(image.getpixel((x + 20, 1)), (90, 90, 90, 255))
        for x in (22, 45):
            self.assertTrue(all(image.getpixel((x, y))[3] == 0 for y in range(20)))

    def test_frozen_fixtures_match_hashes_without_original_project(self):
        from tools.baseline import verify_fixtures
        self.assertTrue(verify_fixtures(ROOT / 'baselines'))


if __name__ == '__main__':
    unittest.main()
