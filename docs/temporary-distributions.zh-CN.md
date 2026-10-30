# 临时GitHub分发与验收清理

仅供用户和当前Codex；不放外部任务包。用户已授权：为了千问领取任务临时上传，验收时删除远端临时包，保留本地证据。

## LT03-Linux（2026-10-29）

- 目标仓库：`Chenamel/deterministic-pixel-art`。
- 临时Release/tag：`tmp-lt03-rc6-20261029`，仅为任务分发，不是新Skill版本。
- 附件：`LT03-Linux.zip`；本地保留 `dist/linux-v1.2.0-rc.6-lt03/LT03-Linux.zip`。
- 已上传：Release ID `426977499`，附件ID `685775801`。无登录下载HTTP200、252,759字节，SHA-256 `49459473a96d9ab578997504dc72a721a5c18eb7a641a7322a92dc1c23cb34c5` 一致。详细审计在 `evaluation/linux-trial-20261029/publication.json`。
- 当前状态：**已验收并完成远端清理。** 2026-10-29删除Release426977499、附件685775801及同名tag；旧下载入口HTTP404，其余Release/附件及main/开发分支不变，最新稳定版v1.1.1。本地包和原始结果保留，详见 [LT03核验](lt03-results-20261029.zh-CN.md)；审计 `evaluation/lt03-results-20261029/cleanup.json`。不要重建临时发布或要求用户再次下载。
- **验收关闭条件：** 收到submission与可用过程记录，原样留档，完成独立核验；如需补交，先完成补交。不要在千问仍需下载、结果待补交时删除。
- **关闭动作：** 只删除这个临时Release、其附件和同名tag；不删除正式Release、开发分支或本地ZIP/原始结果。记录清理时间，并确认下载链接已失效、正式版本未变。

历史清理命令（已执行，不要重复）：

```text
gh release delete tmp-lt03-rc6-20261029 --repo Chenamel/deterministic-pixel-art --cleanup-tag --yes
```

清理责任随 `RESUME_HERE.zh-CN.md` / `WORK_STATE.md` 一起接续，不依赖提醒自动化。
