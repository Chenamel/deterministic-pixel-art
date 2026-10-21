# v1.2.0-rc.1: capability evidence and external trial protocol

[简体中文说明](#中文说明)

The external audits identified real failures and a useful text-only workflow gap.
The reliability fixes shipped separately in v1.1.1. This candidate adds objective
inspection, exact PNG import and content-bound layout reuse. It does not generate
an aesthetic score or automatically redesign artwork.

## Measured capabilities

The [eight-task artifact results](measurements/feedback-capabilities.json) verify
exact RGBA import/render round trips, bounded editable grids and identical shared
analysis in review and inspect. This is scripted execution, not an external agent
experiment. Source tests cover empty/opaque/partial-alpha input, hidden RGB,
coordinate scopes, component neighborhoods, caps, legacy/stale/conflicting layouts,
more than 62 colors, 16-bit and animated PNG rejection, and overwrite protection.
The 43 stable migration outputs remain unchanged.

Text facts now distinguish the earlier 32×32 ship revisions whose old review JSON
was identical. Bbox, colors and components explain pixel structure; none determines
whether an exhaust, direction or material is aesthetically convincing.

## Interfaces and costs

- `inspect` / `inspect_image` produce bounded geometry, palette, alpha, symmetry,
  component and cell facts. Exact grids require <=64×64 and <=62 colors.
- `import` / `image_to_spec` preserve decoded 8-bit RGBA without quantization.
  Larger palettes use row-run rects. Output is capped at 4 MiB; this can be much
  larger and less semantic than the original hand-authored spec.
- `review` adds shared analysis without changing its tuple return or legacy bbox.
  New analysis rectangles use xywh; legacy review comparison keeps ltrb.
- Layout sidecars retain old fields and add version/digest. Optional PNG embedding
  changes file bytes; without the flag it retains the prior encoding behavior.
- Analysis adds CPU work and JSON. Use a region or named cell for focused work.
  No correction-round, token-saving or cold-start speed claim is established.

The [paired local timing record](measurements/feedback-performance.json) compares
v1.1.0 with this candidate using Python 3.14.2 / Pillow 12.3.0 on one Windows host.
After two warmups, 12 alternating process pairs gave these medians:

| Operation | v1.1.0 | Candidate | Observed change |
|---|---:|---:|---:|
| Pure ship render (200 samples) | 0.0771 ms | 0.0765 ms | effectively unchanged |
| Full render command | 165.0 ms | 180.0 ms | +15.0 ms / +9.1% |
| Full review command | 177.8 ms | 194.4 ms | +16.7 ms / +9.4% |
| Review JSON | 1,237 bytes | 6,999 bytes | 5.66 times the original size |

Default rendered PNG bytes were identical in this case. These are process and
artifact costs, not measured agent productivity. The additional JSON is a real
context cost; focused `inspect --region` or `--cell` avoids reporting unrelated
cells. No token counts were collected, so byte growth is not a token measurement.

## Paired external trials

The release provides an agent bundle and a separate evaluator bundle. Do not give
the grading fixtures or version key to agents. Each bundle contains fixed inputs
and SHA-256 checksums; runtime A/B labels are nominal masking because a determined
agent could inspect version metadata. No runtime source is patched to hide it.

Use at least one text-only and one multimodal environment. Within each environment,
run every task with both packages in fresh conversations, keeping the exact model,
permissions, Python/Pillow and prompt unchanged. Alternate A/B order by task and
reverse order in the second environment. Each task allows at most two candidates
and two targeted revisions. Standard Pillow scripting is allowed in both arms;
record those commands too. Treat offline/native failures separately from runs
using a compatibility shim, and never silently patch the runtime.

Eight controlled repair tasks cover two icon sets, ship/material sprites, UI
states/panel and Minecraft states/panel. They preserve existing art and localize
changes. The original creation briefs are also supplied as optional visual trials;
repair-task success is not proof of improved open-ended drawing aesthetics.

Use the supplied runner to record command outputs and elapsed times. Preserve the
spec, final PNG, initial localization, command logs, environment and raw conversation.
Record unknown token usage as null. Logs are inspectable evidence, not tamper-proof
telemetry; retain provider-generated transcripts where available.

## Stable-release gate

All engineering checks must pass. Eight paired tasks must be complete in both
representative environment types, with no candidate contract violations or
critical direction/state/content regression. At least six task IDs must show a
documented improvement in localization success or revision count, with no opposing
regression in the other environment. Command count and timing are secondary facts,
not substitutes for that gate. A human or independent visual agent records checks
of semantic/visual regressions; the evaluator does not infer those from pixels.

Results stay categorized as improved/unchanged/regressed. Provider scores and
the old 25-item coverage percentages are not averaged. Until paired evidence is
supplied and passes the evaluator, `workflow_gain_proven=false`, this stays a
prerelease and local Codex uses stable v1.1.1. No independent visual or in-game
acceptance is claimed.

The [current external gate result](measurements/feedback-external-gate.json) has
zero external runs and correctly fails. Fifteen isolated bundle smoke checks
verify checksums, answer separation, both runtimes, recording and this rejection;
their temporary logs are deleted and never submitted as model trials.

To rebuild and check the evaluation bundles from a full checkout after
`tools/check.py`, run `python -B tools/build_agent_eval.py` followed by
`python -B tools/test_agent_bundle.py`. Generated ZIPs are in
`evaluation/agent-eval/`; the fixed v1.1.0 baseline commit must exist locally.

## 中文说明

本候选版已经具备图片文本分析、静态 8 位 PNG 无损导入和布局复用能力。
八项自动场景验证的是像素往返与接口行为，不能替代外部 Agent 前后测评。
新版文本报告能显示旧报告无法区分的形体变化，但不会判断美丑或自动修改素材。

同机配对实测中，纯渲染基本持平，完整 render/review 命令的中位耗时分别增加
15.0/16.7 ms（约 9%），该样例的审阅 JSON 从 1,237 增至 6,999 字节。
更丰富的分析带来运行与上下文成本；区域/单元分析适合小改。这不是实际 token
或 Agent 创作耗时的测量，也不抵消尚未证明的工作流收益。

测评包分成 Agent 使用包与单独的验收包；后者的答案图和版本键不交给被测模型。
每个纯文本/多模态代表环境都用相同模型、依赖、提示词和预算完成 A/B 两组，
保留命令输出、规格、PNG、定位记录、修改次数及原始会话。两组均允许自行写 Pillow
分析代码，并把额外步骤计入记录。环境原生失败与加兼容垫片后的结果分开统计。

八项受控修改任务通过后，还需至少六项在定位成功率或修改轮次上有具体收益，
另一环境无反向退步，同时由人工或独立视觉代理复检方向、状态和关键内容，才能发布稳定版。
这些证据尚未产生，因此目前只发布候选版，本地正式 Skill 保持 v1.1.1。
