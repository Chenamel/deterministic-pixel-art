"""Package the reviewed full-size logo assets as a separate Release attachment."""
from pathlib import Path
import argparse
import hashlib
import io
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VARIANTS = ("badge-dark", "badge-light", "mark-dark", "mark-light", "mono-black", "mono-white")
SIZES = (32, 64, 128, 256, 512)
ARCHIVE_NAME = "deterministic-pixel-art-logos.zip"


def checked_files(assets):
    manifest = json.loads((assets / "manifest.json").read_text(encoding="utf-8"))
    expected = {f"{variant}/pixel-anchor-{size}.png" for variant in VARIANTS for size in SIZES}
    entries = manifest["assets"]
    if len(entries) != 30 or {entry["file"] for entry in entries} != expected:
        raise ValueError("Logo manifest must contain six variants in all five sizes.")
    for entry in entries:
        variant, size = entry["variant"], entry["size"][0]
        detail = "enhanced" if variant.startswith("badge-") and size >= 256 else "simple"
        name = f"{variant}/pixel-anchor-{size}.png"
        if (entry["file"] != name or entry["spec"] != name.removesuffix(".png") + ".json"
                or entry["size"] != [size, size] or entry["detail"] != detail):
            raise ValueError("Logo recommendation or dimensions do not match the approved size rules.")
        if hashlib.sha256((assets / name).read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError(f"Logo content changed: {name}")
    expected |= {name.removesuffix(".png") + ".json" for name in expected}
    expected |= {"README.md", "README.zh-CN.md", "LICENSE", "manifest.json",
                 "preview/themes.png", "preview/default-sizes.png", "SHA256SUMS.txt"}
    actual = {p.relative_to(assets).as_posix() for p in assets.rglob("*") if p.is_file()}
    if actual != expected:
        raise ValueError("Logo folder has missing or unexpected files; rebuild it before packaging.")
    sums = {}
    for line in (assets / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, name = line.split(None, 1)
        if name in sums:
            raise ValueError("Duplicate logo checksum entry.")
        sums[name] = digest
    if set(sums) != actual - {"SHA256SUMS.txt"}:
        raise ValueError("Logo checksum list is incomplete.")
    data = {name: (assets / name).read_bytes() for name in sorted(actual)}
    for name, digest in sums.items():
        if hashlib.sha256(data[name]).hexdigest() != digest:
            raise ValueError(f"Logo content changed: {name}")
    return data


def package_bytes(assets):
    files = checked_files(assets)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in files.items():
            entry = zipfile.ZipInfo("pixel-anchor-logos/" + name, (1980, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            entry.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(entry, data)
    return buffer.getvalue(), len(files)


def package(assets, out):
    if out.exists():
        raise FileExistsError("Use a new output directory; previous packages are preserved.")
    data, count = package_bytes(assets)
    digest = hashlib.sha256(data).hexdigest()
    out.mkdir(parents=True, exist_ok=False)
    (out / ARCHIVE_NAME).write_bytes(data)
    (out / "SHA256SUMS.txt").write_text(f"{digest}  {ARCHIVE_NAME}\n", encoding="ascii", newline="\n")
    return {"archive": str(out / ARCHIVE_NAME), "files": count, "bytes": len(data), "sha256": digest}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = package(ROOT / "assets/brand/logo-kit", args.out)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(2, f"Logo packaging failed: {error}\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
