# 项目状态速览

**最后更新：2026-05-29**

## 这是什么

船舶主机冷却水系统的**多粒度需求证据检索系统**，面向英文普刊论文（实验对比 G1–G4 + 消融 A1/A2）。

核心流程：原始需求 → LLM拆分子需求 → 粗粒度召回（source_chunks）→ 细粒度召回（evidence_units）→ profile评分 → LLM审查 → 工程需求生成 → 质量门 → SysML XML输出。

## 启动

```bash
# 工作目录：cooling_rag_multigranular/（含 requirements.txt 的那层）
streamlit run app.py
```

## 关键文件

| 路径 | 职责 |
|---|---|
| `app.py` | 唯一入口，路由6个页面 |
| `ui/state.py` | `init_state()` / `normalize_df()` / 默认需求表（R001–R030） |
| `ui/pages/retrieval.py` | 检索工作台（需求表 + 启动检索） |
| `ui/pages/experiment.py` | 实验对比（G1–G4、A1、A2） |
| `ui/pages/metrics.py` | 指标分析（M1–M5自动 + M6人工） |
| `cooling_rag_mg/pipeline.py` | `run_requirements_with_services()` 主流程 |
| `cooling_rag_mg/experiment_runner.py` | `run_g1/g2/run_pipeline_group/compute_metrics` |
| `cooling_rag_mg/requirement_splitter.py` | v2拆分器（LLM + source_phrase溯源 + 审核循环） |
| `cooling_rag_mg/evidence_judge.py` | LLM证据审查，fallback阈值规则 |
| `cooling_rag_mg/quality_gate.py` | 5维质量门（error阻断，warning不阻断） |

## 实验流程（三轮对比）

```bash
# 一键跑三轮（G1–G4 + A1 + A2，每轮从100条需求池随机抽30条）
python scripts/26_run_three_rounds.py

# 计算指标（M1–M5自动，M6读取 M6_review.json）
python scripts/22_compute_metrics.py

# 导出 LaTeX 表格
python scripts/23_export_latex_table.py

# 导出 case study
python scripts/24_export_case_study.py --index 0
```

**结果目录：** `data/search_results/batch_YYYYMMDD_HHMMSS/experiment/`

每轮 G4 结束后自动生成 `M6_review.json`（供人工审核）。

## M6 人工审核

**双维度审核**：

| 字段 | 含义 | 适用范围 |
|---|---|---|
| `decomposition_correct` | 这条 shall 是原始需求的合理拆分？ | 所有 ER |
| `traceability_correct` | 引用证据是否支持该 shall？ | 有证据的 ER |

三个子指标：
- **M6_decomp**：拆分正确率
- **M6_trace**：溯源精度（仅有证据的 ER）
- **M6_gap**：证据缺口率（拆分正确但无证据）

审核标准见 `M6_审核标准.md`。

```bash
m6_review.bat          # 双击启动桌面审核程序
python scripts/m6_review_ui.py   # 或命令行启动
```

## 三轮实验结果（已完成，2026-05-29）

### M1–M5 自动指标（mean ± std，3轮）

| 指标 | G1 | G2 | G3 | **G4** | A1 | A2 |
|---|---|---|---|---|---|---|
| M1 无证据率 ↓ | — | 11.5±1.7% | 22.3±3.7% | **22.3±3.7%** | 22.3±3.7% | 20.9±3.9% |
| M2 质量门通过率 ↑ | — | — | — | **64.7±5.2%** | — | 69.8±6.2% |
| M3 过度推断率 ↓ | 4.1±2.6% | 4.5±2.6% | 4.4±2.6% | **4.4±2.6%** | 4.4±2.6% | 4.4±4.0% |
| M4 可验证性 ↑ | 96.1±2.0% | 93.5±1.8% | 98.6±1.5% | **98.6±1.5%** | 98.6±1.5% | 98.1±0.7% |

### M6 人工审核（G4，3轮已完成）

| 指标 | Mean ± Std |
|---|---|
| M6_decomp 拆分正确率 | **96.1% ± 2.2%** |
| M6_trace 溯源精度 | **65.7% ± 4.2%** |
| M6_gap 证据缺口率 | **23.1% ± 3.3%** |

### 关键结论

- G2 → G3/G4：M4 +5.1pp（verifiability），M1 +10.8pp（evidence-free rate 上升）
- Profile Scoring（G4 vs A2）：M4 差异不显著（T=0 deterministic）
- 质量门为独立质量检验层，M2 通过率 64.7%
- M6_trace 65.7%，M6_gap 23.1% 说明约 1/4 合理拆分在 KB 中无对应文件

## Grounding Score（动作 A，2026-05-29）— 原始命题检验

