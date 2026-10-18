# Bounded evidence pipeline optimization — 2026-10-18

This is a local code repair and offline verification, not a new experiment. No historical outputs, KB values, expert workbooks, manuscript or response files were updated. S2 remains closed. No external model/API calls, paid inference, expert contact or publication occurred.

## Git and rollback

- Original project HEAD: `0657f93` (pre-existing working tree was dirty).
- Branch: `fix/evidence-contracts-20261018`.
- Pre-repair checkpoint: `3659d37ed21a2f286027f2603b171f2ad22565fe`.
- Code/test repair commit: `6c242c587d7132ccdf59b26d13117563bc9ced6d`.
- The checkpoint committed only the previously modified classifier. Other existing tracked and untracked work was left in place, not bundled into this repair. The protected hashes also describe the actual dirty working-tree data, not a hypothetical clean HEAD.
- To undo this repair while retaining the checkpoint and unrelated work, revert the code/test repair commit; do not use a whole-tree hard reset. The documentation-only delivery commit can remain.

## Actual changed files

1. `cooling_rag_mg/grade_classifier.py`: `dGH`; NFKC normalization of criteria; single/double-brace, case/space and full-width TBD recognition; preserve exact Unicode KB ID boundary matching; per-output classifier version, reason and explicit scope. New version: `grade-v3-dgh-normalized-explained`. Citation IDs themselves are not Unicode-normalized into potentially different identifiers. Numeric-unit recognition remains finite, not semantic understanding.
2. `cooling_rag_mg/evidence_contracts.py` (new): shared pure offline contracts for parameter validation, first-reference de-duplication, stable evidence selection, whole-record/whole-paragraph budgets, explicit missing applicability, and complete required shall/citation field validation.
3. `cooling_rag_mg/kb_value_extractor.py`: preserve `value_text/operator/unit`; optional `parameter/conditions/model/source_span`; no inferred historical fields. Validate types/operators and supplied verbatim source span. Distinguish no values from API/parse/schema/truncation/omitted-context failures in annotations. Legacy public list-return interface retained.
4. `cooling_rag_mg/structured_req_generator.py`: serialize complete parameter records including operator/unit and explicit nulls, source/applicability metadata; bounded whole paragraphs rather than character slicing; reject invalid required fields/citation types instead of returning apparently valid partial items. Prompt explicitly treats missing applicability as unresolved, not a license to generalize.
5. `scripts/77_run_v4_rag.py`: replace set iteration with first occurrence in saved v3 references; store ordered input IDs, missing IDs, selected IDs, selection policy, evidence block hash and extraction statuses for future runs. The script was not run against production inputs or outputs.
6. `tests/test_bounded_evidence_contracts.py` (new): saved examples, synthetic boundaries, multi-process prompt hashes, and a fully mocked entrypoint integration test writing only under pytest temporary storage.
7. `tests/test_truncation_config.py`: update the existing limit test to check whole-paragraph budget behavior instead of expecting arbitrary character slicing. The 1200/2400 environment settings remain exercised.

## Determinism and budgets

The selection policy is `numeric-first-stable-first-reference-v1`. Numeric-first remains a simple existing heuristic, not a relevance/authority optimum. First-reference order comes from saved v3 attribution lists, not recovered historical retrieval rank. Stable sorting preserves that order within each group; duplicate IDs are removed and conflicting duplicates fail explicitly. Default maximum remains 12; configured positive limits remain supported.

Default extraction context stays 1200 characters; final evidence context stays 500 characters per unit. Whole blank-line-delimited paragraphs (including adjacent single-line table rows) are retained or omitted. Oversized paragraphs are not sliced. Omission counts/statuses are explicit. Parameter JSON records have a separate 1600-character per-unit budget and applicability records a 700-character budget; each is retained whole or omitted explicitly. Source titles over 300 characters are replaced by an explicit unknown/omitted label. Optional missing parameter fields become null in the prompt, not manufactured content in historical data.

This conservative strategy can omit a useful oversized paragraph, and paragraph boundaries cannot guarantee semantic completeness across separate paragraphs. It prevents mechanical partial-record truncation, not all semantic context loss. It can yield more TBDs. No quality improvement is claimed without model verification.

## Offline checks and reproducible commands

Use the delivered `run_offline_tests.py`, rather than invoking pytest directly: the existing repository autouse fixture clears its default disk cache. The launcher substitutes a disposable cache, blocks socket connections, suppresses bytecode and pytest cache writes, and directs temporary files into the delivery directory.

PowerShell environment:

```powershell
$env:PYTHONPATH=''
$env:PYTHONIOENCODING='utf-8'
$env:OMP_NUM_THREADS='8'
$python = 'D:\Users\yando\miniconda3\envs\cooling_rag_env\python.exe'
$runner = 'D:\cooling_rag_multigranular\cooling_rag_multigranular\revision_artifacts\bounded_optimization_20261018\run_offline_tests.py'
& $python -B $runner
& $python -B $runner tests/test_requirement_status.py tests/test_ea_folded_ui.py tests/test_ea_validate.py tests/test_paper_tables.py tests/test_paper_numbers.py
```

