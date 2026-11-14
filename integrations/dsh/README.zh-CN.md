# 在 DSH 中使用 Deterministic Pixel Art

[English](README.md)

这是本项目的可选第三方 DSH bundle，携带原 `deterministic-pixel-art` Skill、
说明、Python 工具、配方和可编辑示例。用户与模型都可按需调用；同名本地 Skill
可以优先使用。

## 已安装：直接开始对话

在已安装并启用插件的同一个 DSH 配置中开启对话，发送：

> 请使用 deterministic-pixel-art，制作一个 16×16、透明背景的像素提灯。先读取这个 Skill 并检查可用的 Python/Pillow 环境。交付 PNG、可继续修改的 JSON，以及 8 倍最近邻预览；完成后看图检查。

拿到图片后可以继续说：

> 只把提灯的金属边框改成深棕色，玻璃和其他部分保持原样。保留初版，另交修改后的 PNG 和源文件。

也可以提供已有 PNG，指出要修改的区域、保留的部分及目标效果。不必先学习命令
或 JSON；需要特定游戏风格时，提供参考图或明确要求。

应收到原尺寸 PNG 和可编辑源文件。只有放大预览图还不够；桌面可直接交付文件，
仅命令行环境则应返回文件的绝对路径。

## 安装与兼容版本

| 名称 | 用途 |
| --- | --- |
| Deterministic Pixel Art | 展示名称 |
| `dsh-skill-deterministic-pixel-art` | npm 安装包名 |
| `deterministic-pixel-art` | 对话中使用的 Skill 名称 |

本目录对应 bundle **0.1.2-rc.1**，支持 DSH core 与 DSH Skill
**0.2.2-rc.1 至 0.2.2-rc.3**。Node 要求 **>=24.9.0**，Cordis 为
**~4.1.0**；绘图需要 Python **3.10+**、Pillow **>=10.4,<13**。
更早版本、未来 rc 及正式版不在兼容声明内。桌面应用版本与内核版本不同，可用
该安装的 `dsh --version` 核对内核。

通过 DSH 支持的 npm 插件安装入口，将包装入实际用于聊天的配置并启用。
已有正常配置的 CLI 用户，可将 `YOUR-PROFILE` 换成自己的非 `desktop` profile：

```text
dsh plugin --profile YOUR-PROFILE add dsh-skill-deterministic-pixel-art@0.1.2-rc.1
```

