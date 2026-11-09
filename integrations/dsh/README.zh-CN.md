# 在 DSH 中使用 Deterministic Pixel Art

[English](README.md)

这是本项目的可选第三方 DSH bundle，携带原 `deterministic-pixel-art` Skill、
说明、Python 工具、配方和可编辑示例。用户与模型都可按需调用；同名本地 Skill
可以优先使用。目前未发布到 npm，也未收录于 DSH 市场。

## 生成本地包

在源码仓库安装 Python 和开发依赖后运行：

```sh
python -B tools/package_dsh.py --out dist/dsh-package
npm pack ./dist/dsh-package --ignore-scripts --pack-destination dist
```

生成目录必须不存在。包没有安装脚本。首版限定 DSH core **0.2.2-rc.1**、Node
**>=24.9.0**；宿主需提供 DSH Skill **0.2.2-rc.1** 和 Cordis **~4.1.0**。
其他 DSH 版本未声明兼容。

## 用新配置试跑命令行

在 DSH NEXT 的 **DSH Terminal** 中运行 `dsh`，选择未使用过的 profile 名称；
以下用 `pixel-art`。**先初始化一次，再安装插件**：`--from-default-profile`
会替换目标 profile，包括其中的插件和本地配置。以后启动任务不要重复初始化。

```text
dsh --profile pixel-art --from-default-profile headless --help
dsh plugin --profile pixel-art add "/absolute/path/to/dsh-skill-deterministic-pixel-art-0.1.0.tgz"
```

将归档路径替换为前面实际生成的文件；含空格路径保留引号。第一条命令初始化配置，
不调用模型。这些命令只作用于 `pixel-art`，不会把插件安装到 Desktop profile。

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

## 验证与发布状态

本机验证基线为 Windows DSH NEXT **2.0.22-next**、core **0.2.2-rc.1**、Node
**24.21.0**、Python **3.12.14**、Pillow **12.3.0**。
`python -B tools/check_dsh.py` 需要 Node/npm 和开发依赖，检查实际归档、真实
Skill 服务与搬移后的绘图工具，不需要模型调用。

`tools/package_dsh.py` 复用 `skill-content/`、`src/`、`recipes/` 与原示例目录的
权威输入；不手工维护生成资源，不建立第二套绘制引擎。`skill-manifest.json`
记录文件哈希。DSH 与宿主 peer 不随包分发；许可和来源见 LICENSE、NOTICE.md。

公开安装仍需确认 npm 名称、版本与账号所有权，发布已审归档，再单独提交市场。
本项目不是 DeepSeek 官方插件。也可以按原仓库的
[INSTALL.md](https://github.com/Chenamel/deterministic-pixel-art/blob/main/INSTALL.md)
直接安装原生 Skill。
