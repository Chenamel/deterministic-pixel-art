# Paired agent trials / Agent 配对测评

Use a fresh conversation for each task/package. Supply only the selected runtime,
task input directory and this protocol. Do not supply the evaluator bundle,
expected images, version mapping or earlier audit conclusions. Runtime labels
are nominal masking; version metadata remains intact.

Run all eight tasks with both A and B in a text-only environment and a multimodal
environment. Keep the exact model, access permissions and Python/Pillow the same
within each environment. Alternate A/B order by task; reverse it in the second
environment. Use a new output directory per run. Both packages may use ordinary
Pillow scripts, and those commands must be logged too. At most two candidates and
two targeted correction rounds are allowed; do not manufacture a revision to use
the budget. Do not install an input package globally or change its runtime.

1. Start timing immediately after receiving the task:
   `python runner.py start --out RUN --task TASK --package A --package-zip packages/A.zip --environment ENV --mode text_only --model EXACT_MODEL_ID`.
   Use `multimodal` only when the model can actually inspect images. Add `--shim`
   only if a compatibility patch is really necessary; describe it in the transcript.
2. Read the task request. Inspect the provided input, then save your initial
   localization to `RUN/localization.json` as `{"regions":[[x,y,w,h]],"reason":"..."}`.
   Coordinates are global image pixels. Save localization before editing; retain
   it unchanged. Do not guess provider token usage.
3. Execute commands through `python runner.py run --out RUN -- EXECUTABLE ARG...`.
   The child working directory is RUN, so use absolute input/runtime paths.
   Keep helper scripts and all intermediate candidates in RUN. Preserve the raw
   agent conversation separately, including file edits and image inspection.
4. Produce `RUN/final.json` and `RUN/final.png`. Keep a short `notes.md` explaining
   any uncertainty, visual tradeoff, direction/state meaning and content overlap.
   This is a surgical edit: preserve pixels outside the requested change.
5. End with `python runner.py finish --out RUN --candidates N --revisions R`.
   Add `--tokens COUNT` only for measured provider usage. For failures use
   `--failure-stage environment|localization|repair`; retain errors and partial files.

The recorder measures wall time and command latency, not internal model reasoning
or provider token counts. It is inspectable evidence, not tamper-proof telemetry.
Do not combine unrelated agent/environment timings into an average speedup.

## 中文提示

每项任务、每个版本单独开新会话，输入与权限保持一致。先保存初次定位，再修改；
最多两个候选、两轮修正，不要求用满预算。所有 Python/Pillow 辅助分析也要记入命令。
不要给模型验收包或版本键；无法看图的模型不标为多模态。未知 token 填空值，
失败保留原始输出，原生环境失败与兼容垫片后的结果分开记录。

把两个环境各 A/B 八项的 RUN 目录和原始会话交给验收者。验收者运行独立评估脚本，
核对像素契约、初次定位、修改轮次和图像语义。八项原始创作需求另附为可选视觉试验；
局部修复成功不等于通用审美提高。
