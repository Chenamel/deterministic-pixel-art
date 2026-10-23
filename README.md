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
| [transparent-grid.json](examples/transparent-grid.json) | A complete minimal transparent grid |
| [workflows/](examples/workflows/) | Named-cell editing, an original native 128×128 courier and a 256×256 component/tile scene |
| [Independent chunk demo](demos/chunk-scene/README.md) | Four separately authored 128px sources, frozen seam contract, file assembly and an exact single-chunk edit |

Keep the spec alongside the resulting PNG. Inspect native-size artwork and a magnified preview; dimensions alone cannot verify direction, state meaning, or readability.

The **published v1.2.0-rc.2 candidate** adds named PNG editing, exact allowed-change checks and component assembly to the existing textual inspection and lossless import tools. For an existing PNG, run `python src/pixel_art.py import --image existing.png --out editable.json`; add `--metadata layout.json` to retain named atlas cells. No color quantization is applied; decoded 8-bit RGBA, including hidden RGB, is preserved. See the [text workflow](skill/deterministic-pixel-art/references/text-workflow.md).

For an existing named atlas, replace one cell and prove that other pixels are unchanged:

```sh
python src/pixel_art.py import --image examples/workflows/atlas-before.png --metadata examples/workflows/atlas-before-layout.json --out output/editable.json
python src/pixel_art.py replace-cell --spec output/editable.json --cell transfer --replacement examples/workflows/atlas-replacement.json --out output/candidate.json --image-out output/candidate.png --metadata output/candidate-layout.json
python src/pixel_art.py verify --image output/candidate.png --compare examples/workflows/atlas-before.png --allow-region 32 0 16 16
python src/pixel_art.py assemble --project examples/workflows/scene-tiles.json --out output/scene.png --report output/assembly.json --seams output/seams.png
```

![Original courier at native 128×128, shown at 3× nearest-neighbor](docs/workflows/sprite-128-preview.png)
![Original 256×256 watermill scene, shown at 2×](docs/workflows/scene-256-preview.png)

The [editing and assembly guide](skill/deterministic-pixel-art/references/workflows.md) explains masks, component cropping, explicit copy/composite behavior and boundary ownership. `render --preview-background E9EDF2` selects a target background. On a filesystem that rejects hard links, explicitly choose `--portable-output` or a local output directory. Portable publication preserves no-overwrite, but newly created files can be visible while being written.

`review` writes a contact sheet and advisory JSON report with native/enlarged views, light/dark backgrounds, grayscale and optional named atlas cells, sprite silhouettes and baseline differences. Pass a [review context](skill/deterministic-pixel-art/references/review.md) to declare backgrounds, reserved content and functional color pairs. Warnings return success; malformed inputs return an error. It never edits the source image or assigns an aesthetic score.

The [format reference](skill/deterministic-pixel-art/references/formats.md) covers JSON v1, the compact GUI DSL, `render(spec)`, `Canvas`, validation rules, and atlas metadata. Invalid symbols, unknown commands, and implicit clipping produce errors. Rectangles use `x, y, width, height`.

## Editable recipes (local rc.3)

For repeated variants, use the shipped Python recipes instead of editing expanded point lists:

```sh
python recipes/icons.py --out-dir output/icons --ink F5C26B
python recipes/buttons.py --out-dir output/buttons --width 64 --content 28 4 30 10 --hover 426B83
python recipes/courier128.py --out-dir output/courier --stripe E17B57 --stripe-light F9D5A0
```

In an extracted Skill, resolve these at `<skill>/scripts/recipes/`. Defaults retain exact reference pixels at Pillow 12.3.0; changed outputs include independent JSON/PNG/layout. [Recipe results and costs](docs/recipe-workflows.md): the ZIP grows 4.3%. See the actual-font consumer example below for text and interaction checks.

## Real PNG consumer demo

```sh
python tools/build_consumer_demo.py --force
python -m http.server 8765 --bind 127.0.0.1 --directory demos/pixel-ui
```

