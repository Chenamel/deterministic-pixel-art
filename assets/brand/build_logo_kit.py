"""Build the full Pixel Anchor logo kit with enhanced 256/512px badges."""
from pathlib import Path
from copy import deepcopy
import argparse
import hashlib
import json
import sys

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
SIZES = (32, 64, 128, 256, 512)
LIGHT = {"2B4355": "B8C6CC", "101D2C": "F3F0E8", "DAE9EC": "24384B",
         "62D8E8": "146F80", "F5C26B": "9F5719"}


def recolor(value, colors):
    if isinstance(value, dict):
        return {key: recolor(item, colors) for key, item in value.items()}
    if isinstance(value, list):
        return [recolor(item, colors) for item in value]
    return colors.get(value, value) if isinstance(value, str) else value


def enlarge(spec, scale):
    return deepcopy(spec) if scale == 1 else {
        "version": 1, "kind": "preview", "source": deepcopy(spec),
        "scale": scale, "background": None}


def rect(x, y, w, h, color):
    return {"op": "rect", "x": x, "y": y, "w": w, "h": h, "color": color}


def detail_spec(base, theme):
    """Keep the 128px silhouette; add thin bevels inside existing colored areas."""
    if theme == "dark":
        frame_hi, frame_lo, inset_hi, inset_lo = "577284", "162A38", "193347", "0C1621"
        bracket_hi, bracket_lo = "F0FAFC", "93BBC6"
        cell_hi, cell_lo, active_hi, active_lo = "9AE8F1", "258C9D", "FFE0A4", "B57B31"
    else:
        frame_hi, frame_lo, inset_hi, inset_lo = "DCE4E6", "8A9EA8", "E8E4DA", "D5D2C9"
        bracket_hi, bracket_lo = "476579", "142936"
        cell_hi, cell_lo, active_hi, active_lo = "328898", "0A4D60", "C58C36", "754308"
    operations = [{"op": "blit", "x": 0, "y": 0, "source": enlarge(base, 4)}]
    operations += [rect(8, 1, 112, 1, frame_hi), rect(1, 8, 1, 112, frame_hi),
                   rect(8, 126, 112, 1, frame_lo), rect(126, 8, 1, 112, frame_lo),
                   {"op": "bevel", "x": 5, "y": 5, "w": 118, "h": 118,
                    "tl": inset_hi, "br": inset_lo, "thickness": 1}]
    mark = base["operations"][2]["source"]
    for operation in mark["operations"][:8]:
        x, y, w, h = [operation[key] * 4 for key in ("x", "y", "w", "h")]
        operations.append({"op": "bevel", "x": x, "y": y, "w": w, "h": h,
                           "tl": bracket_hi, "br": bracket_lo, "thickness": 1})
    for y in (36, 56, 76):
        for x in (36, 56, 76):
            hi, lo = (active_hi, active_lo) if (x, y) == (56, 56) else (cell_hi, cell_lo)
            operations += [rect(x, y, 16, 2, hi), rect(x, y + 2, 1, 12, hi),
                           rect(x, y + 14, 16, 2, lo), rect(x + 15, y + 2, 1, 12, lo)]
    return {"version": 1, "kind": "draw", "size": [128, 128], "operations": operations}


