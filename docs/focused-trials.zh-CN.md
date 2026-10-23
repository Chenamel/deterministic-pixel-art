# 三项定向复测：发给谁、发什么

本轮只开三个新会话，每个平台一个任务。每个 ZIP 都包含冻结的 **v1.2.0-rc.2 Skill**、固定输入、短提示词和记录器；无需另外安装旧测评包。

| 交给谁 | 下载包 | 任务 |
|---|---|---|
| **WorkBuddy / DeepSeek** | [P1-W-DeepSeek.zip](https://github.com/Chenamel/deterministic-pixel-art/releases/download/v1.2.0-rc.2/P1-W-DeepSeek.zip) | 改一个命名图标，再改空心边框；验证其他RGBA不变 |
| **千问办公助理** | [P1-C-Qwen.zip](https://github.com/Chenamel/deterministic-pixel-art/releases/download/v1.2.0-rc.2/P1-C-Qwen.zip) | 原生与便携输出、拒绝覆盖、依赖和挂载记录 |
| **Gemini任务模式** | [P1-V-Gemini.zip](https://github.com/Chenamel/deterministic-pixel-art/releases/download/v1.2.0-rc.2/P1-V-Gemini.zip) | 只改metal单元并实际看图，检查浅背景及剪影 |

发布状态：**本地三包已验证；GitHub下载与当前提交CI尚待确认。确认后更新此行。**

## 直接复制的启动语

DeepSeek、Gemini：上传对应ZIP，复制：

> 解压此任务包，阅读根目录的 START_HERE.md，使用包内 Skill 实际完成任务。按 run.py 记录命令，不修改原始输入，保留失败。最后提供 submission-P1-*.zip 和可导出的原始会话。请给具体困难和改进建议，不需要全面评分或模型排名。

千问：无需上传ZIP，复制：

> 请下载 https://github.com/Chenamel/deterministic-pixel-art/releases/download/v1.2.0-rc.2/P1-C-Qwen.zip 并解压，阅读 P1-C/START_HERE.md，使用包内 Skill 实际执行任务。按 run.py 记录命令和失败，区分原生与便携输出，不自动添加 --force。最后提供 submission-P1-C.zip 和可导出的原始会话。无法下载时给出实际错误，不假装已执行。

每包中的 `START_HERE.md` 就是完整任务提示词。用户不必手抄命令或重新整理测评材料；需要完整提示词时也可直接复制仓库中的 [P1-W](../benchmarks/focused/P1-W.md)、[P1-C](../benchmarks/focused/P1-C.md)、[P1-V](../benchmarks/focused/P1-V.md)。

## 收回什么、如何使用

每个平台交回一个 `submission-P1-*.zip`，另附能导出的原始会话；失败也提交。包内 `RUN/` 保存可编辑规格、PNG、布局、检查结果、简短反馈及命令/环境记录。平台没提供的token保留空值。

协调端依次核对：输入和Skill哈希、实际命令/报错、PNG重渲染、非目标RGBA、布局及具体视觉意见。逐条归类为“确认修复 / 仍存在 / 无法复现 / 环境阻断”，再决定窄范围修正。原始云端挂载没有复现时，不以别处成功代替。

这是修复回归与易用性反馈，**不是旧版/新版受控A/B或独立审美证明**。本地脚本演练与实际平台结果分开统计；三份新任务尚未返回，不自动提升稳定版。无需重做先前八项探索任务，豆包和元宝本轮不重复安排。

构建器：`tools/build_focused_trials.py`；本地记录与限制见 [focused-trials-report.zh-CN.md](focused-trials-report.zh-CN.md)。
