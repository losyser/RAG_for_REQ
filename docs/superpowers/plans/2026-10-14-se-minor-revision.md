# Systems Engineering 稿件 4762284 小修 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在截止日期前提交修改稿（2026-11-07，已申请延期作为缓冲），并做到三点：①逐条解决两位审稿人提出的 27 个问题；②修正自查发现的 KB 出处问题；③让论文里的每一个数字都能由脚本从新一轮运行结果中复现。

**Architecture:** 按依赖顺序分四个阶段，后一阶段只依赖前一阶段的产出。
- **阶段 A（地基）**：KB 出处审计 → 生成审计后的 KB（v3）→ 改用以 KB 为准的分级器 → 全管线重跑，并在重跑过程中顺带计时，供 R1-4.7 使用。
- **阶段 B（新证据）**：各项新实验。部分实验需要人工标注，标注任务打包成一份专家工作簿（xlsx），一次发出。
- **阶段 C（图表与正文）**：重做图表，按审稿意见逐条修改正文。
- **阶段 D（交付）**：回复信、latexdiff 标记版、过时数字扫描、编译。

论文中的数字一律只从 `paper_numbers.json` 取，这个文件由脚本生成。

**Tech Stack:** Python 3（Windows conda 环境 `cooling_rag_env`：torch 2.11+cu128、sentence-transformers 5.5.1、faiss、rank_bm25、scipy、sklearn）；DeepSeek API（`deepseek-chat`）；Qwen API（`qwen-max`）；BGE-M3（`D:/models/bge-m3`）；TeX Live 2025（Windows）；latexdiff 1.3.1a（WSL）；Enterprise Architect（用户本机）。

**Spec:** 审稿意见 `D:\cooling_rag_multigranular\SystemsEngineering.md`（用户粘贴过的完整版，以对话中的版本为准，其中 R1-4.6 是完整的）；修改对象 `paper_wiley_submission_to_be_revised/paper_wiley.tex`。

---

## Global Constraints

- **唯一的修改对象**是 `paper_wiley_submission_to_be_revised/paper_wiley.tex` 及同目录下的 `table_*.tex`。`paper/paper_els.tex` 和中文 MD 冻结，不再同步。
- **Python 统一通过** `D:\cooling_rag_multigranular\cooling_rag_multigranular\run_py.bat` 调用（由 Task 0 创建）。原因：系统 `PYTHONPATH` 被 Tribon 污染，必须清空；还需要 `PYTHONIOENCODING=utf-8`。WSL 中的调用格式为 `cmd.exe /c "D:\cooling_rag_multigranular\cooling_rag_multigranular\run_py.bat <参数>"`。下文写 `PY <参数>` 即指这条命令。
- **多行或带引号的 Python 片段不得用 `PY -c "..."` 执行**，因为 cmd.exe 会拆坏嵌套引号（已实测失败）。一律把代码写入 `D:\cooling_rag_multigranular\tmp\snip_<任务号>.py`，再执行 `PY ..\tmp\snip_<任务号>.py`。run_py.bat 会先 cd 到项目根目录，所以片段里的相对路径都以项目根目录为基准。下文所有 `PY -c` 写法都按这条规则执行。
- **LaTeX 统一用** `D:\Program Files\texlive\2025\bin\windows\`。WSL 自带的 TeX 缺少 `stix2.sty`，不能用。
- **重跑中所有 LLM 调用一律 T=0**。v3 的证据选择步骤 `generate_rag_v3` 默认 T=0.2，重跑时必须显式传 `temperature=0.0`。
- **KB 以审计后的 `data/processed/evidence_units_v3_audited.jsonl` 为准**。`evidence_units_v2.jsonl` 只作为审计前快照保留，不得修改。
- **覆盖任何结果文件之前**，必须先把旧文件归档到 `data/search_results/_archive_preaudit_20261014/`（Task 0）。
- **论文只主张可溯源性（traceability），不主张正确性（correctness）。** 不得出现 "eliminates hallucination"、"guarantee"、"RAG is more correct" 之类的说法。
- **新增引文只能用本计划 Task 14.4 中已核实的 BibTeX**，不得自行补造。
- **不确定的事实（用户尚未回答）一律按 §决策门 的默认值执行**，并在回复信里如实写明。
- **数字一律来自 `data/search_results/exp_v4/paper_numbers.json`**（Task 6 生成）。禁止手算后直接写进正文。
- prompt 原文是中文。附录给出英译，并注明 "English translation of the original Chinese prompt"。

## 决策门（用户未答复时的默认值，执行时不再回头改计划）

| ID | 问题 | 默认值 | 截止日 |
|---|---|---|---|
| D1 | 108 条 `KB_DRAFT_v1` 单元 | **全部删除** | — |
| D2 | LATE 组单元（S60 以后的编号或无编号，共 56 条）中无法对照原文核实的 | **删除** | — |
| D3 | 被标为 L1 的厂家资料（project_guide、installation_guide、engine_manual） | **降为 L2** | — |
| D4 | 外部专家人选 | 10-20 前没有确定外部专家，就改由**合作者 Feihui Yuan（外高桥船厂，未参与 KB 构建）**标注，并在 Threats 中写明"独立但非外部" | 10-20 |
| D5 | 延期 | 10-15 发邮件申请延到 11-21；无论是否获批，都按 11-07 推进 | 10-15 |
| D6 | 真实需求（R1-4.4） | Feihui Yuan 在 10-24 前提供 ≥10 条脱敏需求就跑 E6，否则只做论证 | 10-24 |
| D7 | 滑油试点（R1-6.1） | **不做**全量试点；改做 taxonomy 可迁移性分析（Task 14.8），回复信写"部分采纳"并说明理由 | — |
| D8 | GPT-5.5 的使用方式（R1-4.3） | 按用户答复，从 Task 14.3 的两套文字中选一套；用户未答复则用"网页界面"版 | 10-17 |
| D9 | 第二专家盲评 | 在 KB 清洗后的新 RAG 输出上**重新做 50 条盲评**（工作簿 S3），并在论文中如实报告 | — |
| D10 | 标注流程（R1-4.1） | 按代码事实写：LLM 辅助加作者抽查，无系统复核记录；用 E2 的 κ 补足 | — |

## Review Focus

1. **模型输出了 KB 中不存在的 kb_id，或把引用写成字符串**（qwen-max 已经出现过）。期望：KB 中不存在的 ID 视为未引用；数值判据没有任何有效引用时判为 X；字符串中能解析出合法 ID 的照常采信。→ Task 4 有对应测试。
2. **KB 中标为 L1、但记录里没有条款定位信息的单元**。期望：判为 B，不判 A，因为 A 要求 KB 记录本身带条款号，而不是模型自己声称的 has_clause。→ Task 4 有对应测试。
3. **重跑后 Grade X > 0，或某一臂 0 条 shall**。期望：统计脚本不崩溃（分母为 0 时输出 null），X 的数量如实进入 `paper_numbers.json`，不能被过滤掉。→ Task 6 有对应测试。
4. **专家工作簿中有空白、拼写错误或非法取值**。期望：评分脚本跳过这些行并报告跳过数量；κ 只在两人都给出合法值的条目上计算。→ Task 8 有对应测试。
5. **数值比对时的格式差异**：`70–85°C` 与 `70-85 ℃`、`1.5倍` 与 `1.5×`、全角数字等。期望：派生类型判定在归一化之后再比对，不会把 Direct 误判为 Derived。→ Task 11 有对应测试。

---

## 审稿意见 → 任务映射（覆盖检查表）

| 意见 | 解决方式 | 任务 |
|---|---|---|
| R1-1.0 摘要难读 | 重写摘要：短句；先定义术语再出数字 | 14.1 |
| R1-1.1 "main DeepSeek implementation" | 改为 "the LLM-based workflow (instantiated with DeepSeek-V3)" | 14.1 |
| R1-1.2 / 2.1 unit 含义不清 | 摘要和 Intro 首次出现处给出 evidence unit 的定义，正文加样例框 | 14.1、14.2 |
| R1-2.2 微调 SLM 与 RAG 的对比 | Intro 新增一段，引 Ovadia 2024、Soudani 2024 | 14.2 |
| R1-3.1 RW 太简略、加 Graph/Ontology RAG | 扩写 RE 和追溯小节，新增 Graph/Ontology RAG 小节 | 14.4 |
| R1-4.1 标注流程 | 按事实重写标注流程 | 14.3 |
| R1-4.2 外部 κ | E2：120 条单元由外部或独立专家盲标，计算 Cohen's κ；新增 Threats 小节 | 8、14.9 |
| R1-4.3 GPT-5.5 API 还是网页、泄漏 | 如实说明使用方式；E5 泄漏统计 | 9、14.3 |
| R1-4.4 合成数据、人类歧义 | 论证 + 歧义处理数据 + E6（视 D6 而定） | 14.3、14.10 |
| R1-4.5 prompts | 附录 A：全部 prompt 英译 | 15 |
| R1-4.6 准确率测试 / F1 | E1：Stage 1 映射 P/R/F1 与三种基线；输出层盲评正确率（D9） | 7、8 |
| R1-4.7 CPU/GPU、延迟 | 重跑时分阶段计时，另测 CPU 与 GPU 的编码耗时 | 5、6、10 |
| R1-4.8 MBSE 图 | 新增 Fig 3：SysML BDD/IBD，带 «satisfy» 和 «trace» | 13 |
| R1-5.0、6.0、7.0 | 无需修改，回复信致谢 | 16 |
| R1-6.1 其他系统 | 部分采纳（D7）：可迁移性分析 + 详细的后续工作 | 14.8 |
| R1-6.2 为什么选冷却水系统、迁移挑战 | Discussion 新增小节 | 14.8 |
| R1-6.3 tier-b 证据怎么处理 | 复核路由策略、XMI 标签、各类数量统计 | 11、14.7 |
| R2 删除冗余句 | 删除 | 14.2 |
| R2 Fig 4/5 冗余 | 两张 EA 图合并为一张；删除旧 Fig 3 和表 6（内容重复） | 13 |
| R2 并排对比 | 新表：两个案例的 RAG 与 no-RAG 并排对比 | 12 |
| R2 直接需求与派生需求 | 派生类型（Direct、Synthesized、Derived、Deferred、Unsupported），映射到 SysML 关系 | 11、14.6 |
| R2 权威文档冲突 | 优先级规则 + 确定性冲突检测 + P0 审计实例 | 11、14.6 |
| R2 chunk、overlap、embedding、BM25 敏感性 | E3：切分边界分析、截断变体、融合与参数变体、替代 embedding 模型 | 10 |
| R2 AI4SE/SE4AI、ARDoCo 引文 | Hey 2025、Fuchß 2025、Bonner 2024、Legesse 2025 | 14.4 |
| 自查 P0：KB 出处 | 审计、删除、降级，以 KB 为准分级，重跑，在回复信中主动说明 | 1–6、16 |
| 自查：Methods 与代码不一致（漏写证据选择步骤、T=0.2、截断上限、"CPU"） | Methods 如实补写 | 14.3 |

---

## 文件结构

**新建**
- `cooling_rag_multigranular/run_py.bat`：Windows Python 包装脚本
- `cooling_rag_mg/kb_provenance.py`：单元出处分组、自动标记、建议动作
- `cooling_rag_mg/numeric_norm.py`：数值抽取与归一化（Task 11 和 Task 4 共用）
- `cooling_rag_mg/review_routing.py`：派生类型、冲突检测、复核路由
- `cooling_rag_mg/retrieval_variants.py`：检索变体（模式、权重、k₀、k）
- `scripts/94_kb_provenance_audit.py`：生成审计表
- `scripts/95_apply_kb_audit.py`：按审计表生成 v3 KB
- `scripts/96_rerun_postaudit.py`：重跑驱动
- `scripts/97_build_expert_workbook.py`：生成专家工作簿 xlsx
- `scripts/98_score_expert_workbook.py`：工作簿评分（κ、F1、盲评）
- `scripts/99_retrieval_sensitivity.py`：E3 敏感性分析
- `scripts/100_paper_numbers.py`：论文数字注册表
- `scripts/101_stage1_baselines.py`：E1 基线
- `scripts/102_leakage_check.py`：E5 泄漏检验
- `scripts/103_routing_report.py`：E7、E8 统计 + 复核路由
- `scripts/104_side_by_side.py`：并排对比候选
- `scripts/105_regrade_existing.py`：在旧结果上以 KB 重新分级（不调 API）
- `tests/test_kb_provenance.py`、`tests/test_grade_classifier_kb.py`、`tests/test_numeric_norm.py`、`tests/test_review_routing.py`、`tests/test_retrieval_variants.py`、`tests/test_expert_scoring.py`、`tests/test_paper_numbers.py`
- `paper/figures/fig3_sysml_arch.tex`：新 Fig 3（TikZ）
- `paper_wiley_submission_to_be_revised/response_to_reviewers.tex`

**修改**
- `cooling_rag_mg/grade_classifier.py`：增加可选参数 `kb_index`
- `cooling_rag_mg/config.py`：`evidence_units_jsonl` 优先读 v3_audited
- `cooling_rag_mg/coverage_retrieval.py`：`aligned_retrieve` 增加可选参数 `timing`
- `cooling_rag_mg/hybrid_fusion.py`：`rrf_fuse` 增加可选参数 `weights`
- `cooling_rag_mg/structured_req_generator.py`、`cooling_rag_mg/kb_value_extractor.py`：截断上限改为可由环境变量配置，默认值不变
- `scripts/54_run_pipelines_v3.py`：新增 `--rag-only` 参数；T=0；记录计时
- `scripts/77_run_v4_rag.py`、`77q_run_v4_rag_qwen.py`、`85_run_random_retrieval_ablation.py`、`70b_kb_verification_v4.py`：改读 v3 KB；以 KB 为准分级；77 额外保存抽取值和计时
- `scripts/79_evaluate_v4.py`：引用率和 L1 引用率改为以 KB 为准计算
- `scripts/92_export_ea_native_xmi.py`：新增复核路由、派生类型标签
- `paper/figures/fig2_pipeline.tex`：补画证据选择步骤
- `paper_wiley_submission_to_be_revised/paper_wiley.tex`、`paper_bibliography.bib`、`table_*.tex`

---

## 阶段 A：地基

### Task 0：环境、快照与延期申请

**Files:**
- Create: `cooling_rag_multigranular/run_py.bat`
- Create: `data/search_results/_archive_preaudit_20261014/`（复制）
- Create: `paper_wiley_submission_to_be_revised/paper_wiley_original_submission.tex`（复制）

- [ ] **Step 1：创建 Python 包装脚本（必须是 CRLF）**

```bash
printf '@echo off\r\nset PYTHONPATH=\r\nset PYTHONIOENCODING=utf-8\r\ncd /d D:\\cooling_rag_multigranular\\cooling_rag_multigranular\r\nD:\\Users\\yando\\miniconda3\\envs\\cooling_rag_env\\python.exe %%*\r\n' > /mnt/d/cooling_rag_multigranular/cooling_rag_multigranular/run_py.bat
mkdir -p /mnt/d/cooling_rag_multigranular/tmp
printf 'import torch\nprint(torch.cuda.is_available())\n' > /mnt/d/cooling_rag_multigranular/tmp/snip_t0.py
cmd.exe /c "D:\cooling_rag_multigranular\cooling_rag_multigranular\run_py.bat ..\tmp\snip_t0.py"
```
Expected: 输出 `True`

- [ ] **Step 2：安装 openpyxl，并确认基线测试通过**

```bash
cmd.exe /c "D:\cooling_rag_multigranular\cooling_rag_multigranular\run_py.bat -m pip install openpyxl==3.1.5"
cmd.exe /c "D:\cooling_rag_multigranular\cooling_rag_multigranular\run_py.bat -m pytest -q tests -p no:cacheprovider"
```
Expected: `121 passed, 1 error`。这个 error 是 `test_grounding.py::test_load_evidence_text_map` 的 PermissionError，属于既有问题，与本次修改无关，记下即可。

- [ ] **Step 3：归档旧结果、KB、索引和原始稿件**

```bash
cd /mnt/d/cooling_rag_multigranular/cooling_rag_multigranular
A=data/search_results/_archive_preaudit_20261014
mkdir -p $A/indexes
cp -r data/search_results/exp_v3 data/search_results/exp_v4 $A/
cp data/processed/evidence_units_v2.jsonl $A/
cp -r data/indexes/evidence_units $A/indexes/
cp ../paper_wiley_submission_to_be_revised/paper_wiley.tex ../paper_wiley_submission_to_be_revised/paper_wiley_original_submission.tex
for f in ../paper_wiley_submission_to_be_revised/table_*.tex; do cp "$f" "${f%.tex}_orig.tex"; done
ls $A $A/indexes
```
Expected: 列出 `exp_v3 exp_v4 evidence_units_v2.jsonl indexes/evidence_units`

- [ ] **Step 4：用户向编辑发送延期申请（D5）**

邮件正文（用户从投稿系统或回复编辑邮件发出）：

> Dear Dr. Whitcomb, thank you for the minor-revision decision on manuscript 4762284. To address the reviewers' requests for an external inter-annotator agreement study, a Stage-1 mapping accuracy test, and a retrieval sensitivity analysis — and to complete an additional provenance audit of our knowledge base that we initiated ourselves — we kindly request an extension of the revision deadline to November 21, 2026. Kind regards, Dongsan Yan (on behalf of all authors)

---

### Task 1：KB 出处审计模块与审计表

**Files:**
- Create: `cooling_rag_mg/kb_provenance.py`
- Create: `scripts/94_kb_provenance_audit.py`
- Test: `tests/test_kb_provenance.py`

**Interfaces:**
- Produces: `source_document(u: dict) -> str`、`provenance_group(u: dict) -> str`（取值为 `"DRAFT" | "CCS2025" | "ORIG" | "LATE"`）、`audit_flags(u: dict) -> list[str]`、`proposed_action(u: dict) -> str`（取值为 `"DROP" | "RETIER_L2" | "VERIFY" | "KEEP"`）
- Produces 文件: `data/processed/kb_audit/kb_provenance_audit.csv`（utf-8-sig 编码），列为 `id, group, kb_tier, source_type, source_document, location, flags, proposed_action, spotcheck, decision, corrected_source, corrected_location, evidence_of_verification, text_snippet`

- [ ] **Step 1：写失败的测试**

```python
# tests/test_kb_provenance.py
from cooling_rag_mg.kb_provenance import provenance_group, audit_flags, proposed_action


def _u(id_, src, tier="L1", stype="ship_rule", text="x", topic=""):
    return {"id": id_, "text": text, "kb_tier": tier,
            "metadata": {"source_document": src, "source_type": stype, "topic": topic}}


def test_draft_group_and_drop():
    u = _u("E-DRAFT-ALARM-001", "KB_DRAFT_v1", stype="project_guide")
    assert provenance_group(u) == "DRAFT"
    assert proposed_action(u) == "DROP"
    assert "llm_drafted" in audit_flags(u)


def test_ccs2025_group_keep():
    u = _u("L1-CCS2025-7-251.6-001", "CCS《钢质海船入级规范》2025")
    assert provenance_group(u) == "CCS2025"
    assert proposed_action(u) == "KEEP"


def test_orig_numbering_below_60():
    assert provenance_group(_u("E-PUMP-001", "S42 MAN 49/60DF Project Guide")) == "ORIG"


