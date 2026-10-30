# Pixel Anchor 品牌接入

## 展示内容

[英文首页](../README.md)与[中文首页](../README.zh-CN.md)采用同一 Pixel Anchor 图形和英文项目名。中文副文案为“面向 AI 的像素绘图与精确编辑”；图标保持纯图形。

- 标题图：[英文深色](images/brand/header-en-dark.png)／[浅色](images/brand/header-en-light.png)，[中文深色](images/brand/header-zh-CN-dark.png)／[浅色](images/brand/header-zh-CN-light.png)。原生384×112，最近邻3倍导出1152×336；README使用深浅主题picture，默认浅色。
- Skill展示：[源配置](../skill-content/agents/openai.yaml)及生成副本采用32px／128px固定深底徽章，展示名为Deterministic Pixel Art，品牌色为`#146F80`。短说明、默认提示和调用策略保留。
- 新构建的Skill只增加两张PNG图标及展示元数据；标题图、字体及制作资料不进入Skill。现有v1.2.0 Release与安装版不变。

展示字段参考[OpenAI技能文档](https://developers.openai.com/codex/skills/)。配置与文件检查不能证明原生界面已经加载图标。

## 编辑与来源

[素材说明](../assets/brand/README.md)提供已选规格、无需字体的重建命令及改字入口。[生成器](../assets/brand/build_identity.py)仅依赖已选规格，使用工具实际渲染四张标题图和两张图标；改中文时先验证字体字符映射。

中文使用Fusion Pixel Font12px简中版本，英文使用Silkscreen。固定版本、摘要和SIL OFL1.1许可见[字体记录](../assets/brand/font-notices/README.md)。Fusion完整字体不随仓库和Skill分发；现有文字已保存在可编辑points规格中。

## 验证范围

[审阅报告](brand-review-20261030.zh-CN.md)记录独立公开副本重建、打包与同步结果；[五项自查](self-check-brand-20261030.md)列出链接、双语、引用、覆盖及未做事项。运行时、JSON v1、公共接口与既有像素输出不在本次变更范围。

实际Codex原生图标加载、移动端裁切、独立受众辨识及商标检索仍未验证。作者看图与工程检查不作为普遍审美或提效收益证明。
