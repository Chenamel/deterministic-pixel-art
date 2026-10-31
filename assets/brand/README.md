# Pixel Anchor identity

**A — Pixel Anchor** is the selected direction for Deterministic Pixel Art.
Its selection corners enclose a pixel grid with one active cell, emphasizing
precise editing. English and Chinese headers share the same mark and English
project name; the Chinese subtitle reads “面向 AI 的像素绘图与精确编辑”.

- [English header, dark](../../docs/images/brand/header-en-dark.png) / [light](../../docs/images/brand/header-en-light.png).
- [中文标题图，深色](../../docs/images/brand/header-zh-CN-dark.png) / [浅色](../../docs/images/brand/header-zh-CN-light.png).
- [Editable header specifications](identity/) and [identity generator](build_identity.py).
- [Font provenance and licensing](font-notices/README.md).
- [Full-size logo kit](logo-kit/README.md) / [全尺寸素材说明](logo-kit/README.zh-CN.md):
  32/64/128px simple badges, enhanced 256/512px badges, plus transparent and monochrome marks.
  The complete set is a separate Release attachment; [future release checklist](../../docs/releases/README.md).

The source Skill metadata now points to the 32px and 128px fixed-background
badges. Fonts and headers stay outside the standalone Skill. The published
v1.2.0 ZIP and existing global installation are unchanged by this local batch.

## Assets and rebuilding

- Fixed-background Skill icons: [32px](../../skill-content/assets/brand/pixel-anchor-32.png) / [128px](../../skill-content/assets/brand/pixel-anchor-128.png).
- Native headers are 384×112; exported headers are 1152×336, using integer 3× nearest-neighbor scaling.
- [Selected specifications](identity/) retain the geometry and rasterized lettering. Rebuilding existing text needs no font installation:

```sh
python src/pixel_art.py render --spec assets/brand/identity/header-zh-CN-light.json --out output/brand-native.png
python src/pixel_art.py preview --image output/brand-native.png --out output/brand.png --scale 3 --background F3F0E8
```

To change the Chinese subtitle, edit `ZH_TEXT` in [build_identity.py](build_identity.py),
obtain the pinned font in the [font record](font-notices/README.md), and run:

```sh
python -B assets/brand/build_identity.py --skill skill/deterministic-pixel-art --font path/to/fusion-pixel-12px-monospaced-zh_hans.otf --out output/brand-rebuild --evidence output/brand-build-log
```

The helper uses only the selected public specifications. It creates output and
log directories and refuses an existing output directory or command log.
Review the new wording and its bounds before replacing the selected assets.

The original assets were rendered using the published **v1.2.0 Skill ZIP**
(`532d8a61cf4c0eba6966c7dccaf99a7e7af2632aab9e7435c54317cba02ff19e`).
Only the two PNG icons and UI metadata enter a newly built Skill; fonts and
headers stay in the repository. The published v1.2.0 ZIP remains unchanged.
Original geometry and code use the [MIT license](../../LICENSE); font licensing
is recorded separately. These are author-reviewed assets, not evidence of
general art-quality gains.

[Integration](../../docs/brand-integration-20261030.zh-CN.md) · [Review](../../docs/brand-review-20261030.zh-CN.md).
