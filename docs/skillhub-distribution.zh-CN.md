# 从完整 Skill 生成 SkillHub 包

SkillHub 要求 SKILL.md 含 `slug`、`version`、`displayName`；通用 Skill 保留自己的 name、description 与 license。使用平台适配包共用运行时和指南，避免维护第二份产品内容。

先按项目流程生成并核验完整 `skill/deterministic-pixel-art`，提交选定的产品内容，再运行：

```sh
python tools/package_skillhub.py --out dist/skillhub-v1.2.2
```

默认要求已跟踪内容没有未提交改动，并逐文件核对完整 Skill 与 HEAD 的字节，防止未跟踪或被忽略的额外文件混入来源记录；Skill 目录以外的未跟踪本地笔记不影响打包。从无 Git 的已核对快照打包时，可用 `--source-commit` 提供对应的完整提交 SHA。脚本不会将手动提供的 SHA 与远端内容作独立认证，仍应核对实际输入的文件清单。

工具拒绝已有输出目录及不含运行时的 skill-content/，生成根目录式 ZIP、逐文件清单和 SHA256SUMS.txt。版号取自打包运行时；只增加平台 frontmatter 和 DISTRIBUTION.json，其余文件保持通用包原字节。脚本不登录、不请求 Token、不上传；通用包与现有安装均不替换。

上传时使用专用 ZIP。图标可取包内 assets/brand/pixel-anchor-128.png；官方说明指出 CLI 不自动上传头像，平台头像需按实际页面另选。公开版号、slug 可用性、账号实名及平台审核由实际发布流程确认。官方教程的 CLI 安装方式为 Mac/Linux，Windows 使用 WSL；一次性上传可用网页。

官方 CLI 的 publish --dry-run 只验证元数据，不等于验证全部文件或实际运行。候选仍需检查清单、许可、根目录、解压执行和对应源提交。平台登录后网页的上传限制不能由本地 CLI 的限制代替。

来源：[发布教程](https://skillhub.cn/tutorials#publish-via-cli) · [发布字段说明](https://skillhub.cn/ai/release.md)。
