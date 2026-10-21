---
name: deterministic-pixel-art
license: MIT
description: Create or edit deterministic pixel-art PNG sprites, icons, GUI components and named atlases from editable grids, integer drawing commands or Python masks. Includes bounded text inspection, lossless PNG import, contextual visual review and optional Minecraft styling. Use vector tools for vector icon systems and image generation for photorealistic imagery.
---

# Deterministic Pixel Art

Create editable specifications and exact-grid PNGs with Python and Pillow. Work at native logical resolution and enlarge with nearest-neighbor scaling.

## Choose the shortest useful path

- **Small edit:** inherit dimensions, palette, lighting, outline and atlas order. Modify only the affected region and check its neighbors. An existing PNG can be imported to an editable spec. Alternatives and a full contact sheet are optional.
- **Text-only work:** read [text-workflow.md](references/text-workflow.md). Use `inspect` for coordinates, colors, components and a bounded symbol grid; import, edit, render and compare. Measurements do not identify objects or judge beauty.
- **Visual work:** inspect native size and nearest-neighbor enlargement on the intended background. Use [review.md](references/review.md) for contact sheets, named cells, baseline differences, intentional specks and declared functional contrast pairs.

For new artwork, capture meaning, native size, target background, style reference, palette roles, light/outline rules, state names and consumer constraints. User references take priority over demo styling. Read only the relevant guide:

- [Pixel art](references/pixel-art.md): silhouettes, clusters, diagonals, form and material.
- [Pixel UI](references/ui.md): hierarchy, spacing, optical weight, state language and text reservations.
- [Minecraft](references/minecraft.md): version-specific slots, bevel seams, UV and GUI-scale contracts; an optional style.

When a new shape is uncertain, compare two silhouette ideas. For a UI set, establish layout and one representative component before expanding states. Normally stop after two targeted revision rounds; retain unresolved candidates and state the specific remaining issue.

## Represent and render

Read [formats.md](references/formats.md) for the chosen representation or Python API. Prefer grid/palette for small sprites, integer draw operations for geometric components, masks for irregular shapes and named atlases for equal-size states. Mirror only symmetric forms. Rectangles use `x,y,width,height`; unknown symbols and implicit clipping are errors. Primitives replace RGBA; `blit` composites source-over.

Resolve `scripts/pixel_art.py` relative to this skill, not the working directory. Use Python 3.10+ with Pillow >=10.4,<13; the fixed reproduction baseline is Pillow 12.3.0. Install `requirements.txt` in a task-local virtual environment when needed.

```text
python <skill>/scripts/pixel_art.py render --spec scene.json --out candidate.png --preview preview.png --metadata layout.json
python <skill>/scripts/pixel_art.py inspect --image candidate.png --metadata layout.json --cell normal --grid
python <skill>/scripts/pixel_art.py validate --image candidate.png --rules rules.json
```

Omit `--cell` for a non-atlas image. `render --embed-metadata` optionally stores layout for later automatic reuse. Keep the editable spec alongside the PNG. Existing outputs require `--force`; revise accepted art into a separate candidate unless replacement is requested. Python APIs include `Canvas`, `render`, `outline`, `make_preview`, `validate`, `inspect_image` and `image_to_spec`; keep task-specific writes behind an entrypoint.

## Check against intent

Validate the consumer's size, alpha, palette and atlas contracts. Transparent margins, binary alpha, symmetry and palette limits apply only when required. Preserve UVs, state order, reserved content and attached opaque edges. Check direction and silhouette before detail, then lighting/material, set consistency, state meaning and seams.

UI scenes need real content and the consumer font to establish text fit; state what remains unchecked when unavailable. Hand-placed antialiasing, dithering and isolated pixels may be intentional. A warning prompts inspection; a clean report is not visual acceptance. Report concrete changes and tradeoffs, distinguishing author review, independent review and actual in-game tests. [sources.md](references/sources.md) records the external methods and their limits; bundled examples are original artwork.
