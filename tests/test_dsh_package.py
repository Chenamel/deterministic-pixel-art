"""Check source metadata parsing and non-destructive DSH package construction."""

from pathlib import Path
import tempfile
import unittest

from tools import package_dsh


class DshMetadataTests(unittest.TestCase):
    def test_folded_yaml_description(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'SKILL.md'
            path.write_text(
                '---\nname: deterministic-pixel-art\ndescription: >-\n'
                '  Create editable pixels.\n  Keep the source.\n---\n\nBody.\n',
                encoding='utf-8',
            )
            self.assertEqual(
                package_dsh.skill_metadata(path)['description'],
                'Create editable pixels. Keep the source.',
            )

    def test_existing_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'package'
            path.mkdir()
            sentinel = path / 'user.txt'
            sentinel.write_bytes(b'keep me')
            with self.assertRaises(FileExistsError):
                package_dsh.build(path)
            self.assertEqual(sentinel.read_bytes(), b'keep me')
            self.assertEqual(list(path.iterdir()), [sentinel])


if __name__ == '__main__':
    unittest.main()