Open `http://127.0.0.1:8765/`. The [repository-only demo](demos/pixel-ui/README.md) uses named PNG atlas cells, a bundled Latin pixel font, native keyboard/mouse controls and 1/2/3× scaling. Compare the preserved 64px baseline with the 96px revision: the actual `EXPORT MAP` label now fits. [Consumer findings and limits](docs/consumer-ui-report.md): 89 source tests, 43 stable images and 77 isolated ZIP cases pass; the sealed Skill ZIP is unchanged. No Minecraft or Chinese-font acceptance is claimed.

## Use as a Codex skill

Download the Skill ZIP and SHA-256 manifest from [Releases](https://github.com/Chenamel/deterministic-pixel-art/releases). Release tags pin the runtime and guidance together; `v1.0.0` preserves the previous stable baseline. Verify the checksum, then extract the self-contained `deterministic-pixel-art` folder into your Codex skills directory (`$CODEX_HOME/skills`, or `~/.codex/skills` by default), and install its `requirements.txt` in a Python environment available to your task. Back up any previous installation outside the skills directory. The same folder is available at [skill/deterministic-pixel-art](skill/deterministic-pixel-art/SKILL.md).

Example request: “Use `$deterministic-pixel-art` to create four 16×16 directional icons in a named horizontal atlas, with a transparent one-pixel margin and an enlarged preview.”

Build a tested ZIP with `python -B tools/check.py` after installing the development dependencies below. The ZIP is generated locally, rather than committed. No global skill installation happens during the checks.

## What improved, and what did not

v1.2.0-rc.2 is a published prerelease. Eight external exploratory tasks supplied useful feedback; all 10 main final PNGs were reproduced exactly in the fixed baseline environment. They are not the previously proposed controlled A/B trials. The [current workflow report](docs/workflow-report.md) records the fixes, exact edit/assembly checks and limits; the [earlier candidate protocol](docs/audit-v1.2.md) remains historical. Workflow time, correction-round savings and general aesthetic improvement are not established. The latest stable release and installed local Skill remain v1.1.1.

For the current three focused follow-ups, use the [simple platform assignment and verified downloads](docs/focused-trials.zh-CN.md). The [older trial guide](docs/agent-testing-guide.zh-CN.md) remains available for the historical protocol. The optional `tools/prepare_agent_trials.py` splits the released agent bundle into one-package, one-task session ZIPs. Controlled comparisons, open audits, creative trials and independent review have separate prompts and evidence requirements.

In the earlier rc.1 local Windows comparison with v1.1.0, full render/review command medians increased by 15.0/16.7 ms (about 9%); the sample review JSON grew from 1,237 to 6,999 bytes. Pure rendering was essentially unchanged. These historical costs are separate from agent workflow outcomes.

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

This runs source unit tests, 43 image regressions, integrity checks for 86 historical fixture files and eight frozen study baselines, eight exact import/inspection tasks, executable editing/assembly controls, benchmarks, reproducible ZIP packaging, and artifact checks from an unrelated directory containing spaces and Chinese characters. Exact current counts are recorded in the [workflow report](docs/workflow-report.md). It needs no original mod checkout or Codex installation. Results are written to ignored `output/` and `evaluation/` directories.

When the official skill-creator validator is available, also run:

```sh
python -B tools/test_skill.py --python /path/to/python --validator /path/to/quick_validate.py
```

The default project-local validator checks metadata and references; it is not the official validator. GitHub Actions is configured for Python 3.14 on Windows and Ubuntu. Platform validation is established by completed runs, not by the workflow file alone.

`src/` holds the runtime, `skill-content/` holds maintained instructions and references, and `skill/` is the generated distribution. Make changes in the source directories, then run the checks to synchronize the skill. `tools/package_skill.py` copies these sources and records every packaged file. `quality/` preserves study briefs, frozen baselines, alternatives and self-review records. `baselines/` contains curated historical fixtures; see [provenance](docs/PROVENANCE.md). The complete original-project preservation archive remains outside this repository.

## License

[MIT](LICENSE), including the standalone skill. The repository-only demo bundles unmodified Silkscreen Regular under its separate [SIL OFL 1.1](demos/pixel-ui/fonts/OFL.txt); it is not in the Skill ZIP. Pillow and the development-only PyYAML are installed dependencies and are not vendored.
