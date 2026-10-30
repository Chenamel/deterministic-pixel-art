# Verification and limits

[中文](verification.zh-CN.md) · [README](../README.md)

## Engineering evidence

The prepared v1.2.0 contents passed 165 source tests, 106 isolated package scenarios, 43 stable-image comparisons, reproducible packaging and official Skill format validation. The corresponding preparation commit passed eight Windows/Ubuntu CI jobs, including Pillow 10.4, 11.3, 12.1 and 12.3. These counts describe the prepared contents, not automatic proof that every later commit passed.

See the [English release notes](releases/v1.2.0.md), [CI runs](https://github.com/Chenamel/deterministic-pixel-art/actions) and [detailed preparation record in Chinese](releases/v1.2.0-preparation.zh-CN.md). The package manifest records each file's SHA-256 so changes can be detected. PNG compatibility means decoded RGBA equality, not identical compression bytes. The fixed reproduction baseline is Python 3.14.2 / Pillow 12.3.0; supported versions may differ in polygon filling.

## External use

Collected external task evidence spans icons, sprites, material variants, generic UI, text placement in an application, environment recovery, Minecraft-style panels and 256px chunk composition. Different agents and environments completed different tasks; this is not a controlled model ranking or an old/new comparison.

The original LT04 submission had reversed horizontal directions and missing earlier revisions; the coordinator's repair is not the model's self-correction. LT08's final pixels and observed workflow were checked, but its claimed earliest revisions and failure were not fully preserved. These limits remain in the [LT04 record](lt04-results-20261029.zh-CN.md) and [LT08 record](lt08-results-20261030.zh-CN.md), both in Chinese.

## Visual results and application limits

Automated analysis provides geometry, palette, alpha, components and differences. It cannot establish object meaning, beauty or whether a control shows the correct state. Visual warnings are prompts to inspect, not universal art rules. Native-size and background checks remain necessary.

General aesthetic improvement, token savings and faster task completion have not been established. Minecraft game integration, arbitrary fonts, multi-agent chunk production and artwork drawn directly at 512×512 remain unverified or separate work. Actual-font/browser demos and offline seam checks cover only the conditions they exercise.

Historical measurements remain available: [initial optimization, Chinese](optimization-report.zh-CN.md), [authored visual study](quality-report.md), [workflow report](workflow-report.md), [usability costs](usability-20261029.md). Pure-render speedups exclude startup/disk I/O; historical full-command measurements did not show a speedup. More documentation or a shorter install command alone does not demonstrate broader adoption.
