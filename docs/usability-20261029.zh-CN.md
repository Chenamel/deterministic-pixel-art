# LT03 后的易用性改进

2026-10-29。本轮由用户授权实施两项小改，已完成本地验证。稳定安装仍为 v1.1.1，冻结 rc.6 及历史外测证据保持原样；没有新 tag、Release 或外部任务包。

## 现在怎样用

在启动工具的同一个任务 shell 设置一次，后续主命令和绘图配方继承便携输出选择：

```powershell
$env:PIXELART_PORTABLE_OUTPUT = '1'
python src/pixel_art.py render --spec examples/gem-16.json --out output/task/gem.png
python recipes/icons.py --out-dir output/task/icons
```

Linux/macOS shell 使用 `export PIXELART_PORTABLE_OUTPUT=1`。不同 Agent 的独立 shell 调用不一定共享环境，需由启动器传入同一个设置；没有新增项目配置文件或用户全局配置。

优先级：单条命令的 `--portable-output` / `--no-portable-output` → 环境变量 → 原有默认。不设置或 `0` 沿用默认；其他值在写入前报错，可以用显式选项覆盖。PowerShell 用 `Remove-Item Env:PIXELART_PORTABLE_OUTPUT` 取消，POSIX shell 用 `unset PIXELART_PORTABLE_OUTPUT`。

便携方式仍拒绝覆盖，既有文件需要有意使用 `--force`。新文件写入期间可被读取者看见，默认方式不会自动降级。只读命令与 Python `publish` 默认行为不读取该设置。

环境恢复只在需要时读取 [工作流指南](../skill-content/references/workflows.md#environment-and-output-recovery)：挂载拒绝符号链接时将 venv 放在本地临时盘；缺 `ensurepip` 时使用 `venv --without-pip`，通过现有 pip 的 `--python` 安装到目标环境，并核对实际解释器及 Pillow 路径。没有可用 pip 时明确报告缺少的前提。

## 本轮验证

| 项目 | 结果 |
|---|---|
| 源码测试 | 131 项通过，含新增 7 组输出选择回归 |
| 独立解压包 | 中文及空格工作目录、清除 PYTHONPATH，106 项通过 |
| 官方 Skill 校验 | 通过；源码及指导源与生成分发目录一致 |
| 像素兼容 | 43 张稳定资产逐像素一致，原历史夹具完整 |
| 输出语义 | 全部 8 类写入命令、配方继承、显式覆盖、错误设置、拒绝覆盖、并发与失败回滚通过 |
| 环境恢复 | 新建无 pip 环境，外部 pip 安装 Pillow 12.3.0，使用目标解释器实际绘图通过 |
| 保护与打包 | 357 个保护文件哈希不变；重复打包字节一致 |

当前本地环境为 Windows / Python 3.14.2 / Pillow 12.3.0。硬链接失败采用受控注入；本轮没有真实 Linux/FUSE 或实际缺失 ensurepip 的环境复测。测试器原 60 秒总限时中断了一次，延至 180 秒后完整 131 项用时 74.381 秒通过；没有降低断言或跳过用例。

## 收益与成本

一个进程设置可代替后续每条命令重复选项；实际 Agent 的用时、token 和失误率改善仍待使用记录，不把这一机制等同于已测得创作收益。

开发 ZIP 为 237,664 字节，比冻结 rc.6 多 1,080 字节（0.46%），仍为 98 文件，未增加运行依赖。它是未编号的开发产物，不替换冻结候选；源码版本字符串也不代表已发布新候选。

相同图及三个输出，前后交错各 12 次完整命令的本机中位耗时：修改前默认 243.2ms、修改后默认 253.5ms、修改后进程便携 263.3ms。分别观察到约 +10.3ms / +20.1ms，包含启动和磁盘操作，样本区间重叠；未显示提速，也不足以判定稳定的性能退步。输出 PNG/预览/布局字节均相同。本轮没有修改绘制算法或声称画质提升。

[机器摘要](measurements/usability-20261029.json) 保存完整数值；原始测试、安装记录、修改前快照和保护清单保存在忽略的 `evaluation/usability-20261029/`，不进入 Skill 上下文。

## 当前位置与下一步

共四个主阶段：P1–P3、P4a 已完成，P4b 原生512暂缓。当前是候选外部验收后的易用性小批次，已完成。下一步准备 LT04 实际创作任务及最少操作说明，继续按额度手动推进；本轮尚未制作或发送。新候选、正式发布和本地安装更新仍按已有门槛单独处理。
