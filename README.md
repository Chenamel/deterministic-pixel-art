# Deterministic Pixel Art

[简体中文](README.zh-CN.md) · [MIT license](LICENSE) · [Specification and Python API](skill/deterministic-pixel-art/references/formats.md)

Create editable pixel-art PNGs from character grids, integer drawing commands, masks, and named sprite atlases. Rendering uses Python and Pillow, with exact pixel coordinates and nearest-neighbor previews. Minecraft GUI styling is an optional preset.

![Original UI studies: frozen baseline on the left, candidate on the right](docs/quality/ui.png)

## Quick start

The reproducibility baseline is Python 3.14.2 with Pillow 12.3.0. Runtime compatibility checks also cover Pillow 10.4, 11.3 and 12.1 on Python 3.10+. From a checkout, create a virtual environment and activate it:

```sh
python -m venv .venv
```

Windows PowerShell: `.\.venv\Scripts\Activate.ps1`

macOS/Linux shell: `source .venv/bin/activate`

```sh
python -m pip install -r requirements.txt
python src/pixel_art.py render --spec examples/gem-16.json --out output/gem.png --preview output/gem-preview.png
python src/pixel_art.py validate --image output/gem.png
python src/pixel_art.py inspect --image output/gem.png --grid
python src/pixel_art.py review --image output/gem.png --out-dir output/gem-review
```

Use absolute script/input/output paths when running from another working directory. Existing outputs require an explicit `--force` to overwrite.

## Pick an example

| Example | Use it for |
|---|---|
| [gem-16.json](examples/gem-16.json) | A mirrored 16×16 sprite with a custom palette |
| [asymmetric-ship-32.json](examples/asymmetric-ship-32.json) | A 32×32 asymmetric sprite drawn with polygons |
| [generic-panel-96x40.json](examples/generic-panel-96x40.json) | A GUI panel with a non-Minecraft palette |
| [minecraft-button-states.json](examples/minecraft-button-states.json) | A named atlas of five optional Minecraft-style button states |
| [quality/](examples/quality/) | Eight editable studies: icons, materials, UI states, layout and Minecraft controls |

Keep the spec alongside the resulting PNG. Inspect native-size artwork and a magnified preview; dimensions alone cannot verify direction, state meaning, or readability.

The **v1.2.0-rc.1 candidate** adds bounded textual pixel facts, exact PNG-to-spec import and optional layout reuse. For an existing PNG, run `python src/pixel_art.py import --image existing.png --out editable.json`, edit the spec, render a separate candidate and inspect it with `--compare existing.png`. No color quantization is applied; decoded 8-bit RGBA, including hidden RGB, is preserved. See the [text workflow](skill/deterministic-pixel-art/references/text-workflow.md).

`review` writes a contact sheet and advisory JSON report with native/enlarged views, light/dark backgrounds, grayscale and optional named atlas cells, sprite silhouettes and baseline differences. Pass a [review context](skill/deterministic-pixel-art/references/review.md) to declare backgrounds, reserved content and functional color pairs. Warnings return success; malformed inputs return an error. It never edits the source image or assigns an aesthetic score.

The [format reference](skill/deterministic-pixel-art/references/formats.md) covers JSON v1, the compact GUI DSL, `render(spec)`, `Canvas`, validation rules, and atlas metadata. Invalid symbols, unknown commands, and implicit clipping produce errors. Rectangles use `x, y, width, height`.

## Use as a Codex skill