def preview_sheet(items, out, size, columns):
    padding, label_h = 16, 32
    card_w, card_h = size + padding * 2, size + padding * 2 + label_h
    rows = (len(items) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * card_w, rows * card_h), "#CED7DD")
    draw = ImageDraw.Draw(sheet)
    for index, (label, source, background) in enumerate(items):
        x, y = (index % columns) * card_w, (index // columns) * card_h
        draw.rectangle((x + 3, y + 3, x + card_w - 4, y + card_h - 4), fill=background)
        with Image.open(source) as image:
            icon = image.convert("RGBA").resize((size, size), Image.Resampling.NEAREST)
        panel = Image.new("RGBA", icon.size, background)
        panel.alpha_composite(icon)
        sheet.paste(panel.convert("RGB"), (x + padding, y + padding))
        foreground = "#E9EDF2" if background == "#182637" else "#24384B"
        draw.text((x + padding, y + padding + size + 8), label, fill=foreground)
    sheet.save(out, format="PNG")


def readme_english():
    return """# Pixel Anchor logo kit

Five sizes, six appearances, with the approved enhanced badges as the large-size defaults.
[中文说明](README.zh-CN.md)

## Choose a variant

| Variant | Files | Use |
|---|---|---|
| Dark badge | [32](badge-dark/pixel-anchor-32.png), [64](badge-dark/pixel-anchor-64.png), [128](badge-dark/pixel-anchor-128.png), [256](badge-dark/pixel-anchor-256.png), [512](badge-dark/pixel-anchor-512.png) | Fixed dark background |
| Light badge | [folder](badge-light/) | Fixed light background |
| Mark for dark backgrounds | [folder](mark-dark/) | Transparent; pale brackets, cyan cells |
| Mark for light backgrounds | [folder](mark-light/) | Transparent; dark brackets, teal cells |
| Black mark | [folder](mono-black/) | Transparent, one black ink color |
| White mark | [folder](mono-white/) | Transparent, one white ink color |

Each variant contains 32/64/128/256/512px PNGs and self-contained JSON specifications: 30 of each.

## Detail and sizing

The 32/64/128px badges retain the simple design. The 256/512px badges use the enhanced design:
thin highlights and shadows inside the frame, brackets and cells, while keeping the silhouette,
nine-cell layout and amber center. Only one recommended file exists for each variant and size.
Transparent and monochrome marks remain flat at every size.

Enlargement uses integer nearest-neighbor scaling without smoothing. Choose the simple 32/64/128px
file for compact UI instead of shrinking an enhanced badge. The original 32/128px dark PNGs match
the v1.2.1 Skill icons byte for byte. No text, gradients or external fonts are required.

See [all appearances](preview/themes.png) and [recommended size comparison](preview/default-sizes.png).

## Theme switching

Marks have transparent backgrounds; badges keep their solid interiors and transparent corners.
Black and white mean one visible ink color, not grayscale. A PNG does not detect the system theme:
the application selects the file. A web page can do this without JavaScript:

```html
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="mark-dark/pixel-anchor-512.png">
  <img src="mark-light/pixel-anchor-512.png" width="128" height="128" alt="Deterministic Pixel Art">
</picture>
```

For crisp web edges, use `image-rendering: pixelated` and an integer display size.

## Rebuild and verify

With a compatible Skill and Python/Pillow installed:

```sh
python <skill>/scripts/pixel_art.py render --spec badge-dark/pixel-anchor-512.json --out rebuilt.png
```

[manifest.json](manifest.json) identifies the simple/enhanced choice and file/RGBA hashes.
[SHA256SUMS.txt](SHA256SUMS.txt) checks the included files. The artwork uses [MIT](LICENSE).
This standalone asset kit is a separate Release download; the Skill needs only its 32/128px icons.
"""


def readme_chinese():
    return """# Pixel Anchor Logo 素材包

五种尺寸、六种外观，大尺寸徽章默认使用已选定的增强版。[English](README.md)

## 怎么选

| 用途 | 版本 |
|---|---|
| 使用深底徽章 | [32](badge-dark/pixel-anchor-32.png)、[64](badge-dark/pixel-anchor-64.png)、[128](badge-dark/pixel-anchor-128.png)、[256](badge-dark/pixel-anchor-256.png)、[512](badge-dark/pixel-anchor-512.png) |
| 使用浅底徽章 | [浅底徽章目录](badge-light/) |
| 放在深色背景上，不带底板 | [深色背景用透明图形](mark-dark/) |
| 放在浅色背景上，不带底板 | [浅色背景用透明图形](mark-light/) |
| 只使用黑色 | [纯黑透明图形](mono-black/) |
| 只使用白色 | [纯白透明图形](mono-white/) |

每套都提供 32、64、128、256、512 五种尺寸，共 30 张 PNG 和 30 份独立可编辑 JSON。

## 细节与尺寸

32/64/128 徽章使用简洁版；256/512 徽章默认使用增强版，为边框、定位角和色块补少量明暗边缘。
外轮廓、九格布局和中心强调格保持。每个外观、每个尺寸只有一份推荐文件，不必再挑基础或增强。
透明图形与纯黑/纯白版本在所有尺寸下都保持平面简洁。

所有放大均使用整数倍最近邻，不模糊。紧凑界面请选择 32/64/128，不要把增强版缩成小图标。
深底 32/128 PNG 与 v1.2.1 Skill 图标逐字节相同。素材不含文字、渐变或外部字体。

快速查看：[六种外观](preview/themes.png)、[推荐尺寸对照](preview/default-sizes.png)。

## 深浅主题怎样切换

透明图形没有底板；徽章有实色内部和透明角点。纯黑/纯白各只有一种可见颜色，不是灰度图。
PNG 本身不会感知系统主题，需要网页或应用选择对应图片。网页可使用：

```html
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="mark-dark/pixel-anchor-512.png">
  <img src="mark-light/pixel-anchor-512.png" width="128" height="128" alt="Deterministic Pixel Art">
</picture>
```

想让像素边缘保持清晰，可设 `image-rendering: pixelated`，并按整数倍尺寸显示。

## 重绘与校验

已有兼容的 Skill 和 Python/Pillow 时：

```sh
python <skill>/scripts/pixel_art.py render --spec badge-dark/pixel-anchor-512.json --out rebuilt.png
```

[manifest.json](manifest.json) 标明简洁/增强选择及文件和 RGBA 像素摘要；[SHA256SUMS.txt](SHA256SUMS.txt) 用于核对包内文件。
原创图形使用 [MIT 协议](LICENSE)。完整素材包作为独立 Release 下载附件，Skill 本身只需带 32/128 图标。
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("Use a new output directory; existing artwork is preserved.")
    scripts = args.skill / "scripts"
    if not (scripts / "pixelart").is_dir():
        parser.error("--skill must contain scripts/pixelart")
    sys.path.insert(0, str(scripts.resolve()))
    import pixelart
    source = ROOT / "assets/brand/identity/icon-32.json"
    original = json.loads(source.read_text(encoding="utf-8"))
    mark = original["operations"][2]["source"]
    variants = {"badge-dark": original, "badge-light": recolor(original, LIGHT),
                "mark-dark": mark, "mark-light": recolor(mark, LIGHT),
                "mono-black": recolor(mark, {c: "000000" for c in ("DAE9EC", "62D8E8", "F5C26B")}),
                "mono-white": recolor(mark, {c: "FFFFFF" for c in ("DAE9EC", "62D8E8", "F5C26B")})}
    args.out.mkdir(parents=True)
    manifest = {"version": 1, "name": "Pixel Anchor", "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "sizes": list(SIZES), "badge_defaults": {"32": "simple", "64": "simple", "128": "simple",
                "256": "enhanced", "512": "enhanced"}, "assets": []}
    def export(path, spec, variant, size, detail):
        png = args.out / path
        png.parent.mkdir(parents=True, exist_ok=True)
        spec_file = png.with_suffix(".json")
        spec_file.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8", newline="\n")
        result = pixelart.render(spec)
        if result.size != (size, size):
            raise ValueError("Unexpected logo dimensions")
        result.save(png, format="PNG")
        manifest["assets"].append({"file": path, "spec": spec_file.relative_to(args.out).as_posix(),
            "variant": variant, "size": [size, size], "detail": detail,
            "sha256": hashlib.sha256(png.read_bytes()).hexdigest(),
            "rgba_sha256": hashlib.sha256(result.convert("RGBA").tobytes()).hexdigest()})
    for name, spec in variants.items():
        for size in SIZES:
            enhanced = name.startswith("badge-") and size >= 256
            selected = detail_spec(spec, name.removeprefix("badge-")) if enhanced else spec
            native = 128 if enhanced else 32
            export(f"{name}/pixel-anchor-{size}.png", enlarge(selected, size // native), name, size,
                   "enhanced" if enhanced else "simple")
    preview = args.out / "preview"
    preview.mkdir()
    preview_sheet([(name, args.out / f"{name}/pixel-anchor-128.png",
                    "#182637" if name in ("badge-dark", "mark-dark", "mono-white") else "#F3F0E8")
                   for name in variants], preview / "themes.png", 128, 3)
    preview_sheet([(f"{size}px / " + theme,
                    args.out / f"badge-{theme}/pixel-anchor-{size}.png",
                    "#182637" if theme == "dark" else "#F3F0E8")
                   for theme in ("dark", "light") for size in (128, 256)],
                  preview / "default-sizes.png", 256, 2)
    (args.out / "README.md").write_text(readme_english(), encoding="utf-8", newline="\n")
    (args.out / "README.zh-CN.md").write_text(readme_chinese(), encoding="utf-8", newline="\n")
    (args.out / "LICENSE").write_bytes((ROOT / "LICENSE").read_bytes())
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    hashes = "".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(args.out).as_posix()}\n"
                     for p in sorted(args.out.rglob("*")) if p.is_file())
    (args.out / "SHA256SUMS.txt").write_text(hashes, encoding="utf-8", newline="\n")
    print(json.dumps({"assets": 30, "enhanced_badges": 4, "output": str(args.out)}))


if __name__ == "__main__":
    main()
