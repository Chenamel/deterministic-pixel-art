---
name: deterministic-pixel-art
license: MIT
description: Create or edit deterministic pixel-art PNG sprites, icons, GUI components and named atlases from editable grids, integer drawing commands or Python masks. Includes image measurements with limits on report size, lossless PNG import, visual checks on chosen backgrounds and optional Minecraft styling. Use vector tools for vector icon systems and image generation for photorealistic imagery.
---

# Deterministic Pixel Art

Create editable specifications and exact-grid PNGs with Python and Pillow. Work at native logical resolution and enlarge with nearest-neighbor scaling.

## Choose the shortest useful path

- **Unclear or changing direction in a small flat action icon:** read [action-icons.md](references/action-icons.md) to decide direction and silhouette before detail. Skip this card for color-only edits when the action is already clear.
- **Small edit:** inherit dimensions, palette, lighting, outline and atlas order. Modify only the affected region and check its neighbors. An existing PNG can be imported to an editable spec. Alternatives and a full contact sheet are optional.
- **Text-only work:** read [text-workflow.md](references/text-workflow.md). Use `inspect` for coordinates, colors, components and a size-limited symbol grid; import, edit, render and compare. Measurements do not identify objects or judge beauty.
- **Visual work:** inspect native size and nearest-neighbor enlargement on the intended background. Use [review.md](references/review.md) for contact sheets, named cells, baseline differences, intentional specks and declared functional contrast pairs.
- **Named PNG edit or component scene:** read [workflows.md](references/workflows.md) for named import, single-cell replacement, exact allowed-change checks and PNG assembly. Load it only for these tasks.
- **Parameterized variants or large point lists:** use the [editable recipes](references/recipes.md) for icons, UI states, a 128×128 sprite and a component scene. Change named parameters or short source functions, then regenerate the JSON/PNG; small one-off edits need no recipe.
- **Separately drawn chunks:** read [chunking.md](references/chunking.md) to define chunk boundaries, align repeating textures, connect shapes across seams and check local edits; start with the two-chunk example.

For new artwork, capture meaning, native size, target background, style reference, palette roles, light/outline rules, state names and the requirements of the game or application that will use the image. User references take priority over demo styling. Read only the relevant guide:

- [Pixel art](references/pixel-art.md): silhouettes, clusters, diagonals, form and material.
- [Pixel UI](references/ui.md): hierarchy, spacing, optical weight, state language and text reservations.
- [Minecraft](references/minecraft.md): version-specific slots, bevel seams, UV coordinates and GUI-scale requirements; an optional style.

When a new shape is uncertain, compare two silhouette ideas. For a UI set, establish layout and one representative component before expanding states. Normally stop after two targeted revision rounds; retain unresolved candidates and state the specific remaining issue.

## Represent and render

Read [formats.md](references/formats.md) for the chosen representation or Python API. Prefer grid/palette for small sprites, integer draw operations for geometric components, masks for irregular shapes and named atlases for equal-size states. Mirror only symmetric forms. Rectangles use `x,y,width,height`; unknown symbols and implicit clipping are errors. Primitives replace RGBA; `blit` composites source-over.

Grid transparency needs an explicit palette entry, such as `".":null`. This complete 3×3 spec renders one opaque center pixel; [transparent-grid.json](assets/transparent-grid.json) is a larger example:

```json
{"version":1,"kind":"grid","rows":["...",".X.","..."],"palette":{".":null,"X":"62D8E8"}}
```

Resolve `scripts/pixel_art.py` relative to this skill, not the working directory. Use Python 3.10+ with Pillow >=10.4,<13; the fixed reproduction baseline is Pillow 12.3.0. Install `requirements.txt` in a task-local virtual environment when needed.

```text
python <skill>/scripts/pixel_art.py render --spec scene.json --out candidate.png --preview preview.png --preview-background 172033 --metadata layout.json
python <skill>/scripts/pixel_art.py inspect --image candidate.png --metadata layout.json --cell normal --grid
python <skill>/scripts/pixel_art.py validate --image candidate.png --rules rules.json
```

Omit `--cell` for a non-atlas image. `render --embed-metadata` optionally stores layout for later automatic reuse. Keep the editable spec alongside the PNG. Existing outputs require `--force`; revise accepted art into a separate candidate unless replacement is requested. When revision history is required, retain each reviewed candidate's spec, PNG, layout and generator source before rebuilding. Python APIs include `Canvas`, `render`, `outline`, `make_preview`, `validate`, `inspect_image` and `image_to_spec`; keep task-specific writes behind an entrypoint.

## Check against intent

Use `preview --image candidate.png --out native.png --scale 1 --background 172033` for a native target-background view; `review` makes diagnostic sheets. `import` creates editable pixels, `replace-cell` updates one atlas member, `verify` checks allowed RGBA changes, and `assemble` places PNG components. If a visual description conflicts with the pixels, follow the [local fact check](references/review.md#when-a-visual-description-conflicts) before revising artwork.

If the filesystem rejects hard links when creating output files, choose a local output directory, use `--portable-output`, or explicitly set `PIXELART_PORTABLE_OUTPUT=1` once in the task shell. CLI and recipes inherit it; `--no-portable-output` overrides it for one command. This mode still refuses to overwrite existing files, but another program may read a new file before writing has finished. Never add `--force` automatically. Task-local environment setup and dependency recovery are in [workflows.md](references/workflows.md). Supported Pillow versions can differ in polygon fill; exact reproduction uses the fixed baseline or an unchanged imported pixel spec.

Check the size, transparency, palette and atlas layout required by the receiving game or application. Transparent margins, binary alpha, symmetry and palette limits apply only when required. Preserve UVs, state order, reserved content and attached opaque edges. Check each named cell's actual direction, function or state against the brief before detail; correct names and layout do not prove the pictured meaning. Then inspect silhouette, lighting/material, set consistency and seams.

UI scenes need real content and the application's actual font to establish text fit; [consumer-ui.md](references/consumer-ui.md) includes the optional `label_atlas.py` helper for actual-font composites, explicit raster mode and state offsets, plus checks for mouse and keyboard behavior. State what remains unchecked when unavailable. Hand-placed antialiasing, dithering and isolated pixels may be intentional. A warning prompts inspection; a report with no warnings still needs visual review. Report concrete changes and tradeoffs, distinguishing author review, independent review and actual in-game tests. [sources.md](references/sources.md) records the external methods and their limits; bundled examples are original artwork.
