---
name: deterministic-pixel-art
license: MIT
description: Create or edit deterministic pixel-art PNG assets from text grids, palettes, integer drawing commands, or Python pixel masks. Use for sprites, icons, pixel GUI components and sprite atlases, including optional Minecraft styling. Use existing vector tools for SVG/icon-system edits and image generation tools for photorealistic imagery.
---

# Deterministic Pixel Art

Create editable specifications and exact-grid PNG assets using Python and Pillow; no image-generation API is needed. Work at the asset's native logical resolution and preview with nearest-neighbor scaling.

## Choose the representation

- Use grid + palette for small sprites; mirror only shapes that are actually symmetric. Unknown symbols are errors, including `.` unless explicitly mapped to null.
- Use draw operations for geometric GUI components and masks for irregular silhouettes. Rectangles use **x, y, width, height**, never inclusive end coordinates.
- Use an atlas for named, equal-size states. Preserve the consumer's existing dimensions, cell order, UVs and margins when editing an asset.
- Use the compact DSL for simple Minecraft panels. Choose JSON or the Python API for general artwork, custom masks, explicit clipping and composition.

Read [formats.md](references/formats.md) for the selected format/API. Read [minecraft.md](references/minecraft.md) only when Minecraft styling is wanted. Do not apply that preset's palette or transparency constraints to unrelated assets.

## Run and inspect

Use an available Python with Pillow. The tested dependency is pinned in `requirements.txt`; install it into a task-local virtual environment if needed. Resolve `scripts/pixel_art.py` relative to this skill, not the working directory.

```text
python <skill>/scripts/pixel_art.py render --spec scene.json --out sprite.png --preview preview.png --metadata layout.json
python <skill>/scripts/pixel_art.py validate --image sprite.png --rules rules.json
python <skill>/scripts/pixel_art.py preview --image sprite.png --out grey-preview.png --background C6C6C6 --scale 8
```

Start from the relevant JSON example in `assets/` rather than copying renderer code. Keep the editable spec with the generated asset. Output paths must be explicit; existing files are refused unless `--force` is supplied. Generate a separate candidate when revising existing artwork unless overwriting is part of the user's request.

Validate dimensions, RGBA mode, intended alpha values and relevant cell contracts. Transparent margins are a requested rule, not a universal requirement; opaque panels and opaque atlas cells are valid. Partial alpha is supported; restrict to 0/255 when the target requires it. Out-of-bounds drawing fails unless that operation sets `clip: true`.

Inspect both native-size output and an enlarged preview. Check silhouette, arrow direction, distinct states, cell boundaries and contrast against the intended background. For UI assets, also composite onto the real component at 1:1; a large preview alone does not establish readability. Fix the spec and rerender when defects are observed. Do not describe automated checks as a blind visual review or claim in-game verification without doing it.

For custom Python recipes, import `Canvas`, `render`, `outline`, `make_preview`, and `validate` from `scripts/pixelart`; put geometry in the task's recipe and keep file writes behind an explicit entrypoint. Importing the supplied runtime does not write files.
