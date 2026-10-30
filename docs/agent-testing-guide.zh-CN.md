# 外部 AI 测评：怎样分发、运行和提交

2026-10-25：当前先按 [长期额度分配与首轮两包](long-term-testing.zh-CN.md) 执行rc.5上手任务。本文下面保留历史rc.1固定A/B协议；不要拿旧包当作当前候选。新的长期A/B需在小试反馈后重新冻结对照，尚未分发；单版覆盖不计入配对门槛。

需要统一提示词，但不建议把“八项配对、全面找 bug、创作和审美验收”塞进同一长会话。
它们回答的问题不同。很多 AI 有助于发现不同环境与使用习惯下的问题；只有同模型、
同环境、同需求的配对，才能支持版本收益判断。重复赞美或无产物的打分不增加证明力。

## 先选测评路线

| 路线 | 交给谁 | 要回答的问题 | 发什么 |
|---|---|---|---|
| 固定 A/B 局部修复 | 能执行 Python 的 Agent；至少一个纯文本环境、一个能看图的环境 | 定位/修复是否更成功、步骤或修改轮次是否减少 | 每会话一个分发 ZIP，使用 PROMPT.md |
| 开放审计 | 不同平台/模型的使用者，可分配可靠性、编辑、UI 等不同重点 | 有哪些实际不足、兼容问题、使用成本和改进机会 | 单个 Skill 包 + [开放审计提示词](../benchmarks/prompts/open-audit.zh-CN.md) + findings 模板 |
| 独立创作 | 能执行的模型；审美由能看图者复检 | 新作品的方向、轮廓、材质、状态与布局是否更好 | 单个 Skill 包 + [创作提示词](../benchmarks/prompts/creative-task.zh-CN.md) |
| 独立验收 | 未参与该作品生成的看图 Agent 或人工 | 原始提交是否支持结论，有无关键退步 | 验收包 + RUN/原始会话 + [验收提示词](../benchmarks/prompts/independent-review.zh-CN.md) |

没有代码执行能力的聊天模型可提静态/视觉意见，不能标为命令实测。模型自称多模态
不够：必须实际能查看本次图片；仅用 Pillow 读像素属于纯文本分析。

## 当前包里有什么

