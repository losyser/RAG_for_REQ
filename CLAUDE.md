# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 工作记录自动更新规则

每次会话涉及以下任何变更时，**必须主动、及时**更新 `/home/yan/.claude/projects/-mnt-d-cooling-rag-multigranular/memory/` 下对应的记忆文件和 MEMORY.md 索引，无需等用户提醒：

- 论文状态变化（投稿/拒稿/修改/题目更新）
- 实验结果或数据更新
- KB 内容变更
- 项目方向或定位调整
- 代码/脚本关键修改

更新原则：**直接修改对应记忆文件**，不要新建冗余条目；如原记忆已过时，覆盖更新并在 MEMORY.md 同步修改摘要行。

## Commands

All commands run from `cooling_rag_multigranular/` (the inner project directory that contains `requirements.txt`).

**Install dependencies:**
```bat
D:\Users\yando\miniconda3\envs\cooling_rag_env\python.exe -m pip install -r requirements.txt
```

**First-time setup:**
```bat
python scripts/11_build_multigranular_indexes.py   # Build FAISS + BM25 indexes
```

> Note: `evidence_units.jsonl` and `source_chunks.jsonl` are maintained manually (scripts 30–36).
> Do NOT regenerate them from `evidence.docx` — that would overwrite hand-curated entries.

**Smoke test (runs a single requirement through the full pipeline):**
```bat
python scripts/13_smoke_test.py
```

**Launch Streamlit UI:**
```bat
streamlit run app.py
```

**Experimental evaluation pipeline — 3-round canonical (paper reproduction):**
```bat
python scripts/25_generate_requirement_pool.py           # One-time: build 100-req pool → data/processed/requirement_pool_100.jsonl
python scripts/26_run_three_rounds.py [--groups G1 G2 G3 G4 A1 A2] [--seeds 42 7 99]
                                                         # Runs 3 rounds; auto-generates M6_review.json per round
python scripts/22_compute_metrics.py                     # Compute M1–M5 from three_round_summary.json; read M6_review.json for M6
python scripts/27_statistics.py                          # Per-requirement Wilcoxon + bootstrap CI
python scripts/28_baselines.py all                       # Long-context LLM, KB scaling, noise-KB baselines
python scripts/29_analysis.py all                        # Failure taxonomy, QG calibration, held-out, heatmaps
python scripts/23_export_latex_table.py                  # Export LaTeX table for paper
python scripts/24_export_case_study.py [--index 0]       # Export one G4 case for paper body
```

**Single-batch legacy pipeline (per-batch, not used for paper):**
```bat
python scripts/20_generate_test_requirements.py          # Legacy: generate 20 test requirements into test_requirements.jsonl
python scripts/21_run_experiment.py [--groups G1 G2 G3 G4 A1 A2] [--top-k 4]
```

## Environment Variables (`.env`)

| Variable | Purpose | Default |
|---|---|---|
| `BGE_M3_MODEL_PATH` | Path to local BGE-M3 embedding model | `D:/models/bge-m3` |
| `DEEPSEEK_API_KEY` / `api_key` | DeepSeek API key; system degrades gracefully without it | — |
| `DEEPSEEK_BASE_URL` / `base_url` | API base URL | `https://api.deepseek.com` |
| `RAW_DOCX_PATH` | Override path to evidence docx | `data/raw/evidence.docx` |
| `DEVICE` | `cpu` or `cuda` | auto-detected |
| `USE_REQUIREMENT_SPLITTER` | Set to `0` to disable LLM splitting | `1` |
| `USE_EVIDENCE_JUDGE` | Set to `0` to disable LLM judging | `1` |
| `DEBUG_DEVICE` | Set to `1` to print device info at startup | `0` |

## UI Architecture

The Streamlit app is split into a `ui/` package. `app.py` at the project root is the single entry point.

```
app.py                         # streamlit run app.py
ui/
  state.py                     # DEFAULT_REQUIREMENTS, all label dicts, init_state(), normalize_df()
  styles.py                    # inject_css() — full design-system CSS
  sidebar.py                   # render_nav_sidebar()
  components/
    shared.py                  # status_pill_html, badge_html, format_duration, etc.
  pages/
    retrieval.py               # render_retrieval_workspace() + payload helpers + card renderers
    results.py                 # render_retrieval_results_workspace()
    engineering.py             # render_engineering_workspace() + SysML diagram helpers
    experiment.py              # render_experiment_workspace() + group-level helpers
    metrics.py                 # render_metrics_workspace() + charts + M6 review
    evidence_manager.py        # Evidence DB status, coverage stats, maintenance scripts
```

