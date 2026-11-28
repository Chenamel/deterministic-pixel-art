import hashlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from urllib.error import URLError
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

    def test_retries_transient_network_errors_and_verifies_digest(self):
        digest = hashlib.sha256(self.archive).hexdigest()
        side_effects = [URLError("temp 1"), URLError("temp 2"), io.BytesIO(self.archive)]
        with patch.object(installer, "ARCHIVE_SHA256", digest), \
             patch.object(installer, "urlopen", side_effect=side_effects) as mock_open, \
             patch.object(installer.time, "sleep") as mock_sleep:
            data = installer.download_archive(retries=2, retry_delay=0.1)
        self.assertEqual(data, self.archive)
        self.assertEqual(mock_open.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)

    def test_does_not_retry_sha256_mismatch(self):
        with patch.object(installer, "urlopen", return_value=io.BytesIO(b"unexpected")) as mock_open, \
             patch.object(installer.time, "sleep") as mock_sleep:
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                installer.download_archive(retries=3, retry_delay=0.1)
        self.assertEqual(mock_open.call_count, 1)
        mock_sleep.assert_not_called()

    def test_offline_archive_installs_without_network_and_verifies_sha256(self):
        local_zip = self.root / "local.zip"
        local_zip.write_bytes(self.archive)
        digest = hashlib.sha256(self.archive).hexdigest()
        with patch.object(installer, "ARCHIVE_SHA256", digest), \
             patch.object(installer, "urlopen", side_effect=AssertionError("unexpected network access")):
            result = installer.install(self.root / "offline-installed", archive_path=local_zip)
        self.assertEqual((result / "SKILL.md").read_bytes(), self.files["deterministic-pixel-art/SKILL.md"])

        bad_zip = self.root / "bad.zip"
        bad_zip.write_bytes(b"corrupted")
        with patch.object(installer, "ARCHIVE_SHA256", digest):
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                installer.install(self.root / "offline-bad", archive_path=bad_zip)

    def test_rejects_non_https_url_and_conflicting_sources(self):
        with self.assertRaisesRegex(ValueError, "https://"):
            installer.download_archive(url="http://example.invalid/release.zip", retries=0)
        with self.assertRaisesRegex(ValueError, "not both"):
            installer.install(
                self.root / "conflict",
                archive_path=self.root / "missing.zip",
                url="https://example.invalid/custom.zip",
            )


if __name__ == "__main__":
    unittest.main()
