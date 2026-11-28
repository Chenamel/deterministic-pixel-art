# SkillHub 分发

完整 Skill 包含图片素材、Python 工具和 MIT 许可文件。SkillHub CLI 2026.8.5 的发布接口会把目录文件作为上传包；该平台拒绝无后缀 `LICENSE`，网页端也禁止图片等二进制文件。因此，不能把删掉这些内容后的目录当成完整 Skill 上传。

SkillHub 可使用一个文本安装入口：入口包只包含 `SKILL.md` 和 `install.py`，明确要求联网，并从 GitHub v1.4.1 稳定发行下载完整 ZIP。安装脚本会核对固定 SHA-256、检查 ZIP 路径和文件上限，再解压到用户指定且尚不存在的目录。它不会覆盖已有安装，也不自动安装 Python 依赖。

网页发布表单允许单独上传 JPG、PNG 或 WebP 图标，截图所示上限为 5 MB。随包 CLI 的 `publish` 元数据与 multipart 文件上传没有图标字段；CLI 中的图片上传函数用于评论。需要 Skill 图标时，在网页表单中单独添加。可用图标为 `skill/deterministic-pixel-art/assets/brand/pixel-anchor-128.png`。

## 完整包

先按项目流程生成并核验完整 `skill/deterministic-pixel-art`，提交选定的产品内容，再运行：

```sh
python tools/package_skillhub.py --out dist/skillhub-v1.4.1
```

该工具要求已跟踪内容无未提交改动，并逐文件核对完整 Skill 与 HEAD 的字节，避免未跟踪或被忽略的额外文件混入来源记录；Skill 目录以外的本地笔记不影响打包。从无 Git 的已核对快照打包时，可用 `--source-commit` 提供完整提交 SHA。脚本不会将手动提供的 SHA 与远端内容作独立认证，仍应核对实际输入的文件清单。

工具拒绝已有输出目录及不含运行时的 `skill-content/`，生成根目录式 ZIP、逐文件清单和 `SHA256SUMS.txt`。版号取自打包运行时；只增加平台 frontmatter 和 `DISTRIBUTION.json`，其余文件保持通用包原字节。脚本不登录、不请求 Token、不上传，也不替换通用包或现有安装。完整包适用于离线分发，或平台允许所有文件类型时。

## 在线安装入口

生成只含文本的 SkillHub 上传 ZIP：

```sh
python tools/package_skillhub_installer.py --out dist/deterministic-pixel-art-skillhub-v1.4.1.zip
```

先运行 `skillhub publish <zip> --dry-run` 检查平台元数据，再发布入口 ZIP。CLI dry-run 只验证元数据，不代表实际发布或安装流程已通过。入口不是完整离线 Skill；它要求联网，从 GitHub v1.4.1 稳定发行下载完整包，并固定校验 SHA-256。新版发布时，先完成 GitHub 稳定版发布，再更新入口中的版本、下载地址、摘要和说明。

源码与测试位于 `integrations/skillhub-installer/` 和 `tests/test_skillhub_installer.py`。安装器要求 Python 3.10+，不会替换已有目录，也不会自动安装 `requirements.txt` 中的依赖。

发布前仍须确认账号权限、slug 可用性和平台审核结果。官方教程：[通过 CLI 发布](https://skillhub.cn/tutorials#publish-via-cli) · [发布字段说明](https://skillhub.cn/ai/release.md)。
