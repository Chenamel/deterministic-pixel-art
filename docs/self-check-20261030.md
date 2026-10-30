# v1.2.0正式编号准备：本轮自查

本轮范围：基线644be6f之后的正式版本准备。下方“上一轮交付自查快照”保留其当时统计，不代替本轮结果。新增变动是版本常量、生成副本和发布说明；不改渲染逻辑、API、JSON v1、配方或Skill指导。

## 1. 链接与文件引用

本轮重新遍历docs/、skill-content/和两份README：源文件144个，审计输出2个另查。明确相对链接**共检查361个，失效0**（源358、审计输出3）；扩展源文件引用1379个：存在807、同文档片段1、失效0、**未验证571**（缺上下文489、模板8、当前未生成/未找到的输出74）。逐项文件:行号见[本轮引用明细](self-check-references-20261030.md)。本地忽略目录引用94个单列；外部URL60项未逐站访问。审计输出中的来源清单不递归计数，输出本身的明确链接另行检查。

## 2. 双语结构

README的7节标题翻译对应；代码块命令差异0、表格数据行数差异0。新增版本说明5节标题按顺序对应，代码块1/1且相同，各节均无表格。结构性遗漏0。此结论为结构与代理语义对照，不是逐字翻译质量评分。

| 英文版本说明标题 | 中文版本说明标题 | 代码块数（英/中） | 表格数据行数（英/中） |
|---|---|---|---|
| v1.2.0 — editable pixels and scoped workflows | v1.2.0 — 可编辑像素与精确修改工作流 | 0/0 | []/[] |
| Changes since v1.1.1 | 相对 v1.1.1 的变化 | 0/0 | []/[] |
| Compatibility and setup | 兼容性与运行 | 1/1，命令相同 | []/[] |
| Evidence and limits | 依据与边界 | 0/0 | []/[] |
| Distribution | 分发内容 | 0/0 | []/[] |

README逐节标题和代码块/表格清单仍见下方历史对照表，标题与节数本轮未改。其他历史文档不要求全量双语对应，未验证。

## 3. Skill引用一致性

维护源与生成Skill的references目录各11份Markdown，入口直接引用全部11份；缺失0、未引用0、递归不可达0。最终编号打包后复查，当前指导文件本身不变。可达性不证明教学有效性。

## 4. 本次模块与测试覆盖缺口

- src/pixelart/__init__.py只修改版本常量；tests/test_analysis.py、test_workflows.py等经公共API覆盖函数调用，tools/test_skill.py在独立解压环境读取版本并运行入口。本轮额外检查正式包版本等于1.2.0，且98文件中只有该版本模块发生变化。
- 生成模块skill/deterministic-pixel-art/scripts/pixelart/__init__.py由打包器复制，使用逐文件摘要和实际入口覆盖，不重复维护镜像单测。
- README、CHANGELOG、版本说明、发布条件及恢复记录属于文档修改，用链接/双语结构/实际命令验证，不为可逆文案增加镜像测试。
- 不新增功能或修改测试断言；本轮编号内容重跑165源码测试、106整包检查、43稳定图、重复打包及官方校验通过。行/分支覆盖率未验证。

## 5. 未做事项与未验证项

- 正式公开发布、main合并、tag/Release和本地Skill更新不在本轮准备交付内；稳定v1.1.1与旧候选保持。
- 不补造32次受控比较或普遍画质、耗时、token收益；外测原失败与过程限制保留。
- 缺少上下文、模板及未生成输出仍逐条标记未验证，不上传私有材料消除告警；外部URL逐站可达性、所有章节锚点、自然语言隐含引用未验证。
- 游戏内集成、任意字体、原生512、多代理协作不在本轮范围，未验证。

## 写入报告后的检查