Navigation keys (stored in `st.session_state.active_workspace`):
`retrieval_workspace` | `retrieval_results` | `engineering_workspace` | `experiment_comparison` | `metrics_analysis` | `evidence_manager`

The old `apps/requirement_collection_ui.py` and `apps/experiment_ui.py` are kept as legacy entry points but the canonical code lives in `ui/`.

## RAG Pipeline Architecture

The system is a multi-granular RAG pipeline for engineering evidence retrieval, domain-specific to ship main engine cooling water systems.

### Data Layer: Three Granularities

The knowledge base is maintained manually via `scripts/30–36`. **Do not regenerate from `evidence.docx`** — that would overwrite hand-curated entries.

- **`evidence_units.jsonl`** — one entry per evidence item (fine-grained). Each unit has a `parent_chunk_id` linking it to a source chunk.
- **`source_chunks.jsonl`** — groups of evidence units sharing the same source document + component + aspect (coarse-grained). Used for first-pass retrieval.
- **`evidence_groups.jsonl`** — groups by `(component_objects[0], requirement_intents[0], engineering_phase[0])`. Used for sibling-evidence expansion at retrieval time.

All evidence metadata is normalized through `schema.py:normalize_v2_metadata()`, which maps both Chinese and English field names to canonical V2 keys (`component_objects`, `requirement_intents`, `can_support`, `evidence_strength`, `applicability_level`, `is_generalizable`, etc.).

### Index Layer

`index_store.py` builds and loads a `BuiltIndex` that combines:
- **FAISS** `IndexFlatIP` (inner-product, normalized vectors → cosine similarity) using local BGE-M3 embeddings
- **BM25Okapi** (rank-bm25) on tokenized `search_text` fields

Both source_chunks and evidence_units have separate indexes stored under `data/indexes/`.

### Retrieval Pipeline (`pipeline.py` + `retrieval_engine.py`)

For each raw requirement:
1. **Split** (`requirement_splitter.py`): LLM (DeepSeek) splits into ≤4 sub-requirements by engineering type (`redundancy`, `installation`, `parameter`, `alarm_protection`, etc.). Falls back to sentence-boundary rule splitting if LLM unavailable.
2. **Profile building** (`retrieval_profile.py`): Builds a structured `RetrievalProfile` by matching sub-requirement text against `COMPONENT_MAP`, `ASPECT_MAP`, and `CONDITION_MAP` synonym dictionaries, then merging with `TYPE_PROFILE` defaults for the requirement type.
3. **Coarse retrieval**: BM25 + vector search on `source_chunks` → RRF fusion → profile scoring → top-`coarse_k` chunks. Creates `allowed_chunks` set.
4. **Fine retrieval**: BM25 + vector search on `evidence_units` → RRF fusion. Units whose `parent_chunk_id` is in `allowed_chunks` receive a `coarse_bonus` of +0.30.
5. **Profile scoring** (`_score_by_profile`): Adjusts each item's score based on component/aspect/phase/condition/can_support matches, evidence strength, source type, and generalizability. Key weights: component match +0.40–0.60, aspect match +0.35–0.60, `direct` strength +0.50, `ship_rule`/`class_rule` source +0.40.
6. **Group expansion**: For top results, pulls sibling evidence from `evidence_groups` (up to 4 per group). Expanded items start from RRF base score 0.15 (replacing their actual RRF rank), but profile scoring is still applied on top, so high-profile-match expanded items can outrank primary candidates.
7. **Soft filter** (`_soft_filter_by_profile`): Hard-rejects `not_applicable` and `is_noise=True`; filters low-score `paper`/`patent`; assigns `retrieval_role`.
8. **Applicability filter** (`applicability_filter.py`): Rule-based hard-reject (e.g., `background+background_reference`, `paper+is_generalizable=no` for engineering types) and score delta adjustments. Checks `unsupported_requirements` field against requirement text via keyword-group matching.
9. **Evidence judge** (`evidence_judge.py`): LLM (DeepSeek) classifies each candidate as `direct`/`indirect`/`background`/`not_applicable` and assigns `evidence_role`. Falls back to threshold-based rules (score ≥ 0.65) if LLM unavailable.
10. **Evidence gap classification**: If no `direct` evidence is selected, classifies the gap type (`no_candidate`, `applicability_filtered_all`, `only_indirect`, `installation_evidence_gap`, etc.) and generates a suggested document update.

