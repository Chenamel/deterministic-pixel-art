# 命令示例

[English](usage.md) · [首页](../README.zh-CN.md)

按首页步骤准备环境后，在仓库根目录运行以下命令。本文适用于 v1.2.0；更早的安装包可能缺少部分命令。从其他目录运行时，请使用绝对路径。如果使用已安装的 Skill，将 `src/pixel_art.py` 换成其中的 `scripts/pixel_art.py`、`examples/` 换成 `assets/`、`recipes/` 换成 `scripts/recipes/`。

## 修改命名图集的单格

按名称导出图集中的一格，无需手动填写它在图集中的坐标：

```sh
python src/pixel_art.py import --image examples/workflows/atlas-before.png --metadata examples/workflows/atlas-before-layout.json --cell transfer --out output/transfer.json
```

编辑 `output/transfer.json` 后替换这一格，并检查修改是否超出指定范围。要直接运行完整示例，可先使用下方提供的替换文件：

```sh
python src/pixel_art.py replace-cell --spec examples/workflows/atlas-editable.json --cell transfer --replacement examples/workflows/atlas-replacement.json --out output/candidate.json --image-out output/candidate.png --metadata output/candidate-layout.json
python src/pixel_art.py verify --image output/candidate.png --compare examples/workflows/atlas-before.png --allow-region 32 0 16 16 --out output/change.json
```

预期得到 `valid: true`、`changed_inside: 66`、`changed_outside: 0`：transfer 这一格内改变了 66 个像素，这一格以外没有变化。使用自己修改的文件时，改为 `--replacement output/transfer.json`；如果文件没改，变化像素数应为 0。也支持导入整张图片，保留解码后的 8 位 RGBA 值，包括全透明像素里的 RGB；无法恢复原图层或绘制步骤。

## 修改网格的一种颜色

创建输出目录，将这份完整规格保存为 `output/recolor.json`（当前工作树的 `examples/transparent-grid.json` 也提供同一规格）：

```json
{"version":1,"kind":"grid","rows":["....",".xx.",".xx.","...."],"palette":{".":null,"x":"F5C26B"}}
```

把调色板的 `"x": "F5C26B"` 改成 `"x": "62D8E8"`，保留 `".": null` 和各行网格，然后渲染：

```sh
python src/pixel_art.py render --spec output/recolor.json --out output/recolor.png --preview output/recolor-preview.png
```

预期得到4×4图像，中间4个像素变成青色，边缘透明；32×32预览为8倍最近邻放大。保留JSON即可继续修改。稳定版v1.1.1使用自己的脚本路径，也能渲染这份内联规格；它的包内没有 `transparent-grid.json`。

## 分析或审阅

```sh
python src/pixel_art.py inspect --image output/gem.png --grid
python src/pixel_art.py review --image output/gem.png --out-dir output/gem-review
```

`inspect` 输出尺寸、颜色、透明度等分析结果，并限制逐项列出的数量，避免报告过长。`review` 还会生成便于看图检查的预览。可按[背景、图集布局和检查提示的说明](../skill/deterministic-pixel-art/references/review.md)配置检查条件。两个命令都不能代替人工判断图案是否容易辨认、是否好看。

## 使用 Python 示例脚本

```sh
python recipes/icons.py --out-dir output/icons --ink F5C26B
python recipes/buttons.py --out-dir output/buttons --width 96 --content 23 4 70 10
python recipes/chunk_pair.py --out-dir output/bridge
```

这些 Python 示例脚本会输出可继续编辑的 JSON 文件和 PNG。[真实字体检查](../skill/deterministic-pixel-art/references/consumer-ui.md)说明如何检查文字是否放得下；[浏览器 UI 演示](../demos/pixel-ui/README.md)展示按钮状态和交互检查。换用其他字体或接入 Minecraft 后，仍需在实际环境中检查。

## 恢复环境问题

覆盖已有文件必须明确使用 `--force`；建议把新方案写入单独目录，保留已确认的版本。如果文件系统不支持创建硬链接，可改用本地输出目录或添加 `--portable-output`。从 v1.2.0 起，也可在终端设置一次：PowerShell 用 `$env:PIXELART_PORTABLE_OUTPUT = '1'`，POSIX shell 用 `export PIXELART_PORTABLE_OUTPUT=1`。后续工具命令和示例脚本都会使用便携输出模式；单条命令加 `--no-portable-output` 可临时关闭。便携模式仍不会自动覆盖已有文件，但其他程序可能读到尚未写完的新文件。

[详细恢复步骤](../skill/deterministic-pixel-art/references/workflows.md)说明如何创建项目专用的 Python 环境，以及缺少 pip 时如何安装依赖。安装依赖和运行命令请使用同一个 Python。需要得到完全一致的像素时，请使用项目指定的 Pillow 12.3.0；其他受支持版本的多边形填充结果可能不同。
