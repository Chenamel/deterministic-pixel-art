---
name: deterministic-pixel-art
license: MIT
description: Create or edit deterministic pixel-art PNG sprites, icons, GUI components and named atlases from editable grids, integer drawing commands or Python masks. Includes image measurements with limits on report size, lossless PNG import, visual checks on chosen backgrounds and optional Minecraft styling. Use vector tools for vector icon systems and image generation for photorealistic imagery.
---

# Deterministic Pixel Art

Create editable specifications and exact-grid PNGs with Python and Pillow. Work at native logical resolution and enlarge with nearest-neighbor scaling.

## Deliver a flat JSON asset

Use the same delivery command for JSON v1 `kind: grid` and `kind: draw`. The toolkit option `--mode grid` accepts both source kinds and packages the editable JSON.

Run these commands from the folder containing `asset.json` and the bundled Skill.

```text
python deterministic-pixel-art/scripts/pixel_art.py render --spec asset.json --out asset.png --preview asset-6x.png --preview-background 172033 --scale 6
python deterministic-pixel-art/scripts/recipes/asset_toolkit.py deliver --source asset.json --mode grid --out-dir delivery --pack-zip result.zip --background 172033 --scale 6
python deterministic-pixel-art/scripts/recipes/asset_toolkit.py rebuild --input result.zip --out-dir rebuilt-check
```

Open the native image and the nearest-neighbor preview on the intended background. The delivery folder contains `native.png`, `nearest.png` and `REBUILD.md`.

### Local edit on an existing PNG (`png-native`)

To recolor or patch an existing PNG without flattening layers or touching pixels outside declared rectangles/masks (`--recolor` takes `{"#AABBCC": "#112233"}` or color pairs; `--patch` takes `{"ops": [{"op": "pixel"|"points"|"rect", ...}]}`; pass `--allow-alpha-change` only when silhouette changes are intended):

```text
python deterministic-pixel-art/scripts/recipes/asset_toolkit.py deliver --mode png-native --source input.png --allow-region 8 10 16 14 --recolor map.json --out-dir delivery --pack-zip result.zip --background 172033 --scale 6
```

### Local edit on an existing `draw` spec (`patch-draw`)

Inspect the source SHA-256 and zero-based operation indices first (`--inspect-ops` is read-only and accepts only `--source`, `--offset`, `--limit`), then apply one contiguous operation slice (`{"version":1,"base_sha256":"<file_sha256>","at":12,"remove":1,"insert":[...]}` using `rect`, `points`, `line`, `polygon`, or `mask`):

```text
python deterministic-pixel-art/scripts/recipes/asset_toolkit.py patch-draw --source draft.json --inspect-ops
python deterministic-pixel-art/scripts/recipes/asset_toolkit.py patch-draw --source draft.json --patch patch.json --allow-region 8 10 16 14 --out revised.json
```

## Choose the shortest useful path

