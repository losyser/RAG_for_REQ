# UI evidence and retrieval checks — 2026-10-18

## Checkpoint and scope

- Baseline: `d0afe01ecc1beb7cca3b65735bb21c37d4fd87da`.
- Checkpoint tag: `checkpoint/ui-evidence-contracts-20261018`.
- Branch: `fix/ui-evidence-contracts-20261018`.
- Code/test commit: `301bb465b042fa9843eca06d27ac112fd27edcc3`.
- Only four source/test files changed: `cooling_rag_mg/engineering_requirement_agent.py`, `cooling_rag_mg/coverage_retrieval.py`, new `cooling_rag_mg/ui_evidence_contracts.py`, new `tests/test_ui_evidence_contracts.py`.
- The pre-existing modified UI page and other unrelated changes were preserved. This is a backend UI-pipeline repair, not a redesign of the page. No API/model generation, paid inference, primary experiment, KB edit, workbook edit, manuscript edit, expert task or publication occurred.

## Confirmed defects fixed

1. **UI evidence text was lost before budgeting.** `compact_requirement_context` called `compact_evidence(..., text_limit=0)`. `truncate(nonempty_text, 0)` returns `...`, so the later dynamic budget never saw the original text. A zero intermediate budget now means defer budgeting; whole paragraphs are selected from actual text at the existing dynamic 300–600 character budget.
2. **Reference checks used incomplete background IDs.** The previous guard retained only the first six displayed background records' IDs. It now retains the full exclusion list, independently of the six-record display cap. First-selected support order and the default 20 support-evidence cap are unchanged; omitted IDs are recorded.
3. **Removed references could leave a direct-evidence claim.** Background/unknown-context citations are now removed with a preserved reported-ID list and explicit risk entry. If all citations disappear, the status becomes `evidence_gap`; partial loss yields `need_confirmation`. Neither state is a semantic determination.
4. **Explicit fallback result cap was ignored.** `aligned_retrieve` now applies an explicitly supplied `max_total` to the no-mapping fallback, too. The default limits, ranking and fallback trigger do not change. Non-positive limits are rejected explicitly.

## UI schema and reviewable risks

The UI hierarchy remains intact: `requirement_set_id`, `id`, `parent_id`, `level`, `acceptance_criteria`, `evidence_ids`, `support_status`, relationships and scope fields. It is not converted into v4's flat `measurable_criterion/evidence_citations` schema.

Legacy scalar strings in criteria/reference/constraint-list fields are wrapped as one string, without guessing delimiters. Invalid items and source-ID mismatches are recorded; duplicate requirement IDs are rejected rather than guessing relationship targets. References are checked only against the supplied support context. Without that context, reference scope stays unknown. Normalizer changes, dangling parents and removed dangling relationships are reported with their original values. Legitimate relationships originating at the original source requirement remain allowed.

`_validation_report` and per-row `_semantic_support/_applicability` remain `unknown`, even when reference IDs exist. Fallback output also carries an explicit unknown report. The code does not equate regex matches, same IDs, retrieval judge labels or legacy `verified_by_direct_evidence` with independent semantic verification. The existing shared display semantics continue to label these as reported/unverified. The new detailed report is available in the result JSON; this batch does not add a dedicated visualization to the already-modified UI page.

Already-extracted parameter records preserve `value_text/operator/unit` and optional context together under the prior bounded-record helper. No new extraction is invoked and missing historical fields are not manufactured. Metadata over budget is omitted whole and marked. Constraint records over budget are also explicitly marked; missing conditions/model and incomplete cited context become risks. This bounds serialized additions but does not establish semantic completeness across paragraphs.

## Saved-input replay: what changed and what did not

`replay_saved_ui.py` loads the exact baseline implementation from Git and runs only pure compaction/normalization, with networking blocked. It traverses every saved `batch_*/all_requirements_results.json` and every saved UI `engineering_requirements_*/engineering_requirements.json`, rather than selecting high-scoring cases. See `SAVED_REPLAY.json` for per-file/per-source results and examples.

| Check | Before | After |
|---|---:|---:|
| Saved retrieval contexts replayed | 28 | 28 |
| Selected support-evidence occurrences | 234 | 234; same IDs/order in every context |
| Evidence bodies reduced to only `...` | 234 | 0 |
| Evidence occurrences with retained real text | 0 | 123 |
| Oversized whole paragraphs omitted explicitly | Not distinguished from text-loss bug | 111 |
| Saved UI output sets normalized | 120 | 120 |
| Retained engineering requirements | 367 | 367 |
| Normalization exceptions | 0 | 0 |

**The 111 empty over-budget bodies are a remaining limitation, not a successful full-context recovery.** Metadata and available parameter records remain separate, but they cannot replace omitted source context. The current conservative policy may result in more unknown/TBD behavior. A future bounded clause/window strategy would require its own validation; it was not silently substituted here.

Only 22 of the 120 output sets have matching source records in their saved same-batch retrieval files. Those 22 had no references outside the available support context. The other 98 retain unknown reference scope. This is not a measured citation precision/recall or proof of semantic support.

