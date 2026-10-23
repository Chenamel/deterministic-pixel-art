# Resume this work here

Updated: 2026-10-24. Active branch: `codex/visual-quality`.

## 最新检查点：rc.4候选收口完成；下一项P1外部回收与发布门槛

2026-10-24，从干净的 `ebac2a0` 继续。P4a及8组CI已完成，不重复绘制。原生512目前没有确定的消费端、细节预算或必须跨块的大结构需求；仅增加画布不能证明创作/编辑收益。因此P4b绘制暂缓，不记为通过。以后出现256无法表达的具体构图、原生细节与局部编辑需求时，另冻结新合同再启动。

当前执行已批准的收口分支：将P3真实字体/状态组合与P4独立块/全局相位/单一所有权方法提炼成按需Skill指导，附最小可编辑分块例子；形成新的本地候选 `v1.2.0-rc.4`，保留rc.2/rc.3，不更新已安装v1.1.1。新例子用来演示方法，不冒充原生512、独立模型评测或游戏内验收。

本地收口已完成：2份按需指导、64×32双块最小例子、98源码测试/43稳定图/86独立ZIP、官方格式校验、10张外部旧图/布局、138保护文件均通过。视觉看过原尺寸/4倍/接缝，未需修正；旗帜24个RGBA变化、区外0，单块重拼和旧布局拒绝通过。新包97文件/230,474字节，SHA-256 `cb3472769754dbd9b5d56397e2620f6be12c253a8162a1642acd71225b4e69c1`，封存在 `dist/v1.2.0-rc.4/`。比rc.3增加7,490字节/3.359%，不宣称token或普遍画质收益。双语报告 `docs/candidate-closeout.zh-CN.md` / `.md`，机器记录 `docs/measurements/candidate-closeout.json`；原始检查 `evaluation/closeout-20261024/`。rc.2/rc.3哈希、已安装1.1.1已核对。

