# rc.5 first-wave external results

2026-10-28. [中文](long-term-results-20261028.zh-CN.md) · [Measurements](measurements/long-term-results-20261028.json).

All three submissions passed independent engineering checks. LT01 also passed offline direction/boundary review; the two LT02 consumers need a follow-up on consistent pressed icon/text movement. This is a small, single-version usability sample, not a version-benefit experiment or model ranking.

| Run | Recorded commands | Nonzero exits | Independently checked result |
|---|---:|---:|---|
| GLM-5.3-Flash / LT01 | 11 | 0 | Named-cell edit; 70 RGBA pixels changed, zero outside transfer; layout retained |
| DeepSeek-V4.1-Flash / LT02 | 11 | 1 | Six 88×18 states and 18 actual-font instances; layout, padding and pixel reconstruction pass |
| MiniMax-M3.1-Flash / LT02 | 13 | 2 | Same deterministic recipe/parameters produce identical source and consumer PNGs; engineering checks pass |

The three failures were a participant helper path typo, a participant coordinate conversion bug, and a bounded-grid refusal on an already-selected 88×18 cell. All were retained and resolved or worked around. Submitted Python was not executed: the trusted, hash-matched recorder checked isolated copies; six spec/PNG pairs and three imported/cropped specs were independently reconstructed. Last-command file snapshots matched the returned files. MiniMax's raw session is inside its submission, so all three producer transcripts are available.

Gemini's Markdown review was supplied; its JSON and raw reviewer session were not. All 21 PNG file/RGBA hash rows matched the received artifacts. That corroborates artifact identity, not every claimed tool action. Producer logs contain image-opening calls and the named model IDs. Equal outputs are expected from the recipe, not evidence of copying or equal model ability.

The important findings are:

- The pressed icon moves down while labels stay fixed. Relative motion is possible within the frozen contract: an isolated example using non-pressed y=2 and pressed y=3 passes the existing checker. Moving only the submitted pressed baseline from y=3 to y=4 fails padding. Neither result establishes optimal optical alignment.
- Default font rasterization contains intermediate coverage values. A monochrome variant fails only the two consumer reconstruction checks because the benchmark fixes the default Pillow path. Future consumer support should declare grayscale/monochrome choice explicitly while preserving the old default. Nearest-neighbor scaling does not remove existing font smoothing.
- A submitted 40px crop truncates START. It cannot establish a defect in the complete label, nor disprove a subjective native-size observation. Full-label crops show intact glyphs.
- `inspect --grid` suggests selecting a cell even when the selected cell is already 88×18. Improve dimensions/region guidance; keep bounded text output. Ordinary inspection and 60×18 regional grids work.
- A short-label recipe example is valid but unsuitable for EXPORT MAP. Clarify capacities, half-open rectangle bounds, and using Context together with verified layout metadata.
- Both UI producers wrote their own font-measurement/consumer scripts. Prioritize one optional reusable helper over adding several commands, automatic layout, larger grids or automatic overwrite.

Disabled contrast, uniform-width whitespace, the small selection mark and arrow shoulders are context-dependent visual choices, not automatic failures of this task. A single-version issue cannot be labeled a version regression. Interaction, color-vision scenarios and Minecraft integration remain untested.

Raw producer logs expose response usage counters despite `session.json.tokens=null`. They include repeated/cached input, later export work and incomplete snapshots, so they are not complete task billing or a comparative efficiency metric. Individual usage and raw conversations remain local. Session duration and command duration are different measurements.

Next: make a narrow consumer/guidance improvement, validate locally, then run one focused external follow-up. Prepare Qwen's Linux/portable-output trial afterwards; no LT03 package has been distributed yet. Preserve all old inputs, submissions and labels. No runtime, sealed rc.5, stable installation or release was changed in this audit; no rc.6 was built.

The original two-environment/eight-task/two-version acceptance gate is unchanged. Main stages: P1/P2/P3/P4a complete, P4b native512 deferred. Current checkpoint: external audit complete; next: focused UI/guidance fixes. All eight original files and 170 protected files were hash-verified unchanged.
