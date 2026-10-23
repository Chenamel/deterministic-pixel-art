# Editable Python recipes

Use these for repeated variants or a large mask-based asset. Small JSON edits can stay small; an imported PNG remains a pixel specification, not recovered source objects. The recipes are original examples, not a required style or a new input format. Copy a recipe and `_common.py` together when adapting its geometry; use the Skill's runtime as described below.

Run the shipped recipe by absolute path with the same task-local Python/Pillow environment as `pixel_art.py`; no repository checkout is needed:

```text
python <skill>/scripts/recipes/icons.py --out-dir icons --ink F5C26B
python <skill>/scripts/recipes/buttons.py --out-dir buttons --width 64 --content 28 4 30 10 --hover 426B83
python <skill>/scripts/recipes/courier128.py --out-dir courier --stripe E17B57 --stripe-light F9D5A0
python <skill>/scripts/recipes/scene256.py --out-dir scene --roof 684C6A --roof-light A07A89
```

Each produces `asset.json`, `asset.png`, content-bound `layout.json` and a nearest-neighbor `preview.png`. Buttons also produce `context.json`, with absolute reserved-text rectangles derived from the current cell layout; text is drawn by the consumer. These rectangles avoid the recipe's icon/focus/selection pixels. Verify real font fit in the consumer. Omitting `--content` declares no text reservations.

The scene recipe re-renders every small component before assembly and writes `scene/*.json/png`, `project.json`, `assembly.json` and `seams.png`. Its `asset.json` is the self-contained JSON rendering control. The project uses the new component PNGs, never previously generated files. It is a component/crop control, not independently authored seamless chunks.

Omit options to reproduce the bundled reference artwork exactly at the fixed Pillow12.3.0 baseline. Other supported Pillow versions may differ in polygon rasterization. CLI parameters cover frequent variants; the short source functions name shapes and colors. Rendered JSON can remain large: it is the exchange/reproduction output, not necessarily the next file the model should read or edit. For the128px courier, stripe and stripe-light changes stay inside `[42,68,48,10]`; changing hull also changes other surfaces. Check before/after with `verify --allow-region 42 68 48 10`.

Existing outputs are refused as a group. Use a fresh candidate directory, or explicitly `--force` for an authorized rebuild. The recipes reuse staged publication and support `--portable-output` on filesystems rejecting hard links; new portable files can be visible while writing. No cache or background process is required. Compare native-size images and the consumer contract after changing parameters; parameterization does not establish aesthetic quality or token savings.

When copying a recipe outside the Skill folder, keep `_common.py` alongside it and make the original Skill's `scripts` directory available via `PYTHONPATH`. Alternatively edit a task-local copy of the complete Skill folder; avoid changing the shared installed version for one project.
