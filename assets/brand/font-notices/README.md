# Fonts used in brand headers

The Chinese subtitle uses **Fusion Pixel Font**, 12px monospaced, simplified
Chinese variant, from [TakWolf/fusion-pixel-font](https://github.com/TakWolf/fusion-pixel-font).
It is licensed under [SIL Open Font License 1.1](FusionPixel-OFL.txt).

- Release: [2026.10.25](https://github.com/TakWolf/fusion-pixel-font/releases/tag/2026.10.25).
- Archive: `fusion-pixel-font-12px-monospaced-otf-v2026.10.25.zip`.
- Archive SHA-256: `6e4cd37ad32ccdab76858759397a01c3ec372ac37fdf3acf0705da7b44281302`.
- Font: `fusion-pixel-12px-monospaced-zh_hans.otf`.
- Font SHA-256: `2e63342fd51ba29831406c8ad8fc919868de0c9dc9277d3a11614a5bc7a26907`.

Copyright (c) 2022, TakWolf. The license notice is copied unmodified from the
release archive. The full Fusion Pixel font is a build input cached locally;
it is not vendored in this repository or included in the standalone Skill.

English text uses the repository's unmodified
[Silkscreen Regular](../../../demos/pixel-ui/fonts/Silkscreen-Regular.ttf),
under [SIL OFL 1.1](../../../demos/pixel-ui/fonts/OFL.txt).

The headers retain editable point specifications, so their exact PNGs can be
rebuilt with the Pixel Art renderer without loading fonts. To change wording,
obtain the pinned font above and run [build_identity.py](../build_identity.py)
with its `--font` argument. Glyph coverage, actual ink bounds and non-overlap
are checked separately from visual readability.