本轮报告先写入，再从637文件干净中文空格副本完整运行tools/check.py：165源码测试、106整包场景、43稳定图、86历史夹具与两次一致打包通过，流水线206.683秒；官方格式校验另行通过。正式编号ZIP为238,390字节、98文件，SHA-256为532d8a61cf4c0eba6966c7dccaf99a7e7af2632aab9e7435c54317cba02ff19e。相对184e2c6e旧开发包，97文件字节不变，唯一差异为版本模块中的常量；不是新一次行为或画质优化。

精确提交CI在提交后核对，结果以该提交检查页面、本地检查点和随包verification.json绑定记录为准，未出炉前为**未验证**。执行记录汇入[正式版本准备记录](releases/v1.2.0-preparation.zh-CN.md)及本地evaluation/release-v1.2.0-preparation-20261030/，不借用644be6f的基线CI冒充本轮结果。后续仅文档收尾不改已检查的运行时/测试/Skill。

共4主阶段：P1–P3/P4a完成，P4b512暂缓；当前位置正式版本准备，下一步完成最终编号检查与可审阅提交。

---

# 上一轮交付自查快照


2026-10-30（北京时间）。审阅基线为开发分支 HEAD 91a63189a47331c15e529dc7fc1f703fc6afa087 及其全部待交付工作树改动，不只检查这次新增工具。目的为工具可用性验收，不改写LT04失败或LT08过程限制。

## 1. 链接与文件引用

遍历 docs/、skill-content/、README.md、README.zh-CN.md 的全部文件：源清单141个，另有2个审计输出文件单独检查，文本按Markdown链接/引用定义、HTML href/src、可识别文件名和反引号目录扫描；二进制图片记录在清单但没有文本链接可解析。审计报告与附录属于输出，避免把输出中的引用清单再次递归计数；它们的明确链接另外检查。

**明确的相对链接共检查 354 个，失效 0：源文件353个，两个审计输出文件另1个。** 范围含1个同文档章节链接；这里只验证文件存在，所有章节名对应的锚点是否有效为**未验证**。诊断清单中的来源路径是源清单的镜像，不递归重复计数。

扩展源文件的裸文件名/目录/代码块和JSON里的文件引用，共检查 1339 个相对候选：存在 797 个、同文档片段 1 个、可定位失效 0 个，另有 541 个**未验证**。具体构成为缺上下文 465、模板 8、当前目录下未生成或未找到的输出/本地证据 68。不能把这 541 项写成“已确认有效”，也不能把示例输出不存在都判作产品缺陷。

失效清单：明确链接及可定位文件引用未发现失效。未验证与本地忽略证据的**逐项文件:行号清单**见[引用明细](self-check-references-20261030.md)。成功项及各次尝试路径保存在本地 evaluation/delivery-self-check-20261030/reference-inventory.json。

解析依据：Skill指导源的资源链接按打包后的同目录解析；metrics/first-pass-metrics里的旧模组路径按baselines/manifest.json声明的历史根解析；LT06的src/gen_chest.py明确指返回包RUN内源码，当前证据副本存在。不修改历史测量JSON。仅凭裸同名文件不能猜测目标；这类保留未验证。

外部URL另记录 60 项，本轮不做逐站可达性检测；本机绝对路径不算可移植相对链接。自然语言中不含可识别路径的暗示性文件引用为**未验证**。本地存在不代表GitHub克隆后可得，附录单列位于忽略目录的 94 项（包括output目录中的4项）。

额外区分了本地与仓库分发：发现以下10处Markdown下载样式链接指向未跟踪的历史ZIP，文件本地存在，但干净克隆不含它们。已改为明确标注“不随仓库分发”的本地归档位置，保留包与历史摘要，不上传原始材料、不重建临时发布。位置为修正后的同一行。