def test_late_numbering_and_unnumbered():
    assert provenance_group(_u("E-X-1", "S66 IACS Unified Requirements M72 Hydraulic Testing")) == "LATE"
    assert provenance_group(_u("E-X-2", "Wärtsilä 46F Series Product Manual", tier="L2")) == "LATE"
    assert proposed_action(_u("E-X-1", "S66 IACS Unified Requirements M72 Hydraulic Testing")) == "VERIFY"


def test_known_misattribution_drop():
    u = _u("E-ISO8861-001", "S63 ISO 8861:1998 Shipbuilding Cooling Systems Requirements", stype="standard")
    assert "misattributed_title" in audit_flags(u)
    assert proposed_action(u) == "DROP"
    u2 = _u("E-IACS-M3-001", "S60 IACS Unified Requirements M3.1 Cooling Systems")
    assert proposed_action(u2) == "DROP"


def test_synthesized_marker_drop():
    u = _u("E-PARAM-HT-001", "S60 IACS Unified Requirements M3.1 Cooling Systems",
           text="Standard Parameter Limits\n(Consolidated from IACS UR M3.1, ISO 8861)")
    assert "synthesized" in audit_flags(u)
    assert proposed_action(u) == "DROP"


def test_solas_consolidated_edition_not_flagged():
    u = _u("E-SOLAS-COOL-001", "S49 SOLAS 2024 Chapter II-1 Regulation 26",
           text="SOLAS 2020 Consolidated Edition, Chapter II-1, Part C, Regulation 26")
    assert "synthesized" not in audit_flags(u)
    assert proposed_action(u) == "KEEP"


def test_orig_nonregulatory_l1_retier():
    u = _u("E-HT-009", "S21 Caterpillar Cooling Systems Application and Installation Guide",
           stype="installation_guide")
    assert proposed_action(u) == "RETIER_L2"


def test_orig_regulatory_l1_keep():
    u = _u("E-SW-ALARM-001", "S43 ABS Marine Vessel Rules Part 4 2021", stype="ship_rule")
    assert proposed_action(u) == "KEEP"
```

- [ ] **Step 2：运行，确认失败**

Run: `PY -m pytest tests/test_kb_provenance.py -q -p no:cacheprovider`
Expected: FAIL，`ModuleNotFoundError: cooling_rag_mg.kb_provenance`

- [ ] **Step 3：实现**

```python
# cooling_rag_mg/kb_provenance.py
"""KB 出处审计：把每条证据单元归入出处组，并给出建议动作。

组别：
  DRAFT   —— KB_DRAFT_v1，由 LLM 起草（scripts/56），不是从原文切分的
  CCS2025 —— 从 CCS 入级规范 PDF 按页提取的 L1 单元（scripts/63b）
  ORIG    —— 原始语料，source_document 编号 S01–S59，从原文切分
  LATE    —— 后期补充（编号 ≥S60 或没有编号），需要逐条对照原文核实
"""
from __future__ import annotations

import re

REGULATORY_TYPES = {"ship_rule", "standard"}
_SNUM = re.compile(r"^S(\d+)\b")
_LATE_MIN = 60
# 注意：只匹配 "Consolidated from"；"SOLAS Consolidated Edition" 是官方版本名，不算综合单元
_SYNTH_MARKERS = ("Consolidated from", "consolidated from", "Industry consensus", "General Practice",
                  "Multiple sources", "Best Practice", "综合")
# 已核实的标题误标（见计划 §0）：键为 source_document 中的子串
KNOWN_MISATTRIBUTED = {
    "ISO 8861": "ISO 8861:1998 = Engine-room ventilation in diesel-engined ships",
    "Unified Requirements M3.1 Cooling": "IACS UR M3 = Speed governor and overspeed protective device",
    "Unified Requirements E10 Machinery Control": "IACS UR E10 = Test specification for type approval",
}


def source_document(u: dict) -> str:
    return ((u.get("metadata") or {}).get("source_document") or "").strip()


def provenance_group(u: dict) -> str:
    src = source_document(u)
    if src == "KB_DRAFT_v1" or str(u.get("id", "")).startswith("E-DRAFT-"):
        return "DRAFT"
    if str(u.get("id", "")).startswith("L1-CCS2025"):
        return "CCS2025"
    m = _SNUM.match(src)
    if m and int(m.group(1)) < _LATE_MIN:
        return "ORIG"
    return "LATE"


def audit_flags(u: dict) -> list[str]:
    flags: list[str] = []
    src = source_document(u)
    meta = u.get("metadata") or {}
    head = (u.get("text") or "")[:300]
    if provenance_group(u) == "DRAFT":
        flags.append("llm_drafted")
    if any(k in src for k in KNOWN_MISATTRIBUTED):
        flags.append("misattributed_title")
    blob = " ".join([head, src, str(meta.get("topic", "")), str(meta.get("location", ""))])
    if any(mk in blob for mk in _SYNTH_MARKERS):
        flags.append("synthesized")
    if u.get("kb_tier") == "L1" and meta.get("source_type") not in REGULATORY_TYPES:
        flags.append("l1_nonregulatory")
    return flags


def proposed_action(u: dict) -> str:
    flags = audit_flags(u)
    if {"llm_drafted", "misattributed_title", "synthesized"} & set(flags):
        return "DROP"
    grp = provenance_group(u)
    if grp == "LATE":
        return "VERIFY"
    if "l1_nonregulatory" in flags:
        return "RETIER_L2"
    return "KEEP"
```

- [ ] **Step 4：运行，确认通过**

Run: `PY -m pytest tests/test_kb_provenance.py -q -p no:cacheprovider`
Expected: `9 passed`

- [ ] **Step 5：写审计表生成脚本**

```python
# scripts/94_kb_provenance_audit.py
"""生成 KB 出处审计表 data/processed/kb_audit/kb_provenance_audit.csv。

spotcheck=1 标记需要抽样核对原文的保留单元：每份法规类文档（ORIG 组 L1、CCS2025）抽 3 条，SEED=42。
用法：PY scripts/94_kb_provenance_audit.py
"""
from __future__ import annotations

import csv
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cooling_rag_mg.kb_provenance import audit_flags, proposed_action, provenance_group, source_document

KB = ROOT / "data/processed/evidence_units_v2.jsonl"
OUT_DIR = ROOT / "data/processed/kb_audit"
OUT = OUT_DIR / "kb_provenance_audit.csv"
COLS = ["id", "group", "kb_tier", "source_type", "source_document", "location", "flags",
        "proposed_action", "spotcheck", "decision", "corrected_source", "corrected_location",
        "evidence_of_verification", "text_snippet"]


def main() -> None:
    units = [json.loads(l) for l in KB.open(encoding="utf-8")]
    rng = random.Random(42)
    by_doc: dict[str, list[str]] = defaultdict(list)
    for u in units:
        if proposed_action(u) == "KEEP" and u.get("kb_tier") == "L1":
            by_doc[source_document(u)].append(u["id"])
    spot = {i for ids in by_doc.values() for i in rng.sample(sorted(ids), min(3, len(ids)))}

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for u in units:
            meta = u.get("metadata") or {}
            act = proposed_action(u)
            w.writerow({
                "id": u["id"], "group": provenance_group(u), "kb_tier": u.get("kb_tier"),
                "source_type": meta.get("source_type", ""), "source_document": source_document(u),
                "location": meta.get("location", ""), "flags": ";".join(audit_flags(u)),
                "proposed_action": act, "spotcheck": int(u["id"] in spot),
                "decision": "" if act == "VERIFY" or u["id"] in spot else act,
                "corrected_source": "", "corrected_location": "", "evidence_of_verification": "",
                "text_snippet": (u.get("text") or "")[:300].replace("\n", " "),
            })
    acts = Counter(proposed_action(u) for u in units)
    print("units:", len(units), "| proposed:", dict(acts), "| spotcheck:", len(spot))
    print("written:", OUT)


if __name__ == "__main__":
    main()
```

- [ ] **Step 6：运行并核对计数**

Run: `PY scripts/94_kb_provenance_audit.py`
Expected（已在真实 KB 上试跑验证）：`units: 1364 | proposed: KEEP 1151, RETIER_L2 49, VERIFY 42, DROP 122 | spotcheck 约 22`。DROP 中 108 条为 DRAFT，另外 14 条是 ISO8861 ×2、UR M3 ×3、UR E10 ×2，以及 "Consolidated from"、"Industry consensus" 一类的综合单元。实际数字记入 `data/processed/kb_audit/README.md`，Task 3 会用到。

---

### Task 2：逐条核对 VERIFY 和 spotcheck 行（人工与 Claude 协作）

**Files:**
- Modify: `data/processed/kb_audit/kb_provenance_audit.csv`（填写 `decision`、`corrected_*`、`evidence_of_verification` 三类列）

**规则（确定性的，不需要临场判断）**
- `decision ∈ {KEEP, DROP, RETIER_L2, RETIER_L3, FIX_SOURCE}`
- **KEEP 或 FIX_SOURCE 的前提**：在原文中找到了该单元的内容，并在 `evidence_of_verification` 里写明出处，格式为 `文件或URL | 条款号或页码 | 原文前 30 个字`。
- 找不到原文、只有二手描述，或原文与单元内容不符的，一律 **DROP**（D2）。
- 原文属于厂家或行业资料的，即使内容属实，tier 也只能是 L2 或 L3。

**可用原文（已确认存在）**
- `D:\cooling_rag_multigranular\IACS_URM_Machinery_Requirements.txt`：IACS UR M 全集，用于核对 M28、M35、M51、M72、M73
- `D:\cooling_rag_multigranular\standards\CCS_Rules_Sea_Going_Steel_Ships_2024_full.txt`：CCS 2024 英文全文
- `D:\cooling_rag_multigranular\standards\IACS_UR_M28/M35/M36/M47*.pdf`
- 46 CFR 用 eCFR 在线核对（https://www.ecfr.gov/current/title-46）
- SOLAS II-1/26 用 IMO 公约文本核对
- DNV 规范用 https://rules.dnv.com（免费公开）核对

- [ ] **Step 1：Claude 先自动核对 IACS 和 CCS 两类**

用下面的辅助脚本，在本地原文中搜索单元文本里的关键数字和短语，把命中的行号写进 `evidence_of_verification`。脚本只提供线索，最终决定仍须由人工逐条填写。

```python
# 一次性辅助，不入库：tmp/audit_grep.py
import csv, re, sys
SRC = {"IACS": r"D:\cooling_rag_multigranular\IACS_URM_Machinery_Requirements.txt",
       "CCS": r"D:\cooling_rag_multigranular\standards\CCS_Rules_Sea_Going_Steel_Ships_2024_full.txt"}
texts = {k: open(v, encoding="utf-8", errors="ignore").read().splitlines() for k, v in SRC.items()}
rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8-sig")))
for r in rows:
    if r["proposed_action"] != "VERIFY" and r["spotcheck"] != "1":
        continue
    key = "IACS" if "IACS" in r["source_document"] else ("CCS" if "CCS" in r["source_document"] else None)
    if not key:
        continue
    nums = re.findall(r"\d+(?:\.\d+)?\s*(?:%|°C|bar|MPa|kPa|s\b|min)", r["text_snippet"])
    hits = [i + 1 for i, line in enumerate(texts[key]) if nums and all(n.split()[0] in line for n in nums[:2])]
    print(r["id"], key, nums[:3], "lines:", hits[:5])
```
Run: `PY ../tmp/audit_grep.py data/processed/kb_audit/kb_provenance_audit.csv`

- [ ] **Step 2：逐条核对其余 VERIFY 行（DNV、SOLAS、46 CFR、PRS、ABS、ISO 9906、BS MA 18 以及无编号单元）**，按上面的规则填表。每条约 3–5 分钟，合计约 4 小时。
- [ ] **Step 3：用户复核** 所有 `decision=KEEP` 且属于 LATE 组的行，以及所有 `FIX_SOURCE` 的行，在 `evidence_of_verification` 末尾追加 `|confirmed-by-user`。
- [ ] **Step 4：完整性检查**

```bash
PY -c "import csv;r=list(csv.DictReader(open('data/processed/kb_audit/kb_provenance_audit.csv',encoding='utf-8-sig')));bad=[x['id'] for x in r if not x['decision']];print('empty decisions:',len(bad),bad[:10])"
```
Expected: `empty decisions: 0 []`

---

### Task 3：应用审计结果，生成 v3 KB，重建索引

**Files:**
- Create: `scripts/95_apply_kb_audit.py`
- Modify: `cooling_rag_mg/config.py:57-59`
- Modify（把 KB 路径从 v2 改为 v3）：`scripts/77_run_v4_rag.py`、`scripts/77q_run_v4_rag_qwen.py`、`scripts/85_run_random_retrieval_ablation.py`、`scripts/70b_kb_verification_v4.py`、`scripts/80_stage25_sample_review.py`

**Interfaces:**
- Produces: `data/processed/evidence_units_v3_audited.jsonl`。每条记录在 `metadata` 下新增 `provenance_group` 和 `audit_decision` 两个字段。
- Produces: `data/processed/kb_audit/kb_audit_summary.json`，键为 `n_before, n_after, by_decision, tier_before, tier_after, sources_after`。

- [ ] **Step 1：实现应用脚本**

```python
# scripts/95_apply_kb_audit.py
"""按审计表生成 evidence_units_v3_audited.jsonl。decision 为空则报错退出。"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cooling_rag_mg.kb_provenance import provenance_group

KB_IN = ROOT / "data/processed/evidence_units_v2.jsonl"
AUDIT = ROOT / "data/processed/kb_audit/kb_provenance_audit.csv"
KB_OUT = ROOT / "data/processed/evidence_units_v3_audited.jsonl"
SUMMARY = ROOT / "data/processed/kb_audit/kb_audit_summary.json"
VALID = {"KEEP", "DROP", "RETIER_L2", "RETIER_L3", "FIX_SOURCE"}


def main() -> None:
    rows = {r["id"]: r for r in csv.DictReader(AUDIT.open(encoding="utf-8-sig"))}
    units = [json.loads(l) for l in KB_IN.open(encoding="utf-8")]
    missing = [u["id"] for u in units if u["id"] not in rows]
    bad = [i for i, r in rows.items() if r["decision"] not in VALID]
    if missing or bad:
        sys.exit(f"audit incomplete: missing={missing[:5]} bad_decision={bad[:5]}")
    out, dec = [], Counter()
    for u in units:
        r = rows[u["id"]]
        d = r["decision"]
        dec[d] += 1
        if d == "DROP":
            continue
        u = json.loads(json.dumps(u))
        meta = u.setdefault("metadata", {})
        if d == "RETIER_L2":
            u["kb_tier"], u["tier_reason"] = "L2", "audit-2026-10: non-regulatory source"
        elif d == "RETIER_L3":
            u["kb_tier"], u["tier_reason"] = "L3", "audit-2026-10: operational/industry reference"
        elif d == "FIX_SOURCE":
            meta["source_document"] = r["corrected_source"] or meta.get("source_document", "")
            meta["location"] = r["corrected_location"] or meta.get("location", "")
        meta["provenance_group"] = provenance_group(u)
        meta["audit_decision"] = d
        out.append(u)
    with KB_OUT.open("w", encoding="utf-8") as f:
        for u in out:
            f.write(json.dumps(u, ensure_ascii=False) + "\n")
    summary = {
        "n_before": len(units), "n_after": len(out), "by_decision": dict(dec),
        "tier_before": dict(Counter(u["kb_tier"] for u in units)),
        "tier_after": dict(Counter(u["kb_tier"] for u in out)),
        "sources_after": len({(u.get("metadata") or {}).get("source_document") for u in out}),
    }
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
```

- [ ] **Step 2：运行**

Run: `PY scripts/95_apply_kb_audit.py`
Expected: 输出 summary，其中 `n_after` 约为 1,190–1,240，`tier_after` 中 L1 约为 110–150。

- [ ] **Step 3：config 优先读 v3**，把 `cooling_rag_mg/config.py:57-59` 替换为：

```python
    def evidence_units_jsonl(self) -> Path:
        for name in ("evidence_units_v3_audited.jsonl", "evidence_units_v2.jsonl"):
            p = self.processed_dir / name
            if p.exists():
                return p
        return self.processed_dir / "evidence_units.jsonl"
```

- [ ] **Step 4：重跑要用到的 5 个脚本改读 v3**

```bash
cd /mnt/d/cooling_rag_multigranular/cooling_rag_multigranular
sed -i 's#evidence_units_v2\.jsonl#evidence_units_v3_audited.jsonl#' scripts/77_run_v4_rag.py scripts/77q_run_v4_rag_qwen.py scripts/85_run_random_retrieval_ablation.py scripts/70b_kb_verification_v4.py scripts/80_stage25_sample_review.py
grep -n "evidence_units_v" scripts/77_run_v4_rag.py scripts/77q_run_v4_rag_qwen.py scripts/85_run_random_retrieval_ablation.py scripts/70b_kb_verification_v4.py scripts/80_stage25_sample_review.py
```
Expected: 5 个文件里都只出现 `evidence_units_v3_audited.jsonl`

- [ ] **Step 5：重建索引**（`scripts/11` 会同时重建 source_chunks 和 evidence_units 两个索引，通过 `.env` 中 `DEVICE=cuda` 在 GPU 上编码）

Run: `PY scripts/11_build_multigranular_indexes.py`
Expected: 最后一行为 `indexes built: ...`。然后检查记录数：
`PY -c "from cooling_rag_mg.index_store import load_index;print(len(load_index('data/indexes/evidence_units').records))"`，应等于 Step 2 的 `n_after`。

- [ ] **Step 6：跑全部测试**，Expected 与 Task 0 Step 2 一致，再加上新增测试的通过数。

---

### Task 4：以 KB 为准的分级器

**Files:**
- Modify: `cooling_rag_mg/grade_classifier.py`
- Create: `cooling_rag_mg/numeric_norm.py`（Task 11 也会用）
- Create: `scripts/105_regrade_existing.py`
- Test: `tests/test_grade_classifier_kb.py`、`tests/test_numeric_norm.py`

**Interfaces:**
- Produces: `valid_citation_ids(evidence_citations, kb_index: dict[str, dict]) -> list[str]`
- Produces: `kb_has_clause(u: dict) -> bool`
- Produces: `classify_grade(measurable_criterion, evidence_citations, kb_index: dict | None = None) -> Grade`。`kb_index=None` 时保持旧行为，现有 10 个测试不受影响。
- Produces: `classify_result_set(result_set, kb_index=None) -> dict`
- Produces: `numeric_norm.extract_numbers(s: str) -> list[str]`（返回规范化后的数字串）

- [ ] **Step 1：写失败的测试**

```python
# tests/test_numeric_norm.py
from cooling_rag_mg.numeric_norm import extract_numbers


def test_ranges_and_fullwidth():
    assert extract_numbers("70–85°C") == ["70", "85"]
    assert extract_numbers("７０-８５ ℃") == ["70", "85"]


def test_decimal_and_multiplier():
    assert extract_numbers("1.5倍设计压力") == ["1.5"]
    assert extract_numbers("1.50×p") == ["1.5"]
    assert extract_numbers("≤ 2 s") == ["2"]


def test_no_numbers():
    assert extract_numbers("{{TBD|unit:°C}}") == []


def test_number_after_chinese_char():
    assert extract_numbers("当冷却水温度高于85°C时") == ["85"]
```

```python
# tests/test_grade_classifier_kb.py
from cooling_rag_mg.grade_classifier import classify_grade, kb_has_clause, valid_citation_ids

KB = {
    "E-L1-CL": {"id": "E-L1-CL", "kb_tier": "L1", "text": "条款 7-25 1.6 冷却水温度高报警",
                "metadata": {"location": "P1935", "section_title": "条款 7-25 1.6"}},
    "E-L1-NOCL": {"id": "E-L1-NOCL", "kb_tier": "L1", "text": "cooling water shall be monitored",
                  "metadata": {"location": "", "section_title": "Cooling"}},
    "E-L2": {"id": "E-L2", "kb_tier": "L2", "text": "HT outlet 90 °C", "metadata": {}},
}


def test_unknown_id_is_uncited_and_numeric_is_x():
    cits = [{"kb_id": "E-NOT-IN-KB", "tier": "L1", "has_clause": "yes"}]
    assert valid_citation_ids(cits, KB) == []
    assert classify_grade("不超过 85°C", cits, kb_index=KB) == "X"


def test_model_claimed_tier_ignored_kb_tier_used():
    cits = [{"kb_id": "E-L2", "tier": "L1", "has_clause": "IACS"}]
    assert classify_grade("不超过 90°C", cits, kb_index=KB) == "B"


def test_l1_without_clause_locator_is_b():
    cits = [{"kb_id": "E-L1-NOCL", "tier": "L1", "has_clause": True}]
    assert kb_has_clause(KB["E-L1-NOCL"]) is False
    assert classify_grade("不超过 85°C", cits, kb_index=KB) == "B"


def test_l1_with_clause_locator_is_a():
    cits = [{"kb_id": "E-L1-CL"}]
    assert kb_has_clause(KB["E-L1-CL"]) is True
    assert classify_grade("不超过 85°C", cits, kb_index=KB) == "A"


def test_string_citation_with_valid_id_is_accepted():
    cits = ["E-L2 / 厂家指南 / L2"]
    assert valid_citation_ids(cits, KB) == ["E-L2"]
    assert classify_grade("90°C", cits, kb_index=KB) == "B"


def test_tbd_and_qualitative_still_c():
    assert classify_grade("{{TBD|unit:°C|ref:MAN}}", [], kb_index=KB) == "C"
    assert classify_grade("满足制造商要求", [], kb_index=KB) == "C"
```

- [ ] **Step 2：运行，确认失败**

Run: `PY -m pytest tests/test_numeric_norm.py tests/test_grade_classifier_kb.py -q -p no:cacheprovider`
Expected: FAIL，报 ImportError

- [ ] **Step 3：实现 `numeric_norm.py`**

```python
# cooling_rag_mg/numeric_norm.py
"""数值抽取与归一化：全角转半角，统一各种连字符，去掉多余的尾零。"""
from __future__ import annotations

import re
import unicodedata

_NUM = re.compile(r"(?<![A-Za-z0-9.])(\d+(?:\.\d+)?)")  # 不能用 \w：中文字符属于 \w，会漏掉"高于85°C"


def _norm_num(s: str) -> str:
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s or "0"


def extract_numbers(s: str) -> list[str]:
    if not s:
        return []
    t = unicodedata.normalize("NFKC", str(s))
    t = re.sub(r"\{\{TBD[^}]*\}\}", " ", t)
    t = re.sub(r"[–—~～]", "-", t)
    return [_norm_num(m.group(1)) for m in _NUM.finditer(t)]
```

- [ ] **Step 4：修改 `grade_classifier.py`**。在文件末尾追加下面的函数，并把 `classify_grade` 和 `classify_result_set` 替换为新版本。`_TBD_PATTERN` 和 `_NUM_PATTERN` 保持不变。

```python
_KBID = re.compile(r"\b(?:E|L1)-[A-Za-z0-9.\-]+")
_CLAUSE = re.compile(
    r"(\d+(?:\.\d+){1,}|\d+-\d+|Reg(?:ulation)?\.?\s*\d+|Rule\s*\d+|Table\s*\d|Tbl\.?\s*\d|"
    r"§\s*\d|条款|第\s*\d+\s*[条章节篇]|Pt\.?\s*\d+|Part\s*\d+|Ch(?:apter)?\.?\s*\d+|UR\s*[A-Z]\d+|CFR\s*\d+)"
)


def kb_has_clause(u: dict) -> bool:
    """KB 记录本身是否带有条款定位信息（位置、节标题或正文开头）。"""
    meta = u.get("metadata") or {}
    blob = " ".join([str(meta.get("location", "")), str(meta.get("section_title", "")),
                     (u.get("text") or "")[:200]])
    return bool(_CLAUSE.search(blob))


def valid_citation_ids(evidence_citations, kb_index: dict) -> list[str]:
    """返回在 KB 中真实存在的被引 ID。兼容 dict 和字符串两种引用格式；去重并保持顺序。"""
    out: list[str] = []
    for c in evidence_citations or []:
        if isinstance(c, dict):
            cands = [str(c.get("kb_id") or "")]
        else:
            cands = _KBID.findall(str(c))
        for cid in cands:
            cid = cid.strip()
            if cid and cid in kb_index and cid not in out:
                out.append(cid)
    return out


def classify_grade(measurable_criterion: str, evidence_citations: list, kb_index: dict | None = None) -> Grade:
    mc = "" if measurable_criterion is None else str(measurable_criterion)
    if _TBD_PATTERN.search(mc):
        return "C"
    if not _NUM_PATTERN.search(mc):
        return "C"
    if kb_index is not None:
        ids = valid_citation_ids(evidence_citations, kb_index)
        if not ids:
            return "X"
        if any(kb_index[i].get("kb_tier") == "L1" and kb_has_clause(kb_index[i]) for i in ids):
            return "A"
        return "B"
    # ---- 旧行为（kb_index=None），保留以兼容旧测试和旧结果 ----
    if not evidence_citations:
        return "X"
    if any(isinstance(c, dict) and c.get("tier") == "L1" and c.get("has_clause", False)
           for c in evidence_citations):
        return "A"
    if any(isinstance(c, dict) and c.get("tier") in ("L1", "L2", "L3") for c in evidence_citations):
        return "B"
    return "X"


def classify_result_set(result_set: dict, kb_index: dict | None = None) -> dict:
    rs = dict(result_set)
    ers = []
    for er in rs.get("engineering_requirements", []):
        e = dict(er)
        e["_grade"] = classify_grade(er.get("measurable_criterion", ""),
                                     er.get("evidence_citations", []), kb_index)
        if kb_index is not None:
            e["_valid_citation_ids"] = valid_citation_ids(er.get("evidence_citations", []), kb_index)
        ers.append(e)
    rs["engineering_requirements"] = ers
    return rs
```

- [ ] **Step 5：运行全部分级器测试**

Run: `PY -m pytest tests/test_grade_classifier.py tests/test_grade_classifier_kb.py tests/test_numeric_norm.py -q -p no:cacheprovider`
Expected: 全部通过（旧测试 10 个、新测试 6+3 个）

- [ ] **Step 6：写 `scripts/105_regrade_existing.py`**。它用 v3 KB 对**归档里的旧结果**重新分级，不调 API。产出用于回复信中说明"审计前后变化"的那一段。

```python
# scripts/105_regrade_existing.py
"""用审计后的 KB 重新分级审计前的结果（不调 API），量化审计的影响。"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cooling_rag_mg.grade_classifier import classify_result_set

