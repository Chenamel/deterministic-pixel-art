# 三项定向复测：发给谁、发什么

**2026-10-25结果更新：三份外部提交已全部收到并完成工程核验。** 53条命令、13组规格/PNG、三张编辑最终图及区外RGBA均已独立检查；千问原生EPERM有记录，/tmp成功仍仅自述。[完整结果、反馈取舍与rc.5改进](p1-results.zh-CN.md)。无需再次安排这三个会话；下面保留原分工和冻结下载供复现。

原分发安排为三个新会话，每个平台一个任务。每个 ZIP 都包含冻结的 **v1.2.0-rc.2 Skill**、固定输入、短提示词和记录器；无需另外安装旧测评包。

2026-10-24重新核验：下面三个公开直链均实际下载成功（HTTP200），字节数和SHA-256与本地最终包完全一致。本地最终目录是 `dist/focused-v1.2.0-rc.2-final/`，不要使用没有 `-final` 的中间构建。虽然当前开发候选已到rc.4，这三项定向复测仍使用包内冻结rc.2，不额外升级Skill，以免改变固定输入/工具基线。无需重做先前八项探索任务。

| 交给谁 | 下载包 | 任务 |
|---|---|---|
| **WorkBuddy / DeepSeek** | [P1-W-DeepSeek.zip](https://github.com/Chenamel/deterministic-pixel-art/releases/download/v1.2.0-rc.2/P1-W-DeepSeek.zip) | 改一个命名图标，再改空心边框；验证其他RGBA不变 |
| **千问办公助理** | [P1-C-Qwen.zip](https://github.com/Chenamel/deterministic-pixel-art/releases/download/v1.2.0-rc.2/P1-C-Qwen.zip) | 原生与便携输出、拒绝覆盖、依赖和挂载记录 |
| **Gemini任务模式** | [P1-V-Gemini.zip](https://github.com/Chenamel/deterministic-pixel-art/releases/download/v1.2.0-rc.2/P1-V-Gemini.zip) | 只改metal单元并实际看图，检查浅背景及剪影 |

发布状态：**v1.2.0-rc.2预发布已上线；8组CI全部通过；9份发布附件与本地一致（8份内容哈希加校验清单），千问直链还完成了无登录实际下载校验。** [发布页](https://github.com/Chenamel/deterministic-pixel-art/releases/tag/v1.2.0-rc.2) · [校验记录](measurements/focused-release.json)。三份外部结果已收回，详见页首；新开发候选rc.5不覆盖这些任务包。

## 直接复制的启动语

DeepSeek、Gemini：上传对应ZIP，复制：

> 解压此任务包，阅读根目录的 START_HERE.md，使用包内 Skill 实际完成任务。按 run.py 记录命令，不修改原始输入，保留失败。最后提供 submission-P1-*.zip 和可导出的原始会话。请给具体困难和改进建议，不需要全面评分或模型排名。

千问：无需上传ZIP，复制：

> 请下载 https://github.com/Chenamel/deterministic-pixel-art/releases/download/v1.2.0-rc.2/P1-C-Qwen.zip 并解压，阅读 P1-C/START_HERE.md，使用包内 Skill 实际执行任务。按 run.py 记录命令和失败，区分原生与便携输出，不自动添加 --force。最后提供 submission-P1-C.zip 和可导出的原始会话。无法下载时给出实际错误，不假装已执行。

每包中的 `START_HERE.md` 是对应冻结任务的完整提示词。仓库中的 [P1-W](../benchmarks/focused/P1-W.md)、[P1-C](../benchmarks/focused/P1-C.md)、[P1-V](../benchmarks/focused/P1-V.md)现已根据反馈补充未来任务的方向与记录说明；复现本轮时使用冻结ZIP内文本，不以新措辞重新判定旧提交。

## GitHub上查看P3/P4的位置

P3/P4已推送至 [`codex/visual-quality`开发分支](https://github.com/Chenamel/deterministic-pixel-art/tree/codex/visual-quality)，尚未合并到默认 `main`，也没有将rc.4作为新Release发布。默认仓库页面或Releases的较早日期不能用来判断开发分支是否已提交；在分支选择器从 `main` 切换到 `codex/visual-quality`，或直接打开上面的链接。

- [P3真实PNG/字体/交互提交1f242565](https://github.com/Chenamel/deterministic-pixel-art/commit/1f24256584e491a054c6bafd825383850b8f0b68)，北京时间2026-10-23 17:47；[示例目录](https://github.com/Chenamel/deterministic-pixel-art/tree/codex/visual-quality/demos/pixel-ui)。
- [P4a独立256分块提交a6d84936](https://github.com/Chenamel/deterministic-pixel-art/commit/a6d84936618b5176c5eecffcea6accd8ec4b745e)，北京时间2026-10-23 23:49；[示例目录](https://github.com/Chenamel/deterministic-pixel-art/tree/codex/visual-quality/demos/chunk-scene)。
- 开发分支还包含2026-10-24的rc.4收口提交；P1发布附件继续保持原冻结包。此次解释不更改默认分支、不合并或提升稳定版本。

## 收回什么、如何使用

每个平台交回一个 `submission-P1-*.zip`，另附能导出的原始会话；失败也提交。包内 `RUN/` 保存可编辑规格、PNG、布局、检查结果、简短反馈及命令/环境记录。平台没提供的token保留空值。

协调端依次核对：输入和Skill哈希、实际命令/报错、PNG重渲染、非目标RGBA、布局及具体视觉意见。逐条归类为“确认修复 / 仍存在 / 无法复现 / 环境阻断”，再决定窄范围修正。原始云端挂载没有复现时，不以别处成功代替。

这是修复回归与易用性反馈，**不是旧版/新版受控A/B或独立审美证明**。本地脚本演练与实际平台结果分开统计；三份已回且工程核验完成，但不自动提升稳定版。无需重做先前八项探索任务，豆包和元宝本轮不重复安排。

构建器：`tools/build_focused_trials.py`；本地记录与限制见 [focused-trials-report.zh-CN.md](focused-trials-report.zh-CN.md)。
