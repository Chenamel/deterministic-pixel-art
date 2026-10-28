# Test document audiences

User-facing dispatch instructions: [test-handoff.zh-CN.md](../docs/test-handoff.zh-CN.md).

`long-term/LT01.md` and `LT02.md` are participant task sources. They describe inputs, actions and required outputs. `long-term/REVIEW.md` is a visual-review source for a separate package containing `TASK.md` and `images/`.

`tools/build_long_term_trials.py` packages only the selected participant task with the frozen Skill, inputs and recorder. Assignment recommendations and manifests are outside the ZIPs in `coordinator/`. Existing wave1/wave1b packages are preserved; changed instructions create different task hashes and do not replace earlier runs.

`prompts/` contains earlier evaluation templates, including coordinator placeholders and multi-task protocols. Do not forward these files directly. Prepare one concrete participant task or one reviewer brief, and keep dispatch/release notes with the coordinator. Historical published packages remain unchanged.