- **Unified workflow entrypoint (route, deliver, verify, rebuild, ZIP pack):** read [toolkit.md](references/toolkit.md) and run `scripts/recipes/asset_toolkit.py`. Routes small grids (`grid`), lossless PNG local edits (`png-native`), fixed-alpha dual-state grids (`shared-grid-states`), geometry/alpha-changing states with local rollback (`state-set`), named atlases (`atlas`), and layered component projects (`assembly`) without forcing flat JSON conversion.
- **Unclear or changing direction in a small flat action icon:** read [action-icons.md](references/action-icons.md) to decide direction and silhouette before detail. Skip this card for color-only edits when the action is already clear.
- **Small edit:** inherit dimensions, palette, lighting, outline and atlas order. Modify only the affected region and check its neighbors. An existing PNG can be imported to an editable spec; exact scoped color changes can use [recolor](references/workflows.md#scoped-color-variants). Alternatives and a full contact sheet are optional.
- **Deliver one existing asset:** run the [single-asset delivery](references/recipes.md#single-asset-delivery) for one PNG or a JSON v1 grid or draw source. Use the named atlas workflow for atlases and keep original drawing layers or scripts separately.
- **Text-only work:** read [text-workflow.md](references/text-workflow.md). Use `inspect` for coordinates, colors, components and a size-limited symbol grid; import, edit, render and compare. Measurements do not identify objects or judge beauty.
- **Visual work:** inspect native size and nearest-neighbor enlargement on the intended background. Use [review.md](references/review.md) for contact sheets, named cells, baseline differences, intentional specks and declared functional contrast pairs.
- **Named PNG edit or component scene:** read [workflows.md](references/workflows.md) for named import, single-cell replacement, exact allowed-change checks and PNG assembly. Load it only for these tasks.
- **Scene edits:** when parts must move together, fills must stay inside a surface, or patterns are hard to read, you may consult [scene-revision.md](references/scene-revision.md). Read the relevant section; simple edits can skip it.
- **Parameterized variants or large point lists:** use the [editable recipes](references/recipes.md) for icons, UI states, a 128×128 sprite and a component scene. Change named parameters or short source functions, then regenerate the JSON/PNG; small one-off edits need no recipe.
- **Check a single PNG's repeating texture:** run the [tile repeat preview](references/recipes.md#single-tile-repeat-preview) directly on the PNG; choose left/right, up/down or both.
- **See named tiles together:** use the [named tile scene](references/recipes.md#named-tile-scene) with an explicit name layout. Replace a named tile and regenerate to update every placement; inspect the actual scene and seams.
- **View every named atlas cell, including atlases over 256 cells:** use [paged atlas review](references/recipes.md#paged-atlas-review). Open every listed native page; the index retains names and global coordinates.
- **Export existing PNG frames as an animation:** use the optional [animation export](references/recipes.md#png-animation-export) with explicit actions and milliseconds. Keep exact PNGs; select GIF alpha/background conversion explicitly.
- **Separately drawn chunks:** read [chunking.md](references/chunking.md) to define chunk boundaries, align repeating textures, connect shapes across seams and check local edits; start with the two-chunk example.

For new artwork, capture meaning, native size, target background, style reference, palette roles, light/outline rules, state names and the requirements of the game or application that will use the image. User references take priority over demo styling. Read only the relevant guide:

- [Pixel art](references/pixel-art.md): silhouettes, clusters, diagonals, form and material.
- [Scene space](references/scene-space.md): optional help with viewing direction, projection, connected forms and object placement; follow the user's reference.
- [Pixel UI](references/ui.md): hierarchy, spacing, optical weight, state language and text reservations.
- [Minecraft](references/minecraft.md): version-specific slots, bevel seams, UV coordinates and GUI-scale requirements; an optional style.

When a new shape is uncertain, compare two silhouette ideas. For a UI set, establish layout and one representative component before expanding states. Normally stop after two targeted revision rounds; retain unresolved candidates and state the specific remaining issue.

## Represent and render

Read [formats.md](references/formats.md) for the chosen representation or Python API. Prefer grid/palette for small sprites, integer draw operations for geometric components, masks for irregular shapes and named atlases for equal-size states. Mirror only symmetric forms. Rectangles use `x,y,width,height`; unknown symbols and implicit clipping are errors. Primitives replace RGBA; `blit` composites source-over.

Grid transparency needs an explicit palette entry, such as `".":null`. This complete 3×3 spec renders one opaque center pixel; [transparent-grid.json](assets/transparent-grid.json) is a larger example:

```json
{"version":1,"kind":"grid","rows":["...",".X.","..."],"palette":{".":null,"X":"62D8E8"}}
```

Minimal `draw` spec (`palette` aliases are optional; `op` supports `rect`, `points`, `line`, `polygon`, `bevel`, `mask`, `blit`, plus `minecraft` preset `button`/`slot`):

```json
{"version":1,"kind":"draw","size":[16,16],"palette":{"fill":"62D8E8","edge":"16223D"},"operations":[{"op":"rect","x":3,"y":3,"w":10,"h":10,"color":"fill"},{"op":"mask","points":[[7,7],[8,7],[7,8]],"color":"F7B955","outline":"edge","neighborhood":4}]}
```

Resolve `scripts/pixel_art.py` relative to this skill, not the working directory. Use Python 3.10+ with Pillow >=10.4,<13; the fixed reproduction baseline is Pillow 12.3.0. Install `requirements.txt` in a task-local virtual environment when needed.

```text
python -B <skill>/scripts/pixel_art.py render --spec scene.json --out candidate.png --preview preview.png --preview-background 172033 --metadata layout.json
python -B <skill>/scripts/pixel_art.py inspect --image candidate.png --metadata layout.json --cell normal --grid
python -B <skill>/scripts/pixel_art.py validate --image candidate.png --rules rules.json
```

Omit `--cell` for a non-atlas image. `render --embed-metadata` optionally stores layout for later automatic reuse. Keep the editable spec alongside the PNG. Existing outputs require `--force`; revise accepted art into a separate candidate unless replacement is requested. When revision history is required, retain each reviewed candidate's spec, PNG, layout and generator source before rebuilding. Keep task-specific writes behind an entrypoint, write temporary helper scripts in your working directory rather than inside `deterministic-pixel-art/`, and run Python scripts and one-liners with `python -B` (Skill CLIs skip bytecode automatically; do not run `git status` or clean `__pycache__` inside `deterministic-pixel-art/`).

Python API (add `scripts/` to `sys.path`; import from `pixelart` or `pixel_art`): `Canvas(w, h, background=None)` exposes `.pixel(x, y, color, *, clip=False)`, `.rect(x, y, w, h, color, *, clip=False)`, `.ellipse(x, y, w, h, color, *, outline_color=None, neighborhood=4, thickness=1, hollow=False, clip=False)`, `.paint(pts, color, *, clip=False)`, `.line(pts, color, *, clip=False)`, `.polygon(pts, color, *, clip=False)`, `.bevel(x, y, w, h, tl, br, thickness=1, *, clip=False)`, `.mask(pts, color, outline=None, *, neighborhood=8, thickness=1, clip=False)`, `.mirror(axis='x', *, region=None)`, `.flip(axis='x', *, region=None)`, `.composite(img, x, y, *, clip=False)`, `.to_spec(*, region=None)`, and `.image`; module helpers include `render`, `outline`, `make_preview`, `validate`, `inspect_image`, and `image_to_spec`. Use this starter instead of hand-writing `PIL.Image` loops and grid serializers:

```python
# Run with: python -B make_asset.py
import json, pathlib, sys
sys.path.insert(0, 'deterministic-pixel-art/scripts')
from pixel_art import Canvas
cv = Canvas(48, 48)
cv.ellipse(8, 12, 32, 32, 'C28E36', outline_color='1C140F')
cv.pixel(20, 20, 'FFF8C8')
cv.mirror('x')
pathlib.Path('asset.json').write_text(json.dumps(cv.to_spec()), encoding='utf-8')
```

## Check against intent

Use `preview --image candidate.png --out native.png --scale 1 --background 172033` for a native target-background view; `review` makes diagnostic sheets. `import` creates editable pixels, `replace-cell` updates one atlas member, `recolor` applies declared color mappings within an explicit scope, `verify` checks allowed RGBA changes, and `assemble` places PNG components. If a visual description conflicts with the pixels, follow the [local fact check](references/review.md#when-a-visual-description-conflicts) before revising artwork.

If the filesystem rejects hard links when creating output files, choose a local output directory, use `--portable-output`, or explicitly set `PIXELART_PORTABLE_OUTPUT=1` once in the task shell. CLI and recipes inherit it; `--no-portable-output` overrides it for one command. This mode still refuses to overwrite existing files, but another program may read a new file before writing has finished. Never add `--force` automatically. Task-local environment setup and dependency recovery are in [workflows.md](references/workflows.md). Supported Pillow versions can differ in polygon fill; exact reproduction uses the fixed baseline or an unchanged imported pixel spec.

Check the size, transparency, palette and atlas layout required by the receiving game or application. Transparent margins, binary alpha, symmetry and palette limits apply only when required. Preserve UVs, state order, reserved content and attached opaque edges. Check each named cell's actual direction, function or state against the brief before detail; correct names and layout do not prove the pictured meaning. Then inspect silhouette, lighting/material, set consistency and seams.

UI scenes need real content and the application's actual font to establish text fit; [consumer-ui.md](references/consumer-ui.md) includes the optional `label_atlas.py` helper for actual-font composites, explicit raster mode and state offsets, plus checks for mouse and keyboard behavior. State what remains unchecked when unavailable. Hand-placed antialiasing, dithering and isolated pixels may be intentional. A warning prompts inspection; a report with no warnings still needs visual review. Report concrete changes and tradeoffs, distinguishing author review, independent review and actual in-game tests. [sources.md](references/sources.md) records the external methods and their limits; bundled examples are original artwork.