ARCH = ROOT / "data/search_results/_archive_preaudit_20261014/exp_v4"
KB = ROOT / "data/processed/evidence_units_v3_audited.jsonl"
OUT = ROOT / "data/search_results/exp_v4/regrade_preaudit_with_v3kb.json"


def main() -> None:
    kb = {json.loads(l)["id"]: json.loads(l) for l in KB.open(encoding="utf-8")}
    res = {}
    for name in ("rag_v4_results.json", "norag_v4_results.json"):
        d = json.loads((ARCH / name).read_text(encoding="utf-8"))
        old = Counter(e["_grade"] for rs in d["result_sets"] for e in rs["engineering_requirements"])
        new = Counter(e["_grade"] for rs in d["result_sets"]
                      for e in classify_result_set(rs, kb)["engineering_requirements"])
        res[name] = {"old": dict(old), "new_with_v3kb": dict(new)}
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False))


if __name__ == "__main__":
    main()
```
Run: `PY scripts/105_regrade_existing.py`
Expected: no-RAG 的 old 与 new 完全相同（174 X / 131 C）；RAG 的 new 中，A+B 明显少于 110，被删除单元引用的数值会变成 X。记下这些数字。

---

### Task 5：管线插桩（`--rag-only`、T=0、计时、可配置截断、保存抽取值）

**Files:**
- Modify: `cooling_rag_mg/coverage_retrieval.py`（`aligned_retrieve` 增加 `timing: dict | None = None`）
- Modify: `cooling_rag_mg/structured_req_generator.py:56-57`
- Modify: `cooling_rag_mg/kb_value_extractor.py`（`text[:1200]` 改为可配置）
- Modify: `scripts/54_run_pipelines_v3.py`
- Modify: `scripts/77_run_v4_rag.py`、`scripts/77q_run_v4_rag_qwen.py`、`scripts/85_run_random_retrieval_ablation.py`（以 KB 为准分级）
- Modify: `scripts/79_evaluate_v4.py`（以 KB 为准计算引用率）
- Test: `tests/test_retrieval_variants.py`（Task 10 中补全）

- [ ] **Step 1：`aligned_retrieve` 计时**。在 `cooling_rag_mg/coverage_retrieval.py` 中：
  - 函数签名末尾加 `timing: dict | None = None,`
  - 在 `pairs = analyze_requirement(...)` 前后加：

```python
    import time as _t
    _t0 = _t.perf_counter()
    pairs = analyze_requirement(requirement_text, analyzer_client, analyzer_model)
    _t1 = _t.perf_counter()
    if timing is not None:
        timing["stage1_s"] = round(_t1 - _t0, 3)
```
  - 在每个 `return` 之前加 `if timing is not None: timing["retrieval_s"] = round(_t.perf_counter() - _t1, 3)`。一共 3 处 return：fallback、提前截断、正常结束。

- [ ] **Step 2：截断上限可配置**。`structured_req_generator.py:56-57` 改为：

```python
import os
_MAX_EVIDENCE_ITEMS = int(os.getenv("RAG_MAX_EVIDENCE_ITEMS", "12"))
_EU_TEXT_LIMIT = int(os.getenv("RAG_EU_TEXT_LIMIT", "500"))
```
`kb_value_extractor.py` 中的 `text[:1200]` 改为 `text[:int(os.getenv("RAG_EXTRACT_CHAR_LIMIT", "1200"))]`，并在文件顶部加 `import os`。默认值不变，所以复现性不受影响。

- [ ] **Step 3：修改 `54_run_pipelines_v3.py`**
  - 增加参数 `ap.add_argument("--rag-only", action="store_true")`。
  - no-RAG 那一段用 `if not args.rag_only:` 包起来；落盘时 `norag_results.json` 也只在 `not args.rag_only` 时写，以免覆盖。
  - 检索调用改为：

```python
        timing: dict = {}
        evidence_list, pairs_used = aligned_retrieve(
            text, searcher, ds_client, ds_model,
            per_pair_k=8, max_total=20, timing=timing,
        )
        _ts = time.perf_counter()
        rag_ers = generate_rag_v3(text, evidence_list, ds_client, ds_model, temperature=0.0)
        timing["selection_s"] = round(time.perf_counter() - _ts, 3)
```
  - 结果字典 `rag_results.append({...})` 中增加 `"_timing": timing,` 和 `"_retrieved_ids": [e.get("id") for e in evidence_list],`。

- [ ] **Step 4：修改 `77_run_v4_rag.py`**
  - 在 `eu_idx = load_eu_index(EU_JSONL)` 之后，把 `classify_result_set(new_rs)` 改为 `classify_result_set(new_rs, eu_idx)`。
  - 计时与保存抽取值：

```python
        _t0 = time.perf_counter()
        annotated = annotate_evidence_units(evidence_units, client, model)
        _t1 = time.perf_counter()
        new_shalls = generate_structured_shalls(
            source_requirement=source_req_text, annotated_evidence=annotated,
            client=client, model=model,
        )
        _t2 = time.perf_counter()
```
  - `new_rs` 中增加 `"_timing": {**rs.get("_timing", {}), "extraction_s": round(_t1-_t0,3), "generation_s": round(_t2-_t1,3)}` 和 `"_evidence_values": {eu["id"]: eu["_extracted_values"] for eu in annotated}`。
  - 文件顶部加 `import time`。
  - 对 `77q_run_v4_rag_qwen.py` 和 `85_run_random_retrieval_ablation.py` 做同样的修改：`classify_result_set(..., eu_idx_or_kb)`。85 中 KB 列表变量名为 `all_eus`，需要先构造 `kb_index = {u["id"]: u for u in all_eus}`。

- [ ] **Step 5：修改 `79_evaluate_v4.py`**，让引用率和 L1 引用率以 KB 为准。顶部加载 KB：

```python
from cooling_rag_mg.grade_classifier import valid_citation_ids
KB = {json.loads(l)["id"]: json.loads(l) for l in
      open(ROOT / "data/processed/evidence_units_v3_audited.jsonl", encoding="utf-8")}
```
把 `cited`、`has_l1`、`multi_src` 三行替换为：

```python
    vids = [valid_citation_ids(er.get("evidence_citations", []), KB) for er in shalls]
    cited = sum(1 for v in vids if v)
    has_l1 = sum(1 for v in vids if any(KB[i].get("kb_tier") == "L1" for i in v))
    multi_src = sum(1 for v in vids if len(v) >= 2)
```

- [ ] **Step 6：冒烟测试（只跑 2 条需求）**

```bash
PY scripts/54_run_pipelines_v3.py --rag-only --limit 2
PY -c "import json;d=json.load(open('data/search_results/exp_v3/rag_v3_results.json',encoding='utf-8'));print(d['result_sets'][0]['_timing'],len(d['result_sets']))"
```
Expected: 输出含 `stage1_s / retrieval_s / selection_s`，结果集为 2 条。冒烟只是检查能跑通，Task 6 会完整重跑、覆盖这个文件。

- [ ] **Step 7：跑全部测试**，Expected 与上一次相同。

---

### Task 6：全管线重跑与论文数字注册表

**Files:**
- Create: `scripts/96_rerun_postaudit.py`
- Create: `scripts/100_paper_numbers.py`
- Test: `tests/test_paper_numbers.py`

**Interfaces:**
- Produces: `data/search_results/exp_v4/paper_numbers.json`。后续所有写作任务只从这里取数字。
- `100_paper_numbers.py` 中的函数 `wilson(k: int, n: int) -> tuple[float|None, float|None]`，返回百分数下限和上限，保留 1 位小数；`n=0` 时返回 `(None, None)`。

- [ ] **Step 1：写重跑驱动**

```python
# scripts/96_rerun_postaudit.py
"""审计后的全量重跑，按顺序执行；任何一步失败就停止。日志写到 logs/rerun_postaudit_*.log。
no-RAG 的 DeepSeek 和 Qwen 生成结果（78、78q）与 KB 无关，不重跑，只重新分级。
"""
from __future__ import annotations

import datetime
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
E4 = "data/search_results/exp_v4"
STEPS = [
    ["scripts/54_run_pipelines_v3.py", "--rag-only"],
    ["scripts/77_run_v4_rag.py"],
    ["scripts/79_evaluate_v4.py"],
    ["scripts/83_grade_c_analysis.py"],
    ["scripts/85_run_random_retrieval_ablation.py"],
    ["scripts/70b_kb_verification_v4.py"],
    ["scripts/71b_paired_conflict_v4.py"],
    ["scripts/59_evaluate_v3.py", "--rag-file", f"{E4}/rag_v4_results.json",
     "--norag-file", f"{E4}/norag_v4_results.json", "--out-dir", f"{E4}/credibility_v4"],
    ["scripts/77q_run_v4_rag_qwen.py"],
]


def main() -> None:
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    log = ROOT / "logs" / f"rerun_postaudit_{datetime.datetime.now():%Y%m%d_%H%M}.log"
    log.parent.mkdir(exist_ok=True)
    (ROOT / E4 / "credibility_v4").mkdir(parents=True, exist_ok=True)
    for i, step in enumerate(STEPS):
        if i < start:
            continue
        print(f"[{i}] {' '.join(step)}", flush=True)
        with log.open("a", encoding="utf-8") as f:
            f.write(f"\n===== [{i}] {' '.join(step)} =====\n")
            r = subprocess.run([sys.executable, *step], cwd=ROOT, stdout=f, stderr=subprocess.STDOUT)
        if r.returncode != 0:
            sys.exit(f"step {i} failed (rc={r.returncode}); see {log}; resume with: 96_rerun_postaudit.py {i}")
    print("all steps done; log:", log)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2：执行（预计 3–5 小时，可以挂在后台）**

Run（后台）：`PY scripts/96_rerun_postaudit.py`
如果中途失败：根据日志修复后，执行 `PY scripts/96_rerun_postaudit.py <失败的步号>` 从那一步续跑。
Expected: 输出 `all steps done`。

- [ ] **Step 3：no-RAG 两臂和 Qwen no-RAG 以 KB 重新分级**（不调 API，原地更新 `_grade`）

```bash
PY -c "
import json
from cooling_rag_mg.grade_classifier import classify_result_set
kb={json.loads(l)['id']:json.loads(l) for l in open('data/processed/evidence_units_v3_audited.jsonl',encoding='utf-8')}
for n in ['norag_v4_results.json','norag_v4_qwen_results.json']:
    p='data/search_results/exp_v4/'+n; d=json.load(open(p,encoding='utf-8'))
    d['result_sets']=[classify_result_set(r,kb) for r in d['result_sets']]
    json.dump(d,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2); print(n,'regraded')
"
```

- [ ] **Step 4：写 `100_paper_numbers.py` 的测试**

```python
# tests/test_paper_numbers.py
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("pn", Path("scripts/100_paper_numbers.py"))
pn = importlib.util.module_from_spec(spec); spec.loader.exec_module(pn)


def test_wilson_zero_n():
    assert pn.wilson(0, 0) == (None, None)


def test_wilson_zero_k_upper_bound():
    lo, hi = pn.wilson(0, 286)
    assert lo == 0.0 and 1.2 <= hi <= 1.4


def test_grade_summary_handles_empty_arm():
    s = pn.grade_summary({"result_sets": []}, kb={})
    assert s["n_shalls"] == 0 and s["grade_X_pct"] is None
```

- [ ] **Step 5：实现 `100_paper_numbers.py`**

