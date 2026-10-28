# Resume this work here

Updated: 2026-10-28 (Asia/Shanghai). Active branch: `codex/visual-quality`.

## 最新沟通与分发约定：外部任务只含操作信息

2026-10-28用户指出任务说明夹带给协调端/用户的备注，要求有取舍、讲清步骤以及哪些资料发给哪个外部AI。**长期偏好：执行包只含任务、必要输入/Skill、运行方式与交付；看图包只含需求/图片；模型分配、历史评价、预期缺陷、发布门槛与统计留在协调端。** 不要求制作模型查询平台数据库、统计token或写冗长方法说明；会话可直接导出再提供。制作和看图模型不接收本页/开发日志/核验结论。

操作入口 `docs/test-handoff.zh-CN.md`；原 `docs/long-term-testing.zh-CN.md` 收为简短入口，旧协议/八类队列保存在 `docs/testing-coordinator-notes.zh-CN.md`。当前先由本Codex完成UI字体/状态与提示改进，本地通过后DeepSeek定向任务→Gemini看图→千问Linux。三个后续包均未生成，不能提前让用户上传旧包；包准备后每次只交付一个文件/链接和一句转发提示。GLM/MiniMax不重复整套。

已精简未来使用的LT01/LT02任务源及看图源；构建器将推荐模型/manifest/哈希清单放ZIP外的coordinator目录，包内task.json只保留记录器必需的id与Skill摘要。新任务哈希不与历史运行混用，已完成的wave1/wave1b ZIP与rc.5/安装不改。旧prompts目录明确为模板，不能直接转发；审阅包须有TASK.md/images，不把制作包或参与者自评整份发给Gemini。原正式门槛没有变更。功能实现的下一项仍为下方UI共性闭环，本轮只整理文档与封包边界。

本次4项针对性封包/实际入口检查通过，含包内精简字段和协调材料隔离断言；19个本地链接有效，178个保护文件摘要不变。记录在忽略的evaluation/prompt-cleanup-20261028。新提示只在临时测试目录封包，未生成/分发新的UI复测包。

## 2026-10-28 当前恢复点：rc.5三份外部提交核验完成，下一项共性UI闭环

用户结果目录 `D:\Users\philia093\Desktop\rc5测试` 共8个原始文件：2份输入ZIP、3份submission、GLM/DeepSeek外置原始JSONL和Gemini review.md。**MiniMax原始JSONL在其submission的RUN/session-export内，三位制作端会话均已收到；Gemini没有独立review.json或原始审阅会话，不要求用户因此重跑。** 原始快照/哈希与核验代码放忽略的 `evaluation/long-term-results-20261028/`，原会话、个人用量/配置不进Git/Skill。

从干净 `155dbc3` 完成：3份可信冻结记录器独立重检全部通过；35条记录命令、3次非零可归因（DeepSeek辅助路径、MiniMax自写坐标换算、已选88×18单格的网格超限）。6组规格/PNG与3组导入/局部规格精确重建。GLM改动70个RGBA像素、区外0、原布局保留。最后命令快照文件无不一致；三份制作日志含名义模型ID及图片打开调用。Gemini的21行图片文件/RGBA哈希全部匹配，未据此声称其每次看图/重渲染已独立证明。LT01离线方向/边界通过；两份LT02源图/消费端相同，工程通过但按下图文一致性待修。

反馈已受控复现并分流：按下图标移1px而文字不动属实，但隔离变体非按下文字y=2/按下y=3可通过旧检查器，不能说契约完全无法实现；只从本次y=3把按下改y=4则3项边距失败。单色字体变体仅2项消费端重建失败，确认旧基准固定默认灰度栅格化；是否单色是显式风格选择，不通用强制。MiniMax的40px裁切截断START，不能当作字形缺陷证据；完整裁切无缺字。网格错误建议--cell但实际已选单格，需改尺寸/区域提示，保留有界输出。短标签64px示例与长标签示例不是语义冲突，但用途应标明；Context与metadata分开是设计，改发现路径而非重复布局。

原始JSONL确有providerData.usage/rawUsage计数，之前“完全不可得”过强；只能作已观察响应的范围明确统计，含重复/缓存输入/后续导出，不能等同整任务计费或版本收益。原始个人用量留私有，不公布数值。不把disabled对比度3.489、短标签留白、小勾号等直接升级为任务失败或普遍审美规则。新旧版本没有配对，不能称本批视觉问题为“新版退步”。