### Output

`evidence_pack.py` saves results to `data/search_results/batch_YYYYMMDD_HHMMSS/`:
- `all_requirements_results.json` — full structured output
- `all_requirements_results.md` — human-readable summary with evidence text excerpts

The Streamlit UI (`apps/requirement_collection_ui.py`) also calls `engineering_requirement_agent.py` to generate formal "shall statements" from selected evidence using a LangGraph-based agent (optional; requires DeepSeek API).

### Engineering Requirement Agent (`engineering_requirement_agent.py`)

LangGraph StateGraph with three nodes: `prepare_context → call_deepseek → parse_and_validate`.

Key functions:
- `generate_engineering_requirements(requirements, retrieval_payload)` — entry point; takes full pipeline output
- `collect_requirement_context(payload, requirement_id)` — extracts one requirement's context from payload
- `compact_requirement_context(context)` — groups evidence by `requirement_intents`, applies dynamic token budget
- `normalize_agent_output(obj, requirement_id)` — validates support_status/verification_method, sanitizes inferred numeric values

Output schema per requirement set: `requirement_set_id`, `source_requirement_id`, `stakeholder`, `engineering_requirements[]`, `relationships[]`, `evidence_gaps[]`, `confirmation_items[]`.

### Quality Gate (`quality_gate.py`)

Post-generation 5-dimension checker. Shared `QualityGate` instance; each call to `check(req)` returns a `QualityReport`.

| Dimension | Strategy | Severity |
|---|---|---|
| `evidence_sufficiency` | Rule: evidence_ids non-empty AND status ≠ evidence_gap | error |
| `verifiability` | Rule: verification_method + criteria present, no vague terms | error/warning |
| `over_inference` | Rule: quantitative values (regex) in shall but status ≠ verified_by_direct_evidence | error |
| `ambiguity` | LLM (DeepSeek) → rule fallback | warning |
| `mbse_completeness` | Rule: all 5 SysML required fields present | error |

`overall_passed = True` only when all error-severity checks pass (warnings don't block).

### SysML Exporter (`sysml_exporter.py`)

`export_requirement_set(requirement_set, output_path)` → SysML-aligned XML with namespace `http://www.omg.org/spec/SysML/20181001/Requirements`. Nests level-2 children inside their level-1 parent `<Requirement>` elements. `export_batch(requirement_sets, output_dir)` saves each as `<setId>.xml`.

### Experimental Framework

**Groups:**
- G1 Direct LLM — no retrieval, same prompt without evidence section
- G2 Flat RAG — evidence_units only, single-granularity, no quality gate
- G3 Multi-RAG — full multi-granular pipeline, no quality gate
- G4 Proposed — multi-granular + quality gate + SysML XML export
- A1 Ablation — G4 without quality gate
- A2 Ablation — G4 without profile scoring (flat RRF only, monkey-patches `_score_by_profile`)

**Metrics (M1–M5 auto-computed by script 22):**
- M1 Evidence-free rate (↓ better): proportion of requirements with empty evidence_ids
- M2 QG pass rate (↑): overall_passed / total (G4/A2 only)
- M3 Over-inference rate (↓): proportion failing the over_inference check
- M4 Verifiability score (↑): proportion passing the verifiability check
- M5 MBSE completeness (↑): proportion with all SysML required fields
- M6 Traceability precision: manual review (dual-dimension: decomposition_correct + traceability_correct);
  script 26 auto-generates `M6_review.json` per round; reviewed via `m6_review.bat` / `scripts/m6_review_ui.py`

**Output directory:** `data/search_results/batch_YYYYMMDD_HHMMSS/experiment/`

### Key Invariants

- `normalize_v2_metadata()` must be called before any field access on evidence metadata — raw JSONL may have Chinese or legacy field names.
- Evidence with `evidence_strength=background` is **never** placed in `selected_results`, regardless of score.
- The `PipelineServices` dataclass in `pipeline.py` is the seam for dependency injection — tests or alternative configurations swap `splitter` and `judge` via this object.
- `LangGraph` import is soft — `engineering_requirement_agent.py` catches the import error and the rest of the system works without it.