实现提交 `c0330223114288a0790a4af9c3f2019e0f5bbeb7` 已推送，[CI运行39985591333](https://github.com/Chenamel/deterministic-pixel-art/actions/runs/39985591333)8组全部成功：Windows/Ubuntu主流程及各自Pillow10.4/11.3/12.1兼容矩阵。逐组记录 `docs/measurements/candidate-closeout-ci.json`。不变代码/包无需重复整轮测试，后续仅文档/CI证据收尾。

下一动作：回收P1外部产物，按定向任务逐项判定修复/仍存在/环境阻断，再检查既有受控稳定发布门槛。P1仍为三个任务包已分发、新外部返回0，不等同通过；入口 `docs/focused-trials.zh-CN.md`。未收结果时不追加无依据功能，不自动发布稳定/更新本地安装。若用户提出明确的原生512交付/细节和局部编辑要求，再重开P4b冻结新合同。每次完成仍直接报告4主阶段状态、当前位置、下一项和外部等待，不新增第五功能阶段。

## 前一检查点：P4a独立256完成并通过CI（后续以上方为准）

用户新要求（2026-10-23）：每次阶段完成的直接回复必须包含 **总阶段与状态、当前位置、下一阶段**，不能只写进文件。主计划共4阶段：P1定向复测（分发完成，外部结果待回）；P2可读配方（完成）；P3真实消费端（完成）；P4独立分块（当前P4a：256；P4b：原生512条件试验，只有P4a过关且有实际收益才启动）。P4完成后是收口/外部验收与发布门槛检查，不自动增加功能阶段或升级稳定版。

P4起点 `2ac193a`，合同先在 `7506d55` 冻结，SHA-256 `f2bf1e01d6d466f83dbaa62465808cde7c55494abe799875099e85973889745a`。四个128局部源码已分别绘制“运河工坊路口”，水道/桥/栏杆/铺砖均跨x/y=128；无整图输入、无裁切生成、无拼合后涂改。`demos/chunk-scene/README.md` 为重建入口，公开产物在该目录assets。

P4a最新证据：94源码测试（新增5）、43稳定图、77ZIP和不变包通过；10外部最终图/布局、138保护文件不变。仅给一个块源码+helper+合同+runtime的隔离目录可精确重建；14条中文空格路径实际命令0意外失败、3预期拒绝。NE旗帜84像素变化，其他三块哈希与所有非目标RGBA保留；注入横移/相位错误被检出。实际查看原尺寸、2倍、灰度、四条接缝/8视图和中心交点，未发现关键断裂，视觉修正0轮。首次检查器误判6个水面高光，修规则不改合同/画面。报告 `docs/chunk-scene-report.zh-CN.md`，机器记录 `docs/measurements/chunk-scene.json`；原始记录 `evaluation/chunks-20261023/`。最后添加批量flag参数后重跑5项针对性测试，最终实现待本提交8组CI。Skill封存哈希、本地v1.1.1不变。

P4a实现提交 `a6d84936618b5176c5eecffcea6accd8ec4b745e` 已推送，[CI运行39981625213](https://github.com/Chenamel/deterministic-pixel-art/actions/runs/39981625213)8组全部成功，覆盖Windows/Ubuntu主流程及Pillow10.4/11.3/12.1兼容矩阵。记录 `docs/measurements/chunk-scene-ci.json`。最终批量flag CLI另行实际调用，PNG与独立块重拼RGBA精确一致，manifest参数匹配。重新读取本地安装仍v1.1.1。

下一动作：P4b先评估原生512的实际用途；只有增量表达/编辑收益明确才画新原生512场景，不能放大旧图冒充。若无明确需求则进入候选收口：把P3/P4可复用方法整理进按需Skill指导/最小例子，再新候选包，不覆盖冻结包；稳定发布仍待既有门槛与P1外部结果。阶段汇报必须在直接文字输出说明：4主阶段；P1外部待回、P2/P3完成、P4a完成；下一P4b条件项/候选收口，不能说四阶段全部通过。

用户已批准依次推进。P1三份定向任务包已分发，外部新返回仍0；P2可读配方与P3真实消费端示例已完成。实际平台结果与本地准备/演练分开记录。原工具、原始提交、已安装稳定Skill继续保留。

P3实现提交：`1f24256584e491a054c6bafd825383850b8f0b68`（起点 `db5b1b3`），已推送。本提交[CI运行39934535393](https://github.com/Chenamel/deterministic-pixel-art/actions/runs/39934535393)的8组全部成功，含Windows/Ubuntu完整流程及Pillow10.4/11.3/12.1兼容矩阵。记录 `docs/measurements/consumer-ui-ci.json`。P3资源/字体/截图仅在仓库，Skill封存rc.3与本地稳定v1.1.1不变。

P3最新恢复点：`demos/pixel-ui/` 与 `tools/build_consumer_demo.py` 已完成。实际浏览器Silkscreen8px下 `EXPORT MAP`宽58px；64px基线文字区30px、六态均溢出，96px改后文字区62px、18项标签/状态全部适配。鼠标/Enter/Space、LOOP选中+焦点、禁用跳过/点击无效、按下/释放/移出取消、两底色1/2/3倍通过。112px/START真实重建与页面同步通过，恢复后13个产物逐字节一致；最终图片使用已校验字节、重载/Enter冒烟通过。3项新测试通过，首次Windows错误输出编码已修正。完整流水线89源码/43稳定图/77ZIP、10外部图/布局、138保护文件通过；重打包与冻结rc.3哈希不变。报告 `docs/consumer-ui-report.zh-CN.md`、`.md`，机器记录 `docs/measurements/consumer-ui.json`；原始记录 `evaluation/consumer-ui-20261023/`。实现提交8组CI已核验通过。下一动作：P4先冻结风格、跨块结构和边界所有权，再分别绘制/拼合/接缝复检。P4尚未开始；稳定/本地v1.1.1、P1三包与本地封存rc.3不变。

- 详细计划：`docs/next-stage-plan.zh-CN.md`；开发过程和决策：`docs/development-log.zh-CN.md`。
- 顺序：P1三个定向复测 → P2参数化创作配方/短编辑路径 → P3实际使用端闭环 → P4真正独立256分块，过关后才考虑512。
- 已解决的编辑入口成本：128飞船JSON为439,756字节、33,744行；P2将49行/2,535字节配方及共享辅助随Skill分发。展开JSON仍保留，源码体积不等同token收益。
- P1三个固定输入任务、一页启动说明、4个端到端测试和三包本地演练已完成。22次演练调用全部符合预期；外部执行数仍为0。入口：`docs/focused-trials.zh-CN.md`；记录：`docs/focused-trials-report.zh-CN.md`。
- P1等待外部结果时可继续本地P2；未收到结果不得记为通过。八项原始核验已完成，不必重做；原受控发布门槛不被短复测自动替代。
- 代码基点为 `e0ed738`；v1.2.0-rc.2原包/哈希和已安装v1.1.1保持不动。下一批改变分发内容时再使用新候选版本。
- P1提交 `8932e7a` 已推送，8组CI全部成功：`https://github.com/Chenamel/deterministic-pixel-art/actions/runs/39916354346`。80源码测试、43稳定图、61项ZIP、官方校验通过；重新打包哈希与冻结rc.2完全相同。
- rc.2预发布已上线，重新下载9附件全部匹配；千问ZIP还完成无登录直链下载和哈希核验。记录：`docs/measurements/focused-release.json`。稳定/本地安装仍v1.1.1；外部三任务0份返回。
- P2新增 `recipes/`：图标、六态按钮、128精灵、256组件场景及共享输出。生成器复用同一几何源码；JSON仍v1。Pillow12.3.0下4份默认图与冻结rc.2一致；固定小改17次独立目录命令、0意外失败（1次预期拒绝覆盖），3份JSON再渲染精确一致。飞船328像素和hover832像素变化均在允许区域，其他RGBA变化0。实际看图复查通过；字体/交互留P3。
- P2本轮86源码测试、77项ZIP场景、官方Skill校验、43稳定图、10外部最终图/布局、138受保护文件全部通过/不变。候选rc.3包91文件/222,984字节，SHA-256 `b680e73c966eb6557ed94bfc2e843dd4fca2c74c8aaf5f279caa2eeece6f308d`。相对rc.2增加9,222字节/4.3%，未测模型token或修改耗时收益。报告：`docs/recipe-workflows.zh-CN.md`、`docs/measurements/recipe-workflows.json`。
- P2代码提交 `5f700d977a05e3e50dd1ae6de9fab7a7b0ee3917` 已推送，8组CI全部成功：`https://github.com/Chenamel/deterministic-pixel-art/actions/runs/39919655914`。本地封存 `dist/v1.2.0-rc.3/deterministic-pixel-art-v1.2.0-rc.3.zip`（同上SHA-256），有逐文件与整包清单；未发布rc.3、未替换本地稳定Skill。
- **P3本地验收与本实现CI完成，下一项P4**。真实字体发现/修正文字溢出，交互与缩放、参数重建已实际验证。下一阶段先冻结256场景全局风格、边界所有权与跨块结构，再分别绘制四块并复检接缝，不能用裁切重组冒充。外部P1结果仍为0，不等同验收通过；Minecraft未做实际字体/游戏内验证。
- 最终任务包：`dist/focused-v1.2.0-rc.2-final/`，勿上传较早无`-final`的中间产物。演练：`evaluation/focused-20261023/中文 rehearsal space attempt2/`。首次协调脚本误写verify选项的失败记录也保留。

## 前一阶段封存快照（后续状态以上方为准）

本轮用户批准的 M1→M2→M3 已完成，当前交付是 **v1.2.0-rc.2 本地候选版**。已通过 76 个源码测试、43 张稳定图回归、10 张外部最终 PNG 精确复现、61 项独立目录 ZIP 测试及官方 Skill 校验。138 个原始/输入文件哈希不变。**未发布到 GitHub、未替换本地已安装 v1.1.1**；八项探索试验不冒充受控 A/B 发布门槛。

- 详细中文结果：`docs/workflow-report.zh-CN.md`；英文：`docs/workflow-report.md`。
- 实测 JSON：`docs/measurements/workflow-validation.json`。
- 可试用包：`dist/v1.2.0-rc.2/deterministic-pixel-art-v1.2.0-rc.2.zip`，213,762 字节、85 文件。
- ZIP SHA-256：`a34e5c58e420fd43702fe9b892fbbae2a32a57a47311e58f242dad140e9ded22`；同目录有 `SHA256SUMS.txt` 和逐文件清单。
- 原生 128 飞船、256 场景、单格编辑规格：`examples/workflows/`；可直接查看 `docs/workflows/` 的预览。
- 下一步顺序按上方新计划：先短复测与降低编辑成本，再做使用端示例和独立256分块。现有四块范例是裁切重组控制，不证明独立生成的风格衔接。
- 已知代价：相对 rc.1 完整 render/review 中位数约慢 22/24 ms；纯渲染基本持平，包体增加约89%。不宣称节省 token、修改轮次或普遍提高审美。
- 仍未验证：本候选新版 Ubuntu/Pillow 多版本 CI、原始 OSS/FUSE 环境、独立盲评与游戏内效果。不要据此提升稳定版本或更新本地安装。

## User-authorized objective

Implement the recommended improvements in order, and maintain durable local notes so interruptions or context compression do not lose decisions or progress. Deliver a tested candidate tool, a named-atlas single-cell editing example, a native 128x128 sprite, and a 256x256 component/tile composition example.

The product serves AI agents creating deterministic pixel icons, sprites, generic UI, optional Minecraft assets, and precise edits. Prioritize convenient workflows and demonstrable correctness over adding commands or aesthetic scores.

## Safety of existing work and release state

- Repository: `D:\mcmod\deterministic-pixel-art`; start commit `d5e6f751c879ab33cbce951441ae1bb9b66be485`.
- Original `D:\mcmod\llm-pixel-art`, mod resources, historical baselines and submitted evaluation material must remain intact.
- Published/local installed stable Skill: v1.1.1. Published candidate: v1.2.0-rc.2; local recipe candidate: v1.2.0-rc.3. Candidates remain separate from the stable installation and controlled acceptance gate. Do not relabel exploratory or focused tasks as the old A/B release gate.
- Keep complete external conversations in local ignored `evaluation/`, outside distributed Skill context and public commits.
- Change source runtime in `src/`, maintained Skill instructions in `skill-content/`, examples in `examples/`; `skill/deterministic-pixel-art` is generated by the packager.

## Evidence already completed (do not repeat the whole audit)

Read `docs/roadmap-20261023.md` for scope and acceptance.

Local full audit: `evaluation/external-pilot-20261023/audit/核验结论与优化顺序.md`.
Measurements: `evaluation/external-pilot-20261023/audit/measurements.json`.
Audit scripts: `evaluation/external-pilot-20261023/audit_pilot.py`, `probe_pillow.py`.

- All 10 main final PNGs from 8 external tasks match their specs in baseline Pillow 12.3.0.
- All four icon edits preserve non-transfer RGBA. Hover changes exactly 96 ring pixels and zero outside.
- Light-primary silhouette review card is blank: confirmed RC bug (foreground equals background).
- Hard-link rejection blocks default publication: external mount logs + controlled Windows simulation; original OSS/FUSE environment not reproduced.
- Pillow 11.1.0 vs 12.3.0 polygon fill differs by 5 pixels in spaceship v1. Same Python 3.12 comparison confirms dependency sensitivity. Finals match. Do not change all polygon rasterization or blame missing source files.
- Existing per-cell occupancy/bbox/margins/centroid already exist in inspect/review JSON. Improve discovery/presentation instead of duplicating analysis.
- Import preserves RGBA but flattens atlas names; source-over atlas assembly must not silently become raw replacement.
- 42 source evaluation inputs and 96 protected original files were hash-verified unchanged.

## Implementation checkpoints

- [x] Persist objective, evidence, constraints and acceptance before editing.
- [x] M1: visible review on all backgrounds; native/zoom views; convenient preview; minimal grid example; actionable output/dependency errors and controlled portable publication; reproduction notes.
- [x] M2: lossless named-atlas import/edit path with current metadata; precise allowed-change verification; executable single-cell example.
- [x] M3: file-based component/tile composition with exact bounds, coverage/overlap checks and explicit copy/composite semantics; native 128x128 sprite and 256x256 scene; inspect/review visuals.
- [x] Verify old APIs/defaults and 43 migration PNGs, external finals, targeted meaningful tests, packaged ZIP in independent Chinese/space paths, official Skill validator, deterministic packaging.
- [x] Record measured results/limitations and final resumable state; no unearned aesthetic-improvement claims.

Current checkpoint: complete local candidate. M1 runtime fixes and explicit `--portable-output`; M2 named lossless import, `replace-cell`, and `verify`; M3 bounded PNG `assemble`. New atlas `assembly:copy`, positions/rows and sparse base are opt-in; old source-over defaults preserved. M3 uses a separate PNG manifest, no file inclusion in JSON v1. Current/legacy sidecars remain differentiated: digest-less legacy metadata only checks structure, not content identity.

Validation completed: all 76 source tests pass, including warnings-as-errors in `tools/check.py`; 43 stable images, 86 historical fixture files and eight frozen studies pass. First full run exposed assembly coverage counting on Pillow mode `1`; fixed by summing nonzero histogram bins. Both project and official validator ZIP runs pass 61 cases; the final documentation-only package update was rebuilt twice and official-validated again. All 85 ZIP entries match the manifest. Builder `tools/build_workflow_examples.py` is included in the portable check pipeline. Component and tile assembly both exactly match the control; atlas edit changes 66 pixels, zero outside transfer. `verify_rc2.py` rechecked all 10 external finals and all 138 protected files without running submitted scripts.

Visual self-review complete: viewed native128/native256, sprite3x, scene2x, multi-background/grayscale/silhouette sheet and final eight seam crops. Corrected antenna contrast, crate/foliage overlap and waterwheel/river placement. Generated examples, `docs/workflows`, `evaluation/workflows` and `output/workflows` reflect final edits. Tile control is crop/reassembly, not evidence of different agents independently painting seamless chunks. README/Chinese README, changelog, maintained references and generated distribution are synchronized. Published baseline/local installed Skill remain untouched.

Local evidence scripts: `evaluation/external-pilot-20261023/verify_rc2.py` (read-only input regression), `evaluation/workflows/measure_costs.py` (rc.1/rc.2 same-machine costs), `evaluation/workflows/seal_candidate.py` (verified local archive/manifests/reports). These contain local evidence paths and stay ignored; portable tools/examples and summary measurements are committed. Detailed raw conversations stay out of public Git and Skill context.

## Useful commands/environment

PowerShell. Baseline interpreter:
`D:\mcmod\deterministic-pixel-art\evaluation\release 验证 space\.venv\Scripts\python.exe`
(Python 3.14.2 / Pillow 12.3.0).

Source tests: `python -m unittest discover -s tests`.
Portable pipeline: `python tools/check.py` (migration/evaluation/packaging/ZIP tests).
Official validator: `C:\Users\philia093\.codex\skills\.system\skill-creator\scripts\quick_validate.py`.
Always specify UTF-8 for text files; use UTF-8 stdout for Chinese paths.

Update this file at milestone boundaries with completed items, exact test results, unresolved issues and the next action. Keep details in the roadmap/report rather than appending a full tool transcript.
