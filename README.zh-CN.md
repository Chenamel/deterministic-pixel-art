# 确定性像素资产

[English](README.md) · [MIT](LICENSE) · [版本下载](https://github.com/Chenamel/deterministic-pixel-art/releases)

面向 AI 的可编辑像素 PNG 工具与 Skill，覆盖图标、精灵、UI、命名图集和组件场景。用字符网格、整数绘图指令或 Python 蒙版创作，也能无损导入已有 PNG、局部修改并核对变化范围。Minecraft 风格按需选用。

![原创原生128像素精灵，最近邻放大展示](docs/workflows/sprite-128-preview.png)

**最新稳定版为 v1.1.1。** 当前开发分支包含冻结 v1.2.0-rc.6 之后的改动，尚未形成新编号版本。下面的用法适用于本工作树及其配套生成 Skill；历史发布包以各自版本说明为准。

## 快速上手

需要 Python 3.10+、Pillow >=10.4,<13。固定复现环境为 Python 3.14.2 / Pillow 12.3.0，`requirements.txt` 锁定该 Pillow 基准。

```sh
python -m venv .venv
```

PowerShell 激活：`.\.venv\Scripts\Activate.ps1`；macOS/Linux shell 激活：`source .venv/bin/activate`，然后执行：

```sh
python -m pip install -r requirements.txt
python src/pixel_art.py render --spec examples/gem-16.json --out output/gem.png --preview output/gem-preview.png
python src/pixel_art.py inspect --image output/gem.png --grid
python src/pixel_art.py review --image output/gem.png --out-dir output/gem-review
```

规格与 PNG 一起保留，在目标背景下检查原尺寸与整数放大图。已有文件必须明确使用 `--force` 才能覆盖；从其他目录运行时使用绝对路径。

## 按任务选入口

| 任务 | 从这里开始 |
|---|---|
| 小型网格精灵 | [透明网格](examples/transparent-grid.json)、[镜像宝石](examples/gem-16.json) |
| 新建非对称精灵 | [32×32飞船](examples/asymmetric-ship-32.json)、[像素画指导](skill/deterministic-pixel-art/references/pixel-art.md) |
| UI 与按钮状态 | [通用面板](examples/generic-panel-96x40.json)、[UI指导](skill/deterministic-pixel-art/references/ui.md)、[短配方](skill/deterministic-pixel-art/references/recipes.md) |
| 已有 PNG / 命名图集局改 | [导入、单格替换与差异核对](skill/deterministic-pixel-art/references/workflows.md) |
| 图片事实与审阅 | [文本分析](skill/deterministic-pixel-art/references/text-workflow.md)、[审阅上下文](skill/deterministic-pixel-art/references/review.md) |
| 独立分块绘制 | [边界约定](skill/deterministic-pixel-art/references/chunking.md)、[四入口256场景演示](demos/chunk-scene/README.md) |
| Minecraft 风格 UI | [专项指导](skill/deterministic-pixel-art/references/minecraft.md) |

已有命名图集可以先导出单格：

```sh
python src/pixel_art.py import --image examples/workflows/atlas-before.png --metadata examples/workflows/atlas-before-layout.json --cell transfer --out output/transfer.json
```

编辑 `transfer.json` 后，将它作为 `--replacement` 替换回图集：

```sh
python src/pixel_art.py replace-cell --spec examples/workflows/atlas-editable.json --cell transfer --replacement output/transfer.json --out output/candidate.json --image-out output/candidate.png --metadata output/candidate-layout.json
python src/pixel_art.py verify --image output/candidate.png --compare examples/workflows/atlas-before.png --allow-region 32 0 16 16
```

也支持整图导入，不量化颜色，保留解码后的8位 RGBA，包括全透明像素里的 RGB。[JSON v1 与 Python API](skill/deterministic-pixel-art/references/formats.md)。

需要参数变体时使用短配方：

```sh
python recipes/icons.py --out-dir output/icons --ink F5C26B
python recipes/buttons.py --out-dir output/buttons --width 96 --content 23 4 70 10
python recipes/chunk_pair.py --out-dir output/bridge
```

配方输出可编辑规格与 PNG。[真实字体辅助](skill/deterministic-pixel-art/references/consumer-ui.md)可检查文字位置，[浏览器演示](demos/pixel-ui/README.md)另行检查交互与缩放；这些结果不代表游戏内或任意字体适配已经通过。

文件系统拒绝硬链接时使用 `--portable-output`。当前开发版可在任务 shell 一次设置：PowerShell 用 `$env:PIXELART_PORTABLE_OUTPUT = '1'`，POSIX shell 用 `export PIXELART_PORTABLE_OUTPUT=1`。CLI 与配方继承，单次 `--no-portable-output` 可覆盖。拒绝覆盖规则保持；便携模式的新文件在写入过程中可能可见。[环境恢复步骤](skill/deterministic-pixel-art/references/workflows.md)。

## 安装 Skill

从 [Releases](https://github.com/Chenamel/deterministic-pixel-art/releases) 下载版本 ZIP 与 SHA-256 清单，核验后将其中的 `deterministic-pixel-art` 文件夹放入 `$CODEX_HOME/skills`，默认是 `~/.codex/skills`。在任务实际使用的 Python 环境安装该文件夹中的 `requirements.txt`；旧安装备份放在技能发现目录之外。

仓库中的[生成 Skill](skill/deterministic-pixel-art/SKILL.md)可独立运行，渲染器与配方位于其 `scripts/`。示例请求：“使用 `$deterministic-pixel-art` 制作四个16×16方向图标，组成命名图集，保留1px透明边距，并在原尺寸核对各方向。”

## 实测依据与边界

- **兼容性：** 43张 v1.0.0 稳定迁移产物保持像素兼容。无损导入与局改比较解码 RGBA，不要求 PNG 压缩字节相同。
- **外部使用：** 已收集八类任务材料，涉及图标、精灵、材质、UI、环境恢复和分块。LT04 原始方向失败与 LT08 早期过程缺口继续保留；收齐八类不等于八项完整通过。
- **本轮收口：** 源码、生成 Skill 与98文件开发 ZIP 一致。新检查结果及仓库校验器修正见[收口报告](docs/candidate-consolidation-20261030.zh-CN.md)。
- **尚未证明：** 单版本使用不能证明普遍画质、token 或任务耗时收益；新旧受控比较、真实 Minecraft 游戏内表现另行验收。[当前发布条件](docs/release-readiness.zh-CN.md)。

历史性能、作者视觉自评和外部反馈分别见[初始优化报告](docs/optimization-report.zh-CN.md)、[视觉研究](docs/quality-report.zh-CN.md)、[工作流报告](docs/workflow-report.zh-CN.md)、[易用性成本](docs/usability-20261029.zh-CN.md)。纯渲染提速不含启动与磁盘；历史完整命令测量未显示提速。工具不提供自动审美评分。

## 开发检查

```sh
python -m pip install -r requirements-dev.txt
python -B tools/check.py
```

检查覆盖源码、稳定图像回归、历史夹具、导入/编辑/组合、可复现打包，以及中文空格路径、不同工作目录的独立运行；会生成本地产物，不自动安装全局 Skill。打包后可执行 `tools/test_skill.py --python /path/to/python --validator /path/to/quick_validate.py` 加入官方格式校验。

运行时维护在 `src/`，配方在 `recipes/`，指导源在 `skill-content/`；`tools/package_skill.py` 生成 `skill/` 与本地 ZIP。平台结论以完成的 CI 为准，Windows/Ubuntu 配置存在本身不算通过。[夹具来源](docs/PROVENANCE.md)。

## 协议

代码、原创图像和独立 Skill 使用 [MIT](LICENSE)。仅仓库演示附带的未修改 Silkscreen Regular 遵循 [SIL OFL 1.1](demos/pixel-ui/fonts/OFL.txt)，字体不进入 Skill ZIP。Pillow 与仅开发使用的 PyYAML 通过依赖安装，不随包捆绑。
