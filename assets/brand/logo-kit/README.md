# Pixel Anchor logo kit

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
