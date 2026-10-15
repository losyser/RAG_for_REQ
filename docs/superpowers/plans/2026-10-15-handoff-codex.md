# 交接文档：Systems Engineering 稿件 4762284 小修（交给 Codex 继续执行）

- 交接时间：2026-10-15 11:20（CST）
- 截止日期：**2026-11-07**（已建议作者向编辑申请延期到 11-21，是否获批未知）
- 原始计划：`docs/superpowers/plans/2026-10-14-se-minor-revision.md`（Task 0–17，下文称"原计划"）
- 执行记录（ledger，含所有决策 `Ruling:`）：`.superpowers/sdd/2026-10-14-se-minor-revision/progress.md`
- Git：内层仓库 `D:\cooling_rag_multigranular\cooling_rag_multigranular`，分支 **`revision-se-4762284`**（从 `main@aab04d8` 切出）。最新提交为 `773982b`
- 论文目录（**不在 git 里**）：`D:\cooling_rag_multigranular\paper_wiley_submission_to_be_revised\`；原稿备份为 `paper_wiley_original_submission.tex` 和 `table_*_orig.tex`

> **先读这份文档，再读 ledger。原计划中有几处判断已被执行结果推翻（见 §3），以本文为准。**

---

## 0. 必读：环境与操作规则（每一条都曾实际踩坑）

1. **Python 只能通过包装脚本调用**：`cmd.exe /c "D:\cooling_rag_multigranular\cooling_rag_multigranular\run_py.bat <参数>"`。
   - 这个 bat 会清空被 Tribon 污染的 `PYTHONPATH`，设置 `PYTHONIOENCODING=utf-8` 和 **`OMP_NUM_THREADS=8`**（不设置的话 torch 和 faiss 会原生崩溃），并 cd 到项目根目录。
   - 下文用 `PY <参数>` 表示这条命令。
2. **不要通过 cmd.exe 执行带引号的 `python -c "..."`**，嵌套引号会被拆坏。代码写进 `D:\cooling_rag_multigranular\tmp\snip_xxx.py`，并在第一行加上 `import sys; sys.path.insert(0, ".")`，然后运行 `PY ..\tmp\snip_xxx.py`。
3. **加载 embedding 模型时一律用 CPU**（`set DEVICE=cpu&& ` 前缀，或者在代码里写 `device="cpu"`）。
   - 本机 GPU（RTX 5060 Laptop）加载模型时报 CUDA OOM，编码长文本时报 CUDA unknown error，不可用。
4. **一次只运行一个会加载 BGE-M3 的进程。** Windows 的提交内存已接近上限（35.5 GB / 39.7 GB，用户同时开着 ChatGPT、Trae 等程序），并发运行会出现 `0xC0000005` 访问冲突。不是代码问题。
5. **LaTeX 用 Windows 版 TeX Live 2025**：`D:\Program Files\texlive\2025\bin\windows\pdflatex.exe`（WSL 自带的 TeX 缺 stix2）。编译脚本见原计划 Task 17 Step 3。latexdiff 用 WSL 里的 `/usr/bin/latexdiff`。
6. **Windows Python 不走代理。** 需要下载文件时，在 WSL 里用 curl（WSL 已配置代理）。
7. **测试**：`PY -m pytest -q tests -p no:cacheprovider --deselect tests/test_grounding.py::test_load_evidence_text_map`。这个被排除的测试是既有的 PermissionError，与本次修改无关。交接时全部测试通过，只有 `tests/test_paper_tables.py` 是例外，它是一个**故意留下的 RED 测试**，见 H3。
8. **TDD**：每一处代码修改都要先写测试并看到它失败。每个任务结束时在 ledger 末尾追加一行 `Task <N>: complete (...)`；每个偏离计划的决定写一行 `Ruling: <决定> — <理由> — <如果判断错了的代价>`。
9. **禁止事项**：
   - 不得编造数字。论文里的数字只能来自 `data/search_results/exp_v4/paper_numbers.json` 及其生成的宏。
   - 不得声称 RAG"更正确"，也不得出现 eliminate、guarantee 之类的说法。
   - 不得新增未经核实的参考文献。
   - 不得删改 `_archive_preaudit_20261014/`。

---

## 1. 已完成的工作（均已提交）

| 原计划任务 | 状态 | 产出 |
|---|---|---|
| T0 环境与快照 | ✅ | `run_py.bat`；归档 `data/search_results/_archive_preaudit_20261014/`（旧结果、旧 KB v2、旧索引） |
| T1–T3 KB 出处审计 | ✅ | `data/processed/kb_audit/kb_provenance_audit.csv`（逐条决定和核实依据）；**`data/processed/evidence_units_v3_audited.jsonl`（1,208 条：L1 111 / L2 455 / L3 642；38 份文档；覆盖 91/183 个合法对）**；共删除 156 条、降级 55 条、修正出处 1 条 |
| T4 以 KB 为准的分级器 | ✅ | `grade_classifier.py`（`kb_index` 参数、`valid_citation_ids`、`kb_has_clause`）；`numeric_norm.py` |
| T5 管线插桩 | ✅ | 54 新增 `--rag-only`、T=0、计时；77 保存 `_evidence_values` 和 `_timing`；截断上限可由环境变量配置 |
| T6 全量重跑 | ✅（只差 Qwen RAG，见 H1） | 新的 RAG、no-RAG、随机检索、no-RAG Qwen 结果，以及 70b、71b、79、83、59（盲评和 H_hard） |
| T7 E1 基线 | ✅ | `exp_v4/e1_predictions.json`、`e1_pool.csv`（候选池 570 个对） |
| T8 专家工作簿 | ✅ 已生成，⏳ 等专家填写 | `data/expert_round2/expert_workbook.xlsx`，4 个表：S1 标注 120 条、S2 候选对 570 个、S3 盲评 50 条、S4 抽取核验 50 条；`expert_key.json` 为隐藏映射；评分脚本 `98` 已就绪 |
| T9 E5 泄漏检验 | ✅ | `exp_v4/e5_leakage.json` |
| T10 E3 | 🟡 只完成切分边界部分 | `exp_v4/sensitivity/boundary.json`；检索部分和端到端部分未做，见 H2 |
| T11 派生类型、冲突、路由 | ✅ | `exp_v4/routing_report.json`（含 `route_reasons`、`rule_validation` 30/30）；`derivation_validation_30.csv` |
| T12 并排对比候选 | 🟡 候选已生成 | `exp_v4/side_by_side_candidates.json`；表格未写，见 H5 |
| T13 图 | 🟡 只完成 Fig 2 | `paper/figures/fig2_pipeline.tex`（新增 Stage 2b），PDF 已复制到稿件目录；Fig 3 和 EA 合并图未做，见 H6 |
| T14 正文 | 🟡 约 40% | 见 §2 |
| T15 附录 A prompts | ✅ | `appendix_prompts.tex` |
| T16 回复信 | ❌ | 见 H8 |
| T17 终检 | ❌ | 见 H9 |

另外新增并已提交的修复（原计划中没有，都是执行中发现的）：
- `index_store.py`：用精确的 NumPy 内积检索（`NumpyFlatIP`）替代 faiss，结果完全等价。
- 模型目录 `D:/models/bge-m3/` 根部补齐了 4 个分词器文件（从 `onnx/` 子目录复制）。
- 生成环节 `max_tokens` 从 4000 提高到 8192；新增 `scripts/107_fill_truncated_sets.py` 补跑被截断的空结果集。
- `valid_citation_ids` 能容忍字符串或数字形式的引用字段。
- 注册表脚本 `100` 汇总时统一用 KB 校验的分级器重新计算所有臂。

---

## 2. 论文 `paper_wiley.tex` 的当前状态

**已改写**（数字一律用宏，宏定义在 `revision_numbers.tex`，由 `100` 生成）：
- 序言中已加入 `\input{revision_numbers.tex}`
- Intro：evidence unit 的定义、"为什么用检索而不用微调"一段（引 ovadia2024、soudani2024）；R2 指出的冗余句已删除
- Related Work：扩写 RE 和追溯小节（Gotel 的正向/反向追溯、SysML 关系、hey2025refsq、fuchss2025lissa、bonner2024incose、legesse2025ai4se）；新增 Graph/Ontology-Based Retrieval 小节
- `paper_bibliography.bib` 已追加 8 条已核实的条目
- Methods：
  - KB 描述，含**审计的如实披露**
  - 标注流程（LLM 辅助加作者抽查，κ 引用 `sec:tag_reliability`）
  - 精确内积检索
  - Stage 2b 证据选择（每条候选只展示前 300 字）
  - Stage 3 和 Stage 4 的截断上限
  - 以 KB 为准的分级
  - 派生类型与 SysML 关系、冲突检测与优先级规则、复核路由
  - GPT-5.5 网页生成 + E5 泄漏数据
  - 合成数据与歧义处理
  - Implementation：deepseek-flash、硬件、CPU、计时
- 新表：`table_eu_example.tex`、`table_kb_composition.tex`（由 `100` 生成）、`table_transfer.tex`
- Discussion 新增三个小节：Review Routing（引 `table_routing.tex`，**该文件尚未生成**）、Choice of Domain and Transfer、Threats to Validity and Limitations（已替换原 Limitations）
- 附录 A：`\appendix \input{appendix_prompts.tex} \input{appendix_sensitivity.tex}`（**后者尚未生成**）

**尚未改写，仍是原稿内容和旧数字，必须重写**：
- 摘要；Significance and Practitioner Points
- Methods 中的 Experimental Arms 表（仍写着 deepseek-v3）、Random-Retrieval Ablation 中的"1,364-unit KB"、Evaluation Metrics、Measurement Bias Analysis
- **整个 Results 一节**（第 832–1237 行附近）
- Discussion 的前三个小节（Traceable Requirement Content……、Disentangling……、Why Conventional Evaluation Methods Fail……）
- Conclusions；Data Availability（需要 Zenodo 新版本的 DOI）

**正文中引用了但宏文件里还没有的宏**（必须由 H3 生成，否则无法编译）：
`\SelSelectedMean \SelRetrievedMean \LeakMaxCos \LeakMedCos \LeakKBNNCos \LeakLCSMax \LeakNumOR \StageOnePairsMean \StageOnePairsMin \StageOnePairsMax \StageOneFallback \EncCPUms \TStageOne \TRetrieval \TSelection \TExtraction \TGeneration \TTotal \TTotalMin \RouteConfirmTierB \RagNShalls \RouteSpot \RouteOpen \RouteAdj \RouteVerify \ExpertNtag \KappaComp \KappaIntent \KappaPair \QwenRagGradeXPct`
（H3 完成后用 H9 Step 2 的脚本自动核对，以脚本结果为准。）

---

## 3. 关键事实与已被推翻的原计划判断（写作时必须遵守）

### 3.1 执行中发现、必须在回复信中主动说明的问题

1. **KB 出处问题**（原计划 §0）：
   - ISO 8861 被误标为冷却系统标准，实际是机舱通风标准。
   - IACS UR M3 被误标，实际内容是调速器与超速保护。
   - SOLAS II-1/26 被引作"冷却"条款，实际 Reg. 26 是 General；`E-SOLAS-COOL-001` 是编造的内容。
   - CCS"第 4 篇第 3 章"被误标，CCS Part 4 是电气部分。
   - 108 条单元由 LLM 起草，**起草所针对的缺口是通过分析测试需求确定的**（`scripts/55`、`56`）。
   - 以上单元均已删除。
2. **原稿所有实验中的稠密检索实际上失效**：`D:/models/bge-m3` 根目录缺少分词器文件，所有中文句子都被切成同一个未知词，嵌入向量相同。6 月归档的索引中，1,364 条向量只有 125 个互不相同。所以原稿的"混合检索"实际上近似于只用 BM25。已修复，并有回归测试 `tests/test_embedding_model_sanity.py`。
3. **`deepseek-chat` 现在解析到 `deepseek-flash`**，deepseek-v3 已下线，API 只提供 deepseek-flash 和 deepseek-v4-pro。因此**所有臂都在 2026-10 用 deepseek-flash 重新生成**。原稿那 30 条非盲 spot-check 评的是旧版 no-RAG 的输出，**已不能代表现在报告的基线**，改用专家工作簿 S3 的盲评。Stage 3 抽取精度要用 S4 重新核验，旧的 P 77.5% / R 86.1% 作废。
4. 6 条 RAG 和 5 条随机检索的结果集因输出被截断为空，已用 `max_tokens=8192` 补跑（只补空结果集，证据和抽取值与原来相同）。

### 3.2 原计划中被证伪的判断

- ❌ 原计划说"原稿的 CCS Tbl 3.9.2.2.8 条款号是错的"——**这个判断本身是错的**。CCS 2025 确有表 3.9.2.2.8（P1519，柴油机部件液压试验，与 IACS UR M72 一致），KB 中有对应单元 `L1-CCS2025-表3.9.2.2.8*`。真正的问题只在于适用的部件范围。**回复信不得把它说成作者的错误。**
- ❌ "GPU 对比 CPU 的编码耗时"：GPU 不可用，只报告 CPU 数据（64.2 ms/查询，见 `encode_latency.json`）。

### 3.3 新结果（审计后的 KB、修复后的嵌入、deepseek-flash）与原稿对比

| 指标 | 新结果 | 原稿 | 写作要求 |
|---|---|---|---|
| RAG shall 数 | 513；A 1 / B 73 / C 439 / **X 0**（CI 0–0.7%） | 286；X 0 | 核心结论成立 |
| RAG 引用率 | 98.6% | 99.3% | |
| RAG L1 引用率 | 21.6% | 38.5% | |
| RAG A+B | 14.4% | 38.4% | |
| no-RAG | 295；**X 204（69.2%**，CI 63.7–74.1） | 57.0% | 核心结论成立且更强 |
| 随机检索 | 485；A 2 / B 42 / X 0；L1 9.3%；A+B 9.1% | X 0；A+B 19.1% | **"语义检索使 A+B 翻倍"不再成立**（14.4 对 9.1，约 1.6 倍）；L1 引用率 21.6 对 9.3 |
| Grade C 构成 | 证据有但无精确值 351（占 C 的 80.0%）、定性 81、无证据 7 | | |
| 后验核查 RAG | 140 条数值型 shall，支持 90.0%，冲突 1 条（0.7%），数值级支持 95.1% | | 冲突那 1 条是 KB 数据错误，见下 |
| 后验核查 no-RAG | 204 条，支持 4.9%，冲突 3 条（1.5%），无法核验 92.2% | 冲突 8.9% | 原稿冲突表 (a)(b) 需按新数据重写 |
| 配对冲突率 | n=34，0.74% 对 1.96%，**p = 0.56，不显著** | p = 0.0028 显著 | **删除"显著"的说法** |
| **H_hard** | RAG 1.46% 对 no-RAG 0.10%，**p = 0.026，RAG 显著更高** | 不显著 | 必须如实报告，用 `hhard_contradiction_analysis.json` 解释：RAG 可核查的声明是 no-RAG 的 3.3 倍（915 对 273）；16 条 RAG 矛盾中有 9 条数值是原样摘自所引厂家文件，矛盾来自不同机型、不同来源之间的差异；1 条来自 KB 自身的数据错误（`E-HT-COMP-036` 中的"−100°C"）；其余 7 条是定性声明 |
| **盲评成对比较（Qwen）** | RAG 胜 64、no-RAG 胜 51、平局 125 | no-RAG 胜 107 对 26 | **"表面质量指标偏向基线"的论点作废**，改为"两臂相当或 RAG 略优" |
| no-RAG（Qwen） | 154；X 57（37.0%） | 41.7% | |
| RAG（Qwen） | **尚未重跑完**，见 H1 | 21.3% | |
| 路由（RAG） | OPEN_ITEM 317、ENGINEER_CONFIRM 91（其中 tier-b 73）、SPOT_CHECK 1；冲突检出 0 | — | |
| 派生类型（RAG） | Deferred 317、Direct 76、Unsupported 7（均为定性）、Synthesized 4、Derived 5；规则核验 30/30（25 条为 Deferred） | — | **人工核验是 Claude 代做的，需作者确认** |
| E5 泄漏 | 最大余弦 0.816，KB 最近邻中位数 0.903；最长公共子串 11 字；60 条需求均不含数字 | — | 没有泄漏迹象 |
| E3 切分边界 | EU 原子切分 0%；固定窗口 128/256/512 字（overlap 0）分别为 76% / 28% / 16% 被切开（样本：25 个"条件+数值"句） | — | |
| 计时（秒/需求） | Stage 1 0.93、检索 0.23、选择 6.05、抽取 9.13、生成 9.67 | — | |
| Stage 1 | 平均 4.17 个对（2–9），回退 0 次；检索平均 16.5 条，选择后平均 10.9 条 | — | |

**核心论点（写作主线）**：cite-or-defer 约束使 RAG 的 Grade X 为 0（no-RAG 为 69%），且与检索质量无关（随机检索同样为 0）。语义检索主要提高的是**法规（L1）来源的引用比例**。可溯源性不等于正确性：H_hard 和盲评都表明，两臂在质量指标上相当，RAG 并不更正确。可溯源性的价值在于让每个数值都**可以被核查**，以及把核查工作量集中到复核路由上。

### 3.4 结论保持策略（作者要求：小修阶段维持原结论，2026-10-15）

原则：**核心结论保持不变，只更新数字并调整次要论据的措辞。不得保留旧数字，也不得挑选指标来"恢复"旧数字。** 旧结果依赖带假出处的 KB 单元和失效的嵌入，公开代码和 KB 无法复现它们。

| 原稿结论 | 新证据 | 修订稿写法 |
|---|---|---|
| 引用率 99.3% 对 0% | 98.6% 对 0% | 保持，只换数字 |
| 头条：Grade X 0% 对 57% | 0% 对 69.2% | 保持，结论更强 |
| 0% 由 cite-or-defer 约束决定，与检索无关 | 随机检索 Grade X 也为 0% | 保持 |
| 语义检索提高有用性（原稿称"A+B 翻倍"） | A+B 14.4% 对 9.1%（1.6 倍）；L1 引用 21.6% 对 9.3%（2.3 倍） | 写成"法规来源引用比例提高到两倍以上，带引用数值的比例也更高"；**不得再写"A+B 翻倍"** |
| Grade C 主要是有证据时的暂缓 | 80.0% | 保持 |
| RAG 的数值忠实于来源 | 数值级支持 95.1%；唯一的冲突来自 KB 数据错误 | 保持 |
| 基线数值无法核查 | no-RAG 92.2% 无法核验 | 保持，并作为主要论据（替代原来的"冲突"论据） |
| 常规指标测不出可溯源性 | 盲评两臂相当（64/51/125）；H_hard 上 RAG 更高，因为可核查的声明多 3.3 倍，矛盾多数是来源之间的差异 | 论点保持；把"基线更受偏好"改为"两臂相当，指标区分不了有出处和没出处" |
| 冲突率显著差异（p = 0.0028） | p = 0.56 | 删除显著性的说法，只保留描述性数据 |
| spot-check 44.8% 有误 | 不再适用（旧模型的输出） | 用 S3 盲评结果替代；结果不利也要如实写 |

回复信口径：作者自查发现了 KB 出处问题、嵌入模型的分词器缺陷以及服务商更换模型版本，已全部修正并重跑；**核心结论（cite-or-defer 使 Grade X 为 0，无约束基线为 69%；常规指标测不出可溯源性的差别）保持不变**；随附新旧数字对照表。

---

## 4. 待办任务（按依赖顺序；H 表示交接任务）

### H1 完成 Qwen RAG 臂（进行中）
- 交接时 77q 正在后台运行（`logs/rerun_postaudit_20261015_1057.log`，第 11/60 条；后台命令跑完后会自动执行 `107 rag_qwen`）。
- 检查是否完成：`rag_v4_qwen_results.json` 的修改时间是 10-15 并且有 `_evidence_values`；日志里出现 `all steps done`；再运行 `PY scripts/107_fill_truncated_sets.py rag_qwen`，确认输出 `still empty: []`。
- 如果没跑完或进程已不在，重新执行：`PY scripts/96_rerun_postaudit.py 10`，然后 `PY scripts/107_fill_truncated_sets.py rag_qwen`。
- 验收：运行 `PY scripts/100_paper_numbers.py`，`paper_numbers.json` 里 `rag_qwen.n_sets == 60`，并在 ledger 中记录 Grade X 和 A+B。

### H2 E3 敏感性的剩余部分（原计划 Task 10 Step 6–8）
1. **模型下载未完成**：`D:/models/mpnet-multilingual/model.safetensors` 截至 2026-10-15 11:40 为 771,738,096 字节（后台续传循环已结束，**文件仍不完整**），完整大小为 1,112,201,288 字节，sha256 为 `b5722100700c48b74c9c199c5f39ff9493c94d1497f719e791d4bc3861d7714a`。这个文件仍不完整，需要继续续传。在 WSL 中续传：
   ```bash
   cd /mnt/d/models/mpnet-multilingual; B=https://huggingface.co/sentence-transformers/paraphrase-multilingual-mpnet-base-v2/resolve/main
   until [ "$(stat -c %s model.safetensors)" -ge 1112201288 ]; do curl -sSL -C - -m 900 -o model.safetensors "$B/model.safetensors"; done; sha256sum model.safetensors
   ```
   哈希必须一致。
2. 下载完成后，**逐个**运行（不得与其他加载模型的进程并发）：
   - `PY scripts/99_retrieval_sensitivity.py --part retrieval`。脚本会自动在 CPU 上构建 `data/indexes/evidence_units_mpnet`。⚠️ `_searcher("mpnet")` 中 `build_index(..., device=cfg.model.device)` 用的是 `.env` 里的 `DEVICE=cuda`，**必须改为 `device="cpu"`**，或者在命令前加 `set DEVICE=cpu&& `。
   - 然后依次运行 `--part e2e --variant vector_only`、`bm25_only`、`embed_mpnet`、`trunc_1200`（每个约 1–2 小时，调用 DeepSeek API）。
   - 最后运行 `--part summary`。
3. 编写 `appendix_sensitivity.tex`，内容为 10 个检索变体的检索层指标表和 4 个端到端变体的分级表。建议在 H3 的 `108_paper_tables.py` 中生成。

### H3 生成全部宏与表格（新增脚本 `scripts/108_paper_tables.py`）
- 已存在一个 **RED 测试 `tests/test_paper_tables.py`**（未提交），它约定了以下接口：
  - `build_macros(N: dict) -> dict[str, value]`：缺失的数据给 `None`（输出为 n/a）；宏名只能含字母。
  - `table_grade(N) -> str`：输出带 `\label{tab:grade}`、单元格格式为 `10.0\% (1)` 的表格。
- 实现 `108`。在 `100` 的 `main()` 末尾调用它：把 `build_macros(N)` 合并进写入 `revision_numbers.tex` 的宏字典（现在 `100` 只写了 KB 相关的宏），并生成以下表格：
  - `table_descriptive.tex`、`table_grade.tex`、`table_ablation.tex`（三臂对比）、`table_posthoc.tex`、`table_crossllm.tex`、`table_blind_eval.tex`（数据来自 `credibility_v4/eval_v3.json` 的 `blind_quality.aggregate`）、`table_hhard.tex`
  - `table_routing.tex`（数据来自 `routing_report.json`）
  - `table_e1.tex`、`table_blind_correct.tex`、`table_stage3.tex`（这三张依赖专家结果，缺失时输出 n/a）
  - `table_sensitivity.tex`、`appendix_sensitivity.tex`
- 宏的数据来源：`paper_numbers.json`；`exp_v3/rag_v3_results.json`（`_n_pairs`、`_retrieved_ids`）；`encode_latency.json`；`e5_leakage.json`；`routing_report.json`；`hhard_contradiction_analysis.json`；`credibility_v4/eval_v3.json`；`expert_scores.json`；`e1_stage1_scores.json`；`stage3_accuracy_subset.json`；`regrade_preaudit_with_v3kb.json`。
- 计时宏：`TTotal` 为五个阶段之和，`TTotalMin` 为 `TTotal × 60 / 60`（分钟）。
- 验收：`test_paper_tables.py` 通过；全部测试通过；H9 Step 2 的未定义宏检查输出为空。

### H4 重写 Results 一节和 Discussion 的前三小节
- 按 §3.3 的写作主线，用宏书写。建议的小节结构：
  1. Descriptive
  2. Numeric Provenance Grades，含 Grade C 构成
  3. Retrieval Contribution，即随机检索消融：如实写 A+B 14.4 对 9.1、L1 21.6 对 9.3
  4. Stage-1 Mapping Accuracy（`\label{sec:stage1}`，E1）
  5. Tagging Reliability（`\label{sec:tag_reliability}`，E2）
  6. Correctness Checks：后验核查、配对冲突（不显著）、H_hard 及其分析、**盲评（S3）**；原 spot-check 只在一句话中作为历史说明，或者删除
  7. Stage-3 Extraction Accuracy（`\label{sec:stage25}`，S4）
  8. Retrieval Sensitivity（`\label{sec:sensitivity}`，E3）
  9. Cross-Generator Robustness（`\label{sec:crossllm}`）
  10. Leakage Check（`\label{sec:leakage}`，E5）
  11. KB Audit（`\label{sec:audit}`）：审计前后对照，数据用 `regrade_preaudit_with_v3kb.json`——旧 RAG 输出用 v3 KB 重新分级后为 A 1 / B 28 / C 176 / X 81
  12. 并排对比（H5）
  13. Native import（H6）
- 正文中已引用的 label：`sec:audit`、`sec:tag_reliability`、`sec:leakage`、`sec:sensitivity`、`sec:stage25`、`sec:crossllm`、`sec:limitations`、`sec:routing`、`sec:transfer`、`tab:conflicts`（冲突表按新的后验核查结果重写，只保留可核实的条目；tier-b 定义要与路由一节保持一致）、`fig:sysml_arch`、`app:prompts`。
- Discussion 前三小节：删除"Why Conventional Evaluation Methods Fail……"中"基线更受偏好"的论证，改写为：表面质量与 H_hard 不能区分"有出处"和"没有出处"，两臂在这些指标上相当。
- 同时改写：摘要（≤200 词，按原计划 14.1）、Practitioner Points、Methods 中的 Experimental Arms 表（改为 deepseek-flash）、Random-Retrieval Ablation 中的"1,364"（改为 `\NKBUnits`）、Evaluation Metrics、Measurement Bias Analysis、Conclusions。

### H5 并排对比表（原计划 Task 12，已有决定）
- **案例 1 = OR008**（温控阀设定值）：RAG 给出 `80°C`，引用 `E-LT-PRESS-003/005`（L2）；no-RAG 给出"例如 70℃~85℃"，没有引用。说明：两者都合理，差别在于可追溯性。
- **案例 2 = OR010**（防冻液浓度）：no-RAG 给出"典型值 30%~60%"，超出 MTU A001065 第 16 页（`E-SYS-WATER-006`，L2）规定的 40%–55% 区间。RAG 在补跑后对 OR010 生成了 6 条 shall，全部为 C 级，需要查看其中关于防冻液的那一条。表注要写明"冲突依据的是厂家规范，不是法规"。
- 写入 `table_side_by_side.tex`（6 列，见原计划 Task 12 Step 3），中文译为英文，**数值不得改动**。
- 从正文中删除 `\input{table_req_case.tex}` 和 OR-001 那张图 `fig:req_diagram`：OR-001 的 Grade A 原本引用的是已删除的单元，这两处内容都已失效。

### H6 图（原计划 Task 13 Step 2–4）
- **新 Fig 3** `paper/figures/fig3_sysml_arch.tex`（TikZ）：BDD 加上从 H5 两个案例中选取的 ER，画出 «satisfy» 指向 block、«trace» 指向证据单元 ID、«deriveReqt» 从 OR 指向 ER；label 为 `fig:sysml_arch`。编译后复制到稿件目录。
- **EA 合并图**：先运行 `PY scripts/92_export_ea_native_xmi.py --sets OR008 OR010 <另选一个含 Grade B 的 OR>`。原计划 Task 11 Step 7 要求给 92 加上路由和派生类型标签，**这一步还没做**，需要先按 TDD 完成。然后由**用户**在 EA 中导入并导出 SVG，再转成 PDF 并裁边，生成 `fig4_ea_revised.pdf`。正文中删除原来两个 EA figure 块，换成一个 `fig:ea`，并全文替换对应的 `\ref`。
- 用户完成之前，可以先用文字说明代替，但**不得保留旧截图**，因为旧截图对应的是旧数据。

### H7 专家结果回收（外部依赖）
- 用户把 `data/expert_round2/expert_workbook.xlsx` 发给专家，收回后保存为 `expert_workbook_filled.xlsx`。
- 运行 `PY scripts/98_score_expert_workbook.py data/expert_round2/expert_workbook_filled.xlsx`，然后运行 `100`，再重新编译。
- 根据实际结果补写 E1、E2、S3、S4 的**解读句**。不得预设结论；结果不利也必须如实写。

### H8 回复信 `response_to_reviewers.tex`（原计划 Task 16）
- 按原计划 Task 16 的结构写。致编辑信的第一段要**主动说明 §3.1 的四项问题**和 §3.3 中变化较大的结论（配对冲突不再显著、H_hard 方向相反、盲评结果、检索带来的增益变小）。
- 逐条回复审稿意见，对应关系见原计划的"审稿意见 → 任务映射"表。
  - R1-4.3：写网页界面、memory 状态没有记录，引用 E5 的数据。**如果用户能确认当时的设置，再改写这一句。**
  - R1-4.7：写 CPU 数据，说明 GPU 不可用的原因。
  - R1-6.1：写"部分采纳"，引用 `tab:transfer`。
  - R2 的切分问题：引用 boundary 分析和 E3。
  - R2 的冲突问题：说明优先级规则；冲突检出为 0；后验核查中的冲突案例。

### H9 终检（原计划 Task 17）
1. **过时数字扫描**：原计划 Task 17 Step 1，扫描列表追加 `57.0`、`44.8`、`0.0028`、`107`、`deepseek-v3`、`FAISS`。
2. **未定义宏检查**（新增）：
   ```bash
   cd /mnt/d/cooling_rag_multigranular/paper_wiley_submission_to_be_revised
   grep -oh '\\[A-Z][A-Za-z]*{}' paper_wiley.tex table_*.tex appendix_*.tex | sort -u | tr -d '{}\\' > /tmp/used.txt
   grep -o 'newcommand{\\[A-Za-z]*}' revision_numbers.tex | sed 's/newcommand{\\//; s/}//' | sort -u > /tmp/def.txt
   comm -23 /tmp/used.txt /tmp/def.txt
   ```
   期望输出为空。如果正文中有不带 `{}` 的宏用法，也要一并核对。
3. 禁用措辞扫描、编译（0 error、没有 undefined 引用）、latexdiff 标记版、全部测试通过：原计划 Task 17 Step 2–5。
4. 提醒用户在 Zenodo 发布新版本（审计后的 KB、审计表、新结果），并把新 DOI 写进 Data Availability。

### H10 收尾
- 对整个分支做一次代码审查（命令：`git diff main...revision-se-4762284 -- cooling_rag_mg scripts tests`）。
- 更新记忆文件 `/home/yan/.claude/projects/-mnt-d-cooling-rag-multigranular/memory/project_minor_revision.md`，写入 §3 的结论。

---

## 5. 需要用户（作者）完成或确认的事项

1. 向编辑申请延期（邮件模板见原计划 Task 0 Step 4）。
2. 把专家工作簿发给外部专家（D4：如果找不到外部专家，可以请 Feihui Yuan）。专家工作量约 6–8 小时。
3. GPT-5.5 当时的使用方式：是否开了 memory，以前是否在 ChatGPT 里粘贴过 KB 内容。
4. 复核 `kb_provenance_audit.csv` 中 LATE 组标为 KEEP 或 FIX_SOURCE 的行（Claude 已核对原文）。另外，ABS、PRS、HY/T 这几份原文不在仓库中，相关单元已标注"未独立复核"。
5. 复核 `derivation_validation_30.csv` 的人工判定（Claude 代做，30/30 一致）。
6. 复核 `data/processed/taxonomy_transfer.csv` 中 45 个方面 × 5 个系统的适用性判断（Claude 起草）。
7. 在 EA 中导入 XMI 并导出合并图（H6）。
8. Zenodo 新版本。
9. 如有真实需求可提供（D6，10-24 之前），可以补做 E6。