结果文档 `docs/long-term-results-20261028.zh-CN.md` / `.md`，机器摘要 `docs/measurements/long-term-results-20261028.json`。原始8用户文件与170保护文件哈希不变。本轮仅核验/复现/排期，**没有改Skill运行时、封存rc.5、稳定安装，没有制作rc.6**；不能把协调端修正图当成外部成功。不重跑未变运行时全套103测试/43图，也不借旧CI冒充本次执行。

下一顺序已记录：①一个可复用可选消费端辅助入口，实际字体边界、显式灰度/单色、状态文字位移、布局/Context同源；保持JSON v1/旧API/默认值，另立新测评协议不回写旧LT02；②网格尺寸报错、标签容量/半开矩形/metadata与记录器短说明；③本地验证后只发1次定向复测，再准备千问LT03 Linux/portable新包。LT03尚无分发包，不让用户拿旧包冒充。优先降低辅助脚本/证据正文负担，不新增无依据命令、256×256巨量网格、任意shell接管或自动覆盖。

四主阶段P1/P2/P3/P4a完成，P4b512仍暂缓；当前位置本批长期外部核验完成，下一项上述UI/提示修正。3个外部运行只覆盖2个任务/1个制作环境，原32会话/至少6项收益门槛未改；稳定/安装1.1.1、候选rc.5不变。不重复让用户做刚收到的Gemini复检，不自动调用平台/花额度/提醒/发布/安装。

## 历史分配：2026-10-27 Step限免结束，改派GLM；MiniMax补测UI

2026-10-27用户提供WorkBuddy截图：GLM-5.3-Flash、MiniMax-M3.1-Flash均显示0.08×。**只调测试分配与分发包外层说明，不修改Skill、rc.5封存包或稳定安装，不根据截图宣称费用或能力优势。** 新分配：GLM→LT01；Deepseek-V4.1-Flash→LT02；前两项回收核验且有额度后，MiniMax可在新会话独立复测同一LT02。Gemini只审实际返回产物。GLM暂按截图高/1M、MiniMax极致/300K，记录实际设置和执行/看图能力；指定模型的思考强度与不固定后端的同名路由区分。深度/窗口变化单独记录，不能用容量估token。

当前分发目录 `dist/long-term-v1.2.0-rc.5-wave1b/`，包按任务命名 `LT01-AtlasEdit.zip` / `LT02-Buttons.zip`，内有同一冻结rc.5、相同输入/绘制需求/预算/记录器/检查器；仅外层推荐、分发标识及环境记录说明更新。旧wave1和历史摘要保留，原Step计划标未运行改派，不记模型失败；MiniMax重复LT02不计新领域或版本A/B。分发指南 `benchmarks/long-term/START_TESTING.zh-CN.md`；总计划 `docs/long-term-testing.zh-CN.md`；新核验数据在 `docs/measurements/long-term-reassignment.json`，本地原始核验在忽略的 `evaluation/long-term-20261027-reassignment/`。下方2026-10-25 Step分配为历史准备记录，不是当前要发的模型。

Skill不因模型售价/限免调整：已有工具错误或多次独立出现的入口阻碍，才决定修工具/说明，另封存候选。单版跨模型反馈不能替代原两环境×八任务×两版本32新会话、至少六项具体收益、另一环境无反退和独立复检门槛；本轮外部执行仍0，不自动调用平台、花额度、发布或安装。保持用户已选**按额度恢复手动推进、无定时提醒**。

本次改派准备完成：4项针对性测试/4条新包中文空格路径实际入口命令通过；两包各97个Skill文件精确匹配，绘制需求与预算不变，163个保护文件哈希不变。LT01-AtlasEdit.zip 244944字节，SHA-256 `eab4a2fcad68cbad65527640cdb821952e66bc7de0ef2598cf781fb05b9722ce`；LT02-Buttons.zip 259158字节，SHA-256 `5ddb879738a4b15710213dc69b63de51c0bd704ec88f1150b9c5f68f129211f4`。不重复不变Skill整轮验证，不据本地入口测试宣传新模型通过。

改派实现 `7bfffae` 已推送 `origin/codex/visual-quality`；main、tag/Release与本地稳定安装不变。本轮记录本地针对性检查，不借用旧8组CI声称本提交远端CI已通过。分发ZIP仍在本地dist，未上传新Release附件。

四主阶段：P1已核验，P2/P3/P4a完成，P4b原生512暂缓。当前位置是正式版前长期外部补证。下一步发GLM的LT01、DeepSeek的LT02；回收submission及过程，先核验工程/像素/布局，再让Gemini独立看图，有额度再补MiniMax。LT05精灵和LT08分块仍待后续独立冻结，不因同模型先做小任务而标完成。当前稳定/安装1.1.1，候选rc.5不变。

