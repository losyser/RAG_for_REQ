# Independent annotation instructions

This packet contains only the original unfilled workbook and a row hash manifest. The original workbook was not overwritten. Keep expert_key.json and expert_readiness_PRIVATE.json with the study coordinator; do not send them to annotators. Do not inspect project outputs, arm identities, or existing KB labels before annotation.

S1 (120 items): independently assign component and intent/aspect using the supplied taxonomy. This estimates agreement with existing KB labels, not Stage 1 mapping accuracy. A second independent workbook allows inter-annotator agreement after aligning item IDs. Undefined kappa (constant categories) must remain null.

S2 (570 pooled candidate pairs, 60 source requirements): enter explicit 1 or 0 for every pair. Blank is unfinished, never negative. For EACH source requirement review the full taxonomy for relevant pairs absent from the pool; write missing pairs as component:intent separated by semicolons. Confirm coverage was reviewed for all 60 sources before scoring. Predictions are pooled from DeepSeek, Qwen, BM25 and embedding baselines; micro P/R/F1 pools pair counts across sources. Gold is not available yet.

S3 (50 independent numeric judgments): 25 sampled RAG A/B and 25 baseline X items are shuffled; these are independent items, not 25 paired comparisons. Assign correct/approx/wrong/unknown; unknown is a valid uncertainty answer, blank is unfinished. The existing workbook defines approx as within 20 percent; that is a study rule requiring domain review, not universal engineering acceptability. These selected strata do not estimate whole-arm correctness. Existing Qwen paired blind quality judgments are a separate automated evaluation and must not be called expert judgments.

S4 (50 extraction items): enter nonnegative integer n_correct and n_missed; n_correct cannot exceed the displayed extracted count. Assess only the supplied text, not undocumented historical context. Text column is first 1200 characters; historical prompt exposure requires run evidence.

Return a new filled workbook, never edit identifiers, source text, candidate component/intent fields, or add/remove rows. The scorer blocks missing annotations, invalid values, duplicate/missing/extra IDs and prediction candidates outside the pool. Do not fill answers on behalf of an expert.

Coordinator command (after complete independent annotation and coverage review):
run_py.bat scripts/98_score_expert_workbook.py path/to/filled.xlsx --coverage-confirmed --integrity-manifest revision_artifacts/audit_20261015/expert_integrity_manifest.json --baseline-manifest revision_artifacts/audit_20261015/baseline_manifest.json --out-dir revision_artifacts/expert_scores_NEW
Optional second workbook is a second positional argument. The output directory must not already exist.
