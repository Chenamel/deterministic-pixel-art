# Pixel Asset Workflow Toolkit

`scripts/recipes/asset_toolkit.py` is the unified workflow entrypoint for creating,
locally editing, verifying, previewing, rebuilding, and optionally ZIP-packing
pixel assets without forcing every asset into a single flat JSON grid.

Zero new runtime dependencies: runs on Python 3.10+ and Pillow >=10.4,<13
(reproducibility baseline `Pillow==12.3.0`).

## 1. Choose a source mode from natural-language intent

Run `route` if you are unsure which source format fits a task:

```text
python <skill>/scripts/recipes/asset_toolkit.py route --prompt "局部修改已有 PNG 的提灯玻璃，保持轮廓和背景不变"
```

| Common task | Mode (`--mode`) | Editable source | Native fallback |
|---|---|---|---|
| New small icon/sprite (<=32x32) | `grid` | JSON v1 `grid` or `draw` | `pixel_art.py render` |
| Local edit on an existing PNG (recolor/patch/mask) | `png-native` | Lossless 8-bit PNG + patch/recolor spec | `pixel_art.py recolor` / `verify` |
| Same-silhouette palette-driven dual/multi-state | `shared-grid-states` | `shared-grid-states` JSON -> compiled JSON v1 | `pixel_art.py render` on `specs/*.json` |
| Geometry/alpha-changing states or local patch rollback | `state-set` | `state-set` JSON (regions + patches + recolor) -> JSON v1 | `pixel_art.py render` on `specs/*.json` |
| Named atlas delivery or single-cell replacement | `atlas` | JSON v1 `atlas` or PNG + `layout.json` | `pixel_art.py replace-cell` |
| Layered component project & seam preservation | `assembly` | `project.json` + independent layer PNGs | `pixel_art.py assemble` |

## 2. Core commands

### Deliver (build + 3-tier verify + preview + rebuild check + optional ZIP)

```text
python <skill>/scripts/recipes/asset_toolkit.py deliver \
  --source sprite.json \
  --mode auto \
  --out-dir out/sprite \
  --scale 6 \
  --background 172033 \
  --pack-zip out/sprite.zip
```

For **PNG-native local edits** (skips `image_to_spec` and avoids the 62-color
expansion cliff; refuses to overwrite inputs or silent alpha drift):

```text
python <skill>/scripts/recipes/asset_toolkit.py deliver \
  --mode png-native \
  --source input.png \
  --allow-region 8 10 16 14 \
  --recolor map.json \
  --out-dir out/edited \
  --pack-zip out/edited.zip
```

Add `--allow-alpha-change` only when contour or transparency edits are intended.
For **state-set local rollback**, pass `--disable-patch <patch_id>` to revert one
named patch while keeping other patches and region recolors intact.

### Standalone 3-tier verify (read-only)

```text
python <skill>/scripts/recipes/asset_toolkit.py verify \
  --image candidate.png \
  --baseline original.png \
  --allow-region 8 10 16 14 \
  --contract contract.json
```

### Independent rebuild & ZIP CRC/SHA-256 verification

```text
python <skill>/scripts/recipes/asset_toolkit.py rebuild \
  --input out/sprite.zip \
  --out-dir rebuilt-check
```

## 3. Three-tier verification contract

Every `report.json` separates checks into three layers so heuristics never block
valid multi-component art:

1. **`required` (exit 2, blocks publish)**: static <=8-bit RGBA PNG, integer
   dimensions, valid schema/paths, independent byte-for-byte RGBA rebuild,
   no-clobber atomic publication, ZIP CRC and SHA-256 manifest match.
2. **`contract` (exit 1, blocks publish)**: declared edit mask/region zero
   outside change, alpha lock or per-region `allow_alpha_delta`, optional
   `--contract` rules (`size`, `binary_alpha`, `max_colors`,
   `transparent_margin`, `max_components`, `no_edge_spikes`).
3. **`advisory` (exit 0, informational only)**: 4-connected isolated pixel count,
   exact-color dark 2x2 double-line hints, 8-connected component sizes, perimeter
   edge contacts, and reminder to visually inspect 1x (`native.png`) and
   nearest-neighbor (`nearest.png`) previews on the target background.

## 4. Packaging & interoperability boundaries

- Bare PNGs do not store atlas cell names or layer structure. `png-native`
  warns explicitly and refuses to flatten PNGs that carry named atlas metadata.
- Edited `png-native` bundles include the edit baseline and any supplied mask,
  so the generated verification command can be run after unpacking.
- `atlas` bundles preserve `atlas.json` and `layout.json` with all cell names.
- `assembly` bundles copy all layer PNGs and a relocatable `layers/project.json`
  so unpacking into a clean directory can re-assemble byte-for-byte.
- Output conflicts refuse to overwrite without `--force`; partial failures roll
  back cleanly. Use `--portable-output` or `PIXELART_PORTABLE_OUTPUT=1` on
  filesystems that disallow hard links.
