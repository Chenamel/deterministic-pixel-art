# 确定性像素资产

[English](README.md) · [MIT 协议](LICENSE) · [规格与 Python API](skill/deterministic-pixel-art/references/formats.md)

通过字符网格、整数绘图指令、像素蒙版和命名图集生成可编辑的 PNG。运行时只依赖 Python 与 Pillow，使用精确像素坐标与最近邻预览。Minecraft GUI 风格是可选预设。

![原创 UI 对照：左为冻结基线，右为新版候选](docs/quality/ui.png)

## 快速上手

初始验证环境为 Python 3.14.2、Pillow 12.3.0。在仓库目录创建虚拟环境：

```sh
python -m venv .venv
```

Windows PowerShell 激活：`.\.venv\Scripts\Activate.ps1`；macOS/Linux shell：`source .venv/bin/activate`。

```sh
python -m pip install -r requirements.txt
python src/pixel_art.py render --spec examples/gem-16.json --out output/gem.png --preview output/gem-preview.png
python src/pixel_art.py validate --image output/gem.png
python src/pixel_art.py review --image output/gem.png --out-dir output/gem-review
```

在其他工作目录执行时，为脚本、输入和输出使用绝对路径。已有输出默认拒绝覆盖，需要有意覆盖时使用 `--force`。

## 选择示例

| 示例 | 用途 |
|---|---|
| [gem-16.json](examples/gem-16.json) | 自定义调色板、镜像的 16×16 精灵 |
| [asymmetric-ship-32.json](examples/asymmetric-ship-32.json) | 多边形构成的 32×32 非对称精灵 |
| [generic-panel-96x40.json](examples/generic-panel-96x40.json) | 非 Minecraft 配色的通用 GUI |
| [minecraft-button-states.json](examples/minecraft-button-states.json) | 五种命名按钮状态组成的图集 |
| [quality/](examples/quality/) | 八项可编辑范例：图标、材质、UI 状态、布局及 Minecraft 控件 |

规格与 PNG 一起保存。检查原尺寸与放大预览；尺寸和像素断言不能代替对方向、状态语义和辨识度的判断。

`review` 输出审阅图与建议性 JSON 报告，包括原尺寸、整数放大、深浅背景、灰度，以及可选的命名单元、精灵剪影与基线差异。通过[审阅上下文](skill/deterministic-pixel-art/references/review.md)声明目标背景、内容预留区和功能性颜色对。有提示仍返回成功，无效输入返回错误；工具不修改原图，也不为审美打分。

[格式说明](skill/deterministic-pixel-art/references/formats.md)包含 JSON v1、简短 GUI DSL、`render(spec)`、`Canvas`、校验规则与图集元数据。未知符号、未知指令、隐式裁切会明确报错。矩形坐标统一为 `x, y, width, height`。

## 作为 Codex Skill 使用

从 [Releases](https://github.com/Chenamel/deterministic-pixel-art/releases) 下载 Skill ZIP 与 SHA-256 清单；版本 tag 同时固定运行时和指导文档，`v1.0.0` 保留上一稳定基线。验证哈希后，将压缩包中的 `deterministic-pixel-art` 整个目录放到 Codex 的 skills 目录（`$CODEX_HOME/skills`，默认 `~/.codex/skills`），并在任务可用的 Python 环境中安装该目录的 `requirements.txt`。旧版备份应放在 skills 发现目录之外。仓库中的同一分发目录是 [skill/deterministic-pixel-art](skill/deterministic-pixel-art/SKILL.md)。

调用示例：“使用 `$deterministic-pixel-art` 创建四个 16×16 方向图标，放入有状态名称的横向图集，保留一像素透明边距，并生成放大预览。”

安装开发依赖后运行 `python -B tools/check.py`，可生成经过测试的 ZIP。压缩包在本地生成，不提交到仓库；检查过程不安装全局 Skill。

## 实测收益与代价

v1.1.1 修复空描边、主审阅背景、宽图拼板及文件提交问题，并补充错误定位和 Pillow 兼容检查。详见[外部反馈与可靠性报告](docs/audit-feedback.md)；这些修复不附带新的审美提升结论。

本次质量更新增加按任务选择的创作指导、八项原创可编辑范例及上下文审阅工具。八项前后对照的**作者代理自评**中，六项改善、两项保持原像素；**v1.0.0 的 43 张迁移产物全部保持像素兼容**。JSON v1、现有 Python 公共接口与旧命令行为保留。样本有限且未盲评，不能据此证明模型的通用画质提高；未做真实字体适配和游戏内验收。详见[质量报告](docs/quality-report.zh-CN.md)、[英文报告](docs/quality-report.md)和[原始结果](docs/measurements/visual-quality.json)。

以下是此前渲染优化的独立历史比较：

初始 Windows 评估中，43 张历史图有 40 张逐像素保持。3 张有意变化修复了不完整的按钮合成，或将 footer 对齐实际使用中的资源。

| 纯渲染场景 | 原版 → 新版中位耗时 | 倍率 |
|---|---:|---:|
| 128×48 面板 | 1.3364 → 0.1519 ms | 8.80× |
| 16×16 方块面 | 0.3214 → 0.1032 ms | 3.11× |
| 80×16 图集 | 0.5105 → 0.4381 ms | 1.17× |

以上是单一环境实测，不含进程启动和磁盘 I/O。相同产物的完整命令**慢了 47.03 ms（+35%）**；图集尾部耗时及部分 Python 分配峰值也增加。未测量 token 节省、模型修正轮次或游戏内质量。详见[完整报告](docs/optimization-report.zh-CN.md)和[实测 JSON](docs/measurements/metrics.json)。

这些资产的纯渲染已低于一毫秒，继续压榨速度的绝对收益有限。本次质量更新不宣称节省创作耗时或 token；更丰富的细节也可能增加颜色与绘图操作。

## 开发检查

```sh
python -m pip install -r requirements-dev.txt
python -B tools/check.py
```

检查包含 33 个单元测试、43 张逐图回归、86 个历史夹具文件和八项冻结研究基线的完整性校验、基准测试、可复现 ZIP 打包及 37 项独立目录包执行检查。工作目录含中文和空格，不依赖原模组路径或 Codex 安装；产物写入被 Git 忽略的 `output/` 与 `evaluation/`。

如有 skill-creator 官方校验器，可追加执行：

```sh
python -B tools/test_skill.py --python /path/to/python --validator /path/to/quick_validate.py
```

默认内置的项目校验器检查元数据与引用，不冒充官方校验器。GitHub Actions 配置了 Windows、Ubuntu 和 Python 3.14；配置存在不等于已在相应平台通过。

`src/` 是运行时源码，`skill-content/` 是维护的指导与参考文档，`skill/` 是生成的分发版本。修改源目录后运行检查来同步 Skill；`tools/package_skill.py` 复制来源并记录逐文件清单。`quality/` 保留需求、冻结基线、备选和自评记录。`baselines/` 只保留必要历史夹具，见[来源说明](docs/PROVENANCE.md)；原项目完整保护档案保留在仓库之外。

## 协议

仓库及独立 Skill 使用 [MIT](LICENSE)。Pillow 和仅开发使用的 PyYAML 通过依赖安装，不随仓库捆绑。
