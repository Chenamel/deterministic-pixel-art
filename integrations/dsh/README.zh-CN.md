# 在 DSH 中使用 Deterministic Pixel Art

[English](README.md)

这是本项目的可选第三方 DSH bundle，携带原 `deterministic-pixel-art` Skill、
说明、Python 工具、配方和可编辑示例。用户与模型都可按需调用；同名本地 Skill
可以优先使用。它不是 DeepSeek 官方插件，目前未发布到 npm，也未收录于 DSH 市场。

## 本地试装

在源码仓库安装开发依赖后，生成本地包：

```sh
python -B tools/package_dsh.py --out dist/dsh-package
npm pack ./dist/dsh-package --ignore-scripts --pack-destination dist
```

在 DSH NEXT 的 **DSH Terminal** 中，用新的试用 profile 安装实际生成的 tgz。
含空格路径要加引号，例如：

```text
dsh plugin --profile pixel-art add "C:/my packages/dsh-skill-deterministic-pixel-art-0.1.0.tgz"
```

这会创建或修改指定 profile。生成目录必须不存在，打包工具不会覆盖已有目录。
包没有安装脚本。首版限定 DSH core **0.2.2-rc.1**、Node **>=24.9.0**；宿主需提供
`@deepseek-ai/dsh-skill` **0.2.2-rc.1** 和 Cordis **~4.1.0**。本机验收基线为
Windows DSH NEXT **2.0.22-next**，内含 Node **24.21.0**、Python **3.12.14**、
Pillow **12.3.0**；其他 DSH 版本未声明兼容。

## 调用与排错

向安装了此包的 profile 提出任务，例如：“用 deterministic-pixel-art 制作一个
16×16 PNG 图标，保留可编辑 JSON，并展示图片。”

工具需要 Python 3.10+、Pillow >=10.4,<13。让 DSH 调用
`load_workspace_dependencies` 选择已有环境；固定复现基线为 Pillow 12.3.0。
脚本和 references 路径按 Skill 返回的资源目录解析；输入、JSON 与 PNG 放在任务
工作区，完成后调用 `present` 交付文件。缺 Python 或 Pillow 时先在工作区解决运行
依赖，安装 bundle 不会自动运行 pip。

找不到 Skill 时，先确认当前使用的 profile 与安装时一致。执行
`dsh --profile pixel-art --dump-config`，应能看到 `deterministic-pixel-art-skill`。
若加载报缺宿主 peer 或 DSH 版本不兼容，先修复该运行环境；同名本地 Skill 会覆盖
随包版本。目录中出现 Skill 不代表已执行绘图，仍需运行脚本并检查实际 PNG。

## 来源与发布状态

资源由 `tools/package_dsh.py` 复用既有 Skill 打包映射生成，权威输入仍在
`skill-content/`、`src/`、`recipes/` 与原示例目录。`skill-manifest.json` 记录逐文件
SHA-256；不维护第二套绘制引擎。许可与来源见 LICENSE、NOTICE.md。

独立验收入口为 `python -B tools/check_dsh.py`，需要 Node/npm 和开发依赖。
公开一键安装还需要确认 npm 名称与版本所有权、发布已审阅的归档，并另行提交市场
目录；本轮没有完成这些操作。也可以按原仓库的
[INSTALL.md](https://github.com/Chenamel/deterministic-pixel-art/blob/main/INSTALL.md)
直接安装原生 Skill。
