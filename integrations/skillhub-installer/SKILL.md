---
name: deterministic-pixel-art
description: Bilingual installer for Deterministic Pixel Art v1.4.1 (verified online install with retries or offline local ZIP mode). Installs the deterministic pixel sprite, tile, UI, and lossless PNG editing Skill with SHA-256 verification.
slug: deterministic-pixel-art
version: 1.4.1
displayName: Deterministic Pixel Art
summary: Install Deterministic Pixel Art v1.4.1 (supports retryable online download and verified offline --archive ZIP install) for sprites, UI, scenes, and scoped PNG/draw edits.
license: MIT
homepage: https://github.com/Chenamel/deterministic-pixel-art
tags: [pixel-art, image-editing, python, deterministic, sprites]
---

# Deterministic Pixel Art 安装指南 / Installer (`v1.4.1`)

本 SkillHub 入口只包含纯文本安装说明（`SKILL.md`）与校验安装脚本（[install.py](install.py)），用于在安全校验后部署完整的 **Deterministic Pixel Art v1.4.1**（含渲染与局部编辑 CLI、标准工作流配方和示例素材，[GitHub Release v1.4.1](https://github.com/Chenamel/deterministic-pixel-art/releases/tag/v1.4.1)）。

This SkillHub package is a text-only verified installer containing this guide and [install.py](install.py). It verifies and deploys the full `v1.4.1` Skill archive (`SHA-256: d6a77c0696134b1419470ff36bef5adb24cdb8cf9233323f0b1e24a2c5ba2671`).

---

## 适用场景与核心能力 / When to use

适合在以下日常开发与素材制作任务中调用本 Skill：

- **确定性像素图创作**：生成 16×16 / 32×32 游戏图标、道具、角色、`grid` / `draw` 矢量绘图、UI 面板、多状态按钮、瓦片场景与精灵图集（严格硬边像素，无抗锯齿混色）。
- **无损局部修改（不破坏已有画面）**：
  - `pixel_art.py replace-cell` / `recolor`：按坐标网格或限定区域精确替换已有静态 PNG 颜色与局部单元格，周边像素与 Alpha 透明通道保持字节级不变；
  - `asset_toolkit.py patch-draw`：按标签、索引或 tag 局部修改 `asset_toolkit.json` 的绘制指令，无需重写整份定义。
- **一键打包交付与防呆自检**：用 `asset_toolkit.py deliver` 与 `rebuild` 输出包含源文件、1× 原图、放大预览与 `REBUILD.md` 的交付压缩包，并自动检查 8-连通断块、4-邻域孤立像素点及零 `__pycache__` 污染。

Best suited for game icons, character sprites, UI panels, tile scenes, non-destructive scoped PNG color/cell edits, `patch-draw` instruction updates, and reproducible `deliver`/`rebuild` asset bundles.

---

## 运行前置条件与安全边界 / Requirements & security guarantees

- **运行环境**：`Python >= 3.10`，安装后按需使用 `Pillow>=10.4,<13`（记录在目标目录的 `requirements.txt`）。
- **安全与可靠性约束**：
  - **严格校验固定 SHA-256**（`d6a77c0696134b1419470ff36bef5adb24cdb8cf9233323f0b1e24a2c5ba2671`）；校验失败立刻中止。
  - **路径与大小防呆**：限制压缩包与解压总量各不超过 16 MiB，拒绝 `..` 路径穿越、反斜杠穿越、绝对路径与符号链接，也不覆盖已存在目录。
  - **内置网络重试 + 离线兜底**：默认最多重试 3 次；同时提供 `--archive` 参数支持读取本地已下载压缩包完全离线校验安装（不会偷偷请求未授权第三方域名）。

---

## 安装步骤 / Installation

### 1A. 在线安装（默认自动重试 3 次）/ Online install with automatic retries

```text
python install.py --destination ./skills/deterministic-pixel-art
```

如需调高重试次数或自定义超时：

```text
python install.py --destination ./skills/deterministic-pixel-art --retries 5 --timeout 45
```

### 1B. 国内网络受限或离线环境安装（推荐兜底）/ Offline install via `--archive`

如果当前环境访问 GitHub 超时，可先通过浏览器或已有网络渠道从官方 Release 下载 `deterministic-pixel-art-v1.4.1.zip`，再传入 `--archive` 离线安装（脚本仍会严格核对相同的官方 `ARCHIVE_SHA256`）：

```text
python install.py --archive ./deterministic-pixel-art-v1.4.1.zip --destination ./skills/deterministic-pixel-art
```

若使用你信任的 HTTPS 镜像地址，也可显式通过 `--url https://...` 指定，安装器仍会在解压前核验同一官方 SHA-256，绝不放行被篡改的压缩包。

### 2. 安装 Python 运行依赖 / Install runtime dependency

```text
python -m pip install -r ./skills/deterministic-pixel-art/requirements.txt
```

---

## 安装后快速上手示例 / Quick-start examples after install

设 `<skill>` 为刚安装完成的 `./skills/deterministic-pixel-art` 目录。安装完成后可立即运行以下三类典型任务：

### 示例 1：从 JSON 渲染像素图标并检查孤立像素

```text
python <skill>/scripts/pixel_art.py render --spec <skill>/assets/gem-16.json --out ./out/gem.png --preview ./out/gem-preview.png
```

### 示例 2：一键生成可追溯交付包并校验像素级重建

```text
python <skill>/scripts/recipes/asset_toolkit.py deliver --source <skill>/assets/gem-16.json --out-dir ./out/toolkit-gem --pack-zip ./out/toolkit-gem.zip
python <skill>/scripts/recipes/asset_toolkit.py rebuild --input ./out/toolkit-gem.zip --out-dir ./out/toolkit-rebuilt
```

### 示例 3：按区域无损改色或局部修补 `draw` 指令

```text
python <skill>/scripts/pixel_art.py recolor --help
python <skill>/scripts/recipes/asset_toolkit.py patch-draw --help
```

完整文档、规范格式与更多示例请在安装后查看 `<skill>/SKILL.md` 及 `<skill>/references/formats.md`、`<skill>/references/toolkit.md`、`<skill>/references/workflows.md`。

---

## 常见问题解答 / Troubleshooting FAQ

- **Q1：国内安装时提示 `Download failed` / 连接超时怎么办？**
  - 先尝试 `--retries 5 --timeout 60`；若仍不通，手动下载 `deterministic-pixel-art-v1.4.1.zip` 后使用 `python install.py --archive ./deterministic-pixel-art-v1.4.1.zip --destination <目标目录>`，可免外网并保留完整 SHA-256 安全校验。
- **Q2：提示 `Destination already exists`（目标目录已存在）？**
  - 为防止误删已有自定义修改，安装器拒绝覆盖非空/已存在目录。请更换新的 `--destination` 路径，或自行备份清理旧目录后重试。
- **Q3：运行 Skill 脚本时提示 `No module named 'PIL'`？**
  - 本安装包为保证轻量化和零环境侵入，不会擅自改动系统 Python 包。请在运行 `<skill>/scripts/pixel_art.py` 使用的同一个 Python/venv 中执行 `python -m pip install -r <skill>/requirements.txt`。
- **Q4：提示 `SHA-256 mismatch` 校验失败？**
  - 通常是下载中断导致的截断文件或错误压缩包。请删除残缺文件并确认来源为 [GitHub v1.4.1 Release](https://github.com/Chenamel/deterministic-pixel-art/releases/tag/v1.4.1)（预期摘要 `d6a77c0696134b1419470ff36bef5adb24cdb8cf9233323f0b1e24a2c5ba2671`）。
- **Q5：安装后运行会在项目里留下 `__pycache__` 吗？**
  - 不会。`v1.4.1` 的 `pixel_art.py` 与 `asset_toolkit.py` 作为 CLI 启动时会自动关闭字节码写入。
