# UI excerpt acceptance follow-up — 2026-10-18

Baseline `e139d8a90785829027268b23d8b535044cea5c3b`; code/test repair `0733a38a96b1cbae9a6beb5c3011a4178fa4c4fc`. Same local repair branch. This follow-up changes only `cooling_rag_mg/ui_evidence_contracts.py`, `cooling_rag_mg/engineering_requirement_agent.py`, and `tests/test_ui_evidence_contracts.py`, plus this isolated delivery. It does not change retrieval rankings, KB values, saved experiments, human workbooks or manuscripts.

## The 111 omissions were real zero-body cases

The previous whole-paragraph strategy genuinely returned an empty body for 111 nonempty source-evidence occurrences. Their original lengths were 463–1,351 characters, median 723. Actual per-evidence budgets in the saved contexts ranged from 460 to 580 characters (the general UI formula remains bounded to 300–600). An oversized paragraph could therefore be dropped completely, even when only slightly longer than its budget. Passing the earlier tests did not establish that this policy retained useful text.

There were **zero contexts with selected support evidence but all evidence bodies empty**, before and after this follow-up. Six of the 28 contexts had no selected support evidence in the saved input to begin with; they remain empty. These are different conditions and are counted separately in `EXCERPT_REPLAY.json`.

## Local fix, without expanding evidence-body budgets

The existing paragraph selection is retained whenever it yields any text. Only when it would return no text from a nonempty source do we take a bounded fragment of the first source paragraph. The end prefers a sentence/line boundary within the latter half of the allowed window; otherwise it is a hard character cut. The hard-cut case is explicitly identified. This is a retention rule, not a relevance ranking or a claim that adjacent conditions have been preserved.

Every retained body now records:

- source ID plus the existing source document/location metadata;
- exact Unicode-character spans in the original source text, with end-exclusive offsets;
- SHA256 of the original text;
- original/retained character counts and the applied budget;
- `partial_unknown`, truncation and fragment-fallback/boundary flags where applicable.

The replay reconstructs every displayed body from its source spans and checks its hash and length. Offsets and budgets are explicitly prohibited from being used as engineering parameter values. No full original body is smuggled into a new prompt field.

Parameter records retain their existing 1,600-character whole-record budget; the prior per-field metadata/constraint omission limits remain. A new **96,000-character total system+user prompt cap** is enforced before creating a model client. `UI_MAX_PROMPT_CHARS` can explicitly configure this cap. Over-budget inputs produce a labeled conservative fallback instead of silently deleting more evidence. This is a character guard, not a token or currency estimate. It also covers unexpectedly large metadata, original requirement fields, or duplicated grouped evidence in the serialized prompt.

## Saved-input comparison

The exact baseline agent and helper modules are loaded from Git at `e139d8a`, avoiding accidental use of the new helper for the old side. All 28 saved UI retrieval contexts are replayed. Model completions are mocked; no external call occurs.

| Measure | Original text-loss bug (`d0afe01`) | Whole-paragraph repair (`e139d8a`) | This follow-up |
|---|---:|---:|---:|
| Selected evidence occurrences | 234 | 234 | 234 |
| Bodies consisting only of `...` | 234 | 0 | 0 |
| Empty bodies from oversized paragraphs | Not usefully distinguished | 111 | 0 |
| Bodies with actual source text | 0 | 123 | 234 |
| Retained source-body characters | No useful source text | 47,306 | 96,900 |
| Contexts with support evidence but all bodies empty | 0 (placeholder-only is separately bad) | 0 | 0 |
| Contexts with no support evidence supplied | 6 | 6 | 6 |

All 123 previously nonempty bodies remain **byte-for-byte equal as strings**; no earlier retained paragraph was replaced by the new prefix fallback. All selected IDs and order remain identical. The 111 rescued occurrences remain explicitly partial, and do not establish complete conditions or semantic support.

The machine-readable replay contains each context's before/after retained character totals and each evidence occurrence's source length, budget, spans, boundary mode and hash. The actual graph's serialized system+user prompts, using saved IDs/text as the requirement fixture, ranged from **9,499 to 90,328 characters**; none of these 28 fixtures hit the 96,000 cap. These are current replay fixtures, not recovered historical prompts.

## Direct-support guard across execution paths

- Normal parse/normalize and successful JSON-repair paths both pass the supplied evidence scope into the same guard. Empty/placeholder source bodies, partial context or omitted metadata/parameters cannot leave the generated row at legacy `verified_by_direct_evidence`; it is downgraded to `need_confirmation`.
- Unknown/background reference removal retains the reported IDs and downgrades to `need_confirmation` or `evidence_gap` when no IDs remain, as established in the preceding repair.
- The existing five-reference cap now also downgrades a direct claim when it removes references; the complete reported list remains available for review. The cap and order itself are unchanged.
- JSON/schema failure, failed repair and prompt-budget failure use the conservative fallback, which never assigns direct-verified status. Budget failure is checked before client creation. The test suite exercises real LangGraph nodes with mocks, including normal, repaired and blocked paths; no repair API is called.
- With no supplied scope, existence/applicability cannot be verified and remain unknown. The legacy enum is never proof of engineering correctness; even fully retained bodies can be wrong or semantically unrelated.

Downgrading whenever any cited material is incomplete is deliberately conservative and may defer a row that could have been supported by another complete citation. That tradeoff is visible and remains a strategy hypothesis, not an accuracy result.

## Tests and preservation

Final selected regression suite: **216 passed, no skips**, including 13 additional cases beyond the prior 203. The updated tests cover 1/10/300/580/600-character boundaries, exact source spans/hash, preserving previously retained paragraphs, empty/ellipsis/partial bodies, normal and repaired graph paths with invalid references, the five-reference cap, and prompt blocking before client creation. All existing selected UI/v4/retrieval/downstream tests remain included. See `tests_acceptance.txt`.

The saved-data replay is separate from synthetic tests. Its assertions require every excerpt to match original source spans, every body to respect its budget, all earlier nonempty bodies to remain unchanged, unchanged IDs/order and unchanged protected hashes. It does not evaluate new model-generated quality or infer semantic false-accept/false-reject rates.

The same **366 protected historical files** remain unchanged. Existing unrelated working-tree changes are retained. This batch's committed paths are clean; the entire repository is intentionally not reset to a clean tree.

Reproduction (existing offline launcher isolates the model cache and blocks networking):

```powershell
$env:PYTHONPATH=''
$env:PYTHONIOENCODING='utf-8'
$env:OMP_NUM_THREADS='8'
$py='D:\Users\yando\miniconda3\envs\cooling_rag_env\python.exe'
$root='D:\cooling_rag_multigranular\cooling_rag_multigranular'
& $py -B "$root\revision_artifacts\ui_optimization_20261018\run_offline_tests.py"
& $py -B "$root\revision_artifacts\ui_excerpt_followup_20261018\replay_excerpts.py"
```

Remaining hypotheses: a prefix may miss a later qualifier or table heading; a sentence boundary is not a semantic boundary; the unchanged paragraph-first rule can retain a later short note instead of an earlier oversized parameter paragraph; numeric-first and nonempty-mapping hard filtering retain their prior limitations. No model experiment, broader-recall algorithm, KB factual correction or paper change was performed.
