"""Install the complete Skill from its pinned GitHub stable release."""

import argparse
import hashlib
from pathlib import Path
from pathlib import PurePosixPath
import shutil
import stat
import tempfile
from urllib.request import urlopen
import zipfile


ARCHIVE_URL = (
    "https://github.com/Chenamel/deterministic-pixel-art/releases/download/"
    "v1.4.1/deterministic-pixel-art-v1.4.1.zip"
)
ARCHIVE_SHA256 = "d6a77c0696134b1419470ff36bef5adb24cdb8cf9233323f0b1e24a2c5ba2671"
ARCHIVE_ROOT = "deterministic-pixel-art/"
MAX_ARCHIVE_BYTES = 16 * 1024 * 1024
MAX_UNPACKED_BYTES = 16 * 1024 * 1024


def download_archive():
    with urlopen(ARCHIVE_URL, timeout=30) as response:
        data = response.read(MAX_ARCHIVE_BYTES + 1)
    if len(data) > MAX_ARCHIVE_BYTES:
        raise ValueError("Release archive exceeds the download size limit.")
    digest = hashlib.sha256(data).hexdigest()
    if digest != ARCHIVE_SHA256:
        raise ValueError(f"Release archive SHA-256 mismatch: {digest}")
    return data


def install(destination):
    destination = Path(destination).expanduser().resolve()
    if destination.exists():
        raise FileExistsError(f"Destination already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)

    data = download_archive()
    with tempfile.TemporaryDirectory(prefix="deterministic-pixel-art-") as temporary:
        archive_path = Path(temporary) / "release.zip"
        extract_root = Path(temporary) / "extract"
        extract_root.mkdir()
        archive_path.write_bytes(data)
        with zipfile.ZipFile(archive_path) as archive:
            entries = archive.infolist()
            names = [entry.filename for entry in entries]
            if not names or len(names) > 2048 or len(names) != len(set(names)):
                raise ValueError("Release archive has no files or contains duplicate paths.")
            total_size = 0
            for entry in entries:
                normalized = entry.filename.replace("\\", "/")
                path = PurePosixPath(normalized)
                mode = entry.external_attr >> 16
                if (path.is_absolute() or ".." in path.parts or
                        not normalized.startswith(ARCHIVE_ROOT) or stat.S_ISLNK(mode)):
                    raise ValueError(f"Unexpected archive path: {entry.filename}")
                total_size += entry.file_size
                if total_size > MAX_UNPACKED_BYTES:
                    raise ValueError("Release archive exceeds the extraction size limit.")
            archive.extractall(extract_root)

        source = extract_root / ARCHIVE_ROOT.rstrip("/")
        required = (source / "SKILL.md", source / "LICENSE", source / "requirements.txt")
        if not all(path.is_file() for path in required):
            raise ValueError("Release archive is missing required Skill files.")
        if destination.exists():
            raise FileExistsError(f"Destination already exists: {destination}")
        shutil.move(str(source), str(destination))
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", required=True, type=Path)
    args = parser.parse_args()
    try:
        installed = install(args.destination)
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        parser.exit(2, f"Installation failed: {error}\n")
    print(f"Installed Deterministic Pixel Art to {installed}")


if __name__ == "__main__":
    main()
