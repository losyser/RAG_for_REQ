## 8. 可支持的结论与论文备选表述

本次结果支持在所选共同来源、当前修订评分和确认规则下，RAG 有更多已确认正确且适用的候选。它不支持全部数值已验证、盲法有效、模型普遍优越、未知皆错或所有九条错误均已被独立证伪。以下只是可供作者审阅的文字，没有写入论文。

中文：在20个共同原需求中冻结抽取50条数值候选（RAG与无RAG各25条），由一名非作者相关专业研究生完成修订评分。按来源等权，严格“正确且适用”比例分别为30%和0%，配对差为30个百分点（来源bootstrap 95%区间12.5–50个百分点；精确双侧符号检验p=0.015625）。然而，未知结局敏感性边界为−50至77.5个百分点。由于流程记录不完整、既往材料接触未记录、评分经过修订且依据核验并非全部完成，本结果仅作为单评审探索性证据，不构成确证性或已验证盲法的结论。

English: Fifty numerical candidates (25 per arm) were sampled from 20 shared source requirements and assessed in a revised review by one non-author postgraduate reviewer. Source-weighted strictly correct-and-applicable rates were 30% for RAG and 0% without RAG, a paired difference of 30 percentage points (source-bootstrap 95% interval, 12.5–50; exact two-sided sign-test p=0.015625). Unknown-outcome bounds ranged from −50 to 77.5 percentage points. Incomplete process records, unrecorded prior exposure, revised ratings, and incomplete original-source verification limit these findings to exploratory single-reviewer evidence; they do not establish confirmatory efficacy or verified blinding.

## 9. 后续技术方向（尚未实施为实验）

文档解析应保留表格行列、跨页续表、连接符与负号差异；知识块应绑定版本、机型、对象、参数和工况，避免章节背景被误当数值依据。检索可对机型和工况做有界匹配，缺失时明确返回 unknown；向量相似度不能替代适用性判断。

生成后应独立校验引用存在性、数值/单位/比较符/近似限定词一致性，以及条件持续时间和响应时限的区别。正确的数字也可能属于错误对象；语义支持和条件适用性需要分别标注。以上为未来方向，本次没有运行新的对照实验来证明其收益。

## 10. 完成范围、复现与文件组织

本归档集中保存冻结输入与协议、样本与原行映射、三版原始返表、规范化副本、版本差异、用户补充声明、原始阻断结果、显式事后策略、统计代码、最终逐条结果和20源分母。可发评审的原始空白材料与协调者资料分开；整个归档含解盲信息，不能整体外发。

原版厂商/规则 PDF 因体量与版权不随包复制；[资料索引](03_资料来源索引/原版资料索引.html)保留原本机路径、官方或出版者 URL、版本和 SHA256。因此统计复现材料可携带，PDF 原文查证不完全可携带。没有把索引链接存在当作来源支持已完成。

可离线重放当前评分统计与八项验收测试；不重新调用模型、不重新抽样、不新增人评、不修改历史评分、不重跑全量主实验、不改变 KB、结果或论文。旧的材料生成脚本保留方法来源，其原机器路径依赖在复现说明中明确列出。未重建当时搜索服务结果或模型生成过程，也未补造评审时间、暴露信息和专业经历。

[复现命令与依赖](04_复现与文件索引/复现说明.md)；[文件索引](04_复现与文件索引/文件索引.html)。最终执行状态、保护文件哈希和 ZIP 校验以同目录 VERIFICATION.json 与交付记录为准，避免把尚未执行的核验写成完成。

关键历史提交：4517f49（初始材料交付）、98398c6（显示修订）、4efa443 / 3820560（查证材料v1/v2）、78a80a9（v1返表）、8f3a006（v2）、f72795e（技术清理）、dc43d6b / b239940（v3原件及描述）、17a9792 / 2b751149（事后授权归档及探索性结果）。本次构建开始提交为2b751149615f1a895c72827ad3dfd1ba987189b0；最终归档提交号在交付消息中给出。
