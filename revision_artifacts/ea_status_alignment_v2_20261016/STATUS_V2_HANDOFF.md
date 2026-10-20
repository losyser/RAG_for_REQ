# 状态语义与 UI / EA 一致性修正交付

日期：2026-10-16。已在已授权的 111.qea 追加且仅追加一次四个独立包，图 ID 7–10：REQ_status_v2_cn98_rule、REQ_status_v2_cn98_support、REQ_status_v2_en23_rule、REQ_status_v2_en23_support。导入前一致性备份：111_before_status_v2.qea。没有切换模型、修改注册表、终止用户进程、调用付费生成 API、提交或推送 Git；论文与回复稿未修改。

## 结果

- 共享 requirement_status.py 同时驱动 UI 和 EA。Coloring by 可切换 Rule grade / Evidence support；切换不改原始正文、等级、原始支撑状态或关系。
- A/B/C/X 是既有 criterion/citation 规则结果，不是证据语义核验或置信概率。已存在 grade 优先保留；缺失时仅按原分类器生成展示值并标记 computed_display_only。没有改分类器和既有正式样本等级。
- 原始 verified_by_direct_evidence 映射为 Reported direct (unverified)，indirect 同样标明 unverified。缺失或未知状态显示 Not assessed，不能从 A/B/C/X、legacy Direct、模型自称 semantic_support_verified 推断 Verified。
- semantic_verification_state 目前全部 not_assessed。本轮没有实现独立签署审查记录的接入或完成语义核验，不能把新显示层当作验证证明。
- Rule grade 沿用来源灰、A绿、B蓝、C橙、X红；本次两批数据没有 A，不生成伪造 A 节点。Evidence support 使用独立状态配色，图例明确 unverified。
- 所有关系仍为 Nesting（分组），未新增 deriveReqt / satisfy / verify 或证据支持边。JSON 原始 type=derive 描述仍作为原始信息保存。

## 参考与结构

本地 references/ea_native_sel1_verified.xml 已再次校验 SHA256：b2893c10d44a6154dbdc0d3447e1526cd0847bd0613aaabe68bd4fbaab2bcd89。参考含 11 个 ClassifierRole，独立内容 tagged values 确有 id/text；并非把 ID 当名称。延续此前修正的 Collaboration / ClassifierRole、EA root Class、SysML1.4 requirement stereotype/xref、documentation 与 content tagged values 结构。

最终样本 name=High-Temperature Valve Setpoint，id=OR008.1，text 完整保留两句规范要求（79°C nominal、77–85°C range），criterion 独立存放；grade=B，但 Evidence support=Not assessed。name/id/text 完整示例见 final/name_id_text_examples.json。memo 前缀为 EA 长标签编码，不属于规范句正文。

本轮按后续已接受的折叠小图方式显示名称头与 id 区，完整 text 仍独立保存在标签/Notes，可展开；并非删正文。中文原始源需求没有另行审定的短标题时保留原文作为标题，没有虚构英文翻译。原新截图附件本轮没有重新获得像素，不能声称重新看过该附件；final 中四张新图则已实际查看。

## 验收证据

1. 全量 pytest：276 passed in 8.96s，tests_final.xml。
2. 真实浏览器访问本机 Streamlit，逐节点比较两种模式与真实下载 XML：中文98子需求 ×2，英文20子需求 ×2，全部匹配。browser/acceptance.json。下载按钮改为 on_click=ignore，防止重跑导致下载取消；浏览器等待整批显示模式一致，避免读到过渡 DOM。
3. 中文原批：30来源+98子项；子项 C93/B3/X2，reported_direct4 / reported_indirect5 / evidence_gap87 / needs_review2。英文正式样本：3来源+20子项，B7/C13，20个全部 Not assessed。两批明确分开核验，不混用指标。英文 UI 验收使用原样本的临时离线适配夹具，保留原等级/正文/引用，无 support_status。
4. 原生 EA 导入、回读和图片导出实际成功：每个中文包128需求、3647属性、98关系；每个英文包23需求、720属性、20关系；共302需求实例、8734属性、236关系，全部逐项匹配。native_validation.json。
5. 四张代表小图各显示4节点，原生颜色与共享定义逐项相符；完整模型未删节点。每张有 PNG 1069×950 和含文本绘制记录的 EMF；保留 EA 试用水印，未规避授权限制。final/status_semantic_validation.json。
6. 未审定中文翻译的 English paper 导出在真实 UI 被明确拒绝，没有冒充英文论文图。
7. 原始 data 下137个既有 JSON/JSONL/XML SHA256 均未变。临时英文夹具已备份到 browser_fixture 后精准移除，data_integrity.json。

## 原生修复与保护边界

初次导出的显式普通 Package 图形会遮挡节点；仅增加 sequence 不足以修复。最终导出器去除这一多余图形，让 EA 自动生成原生图框。已从新图7–10移除普通包图形并重导出；没有删除模型包/需求/关系。最终文件只使用 final/；根目录同名前缀图片/XML保留为失败尝试证据，不作为交付版本。

原有125个对象、2335项属性、100条模型关系的整行数据均未变，包仅根节点 LastLoadDate 更新。但不能声称原有图数据库逐字节不变：5张旧图保存字段变化，7个旧 diagramobject 行、3个旧 diagramlink 行和4个 xref 行存在差异，包括两节点的小幅坐标变化、旧温控图绘制顺序及路径变化、SaveTag/泳道保存信息变化。这些差异发生于当前 EA 会话保存期间，无法单凭回读归因于用户编辑或 EA 自动保存；没有擅自回滚它们。完整差异见 prior_diagram_session_differences.json；原始一致性备份完整保留。不得宣称旧布局完全未变。

## 文件

- final/status_v2_{cn98,en23}_{rule,support}.{xml,png,emf}：最终4套，XML为完整模型+代表图。
- code_after/、status_v2_changes.patch：本轮代码与基于本轮前状态的补丁；用户此前更改保留。
- acceptance_scripts/：原生和浏览器验收脚本；不要重复执行导入脚本，已有4包。
- browser/、native_validation.json、same_batch_alignment.json、input_provenance.json：验收与来源。
- 111_before_status_v2.qea：本地导入前备份（不包含在轻量ZIP）。

本轮范围完成；剩余限制为 EA 试用水印、尚无独立语义签署核验流程、旧图会话布局差异不能做完全不变声明。参考图截图未重看，不影响这次实际原生图片验收。