```python
# scripts/100_paper_numbers.py
"""从各结果文件汇总论文中出现的全部数字，写入 exp_v4/paper_numbers.json。
可选文件（E1/E2/E3/E5/E7/E8/盲评）存在才读，缺失则写 null，不会报错。
"""
from __future__ import annotations

import json
import math
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cooling_rag_mg.grade_classifier import valid_citation_ids

E4 = ROOT / "data/search_results/exp_v4"
KBP = ROOT / "data/processed/evidence_units_v3_audited.jsonl"


def wilson(k: int, n: int, z: float = 1.959964):
    if n == 0:
        return (None, None)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (round(max(0.0, c - h) * 100, 1), round(min(1.0, c + h) * 100, 1))


def _pct(k, n):
    return None if n == 0 else round(k / n * 100, 1)


def grade_summary(d: dict, kb: dict) -> dict:
    ers = [e for rs in d.get("result_sets", []) for e in rs.get("engineering_requirements", [])]
    n = len(ers)
    g = Counter(e.get("_grade") for e in ers)
    vids = [valid_citation_ids(e.get("evidence_citations", []), kb) for e in ers]
    out = {"n_shalls": n, "n_sets": len(d.get("result_sets", []))}
    for k in "ABCX":
        out[f"grade_{k}"] = g.get(k, 0)
        out[f"grade_{k}_pct"] = _pct(g.get(k, 0), n)
    out["grade_AB_pct"] = _pct(g.get("A", 0) + g.get("B", 0), n)
    out["grade_X_ci"] = wilson(g.get("X", 0), n)
    out["citation_rate_pct"] = _pct(sum(1 for v in vids if v), n)
    out["l1_citation_rate_pct"] = _pct(sum(1 for v in vids if any(kb[i]["kb_tier"] == "L1" for i in v)), n)
    out["multi_source_pct"] = _pct(sum(1 for v in vids if len(v) >= 2), n)
    return out


def _load(p: Path):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def main() -> None:
    kb = {json.loads(l)["id"]: json.loads(l) for l in KBP.open(encoding="utf-8")}
    N = {"kb": {"n_units": len(kb), "tiers": dict(Counter(u["kb_tier"] for u in kb.values())),
                "n_sources": len({(u.get("metadata") or {}).get("source_document") for u in kb.values()}),
                "audit": _load(ROOT / "data/processed/kb_audit/kb_audit_summary.json")}}
    for key, fn in [("rag", "rag_v4_results.json"), ("norag", "norag_v4_results.json"),
                    ("random", "ablation_random_retrieval_results.json"),
                    ("rag_qwen", "rag_v4_qwen_results.json"), ("norag_qwen", "norag_v4_qwen_results.json")]:
        d = _load(E4 / fn)
        N[key] = grade_summary(d, kb) if d else None
    rag = _load(E4 / "rag_v4_results.json") or {"result_sets": []}
    tim = [rs.get("_timing", {}) for rs in rag["result_sets"]]
    N["timing_s_mean"] = {k: (round(sum(t.get(k, 0) for t in tim) / len(tim), 2) if tim else None)
                          for k in ("stage1_s", "retrieval_s", "selection_s", "extraction_s", "generation_s")}
    for key, fn in [("grade_c", "grade_c_analysis.json"), ("posthoc", "norag_kb_verification.json"),
                    ("paired_conflict", "paired_conflict_analysis.json"),
                    ("credibility", "credibility_v4/eval_v3.json"),
                    ("regrade_preaudit", "regrade_preaudit_with_v3kb.json"),
                    ("e1_stage1", "e1_stage1_scores.json"), ("expert", "expert_scores.json"),
                    ("e3_sensitivity", "sensitivity/summary.json"), ("e5_leakage", "e5_leakage.json"),
                    ("routing", "routing_report.json"), ("stage3_subset", "stage3_accuracy_subset.json")]:
        d = _load(E4 / fn)
        N[key] = (d.get("summary", d) if isinstance(d, dict) else d) if d is not None else None
    (E4 / "paper_numbers.json").write_text(json.dumps(N, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: N[k] for k in ("kb", "rag", "norag", "random")}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
```

- [ ] **Step 6：运行测试与脚本**

Run: `PY -m pytest tests/test_paper_numbers.py -q -p no:cacheprovider`，然后 `PY scripts/100_paper_numbers.py`
Expected: 测试 3 passed。脚本打印 kb、rag、norag、random 四块；norag 的 `grade_X` 必须仍为 174，`n_shalls` 为 305。

- [ ] **Step 7：重跑后的强制检查**（若任何一项不满足，停下来如实记录，不得调参"修"结果）
  - `rag.citation_rate_pct`、`rag.grade_X`、`random.grade_X` 三个数如实记录。若 Grade X > 0，到 `rag_v4_results.json` 里找到这些 shall 并归因（模型违反了约束，还是引用的 ID 已被删除），写入 `data/search_results/exp_v4/rerun_notes.md`。
  - 原 Stage 3 精度样本（50 条）只在保留下来的单元上重算，生成 `stage3_accuracy_subset.json`：

```bash
PY -c "
import json
kb={json.loads(l)['id'] for l in open('data/processed/evidence_units_v3_audited.jsonl',encoding='utf-8')}
S=json.load(open('data/search_results/exp_v4/stage25_sample_data.json',encoding='utf-8'))
R=json.load(open('data/search_results/exp_v4/stage25_review_results.json',encoding='utf-8'))
out={}
for tier in ['L1','L2','L3','ALL']:
    ids=[s['eu_id'] for s in S if s['eu_id'] in kb and (tier=='ALL' or s['tier']==tier)]
    c=sum(R[i]['correct_count'] for i in ids); m=sum(R[i]['missed_count'] for i in ids); x=sum(R[i]['n_extracted'] for i in ids)
    out[tier]={'n_units':len(ids),'precision':round(c/x*100,1) if x else None,'recall':round(c/(c+m)*100,1) if c+m else None}
json.dump(out,open('data/search_results/exp_v4/stage3_accuracy_subset.json','w'),indent=1);print(out)"
```
  - 再运行一次 `PY scripts/100_paper_numbers.py`。

---

## 阶段 B：新证据

### Task 7：E1 Stage 1 映射的基线与候选池（R1-4.6）

**Files:**
- Create: `scripts/101_stage1_baselines.py`

**Interfaces:**
- Consumes: `exp_v3/rag_v3_results.json` 中的 `_pairs_used`（格式为 `"comp×intent"`，Task 6 重跑后的版本）；`evidence_taxonomy.TAXONOMY / COMPONENTS / INTENTS / all_pairs()`；`text_utils.simple_tokens`
- Produces: `exp_v4/e1_predictions.json`，结构为 `{system: {OR_id: [[comp, intent], ...]}}`，系统包括 `deepseek, qwen, bm25, embed`
- Produces: `exp_v4/e1_pool.csv`，列为 `or_id, requirement_text, component, intent, component_desc, intent_desc`（打乱顺序，**不含系统标签**）

- [ ] **Step 1：实现**

```python
# scripts/101_stage1_baselines.py
"""E1：Stage 1（需求 → (c,i) 对）的 DeepSeek 结果与三种基线，并生成盲标候选池。
基线说明：
  bm25  —— 用 BM25 把需求文本与 183 个合法 (c,i) 的"部件描述+方面描述"做匹配，取 top-k
  embed —— BGE-M3 余弦相似度，取 top-k
  qwen  —— 同一个 analyzer prompt，换用 qwen-max
  k = 4，与 DeepSeek 平均每条需求约 3.8 个对的数量接近
"""
from __future__ import annotations

import csv
import json
import random
import sys
from pathlib import Path

import numpy as np
from rank_bm25 import BM25Okapi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cooling_rag_mg.config import get_config
from cooling_rag_mg.evidence_taxonomy import COMPONENTS, INTENTS, all_pairs
from cooling_rag_mg.index_store import load_sentence_transformer
from cooling_rag_mg.requirement_analyzer import analyze_requirement
from cooling_rag_mg.text_utils import simple_tokens

E3 = ROOT / "data/search_results/exp_v3/rag_v3_results.json"
OR = ROOT / "data/processed/original_requirements_v2.jsonl"
OUT = ROOT / "data/search_results/exp_v4"
K = 4


def pair_doc(c: str, i: str) -> str:
    return f"{c} {COMPONENTS.get(c, '')} {i} {INTENTS.get(i, '')}"


def main() -> None:
    cfg = get_config()
    reqs = [json.loads(l) for l in OR.open(encoding="utf-8")]
    pairs = all_pairs()
    docs = [pair_doc(c, i) for c, i in pairs]
    pred: dict[str, dict[str, list]] = {"deepseek": {}, "qwen": {}, "bm25": {}, "embed": {}}

    v3 = json.loads(E3.read_text(encoding="utf-8"))
    for rs in v3["result_sets"]:
        pred["deepseek"][rs["source_requirement_id"]] = [p.split("×") for p in rs.get("_pairs_used", [])]

    bm = BM25Okapi([simple_tokens(d) for d in docs])
    model = load_sentence_transformer(cfg.model.embedding_model_path, device=cfg.model.device, label="[E1]")
    dv = model.encode(docs, normalize_embeddings=True)
    qclient = cfg.qwen.make_client()
    for r in reqs:
        rid, text = r["requirement_id"], r["requirement_text"]
        s = bm.get_scores(simple_tokens(text))
        pred["bm25"][rid] = [list(pairs[j]) for j in np.argsort(s)[::-1][:K]]
        qv = model.encode([text], normalize_embeddings=True)[0]
        pred["embed"][rid] = [list(pairs[j]) for j in np.argsort(dv @ qv)[::-1][:K]]
        pred["qwen"][rid] = [list(p) for p in analyze_requirement(text, qclient, cfg.qwen.model)]
        print(rid, {k: len(v.get(rid, [])) for k, v in pred.items()}, flush=True)

    (OUT / "e1_predictions.json").write_text(json.dumps(pred, ensure_ascii=False, indent=1), encoding="utf-8")
    text_of = {r["requirement_id"]: r["requirement_text"] for r in reqs}
    pool = sorted({(rid, c, i) for sysd in pred.values() for rid, ps in sysd.items() for c, i in ps})
    random.Random(42).shuffle(pool)
    with (OUT / "e1_pool.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["or_id", "requirement_text", "component", "intent", "component_desc", "intent_desc"])
        for rid, c, i in pool:
            w.writerow([rid, text_of[rid], c, i, COMPONENTS.get(c, ""), INTENTS.get(i, "")])
    print("pool size:", len(pool))


if __name__ == "__main__":
    main()
```

- [ ] **Step 2：运行**

Run: `PY scripts/101_stage1_baselines.py`
Expected: 打印 60 行进度。`pool size` 大约在 500–700 之间，作为标注工作量的估计写进工作簿说明。

---

### Task 8：专家工作簿（E1 金标、E2 κ、盲评）与评分（R1-4.2、R1-4.6、D9）

**Files:**
- Create: `scripts/97_build_expert_workbook.py`
- Create: `scripts/98_score_expert_workbook.py`
- Test: `tests/test_expert_scoring.py`

**Interfaces:**
- Produces: `data/expert_round2/expert_workbook.xlsx`，共 4 个 sheet：
  - `README`：标注说明
  - `S1_tagging`：列为 `item, eu_id(隐藏), text, component, intent`，后两列为下拉框
  - `S2_pairs`：列为 `item, or_id, requirement_text, component, component_desc, intent, intent_desc, relevant`，`relevant` 取 1 或 0；另加一列 `missing_pairs`，填写候选中遗漏的 `comp:intent;…`
  - `S3_values`：列为 `item, shall_statement, measurable_criterion, verdict`，`verdict` 取 correct、approx、wrong、unknown
- Produces: `data/expert_round2/expert_key.json`，即隐藏映射
- Produces: `exp_v4/expert_scores.json` 和 `exp_v4/e1_stage1_scores.json`
- 评分函数：`score_kappa(a: list, b: list) -> dict`、`prf(pred: dict, gold: dict) -> dict`、`bootstrap_f1(pred, gold, n=1000, seed=42) -> tuple`

- [ ] **Step 1：写评分测试**

```python
# tests/test_expert_scoring.py
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("sc", Path("scripts/98_score_expert_workbook.py"))
sc = importlib.util.module_from_spec(spec); spec.loader.exec_module(sc)


def test_kappa_skips_blank_and_invalid():
    a = ["pump", "", "cooler", "pump", "BAD"]
    b = ["pump", "pump", "cooler", "cooler", "pump"]
    r = sc.score_kappa(a, b, valid={"pump", "cooler"})
    assert r["n_used"] == 3 and r["n_skipped"] == 2


def test_prf_micro():
    pred = {"OR1": {("a", "x"), ("b", "y")}, "OR2": {("c", "z")}}
    gold = {"OR1": {("a", "x")}, "OR2": {("c", "z"), ("d", "w")}}
    r = sc.prf(pred, gold)
    assert r["precision"] == round(2 / 3 * 100, 1) and r["recall"] == round(2 / 3 * 100, 1)


def test_prf_empty_gold_no_crash():
    assert sc.prf({"OR1": set()}, {"OR1": set()})["f1"] is None
```

- [ ] **Step 2：运行，确认失败**

Run: `PY -m pytest tests/test_expert_scoring.py -q -p no:cacheprovider`，Expected: FAIL

- [ ] **Step 3：实现构建脚本**

```python
# scripts/97_build_expert_workbook.py
"""生成发给专家的盲标工作簿。SEED=42。
S1：从审计后的 KB 中按 tier 各抽 40 条（共 120 条），盲标 (component, intent)。
S2：E1 候选池（e1_pool.csv），逐对判断是否相关，遗漏的对写在 missing_pairs 列。
S3：新 RAG 中有数值的 shall（A/B 级）25 条 + no-RAG 中 Grade X 的 shall 25 条，打乱顺序，隐去臂别和引用。
"""
from __future__ import annotations

import csv
import json
import random
import re
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cooling_rag_mg.evidence_taxonomy import COMPONENTS, INTENTS

KB = ROOT / "data/processed/evidence_units_v3_audited.jsonl"
E4 = ROOT / "data/search_results/exp_v4"
OUT = ROOT / "data/expert_round2"
README = [
    "本工作簿共三部分，请独立完成，不要查看项目代码或数据。预计 5–6 小时。",
    "S1：阅读每条证据文本，从下拉框选出它最主要描述的部件(component)和工程方面(intent)，各选一个。",
    "S2：判断每个(部件, 方面)是否与该条原始需求直接相关：相关填1，不相关填0。若该需求还有其他相关对未列出，写在 missing_pairs，格式 comp:intent;comp:intent。",
    "S3：仅凭工程知识，判断每条 shall 的数值判据：correct(与规范或业界做法一致) / approx(±20%以内) / wrong(明显偏离) / unknown(超出把握)。",
    "部件与方面的含义见 S1 右侧的对照表。",
]


def main() -> None:
    rng = random.Random(42)
    OUT.mkdir(parents=True, exist_ok=True)
    kb = [json.loads(l) for l in KB.open(encoding="utf-8")]
    wb = Workbook()
    ws = wb.active; ws.title = "README"
    for line in README:
        ws.append([line])
    key: dict = {"S1": {}, "S2": {}, "S3": {}}

    s1 = wb.create_sheet("S1_tagging")
    s1.append(["item", "eu_id", "text", "component", "intent", "", "component_ref", "desc", "intent_ref", "desc"])
    sample = []
    for tier in ("L1", "L2", "L3"):
        pool = sorted([u for u in kb if u["kb_tier"] == tier], key=lambda u: u["id"])
        sample += rng.sample(pool, min(40, len(pool)))
    rng.shuffle(sample)
    for n, u in enumerate(sample, 1):
        s1.append([n, u["id"], (u.get("text") or "")[:1500], "", ""])
        key["S1"][str(n)] = {"eu_id": u["id"], "component": u.get("primary_component"),
                             "intent": u.get("primary_intent"), "tier": u["kb_tier"]}
    for r, (c, d) in enumerate(COMPONENTS.items(), 2):
        s1.cell(r, 7, c); s1.cell(r, 8, d)
    for r, (i, d) in enumerate(INTENTS.items(), 2):
        s1.cell(r, 9, i); s1.cell(r, 10, d)
    s1.column_dimensions["B"].hidden = True
    dvc = DataValidation(type="list", formula1=f"=$G$2:$G${len(COMPONENTS)+1}")
    dvi = DataValidation(type="list", formula1=f"=$I$2:$I${len(INTENTS)+1}")
    s1.add_data_validation(dvc); s1.add_data_validation(dvi)
    dvc.add(f"D2:D{len(sample)+1}"); dvi.add(f"E2:E{len(sample)+1}")

    s2 = wb.create_sheet("S2_pairs")
    s2.append(["item", "or_id", "requirement_text", "component", "component_desc", "intent",
               "intent_desc", "relevant", "missing_pairs"])
    rows = list(csv.DictReader((E4 / "e1_pool.csv").open(encoding="utf-8-sig")))
    for n, r in enumerate(rows, 1):
        s2.append([n, r["or_id"], r["requirement_text"], r["component"], r["component_desc"],
                   r["intent"], r["intent_desc"], "", ""])
        key["S2"][str(n)] = [r["or_id"], r["component"], r["intent"]]
    dv01 = DataValidation(type="list", formula1='"1,0"'); s2.add_data_validation(dv01)
    dv01.add(f"H2:H{len(rows)+1}")

    num = re.compile(r"\d")
    def numeric(path, grades):
        d = json.loads(path.read_text(encoding="utf-8"))
        return [(rs["source_requirement_id"], e) for rs in d["result_sets"]
                for e in rs["engineering_requirements"]
                if e.get("_grade") in grades and num.search(str(e.get("measurable_criterion", "")))]
    rp, npool = numeric(E4 / "rag_v4_results.json", {"A", "B"}), numeric(E4 / "norag_v4_results.json", {"X"})
    m = min(25, len(rp), len(npool))  # 两臂等量；若 RAG 的 A+B 不足 25 条，按实际数量抽取，并在论文中写明 n
    rag, nor = rng.sample(rp, m), rng.sample(npool, m)
    items = [("RAG", s, e) for s, e in rag] + [("no-RAG", s, e) for s, e in nor]
    rng.shuffle(items)
    s3 = wb.create_sheet("S3_values")
    s3.append(["item", "shall_statement", "measurable_criterion", "verdict"])
    for n, (arm, sid, e) in enumerate(items, 1):
        s3.append([n, e.get("shall_statement", ""), str(e.get("measurable_criterion", "")), ""])
        key["S3"][str(n)] = {"arm": arm, "sid": sid, "grade": e.get("_grade")}
    dvv = DataValidation(type="list", formula1='"correct,approx,wrong,unknown"'); s3.add_data_validation(dvv)
    dvv.add(f"D2:D{len(items)+1}")

    wb.save(OUT / "expert_workbook.xlsx")
    (OUT / "expert_key.json").write_text(json.dumps(key, ensure_ascii=False, indent=1), encoding="utf-8")
    print("S1", len(sample), "S2", len(rows), "S3", len(items), "->", OUT / "expert_workbook.xlsx")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4：实现评分脚本**

```python
# scripts/98_score_expert_workbook.py
"""对专家工作簿评分。
用法：PY scripts/98_score_expert_workbook.py <filled.xlsx> [<second_annotator.xlsx>]
输出：exp_v4/expert_scores.json（E2 κ、S3 盲评）、exp_v4/e1_stage1_scores.json（E1 P/R/F1）
"""
from __future__ import annotations

import json
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
E4 = ROOT / "data/search_results/exp_v4"
KEY = ROOT / "data/expert_round2/expert_key.json"


def score_kappa(a: list, b: list, valid: set | None = None) -> dict:
    from sklearn.metrics import cohen_kappa_score
    pairs = [(x, y) for x, y in zip(a, b) if x and y and (valid is None or (x in valid and y in valid))]
    if len(pairs) < 2:
        return {"kappa": None, "agreement_pct": None, "n_used": len(pairs), "n_skipped": len(a) - len(pairs)}
    xs, ys = zip(*pairs)
    k = cohen_kappa_score(xs, ys)
    return {"kappa": round(float(k), 3), "agreement_pct": round(sum(x == y for x, y in pairs) / len(pairs) * 100, 1),
            "n_used": len(pairs), "n_skipped": len(a) - len(pairs)}