| 文件:行号 | 历史包 |
|---|---|
| docs/guidance-lt07-preparation.zh-CN.md:19 | LT07-Minecraft.zip |
| docs/lt04-correction-20261029.zh-CN.md:43 | LT04-review.zip |
| docs/lt04-preparation.zh-CN.md:11 | LT04-Icons.zip |
| docs/lt04-results-20261029.zh-CN.md:13 | LT04-Icons.zip |
| docs/lt05-preparation.zh-CN.md:9 | LT05-Sprite.zip |
| docs/lt05-results-20261030.zh-CN.md:11 | LT05-Sprite.zip |
| docs/lt06-preparation.zh-CN.md:9 | LT06-Materials.zip |
| docs/lt06-results-20261030.zh-CN.md:9 | LT06-Materials.zip |
| docs/lt07-results-20261030.zh-CN.md:11 | LT07-Minecraft.zip |
| docs/lt08-preparation.zh-CN.md:9 | LT08-Chunks.zip |

## 2. README双语结构

英文/中文均 7 节，按顺序核对标题含义与级别。标题文字是译名差异，没有缺节；所有代码块内容逐行相同，表格数据行数相同。本文不是逐字翻译质量评分。

| 英文标题（行） | 中文标题（行） | 代码块数（英/中） | 表格数据行数（英/中） |
|---|---|---|---|
| Deterministic Pixel Art（1） | 确定性像素资产（1） | 0/0，命令相同 | []/[] |
| Quick start（11） | 快速上手（11） | 2/2，命令相同 | []/[] |
| Choose a workflow（30） | 按任务选入口（30） | 3/3，命令相同 | [7]/[7] |
| Install as a Skill（69） | 安装 Skill（69） | 0/0，命令相同 | []/[] |
| Evidence and limits（75） | 实测依据与边界（75） | 0/0，命令相同 | []/[] |
| Development（84） | 开发检查（84） | 1/1，命令相同 | []/[] |
| License（95） | 协议（95） | 0/0，命令相同 | []/[] |

结构性遗漏清单：0。代码块命令差异：0。表格数据行数差异：0。行内环境设置文字由人工/代理对照，PowerShell/POSIX、便携选项和版本状态含义对应；其他文档的全量双语对应未验证。

## 3. SKILL引用一致性

skill-content/SKILL.md和生成的skill/deterministic-pixel-art/SKILL.md分别构建引用图：references目录均11份Markdown，入口均直接引用全部11份。缺失0；存在但入口未引用0；递归不可达0。文件清单：chunking、consumer-ui、formats、minecraft、pixel-art、recipes、review、sources、text-workflow、ui、workflows（均为.md）。

这证明文件可达，不证明每条指导必要、有效或能提高模型创作质量。其他未声明的模型运行时自动发现机制为未验证。

## 4. 测试覆盖缺口

下表为静态导入/测试调用与真实命令依据，不是行覆盖率或分支覆盖率；未运行覆盖率插桩，不提供百分比。完整干净副本补出了原覆盖盲点：三组测试依赖本机ZIP，修复后已完整重跑通过；随后CI暴露的Windows测试路径问题另见末节。tests/列省略统一目录前缀。

