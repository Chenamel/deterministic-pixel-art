# 独立验收提示词（交给未参与生成的看图 Agent 或人工）

你负责复核实际产物。你没有参与这些任务的生成，不需要迎合作者或证明新版更好。附件包括独立验收包、各环境提交的 RUN 和原始可见会话。不要重新生成图像代替受测产物，也不要修补答案或修改运行记录。

1. 核对验收包和提交文件的 SHA-256。记录你实际可用的看图/执行能力与模型名称。只阅读文本而无法看图时，不能完成图像语义验收；相关项保持 null。没有代码环境时可做视觉意见，但自动门槛尚待执行。
2. 使用同一 Python/Pillow，在验收包中运行：

```text
python evaluate_agent_results.py --manifest manifest.json --runs ABSOLUTE_RUNS_ROOT --out automatic-result.json
```

第一次 exit 1 可能只是缺少配对或独立视觉记录，并不自动表示程序崩溃。保留真实输出。run 缺失、哈希不符、模型/环境不配对、shim、定位记录时机或候选/修正预算不清，分别列出；不要补造日志。
3. 参照 visual-review-template.json，把示例环境名替换成实际 run.json 的 environment。逐项查看 request、输入与最终 PNG，并核对任务约束；必要时查看参考单元、原尺寸、最近邻放大和目标背景。填写每个被验收候选的真实 final.png SHA-256、critical_regression 和具体 notes。填写真实 reviewer 和 type=human 或 independent_agent。
4. 图像语义至少检查：方向与符号意义、状态区别和布局、关键内容/文字预留区、轮廓与颜色、MC 边缘衔接、非目标像素误改。说明哪里“改善/持平/退步/无法判断”；小修补不应被强迫接受新的画风。不要把像素相等、某项对称或对比率直接当作审美通过。不能确认无关键退步时保留 null/明确 false gate，不能勉强填通过。
5. 生成视觉记录后再次运行：

```text
python evaluate_agent_results.py --manifest manifest.json --runs ABSOLUTE_RUNS_ROOT --visual-review visual-review.json --out final-result.json
```

自动脚本只是证据与既定门槛检查器；还要人工复核原始会话是否支持候选数/修正轮次和看图模式、是否选报成功样本、初次定位是否在修改前记录、环境失败是否正确分类。脚本并非防篡改遥测，不能确认的证据注明未验证。

提交 `automatic-result.json`、`visual-review.json`、`final-result.json`、`independent-review.md`，并保留原始命令输出。报告分别列出工程检查、配对可比性、工作流收益、图像语义和审美意见。评价主体不同、环境不同的分数不要平均排名；未知 token 与耗时保持未知。

当前稳定门槛要求：工程检查通过；纯文本与多模态代表环境各完成八项 A/B；候选无方向/状态/关键内容等实质退步；至少六项任务有定位成功率或修正轮次收益且另一环境无反向退步。真实结果不满足时明确“未达到”，同时保留有效发现。失败不应转写为“总体通过”。开放创作的审美意见另列，不能由这些局部修复任务推导普遍画质提升。