Download the Skill ZIP and SHA-256 manifest from [Releases](https://github.com/Chenamel/deterministic-pixel-art/releases). Release tags pin the runtime and guidance together; `v1.0.0` preserves the previous stable baseline. Verify the checksum, then extract the self-contained `deterministic-pixel-art` folder into your Codex skills directory (`$CODEX_HOME/skills`, or `~/.codex/skills` by default), and install its `requirements.txt` in a Python environment available to your task. Back up any previous installation outside the skills directory. The same folder is available at [skill/deterministic-pixel-art](skill/deterministic-pixel-art/SKILL.md).

Example request: “Use `$deterministic-pixel-art` to create four 16×16 directional icons in a named horizontal atlas, with a transparent one-pixel margin and an enlarged preview.”

Build a tested ZIP with `python -B tools/check.py` after installing the development dependencies below. The ZIP is generated locally, rather than committed. No global skill installation happens during the checks.

## What improved, and what did not

v1.2.0-rc.1 is a candidate: automated checks establish the new measurements and exact round trips. External paired agent trials are pending; workflow time, correction-round savings and general aesthetic improvement are not yet established. The [candidate report and evaluation protocol](docs/audit-v1.2.md) separate measured capabilities from these pending outcomes. The latest stable release remains v1.1.1.

In one local Windows comparison with v1.1.0, full render/review command medians increased by 15.0/16.7 ms (about 9%); the sample review JSON grew from 1,237 to 6,999 bytes. Pure rendering was essentially unchanged. These costs are reported separately from agent workflow outcomes.

v1.1.1 fixes null mask outlines, primary review backgrounds, wide-image sheets and output publication failures. It adds precise diagnostics and a Pillow compatibility boundary. See the [external-feedback and reliability report](docs/audit-feedback.md); these fixes make no new aesthetic-improvement claim.

The visual-quality update adds task-specific art direction, eight original editable studies and contextual review. In an **author self-review of eight paired tasks**, six were preferred and two retained their exact pixels. All **43 v1.0.0 migration outputs remain pixel-compatible**. JSON v1, existing public Python interfaces and previous commands are preserved. This is a small, unblinded authored study, not independent evidence of a general model-quality improvement. Actual fonts and in-game integration were not tested. See the [quality report](docs/quality-report.md), [Chinese report](docs/quality-report.zh-CN.md) and [raw study results](docs/measurements/visual-quality.json).

The earlier rendering optimization remains a separate historical comparison:

The initial Windows comparison preserved 40 of 43 legacy images pixel-for-pixel. Three declared changes fix incomplete button compositions or align a footer with the resource actually in use.

| Pure rendering case | Original → new median | Speedup |
|---|---:|---:|
| 128×48 panel | 1.3364 → 0.1519 ms | 8.80× |
| 16×16 block face | 0.3214 → 0.1032 ms | 3.11× |
| 80×16 atlas | 0.5105 → 0.4381 ms | 1.17× |

These are measured results from one environment, excluding process startup and disk I/O. The equivalent full command became **47.03 ms slower (+35%)**; atlas tail latency and some Python allocation peaks also increased. Token savings, fewer model correction rounds, and in-game quality were not measured. See the [detailed report in Chinese](docs/optimization-report.zh-CN.md) and [raw measurements](docs/measurements/metrics.json).

Further render-speed tuning has limited absolute benefit for these sub-millisecond assets. The quality update makes no workflow-speed or token-saving claim. More detailed examples can require more colors and drawing operations.

## Development checks

```sh
python -m pip install -r requirements-dev.txt
python -B tools/check.py
```

This runs 61 unit tests, 43 image regressions, integrity checks for 86 historical fixture files and eight frozen study baselines, eight exact import/inspection tasks, benchmarks, reproducible ZIP packaging, and 45 artifact checks from an unrelated directory containing spaces and Chinese characters. It needs no original mod checkout or Codex installation. Results are written to ignored `output/` and `evaluation/` directories.

When the official skill-creator validator is available, also run:

```sh
python -B tools/test_skill.py --python /path/to/python --validator /path/to/quick_validate.py
```

The default project-local validator checks metadata and references; it is not the official validator. GitHub Actions is configured for Python 3.14 on Windows and Ubuntu. Platform validation is established by completed runs, not by the workflow file alone.

`src/` holds the runtime, `skill-content/` holds maintained instructions and references, and `skill/` is the generated distribution. Make changes in the source directories, then run the checks to synchronize the skill. `tools/package_skill.py` copies these sources and records every packaged file. `quality/` preserves study briefs, frozen baselines, alternatives and self-review records. `baselines/` contains curated historical fixtures; see [provenance](docs/PROVENANCE.md). The complete original-project preservation archive remains outside this repository.

## License

[MIT](LICENSE), including the standalone skill. Pillow and the development-only PyYAML are installed dependencies and are not vendored.
