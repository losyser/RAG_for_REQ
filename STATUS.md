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