从 [v1.2.0-rc.1 Release](https://github.com/Chenamel/deterministic-pixel-art/releases/tag/v1.2.0-rc.1)
下载 agent-evaluation、agent-evaluator 和 SHA256SUMS。

- `agent-evaluation-*.zip`：`packages/A.zip`、`B.zip`、`runner.py`、八个 `tasks/` 和协议。
- 每个任务有 `request.md`、`input.png`、`context.json`、`layout.json`；只有需要时才有 reference.png。
- `agent-evaluator-*.zip`：验收答案、版本映射、评估器与视觉复检模板。协调者保留，
  不交给正在执行固定任务的模型。公开仓库只能做到名义遮蔽，无法承诺严格盲测。
- 本次 A/B 固定对比 v1.1.0 与 v1.2.0-rc.1，**不是**把当前正式 v1.1.1 自动作为旧版。
  不换掉某一包，也不从 main 在线安装替代附件。

八项是局部修复任务。不要看到方向图标或飞船就重新设计整张图片；目标是修复 request
指定的问题，并保留其余像素。创作任务另开研究，不把它交给这个精确像素验收器。

## 最省操作的分发方法

协调者在仓库中运行下面的脚本。它只拆包、生成提示词和分发顺序，不执行 AI，也不生成测评结果。
不需要 Pillow。先按 Release 的 SHA256SUMS 校验原始 Agent 包；也可把其中 digest
作为 `--expected-sha256` 传给脚本。

```text
python tools/prepare_agent_trials.py --bundle PATH/agent-evaluation-v1.2.0-rc.1.zip --out PATH/text-env1-sessions --environment text-env1 --model "平台可见的实际模型名称" --mode text_only --order forward
python tools/prepare_agent_trials.py --bundle PATH/agent-evaluation-v1.2.0-rc.1.zip --out PATH/visual-env1-sessions --environment visual-env1 --model "平台可见的实际模型名称" --mode multimodal --order reverse
```

路径有空格时加双引号。模型精确版本未知可写平台可见名称，并在报告注明未知。
每个环境生成 16 个 ZIP（八个任务 × A/B）、schedule.csv 与协调记录。每 ZIP 只有
一个包、一个任务、runner、已填写配置的 PROMPT.md 和哈希清单，没有另一包或验收答案。
第二环境使用相反交错顺序，但每环境内的模型、解释器、Pillow、权限和提示词保持一致。

逐个分发，每个都开全新会话，发该 ZIP 并粘贴这句：

> 请解压附件，先读取 PROMPT.md，按其中配置实际完成本次任务。请提交 RUN 目录 ZIP
> 与原始可见会话；能力不足和失败如实保留，不以总结代替产物。

不要把 16 个 ZIP 一次性发给一个会话，也不要带入另一个版本的评价。不要向被测 AI
展示协调者的版本键、expected、其他 Agent 答案或本工具作者希望的收益。
同一环境的 A 和 B 必须由同一模型/配置完成，不是 A 给 DeepSeek、B 给另一个模型。

如果平台只能安装全局 Skill，必须能隔离实例或彻底移除另一版并开新会话，记录实际加载
路径与哈希。不能确认加载哪一版时可做开放反馈，不能算严格可比运行。推荐直接用附件
中的脚本，而不依赖平台全局 Skill 发现机制。

没有分发脚本时，也可以手工给每个新会话选一个 package 和一个 task，再填写
[固定任务提示词](../benchmarks/prompts/paired-task.zh-CN.md) 顶部五项配置。命令与保存规则相同。

## 建议先做小规模试运行

先选一个纯文本环境和一个多模态环境，用 directions-12、ship-32、ui-states 各做
A/B，确认上传、执行、归档和模型权限正常，再补齐剩余五项。开始就固定所有任务、顺序
和预算，失败也保存；不要试到哪个有利才留下哪个。试运行若更改了提示词/预算，旧结果
作为预试验保留，确认版从新会话重新做，不能混成同一轮证据。

最低完整固定测评是 **2 环境 × 8 任务 × 2 包 = 32 次新会话**。更多模型先做 1–2 项
开放审计，分工侧重兼容性、文本编辑、像素 UI/审美，避免所有模型重复一份清单。
小样本不适合综合排名，也不能从多模型数量直接宣称统计可靠。

## 收回什么

每会话收回 RUN 目录和原始可见会话。RUN 应含 final.json、final.png、localization.json、
notes.md、feedback.md、辅助脚本/中间候选、run.json、commands.jsonl、stdout/stderr。
不要只截图反馈，也不要只交最后一张 PNG。统一归档到：

```text
results/
  text-env1/
    directions-12/A/  # 此目录里放 RUN 的内容
    directions-12/B/
    ...
  visual-env1/
    ...
transcripts/          # 原始可见会话、文件编辑和图像查看记录
open-audits/          # 开放审计，不混入 results 的固定门槛输入
creative-trials/      # 创作产物，单列审美比较
```

环境标识与目录名可以相同，但自动脚本以 run.json 里的 environment 为准。一次 environment
中每个任务/包只能有一份主运行；重跑、不同种子或修过环境的运行保留到单独研究目录，
不要悄悄取代失败。如果反复运行，须为每次复本明确标识，配对时避免混合环境。

计时是实际记录的墙钟与子命令时间，不等于模型纯推理时间；图像查看、文件编辑等可能
只在会话中可见。token 没有平台实测就留 null，不按字符推算。旧 runner 在零候选失败时
不能 finish：保留未完成记录，明确是环境/流程失败，不能虚填候选数使其通过。

## 怎样做验收

把所有 results、会话与验收包交给未参与生成的看图者，使用独立验收提示词。先运行：

```text
python evaluate_agent_results.py --manifest manifest.json --runs ABSOLUTE_RESULTS --out automatic-result.json
```

填写视觉复检模板的实际环境名、最终 PNG 哈希、reviewer、具体观察及 critical_regression，
再用 `--visual-review visual-review.json --out final-result.json` 运行。
exit 1 表示未达到门槛，可能来自缺少结果/复检，并非都属于崩溃。不要修改原始 RUN，
更不能让被测模型自填独立验收。缺失和失败也交回，协调者可进一步复现。

现有自动脚本核对冻结产物、像素契约、规格复现和配对条件；它不能证明会话无作弊，
也不能自己理解方向/状态语义。最终还要核对会话与视觉记录。当前发布门槛还要求候选
无关键退步，且至少六项任务在定位成功率或修改轮次上有具体收益、另一环境无反向退步。
不满足就保留 RC，有用的缺陷反馈仍可以采纳，不需要强行凑出六项收益。

## 如何把反馈转成优化

使用 [findings-template.json](../benchmarks/prompts/findings-template.json)，每条有触发输入、
最小命令、期望/实际、证据区域、影响、最小建议与验证办法。未知事实保持 null。
按以下顺序核验和排期：

1. 可复现的数据损失、错误像素、误覆盖、任务阻断：优先修复，保留最小回归样例。
2. 反复出现的额外命令、手抄布局、难懂错误与环境问题：记录具体成本，再设计流程改进。
3. 有原尺寸/场景依据的视觉问题：另存候选，通过独立看图比较；不强制全局换风格。
4. 静态猜测、审美偏好和未支持的新功能：标明证据程度与适用场景，不自动当缺陷。

多个 Agent 报告同一根因应合并成一项，并保留各自环境与复现证据；数量不是多票表决。
相反意见保留，优先看产物、需求和复现，不按模型名气决定。修复后重跑原失败输入，
再看像素兼容和工作流代价；审美收益、工程正确性、效率分别报告。
