# Post-commit review and corrections — 2026-10-18

This review examined the actual `3659d37..9f2ee05` diff, callers, saved records and tests. It supplements and supersedes the initial report where the implementation changed. It is a second-pass code review, not an independent human expert assessment.

Reviewed delivery: `9f2ee051e483b1c1b111c7ee5f32d3e62a7b0ab8`.
Review correction commit: `4b19b0531bd35895c6061b7f7c9e9bd37924bb3c`.
Original rollback checkpoint remains `3659d37ed21a2f286027f2603b171f2ad22565fe`.

## Findings actually reproduced and fixed

1. **Qwen ordering gap.** `scripts/77q_run_v4_rag_qwen.py` still traversed a set after the first repair. It now uses the same saved-reference ordered de-duplication and records the same selection IDs/policy/hash/extraction statuses as script 77. Both entrypoints have fully mocked end-to-end tests. No production entrypoint or external model was executed.
2. **Numeric ID false positives.** The previous regex graded `OR010dGH`, `ID10dGH`, and `ID-10dGH` as numeric (X without a citation). A numeric-token left boundary now rejects these; signed numeric values and unspaced Chinese phrases such as `硬度不超过10dGH` still work. Rule version is now `grade-v4-unit-token-boundaries`. It remains a finite lexical detector: it does not determine the engineering meaning of arbitrary identifiers or prose.
3. **Optional provenance fields were only type-checked.** `source_span` already required an exact substring, but `model`, `conditions`, and `parameter` did not. New extraction now requires every nonempty optional field to be verbatim in the supplied evidence context. Missing fields stay missing/null; no code invents a model or condition. This can reject paraphrases and is deliberately conservative. A substring check is not proof that the field is semantically attached to the selected value.
4. **Context completeness was insufficiently explicit.** The first repair counted omitted paragraphs but did not state completeness directly. Final evidence blocks now explicitly say `partial_unknown` when paragraphs were omitted, otherwise `all_paragraphs_retained` with a warning that this is only a text-retention statement, not semantic completeness. Extraction status is propagated to the prompt, with `unknown_historical` for absent old status. Partial extraction prompts explicitly warn that conditions may be missing. Cross-paragraph conditions remain a limitation; no claim of fully solved semantic context loss is made.

## Compatibility review

The saved-data schema scan is in `POSTCOMMIT_DIAGNOSTIC.json`:

- RAG: 513/513 satisfy the new required output schema.
- Random retrieval: 485/485 satisfy it.
- No-RAG: 293/295 satisfy it; two have non-list citations.
- Qwen: 0/229 satisfy it: all 229 have string acceptance criteria and citations; six additionally lack a nonempty string criterion.

These Qwen shapes were tolerated by the former minimal parser, but violate the documented generated-object contract requiring list criteria/list citation objects. The new generation parser intentionally rejects them rather than inventing clause flags, sources or metadata. Historical loading/grading does not call this parser and still accepts legacy string citations through the existing classifier. No existing historical outputs were rewritten. Future Qwen generation could yield more rejected/empty results; offline tests do not establish its schema compliance rate. This is an explicit compatibility boundary, not universal backward compatibility.

Legacy extraction records with the three string fields remain supported, including saved textual operators `最大`, `up to`, `max`, `大于`, `min.`. Optional fields are not backfilled from guessed facts. Parameter records serialize `value_text`, `operator`, and `unit` as separate JSON fields: a `value_text` already containing `<= 10 dGH` is not concatenated into `<= <= 10 dGH dGH`. The regression test checks this directly.

## Actual caller coverage