- Final core suite: **98 passed** (`test_final_core.txt`), including all direct classifier/extractor/generator tests, truncation configuration, token limits, review routing, revision contracts, v3 generation, fill-empty behavior, failure contracts, pipeline passthrough, numeric normalization and grounding.
- Downstream suite: **41 passed** (`test_downstream.txt`).
- Total: **139 passed**. `git diff --check` passed.
- Three fresh processes, `PYTHONHASHSEED=1,17,123`, produced the same hash: `bedfbac2a44af269b75e4f677e3b2a565bfaa4f2feb478d2902b516756ca4695`. This hashes the new full prompt template over 60 saved evidence/value sets, using source IDs as fixed source-text fixtures. It does not reconstruct original historical prompts. The integration test separately exercises script 77 from mocked v3 references through extraction, prompt generation, classification and a new temporary output file.
- Initial attempts: the generic Python runtime lacked diskcache; the existing project Conda environment was used without installing packages. First executable suite: 94 passed / 1 failed because saved operator strings include `最大`, `up to`, `max`, `大于`, `min.`. The contract was fixed to preserve these explicit legacy forms, then 97 passed. Adding the entrypoint integration test gave the final 98 passes. Earlier logs are retained for transparency.

## Three saved examples: no regeneration

Source: `data/search_results/exp_v4/rag_v4_results.json`. Positions below are one-based within each source's output list.

| Example | Saved grade | Checkpoint classifier | New classifier | What this means |
|---|---|---|---|---|
| OR001, position 1 | B | C | C | Prior checkpoint already fixed single-brace TBD. This repair preserves it; no new engineering threshold was generated. |
| OR010, position 1 | C | C | B | `≤ 10 dGH` is now recognized as numeric and cited. This is a rule correction, not newly established applicability or correctness. |
| OR023, position 5 | B | B | B | Suspicious `-100°C` remains unchanged. Grade B still checks numeric formatting and citation metadata, not semantic support. |

All three criterion strings are unchanged. `diagnostic.json` records the separate saved/checkpoint/new grades and reasons. No full-table performance metric was recomputed or used as an acceptance target.

## OR023 source risk, preserved separately from KB

Local evidence: `data/processed/evidence_units_v3_audited.jsonl`, line 187, `E-HT-COMP-036`; declared source `S30 MAN Energy Solutions, 49/60 Project Guide, Marine Four-stroke diesel engine`, location P134. It already contains `-100°C` in the engine-inlet preheating statement. Its text is 449 characters, so that saved example is not explained by a 500-character text cut. The KB does not record a sufficient edition/date identity. A filename search under `D:\cooling_rag_multigranular` did not locate a matching local MAN 49/60 PDF; no local page screenshot or exact original-edition match is claimed.

Independent official-source verification supplied by the coordinating task: [MAN 49/60 IMO Tier II Project Guide](https://man-es.com/applications/projectguides/4stroke/Propulsion/PG_P-II_4960.pdf), Revision 12.2025/3.0, dated 2025-12-03, 508 pages, SHA256 `29da4ba210bc2bba9b3f00d6f4f0aee15c6c7847568d5dd69355b3028692ffc1`. The coordinating task reports visually checking printed/PDF P134: engine inlet before-start preheating is min 60 / max 80°C; an adjacent LP TC outlet row has a separate dash and max 100°C, footnote 3, operation at alarm level. This version does not support the KB's -100°C statement. Row/column concatenation is a plausible cause, not proven provenance of the local KB. The local original edition remains unmatched. No KB correction was made, and no screenshot is fabricated or included.

## Preservation and remaining limits

`protected_before.json` and `protected_after.json` cover **366 files**: all files enumerated in project `data/processed`, `data/search_results`, the submission manuscript directory, and discovered `.xlsx/.xlsm` workbooks under the outer project root. Every hash matched. A separate comparison of tracked files confirmed no unrelated tracked content changed. Pre-existing inaccessible pytest temporary directories were not accessed; these are not experiment-data inputs.

The repair does not validate numeric entailment, resolve conflicting manufacturers, prove project applicability, repair the historical -100°C, establish extraction recall, recover historical retrieval rank, or rerun Stage1. v4's historical reuse of v3 remains acknowledged; `_pairs_used` recording gaps are not evidence that reuse did not occur. The no-RAG/RAG prompt asymmetry and limited unit vocabulary remain documented. The extractor's 600-token response budget is unchanged; truncation is now explicit rather than silently treated as no numeric evidence.

A later authorized, small paired model check would be needed to measure whether the new context/validation behavior improves outputs or increases empty/TBD results. Use preselected saved cases with missing conditions, long paragraphs and more than 12 candidates; compare trace completeness, unsupported values and applicability, not grade uplift. That model check was not executed and does not reopen S2 or require a new expert task.
