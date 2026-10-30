# P1-C：千问办公助理云端环境与输出

这是针对原云端挂载的复测。请实际执行，记录平台显示的模型名称、Python/Pillow路径、挂载位置、依赖失败和恢复方式；无法确认是否原文件系统就写“未知”。

先读包内 `deterministic-pixel-art/SKILL.md`，在本目录运行：

```text
python run.py start --model "平台显示的实际模型名称"
python run.py tool render --spec inputs/panel.json --out RUN/native.png --preview RUN/native-preview.png --preview-background E9EDF2
```

Python3.10+、Pillow>=10.4,<13；12.3.0为固定复现基准。如缺依赖，优先任务局部环境。挂载不支持虚拟环境符号链接时，在本地临时目录创建环境，或安装到新的任务局部 `deps/` 并为任务进程设置PYTHONPATH。保存原生失败，换环境后的成功另记；不要修改工具或全局包。

在部分对象存储挂载上，默认硬链接发布可能被拒；这正是需要保留的环境事实，不自动改成 `--force`。目录外验证（例如输出到本地临时目录）也可通过 `run.py tool ...` 记录命令、环境、退出码和stdout/stderr；记录器仅对RUN内产物自动保存前后哈希，目录外产物请另行保存哈希/图片。只有笔记不能代替该次命令证据。平台不提供token用量时保留null。

无论默认输出是否成功，都实际运行下面的便携输出：

```text
python run.py tool render --spec inputs/panel.json --out RUN/portable.png --preview RUN/portable-preview.png --preview-background E9EDF2 --portable-output
python run.py tool render --spec inputs/panel.json --out RUN/portable.png --portable-output
python run.py tool review --image RUN/portable.png --out-dir RUN/review --portable-output
```

第二次portable渲染应拒绝覆盖并返回2，保留前次PNG哈希。该非零退出是预期测试结果；继续审阅和检查。不要靠 `--force` 绕过文件系统问题。便携新文件可能在写入期间可见，不声称具有原子可见性。

请实际查看预览，确认目标底色和面板没有截断；将环境事实、原生/便携结果和恢复步骤写到 `RUN/environment-notes.md`，使用困难写到 `RUN/feedback.md`。运行 `python run.py check` 和 `python run.py finish`，提交 `submission-P1-C.zip` 及可导出的会话。失败也可归档；不要把“本环境未报错”写成“所有云端挂载都已修复”。
