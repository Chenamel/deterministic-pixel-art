# P1-W：WorkBuddy / DeepSeek 精确小改

这是修复回归与易用性反馈，无需重画整套，也不做模型排名。使用包中的 Skill，可复用其范例；保留原始输入。

先查看 `deterministic-pixel-art/SKILL.md` 的小改入口。在本目录启动：

```text
python run.py start --model "平台显示的实际模型名称"
```

使用 Python3.10+、Pillow>=10.4,<13；精确复现基准为12.3.0。需要时在任务局部环境安装 `deterministic-pixel-art/requirements.txt`，用同一个已安装Pillow的解释器启动run.py及所有后续命令（它会用sys.executable启动工具）。`python run.py tool ...` 相当于调用包内 pixel_art.py，并保存命令和报错，例如：

```text
python run.py tool import --image inputs/atlas.png --metadata inputs/layout.json --out RUN/editable.json
```

完成两处小改：

1. 图集 transfer 单元 `[32,0,16,16]` 改成**左右并排的两支竖直箭头：左支朝上↑，右支朝下↓**，两支不相连，原色 `D8E3ED`；其余add/refresh/lock保持全部RGBA不变。这里明确了方向和排列，不要求上下堆叠的横向箭头。保存 `RUN/final.json`、`final.png`、新 `final-layout.json`。
2. 将 `inputs/hover.png` 的hover单元边框全部改成不透明 `F5C26B`，包括原来透明的四个角；允许范围是 `inputs/allowed-ring.png` 的非零像素。边框内部和其他单元RGBA不变。保存可独立重渲染的 `RUN/hover.json`、`hover.png`。

通过 `tool verify` 实际检查区域/空心蒙版。查看原尺寸与最近邻预览，说明箭头是否仍清晰；不要以边框的外接矩形代替空心蒙版。辅助脚本和修改过程保存在RUN内。

候选可各用 `RUN/candidates/v01/`、`v02/` 保存规格、PNG、布局和审阅图，再将选定方案写入最终路径，避免反复占用final路径。不自动添加 `--force`；需要后续修改时可另存候选。`replace-cell --metadata`会写完整atlas及新摘要，无需手工重建sidecar。平台不提供token用量时保留null，不猜测。

运行 `python run.py check`，把具体困难、失败及使用建议写入 `RUN/feedback.md`，最后 `python run.py finish`。提交生成的 `submission-P1-W.zip` 和能导出的原始可见会话。失败也提交；检查器只判工程契约，不评箭头审美。新测试使用重新解压的目录；已有输出不要自动加 `--force`。