**动机：** M3/M4 只测生成文本的形式（正则数字、字段存在性），测不到"证据质量"。新增 grounding score 直接量化"被引证据对 shall 的语义支持度"，穿透 prompt 约束，在 G2/G3/G4 横向对比，检验原始命题"多粒度检索提供更对口证据"。

**两个互补测法**（脚本 `scripts/40_grounding_score.py`）：
1. **reranker 客观分**：BGE-reranker-v2-m3 对每个 (shall, evidence) 对打相关分（本地、零 API、可复现）。
2. **LLM 蕴含分**：Qwen（独立于生成所用的 DeepSeek）判 support/partial/none → 1.0/0.5/0.0。

**配对单位 = 唯一 source_requirement_id**。注意：T=0 下 LLM API 仍有随机性，多轮重跑同一需求会产生**伪重复**；按 (batch, src) 计数会把 n 夸大到 186、p 失真。已修复为按唯一 src 跨轮取均值（commit 30d5c7f）。

### 结果（3 个 canonical 轮次，去重 n=42）

| 测法 | G2 均值 | G3 均值 | G2−G3 差 | p | 95% CI |
|---|---|---|---|---|---|
| reranker（客观） | 0.732 | 0.577 | **+0.095** | **0.001** | [+0.042, +0.148] |
| Qwen（独立 LLM） | 0.706 | 0.599 | +0.053 | 0.193 | [−0.024, +0.129] |

- 两测法绝对水平吻合（~0.6–0.7），方向一致：**G2（扁平）≥ G3（多粒度）**，无一测法出现 G3 > G2。
- 全量 9 batch 的 reranker 稳健性旁证一致（去重均值 n=54：diff=+0.054, p=0.021）。
- Qwen verdict 分布健康（support 37.6% / partial 51.3% / none 11.1%，无限流污染）。

### 结论：原始命题**证伪**（spec 分支乙）

**多粒度检索并未提供"更对口"的证据**：客观 reranker 显示多粒度证据的**逐条契合度显著更低**（兄弟/粗粒度扩展引入更发散证据，拉低均值），独立 LLM 判官则看不出显著差异——但两者都**不支持** "G3 > G2"。

**真正的差异是精度-覆盖权衡**：G3/G4 为更多需求产出了证据（去重后有证据的源需求 52/54 条 vs G2 的 45 条，覆盖↑），代价是每条证据契合度↓。论文走分支乙：诚实报告"当前 KB 规模下，检索粒度对单条证据契合度无正向贡献，多粒度的价值在覆盖而非精度"，配合 KB 覆盖瓶颈（M6_gap 23%）叙事。

**产物：** `data/search_results/grounding_score.json` + `grounding_score_table.tex`（LaTeX 表）。

**可选后续：** 文心（ERNIE）作第三独立模型复算（`--llm ernie`，~1027 次调用），进一步加固"G2 ≥ G3"的跨模型稳健性；但不改变证伪结论。

## 数据

- 原始文档：`data/raw/evidence.docx`
- 需求池：`data/processed/requirement_pool_100.jsonl`（P001–P100）
- 三粒度索引：`data/indexes/`（`evidence_units` + `source_chunks` + `evidence_groups`）
- 实验结果：`data/search_results/batch_*/experiment/`

## 环境变量（`.env`）

```
BGE_M3_MODEL_PATH=D:/models/bge-m3
DEEPSEEK_API_KEY=...
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

LLM（拆分器 + 审查 + 质量门）均有 fallback，无 API key 系统仍可运行。

## 已完成的主要工作

| 时间 | 内容 |
|---|---|
| 早期 | app.py 无限循环修复、实验页 rerun 修复、需求勾选跨页丢失修复 |
| 2026-05-24 | 拆分器v2：source_phrase溯源 + allowed_engineering_aspects硬约束 + 审核循环 |
| 2026-05-26 | 三轮实验脚本（script 26）：CUDA OOM修复、自动生成M6_review.json |
| 2026-05-26 | M6审核UI迁移为独立Tkinter桌面程序（m6_review_ui.py + m6_review.bat） |
| 2026-05-26 | M6双维度改造：decomposition_correct + traceability_correct，三子指标输出 |
| 2026-05-26 | 三轮实验完成，M6人工审核完成，全部指标汇总完毕 |
| 2026-05-29 | 论文草稿完成（paper/paper.tex），经9轮审核30项修复，达到投稿质量 |

## 投稿前剩余（仅流程）

1. `pdflatex` 重新编译 → 更新 `out/paper.pdf`
2. 替换 `<anonymized-during-review>` → GitHub 仓库 URL
3. 替换 `<Zenodo-DOI-pending>` → Zenodo DOI

## 审稿意见

详见 `paper/review_feedback.md`（模拟4位审稿人意见，Major Revision 6条必须修改项）。
