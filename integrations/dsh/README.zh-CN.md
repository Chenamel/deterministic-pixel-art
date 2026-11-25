# 在 DSH 中使用 Deterministic Pixel Art

[English](README.md)

在 DSH 对话里直接说想画什么，或贴一张已有 PNG 让它只改其中某一块。插件包内已经自带绘制脚本、示例和说明，平时用不需要自己写像素坐标或 Python 代码。

## 快速开始（装完即可用）

在安装并启用了本插件的 DSH 配置里新开一个对话，发送：

> 请使用 deterministic-pixel-art，画一个 16×16、透明背景的像素提灯。先读取这个 Skill 并检查 Python/Pillow 环境，最后把原尺寸 PNG、可二次编辑的 JSON 和 8 倍放大预览一起交给我，并看图核对一遍。

拿到图后如果要微调局部，可以接着说：

> 只把提灯的金属外框改成深棕色，玻璃和其他地方不动；保留第一版，另存修改后的 PNG 和源文件。

也可以直接发已有 PNG，写清改哪里、留哪里。注意确认 AI 交回来了**原尺寸 PNG** 和 **JSON 源文件**（只有放大图或仅调用看图工具不算完成交付）。

## 安装与运行前提

| 项目 | 说明 |
| --- | --- |
| 显示名称 | Deterministic Pixel Art |
| npm 包名 | `dsh-skill-deterministic-pixel-art` |
| 对话内 Skill 名称 | `deterministic-pixel-art` |
| 当前插件版本 | `0.1.5`（已验证适配 DSH `0.2.2-rc.1`–`rc.5`、`0.2.3-alpha.1`） |
| 依赖环境 | Node **>=24.9.0**、Python **3.10+**、Pillow **>=10.4,<13**（固定推荐 12.3.0） |

在常用的 CLI 配置中执行安装（将 `YOUR-PROFILE` 换成实际的非 `desktop` 配置名；桌面端直接在 DSH 桌面插件页安装，或去 [GitHub Releases](https://github.com/Chenamel/deterministic-pixel-art/releases/latest) 下载 TGZ）：

```text
dsh plugin --profile YOUR-PROFILE add dsh-skill-deterministic-pixel-art@0.1.5
```

> 旧版 `0.1.3` 卡死了 `0.2.2-rc.3` 上限导致新 DSH 装不上；`0.1.5` 已放开版本限制，通过 npm 可直接升级安装，不必等市场同步。

## 可选：新建纯命令行配置

已有可用 DSH 配置可以跳过本节。在 `dsh`（或 DSH NEXT 的 **DSH Terminal**）里挑一个新配置名（如 `pixel-art`），**只在首次初始化一次**（`--from-default-profile` 会覆盖已有配置与插件）：

```text
dsh --profile pixel-art --from-default-profile headless --help
```

然后从 npm（或下载后的本地 `.tgz` 绝对路径）装入插件：

```text
dsh plugin --profile pixel-art add dsh-skill-deterministic-pixel-art@0.1.5
```

```text
dsh plugin --profile pixel-art add "/absolute/path/to/dsh-skill-deterministic-pixel-art-0.1.5.tgz"
```

如果使用常规 DeepSeek 账号登录（而非自配 API Key），完成登录后在任务目录放入如下 `dsh-account.patch.yml`（仅配置开关，不要写入密钥）：

```yaml
- id: agent-default-model
  config:
    provider: deepseek-account
    model: deepseek-flash
- id: credentials
  disabled: false
- id: authorization
  disabled: false
- id: deepseek-account
  disabled: false
```

在准备存图的工作目录发起任务，并用返回的真实 `sessionId` 继续改图（若已有 API Key 配置，去掉 `--patch` 即可）：

```text
dsh --profile pixel-art --patch ./dsh-account.patch.yml --json --permission-mode workspace-write --approval-policy never "用 deterministic-pixel-art 画一个16×16灯笼PNG，保留可编辑JSON。"
```

```text
dsh --profile pixel-art --patch ./dsh-account.patch.yml --json --permission-mode workspace-write --approval-policy never --session-id session-YOUR-ID "把轮廓改深一点。"
```

*(提示：`--approval-policy never` 会让需要审批的动作直接失败；发起任务会消耗模型额度。)*

## 常见问题排查

- **对话里找不到 Skill**：运行 `dsh --profile pixel-art --dump-config` 确认包含 `deterministic-pixel-art-skill`，并核对当前使用的 profile 与安装时一致（同名本地 Skill 会覆盖插件版）。
- **缺 Python / Pillow**：安装 npm 插件不会顺带安装 Python 依赖，需确保当前环境已装 Python 3.10+ 和 Pillow（可用 `load_workspace_dependencies` 选择环境）。
- **报 `ACCOUNT_SIGN_IN_REQUIRED`**：检查登录状态、`DSH_HOME` 与配置覆盖项即可，不用重装插件。
- **Windows 报 `windows-acl workspace grant failed`**：把任务放到用户目录下当前账号拥有完全权限的独立文件夹里重试（保持 `workspace-write`）。
- **非 DSH 用户安装原生 Skill**：见 [INSTALL.md](https://github.com/Chenamel/deterministic-pixel-art/blob/main/INSTALL.md)。

<details>
<summary>兼容细节、审计与本地打包说明（开发维护者参考）</summary>

- **宿主兼容声明**：`engines.dsh: "*"` 且 DSH Skill registry / Cordis 宿主 peer 设为通配符，供 DSH 内置 pnpm 安装器放行宿主预发布版（普通 npm 严格 peer 解析仍可能拦截）。
- **测试矩阵与基线**：Windows/Ubuntu CI 定期在 DSH `0.2.2-rc.1`–`rc.5` 与 `0.2.3-alpha.1` 上校验归档、Skill 服务及工具搬移（`python -B tools/check_dsh.py`）。开发实测环境：Windows DSH NEXT `2.0.22-next`、core `0.2.2-rc.1`、Node `24.21.0`、Python `3.12.14`、Pillow `12.3.0`。另 2026-11-15 对 DSH `rc.1` 宿主依赖树的 `npm audit` 曾报 7 项高危（含 `zod`），`rc.2`/`rc.3` 为 0 项。
- **打包构建方式**：`tools/package_dsh.py` 复用 `skill-content/`、`src/`、`recipes/` 与示例目录权威输入（哈希记入 `skill-manifest.json`，版权与出处见 `LICENSE`/`NOTICE.md`）。本项目非 DeepSeek 官方插件。

```sh
python -B tools/package_dsh.py --out dist/dsh-package
npm pack ./dist/dsh-package --ignore-scripts --pack-destination dist
```

</details>