Three independent processes with hash seeds 1, 17 and 123 produced the same serialized compaction hash for the 28 real contexts: `d52dac0b80d15df5c4d18d2de66c0db8d94ad65ae9fa33755e5ac21479a0a3f1` (`UI_HASHES.json`). Generated timestamps are not part of this compaction check.

## Rejection and acceptance boundaries

- Legal legacy UI shape: tested with hierarchy, string fields and source relationships; no requirement dropped in the 367-row saved replay. This is structural preservation, not proof that every retained row is valid engineering content.
- Forged/out-of-context IDs, wrong source IDs, duplicate requirement IDs, malformed list members and dangling relationships: synthetic regression cases exercise rejection or explicitly logged normalization.
- A real ID attached to semantically unrelated evidence is deliberately **not classified as supported**: it can pass the existence check, but semantic support remains unknown. A regression test fixes that boundary. There is no semantic false-accept/false-reject rate because no new gold labels or model evaluation were created.
- A valid JSON response with the wrong UI container schema triggers the conservative fallback and an unknown validation report, without invoking an external repair API in the test. The actual LangGraph nodes are executed with mocked completion/config objects; this is more than calling a formatting helper in isolation.

## Retrieval policy diagnosis without changing the experiment

An optional diagnostics dictionary now reports mapping pairs, processed-pair hit counts, whether the existing empty-mapping fallback ran, and nonempty-mapping/zero-result cases. It performs no extra retrieval. Mapping correctness and recall are explicitly unknown. The regression test demonstrates that a nonempty wrong mapping still hard-filters to zero; an available mock unfiltered result is not consulted. This risk remains unresolved by design, not hidden behind a passing test.

`diagnose_numeric_selection` describes the unchanged numeric-first/stable/max12 policy on saved values. Across the 60 frozen RAG source sets, **25 omit at least one non-numeric evidence unit**. This is a selection-loss indicator, not measured relevance or recall loss. No authority score, broader recall, alternative reranker or changed default was introduced.

Possible future opt-in comparisons: an explicitly named unfiltered-rescue variant for nonempty mapping with zero hits; a relevance/authority-coverage selection variant versus numeric-first. They would alter the experimental policy and require separate declared inputs/results. They are recommendations, not enabled configurations or experiments in this batch.

## Read-only KB checks

Among 1,208 KB units, missing top-level-or-metadata counts are: source document 0; location 4; manufacturer 234; engine model 587; applicable condition 43. These are missingness counts, not error labels: a general rule need not have a manufacturer/model. No metadata was filled from guesses.

OR023's -100°C remains unchanged. The earlier official-source discrepancy and unmatched local-edition provenance remain unresolved; no fact correction or safety guarantee is inferred from code tests or Grade B.

## Tests, commands and protection

Final selected regression suite: **203 passed, no skips** (15 new UI/retrieval cases plus 188 existing selected cases, including the prior repair's tests). This is not the entire repository suite. Intermediate runs were 46, 200 and 202 passes as coverage was added; final evidence is `tests_final_complete.txt`. Scoped diff checks pass.

```powershell
$env:PYTHONPATH=''
$env:PYTHONIOENCODING='utf-8'
$env:OMP_NUM_THREADS='8'
$py='D:\Users\yando\miniconda3\envs\cooling_rag_env\python.exe'
$batch='D:\cooling_rag_multigranular\cooling_rag_multigranular\revision_artifacts\ui_optimization_20261018'
& $py -B "$batch\run_offline_tests.py"
& $py -B "$batch\replay_saved_ui.py"
```

The launcher isolates the legacy autouse model cache, blocks socket connections, suppresses bytecode and pytest cache writes, and writes temporary results under this batch directory. Hash subprocesses only read saved inputs and run compaction; no model client is created.

The protected manifest covers the same 366 historical files: 25 processed/KB files, 193 result/archive files, 110 submission files and 38 workbooks including human-review originals/copies. All hashes remain unchanged. All unrelated pre-existing tracked content also matches the batch-start hashes. The full repository remains dirty from pre-existing user work; this batch's committed paths are clean. No hard reset or broad git add was used.

## What would require model calls later — not executed

Generation effectiveness is still unverified. A bounded proposal is six fixed diagnostic cases, chosen before any new score: frozen v4 OR001/OR010/OR023 plus saved UI R001/R002/R003 from `batch_20260730_164747`. Compare baseline/new prompts with the same saved evidence, one generation per variant: **12 completion calls, zero fresh extraction/retrieval/model-repair calls, zero automatic retries**. These are purposive defect cases, not a representative quality sample.

The locally configured alias is `deepseek-chat`; the actual provider/version and current input/cache/output prices have not been independently established for a new run. A numeric currency estimate or spending cap would therefore be fabricated. Before execution, freeze provider/version, count each prompt with the provider's tokenizer, price those tokens using the verified tariff, and obtain a currency cap. An output cap of 8,192 tokens per call would give at most 98,304 output tokens across 12 calls; input-token cost still must be computed from the frozen prompts. Both the currency ceiling and any such model run remain unapproved/unexecuted. No fee authorization was inferred from “验证”.
