# Deterministic Pixel Art

[简体中文](README.zh-CN.md) · [MIT](LICENSE) · [Releases](https://github.com/Chenamel/deterministic-pixel-art/releases)

An AI-oriented tool and Skill for editable pixel-art PNGs: icons, sprites, UI components, named atlases and component scenes. Create from grids, integer drawing commands or Python masks; import PNGs without quantization, make scoped edits and check exactly which pixels changed. Minecraft styling is optional.

![Original native-128 sprite, enlarged with nearest-neighbor scaling](docs/workflows/sprite-128-preview.png)

**Version status:** the latest stable release is **v1.1.1**. This development branch contains changes after frozen **v1.2.0-rc.6**, not a new numbered release. The commands below require this checkout or its matching generated Skill; older packages have their own pinned capabilities.

## Quick start

Use Python 3.10+ and Pillow >=10.4,<13. The reproducibility baseline is Python 3.14.2 / Pillow 12.3.0; `requirements.txt` pins that Pillow version.

```sh
python -m venv .venv
```

Activate with `.\.venv\Scripts\Activate.ps1` in PowerShell, or `source .venv/bin/activate` in a POSIX shell, then:

```sh
python -m pip install -r requirements.txt
python src/pixel_art.py render --spec examples/gem-16.json --out output/gem.png --preview output/gem-preview.png
python src/pixel_art.py inspect --image output/gem.png --grid
python src/pixel_art.py review --image output/gem.png --out-dir output/gem-review
```

Keep the spec with the PNG. Check native size and an integer enlargement on the intended background. Existing files require explicit `--force` to overwrite; use absolute paths when running from another directory.

## Choose a workflow

| Task | Start here |
|---|---|
| Grid sprite | [Transparent grid](examples/transparent-grid.json), [mirrored gem](examples/gem-16.json) |
| Asymmetric sprite | [32×32 ship](examples/asymmetric-ship-32.json), [pixel-art guidance](skill/deterministic-pixel-art/references/pixel-art.md) |
| UI or button states | [Generic panel](examples/generic-panel-96x40.json), [UI guidance](skill/deterministic-pixel-art/references/ui.md), [recipes](skill/deterministic-pixel-art/references/recipes.md) |
| Existing PNG / named atlas edit | [Import, replace-cell and verify](skill/deterministic-pixel-art/references/workflows.md) |
| Image facts or review | [Text inspection](skill/deterministic-pixel-art/references/text-workflow.md), [review context](skill/deterministic-pixel-art/references/review.md) |
| Separate chunks | [Chunk contracts](skill/deterministic-pixel-art/references/chunking.md), [four-source 256×256 demo](demos/chunk-scene/README.md) |
| Minecraft-style UI | [Optional guidance](skill/deterministic-pixel-art/references/minecraft.md) |

Import an existing named cell:

```sh
python src/pixel_art.py import --image examples/workflows/atlas-before.png --metadata examples/workflows/atlas-before-layout.json --cell transfer --out output/transfer.json
```

Edit `transfer.json`, then use it as `--replacement`:

```sh
python src/pixel_art.py replace-cell --spec examples/workflows/atlas-editable.json --cell transfer --replacement output/transfer.json --out output/candidate.json --image-out output/candidate.png --metadata output/candidate-layout.json
python src/pixel_art.py verify --image output/candidate.png --compare examples/workflows/atlas-before.png --allow-region 32 0 16 16
```

Full-image `import` is also available. Decoded 8-bit RGBA, including hidden RGB, is preserved. [JSON v1 and Python API](skill/deterministic-pixel-art/references/formats.md).

For repeated variants, start with a short recipe:

```sh
python recipes/icons.py --out-dir output/icons --ink F5C26B
python recipes/buttons.py --out-dir output/buttons --width 96 --content 23 4 70 10
python recipes/chunk_pair.py --out-dir output/bridge
```

Recipes export editable specs and PNGs. The optional [actual-font helper](skill/deterministic-pixel-art/references/consumer-ui.md) checks text placement; the [browser demo](demos/pixel-ui/README.md) tests controls and scaling separately. Neither establishes Minecraft game integration or arbitrary font support.

On a filesystem that rejects hard links, choose `--portable-output`. In this development version, set it once per task shell: `$env:PIXELART_PORTABLE_OUTPUT = '1'` in PowerShell or `export PIXELART_PORTABLE_OUTPUT=1` in POSIX shells. CLI and recipes inherit it; `--no-portable-output` overrides one command. No-overwrite still applies; new portable files can be visible while writing. [Environment recovery](skill/deterministic-pixel-art/references/workflows.md).

## Install as a Skill

Download a versioned ZIP and SHA-256 manifest from [Releases](https://github.com/Chenamel/deterministic-pixel-art/releases), verify the checksum, then extract its `deterministic-pixel-art` folder into `$CODEX_HOME/skills` (default `~/.codex/skills`). Install that folder's `requirements.txt` into the Python environment used by the task. Keep old backups outside the skills discovery directory.

The checkout's [generated Skill](skill/deterministic-pixel-art/SKILL.md) is self-contained; its renderer and recipes are under `scripts/`. Example request: “Use `$deterministic-pixel-art` to create four 16×16 directional icons in a named atlas, keep a transparent one-pixel margin, and check each direction at native size.”

## Evidence and limits

- **Compatibility:** 43 stable v1.0.0 migration outputs remain pixel-compatible. Import and scoped-edit checks compare decoded RGBA, not PNG compression bytes.
- **External use:** eight task categories supplied evidence across icons, sprites, materials, UI, environment recovery and chunks. LT04's original direction failure and LT08's incomplete early history remain recorded; collected categories do not mean complete passes.
- **Current consolidation:** source, generated Skill and the 98-file development ZIP match. Fresh checks and the repository-only link-checker fix are in the [consolidation report](docs/candidate-consolidation-20261030.zh-CN.md).
- **Unproven benefits:** single-version sessions do not establish general art-quality, token or workflow-time gains. Controlled old/new comparisons and Minecraft integration remain separate. [Current release gates](docs/release-readiness.zh-CN.md).

Historical results are separate reports: [initial optimization](docs/optimization-report.zh-CN.md), [authored visual study](docs/quality-report.md), [workflow report](docs/workflow-report.md), [usability costs](docs/usability-20261029.md). Pure-rendering speedups exclude startup and disk I/O; historical full-command measurements did not show a speedup. No automatic aesthetic scoring is provided.

## Development

```sh
python -m pip install -r requirements-dev.txt
python -B tools/check.py
```

Checks cover source tests, stable images, preserved fixtures, import/edit/assembly workflows, reproducible packaging and execution from an unrelated Chinese/space path. They generate local artifacts and do not install a Skill globally. After packaging, optionally run `tools/test_skill.py --python /path/to/python --validator /path/to/quick_validate.py` for official Skill validation.

Maintain runtime code in `src/`, recipes in `recipes/`, and guidance in `skill-content/`. `tools/package_skill.py` generates `skill/` and the local ZIP. Completed CI runs establish platform results; the Windows/Ubuntu workflow configuration alone does not. [Fixture provenance](docs/PROVENANCE.md).

## License

[MIT](LICENSE) covers the code, original artwork and standalone Skill. The repository-only demo includes unmodified Silkscreen Regular under [SIL OFL 1.1](demos/pixel-ui/fonts/OFL.txt); the font is not in the Skill ZIP. Pillow and development-only PyYAML are installed dependencies, not vendored files.
