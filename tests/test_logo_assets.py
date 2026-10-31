from pathlib import Path
import io
import json
import shutil
import tempfile
import unittest
import zipfile

from PIL import Image
from tools.package_logo_assets import checked_files, package, package_bytes

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets/brand/logo-kit"


def rgba(path):
    with Image.open(path) as image:
        return image.convert("RGBA")


class LogoAssetsTests(unittest.TestCase):
    def test_complete_matrix_and_default_selection(self):
        files = checked_files(ASSETS)
        self.assertEqual(len(files), 67)
        entries = json.loads(files["manifest.json"])["assets"]
        enhanced = {entry["file"] for entry in entries if entry["detail"] == "enhanced"}
        self.assertEqual(enhanced, {f"badge-{theme}/pixel-anchor-{size}.png"
                                   for theme in ("dark", "light") for size in (256, 512)})

    def test_original_skill_icons_remain_exact(self):
        for size in (32, 128):
            with self.subTest(size=size):
                self.assertEqual((ASSETS / f"badge-dark/pixel-anchor-{size}.png").read_bytes(),
                                 (ROOT / f"skill-content/assets/brand/pixel-anchor-{size}.png").read_bytes())

    def test_text_hashes_survive_git_line_endings(self):
        for path in ASSETS.rglob("*"):
            if path.is_file() and path.suffix in (".md", ".json", ".txt"):
                with self.subTest(file=path.name):
                    self.assertNotIn(b"\r", path.read_bytes())

    def test_enhancement_preserves_silhouette_and_cell_centers(self):
        for theme in ("dark", "light"):
            small = rgba(ASSETS / f"badge-{theme}/pixel-anchor-32.png")
            large = rgba(ASSETS / f"badge-{theme}/pixel-anchor-256.png")
            enlarged = small.resize((256, 256), Image.Resampling.NEAREST)
            with self.subTest(theme=theme):
                self.assertNotEqual(enlarged.tobytes(), large.tobytes())
                self.assertEqual(enlarged.getchannel("A").tobytes(), large.getchannel("A").tobytes())
                for y in (11, 16, 21):
                    for x in (11, 16, 21):
                        self.assertEqual(large.getpixel((x * 8, y * 8)), small.getpixel((x, y)))
                large512 = rgba(ASSETS / f"badge-{theme}/pixel-anchor-512.png")
                self.assertEqual(large.resize((512, 512), Image.Resampling.NEAREST).tobytes(), large512.tobytes())

    def test_reproducible_complete_zip(self):
        first, count = package_bytes(ASSETS)
        second, _ = package_bytes(ASSETS)
        self.assertEqual(first, second)
        with zipfile.ZipFile(io.BytesIO(first)) as archive:
            self.assertEqual(count, 67)
            self.assertEqual(len(archive.namelist()), count)
            self.assertIsNone(archive.testzip())

    def test_changed_content_rejected_before_writing(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            assets = directory / "assets"
            shutil.copytree(ASSETS, assets)
            (assets / "badge-dark/pixel-anchor-512.png").write_bytes(b"incomplete copy")
            out = directory / "delivery"
            with self.assertRaisesRegex(ValueError, "content changed"):
                package(assets, out)
            self.assertFalse(out.exists())

    def test_previous_package_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            marker = directory / "keep.txt"
            marker.write_text("previous delivery", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                package(ASSETS, directory)
            self.assertEqual(marker.read_text(encoding="utf-8"), "previous delivery")
            self.assertEqual(list(directory.iterdir()), [marker])