## 历史准备：2026-10-25长期额度测试首轮两包

2026-10-25用户提供WorkBuddy可选模型截图，说明豆包/千问额度需刷新、Gemini Pro可长期分批复检，希望尽量完成测试。当前行动是分配与准备外部任务，**不是自动调用平台/消耗额度或取消原发布门槛**。计划 `docs/long-term-testing.zh-CN.md`；私有额度/结果台账 `evaluation/long-term-20261025/{schedule,quota,paired-queue}.csv`，不可提交Git或Skill。截图倍率/免费活动不当作价格、能力或刷新政策，第二额度面板未独立确认归属/时区，个人用量不公开。

先只发两份：WorkBuddy **Step-5-Preview → LT01命名单格修改**，WorkBuddy **Deepseek-V4.1-Flash → LT02配方/六态/真实字体18实例**。最终包目录 `dist/long-term-v1.2.0-rc.5-wave1/`，内含START_HERE、冻结97文件rc.5、记录器、输入/必要字体许可。LT01-Step5.zip 244822字节 SHA-256 `fb904ed420dc78afe9a7bd89b1006ef3fdb6ff1267ad963237ebf5a9650e16ad`；LT02-DeepSeek.zip 258977字节 SHA-256 `6a983a27c8ad7e4bf96bb98fa2a333c8e363a7e1cee9a20110a4c68d41ce423b`。4项新增针对性测试通过，2包中文/空格路径协调端实际演练通过，已看箭头原尺寸和字体3倍图；这些**不是模型执行**，本轮外部结果0。

Gemini等两份真实产物回来后，用 `benchmarks/long-term/REVIEW.md` 独立复检，不先看作者好评。千问额度恢复后再准备LT03公开下载；后续Hy3/GLM-5.3-Flash/MiMo/豆包/MiniMax按八类覆盖逐项领取，不要求每模型全跑。Hy4/元宝为可选辅助，不依主观印象提前定能力；路由“快速/均衡/极致”不进入固定模型A/B。

A/B为另一队列：先等两项上手反馈，再冻结当时稳定版和当前候选/协议，建议1.1.1对rc.5或修正后的新候选，但**新对照包尚未制作/分发**；历史1.1.0/rc.1包不替换，原32会话/至少6项收益门槛未改。拟WorkBuddy/DeepSeek文本条件与千问多模态条件，每次一对，同模型/环境/预算；模型变更单列批次。无需找天生盲模型。**2026-10-25用户已明确选择按额度恢复手动推进，不设置定时提醒或自动化，不自动调用其他平台或消耗额度**；不是待答问题。首轮LT01/LT02分配保持不变，用户返回实际产物后再整理/核验并领取下一项。

