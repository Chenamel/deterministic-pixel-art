# Deterministic Pixel Art

[简体中文](README.zh-CN.md) · [MIT license](LICENSE) · [Specification and Python API](skill/deterministic-pixel-art/references/formats.md)

Create editable pixel-art PNGs from character grids, integer drawing commands, masks, and named sprite atlases. Rendering uses Python and Pillow, with exact pixel coordinates and nearest-neighbor previews. Minecraft GUI styling is an optional preset.

![Asset comparisons and generic examples](docs/comparison.png)

## Quick start

The tested runtime is Python 3.14.2 with Pillow 12.3.0. From a checkout, create a virtual environment and activate it:

```sh
python -m venv .venv
```

Windows PowerShell: `.\.venv\Scripts\Activate.ps1`

macOS/Linux shell: `source .venv/bin/activate`

```sh
python -m pip install -r requirements.txt
python src/pixel_art.py render --spec examples/gem-16.json --out output/gem.png --preview output/gem-preview.png
python src/pixel_art.py validate --image output/gem.png
```

Use absolute script/input/output paths when running from another working directory. Existing outputs require an explicit `--force` to overwrite.

## Pick an example

| Example | Use it for |
|---|---|
| [gem-16.json](examples/gem-16.json) | A mirrored 16×16 sprite with a custom palette |
| [asymmetric-ship-32.json](examples/asymmetric-ship-32.json) | A 32×32 asymmetric sprite drawn with polygons |
| [generic-panel-96x40.json](examples/generic-panel-96x40.json) | A GUI panel with a non-Minecraft palette |
| [minecraft-button-states.json](examples/minecraft-button-states.json) | A named atlas of five optional Minecraft-style button states |

Keep the spec alongside the resulting PNG. Inspect native-size artwork and a magnified preview; dimensions alone cannot verify direction, state meaning, or readability.

The [format reference](skill/deterministic-pixel-art/references/formats.md) covers JSON v1, the compact GUI DSL, `render(spec)`, `Canvas`, validation rules, and atlas metadata. Invalid symbols, unknown commands, and implicit clipping produce errors. Rectangles use `x, y, width, height`.

## Use as a Codex skill

The self-contained [skill/deterministic-pixel-art](skill/deterministic-pixel-art/SKILL.md) folder contains its runtime, examples, references, and MIT license. Copy that folder to your Codex skills directory (`$CODEX_HOME/skills`, or `~/.codex/skills` by default), and install its `requirements.txt` in a Python environment available to your task.

Example request: “Use `$deterministic-pixel-art` to create four 16×16 directional icons in a named horizontal atlas, with a transparent one-pixel margin and an enlarged preview.”

Build a tested ZIP with `python -B tools/check.py` after installing the development dependencies below. The ZIP is generated locally, rather than committed. No global skill installation happens during the checks.

## What improved, and what did not

The initial Windows comparison preserved 40 of 43 legacy images pixel-for-pixel. Three declared changes fix incomplete button compositions or align a footer with the resource actually in use.

| Pure rendering case | Original → new median | Speedup |
|---|---:|---:|
| 128×48 panel | 1.3364 → 0.1519 ms | 8.80× |
| 16×16 block face | 0.3214 → 0.1032 ms | 3.11× |
| 80×16 atlas | 0.5105 → 0.4381 ms | 1.17× |

These are measured results from one environment, excluding process startup and disk I/O. The equivalent full command became **47.03 ms slower (+35%)**; atlas tail latency and some Python allocation peaks also increased. Token savings, fewer model correction rounds, and in-game quality were not measured. See the [detailed report in Chinese](docs/optimization-report.zh-CN.md) and [raw measurements](docs/measurements/metrics.json).

Further render-speed tuning has limited absolute benefit for these sub-millisecond assets. Batch CLI support may help repeated invocations, but has not been implemented or benchmarked. Current release work focuses on portable tests and reproducible packaging.

## Development checks

```sh
python -m pip install -r requirements-dev.txt
python -B tools/check.py
```

This runs 24 unit tests, 43 image regressions, integrity checks for 86 frozen fixture files, benchmarks, reproducible ZIP packaging, and 19 artifact checks from an unrelated directory containing spaces and Chinese characters. It needs no original mod checkout or Codex installation. Results are written to ignored `output/` and `evaluation/` directories.

When the official skill-creator validator is available, also run:

```sh
python -B tools/test_skill.py --python /path/to/python --validator /path/to/quick_validate.py
```

The default project-local validator checks metadata and references; it is not the official validator. GitHub Actions is configured for Python 3.14 on Windows and Ubuntu. Platform validation is established by completed runs, not by the workflow file alone.

`src/` is the runtime source, `skill/` is the generated distribution, and `tools/package_skill.py` holds its instruction/reference sources. Make runtime changes in `src/`, then run the checks to synchronize the skill. `baselines/` contains curated historical fixtures; see [provenance](docs/PROVENANCE.md). The complete original-project preservation archive remains outside this repository.

## License

[MIT](LICENSE), including the standalone skill. Pillow and the development-only PyYAML are installed dependencies and are not vendored. Repository visibility is managed separately from the license; the initial repository is private.
