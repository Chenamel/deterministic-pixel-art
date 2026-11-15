"""Build the text-only SkillHub installer package."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "integrations/skillhub-installer"
SEMVER = re.compile(r"\d+\.\d+\.\d+\Z")


def build(output):
    if output.exists():
        raise FileExistsError(f"Output already exists: {output}")
    files = {
        "SKILL.md": SOURCE / "SKILL.md",
        "install.py": SOURCE / "install.py",
    }
    contents = {name: path.read_bytes() for name, path in files.items()}
    skill_text = contents["SKILL.md"].decode("utf-8")
    match = re.search(r"^version:\s*(\S+)\s*$", skill_text, re.M)
    if not match or not SEMVER.fullmatch(match[1]):
        raise ValueError("Installer Skill must declare a stable SemVer version.")
    if any(b"\0" in data for data in contents.values()):
        raise ValueError("SkillHub installer packages must contain text files only.")

    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(contents.items()):
            entry = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, data)
    return {
        "archive": str(output),
        "version": match[1],
        "files": len(contents),
        "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "manifest": {name: hashlib.sha256(data).hexdigest() for name, data in sorted(contents.items())},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = build(args.out)
    except (OSError, ValueError) as error:
        parser.exit(2, f"SkillHub installer packaging failed: {error}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
