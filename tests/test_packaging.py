import unittest
from tools.test_skill import nonportable_host_path


class PortableCitationTests(unittest.TestCase):
    def test_external_sources_are_not_host_paths(self):
        self.assertFalse(nonportable_host_path('[Forge](https://docs.minecraftforge.net/en/1.20.1/gui/screens/)'))
        self.assertFalse(nonportable_host_path('Use assets/quality/ui-panel.json'))
        for value in ('C:/Users/name/file.png',r'D:\work\scene.json','/home/name/file','/Users/name/file'):
            with self.subTest(value=value):self.assertTrue(nonportable_host_path(value))