当前仅新增测评构建器/记录器/提示词/文档，不修改Skill运行时或封存ZIP，稳定/安装仍1.1.1。实现 `1ec1022f591310bf61b7fbfea41ac008e26b3863` 已推送，[CI运行40118220301](https://github.com/Chenamel/deterministic-pixel-art/actions/runs/40118220301) 8组全部成功；记录 `docs/measurements/long-term-preparation-ci.json`。两个任务包内97个Skill文件逐一与封存rc.5匹配，原rc.5及安装文件摘要不变；交付目录完整清单已重核。

本轮分配/首轮准备完成，**实际外部执行0**。下一项用户各开新会话交LT01/LT02，回收submission/会话后独立核验、Gemini复检并更新台账；有额度再准备LT03公开链接和后续单版领域，先小试反馈后冻结新的长期A/B。不要重复准备首轮包或把协调端演练写成外部结果。四阶段仍P1审核/P2/P3/P4a完成，P4b512暂缓；当前为长期补证/正式发布验收，不新增第五功能阶段。

发布距离与未验证痛点：[docs/release-readiness.zh-CN.md](docs/release-readiness.zh-CN.md)。2026-10-25用户追问后已逐项核对：rc.5新入口尚无外部新会话试用，原八项配对/至少六项收益门槛未达；旧A/B包固定1.1.0/rc.1，不能直接证明rc.5。文档建议可由用户决定将工具可用性与普遍效率/审美声明分开验收，但**尚未改变原门槛**，不据此自动合并/发布/安装。工程实现与P1审核无需重做，512不是前置条件。

## 最新恢复点：P1核验及rc.5收口完成，本实现8组CI通过

2026-10-25，用户提供 `D:\Users\philia093\Desktop\RC1测试`，含WorkBuddy/DeepSeek、千问、Gemini三个submission ZIP和7份过程/反馈Markdown。从干净提交 `e66d87d` 继续。目录名不直接当成工具版本；以各包task、环境、校验记录和实际输入核对冻结rc.2。

执行顺序：记录原始文件哈希/保存本地快照 → 只读检查ZIP结构、输入/工具哈希、命令/环境与失败 → 使用可信仓库运行时独立重渲染/检查RGBA和布局 → 查看PNG前后/目标背景 → 逐条反馈归因与必要的窄范围复现/修正 → 写公开汇总与恢复点。外部附带脚本只作证据，不直接执行；原始资料不修改、不提交到公开仓库或Skill。

原始核验目录为忽略的 `evaluation/p1-results-20261025/`。**P1三份已收到且工程核验完成；P2/P3/P4a完成，P4b暂缓**。本轮新增窄范围编辑入口，另封存本地rc.5；已发布rc.2、冻结rc.3/rc.4和稳定/已安装1.1.1不动。不能将本轮短复测当作八项受控配对门槛或普遍审美/效率证明。

首轮独立核验已通过：53条命令、5次非零退出均可归因（3次防覆盖、1次Pillow13范围拒绝、1次挂载硬链接EPERM）；13份规格/PNG成对重渲染精确一致，3张编辑最终图在冻结rc.2和当前rc.4均精确重建。改动为70/96/195个RGBA像素，区外均0；千问portable及目标背景预览与冻结输入一致。已看原尺寸/放大对照、浅底剪影和千问预览，未发现新的核心像素错误。10份用户原始文件哈希不变。注意：submission只含RUN，远端工具哈希为日志声明，未随包提供完整runtime供独立重哈希。

已用可信冻结记录器复现：目录外输出命令可记录到commands.jsonl，仅自动产物哈希限RUN；千问的/tmp成功为自述笔记，缺命令和PNG佐证，不作已独立核验事实。Gemini失败实际是第17条，文字自述第15条有出入，以JSONL为准。

已实现窄范围易用性改进：可选 `import --cell` / `image_to_spec(...,cell=...)` 通过已验证布局直接导出命名单格；补候选目录/最终输出和palette映射说明，明确未来任务方向语义。无新旋转语法、图库、自动覆盖或警告静默化。首次漏改API懒加载转发包装导致4项测试失败，修正后11项针对性通过；记录保留。实际V提交的5命令闭环精确重建最终图，195像素变化/区外0；全图规格5857字节→选格1551字节，只证明减少手工查找复制，不是token收益。

rc.5完整检查通过：**103源码测试/43稳定图/91独立ZIP场景**，官方格式及中文空格临时目录实际导入/渲染通过；10张历史外部最终图/布局一致，138历史+10本轮来源共148文件哈希不变。包97文件/231,561字节，较rc.4增加1087字节/0.472%，SHA-256 `2b9cb652fb9e4a50bd3e4d11e098003b86c6195a16c9b1730dbc6907839178a4`。封存目录 `dist/v1.2.0-rc.5/`，双语结果 `docs/p1-results.zh-CN.md` / `.md`，机器记录 `docs/measurements/p1-results.json` / `p1-candidate.json`。原始10文件、旧候选和稳定1.1.1已再检查，未修改。

实现提交 `6f685f4ceea4078bed4445d88e658739382d579c` 已成功推送至 `codex/visual-quality`；[本实现CI运行40113419219](https://github.com/Chenamel/deterministic-pixel-art/actions/runs/40113419219)8组全部成功，覆盖Windows/Ubuntu主流程和各自Pillow10.4/11.3/12.1兼容矩阵。逐组记录 `docs/measurements/p1-results-ci.json`，同步到候选验收数据/本地封存目录。没有将较早提交的成功当作本次结果。

最终收尾已通过：109处维护文档本地链接有效；本地封存13项交付文件清单匹配，rc.5 ZIP摘要不变；三个历史候选、10份本轮来源及本地已安装文件哈希再次核对不变。原始记录 `evaluation/p1-results-20261025/final-integrity.json`，原始会话没有进入Git/Skill。源码实现CI8/8已完成，最后文档改动无需重复整轮检查。

本轮核验与候选交付已完成。下一项：围绕明确的真实项目与消费端使用rc.5，观察选格→局部修改→替换→使用端的阻碍；需要正式发布时核对先前约定的八项配对/具体工作流收益门槛，不用本轮三项代替。无新问题不重复测试不变整包，不增加画布/命令来制造进度；不合并main、不自动发布稳定/更新安装。原始云挂载、独立审美与游戏内仍未证实。阶段直接回复必须含4主阶段状态/当前位置/下一项/外部待项；P4b512只有具体需求才重启。

## 历史检查点：rc.4候选收口（当前状态以上方为准）

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