若 registry 尚无 0.1.2-rc.1，说明该版本尚未发布；本地候选按文末的
[打包说明](#生成本地包)生成，不要将仅声明 rc.1 的旧 0.1.0 当作新版替代。
npm CLI 不管理 Electron 专用的 `desktop` profile；桌面使用其自身的插件入口
或内置命令。npm 安装无需等待市场收录。

## 可选：新建命令行配置

已有可用配置可以跳过本节。使用官方 DSH CLI，或在 DSH NEXT 的
**DSH Terminal** 中运行 `dsh`，选择未使用过的 profile 名称；
以下用 `pixel-art`。**先初始化一次，再安装插件**：`--from-default-profile`
会替换目标 profile，包括其中的插件和本地配置。以后启动任务不要重复初始化。

```text
dsh --profile pixel-art --from-default-profile headless --help
```

这条命令初始化配置，不调用模型。随后**选择一种**安装方式。官方 npm registry
提供 **0.1.2-rc.1** 时，使用精确包版本：

```text
dsh plugin --profile pixel-art add dsh-skill-deterministic-pixel-art@0.1.2-rc.1
```

本地候选按文末说明生成归档，改用其绝对路径；含空格路径保留引号：

```text
dsh plugin --profile pixel-art add "/absolute/path/to/dsh-skill-deterministic-pixel-art-0.1.2-rc.1.tgz"
```

两种方式都安装到 `pixel-art`；Desktop 使用独立的 profile。
npm 安装无需等待 DSH 市场收录。

官方 `headless` 模板默认关闭托管账户服务。若使用平时登录的 DeepSeek 账户，在
任务目录保存以下 `dsh-account.patch.yml`；它只含配置，不填 token：

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

通过 DSH 的正常账户界面登录，并确保使用同一 `DSH_HOME`；不要复制凭据到此文件。
在希望保存 JSON 和 PNG 的任务目录启动新任务：

```text
dsh --profile pixel-art --patch ./dsh-account.patch.yml --json --permission-mode workspace-write --approval-policy never "用 deterministic-pixel-art 画一个16×16灯笼PNG，保留可编辑JSON。"
```

`--json` 输出运行事件，其中包括新的 `sessionId`。继续会话时保持同一工作目录，
将示例 ID 换成返回的真实 ID：

```text
dsh --profile pixel-art --patch ./dsh-account.patch.yml --json --permission-mode workspace-write --approval-policy never --session-id session-YOUR-ID "把轮廓改深一点。"
```

命令选择 `workspace-write` 模式，实际隔离程度取决于 DSH 与平台；`never` 关闭
交互审批，需要审批的操作会失败。模型任务可能消耗账户余额，上述命令没有设置
金额上限。若已用 API key 或
其他配置好的 profile，保留其模型设置，将插件装入该 profile 即可，不必套用账户
overlay。

## 使用与排错

工具需要 Python **3.10+**、Pillow **>=10.4,<13**；固定复现基线为 Pillow
**12.3.0**。有 `load_workspace_dependencies` 时用它选择环境；没有时通过可用
shell 检查 Python 和 Pillow。缺少它们属于运行前置条件，安装 bundle 不会自动
运行 pip。按 Skill 的资源目录解析脚本与 references，源文件和 PNG 保存在任务
目录。

有 `present` 时用它交付文件。默认 headless 应提供输出文件的绝对路径；`read_image`
可供模型检查；看图调用不能证明已经向用户交付。桌面 profile 可以有额外工具。
加载 Skill 本身不会生成或展示 PNG。

找不到 Skill 时，先确认当前 profile 与安装时一致。
`dsh --profile pixel-art --dump-config` 应包含 `deterministic-pixel-art-skill`。
加载报缺宿主 peer 或版本不兼容时，先解决运行环境。`ACCOUNT_SIGN_IN_REQUIRED`
表示账户路线不可用，应检查 overlay、正常登录和 `DSH_HOME`，不必重装 Skill。
同名本地 Skill 会覆盖随包版本。

Windows 若出现 `sandbox-local: windows-acl workspace grant failed`，shell 命令
可能在 Python 启动前就被阻止。可保持 `workspace-write`，先将任务副本放到用户
目录下、当前账户具有完全控制权限的独立文件夹再试。若仍失败，使用 DSH 的沙箱
诊断；重装本 bundle 无法修复宿主目录权限。

## 验证与来源

本机验证基线为 Windows DSH NEXT **2.0.22-next**、core **0.2.2-rc.1**、Node
**24.21.0**、Python **3.12.14**、Pillow **12.3.0**。
`python -B tools/check_dsh.py` 需要 Node/npm 和开发依赖，检查实际归档、真实
Skill 服务与搬移后的绘图工具，不需要模型调用。
CI 在 Windows 和 Ubuntu 分别用 `--skill-version` 检查三版配套服务。

`tools/package_dsh.py` 复用 `skill-content/`、`src/`、`recipes/` 与原示例目录的
权威输入；不手工维护生成资源，不建立第二套绘制引擎。`skill-manifest.json`
记录文件哈希。DSH 与宿主 peer 不随包分发；许可和来源见 LICENSE、NOTICE.md。

本项目不是 DeepSeek 官方插件。也可以按原仓库的
[INSTALL.md](https://github.com/Chenamel/deterministic-pixel-art/blob/main/INSTALL.md)
直接安装原生 Skill。

## 生成本地包

仅源码开发或本地候选验收需要本节。在源码仓库安装 Python 和开发依赖后运行：

```sh
python -B tools/package_dsh.py --out dist/dsh-package
npm pack ./dist/dsh-package --ignore-scripts --pack-destination dist
```

生成目录必须不存在。包没有安装脚本；通常使用者直接安装 npm 包即可。
