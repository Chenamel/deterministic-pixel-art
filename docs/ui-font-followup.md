# rc.6: actual-font and state-label workflow

2026-10-28, starting at `e726942`. The published and installed stable Skill remains v1.1.1.

The optional `recipes/label_atlas.py` reads an atlas, content-bound layout, Context text reservations and a caller-supplied font. It writes native/3x consumer composites and measured placement data. Rasterization is explicitly monochrome or grayscale. Each label shares one cell-local origin across states, with declared state offsets, while retaining padding in every state. An impossible fit is rejected; the atlas stays text-free.

This reuses font-measurement/composition logic that two external UI agents independently wrote. External command-count or correction-round savings have not yet been measured. The helper requires one text reservation per named cell and a content-bound layout; existing core handling of legacy metadata is unchanged.

Bounded grid errors now report the selected dimensions and global origin. An88×18 cell directs the caller to a smaller full-image region or summary facts. The64×64/62-color limits remain. Examples clarify short-label capacity, half-open rectangle bounds and supplying Context together with metadata.

Local Windows/Python3.14.2/Pillow12.3.0 validation passed117 source tests,97 extracted-ZIP cases and the official Skill validator. All43 stable migration outputs and default recipe pixels remain compatible. Tests cover font fit, explicit raster modes, shared placement, stale layout, missing font, invalid reservations, no-overwrite and input aliases. Removing pressed text motion while rebuilding matching image/report data fails exactly the three pressed-offset checks. Historical LT02 semantics and sealed packages remain intact.

![Native consumer](ui-font-followup/consumer.png)

[3x view](ui-font-followup/consumer-3x.png). Author inspection found complete labels and retained state marks; pressed text and icon both move down1px. The placement satisfies the existing10px reservation and2px padding; it is not proof of optimal optical alignment for other fonts or consumers.

The candidate is98 files/236,584 bytes,5,023 bytes larger than rc.5 (+2.169%). Dependencies remain Python/Pillow; JSON v1, public APIs and core drawing defaults are unchanged. The29 historical distribution files,44 installed stable files and8 user submissions retain their hashes. The generated repository Skill is intentionally rebuilt separately.

Next: one fresh WorkBuddy/DeepSeek UI task, then an image-only Gemini review and a Qwen Linux task. No new external run, independent aesthetic gain, game integration, token saving or stable-release acceptance is claimed. Cross-platform CI results are recorded separately. See [measurements](measurements/ui-font-followup.json) and the [Chinese report](ui-font-followup.zh-CN.md).