def prf(pred: dict, gold: dict) -> dict:
    tp = sum(len(pred.get(r, set()) & g) for r, g in gold.items())
    np_ = sum(len(pred.get(r, set())) for r in gold)
    ng = sum(len(g) for g in gold.values())
    p = tp / np_ if np_ else None
    rc = tp / ng if ng else None
    f = (2 * p * rc / (p + rc)) if p and rc else None
    r1 = lambda v: None if v is None else round(v * 100, 1)
    return {"precision": r1(p), "recall": r1(rc), "f1": r1(f), "tp": tp, "n_pred": np_, "n_gold": ng}


def bootstrap_f1(pred: dict, gold: dict, n: int = 1000, seed: int = 42):
    rng = random.Random(seed); ids = sorted(gold); vals = []
    for _ in range(n):
        s = [rng.choice(ids) for _ in ids]
        g = {f"{i}_{k}": gold[r] for k, r in enumerate(s) for i in [r]}
        p = {f"{i}_{k}": pred.get(r, set()) for k, r in enumerate(s) for i in [r]}
        f = prf(p, g)["f1"]
        if f is not None:
            vals.append(f)
    vals.sort()
    return (vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1]) if vals else (None, None)


def _sheet(wb, name):
    ws = wb[name]; rows = list(ws.iter_rows(values_only=True)); hdr = rows[0]
    return [dict(zip(hdr, r)) for r in rows[1:] if r and r[0] is not None]


