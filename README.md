# Deterministic Pixel Art

[简体中文](README.zh-CN.md) · [MIT](LICENSE) · [Releases](https://github.com/Chenamel/deterministic-pixel-art/releases) · [AI install](INSTALL.md)

[![Release](https://img.shields.io/github/v/release/Chenamel/deterministic-pixel-art?style=flat-square&label=release)](https://github.com/Chenamel/deterministic-pixel-art/releases/latest)
[![Main branch checks](https://img.shields.io/github/actions/workflow/status/Chenamel/deterministic-pixel-art/test.yml?branch=main&style=flat-square&label=checks)](https://github.com/Chenamel/deterministic-pixel-art/actions/workflows/test.yml)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](INSTALL.md)
[![MIT license](https://img.shields.io/github/license/Chenamel/deterministic-pixel-art?style=flat-square)](LICENSE)

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/images/brand/header-en-dark.png">
  <source media="(prefers-color-scheme: light)" srcset="docs/images/brand/header-en-light.png">
  <img alt="Deterministic Pixel Art — editable pixels, exact changes" src="docs/images/brand/header-en-light.png" width="1152">
</picture>

**Create editable pixel art with AI agents, then verify exactly what changed.**

Make PNG icons, sprites, UI components and named sprite atlases from text grids, integer drawing commands or Python masks. Import existing PNGs without quantization, edit a selected region and assemble separately drawn components. Built for AI-assisted game assets and pixel UI; Minecraft styling is optional.

![Original travel kit: six 32px items with glass, paper, leather and metal materials, composed into an inventory panel](demos/travel-kit/assets/overview.png)

[Editable travel kit](demos/travel-kit/README.md) · [Native UI PNG](demos/travel-kit/assets/ui.png) · [Named item atlas](demos/travel-kit/assets/after.json). Original 32×32 items and a 192×160 static UI composition, with native-size views and integer nearest-neighbor enlargements. JSON sources and the drawing script are included.

**Version: v1.3.0.** [Download the stable Skill](https://github.com/Chenamel/deterministic-pixel-art/releases/tag/v1.3.0) · [What changed](docs/releases/v1.3.0.md). Includes scoped color replacement, paged atlas review, named-tile scene previews and PNG animation export. Exact editing requires static PNGs with channel depth at most 8 bits; editable sources and original PNGs remain the basis for later changes.

## Use with an AI agent

Give an agent with terminal and file access this request:

> Read <https://github.com/Chenamel/deterministic-pixel-art/blob/main/INSTALL.md> and install deterministic-pixel-art from the latest stable release. Check that it supports my intended task, then generate a sample PNG to verify installation.

[AI installation guide](INSTALL.md): select the environment, install the self-contained Skill and run a small render. It also includes an optional `npx skills` shortcut for supported agents. Agents without native Skill support can run the same tools from a task-local folder.

Once installed, try: “Create six 32×32 travel items with a consistent palette and lighting, compose them into a small inventory panel, and keep the editable sources.”

DSH users can start with [installation and quick start](integrations/dsh/README.md):
check compatible versions, install into the profile used for chat, then request an
asset or edit in natural language. This optional third-party bundle carries the same
Skill; npm installation does not require a marketplace listing.

## Use the Python CLI

Requires Python 3.10+ and Pillow >=10.4,<13. The requirements file pins Pillow 12.3.0 for reproducibility.

```sh
git clone https://github.com/Chenamel/deterministic-pixel-art.git
cd deterministic-pixel-art
python -m venv .venv
```

Activate with `.\.venv\Scripts\Activate.ps1` in PowerShell, or `source .venv/bin/activate` on macOS/Linux, then:

```sh
python -m pip install -r requirements.txt
python src/pixel_art.py render --spec examples/gem-16.json --out output/gem.png --preview output/gem-preview.png
```

Expected output: a **16×16 PNG** and a **128×128 nearest-neighbor preview** in `output/`. Without Git, download and extract the checkout ZIP, then open a terminal in its top-level folder. Keep the editable spec with the PNG; existing outputs require explicit `--force` to overwrite.

## Choose a workflow

| Task | Start here |
|---|---|
| Item set / UI composition | [Six travel items, a static inventory panel and a named-item edit](demos/travel-kit/README.md) |
| Small grid sprite | [Transparent grid](examples/transparent-grid.json), [mirrored gem](examples/gem-16.json) |
| Asymmetric sprite | [32×32 ship](examples/asymmetric-ship-32.json), [pixel-art guidance](skill/deterministic-pixel-art/references/pixel-art.md) |
| UI or button states | [Generic panel](examples/generic-panel-96x40.json), [UI guidance](skill/deterministic-pixel-art/references/ui.md), [recipes](skill/deterministic-pixel-art/references/recipes.md) |
| Existing PNG / named atlas edit | [Import, replace-cell and verify](docs/usage.md#edit-a-named-atlas-cell) |
| Image facts or review | [Text inspection](skill/deterministic-pixel-art/references/text-workflow.md), [review context](skill/deterministic-pixel-art/references/review.md) |
| Separate chunks | [Chunk contracts](skill/deterministic-pixel-art/references/chunking.md), [four-source scene](demos/chunk-scene/README.md) |
| Minecraft-style UI | [Optional guidance](skill/deterministic-pixel-art/references/minecraft.md) |

[More command examples](docs/usage.md) cover scoped edits, recipes and environment recovery. The [JSON v1 and Python API](skill/deterministic-pixel-art/references/formats.md) are available for custom generators. The [browser UI demo](demos/pixel-ui/README.md) includes actual-font and interaction checks.

![Travel kit before and after replacing only the lantern glass, with the exact changed-pixel mask](demos/travel-kit/assets/scoped-edit.png)

This example changes **106 RGBA pixels inside the lantern cell, zero outside**. Its shape, brass frame, atlas position and the other five items stay the same. [Run this named-item replacement and verification](demos/travel-kit/README.md#replace-one-named-item), or start with the [tiny grid recolor](docs/usage.md#change-one-grid-color).

## Evidence and limits

- **Reproducible assets:** 43 reference images retain the same decoded pixels. Lossless import and scoped edits compare decoded RGBA, including hidden RGB under zero alpha.
- **Tested workflows:** source/package checks and Windows/Ubuntu CI cover rendering, inspection, import, editing and assembly. External agents have exercised eight task categories; original failures and incomplete records remain documented.
- **Art direction stays contextual:** inspect native-size assets on their intended backgrounds. Automated checks do not establish recognizability, general aesthetic gains, token savings or Minecraft game integration.

[Verification details and remaining limits](docs/verification.md) distinguish engineering checks, external use and visual judgment.

## Help and contribute

[Open an issue](https://github.com/Chenamel/deterministic-pixel-art/issues) for a bug, installation problem or a useful missing workflow. Include the command, error, Python/Pillow versions and a small input when possible. [Contribution guide](CONTRIBUTING.md).

## Development

```sh
python -m pip install -r requirements-dev.txt
python -B tools/check.py
```

Maintain runtime code in `src/`, recipes in `recipes/`, and guidance in `skill-content/`. `tools/package_skill.py` generates the standalone Skill under `skill/`. Full checks create local artifacts without globally installing a Skill. [Fixture provenance](docs/PROVENANCE.md).

For source browsing and edits, see the [source-to-Skill path map](CONTRIBUTING.md#source-and-generated-skill) and the [limited Python format gate](CONTRIBUTING.md#python-formatting).

## License

[MIT](LICENSE) covers the code, original artwork and standalone Skill. Repository visuals use Silkscreen Regular under [SIL OFL 1.1](demos/pixel-ui/fonts/OFL.txt) and Fusion Pixel Font under [SIL OFL 1.1](assets/brand/font-notices/README.md). Fonts are not included in the Skill ZIP. Pillow and development-only PyYAML/Ruff are installed dependencies, not vendored files.