| Caller | Evidence order / repair coverage |
|---|---|
| `scripts/77_run_v4_rag.py` | First saved v3 reference order; repaired stable numeric-first/max12 generator; records selection provenance. |
| `scripts/77q_run_v4_rag_qwen.py` | Previously missed set traversal; now identical ordering/provenance contract, verified by mocked entrypoint test. |
| `scripts/85_run_random_retrieval_ablation.py` | Supplies its sampled list to the shared generator; numeric-first/max12 applies to that list. No change to random sampling design. |
| `scripts/99_retrieval_sensitivity.py` | Already uses sorted ID sets before the shared generator. Deterministic but lexical ID order, not first-reference order or recovered rank. Existing user modifications to this file were not touched. |
| `scripts/107_fill_truncated_sets.py` | Uses saved `_evidence_values` dictionary order and the shared generator. Reproducible for the same saved file, not a recovery of historical pre-set ordering. Not executed on historical outputs. |
| `scripts/80_stage25_sample_review.py`, `scripts/stage25_review_ui.py` | Call the backward-compatible list-return extraction interface. They do not run final max12 generation. Annotation exposes detailed status; the list interface logs non-success states. |
| `ui/pages/engineering.py:287` | Calls `engineering_requirement_agent.generate_engineering_requirements`, which invokes a separate LangGraph path (`engineering_requirement_agent.py:883` onward), not this v4 generator. Its prompt/context rules were not changed and are not claimed covered by this repair. |

There is no longer a set-traversal ordering bug in the two identified script-77 v4 entrypoints. This statement does not claim that every separate UI pipeline has been redesigned or tested for model output quality.

## Tests and limits of the evidence

- Initial delivery: **139 passing tests = 23 new + 116 pre-existing**. One pre-existing truncation test was deliberately updated to exercise whole paragraphs instead of arbitrary slicing.
- After review fixes: **155 passing tests = 39 new + 116 pre-existing**. Core 114; downstream 41. **No skips**, and no failed final tests. See `test_review_core.txt`, `test_review_downstream.txt`, and `test_review_collection.txt`.
- The same isolated-cache/socket-blocking launcher and commands in `OPTIMIZATION_REPORT.md` were used. Calls to model clients in tests are mocks. The hash-test subprocesses execute only local JSON reading, pure formatting and SHA256; no model/client creation or network operation is in that child code. This is an offline test setup, not a claim that an OS firewall was installed.
- Current hash for all three fresh processes (seeds 1/17/123): `6449ff4c10ecbe2a3912c586e35ff1c52daa0ebddb8e6c9808628432601a6c31`. The new context-status text explains the difference from the earlier delivery's hash. The fixture uses all 60 saved evidence/value sets with source IDs as fixed source-text placeholders, not reconstructed historical model prompts.
- No modules were skipped to achieve these counts. These are the selected directly related and downstream regression suites, not the entire repository test collection or a live UI/model integration run.
- Scoped `git diff --check` passes. An unrestricted working-tree diff check also reports pre-existing EA XML whitespace in unrelated user changes; those files were not reformatted or committed.

## Protection, OR023, and actual changed file list

The **366 unchanged protected hashes** consist of 25 processed-data files (including KB), 193 result/archive files, 110 submission-directory files, and 38 discovered workbooks. The workbook list explicitly includes expert packets, C/D before/after originals and working copies, plus baseline copies. This is not a blanket hash claim over every human-review JSON/report or every directory on disk. Unrelated previously tracked content also matches the pre-repair working-tree hashes.

OR023 remains unchanged at B. A new test calls the actual shared display function `requirement_status.normalize_status`: its semantic verification state is `not_assessed`, and its note explicitly says model claims/legacy Direct are not verification. The official MAN page discrepancy remains in the initial report as a source risk; no KB value, paper or workbook was changed, and no safety/engineering correctness guarantee is made.

Final source/test files changed since the checkpoint (8 files):

1. `cooling_rag_mg/grade_classifier.py`
2. `cooling_rag_mg/evidence_contracts.py`
3. `cooling_rag_mg/kb_value_extractor.py`
4. `cooling_rag_mg/structured_req_generator.py`
5. `scripts/77_run_v4_rag.py`
6. `scripts/77q_run_v4_rag_qwen.py`
7. `tests/test_bounded_evidence_contracts.py`
8. `tests/test_truncation_config.py`

All other files in these commits are isolated reports, manifests, test logs, and the offline test launcher under `revision_artifacts/bounded_optimization_20261018`. The complete repository remains dirty from pre-existing user changes; only this repair's source/test/delivery paths are clean after commit. No whole-tree cleanup or hard reset was performed.
