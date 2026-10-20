"""Package only the tested portable runtime, examples and skill references."""
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]

SKILL = '''---
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
'''

FORMATS = '''# Specification v1 and Python API

`render(spec)` takes a mapping or a DSL string and returns a new RGBA Pillow image. JSON supports `version: 1` (default), `kind`, and the fields below. Unknown keys, non-integer coordinates (including booleans), malformed colors and missing fields are errors. Colors are RRGGBB/RRGGBBAA with optional `#`, byte arrays of length 3/4, or null for transparent black. No antialiasing is performed. General RGBA, including partial alpha, is supported.

## Grid

Required: `kind: grid`, nonempty equal-width string `rows`, and `palette` mapping every single-character symbol to a color. Optional `size` asserts the resulting dimensions. `mirror` is `none` (default), `x`, `y`, or `xy`. A half containing its center column/row uses `center_x: true` / `center_y: true`, so that column/row is not duplicated. Each center flag requires its corresponding mirror axis. See `assets/gem-16.json`.

## Draw

Required: `kind: draw`, `size: [width,height]`, `operations: [...]`. Optional `background` defaults transparent; optional `palette` maps color aliases to colors. An operation's color can use an alias directly. Optional `preset: minecraft` enables button and slot; all other operations are general.

| op | Required fields beyond op | Optional fields |
|---|---|---|
| rect | x, y, w, h, color | clip |
| points | points, color | clip |
| line | points (at least 2), color | clip |
| polygon | points (at least 3), color | clip |
| bevel | x, y, w, h, tl, br | thickness=1, clip |
| mask | points, color | outline, neighborhood=8, thickness=1, clip |
| blit | x, y, source (nested spec) | crop: [x,y,w,h], clip |
| button | x, y, w, h, state | clip; requires Minecraft preset |
| slot | x, y | clip; requires Minecraft preset; fixed 18x18 |

`points` is a list of `[x,y]`; line width is one native pixel. Polygon vertices are integers. Coordinates have origin at the top-left. Rectangle extents are positive and exclude `x+w,y+h`. Clip defaults false. Mask outline uses four-neighbor Manhattan or eight-neighbor square expansion; body paints over its outline. Bevel paints top, bottom, left, right in that order per layer; corner overwrite order is intentional. Blit uses RGBA alpha composition once, not alpha-as-mask paste; crop must lie inside the source even with clip enabled. Operations are applied in order. All source specs are embedded data: there is no code execution or file inclusion field.

See `assets/asymmetric-ship-32.json` and `assets/generic-panel-96x40.json`.

## Atlas and preview

Atlas: `kind: atlas`, positive `columns`, `cells: [{name, spec}, ...]`, optional background. Names must be unique; cells render to identical dimensions. Cells are arranged left to right, then top to bottom; the last row can contain unused transparent cells. Columns cannot exceed cell count. In Python, `image.info['pixelart']` contains `cell_size`, `columns`, `rows`, and named `{x,y,w,h}` cell rectangles. The CLI's `--metadata` writes this under `atlas`, plus image size and mode. See `assets/minecraft-button-states.json`.

Preview: `kind: preview`, `source` nested spec, `scale` positive integer (default 8), and `background` (`checker` by default, a color, or null). Preview pixels are nearest-neighbor replicas; the background is composited only into the preview, leaving source transparency intact.

## DSL

Select the DSL in the CLI using a `.dsl` filename. Commands are uppercase, one per line, with whitespace-separated arguments. Blank lines and lines starting with `#` are ignored. No inline comments. Exactly one CANVAS must appear before drawing.

```text
CANVAS 128 48
BG C6C6C6
BEVEL 0 0 128 48 FFFFFF 555555 1
SLOT 8 8
RECT 30 8 18 18 373737
BTN 74 15 46 18 NORMAL
```

Commands: `CANVAS w h`, `BG color`, `RECT x y w h color`, `BEVEL x y w h tl br thickness`, `SLOT x y`, `BTN x y w h state`. The DSL selects the Minecraft preset; it does not permit implicit clipping. Errors report their source line. The two legacy demo DSL specs remain pixel-compatible for valid input.

## Validation

`validate(image, rules)` returns `{valid, errors: [{rule,message}], facts: {size,mode,colors,alpha}}`. Invalid rule syntax raises `PixelArtError`; image contract violations set valid=false. The CLI exits 0 for success, 1 for a contract violation and 2 for input/I/O errors. No output files are created when rendering/specification validation fails; filesystem failures can leave already-written files.

Rules (all optional): `size: [w,h]`, `mode: RGBA`, `alpha: [0,255]`, `palette: [colors...]`, positive `max_colors`, boolean `nonempty`, `cell_size: [w,h]`, integer `transparent_margin`, and `expected_pixels: [{at:[x,y],color:...}]`. Cell size must divide the canvas; margins apply to every cell, not only the outer image border. Palette checks count complete RGBA values, including transparent pixels. State meaning/order comes from atlas metadata and the consumer's contract, not image-only validation.

```json
{"size":[80,16],"mode":"RGBA","alpha":[0,255],"nonempty":true,"cell_size":[16,16],"transparent_margin":1}
```

## Custom Python

Add the skill's `scripts/` directory to sys.path, then:

```python
from pixelart import Canvas, outline, render, make_preview, validate
canvas = Canvas(16, 16)
canvas.rect(3, 3, 10, 10, '#36CFC9')
canvas.mask({(7,7), (8,7), (7,8)}, '#F7B955', '#16223D', neighborhood=4)
image = canvas.image
report = validate(image, {'size':[16,16], 'mode':'RGBA', 'alpha':[0,255]})
```

`Canvas` exposes `rect`, `paint`, `line`, `polygon`, `bevel`, `mask`, and `composite`; the image is `.image`. Python coordinates use the same conventions as JSON. `outline(points, neighborhood=8, thickness=1)` returns edge coordinates; `make_preview(image, scale=8, background='checker')` returns a new image. Use `image.save(path, format='PNG')` only in your recipe's entrypoint. Built-in limits: 8192 per side, 16,777,216 pixels, 24 nested spec levels and outline radius <=64. Limits apply to previews and atlases too. Tested runtime: Python 3.14.2, Pillow 12.3.0; other Python/platform combinations require their own validation.
'''