def main() -> None:
    from openpyxl import load_workbook
    from scipy.stats import fisher_exact
    sys.path.insert(0, str(ROOT))
    from cooling_rag_mg.evidence_taxonomy import COMPONENTS, INTENTS, valid_pair
    key = json.loads(KEY.read_text(encoding="utf-8"))
    wb = load_workbook(sys.argv[1], read_only=True)
    out: dict = {}

    s1 = _sheet(wb, "S1_tagging")
    kc = [key["S1"][str(r["item"])]["component"] for r in s1]
    ki = [key["S1"][str(r["item"])]["intent"] for r in s1]
    ec = [(r.get("component") or "").strip() for r in s1]
    ei = [(r.get("intent") or "").strip() for r in s1]
    out["E2_component"] = score_kappa(kc, ec, set(COMPONENTS))
    out["E2_intent"] = score_kappa(ki, ei, set(INTENTS))
    out["E2_pair"] = score_kappa([f"{a}|{b}" for a, b in zip(kc, ki)],
                                 [f"{a}|{b}" if a and b else "" for a, b in zip(ec, ei)])

    s2 = _sheet(wb, "S2_pairs")
    gold: dict = {}
    for r in s2:
        rid, c, i = key["S2"][str(r["item"])]
        gold.setdefault(rid, set())
        if str(r.get("relevant")).strip() == "1":
            gold[rid].add((c, i))
        for tok in str(r.get("missing_pairs") or "").split(";"):
            if ":" in tok:
                c2, i2 = [t.strip() for t in tok.split(":", 1)]
                if valid_pair(c2, i2):
                    gold[rid].add((c2, i2))
    preds = json.loads((E4 / "e1_predictions.json").read_text(encoding="utf-8"))
    e1 = {}
    for sysname, d in preds.items():
        pd = {rid: {tuple(p) for p in ps} for rid, ps in d.items()}
        res = prf(pd, gold)
        res["f1_ci95"] = bootstrap_f1(pd, gold)
        res["component_level"] = prf({r: {c for c, _ in v} for r, v in pd.items()},
                                     {r: {c for c, _ in v} for r, v in gold.items()})
        res["intent_level"] = prf({r: {i for _, i in v} for r, v in pd.items()},
                                  {r: {i for _, i in v} for r, v in gold.items()})
        e1[sysname] = res
    e1["n_requirements_with_gold"] = sum(1 for g in gold.values() if g)
    (E4 / "e1_stage1_scores.json").write_text(json.dumps(e1, ensure_ascii=False, indent=1), encoding="utf-8")

    s3 = _sheet(wb, "S3_values")
    tab = {"RAG": Counter(), "no-RAG": Counter()}
    for r in s3:
        v = (r.get("verdict") or "").strip()
        if v in {"correct", "approx", "wrong", "unknown"}:
            tab[key["S3"][str(r["item"])]["arm"]][v] += 1
    def fisher(pos):
        a = sum(tab["RAG"][p] for p in pos); b = sum(tab["RAG"].values()) - a
        c = sum(tab["no-RAG"][p] for p in pos); d = sum(tab["no-RAG"].values()) - c
        return round(float(fisher_exact([[a, b], [c, d]])[1]), 3)
    out["S3_blind"] = {"counts": {k: dict(v) for k, v in tab.items()},
                       "p_correct_or_approx": fisher({"correct", "approx"}),
                       "p_correct": fisher({"correct"}), "p_wrong": fisher({"wrong"})}

    if len(sys.argv) > 2:
        wb2 = load_workbook(sys.argv[2], read_only=True)
        t1 = _sheet(wb2, "S1_tagging")
        out["E2_inter_annotator_pair"] = score_kappa(
            [f"{(r.get('component') or '').strip()}|{(r.get('intent') or '').strip()}" for r in s1],
            [f"{(r.get('component') or '').strip()}|{(r.get('intent') or '').strip()}" for r in t1])
    (E4 / "expert_scores.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
```

- [ ] **Step 5：运行评分测试**：`PY -m pytest tests/test_expert_scoring.py -q -p no:cacheprovider`，Expected: 3 passed。
- [ ] **Step 6：生成工作簿并发出**

Run: `PY scripts/97_build_expert_workbook.py`
Expected: `S1 120 S2 <池大小> S3 50`。用户在 10-18 前把 xlsx 发给专家（D4），要求 10-25 前返回。
- [ ] **Step 7：收回后评分**：`PY scripts/98_score_expert_workbook.py data/expert_round2/expert_workbook_filled.xlsx`，然后 `PY scripts/100_paper_numbers.py`。

---

### Task 9：E5 泄漏检验（R1-4.3）

**Files:**
- Create: `scripts/102_leakage_check.py`

- [ ] **Step 1：实现**

```python
# scripts/102_leakage_check.py
"""E5：60 条源需求与 KB 的相似度。
对照组：KB 单元与"其他 KB 单元"之间的最近邻相似度，用来说明什么水平才算"近乎复制"。
指标：BGE-M3 最大余弦；最长公共子串（字符数）；源需求中含数字的比例，以及这些数字在 KB 中的命中率。
"""
from __future__ import annotations

import json
import re
import statistics as st
import sys
from difflib import SequenceMatcher
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cooling_rag_mg.config import get_config
from cooling_rag_mg.index_store import load_sentence_transformer

KB = ROOT / "data/processed/evidence_units_v3_audited.jsonl"
OR = ROOT / "data/processed/original_requirements_v2.jsonl"
OUT = ROOT / "data/search_results/exp_v4/e5_leakage.json"
NUM = re.compile(r"\d+(?:\.\d+)?")


def lcs_len(a: str, b: str) -> int:
    m = SequenceMatcher(None, a, b, autojunk=False).find_longest_match(0, len(a), 0, len(b))
    return m.size


def main() -> None:
    cfg = get_config()
    kb = [json.loads(l) for l in KB.open(encoding="utf-8")]
    reqs = [json.loads(l) for l in OR.open(encoding="utf-8")]
    model = load_sentence_transformer(cfg.model.embedding_model_path, device=cfg.model.device, label="[E5]")
    kv = model.encode([u["text"][:1000] for u in kb], normalize_embeddings=True, batch_size=32)
    rv = model.encode([r["requirement_text"] for r in reqs], normalize_embeddings=True)
    or_max = (rv @ kv.T).max(axis=1)
    kk = kv @ kv.T
    np.fill_diagonal(kk, -1)
    kb_nn = kk.max(axis=1)
    lcs = [max(lcs_len(r["requirement_text"], u["text"]) for u in kb) for r in reqs]
    kb_nums = {n for u in kb for n in NUM.findall(u["text"])}
    or_nums = [NUM.findall(r["requirement_text"]) for r in reqs]
    res = {"summary": {
        "or_max_cos_median": round(float(np.median(or_max)), 3), "or_max_cos_max": round(float(or_max.max()), 3),
        "kb_nn_cos_median": round(float(np.median(kb_nn)), 3),
        "or_lcs_chars_median": st.median(lcs), "or_lcs_chars_max": max(lcs),
        "or_len_chars_median": st.median(len(r["requirement_text"]) for r in reqs),
        "n_or_with_numbers": sum(1 for x in or_nums if x),
        "or_numbers_found_in_kb": sum(1 for x in or_nums for n in x if n in kb_nums),
        "or_numbers_total": sum(len(x) for x in or_nums)}}
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
```

- [ ] **Step 2：运行**：`PY scripts/102_leakage_check.py`。如实记录输出。如果 `or_lcs_chars_max` ≥ 40 或 `or_max_cos_max` ≥ `kb_nn_cos_median`，要把对应的那条需求找出来，在回复信中说明，不得省略。

---

### Task 10：E3 敏感性分析（R2：chunk、overlap、embedding、BM25 权重；R1-4.7 编码耗时）

**Files:**
- Modify: `cooling_rag_mg/hybrid_fusion.py`（`rrf_fuse` 增加 `weights: list[float] | None = None`）
- Create: `cooling_rag_mg/retrieval_variants.py`
- Create: `scripts/99_retrieval_sensitivity.py`
- Test: `tests/test_retrieval_variants.py`

**Interfaces:**
- Produces: `rrf_fuse(result_lists, *, id_key="id", k=60, weights=None)`。当 `weights=None` 时，结果与原函数完全一致。
- Produces: `retrieve_for_pairs(text: str, pairs: list[tuple[str,str]], searcher, *, mode: str = "hybrid", per_pair_k: int = 8, k0: int = 60, w_bm25: float = 0.5, max_total: int = 20) -> list[dict]`，其中 `mode ∈ {"hybrid","vector","bm25"}`
- Produces: `boundary_split_rate(texts: list[str], window: int, overlap: float) -> dict`
- Produces: `exp_v4/sensitivity/<variant>_results.json` 和 `exp_v4/sensitivity/summary.json`

- [ ] **Step 1：写测试**

```python
# tests/test_retrieval_variants.py
from cooling_rag_mg.hybrid_fusion import rrf_fuse
from cooling_rag_mg.retrieval_variants import boundary_split_rate, retrieve_for_pairs


def test_rrf_default_unchanged():
    a = [{"id": "x"}, {"id": "y"}]; b = [{"id": "y"}, {"id": "z"}]
    assert [r["id"] for r in rrf_fuse([a, b])] == [r["id"] for r in rrf_fuse([a, b], weights=[1.0, 1.0])]


def test_rrf_weight_shifts_order():
    a = [{"id": "x"}]; b = [{"id": "y"}]
    assert rrf_fuse([a, b], weights=[0.2, 1.8])[0]["id"] == "y"


class _S:
    def filtered_vector_search(self, q, k, components, intents):
        return [{"id": f"v{j}"} for j in range(k)]
    def filtered_bm25_search(self, q, k, components, intents):
        return [{"id": f"b{j}"} for j in range(k)]


def test_modes_and_cap():
    s = _S()
    assert all(r["id"].startswith("v") for r in retrieve_for_pairs("q", [("c", "i")], s, mode="vector"))
    assert all(r["id"].startswith("b") for r in retrieve_for_pairs("q", [("c", "i")], s, mode="bm25"))
    assert len(retrieve_for_pairs("q", [("c", "i"), ("c2", "i2")], s, per_pair_k=12, max_total=20)) == 20


def test_boundary_split_rate_atomic_text_zero():
    r = boundary_split_rate(["当冷却水温度高于85°C时应报警。"], window=512, overlap=0.0)
    assert r["n_condition_value_sentences"] == 1 and r["split_pct"] == 0.0


def test_boundary_split_rate_small_window_splits():
    t = "x" * 120 + "当冷却水温度高于85°C时应报警。"
    r = boundary_split_rate([t], window=128, overlap=0.0)
    assert r["split_pct"] == 100.0
```

- [ ] **Step 2：运行，确认失败**：`PY -m pytest tests/test_retrieval_variants.py -q -p no:cacheprovider`

- [ ] **Step 3：给 `rrf_fuse` 加权重**，在 `cooling_rag_mg/hybrid_fusion.py` 中：

```python
def rrf_fuse(result_lists: list[list[dict[str, Any]]], *, id_key: str = "id", k: int = 60,
             weights: list[float] | None = None) -> list[dict[str, Any]]:
    fused: dict[str, dict[str, Any]] = {}
    scores: dict[str, float] = {}
    ws = weights or [1.0] * len(result_lists)
    for w, results in zip(ws, result_lists):
        for rank, item in enumerate(results, start=1):
            rid = str(item.get(id_key) or item.get("chunk_id") or item.get("id"))
            if not rid:
                continue
            scores[rid] = scores.get(rid, 0.0) + w / (k + rank)
            if rid not in fused:
                fused[rid] = dict(item)
    for rid, score in scores.items():
        fused[rid]["rrf_score"] = score
    return sorted(fused.values(), key=lambda x: x.get("rrf_score", 0.0), reverse=True)
```

- [ ] **Step 4：实现 `retrieval_variants.py`**

```python
# cooling_rag_mg/retrieval_variants.py
"""E3 用到的检索变体（只给定 pairs 做检索，不调 LLM），以及切分边界分析。"""
from __future__ import annotations

import re
from typing import Any

from cooling_rag_mg.hybrid_fusion import rrf_fuse

_COND = re.compile(r"(当|若|如果|除|但|否则|在.{0,8}时|以下|以上|unless|except|where|when|if|provided that|in case)", re.I)
_VAL = re.compile(r"\d+(?:\.\d+)?\s*(?:°C|℃|MPa|bar|kPa|%|s\b|秒|min|分钟|m³/h|L/min|rpm|kW|mm)")
_SENT = re.compile(r"[^。；;.\n]+[。；;.\n]?")


def retrieve_for_pairs(text: str, pairs: list[tuple[str, str]], searcher: Any, *, mode: str = "hybrid",
                       per_pair_k: int = 8, k0: int = 60, w_bm25: float = 0.5,
                       max_total: int = 20) -> list[dict]:
    seen: dict[str, dict] = {}
    for comp, intent in pairs:
        vec = searcher.filtered_vector_search(text, per_pair_k, components=[comp], intents=[intent]) \
            if mode in ("hybrid", "vector") else []
        bm = searcher.filtered_bm25_search(text, per_pair_k, components=[comp], intents=[intent]) \
            if mode in ("hybrid", "bm25") else []
        lists = [l for l in (vec, bm) if l]
        if mode == "hybrid":
            ranked = rrf_fuse([vec, bm], k=k0, weights=[2 * (1 - w_bm25), 2 * w_bm25])
        else:
            ranked = rrf_fuse(lists, k=k0)
        for cand in ranked:
            cid = cand.get("id")
            if cid and cid not in seen:
                seen[cid] = cand
            if len(seen) >= max_total:
                return list(seen.values())
    return list(seen.values())


def boundary_split_rate(texts: list[str], window: int, overlap: float) -> dict:
    """统计"同时含条件词和数值阈值的句子"中，有多少句没有被任何一个固定窗口完整覆盖。"""
    step = max(1, int(window * (1 - overlap)))
    n = split = 0
    for t in texts:
        starts = list(range(0, max(1, len(t) - window + 1), step)) or [0]
        if starts[-1] + window < len(t):
            starts.append(len(t) - window)
        for m in _SENT.finditer(t):
            s = m.group(0)
            if not (_COND.search(s) and _VAL.search(s)):
                continue
            n += 1
            a, b = m.start(), m.end()
            if not any(st_ <= a and b <= st_ + window for st_ in starts):
                split += 1
    return {"window": window, "overlap": overlap, "n_condition_value_sentences": n,
            "split_pct": round(split / n * 100, 1) if n else None}
```

- [ ] **Step 5：运行测试**：`PY -m pytest tests/test_retrieval_variants.py -q -p no:cacheprovider`，Expected: 5 passed

- [ ] **Step 6：下载替代 embedding 模型**（多语种，无需加前缀）

```bash
PY -c "import os;os.environ['HF_ENDPOINT']='https://hf-mirror.com';from huggingface_hub import snapshot_download;print(snapshot_download('sentence-transformers/paraphrase-multilingual-mpnet-base-v2',local_dir='D:/models/mpnet-multilingual'))"
```
Expected: 打印 `D:/models/mpnet-multilingual`。如果 hf-mirror 失败，去掉 `HF_ENDPOINT` 再试一次（本机代理可以访问 huggingface.co）。

- [ ] **Step 7：实现 `99_retrieval_sensitivity.py`**

```python
# scripts/99_retrieval_sensitivity.py
"""E3 敏感性分析。
--part boundary  ：切分边界分析和截断分析（不调 LLM）
--part retrieval ：用固定的 pairs（取自 Task 6 重跑的 _pairs_used）跑各检索变体，计算检索层指标（不调 LLM）
--part e2e --variant <名称> ：对单个变体跑端到端（证据选择 T=0 → Stage 3 → Stage 4 → 以 KB 为准分级）
--part summary   ：汇总，生成 summary.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import statistics as st
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cooling_rag_mg.config import get_config
from cooling_rag_mg.grade_classifier import classify_result_set
from cooling_rag_mg.index_store import HybridIndexSearcher, build_index, load_index
from cooling_rag_mg.retrieval_variants import boundary_split_rate, retrieve_for_pairs

KBP = ROOT / "data/processed/evidence_units_v3_audited.jsonl"
V3 = ROOT / "data/search_results/exp_v3/rag_v3_results.json"
V4 = ROOT / "data/search_results/exp_v4/rag_v4_results.json"
OR = ROOT / "data/processed/original_requirements_v2.jsonl"
OUT = ROOT / "data/search_results/exp_v4/sensitivity"
ALT_IDX = ROOT / "data/indexes/evidence_units_mpnet"
NUMV = re.compile(r"\d+(?:\.\d+)?\s*(?:°C|℃|MPa|bar|kPa|%|s\b|秒|min|m³/h|L/min|rpm|kW|mm)")
VARIANTS = {
    "default": dict(mode="hybrid"), "vector_only": dict(mode="vector"), "bm25_only": dict(mode="bm25"),
    "w_bm25_0.25": dict(mode="hybrid", w_bm25=0.25), "w_bm25_0.75": dict(mode="hybrid", w_bm25=0.75),
    "k0_10": dict(mode="hybrid", k0=10), "k0_100": dict(mode="hybrid", k0=100),
    "k_4": dict(mode="hybrid", per_pair_k=4), "k_12": dict(mode="hybrid", per_pair_k=12),
    "embed_mpnet": dict(mode="hybrid", _index="mpnet"),
}
E2E = ["vector_only", "bm25_only", "embed_mpnet", "trunc_1200"]


def _kb():
    return {json.loads(l)["id"]: json.loads(l) for l in KBP.open(encoding="utf-8")}


def _pairs():
    v3 = json.loads(V3.read_text(encoding="utf-8"))
    return {rs["source_requirement_id"]: [tuple(p.split("×")) for p in rs.get("_pairs_used", [])]
            for rs in v3["result_sets"]}


def _searcher(name: str, cfg):
    if name == "mpnet":
        if not (ALT_IDX / "faiss.index").exists():
            build_index(jsonl_path=KBP, output_dir=ALT_IDX, text_field="search_text",
                        model_path="D:/models/mpnet-multilingual", device=cfg.model.device, normalize=True)
        return HybridIndexSearcher(load_index(ALT_IDX), device="cpu")
    return HybridIndexSearcher(load_index(ROOT / "data/indexes/evidence_units"), device="cpu")


def part_boundary() -> dict:
    kb = _kb()
    v4 = json.loads(V4.read_text(encoding="utf-8"))
    used = {i for rs in v4["result_sets"] for i in rs.get("_evidence_values", {})}
    texts = [kb[i]["text"] for i in used if i in kb]
    lim = int(os.getenv("RAG_EU_TEXT_LIMIT", "500"))
    res = {"n_used_units": len(texts),
           "pct_used_units_longer_than_prompt_limit": round(sum(len(t) > lim for t in texts) / len(texts) * 100, 1),
           "pct_values_beyond_prompt_limit": round(
               sum(1 for t in texts for m in NUMV.finditer(t) if m.start() >= lim) /
               max(1, sum(1 for t in texts for _ in NUMV.finditer(t))) * 100, 1),
           "eu_atomic": boundary_split_rate(texts, window=10**6, overlap=0.0),
           "fixed_windows": [boundary_split_rate(texts, w, o) for w in (128, 256, 512) for o in (0.0, 0.2)]}
    return res


def part_retrieval(cfg) -> dict:
    kb, pairs = _kb(), _pairs()
    text = {json.loads(l)["requirement_id"]: json.loads(l)["requirement_text"] for l in OR.open(encoding="utf-8")}
    searchers = {"default": _searcher("default", cfg)}
    sets: dict[str, dict[str, list[str]]] = {}
    t_enc = {}
    for name, kw in VARIANTS.items():
        kw = dict(kw); idx = kw.pop("_index", "default")
        if idx not in searchers:
            searchers[idx] = _searcher(idx, cfg)
        s = searchers[idx]
        sets[name] = {}
        t0 = time.perf_counter()
        for rid, ps in pairs.items():
            sets[name][rid] = [r["id"] for r in retrieve_for_pairs(text[rid], ps, s, **kw)] if ps else []
        t_enc[name] = round((time.perf_counter() - t0) / max(1, len(pairs)), 3)
    def jac(a, b):
        a, b = set(a), set(b); return len(a & b) / len(a | b) if a | b else 1.0
    out = {}
    for name, d in sets.items():
        ids = [i for v in d.values() for i in v]
        out[name] = {
            "jaccard_vs_default_mean": round(st.mean(jac(d[r], sets["default"][r]) for r in d), 3),
            "units_per_req_mean": round(st.mean(len(v) for v in d.values()), 2),
            "l1_share_pct": round(sum(kb[i]["kb_tier"] == "L1" for i in ids) / max(1, len(ids)) * 100, 1),
            "numeric_unit_share_pct": round(sum(bool(NUMV.search(kb[i]["text"])) for i in ids) / max(1, len(ids)) * 100, 1),
            "sec_per_req_cpu_query": t_enc[name]}
    (OUT / "retrieval_sets.json").write_text(json.dumps(sets, ensure_ascii=False), encoding="utf-8")
    return out


def part_e2e(variant: str, cfg) -> None:
    from cooling_rag_mg.kb_value_extractor import annotate_evidence_units
    from cooling_rag_mg.req_generation_v2 import generate_rag_v3
    from cooling_rag_mg.structured_req_generator import generate_structured_shalls
    kb, pairs = _kb(), _pairs()
    text = {json.loads(l)["requirement_id"]: json.loads(l)["requirement_text"] for l in OR.open(encoding="utf-8")}
    client, model = cfg.deepseek.make_client(), cfg.deepseek.model
    if variant == "trunc_1200":
        os.environ["RAG_EU_TEXT_LIMIT"] = "1200"; os.environ["RAG_EXTRACT_CHAR_LIMIT"] = "2400"
        import importlib, cooling_rag_mg.structured_req_generator as sg
        importlib.reload(sg); generate_structured_shalls = sg.generate_structured_shalls
        v3 = json.loads(V3.read_text(encoding="utf-8"))
        selected = {rs["source_requirement_id"]: sorted({i for er in rs["engineering_requirements"]
                                                          for i in er.get("evidence_ids", [])})
                    for rs in v3["result_sets"]}
    else:
        sets = json.loads((OUT / "retrieval_sets.json").read_text(encoding="utf-8"))[variant]
        selected = {}
    out = []
    for rid in sorted(text):
        if variant != "trunc_1200":
            ev = [kb[i] for i in sets.get(rid, []) if i in kb]
            ers = generate_rag_v3(text[rid], ev, client, model, temperature=0.0) if ev else []
            selected[rid] = sorted({i for er in ers for i in er.get("evidence_ids", [])})
        eus = [kb[i] for i in selected[rid] if i in kb]
        ann = annotate_evidence_units(eus, client, model)
        shalls = generate_structured_shalls(source_requirement=text[rid], annotated_evidence=ann,
                                            client=client, model=model) if ann else []
        out.append(classify_result_set({"source_requirement_id": rid, "_n_evidence": len(ann),
                                        "engineering_requirements": shalls}, kb))
        print(variant, rid, len(shalls), flush=True)
    (OUT / f"{variant}_results.json").write_text(
        json.dumps({"arm": variant, "result_sets": out}, ensure_ascii=False, indent=1), encoding="utf-8")


def part_summary() -> dict:
    spec = __import__("importlib.util").util.spec_from_file_location("pn", ROOT / "scripts/100_paper_numbers.py")
    pn = __import__("importlib.util").util.module_from_spec(spec); spec.loader.exec_module(pn)
    kb = _kb()
    res = {"boundary": json.loads((OUT / "boundary.json").read_text(encoding="utf-8")),
           "retrieval": json.loads((OUT / "retrieval.json").read_text(encoding="utf-8")),
           "e2e": {"default": pn.grade_summary(json.loads(V4.read_text(encoding="utf-8")), kb)}}
    for v in E2E:
        p = OUT / f"{v}_results.json"
        if p.exists():
            res["e2e"][v] = pn.grade_summary(json.loads(p.read_text(encoding="utf-8")), kb)
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", required=True, choices=["boundary", "retrieval", "e2e", "summary"])
    ap.add_argument("--variant", default="")
    a = ap.parse_args()
    cfg = get_config(); OUT.mkdir(parents=True, exist_ok=True)
    if a.part == "boundary":
        r = part_boundary(); (OUT / "boundary.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    elif a.part == "retrieval":
        r = part_retrieval(cfg); (OUT / "retrieval.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    elif a.part == "e2e":
        assert a.variant in E2E, f"variant must be one of {E2E}"
        part_e2e(a.variant, cfg); r = {"done": a.variant}
    else:
        r = part_summary(); (OUT / "summary.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(r, ensure_ascii=False, indent=1)[:3000])


if __name__ == "__main__":
    main()
```

- [ ] **Step 8：按顺序运行**（e2e 每个变体约 1–2 小时，可以挂后台串行跑）

```bash
PY scripts/99_retrieval_sensitivity.py --part boundary
PY scripts/99_retrieval_sensitivity.py --part retrieval
PY scripts/99_retrieval_sensitivity.py --part e2e --variant vector_only
PY scripts/99_retrieval_sensitivity.py --part e2e --variant bm25_only
PY scripts/99_retrieval_sensitivity.py --part e2e --variant embed_mpnet
PY scripts/99_retrieval_sensitivity.py --part e2e --variant trunc_1200
PY scripts/99_retrieval_sensitivity.py --part summary
PY scripts/100_paper_numbers.py
```
Expected:
- boundary 中 `eu_atomic.split_pct` 应为 0.0，这是由构造决定的，正好用来回答审稿人。
- `fixed_windows` 给出 6 个比例。
- retrieval 部分输出 10 个变体，其中 `default` 的 Jaccard 为 1.0。
- summary 中的 `e2e` 包含 default 和 4 个变体的分级分布。

- [ ] **Step 9：GPU 与 CPU 查询编码耗时**（R1-4.7）

```bash
PY -c "
import time,json
from cooling_rag_mg.index_store import load_sentence_transformer
qs=[json.loads(l)['requirement_text'] for l in open('data/processed/original_requirements_v2.jsonl',encoding='utf-8')]
for dev in ['cpu','cuda']:
    m=load_sentence_transformer('D:/models/bge-m3',device=dev,label='t'); m.encode(qs[:2])
    t=time.perf_counter(); [m.encode([q],normalize_embeddings=True) for q in qs]; print(dev, round((time.perf_counter()-t)/len(qs)*1000,1),'ms/query')
" > data/search_results/exp_v4/encode_latency.txt; cat data/search_results/exp_v4/encode_latency.txt
```
Expected: 两行，分别为 cpu 和 cuda 的每次查询毫秒数。如实写进论文。

---

### Task 11：派生类型、冲突检测与复核路由（R2 派生、R2 冲突、R1-6.3）

**Files:**
- Create: `cooling_rag_mg/review_routing.py`
- Create: `scripts/103_routing_report.py`
- Modify: `scripts/92_export_ea_native_xmi.py`（notes 和 TaggedValue 中写入派生类型与路由）
- Test: `tests/test_review_routing.py`

**Interfaces:**
- Consumes: `numeric_norm.extract_numbers`、`grade_classifier.valid_citation_ids`、v4 结果中的 `_evidence_values`（Task 5 Step 4 产出）
- Produces: `derivation_type(er: dict, kb: dict) -> str`，取值为 `"Unsupported"|"Deferred"|"Direct"|"Synthesized"|"Derived"`
- Produces: `conflict_flag(er: dict, kb: dict, evidence_values: dict[str, list[dict]]) -> dict | None`
- Produces: `review_route(er: dict, kb: dict, evidence_values: dict) -> tuple[str, str]`，route 取值为 `"SPOT_CHECK"|"ENGINEER_CONFIRM"|"OPEN_ITEM"|"ADJUDICATE"|"VERIFY_OR_REJECT"`

**规则（写进论文 Methods，与代码一一对应）**
- **派生类型**，按顺序判定，命中即停：
  1. 没有有效 KB 引用 → **Unsupported**
  2. 判据含 `{{TBD` → **Deferred**
  3. 判据中的所有数字都出现在**同一条**被引单元的正文里 → **Direct**
  4. 所有数字都能在被引单元中找到，但分散在 ≥2 条单元里；或者判据是定性的、且引用了 ≥2 条单元 → **Synthesized**
  5. 其余（有引用，但数字不是原文照搬，或是只引用 1 条单元的定性判据）→ **Derived**
- **冲突**：被引单元 ≥2 条，且其中至少 2 条单元抽取出的值与判据单位相同，但这些单元给出的数值集合互不相交 → 标记 `conflict`。
- **复核路由**，优先级从高到低：
  - `conflict` → **ADJUDICATE**
  - Unsupported 且判据有数值（即 Grade X）→ **VERIFY_OR_REJECT**
  - Deferred → **OPEN_ITEM**
  - Grade A 且派生类型为 Direct → **SPOT_CHECK**
  - 其余有引用的（含 tier-b：只引用 L2/L3 来源的 Grade B，以及 Derived、Synthesized）→ **ENGINEER_CONFIRM**
  - 定性、且无数值的 Unsupported（只在 no-RAG 中出现）→ **ENGINEER_CONFIRM**

- [ ] **Step 1：写测试**

```python
# tests/test_review_routing.py
from cooling_rag_mg.review_routing import conflict_flag, derivation_type, review_route

KB = {
    "E1": {"id": "E1", "kb_tier": "L1", "text": "条款 3.2.1 高温报警 90 °C", "metadata": {"location": "3.2.1"}},
    "E2": {"id": "E2", "kb_tier": "L2", "text": "HT outlet alarm 95 °C", "metadata": {}},
    "E3": {"id": "E3", "kb_tier": "L2", "text": "pressure 3 bar", "metadata": {}},
}


def er(mc, cits, grade):
    return {"measurable_criterion": mc, "evidence_citations": [{"kb_id": c} for c in cits], "_grade": grade}


def test_direct_with_unit_variants():
    assert derivation_type(er("≤ 90℃", ["E1"], "A"), KB) == "Direct"


def test_synthesized_across_units():
    assert derivation_type(er("90°C；3 bar", ["E1", "E3"], "A"), KB) == "Synthesized"


def test_derived_when_number_not_in_text():
    assert derivation_type(er("88°C", ["E1"], "A"), KB) == "Derived"


def test_unsupported_and_deferred():
    assert derivation_type(er("90°C", [], "X"), KB) == "Unsupported"
    assert derivation_type(er("{{TBD|unit:°C}}", ["E1"], "C"), KB) == "Deferred"


def test_conflict_disjoint_values_same_unit():
    ev = {"E1": [{"value_text": "90 °C", "unit": "°C"}], "E2": [{"value_text": "95 °C", "unit": "°C"}]}
    f = conflict_flag(er("90°C", ["E1", "E2"], "A"), KB, ev)
    assert f is not None and set(f["units"]) == {"E1", "E2"}
    assert review_route(er("90°C", ["E1", "E2"], "A"), KB, ev)[0] == "ADJUDICATE"


def test_unit_not_confused_by_letter_s():
    from cooling_rag_mg.review_routing import _unit_of
    assert _unit_of("pressure loss across strainers 3 bar") == "bar"
    assert _unit_of("响应时间 ≤ 2 秒") == "s"
    assert _unit_of("满足要求 as specified") == ""


def test_routes():
    assert review_route(er("90°C", ["E1"], "A"), KB, {})[0] == "SPOT_CHECK"
    assert review_route(er("95°C", ["E2"], "B"), KB, {})[0] == "ENGINEER_CONFIRM"
    assert review_route(er("{{TBD|unit:°C}}", ["E1"], "C"), KB, {})[0] == "OPEN_ITEM"
    assert review_route(er("90°C", [], "X"), KB, {})[0] == "VERIFY_OR_REJECT"
```

- [ ] **Step 2：运行，确认失败**：`PY -m pytest tests/test_review_routing.py -q -p no:cacheprovider`

- [ ] **Step 3：实现**

```python
# cooling_rag_mg/review_routing.py
"""派生类型（ISO/IEC/IEEE 29148 风格的来源关系）、引用证据之间的冲突检测、复核路由。均为确定性规则。"""
from __future__ import annotations

import re
import unicodedata

from cooling_rag_mg.grade_classifier import valid_citation_ids
from cooling_rag_mg.numeric_norm import extract_numbers


_UNIT = re.compile(r"\d\s*(°C|MPa|kPa|bar|%|m³/h|L/min|rpm|kW|mm|min|分钟|秒|s(?![A-Za-z]))")
_UNIT_NORM = {"分钟": "min", "秒": "s"}


def _unit_of(s: str) -> str:
    """返回紧跟在数字后面的第一个物理单位（NFKC 后 ℃ 变为 °C）；没有则返回空串。"""
    m = _UNIT.search(unicodedata.normalize("NFKC", s or ""))
    return _UNIT_NORM.get(m.group(1), m.group(1)) if m else ""


def derivation_type(er: dict, kb: dict) -> str:
    mc = str(er.get("measurable_criterion") or "")
    ids = valid_citation_ids(er.get("evidence_citations", []), kb)
    if not ids:
        return "Unsupported"
    if "{{TBD" in mc:
        return "Deferred"
    nums = extract_numbers(mc)
    if not nums:
        return "Synthesized" if len(ids) >= 2 else "Derived"
    per_unit = {i: set(extract_numbers(kb[i].get("text", ""))) for i in ids}
    if any(set(nums) <= s for s in per_unit.values()):
        return "Direct"
    if set(nums) <= set().union(*per_unit.values()) and len(ids) >= 2:
        return "Synthesized"
    return "Derived"


def conflict_flag(er: dict, kb: dict, evidence_values: dict) -> dict | None:
    ids = valid_citation_ids(er.get("evidence_citations", []), kb)
    unit = _unit_of(str(er.get("measurable_criterion") or ""))
    if len(ids) < 2 or not unit:
        return None
    sets = {}
    for i in ids:
        vals = {n for v in evidence_values.get(i, []) if _unit_of(v.get("unit", "") + v.get("value_text", "")) == unit
                for n in extract_numbers(v.get("value_text", ""))}
        if vals:
            sets[i] = vals
    if len(sets) < 2:
        return None
    keys = list(sets)
    disjoint = all(not (sets[a] & sets[b]) for x, a in enumerate(keys) for b in keys[x + 1:])
    return {"unit": unit, "units": keys, "values": {k: sorted(v) for k, v in sets.items()}} if disjoint else None


def review_route(er: dict, kb: dict, evidence_values: dict) -> tuple[str, str]:
    if conflict_flag(er, kb, evidence_values):
        return "ADJUDICATE", "cited sources state different values for the same quantity"
    d = derivation_type(er, kb)
    g = er.get("_grade")
    if d == "Unsupported" and g == "X":
        return "VERIFY_OR_REJECT", "numeric value without a valid KB citation"
    if d == "Deferred":
        return "OPEN_ITEM", "value deferred to named source document"
    if g == "A" and d == "Direct":
        return "SPOT_CHECK", "value quoted verbatim from an L1 clause-referenced unit"
    ids = valid_citation_ids(er.get("evidence_citations", []), kb)
    if ids and all(kb[i].get("kb_tier") != "L1" for i in ids):
        return "ENGINEER_CONFIRM", "cites manufacturer/operational guidance only (tier-b)"
    return "ENGINEER_CONFIRM", f"derivation type {d}"
```

- [ ] **Step 4：运行测试**：`PY -m pytest tests/test_review_routing.py -q -p no:cacheprovider`，Expected: 7 passed

- [ ] **Step 5：写统计脚本 `103_routing_report.py`**

```python
# scripts/103_routing_report.py
"""对 RAG 和 no-RAG 结果统计派生类型、冲突数、路由分布，并导出 30 条人工核验样本（SEED=42）。"""
from __future__ import annotations

import csv
import json
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cooling_rag_mg.review_routing import conflict_flag, derivation_type, review_route

E4 = ROOT / "data/search_results/exp_v4"
KB = {json.loads(l)["id"]: json.loads(l) for l in
      (ROOT / "data/processed/evidence_units_v3_audited.jsonl").open(encoding="utf-8")}


def main() -> None:
    rep, conflicts, sample_pool = {}, [], []
    for arm, fn in [("rag", "rag_v4_results.json"), ("norag", "norag_v4_results.json")]:
        d = json.loads((E4 / fn).read_text(encoding="utf-8"))
        dt, rt = Counter(), Counter()
        for rs in d["result_sets"]:
            ev = rs.get("_evidence_values", {})
            for k, er in enumerate(rs["engineering_requirements"]):
                dt[derivation_type(er, KB)] += 1
                route, why = review_route(er, KB, ev)
                rt[route] += 1
                f = conflict_flag(er, KB, ev)
                if f:
                    conflicts.append({"or": rs["source_requirement_id"], "k": k, **f,
                                      "criterion": er.get("measurable_criterion")})
                if arm == "rag":
                    sample_pool.append((rs["source_requirement_id"], k, er))
        rep[arm] = {"derivation": dict(dt), "routes": dict(rt)}
    rep["conflicts"] = conflicts
    rep["n_conflicts"] = len(conflicts)
    (E4 / "routing_report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    rng = random.Random(42)
    with (E4 / "derivation_validation_30.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["or", "k", "rule_type", "manual_type", "criterion", "cited_texts"])
        for sid, k, er in rng.sample(sample_pool, min(30, len(sample_pool))):
            from cooling_rag_mg.grade_classifier import valid_citation_ids
            ids = valid_citation_ids(er.get("evidence_citations", []), KB)
            w.writerow([sid, k, derivation_type(er, KB), "", er.get("measurable_criterion"),
                        " || ".join(f"{i}: {KB[i]['text'][:300]}" for i in ids)])
    print(json.dumps({k: v for k, v in rep.items() if k != "conflicts"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
```

- [ ] **Step 6：运行**：`PY scripts/103_routing_report.py`。作者在 `derivation_validation_30.csv` 的 `manual_type` 列人工填写类型，然后计算一致率：`PY -c "import csv;r=list(csv.DictReader(open('data/search_results/exp_v4/derivation_validation_30.csv',encoding='utf-8-sig')));ok=sum(x['rule_type']==x['manual_type'] for x in r if x['manual_type']);n=sum(1 for x in r if x['manual_type']);print(ok,n,round(ok/n*100,1))"`，把结果追加到 `routing_report.json` 的 `"rule_validation"` 键下。所有 `conflicts` 逐条人工确认后，写入 `rerun_notes.md`。

- [ ] **Step 7：EA 导出写入路由信息**。在 `scripts/92_export_ea_native_xmi.py` 中：
  - 顶部加 `from cooling_rag_mg.review_routing import derivation_type, review_route`，并加载 KB（写法同 103）。
  - 在 notes 拼接处（原第 283–287 行）加一行 `f"Derivation: {derivation_type(er, KB)}\nReview: {review_route(er, KB, rs.get('_evidence_values', {}))[0]}\n"`。
  - 再增加 TaggedValue `("review_route", route)`。由于 `classifier_role` 的 tv 列表是在函数内部构造的，需要给 `classifier_role` 加一个参数 `extra_tv: list[tuple[str,str]] | None = None`，在 return 之前执行 `tv += extra_tv or []`。
  - 运行 `PY scripts/92_export_ea_native_xmi.py --sets <Task 12 选定的 3 个 OR>`，Expected: 生成的 XML 中包含 `review_route`。

---

### Task 12：RAG 与 no-RAG 并排对比案例（R2）

**Files:**
- Create: `scripts/104_side_by_side.py`
- Create: `paper_wiley_submission_to_be_revised/table_side_by_side.tex`
- Delete（从正文移除，文件保留）：`table_req_case.tex` 的 `\input`

**选择规则（确定性的，避免挑樱桃）**
- **案例 1（两侧都合理）**：同一条 OR、同一参数单位下，RAG 的 Direct 值与 no-RAG 的 X 值数值相同或相差 ≤20%，且 RAG 引用的是 L1 单元。在满足条件的 OR 中取 ID 最小的一条。
- **案例 2（no-RAG 出错）**：只能从 `paired_conflict_analysis.json` 中、P0 审计后**仍有原文条款支撑**的冲突里选（例如 CCS Pt3 Ch2 §2.7.1.2 的 1.5p 试压，但它只适用于 Class I/II 管路，见下面的注意事项）。如果没有任何冲突能核实到具体条款，案例 2 改选"no-RAG 给出具体值、RAG 给出 Deferred"的一条，并在表注中写明"no-RAG 的数值无法核验"，**不写"错误"**。

> **注意（已查原文）**：CCS 2024 Pt3 Ch2 §2.7.1.2 规定 Ps = 1.5p，但适用范围是 Class I 和 Class II 管路（§2.7.1.1）。冷却水管通常属于 Class III，装船后只要求做工作压力下的泄漏检查（§2.7.3.1）。所以原稿冲突表 (a) 中"1.25× 对比 1.5×"这一条**必须注明管路等级条件**，不能直接写成规范冲突；原稿写的条款号 "Tbl 3.9.2.2.8" 也是错的。

- [ ] **Step 1：实现候选筛选**（输出候选，最终由作者选定）

```python
# scripts/104_side_by_side.py
"""按计划 Task 12 的规则筛选并排对比的候选案例，输出 side_by_side_candidates.json。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cooling_rag_mg.grade_classifier import valid_citation_ids
from cooling_rag_mg.numeric_norm import extract_numbers
from cooling_rag_mg.review_routing import _unit_of, derivation_type

E4 = ROOT / "data/search_results/exp_v4"
KB = {json.loads(l)["id"]: json.loads(l) for l in
      (ROOT / "data/processed/evidence_units_v3_audited.jsonl").open(encoding="utf-8")}


def main() -> None:
    rag = {r["source_requirement_id"]: r for r in json.loads((E4 / "rag_v4_results.json").read_text(encoding="utf-8"))["result_sets"]}
    nor = {r["source_requirement_id"]: r for r in json.loads((E4 / "norag_v4_results.json").read_text(encoding="utf-8"))["result_sets"]}
    case1, case2 = [], []
    for sid in sorted(rag):
        for a in rag[sid]["engineering_requirements"]:
            ua, na = _unit_of(str(a.get("measurable_criterion"))), extract_numbers(str(a.get("measurable_criterion")))
            ids = valid_citation_ids(a.get("evidence_citations", []), KB)
            for b in nor.get(sid, {}).get("engineering_requirements", []):
                if b.get("_grade") != "X":
                    continue
                ub, nb = _unit_of(str(b.get("measurable_criterion"))), extract_numbers(str(b.get("measurable_criterion")))
                if derivation_type(a, KB) == "Direct" and ua and ua == ub and na and nb \
                        and any(KB[i]["kb_tier"] == "L1" for i in ids) \
                        and abs(float(na[0]) - float(nb[0])) <= 0.2 * max(abs(float(na[0])), 1e-9):
                    case1.append({"or": sid, "rag": a, "norag": b, "cited": ids})
                if a.get("_grade") == "C" and "{{TBD" in str(a.get("measurable_criterion")) and ua and ua == ub:
                    case2.append({"or": sid, "rag": a, "norag": b, "cited": ids})
    pc = json.loads((E4 / "paired_conflict_analysis.json").read_text(encoding="utf-8"))
    out = {"case1_candidates": case1[:10], "case2_deferred_candidates": case2[:10], "paired_conflicts": pc}
    (E4 / "side_by_side_candidates.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("case1:", len(case1), "case2(deferred):", len(case2))


if __name__ == "__main__":
    main()
```

- [ ] **Step 2：运行并选定**：`PY scripts/104_side_by_side.py`。按规则选出案例 1 和案例 2，同时确认 Task 13 EA 导出用的 3 个 OR（优先选这两个案例所在的 OR，再补 1 个含 Grade B 的）。
- [ ] **Step 3：写 `table_side_by_side.tex`**（table*，6 列：Source requirement / Arm / Shall (EN) / Criterion / Provenance (KB id, tier, clause) / Grade & review route）。每个案例两行，分别是 RAG 和 no-RAG。中文 shall 由作者译成英文，**不改变数值**。表注写明选择规则，即上面两条的英文版。

---

## 阶段 C：图表与正文

### Task 13：图表重组（R2 Fig 4/5；R1-4.8；Fig 2 补画证据选择步骤）

**Files:**
- Create: `paper/figures/fig3_sysml_arch.tex`，编译后复制到 `paper_wiley_submission_to_be_revised/fig3_sysml_arch.pdf`
- Modify: `paper/figures/fig2_pipeline.tex`（在 Stage 2 和 Stage 3 之间加 "2b Evidence selection (LLM, T=0): per-shall relevance attribution; union passed to Stage 3"）
- Modify: `paper_wiley.tex`：删除 `fig:req_diagram`（旧 Fig 3）及 `\input{table_req_case.tex}`；两张 EA 图合并为一个 figure，label 为 `fig:ea`；新增 `fig:sysml_arch`

- [ ] **Step 1：Fig 2**：修改 TikZ，增加 2b 方框，编号保持 Stage 1–5，2b 作为子步骤。编译：

```bash
printf '@echo off\r\ncd /d D:\\cooling_rag_multigranular\\paper\\figures\r\n"D:\\Program Files\\texlive\\2025\\bin\\windows\\pdflatex.exe" -interaction=nonstopmode %%1 > nul\r\n' > /mnt/d/cooling_rag_multigranular/paper/figures/build_fig.bat
cmd.exe /c "D:\cooling_rag_multigranular\paper\figures\build_fig.bat fig2_pipeline.tex"
cp /mnt/d/cooling_rag_multigranular/paper/figures/fig2_pipeline.pdf /mnt/d/cooling_rag_multigranular/paper_wiley_submission_to_be_revised/
```
Expected: 生成 PDF，打开检查 2b 方框可读。

- [ ] **Step 2：新 Fig 3（SysML 架构图）**。TikZ 画两部分：
  - **(a) BDD**：«block» MainEngineCoolingWaterSystem 组合 HT_Circuit、LT_Circuit、SeaWaterCircuit、ControlAndMonitoring；HT_Circuit 组合 HT_Pump[2]（运行与备用）、TemperatureControlValve、ExpansionTank、JacketWaterCooler；LT_Circuit 组合 LT_Pump[2]、CentralCooler。
  - **(b) 需求关联**：取 Task 12 选定的 3–4 条 ER，画 «satisfy» 虚线箭头指向对应 block（例如 TCV、ExpansionTank、HT_Pump）；画 «trace» 虚线指向带 KB id 的证据单元框；画 «deriveReqt» 从 OR 指向 ER。
  - block 名必须与 taxonomy 的 21 个部件对应，可以从 `evidence_taxonomy.COMPONENTS` 取英文键名。图注说明 BDD 只覆盖 taxonomy 的部件层，是示意性的架构上下文，不是完整的船级社送审模型。
  - 编译：`cmd.exe /c "D:\cooling_rag_multigranular\paper\figures\build_fig.bat fig3_sysml_arch.tex"`，然后复制到稿件目录。

- [ ] **Step 3：EA 图重做（用户在 EA 中操作，约 30 分钟）**
  1. 用 Task 11 Step 7 生成的 XML，在 EA 中执行 Import Package from XMI。
  2. 打开需求图，**只展开 1 个 OR 组的 notes**，其余保持折叠，一张图同时呈现层级和明细。
  3. 导出 SVG，保存为 `exp_v4/REQ_revised.svg`。
  4. 转 PDF 并裁边：

```bash
cd /mnt/d/cooling_rag_multigranular/cooling_rag_multigranular
PY -c "from svglib.svglib import svg2rlg;from reportlab.graphics import renderPDF;renderPDF.drawToFile(svg2rlg('data/search_results/exp_v4/REQ_revised.svg'),'data/search_results/exp_v4/REQ_revised.pdf')"
cmd.exe /c "\"D:\Program Files\texlive\2025\bin\windows\pdfcrop.exe\" --margins 4 D:\cooling_rag_multigranular\cooling_rag_multigranular\data\search_results\exp_v4\REQ_revised.pdf D:\cooling_rag_multigranular\paper_wiley_submission_to_be_revised\fig4_ea_revised.pdf"
```
  如果 `svglib` 不在 cooling_rag_env 中，执行 `PY -m pip install svglib==1.5.1`。

- [ ] **Step 4：在 `paper_wiley.tex` 中替换图块**
  - 删除原 `\begin{figure*}...fig4_req_diagram...\end{figure*}` 整块，以及 `\input{table_req_case.tex}`。
  - 删除两个 EA figure 块，换成一个 figure（`fig4_ea_revised`，label 为 `fig:ea`）。
  - 在 "Native import into a commercial MBSE tool" 段落之前插入 `fig:sysml_arch`。
  - 全文 `grep -n "fig:req_diagram\|fig:ea_struct\|fig:ea_detail\|tab:req_case"`，把所有引用改为新的 label。

- [ ] **Step 5：编译检查**（编译脚本见 Task 17 Step 3），Expected: 0 error，并且没有 `undefined references`。

---

### Task 14：正文逐条修改

所有改动都在 `paper_wiley_submission_to_be_revised/paper_wiley.tex` 中进行。定位一律**用锚点字符串**（`grep -n "<锚点>"`），不用行号，因为行号会随修改漂移。数字一律从 `paper_numbers.json` 取，下文用 `⟨N.key⟩` 表示，例如 `⟨rag.grade_X_pct⟩`。

#### 14.1 摘要（R1-1.0、1.1、1.2）
- [ ] 锚点：`\abstract[ABSTRACT]{%`。整段重写，控制在 200 词以内（Wiley 要求）。结构：
  1. 问题（1 句）。
  2. 方法（2 句）。第一次出现时给出定义：*"a knowledge base of ⟨kb.n_units⟩ evidence units — atomic, source-attributed statements (a single regulatory provision, design parameter or procedure) segmented from ⟨kb.n_sources⟩ authoritative documents"*。模型写成 *"an LLM-based workflow (instantiated with DeepSeek-V3)"*。
  3. 结果（3 句）：`⟨rag.citation_rate_pct⟩` 对比 0%；Grade X `⟨rag.grade_X_pct⟩` 对比 `⟨norag.grade_X_pct⟩`；随机检索消融的结论。
  4. 意义（1 句）。
- [ ] 删除旧摘要中 "indicative single-expert spot-check found 44.8%" 这句，盲评结果改放到 Results。
- [ ] 同步修改 "Significance and Practitioner Points" 中的全部数字（锚点：`\section*{Significance and Practitioner Points}`）。

#### 14.2 Intro（R1-2.1、2.2，R2 冗余句）
- [ ] 锚点 `Retrieval-augmented generation~\cite{lewis2020rag} makes grounding explicit`：在该段之前插入 evidence unit 的定义，并加样例框。样例框用 `\begin{table}`（小表）展示一条真实保留下来的 CCS2025 单元：ID、原文（中文加英译）、来源与条款、(c,i)、tier。
- [ ] 在同一位置之后新增一段 **"Why retrieval rather than fine-tuning"**，写四个论点：
  1. 微调把知识写进参数，**无法给出逐条出处**，而逐条出处正是本文的目标属性。
  2. 船级社规范每年修订，RAG 改 KB 即可生效，微调需要重新训练和验证。
  3. 领域内带标注的"需求–规范"配对数据很少。
  4. 对照研究表明，在知识注入任务上 RAG 往往优于微调（引 Ovadia 2024、Soudani 2024）。

  段末承认：在封闭领域中微调 SLM 可能有优势，"SLM + RAG"的组合列为未来工作。
- [ ] 锚点 `The significance of this capability is systems-engineering rather than purely algorithmic.`：删除这句，把该段其余内容并入上一段末尾。
- [ ] 锚点 `In summary, this paper makes three methodological contributions`：改成四项贡献，第四项为"带出处审计、复核路由和派生类型的 MBSE 导出"。

#### 14.3 Methods（R1-4.1、4.3、4.4、4.7；自查的不一致之处）
- [ ] **KB 小节**（锚点 `\subsection{Evidence Knowledge Base}`）：
  - 删除 "1,199 → 1,349 → 1,364" 这段历史。
  - 改写为：语料由 ⟨kb.n_sources⟩ 份文档切分而来；随后做了出处审计，删除 LLM 起草的单元和综合单元，删除无法核实原文的单元，把厂家资料从 L1 降为 L2。给出 ⟨kb.audit.by_decision⟩ 和 ⟨kb.tiers⟩。
  - **如实披露**：早期为覆盖缺口，曾用 DeepSeek 起草过 108 条单元，缺口是通过分析测试需求确定的。这些单元已全部删除，修订稿中的所有结果均在删除之后重新计算。
- [ ] **标注流程**（锚点 `The tagging was performed by the authors`），替换为（D10）：
  - 21×45 taxonomy 由作者根据功能分解定义。
  - (c,i) 标签由 DeepSeek 在约束提示下给出候选；已有唯一合法标签的单元直接继承。
  - 作者对边界情况（taxonomy gap）逐条确认，其余做抽查，没有留存系统的复核记录。
  - 为此请一名独立的领域专家对 120 条分层随机样本盲标，结果为 κ_component=⟨expert.E2_component.kappa⟩、κ_intent=⟨…⟩、κ_pair=⟨…⟩，见 Section Threats。
- [ ] **管线描述**（锚点 `\subsection{Retrieval Pipeline}` 和 `\subsection{Engineering Requirement Generation}`）补写以下与代码一致的细节：
  - Stage 2 之后有 **Stage 2b evidence selection**：同一 LLM、T=0，对每条候选 shall 归因证据，取并集传给 Stage 3；平均从 ⟨…⟩ 条检索结果中选出 ⟨…⟩ 条。这两个数从 `_retrieved_ids` 和 `_n_evidence` 计算，写进 paper_numbers 的 `rag_evidence_counts`，在 Task 6 Step 7 中补算。
  - Stage 3 只读每条单元的前 1,200 字符；Stage 4 的 prompt 中每条单元只给前 500 字符、最多 12 条单元，并优先保留含数值的单元。截断的影响见 E3。
  - 分级器**以 KB 为准**：被引 ID 必须存在于 KB 中；tier 取自 KB 记录；Grade A 要求 KB 记录本身带条款定位信息（列出 regex 所匹配的格式类型）。
  - 所有调用 T=0。
- [ ] **源需求**（锚点 `They were generated by prompting GPT-5.5 (OpenAI)`），按 D8 二选一：
  - **(a) 网页版**：*"…via the ChatGPT web interface in a fresh session with memory and custom instructions disabled; no knowledge-base content had been entered in the account beforehand. Lexical and semantic overlap with the KB was measured (Section …): maximum cosine ⟨e5.or_max_cos_max⟩ versus a KB nearest-neighbour median of ⟨e5.kb_nn_cos_median⟩; longest common substring ⟨e5.or_lcs_chars_max⟩ characters; ⟨e5.n_or_with_numbers⟩ of 60 inputs contain any numeral."*
  - **(b) API 版**：把 "web interface…" 换成 "via the OpenAI API (stateless; no memory)"，其余相同。
  - 如果用户表示**当时没有关闭 memory**，就写 "memory was enabled; we therefore rely on the overlap measurements above"，并在 Threats 中列为威胁。
- [ ] **合成数据的适用性**（R1-4.4），在同一小节后补一段：
  - 测试输入特意写得模糊，覆盖 13 种角色。
  - pipeline 对歧义的处理方式：Stage 1 可以映射到多个对（给出分布：⟨…⟩）；没有可用对时回退到全库检索（回退 ⟨…⟩ 次）；缺少证据时降级为 deferral。
  - E6 若做了（D6），写 Section 结果；若没做，写进 Threats。
- [ ] **Implementation**（锚点 `running on CPU`），改为：*"BGE-M3 index construction ran on an NVIDIA RTX 5060 Laptop GPU; query-time encoding ran on CPU (Intel i9-14900HX, 32 threads) because each requirement requires a single short-query encoding (⟨encode_latency cpu⟩ ms vs ⟨cuda⟩ ms on GPU). End-to-end mean latency per requirement: Stage 1 ⟨timing.stage1_s⟩ s, retrieval ⟨…⟩ s, evidence selection ⟨…⟩ s, value extraction ⟨…⟩ s, generation ⟨…⟩ s; LLM API calls dominate."*

#### 14.4 Related Work（R1-3.1，R2 引文）
- [ ] 在 `paper_bibliography.bib` 末尾追加下面这些**已核实**的条目：

```bibtex
@inproceedings{hey2025refsq,
  author = {Hey, Tobias and Fuch{\ss}, Dominik and Keim, Jan and Koziolek, Anne},
  title = {Requirements Traceability Link Recovery via Retrieval-Augmented Generation},
  booktitle = {Requirements Engineering: Foundation for Software Quality (REFSQ 2025)},
  series = {Lecture Notes in Computer Science}, volume = {15588}, pages = {381--397},
  publisher = {Springer}, year = {2025}, doi = {10.1007/978-3-031-88531-0_27}}
@inproceedings{fuchss2025lissa,
  author = {Fuch{\ss}, Dominik and Hey, Tobias and Keim, Jan and Liu, Haoyu and Ewald, Niklas and Thirolf, Tobias and Koziolek, Anne},
  title = {{LiSSA}: Toward Generic Traceability Link Recovery through Retrieval-Augmented Generation},
  booktitle = {2025 IEEE/ACM 47th International Conference on Software Engineering (ICSE)},
  pages = {1396--1408}, year = {2025}, doi = {10.1109/ICSE55347.2025.00186}}
@article{bonner2024incose,
  author = {Bonner, Maria and Zeller, Marc and Schulz, Gabor and Savu, Ana},
  title = {{LLM}-based Approach to Automatically Establish Traceability between Requirements and {MBSE}},
  journal = {INCOSE International Symposium}, volume = {34}, number = {1}, pages = {2542--2560},
  year = {2024}, doi = {10.1002/iis2.13285}}
@misc{legesse2025ai4se,
  author = {Legesse, Henock and Bicknell, Stanley},
  title = {{AI}-Enhanced Requirements Traceability Using {MBSE} and Large Language Models for Complex Systems},
  howpublished = {Presentation, SERC AI4SE \& SE4AI Research Workshop, Washington, DC, 18 September 2025. NASA NTRS 20250008721},
  year = {2025}}
@inproceedings{ovadia2024finetuning,
  author = {Ovadia, Oded and Brief, Menachem and Mishaeli, Moshik and Elisha, Oren},
  title = {Fine-Tuning or Retrieval? Comparing Knowledge Injection in {LLMs}},
  booktitle = {Proceedings of the 2024 Conference on Empirical Methods in Natural Language Processing},
  pages = {237--250}, year = {2024}, doi = {10.18653/v1/2024.emnlp-main.15}}
@inproceedings{soudani2024finetuning,
  author = {Soudani, Heydar and Kanoulas, Evangelos and Hasibi, Faegheh},
  title = {Fine Tuning vs. Retrieval Augmented Generation for Less Popular Knowledge},
  booktitle = {Proceedings of the 2024 Annual International ACM SIGIR Conference on Research and Development in Information Retrieval in the Asia Pacific Region (SIGIR-AP '24)},
  pages = {12--22}, year = {2024}, doi = {10.1145/3673791.3698415}}
@article{edge2024graphrag,
  author = {Edge, Darren and Trinh, Ha and Cheng, Newman and Bradley, Joshua and Chao, Alex and Mody, Apurva and Truitt, Steven and Metropolitansky, Dasha and Ness, Robert Osazuwa and Larson, Jonathan},
  title = {From Local to Global: A Graph {RAG} Approach to Query-Focused Summarization},
  journal = {arXiv preprint arXiv:2404.16130}, year = {2024}, doi = {10.48550/arXiv.2404.16130}}
@article{peng2024graphragsurvey,
  author = {Peng, Boci and Zhu, Yun and Liu, Yongchao and Bo, Xiaohe and Shi, Haizhou and Hong, Chuntao and Zhang, Yan and Tang, Siliang},
  title = {Graph Retrieval-Augmented Generation: A Survey},
  journal = {arXiv preprint arXiv:2408.08921}, year = {2024}, doi = {10.48550/arXiv.2408.08921}}
```
- [ ] **RE 小节**（锚点 `\subsubsection{Requirements Engineering for Complex Systems}`）：加 2–3 句，讲需求层级（stakeholder → system → component）、29148 的 9 项单条需求特性（含 traceable、verifiable），说明本文的 OR → ER 对应 stakeholder 需求到系统需求的转换。
- [ ] **追溯小节**（锚点 `\subsubsection{Requirements Traceability and Model-Based Tooling}`）：
  - 补充正向和反向追溯的概念，以及 SysML 的 «deriveReqt»、«refine»、«satisfy»、«verify»、«trace» 几种关系。
  - 加入 LLM 和 RAG 用于追溯恢复的研究：`hey2025refsq`、`fuchss2025lissa`（软件领域），`bonner2024incose`（MBSE 领域），`legesse2025ai4se`（AI4SE）。
  - 对比要点：这些工作都是对**已有**制品做事后**恢复**链接，本文是在**生成**需求时同步建立链接。
- [ ] **新增小节 `\subsubsection{Graph- and Ontology-Based Retrieval}`**，放在 RAG 小节之后：
  - 介绍 GraphRAG（`edge2024graphrag`）：先由 LLM 抽取实体图，再做社区摘要。
  - 引用综述 `peng2024graphragsurvey`。
  - 说明本文的 21×45 taxonomy 是一种轻量本体，用作元数据过滤。
  - 解释为什么没有用完整的知识图谱：①条款需要逐字引用，图抽取会改写原文，破坏可溯源性；②构建和维护成本高；③taxonomy 过滤已经能提供结构对齐。
- [ ] **RAG 小节**：加 1 句 hybrid retrieval 的直观解释，方便非 AI 背景的读者理解。

#### 14.5 Results
- [ ] 重写表 descriptive、grade、ablation、posthoc、conflicts、crossllm、stage25 的所有数字（按 `paper_numbers.json`）。用 `100_paper_numbers.py` 的输出逐格核对。
- [ ] **冲突表 (a)**：删除 ISO 8861 这一行。CCS 试压那一行改为 "CCS Rules 2024 Pt3 Ch2 §2.7.1.2 (Class I/II piping: Ps = 1.5p)"，并加表注说明 Class III 冷却水管的适用条件。如果重跑后这一冲突已不存在，就整行删除，(a) 部分改写为"在审计后的 KB 中，可核实到具体条款的外部冲突共 ⟨…⟩ 条"。
- [ ] **新增小节 `\subsection{Stage-1 Mapping Accuracy}`**（R1-4.6）：一张表，4 个系统 × (P、R、F1 及 95% CI) × 三个层级，加上 gold 的构建方式（候选池加补漏，独立专家标注）。如果 gold 只有一名标注者，要写明。
- [ ] **新增小节 `\subsection{Blind Correctness Assessment}`**（D9）：报告 S3 的计数和三项 Fisher p 值。措辞模板：*"Values were judged comparably correct in both arms (…; Fisher p = …), which is consistent with the paper's claim being traceability rather than correctness: the difference is that only the RAG values can be checked against a cited source."* 同时把原 spot-check 小节降为 "non-blinded, indicative"，并写明两者的差异。
- [ ] **新增小节 `\subsection{Retrieval Sensitivity}`**（R2）：一张小表，列出 default 与 4 个端到端变体的 Grade X、A+B、L1 引用率；正文给出切分边界分析的结论（EU 原子切分 0%，对比固定窗口的 ⟨…⟩%）、截断变体的结论、检索层的 Jaccard 范围。完整 10 个变体的表放附录 B。
- [ ] **Native import 段落**：改为引用 `fig:ea`，并在 notes 中提到 Derivation 和 Review 两个字段。

#### 14.6 派生类型与冲突（R2）
- [ ] 在 Methods 的 `\subsection{Engineering Requirement Generation}` 末尾新增 `\paragraph{Derivation type and SysML relations}`：写 Task 11 中的五类规则；OR→ER 用 «deriveReqt»（29148 中的 derived requirement），ER→EU 用 «trace»，ER→block 用 «satisfy»（见 `fig:sysml_arch`）。
- [ ] 新增 `\paragraph{Conflicting authoritative sources}`：
  - 优先级规则：项目适用的船级社规范（含船旗国认可的规范）> IACS UR、SOLAS > ISO 等国际标准 > 厂家资料 > 运行实践。
  - 版本规则：同一来源以 KB 中记录的最新版本为准，KB 记录版本号。
  - 无法裁决时：标记 conflict，路由为 ADJUDICATE，不自动选值。
  - 当前生成阶段**不做**自动仲裁，只做检测。
- [ ] Results 中补一段：派生类型分布 ⟨routing.rag.derivation⟩；规则人工核验一致率 ⟨routing.rule_validation⟩；冲突检出 ⟨routing.n_conflicts⟩ 条，并逐条说明。

#### 14.7 tier-b 证据与复核路由（R1-6.3）
- [ ] 在 Discussion 新增 `\subsection{Review Routing for Downstream Engineers}`：一张小表列出 5 种路由的规则和数量（⟨routing.rag.routes⟩）；说明**只引用厂家资料或内部实践（tier-b）的需求会被自动标记为 ENGINEER_CONFIRM**；这些标签会随 XMI 一起导入 EA，可以在工具中直接筛选。

#### 14.8 领域选择与迁移（R1-6.1、6.2，D7）
- [ ] 在 Discussion 新增 `\subsection{Choice of Domain and Transfer to Other Ship Systems}`：
  1. **为什么选冷却水系统**：规则覆盖密集（IACS UR M、CCS、厂家指南）；数值判据多，最适合检验 Grade X；作者有资料和船厂合作的基础。
  2. **可迁移性分析**：作者逐项判断 45 个方面对滑油、燃油、通风（HVAC）、电力、网络系统的适用性（适用、需修改、不适用），给出一张小表，每个系统 × 适用比例。判断结果存为 `data/processed/taxonomy_transfer.csv`，列为 `intent, lube_oil, fuel_oil, hvac, power, network`，取值为 Y、M、N，由作者在 Task 14 中填写。部件方面，说明 21 个部件中哪些可以复用、哪些需要替换。
  3. **预期挑战**：电力和网络系统的规范多是逻辑和时序约束，需要把分级规则从"数值"扩展到"逻辑条件"；跨系统接口需求需要跨 KB 检索；L1 表格抽取问题会更突出；不同系统的船级社规范章节结构不同。
  4. 回复信中说明 D7 的理由：本轮修订已经包含 KB 审计和全量重跑，再做跨系统试点会超出修订周期；已把它列为首要后续工作，并给出具体步骤。
- [ ] 同步修改 Limitations 中的 "Single domain" 段，以及 Conclusions 中的未来工作。

#### 14.9 Threats to Validity（R1-4.2 的硬性要求）
- [ ] 把 `\subsection{Limitations}` 改名为 `\subsection{Threats to Validity and Limitations}`，按四类组织：
  - **Internal**：标注由 LLM 辅助完成（κ 结果）；KB 由作者整理，早期曾有按测试需求补缺口的做法（已删除并重跑）；DeepSeek 同时参与生成与后验核查。
  - **Construct**：Grade 衡量的是有没有引用，不衡量正确性；盲评样本量小。
  - **External**：单一领域；测试需求是合成的（E6 是否做过）；只测了两种生成模型。
  - **Conclusion**：样本量和置信区间；没有做多重比较校正的说明。
- [ ] 原有的各段 limitation 并入对应类别，内容不删，只重组。

#### 14.10 E6（D6，可选）
- [ ] 如果拿到 ≥10 条真实需求：存为 `data/processed/real_requirements_e6.jsonl`，字段与 `original_requirements_v2.jsonl` 相同，ID 写成 RR001 起。把 `54 --rag-only`、`77` 的输入路径临时改为该文件，输出改为 `exp_v4/e6_*.json`，跑完后用 `grade_summary` 汇总，在 Results 中加一段。如果没拿到，在 Threats > External 中写明。

---

### Task 15：附录 A（prompts，R1-4.5）与附录 B（敏感性全表）

**Files:**
- Modify: `paper_wiley.tex`（在 `\bibliography` 之前加 `\appendix`；USG.cls 的写法见下）

- [ ] **Step 1：取出 prompt 原文**

```bash
cd /mnt/d/cooling_rag_multigranular/cooling_rag_multigranular
PY -c "
from cooling_rag_mg import requirement_analyzer as a, kb_value_extractor as k, structured_req_generator as s, req_generation_v2 as r
open('../tmp/prompts_zh.txt','w',encoding='utf-8').write('\n\n=====\n\n'.join([a._SYSTEM, a._USER, r._RAG_SYSTEM_V3, k._EXTRACT_PROMPT, s._STRUCTURED_GEN_PROMPT, s._NORAG_PROMPT]))"
```
- [ ] **Step 2：逐段英译**（taxonomy 块只给前 3 行示例，并注明"full list in repository"），用 `lstlisting` 排版（`listings` 包已加载）。每段 prompt 前写一行说明：所属阶段、模型、温度、max_tokens。**Stage 4 的 "数值规则（最高优先级）" 段要原样翻译，不得意译或省略。**
- [ ] **Step 3：USG 附录写法**

```latex
\appendix
\section{Prompts (English translation of the original Chinese prompts)}\label{app:prompts}
...
\section{Full Retrieval-Sensitivity Results}\label{app:sensitivity}
...
```
- [ ] **Step 4：编译检查**，Expected: 0 error

---

## 阶段 D：交付

### Task 16：回复信（`response_to_reviewers.tex`）

**Files:**
- Create: `paper_wiley_submission_to_be_revised/response_to_reviewers.tex`

- [ ] **Step 1：结构**（article 类，11pt）：
  1. 致编辑信（1 页）：总结主要修改。**第一段主动说明 KB 出处审计**：发现了什么（两处标准标题误标、108 条 LLM 起草单元、L1 层级不一致）；怎么处理的（删除或降级、以 KB 为准分级、全量重跑）；哪些结论不变（traceability 和 Grade X 的结论）；哪些数字变了（附审计前后对照，来自 `regrade_preaudit` 和新结果）。
  2. 逐条回复：每条依次写 **Comment**（原文）、**Response**、**Changes in manuscript**（Section 名 + 修订稿行号，行号从编译后 PDF 的 lineno 读取）。
- [ ] **Step 2：逐条回复的要点**（按"审稿意见 → 任务映射"表，共 27 条，一条不漏）：
  - R1-5.0、6.0、7.0：致谢，并说明 Results 和 Discussion 因为重跑和新实验有更新。
  - R1-6.1：写"partially addressed"，并说明 D7 的理由和 Task 14.8 的内容。
  - R2-Fig 4/5：说明两张 EA 图已合并成一张，同时删除了与表格重复的 OR-001 自绘图，腾出的版面用于新增的 SysML 架构图（对应 R1-4.8）。
  - R2-chunk：说明证据单元按条款原子切分，用切分边界统计数据说明，并概述 E3 结论。
- [ ] **Step 3：编译**：`pdflatex response_to_reviewers.tex`（用 Windows TeX），Expected: 0 error

---

### Task 17：最终核查、latexdiff 与编译

- [ ] **Step 1：过时数字扫描**。下面这些原稿数字若仍出现在新稿中，必须逐个确认是新结果恰好相同，否则就是遗漏：

```bash
cd /mnt/d/cooling_rag_multigranular/paper_wiley_submission_to_be_revised
for n in "1,364" "1,199" "1,349" "99.3" "38.4" "38.5" "10.1" "28.3" "61.5" "19.1" "21.3" "80.9" "286" "178" "95.1" "96.3" "75.6" "23.3" "8861" "M3.1" "3.9.2.2.8" "0.0028" "on CPU" "N_{\\\\max}=20"; do c=$(grep -c -- "$n" paper_wiley.tex table_*.tex 2>/dev/null | awk -F: '{s+=$2} END{print s}'); echo "$n -> $c"; done
```
Expected: 每个计数为非零的数字，都要在 `rerun_notes.md` 里记下"已核对：新结果确实等于该值"或改正它。`8861`、`M3.1`、`3.9.2.2.8` 三项必须为 0。

- [ ] **Step 2：禁用措辞扫描**

```bash
grep -n -i "eliminat\|guarantee\|structural guarantee\|more correct\|hallucination-free\|performed by the authors" paper_wiley.tex
```
Expected: 没有输出。若有，按 Global Constraints 改写。

- [ ] **Step 3：编译修改稿**

```bash
printf '@echo off\r\ncd /d D:\\cooling_rag_multigranular\\paper_wiley_submission_to_be_revised\r\nset T=D:\\Program Files\\texlive\\2025\\bin\\windows\r\n"%%T%%\\pdflatex.exe" -interaction=nonstopmode %%1.tex > nul\r\n"%%T%%\\bibtex.exe" %%1 > nul\r\n"%%T%%\\pdflatex.exe" -interaction=nonstopmode %%1.tex > nul\r\n"%%T%%\\pdflatex.exe" -interaction=nonstopmode %%1.tex > nul\r\n' > /mnt/d/cooling_rag_multigranular/paper_wiley_submission_to_be_revised/build.bat
cmd.exe /c "D:\cooling_rag_multigranular\paper_wiley_submission_to_be_revised\build.bat paper_wiley"
cd /mnt/d/cooling_rag_multigranular/paper_wiley_submission_to_be_revised
grep -a -c "^! " paper_wiley.log; grep -a "Output written" paper_wiley.log; grep -a -i "undefined" paper_wiley.log | head
```
Expected: `0`，并打印 `Output written … pages`，没有 undefined 引用。

- [ ] **Step 4：生成 latexdiff 标记版**

```bash
cd /mnt/d/cooling_rag_multigranular/paper_wiley_submission_to_be_revised
latexdiff --flatten paper_wiley_original_submission.tex paper_wiley.tex > paper_wiley_diff.tex
cmd.exe /c "D:\cooling_rag_multigranular\paper_wiley_submission_to_be_revised\build.bat paper_wiley_diff"
grep -a -c "^! " paper_wiley_diff.log
```
Expected: `0`。如果 `--flatten` 报 `\input` 找不到，先把 `table_*.tex` 的旧版本（`*_orig.tex`）内联到原稿副本里再 diff。

- [ ] **Step 5：全部测试通过**：`PY -m pytest -q tests -p no:cacheprovider`，Expected: 只剩 Task 0 记下的那 1 个既有 error。
- [ ] **Step 6：提交包清单**：`paper_wiley.pdf`、`paper_wiley_diff.pdf`、`response_to_reviewers.pdf`、全部源文件（tex、bib、cls、图）打成 zip。Data Availability 中的 Zenodo 链接需要**发布新版本**，上传审计后的 KB、审计表和新的缓存；把新 DOI 写进稿件。这一步由用户在 Zenodo 操作。
- [ ] **Step 7：更新记忆文件** `project_minor_revision.md`，写入结果摘要和提交日期。

---

## 时间表（工作日，假设 10-15 开工；括号内为负责人）

| 日期 | 任务 |
|---|---|
| 10-15（周四） | Task 0（Claude；用户发延期邮件）、Task 1（Claude）、Task 2 中自动核对的部分（Claude） |
| 10-16（周五） | Task 2 人工核对（Claude 起草，用户确认）、Task 3、Task 4 |
| 10-17（周六） | Task 5；启动 Task 6 后台重跑（约 4 小时）；用户答复 D8 |
| 10-18（周日） | Task 6 收尾、Task 7、Task 8 生成工作簿，**发给专家** |
| 10-19 – 10-21 | Task 9、Task 10（e2e 变体夜间跑）、Task 11、Task 12 |
| 10-22 – 10-23 | Task 13（用户做 EA 导出约 30 分钟）、Task 15 |
| 10-24 – 10-29 | Task 14 写作（14.1–14.9）；D6 到期，视情况做 E6 |
| 10-25 | 专家工作簿返回 → Task 8 Step 7 评分 → 补写 14.5 和 14.9 中的 κ、F1、盲评 |
| 10-30 – 11-02 | Task 16 回复信 |
| 11-03 – 11-04 | Task 17 核查与编译；合作者通读 |
| 11-05 – 11-06 | 修改合作者意见；Zenodo 新版本；**提交**（11-07 截止前） |

**关键路径**：Task 2（人工核对）→ Task 6（重跑）→ Task 8（专家标注，外部依赖 7 天）。专家只要拖延超过 10-27，就启动 D4 的替代方案，同时依靠已申请的延期。
