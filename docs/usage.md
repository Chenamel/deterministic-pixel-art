# Command examples

[中文](usage.zh-CN.md) · [README](../README.md)

Run these from the repository root after the README setup. They describe the v1.2.0 checkout; older stable packages have fewer commands. Use absolute paths from another working directory. For an installed Skill, replace `src/pixel_art.py` with its `scripts/pixel_art.py`, `examples/` with its `assets/`, and `recipes/` with its `scripts/recipes/`.

## Edit a named atlas cell

Export one named cell without hand-copying layout coordinates:

```sh
python src/pixel_art.py import --image examples/workflows/atlas-before.png --metadata examples/workflows/atlas-before-layout.json --cell transfer --out output/transfer.json
```

Edit `output/transfer.json`, then replace that cell and verify the allowed change region:

```sh
python src/pixel_art.py replace-cell --spec examples/workflows/atlas-editable.json --cell transfer --replacement output/transfer.json --out output/candidate.json --image-out output/candidate.png --metadata output/candidate-layout.json
python src/pixel_art.py verify --image output/candidate.png --compare examples/workflows/atlas-before.png --allow-region 32 0 16 16
```

Without editing the exported cell, replacement should change zero pixels. Full-image import is also available. Decoded 8-bit RGBA is preserved, including hidden RGB; original layers and drawing instructions are not recovered.

## Inspect or review

```sh
python src/pixel_art.py inspect --image output/gem.png --grid
python src/pixel_art.py review --image output/gem.png --out-dir output/gem-review
```

Inspection gives bounded pixel facts; review adds diagnostic views. See [context and named layouts](../skill/deterministic-pixel-art/references/review.md) to choose target backgrounds and interpret warnings. Neither command automatically judges beauty or object meaning.

## Use editable recipes

```sh
python recipes/icons.py --out-dir output/icons --ink F5C26B
python recipes/buttons.py --out-dir output/buttons --width 96 --content 23 4 70 10
python recipes/chunk_pair.py --out-dir output/bridge
```

Recipes export editable specs and PNGs. [Actual-font checks](../skill/deterministic-pixel-art/references/consumer-ui.md) and the [browser UI demo](../demos/pixel-ui/README.md) cover separate consumer concerns; they do not establish arbitrary font or Minecraft integration support.

## Recover from environment problems

Existing outputs require explicit `--force`; use a fresh candidate directory to preserve accepted work. If a filesystem rejects hard links, choose a local destination or `--portable-output`. Since v1.2.0, set it once in the task shell: `$env:PIXELART_PORTABLE_OUTPUT = '1'` in PowerShell, or `export PIXELART_PORTABLE_OUTPUT=1` in POSIX shells. CLI and recipes inherit it; `--no-portable-output` overrides one command. No-overwrite remains, but new portable files can be visible while writing.

[Detailed environment recovery](../skill/deterministic-pixel-art/references/workflows.md) includes task-local environments and missing-pip cases. Keep the same Python executable for dependencies and commands. Use the pinned Pillow baseline for exact reproduction; supported Pillow versions can differ in polygon fill.
