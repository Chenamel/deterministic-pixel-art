import hashlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from tools.package_skillhub_installer import build


SOURCE = Path(__file__).resolve().parents[1] / "integrations/skillhub-installer/install.py"
SPEC = importlib.util.spec_from_file_location("skillhub_install", SOURCE)
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)


def release_zip(entries):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, data in entries.items():
            archive.writestr(name, data)
    return buffer.getvalue()


class SkillHubInstallerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.files = {
            "deterministic-pixel-art/SKILL.md": b"---\nname: test\n---\n",
            "deterministic-pixel-art/LICENSE": b"MIT",
            "deterministic-pixel-art/requirements.txt": b"Pillow>=10.4,<13\n",
        }
        self.archive = release_zip(self.files)

    def tearDown(self):
        self.temporary.cleanup()

    def install_with_archive(self, archive):
        with patch.object(installer, "download_archive", return_value=archive):
            return installer.install(self.root / "installed")

    def test_extracts_release_to_new_destination(self):
        result = self.install_with_archive(self.archive)
        self.assertEqual((result / "SKILL.md").read_bytes(), self.files["deterministic-pixel-art/SKILL.md"])
        self.assertEqual((result / "LICENSE").read_bytes(), b"MIT")

    def test_rejects_existing_destination_without_replacing_it(self):
        destination = self.root / "installed"
        destination.mkdir()
        marker = destination / "keep.txt"
        marker.write_text("preserve", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            installer.install(destination)
        self.assertEqual(marker.read_text(encoding="utf-8"), "preserve")

    def test_rejects_traversal_paths(self):
        archive = release_zip({"deterministic-pixel-art/../outside.txt": b"bad"})
        with self.assertRaises(ValueError):
            self.install_with_archive(archive)

    def test_rejects_backslash_traversal_paths(self):
        archive = release_zip({"deterministic-pixel-art/..\\outside.txt": b"bad"})
        with self.assertRaises(ValueError):
            self.install_with_archive(archive)

    def test_rejects_unexpected_root(self):
        archive = release_zip({"other/SKILL.md": b"bad"})
        with self.assertRaises(ValueError):
            self.install_with_archive(archive)

    def test_rejects_missing_required_files(self):
        archive = release_zip({"deterministic-pixel-art/SKILL.md": b"skill"})
        with self.assertRaises(ValueError):
            self.install_with_archive(archive)

    def test_rejects_release_digest_mismatch(self):
        with patch.object(installer, "urlopen", return_value=io.BytesIO(b"unexpected")):
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                installer.download_archive()

    def test_builder_outputs_only_text_skill_files(self):
        output = self.root / "installer.zip"
        result = build(output)
        with zipfile.ZipFile(output) as archive:
            names = set(archive.namelist())
            self.assertEqual(names, {"SKILL.md", "install.py"})
            self.assertEqual(len(result["manifest"]), 2)
            self.assertTrue(all(b"\0" not in archive.read(name) for name in names))


if __name__ == "__main__":
    unittest.main()
