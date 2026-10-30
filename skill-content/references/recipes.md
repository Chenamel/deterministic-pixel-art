# Editable Python recipes

Use these for repeated variants or a large mask-based asset. Small JSON edits can stay small; an imported PNG remains a pixel specification, not recovered source objects. The recipes are original examples, not a required style or a new input format. Copy a recipe and `_common.py` together when adapting its geometry; use the Skill's runtime as described below.

Run the shipped recipe by absolute path with the same task-local Python/Pillow environment as `pixel_art.py`; no repository checkout is needed:

```text
python <skill>/scripts/recipes/icons.py --out-dir icons --ink F5C26B
python <skill>/scripts/recipes/buttons.py --out-dir buttons --width 64 --content 28 4 30 10 --hover 426B83
python <skill>/scripts/recipes/courier128.py --out-dir courier --stripe E17B57 --stripe-light F9D5A0
python <skill>/scripts/recipes/scene256.py --out-dir scene --roof 684C6A --roof-light A07A89
python <skill>/scripts/recipes/chunk_pair.py --out-dir bridge --flag 73A5AA
```

The first four recipes each produce `asset.json`, `asset.png`, `layout.json` with a hash of the source pixels and a nearest-neighbor `preview.png`. Buttons also produce `context.json`, with absolute reserved-text rectangles derived from the current cell layout; text is drawn by the application using the atlas. These rectangles avoid the recipe's icon/focus/selection pixels. Check text fit with the application's actual font using [consumer-ui.md](consumer-ui.md). Omitting `--content` declares no text reservations.

The 64px button example is for short labels: its 30px reservation is not enough for `EXPORT MAP` in Silkscreen 8px. For that measured label use `--width 96 --content 28 4 62 10`, then run `label_atlas.py` as shown in [consumer-ui.md](consumer-ui.md). The optional helper uses actual font bounds and explicit grayscale/monochrome drawing, with configurable state offsets; it does not render text into `asset.png`.

`--content X Y W H` uses half-open bounds `[X,X+W)`, `[Y,Y+H)` in each cell. The button recipe requires `X>=23`, `Y>=4`, `X+W<=width-2`, `Y+H<=14`. `context.json` then stores the translated global regions. For `inspect`/`review`, pass both `--context .../context.json` and `--metadata .../layout.json`; do not add layout fields inside the Context just to recover existing names. `inspect --grid` is limited to 64×64: for a wider named cell, omit `--grid` for facts, or replace `--cell` with a smaller `--region X Y W H` in full-image coordinates.

`chunk_pair.py` instead produces an assembled PNG, local specs and a PNG project. See [chunking.md](chunking.md) for its two independently runnable chunks, repeating textures aligned across the seam and precise flag edit; it has no top-level `asset.json`. The original `scene256.py` below remains a component/control example with different provenance.

The scene recipe re-renders every small component before assembly and writes `scene/*.json/png`, `project.json`, `assembly.json` and `seams.png`. Its `asset.json` is the self-contained JSON rendering control. The project uses the new component PNGs, never previously generated files. It is a component/crop control, not independently authored seamless chunks.

Omit options to reproduce the bundled reference artwork exactly at the fixed Pillow 12.3.0 baseline. Other supported Pillow versions may differ in polygon rasterization. CLI parameters cover frequent variants; the short source functions name shapes and colors. Rendered JSON can remain large: it is the exchange/reproduction output, not necessarily the next file the model should read or edit. For the 128px courier, stripe and stripe-light changes stay inside `[42,68,48,10]`; changing hull also changes other surfaces. Check before/after with `verify --allow-region 42 68 48 10`.

Existing outputs are refused as a group. Use a fresh candidate directory, or explicitly `--force` for an authorized rebuild. The recipes prepare all output files before saving them. They support `--portable-output` on filesystems that reject hard links; in this mode, another program may read a new file before writing has finished. No cache or background process is required. Compare native-size images and the target application's image requirements after changing parameters; parameterization does not establish aesthetic quality or token savings.

When copying a recipe outside the Skill folder, keep `_common.py` alongside it and make the original Skill's `scripts` directory available via `PYTHONPATH`. Alternatively edit a task-local copy of the complete Skill folder; avoid changing the shared installed version for one project.
