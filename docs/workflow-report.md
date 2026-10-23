# Exact editing and larger pixel-art workflows

2026-10-23 · **v1.2.0-rc.2, local candidate** · [Detailed Chinese report](workflow-report.zh-CN.md)

Historical snapshot below. The frozen rc.2 has since been [published and passed eight CI jobs](focused-trials-report.zh-CN.md). [Readable recipes](recipe-workflows.md) are the next local rc.3 candidate; the original measurements below remain unchanged.

The candidate addresses observed agent friction: light-background silhouettes now remain visible, every background has a native-size card, previews accept a target background, and explicitly portable publication works without hard links. Named atlas import preserves layout and all decoded RGBA; `replace-cell` changes one member and `verify` checks exact allowed rectangles or masks. A separate `assemble` manifest places bounded PNG components with explicit copy/source-over, crop, overlap and coverage contracts.

The editable [workflow examples](../examples/workflows/) include a native 128×128 asymmetric courier, a 256×256 watermill scene and a transfer-icon edit. The edit changes 66 pixels and zero outside the selected cell. Component assembly and four-tile reassembly exactly match the whole-scene control; there are no coverage gaps, and four boundaries are displayed in eight inspected seam crops. The tile example is crop/reassembly, not independently painted agent chunks.

Windows 11, Python 3.14.2 and Pillow 12.3.0 checks passed:

- **76** source tests, **43** stable migration images and **8** exact import/inspection tasks.
- **61** commands from the extracted ZIP in an unrelated Chinese/space directory, including the official skill-creator validator; a separate project-validator run also passed.
- **85** packaged files verified, deterministic ZIP rebuilt twice.
- **10** external final PNGs rerendered with exact RGBA/layout; **138** protected original/input files retain their hashes. Historical fixtures and frozen authored-study baselines remain intact.

Compared with rc.1 on the same machine (9 samples), pure rendering is essentially unchanged. Full render/review command medians increase from 175.37/235.02 to 197.07/258.78 ms. The sample review JSON grows from 7,505 to 8,966 bytes; the ZIP grows from 113,055 to 213,762 bytes. More native-size views increase the sample sheet from 816×932 to 816×1232. These costs are not model productivity measurements.

Current results are authored visual self-review and deterministic engineering checks. They do not establish general aesthetic gains, token savings, fewer correction rounds, independent blind preference or in-game performance. The eight external exploratory tasks are useful feedback, not the previously specified controlled A/B release gate. This candidate has not yet run updated Ubuntu/Pillow-version CI or original OSS/FUSE-platform checks. Optional portable output preserves no-overwrite but makes NEW files visible while writing; no mode promises a crash-safe multi-file transaction.

The stable release and installed local Skill stay at **v1.1.1**. Next: focused Windows edits, original-mount publication and named-PNG/native128 retests, then independently painted 256px chunks with a shared composition, boundary coordinates and explicit interior ownership before scaling to 512px. See [the roadmap](roadmap-20261023.md) and root `WORK_STATE.md` for durable continuation notes.
