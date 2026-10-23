# P1-V：Gemini 命名PNG与目标背景审阅

这是一次命名PNG编辑与视觉使用反馈，不要求自动审美打分或全面找bug。读取包内Skill的小改、命名编辑和审阅入口。

在本目录启动并查看基线：

```text
python run.py start --model "平台显示的实际模型名称"
python run.py tool review --image inputs/materials.png --metadata inputs/layout.json --context inputs/context.json --out-dir RUN/before-review
python run.py tool import --image inputs/materials.png --metadata inputs/layout.json --out RUN/editable.json
```

使用Python3.10+、Pillow>=10.4,<13，12.3.0为复现基准；需要时使用任务局部环境安装包内requirements。

只修改 `metal` 单元：让它在浅背景上更容易读出受光面与金属体积，保留物体形状、32×32尺寸及原整体风格，不加文字。其他单元必须保持全部RGBA。不要因为工具警告就自动删除有意细节。

保存 `RUN/final.json`、`final.png` 和新 `final-layout.json`，通过tool命令实际渲染/检查，再生成：

```text
python run.py tool review --image RUN/final.png --metadata RUN/final-layout.json --context inputs/context.json --compare inputs/materials.png --out-dir RUN/review
```

实际查看修改前后PNG、原尺寸、深浅底、灰度和剪影；不能只读JSON。写 `RUN/visual-notes.md`：查看了哪些图、哪些具体区域改善/持平/退步、状态或材质能否辨认，以及未确认内容。`light`主背景的剪影应可见；工具不为美观做最终判断。将操作困难和改进建议写到 `RUN/feedback.md`。

运行 `python run.py check` 和 `python run.py finish`，提交 `submission-P1-V.zip` 与可导出的原始会话。保留辅助脚本和候选；失败也提交。本结果是参与者自评，不能冒充独立盲评。