MINECRAFT = '''# Optional Minecraft styling

Select `preset: minecraft` for JSON button/slot operations. The DSL selects it automatically. These are reusable demo conventions, not a promise to match every Minecraft version or mod's artwork; an existing project's asset contract takes priority.

- Panel grey: C6C6C6. Slot: 18x18, fill 8B8B8B, top/left 373737 and bottom/right FFFFFF.
- Button state names: NORMAL, HOVER, PRESSED, SELECTED, DISABLED. Minimum 4x4. NORMAL/HOVER/PRESSED preserve the original demo palette. SELECTED is neutral recessed A0A0A0; DISABLED uses 707070. See `assets/minecraft-button-states.json`.
- Raised controls generally have bright top-left and dark bottom-right; recessed controls reverse that relationship. Distinguish state by silhouette/position when color alone is ambiguous.
- For assets targeting binary transparency, validate alpha [0,255]. Set cell_size and transparent_margin only if that specific atlas requires them. Opaque attached controls should stay opaque.
- Keep native logical sizes, source UVs, state order and reserved content regions from the target project. Do not impose a universal 16x16 content area or transparent border.
- For new icon sets, an optional mode palette is grey A0A0A0, input 559FE8, output E36B6B, bidirectional B679D1, cache 6DBB78. Existing accepted artwork may use different shades.

For an existing mod, generate a candidate asset and compare native-size composites. The generic renderer does not install files into a resource tree or claim in-game visual acceptance.
'''


def main():
    metrics = json.loads((ROOT / 'evaluation/metrics.json').read_text(encoding='utf-8'))
    if not metrics['quality_gate_passed'] or not metrics['fixtures_unchanged']:
        raise RuntimeError('Packaging requires a passing quality gate')
    current_runtime = {p.relative_to(ROOT / 'src').as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in sorted((ROOT / 'src').rglob('*.py'))}
    if metrics.get('runtime_sha256') != current_runtime:
        raise RuntimeError('Runtime changed since evaluation; rerun evaluate.py before packaging')
    skill = ROOT / 'skill/deterministic-pixel-art'
    for sub in ('scripts/pixelart', 'references', 'assets', 'agents'):
        (skill / sub).mkdir(parents=True, exist_ok=True)
    files = {'SKILL.md': SKILL, 'references/formats.md': FORMATS, 'references/minecraft.md': MINECRAFT,
        'agents/openai.yaml': '''interface:
  display_name: "确定性像素资产"
  short_description: "通过网格、整数绘图和可选 Minecraft 预设生成并校验像素资产"
  default_prompt: "使用 $deterministic-pixel-art 生成可编辑、可复现的像素资产并检查原尺寸预览。"
policy:
  allow_implicit_invocation: true
'''}
    for relative, content in files.items():
        (skill / relative).write_text(content, encoding='utf-8', newline='\n')
    shutil.copyfile(ROOT / 'requirements.txt', skill / 'requirements.txt')
    shutil.copyfile(ROOT / 'LICENSE', skill / 'LICENSE')
    shutil.copyfile(ROOT / 'src/pixel_art.py', skill / 'scripts/pixel_art.py')
    for path in sorted((ROOT / 'src/pixelart').glob('*.py')):
        shutil.copyfile(path, skill / 'scripts/pixelart' / path.name)
    for path in sorted((ROOT / 'examples').glob('*.json')):
        shutil.copyfile(path, skill / 'assets' / path.name)
    manifest = {p.relative_to(skill).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(skill.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
    (ROOT / 'evaluation/package-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    archive = ROOT / 'deterministic-pixel-art.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as bundle:
        for relative in manifest:
            # Fixed timestamps and permissions make identical sources reproducible.
            entry = zipfile.ZipInfo(f'deterministic-pixel-art/{relative}', (1980, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            entry.compress_type = zipfile.ZIP_DEFLATED
            bundle.writestr(entry, (skill / relative).read_bytes())
    print(json.dumps({'skill': str(skill), 'files': len(manifest), 'zip_bytes': archive.stat().st_size}))


if __name__ == '__main__':
    main()
