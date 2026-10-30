# 命令示例

[English](usage.md) · [首页](../README.zh-CN.md)

按首页准备环境后，在仓库根目录运行。这里描述 v1.2.0 工作树，旧稳定包可能缺少部分命令。从其他目录运行时使用绝对路径。已安装 Skill 时，将 `src/pixel_art.py` 换成其中的 `scripts/pixel_art.py`、`examples/` 换成 `assets/`、`recipes/` 换成 `scripts/recipes/`。

## 修改命名图集的单格

导出命名单元，避免手抄布局坐标：

```sh
python src/pixel_art.py import --image examples/workflows/atlas-before.png --metadata examples/workflows/atlas-before-layout.json --cell transfer --out output/transfer.json
```

编辑 `output/transfer.json` 后替换该格，并核对允许修改的范围。想直接复跑完整示例，可先用下方提供的替换规格：

```sh
python src/pixel_art.py replace-cell --spec examples/workflows/atlas-editable.json --cell transfer --replacement examples/workflows/atlas-replacement.json --out output/candidate.json --image-out output/candidate.png --metadata output/candidate-layout.json
python src/pixel_art.py verify --image output/candidate.png --compare examples/workflows/atlas-before.png --allow-region 32 0 16 16 --out output/change.json
```

预期得到 `valid: true`、`changed_inside: 66`、`changed_outside: 0`，允许矩形就是原有 transfer 单元。自己的修改使用 `--replacement output/transfer.json`；若未改动，预期为零像素变化。也支持整图导入，保留解码8位 RGBA，包括全透明像素里的 RGB；不恢复原图层或原始绘制指令。

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

分析提供有预算限制的像素事实，审阅增加诊断视图。通过[上下文和命名布局](../skill/deterministic-pixel-art/references/review.md)选择目标背景并理解提示。两种命令都不会自动判断美观或物体含义。

## 使用可编辑配方

```sh
python recipes/icons.py --out-dir output/icons --ink F5C26B
python recipes/buttons.py --out-dir output/buttons --width 96 --content 23 4 70 10
python recipes/chunk_pair.py --out-dir output/bridge
```

配方输出可编辑规格和 PNG。[真实字体检查](../skill/deterministic-pixel-art/references/consumer-ui.md)与[浏览器 UI 演示](../demos/pixel-ui/README.md)分别检查消费端问题，不代表任意字体或 Minecraft 游戏内适配。

## 恢复环境问题

覆盖已有输出必须明确使用 `--force`；将新方案写入单独目录可保留已接受产物。文件系统拒绝硬链接时，可选本地输出目录或 `--portable-output`。从 v1.2.0 起，可在任务 shell 一次设置：PowerShell 用 `$env:PIXELART_PORTABLE_OUTPUT = '1'`，POSIX shell 用 `export PIXELART_PORTABLE_OUTPUT=1`。CLI 与配方继承，单次 `--no-portable-output` 可覆盖。拒绝覆盖规则保持，但便携模式的新文件在写入时可能可见。

[详细恢复步骤](../skill/deterministic-pixel-art/references/workflows.md)包含任务局部环境和缺少 pip 的情况。依赖与命令使用同一 Python；精确复现使用锁定的 Pillow 基准，支持的版本之间多边形填充可能不同。