| 触及模块/文档 | 现有覆盖 | 缺口及处置 |
|---|---|---|
| src/pixelart/output.py | test_output_selection.py；test_reliability.py；test_workflows.py | 默认/进程选择、明确覆盖、错误设置、并发、拒绝覆盖和回滚；未测任意第三方文件系统的掉电行为 |
| src/pixelart/cli.py | test_output_selection.py；test_cli.py；test_workflows.py；test_analysis.py | 8种写入入口继承设置、只读不受设置影响及命令行为；整包另覆盖分发版本 |
| recipes/_common.py | test_output_selection.py；test_recipes.py | 子进程继承/单次覆盖、配方像素契约；没有为薄参数转发再造逐行镜像测试 |
| skill/.../scripts/pixelart/{cli,output}.py；skill/.../scripts/recipes/_common.py | 源模块测试＋tools/test_skill.py独立包 | 生成副本不重复维护单元测试；校验源码/副本/ZIP一致，并执行CLI/API；不是自动发现模型能力测试 |
| tools/test_skill.py；tools/validate_skill.py | test_packaging.py；test_reliability.py | 有效章节链接、缺文件拒绝、同文档片段、虚拟环境解释器路径；完整包检查覆盖整体编排，未单独模拟每种子进程故障 |
| tools/evaluate.py | tests/无直接测试；完整tools/check.py调用 | 评估编排器以真实端到端运行为依据，不写重复自身实现的包装测试；本次Windows/Ubuntu完整CI通过，任意机器性能与超时适用性未验证 |
| tools/audit_trial_history.py | test_trial_history.py | 命令内/间删除重建、源码替换、非法快照和只读磁盘审计 |
| tools/build_linux_trial.py；benchmarks/long-term/linux_runner.py | test_linux_trial.py | 真实解压入口、无损往返、输出/拒绝覆盖、包摘要与协调信息隔离；不是Linux/FUSE挂载模拟全覆盖 |
| tools/build_icon_trial.py；benchmarks/long-term/icons_runner.py | test_icon_trial.py | 图集/像素/布局工程约束及真实打包；图标语义靠图片审阅，不能由工程检查证明 |
| tools/build_icon_review.py | test_icon_review.py | 图片包成员、原图保留和需求隔离；不自动评判审美 |
| tools/build_sprite_trial.py；benchmarks/long-term/sprite_runner.py | test_sprite_trial.py | v1/v2规格、变化范围、图片和交付契约；不验证模型主观描述真伪 |
| tools/build_material_trial.py；benchmarks/long-term/material_runner.py | test_material_trial.py | 共同几何、命名单元、预览与包契约；材质辨识非自动分类 |
| tools/build_minecraft_trial.py；benchmarks/long-term/minecraft_runner.py | test_minecraft_trial.py | 组件/布局/组合/接缝及工程契约；游戏/UV/输入/GUI Scale未验证 |
| tools/build_chunk_trial.py；benchmarks/long-term/chunk_runner.py | test_chunk_trial.py | 四块、边界采样、组合、旗面差异和冻结交付；多代理协作与早期过程完整性未自动证明 |
| tools/self_check.py（本轮新增） | test_self_check.py（5项） | 打包相对资源、缺链接、URL不误识别、双语结构差异、孤立/缺失参考；自然语言隐含引用和任意Markdown语法未验证 |
| 新增/变更tests/test_*.py自身 | 完整unittest发现执行；无测试之测试 | 三组夹具改为临时构包；test_output_selection.py的故障注入/并发钩子与发布器统一解析路径，并清理已退出子进程的管道。保留断言和真实失败，不为测试代码再写相同逻辑 |
| skill-content/{SKILL.md,references/review.md,references/workflows.md}及生成副本 | test_packaging.py＋本报告图遍历＋独立ZIP | 格式/引用/随包完整性有检查；语义和行为改善没有因果覆盖，明确未验证 |
| README、docs、WORK_STATE及benchmarks/long-term任务md/json | 本报告链接/结构审计＋各任务test_*＋独立示例入口 | 文案不逐句写单测；旧阶段叙述保留时需看时间范围；完整历史语义一致性未验证 |

模块表依据原审阅基线91a6318以来的交付差异清单逐项核对；.migration本机迁移脚本不属于交付模块，不执行或提交。生成模块由源码与包一致性检查覆盖，tests不重复维护副本。

## 5. 未做事项与保留问题

- 541个上下文/模板/生成路径未当作已验证成功：完整逐项位置在附录，不靠搜索到同名文件来消除告警。
- 远程URL逐站检查、全部章节锚点、任意Markdown扩展语法及自然语言隐含引用：未验证；本轮提供明确可复跑的有限解析规则。
- 旧历史阶段文字、原始测量与外部过程缺证没有改写；本轮不修样图、不补造失败、早期草稿或A/B数据。旧临时LT03链接已按先前授权删除，不重建。
- 真实Minecraft运行、任意字体/中文排版、原生512、多代理协作和一般画质/耗时/token收益：未验证，不作为新功能扩展。
- 本地原始提交、完整会话、迁移记录、凭据与虚拟环境不上传；本地证据存在不等于公开分发。
- 当前同摘要Skill的外测材料按覆盖范围沿用；最终若有行为变更需补对应检查，不能将单版本任务回填受控收益。
- 正式版本号、main/tag/Release、本地稳定Skill更新尚未执行；本轮完成开发分支提交和对应CI，下一步才是最终编号与发布准备。

