---
name: deterministic-pixel-art
license: MIT
description: Create or edit deterministic pixel-art PNG sprites, icons, GUI components and named sprite atlases from editable text grids, integer drawing commands or Python pixel masks. Includes reference-informed art direction, contextual visual review and optional Minecraft styling. Use existing vector tools for vector icon systems and image generation tools for photorealistic imagery.
---

# Deterministic Pixel Art

Create editable specifications and exact-grid PNGs with Python and Pillow. Work at native logical resolution; enlarge with nearest-neighbor scaling.

## Select the effort and reference

For a small edit, inherit the accepted artwork's dimensions, palette, light direction, outline and atlas contract; inspect the edited area and its neighbors. Do not redesign the set without a reason in the request.

For new assets, capture a short brief: meaning, native size, intended background, style reference, palette roles, outline/light convention, state names and consumer constraints. User-provided reference art takes priority over demo styling. Read only the relevant guide:

- [Pixel art](references/pixel-art.md): silhouette, clusters, diagonals, form and material; start with `assets/quality/ship-32.json` or `materials-32.json`.
- [Pixel UI](references/ui.md): hierarchy, spacing, optical weight, state language and text reservations; start with `assets/quality/ui-states.json` or `ui-panel.json`.
- [Minecraft](references/minecraft.md): target-version conventions, slots, bevel seams and UV/GUI-scale contracts. It is optional, never a universal palette.

For a new sprite or icon, compare two silhouette ideas when the shape is uncertain, then develop the clearer one. For a UI set, establish layout and a representative component before expanding its states. Normally allow up to two targeted revision rounds; a small edit need not produce alternatives. Retain unresolved candidates and describe the specific remaining issue instead of claiming acceptance.

## Represent and render

Read [formats.md](references/formats.md) for the chosen format or API. Use grid + palette for small sprites, draw operations for geometric components, masks for irregular silhouettes, and named atlases for equal-size states. Mirror only genuinely symmetric forms. Use the compact DSL for simple Minecraft panels. Rectangle arguments are `x, y, width, height`; unknown symbols and implicit clipping are errors.

Resolve `scripts/pixel_art.py` relative to this skill, not the working directory. Use an available Python with Pillow; if needed, install `requirements.txt` in a task-local virtual environment.

```text
python <skill>/scripts/pixel_art.py render --spec scene.json --out sprite.png --preview preview.png --metadata layout.json
python <skill>/scripts/pixel_art.py validate --image sprite.png --rules rules.json
python <skill>/scripts/pixel_art.py review --image sprite.png --out-dir review --context context.json --compare previous.png
```

Keep the editable spec alongside the PNG. Choose explicit output paths; existing files require `--force`. When revising accepted artwork, use a separate candidate unless replacement is requested. Python recipes may import `Canvas`, `render`, `outline`, `make_preview` and `validate` from the skill's `scripts/pixelart`; keep task-specific writes behind an entrypoint.

## Inspect against intent

Validate size, mode, intended alpha values and atlas contracts. Transparency margins, binary alpha and palette limits apply only when the consumer requires them. Preserve UVs, cell order, reserved content and attached opaque edges.

Inspect 1:1 and enlarged output on the intended background. Check silhouette and direction before detail; then light/material, set consistency, named states and component seams. UI artwork needs a native-size scene composite; test text reservations with real content and the consumer's font. If that font or runtime is unavailable, state which checks remain unverified.

Use [review.md](references/review.md) when arranging review sheets, per-cell inspection, intentional-speck exceptions or functional contrast pairs. The tool does not alter artwork or judge beauty. A warning is a prompt to inspect; a clean report is not visual acceptance. Revise the spec only when the observed issue conflicts with the brief. Hand-placed antialiasing, dithering, extra colors and isolated pixels may be intentional.

Describe concrete improvements and any tradeoffs. Distinguish author self-review, independent review and actual in-game testing. See [sources.md](references/sources.md) for the external methods and their limits; examples are original work, not bundled third-party artwork.
