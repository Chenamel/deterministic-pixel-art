# Specification v1 and Python API

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