## 报告完成后的完整检查

**完整检查通过。** 本报告先写入，再在中文空格干净副本执行 `python -B tools/check.py`。首次运行165项测试中12项因材质、MC、分块测试依赖Git忽略的根ZIP而失败；已改成从仓库Skill在各自临时目录构建ZIP。没有复制本机根ZIP来绕过问题，首次日志保留在evaluation/delivery-self-check-20261030/initial-full-check/。

修正后完整重跑：165项源码测试通过（161.422秒），106项独立ZIP场景通过，43张稳定图一致，86份历史夹具保持；工作流/浏览器/分块演示构建、迁移、三项评估、两次一致打包和独立包入口全部完成。另调用官方Skill校验器通过。完整流水线耗时197.397秒，不代表模型创作耗时或收益。

重新生成的98文件ZIP与原开发包逐字节相同，SHA-256为184e2c6ef44a0a3f3ec755a2a8c8a450787ac1944ae3a5b412ca1896ddefc0c6。产品运行时、封存候选和稳定安装没有因测试夹具修正而变化。

远端首次CI（提交b5f3dff，run41030987831）失败：新自查工具对含`..`路径的存在性检查依赖平台对未规范化路径的处理，已有资源引用回归失败。在检查存在性前规范化候选路径后，5项针对性检查与完整流水线再次通过（202.578秒）。此修正不进入Skill包。

第二次CI（提交58486e4，run41031679670）四组Ubuntu成功、四组Windows失败。Windows日志均为同两项测试失败：输出发布器规范化路径，而故障注入/并发等待钩子比较未经解析的临时目录；日志显示RUNNER~1与runneradmin路径别名。已让两处钩子双方resolve，并确保子进程即使提前结束也关闭管道，不降低断言、不跳过用例。7项本地输出测试通过；本机没有可用的不同短路径别名，短路径故障的本地直接重现为**未验证**，需以新提交Windows CI检验。原始日志及此次本地重现尝试均保留。

测试钩子修正后，另建不含根ZIP/私有证据的634文件中文空格副本，从报告已写入的源码执行完整检查：165源码测试、106独立包场景、43稳定图及两次一致打包全部通过，完整流水线196.350秒；官方Skill校验器另行通过。此次仅改测试，不改产品运行时或ZIP。

**对应代码提交32e98a74d5c4cf3bb5ad6e585f16f28bb4f86499的[GitHub检查](https://github.com/Chenamel/deterministic-pixel-art/actions/runs/41033059467)已完成，8/8成功。** Windows与Ubuntu各执行一组Python3.14完整流水线，以及Python3.10/Pillow10.4、Python3.12/Pillow11.3、Python3.13/Pillow12.1的三组源码兼容检查。Windows路径钩子在四组真实CI环境中通过；本机缺短别名的限制仍如实保留。此次CI不是历史提交的结果。随后只收尾文档，运行时/测试/Skill与此提交一致；文档提交自身检查另以该提交GitHub状态与本地检查点为准，不借用这次CI的提交身份。

复跑引用清单：在仓库根运行以下命令，审计输出另行验证其明确链接，避免递归统计输出中的诊断列表。

```text
python -B tools/self_check.py --out evaluation/reference-inventory.json --exclude docs/self-check-20261030.md --exclude docs/self-check-references-20261030.md
```

原始证据目录：evaluation/delivery-self-check-20261030/。该目录不进入Skill上下文或公开原始材料。

共4主阶段：P1–P3/P4a完成，P4b原生512暂缓。当前位置交付自查及代码提交平台检查完成，下一步正式编号、最终包与版本说明准备。
