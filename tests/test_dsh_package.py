"""Check source metadata parsing and non-destructive DSH package construction."""

import json
from pathlib import Path
import tempfile
import unittest

from tools import check_dsh, package_dsh


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


class DshHostVersionTests(unittest.TestCase):
    def test_matching_services_and_mixed_version_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory)
            manifests = {}
            for name in check_dsh.HOST_PACKAGES:
                manifest = (
                    package / 'node_modules' / '@deepseek-ai' / name / 'package.json'
                )
                manifest.parent.mkdir(parents=True)
                manifest.write_text(
                    json.dumps({'version': '0.2.2-rc.3'}), encoding='utf-8'
                )
                manifests[name] = manifest
            check_dsh.verify_host_versions(package, '0.2.2-rc.3')
            for name, manifest in manifests.items():
                with self.subTest(service=name):
                    manifest.write_text(
                        json.dumps({'version': '0.2.2-rc.1'}), encoding='utf-8'
                    )
                    with self.assertRaises(RuntimeError) as raised:
                        check_dsh.verify_host_versions(package, '0.2.2-rc.3')
                    self.assertIn(f'@deepseek-ai/{name}', str(raised.exception))
                    manifest.write_text(
                        json.dumps({'version': '0.2.2-rc.3'}), encoding='utf-8'
                    )


if __name__ == '__main__':
    unittest.main()
