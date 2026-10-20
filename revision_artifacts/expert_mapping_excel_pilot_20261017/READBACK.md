# Excel试做读回支持

专家只需填写并回传整个.xlsx。网页和Excel二选一，同一任务不双填。

协调者使用 tools/expert_mapping_review/excel_pilot.py WORKBOOK --package 原calibration_2_sources.pilot.json路径 --output 全新JSON路径。脚本依赖openpyxl（本机捆绑Python已验证）；只读工作簿，拒绝覆盖输出。

本轮实际支持：保留专家代号、源ID/配对ID、中文意见与换行、候选四态、独立首判、遗漏补充、计时、中断、完成声明、候选暴露状态、来源哈希与协议版本。空白与显式“未答”在raw字段中区分，映射到网页字段时均为unanswered，绝不当负例。未完成补充行保留为pending_pair_rows。输入ID/版本/原文/完整目录变化及非法值会报错。

web_answer_fields提供与网页对应的答案字段；扩展字段保存候选逐行意见、计时和暴露声明。输出是独立导入记录，不是网页备份，不能通过“打开旧审查”导入，且不创建/覆盖网页任务。存在流程缺项时列出issues；pilot始终gold_ready=false，不评分。

Excel工作流先完成两源首判再看共享候选页，区别于网页逐源解锁。collection_mode和stage_order明确记录这种差异；阶段顺序、候选暴露为专家自报，不构成强盲法或首判不可修改的证明。

验证：8项隔离测试通过；本机Microsoft Excel成功打开、下拉合法/非法值校验、命名配对列表、公式重算、保存后重开及实际值读回通过。5页已渲染逐页检查，列宽/换行/冻结/目录完整性已核验。模板输入格仍空白。测试只修改临时副本。

修改前检查点d66defe。未更改论文、原实验数据、原工作簿或网页专家答案；没有新模型调用或正式抽样。
