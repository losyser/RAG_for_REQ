# Final project audit handoff (supersedes remaining-work notes in STAGE_HANDOFF.md)

## Final verification

Full suite: 241 passed, 0 failures, 0 errors, 0 skipped; pytest console reported 7.28s; XML duration 7.283s. Latest evidence: tests_final_v3.xml. Command:

    run_py.bat -m pytest -q tests -p no:cacheprovider --basetemp revision_artifacts/audit_20261015/pytest_final_v3 --junitxml revision_artifacts/audit_20261015/tests_final_v3.xml

Environment: Windows build26200 AMD64; Anaconda Python3.11.15; pytest9.0.3, openpyxl3.1.5, NumPy2.4.6, SciPy1.17.1, scikit-learn1.8.0. Wrapper clears PYTHONPATH, OMP_NUM_THREADS=8. See test_environment.json.

Nine CLI negative integrations pass (expected nonzero exit1 and no scores directory): blank annotations, immutable text edit, blank ID, changed ID, formula answer, deleted sample, duplicate sample, manifest-content tamper, manifest/key hash tamper. Unit tests also cover S1/S2/S3/S4 immutable fields, key/sample mismatch and permitted annotation-only edits. All tests use independent fixtures/copies; no expert answers were written into the study workbook. See integrity_integration/results_final.json and logs.

Original workbook, key and predictions are bound to frozen baseline SHA256. Contract is reconstructed from those verified inputs; a modified manifest cannot silently redefine the template. Rows and column sets, immutable text, all sample IDs, candidate identity and formula annotations are checked. Annotation completeness and taxonomy/count validity are separate gates. Second-annotator S1 gets identical integrity validation and ID alignment. This is accidental alteration detection, not a cryptographic signature against replacement of the authoritative baseline itself.

Source profiles now also bind each of the five experiment-arm filenames to its baseline SHA256; this detects cross-arm replacement even though Qwen/DeepSeek historical metadata use the same arm names. Offline audit rerun passed. No new experiments.

## Metric versions and evidence

Historical paper_numbers.json and all original evaluation artifacts remain unchanged. grade-v2-placeholder-unicode-id changes only deterministic placeholder/ID interpretation: DeepSeek RAG B73→69, C439→443, A+B14.4→13.6%; A1/X0 unchanged. Qwen RAG citation91.7→92.6%, L1 citation18.3→19.2%; grades unchanged. Other three arms' registry grade/citation summaries unchanged. New result adoption is an author decision.

Routing all-output denominators: 513/295/485/229/154. Historical RAG report409; refreshed513. RAG routes OPEN_ITEM369, ENGINEER_CONFIRM142, ADJUDICATE1, SPOT_CHECK1. Other-arm routes and heuristic category counts are in routing_v2.json; no semantic truth/math derivation inferred. Candidate conflicts do not establish same-parameter applicability or authority.

Posthoc v2 selected-sentence denominators140 RAG/204 no-RAG. Historical any-supported126/10 splits into all-reported-supported124/2 plus partial2/8. Contradicted1/3 and no-numeric6/3 retained. Not-found7/188. Numeric verdict denominator306/489; supported291/13, contradicted1/5, unverifiable14/471. Full sentence support remains unestablished without independent extraction-coverage validation. Two RAG row-to-final matches are ambiguous, retained explicitly.

H_hard historical source-level macro paired Wilcoxon is unchanged (RAG1.4603% vs no-RAG0.09524%, p0.02615718,60 pairs). New offline micro counts are separate in hhard_audit.json, not substituted for macro. Future script59 now records errors distinctly and excludes them from evaluated denominator; historical not_found error conflation is unrecoverable offline. Existing Qwen paired quality64/51/125 remains an automated paired evaluation, not expert annotations.

Sensitivity boundary/overlap is25 condition-numeric sentences, not a full end-to-end window experiment; RRF k0 is smoothing. Default+3 successful e2e variants remain distinguished from failed HTTP402 trunc_1200. Current deterministic guards reject empty/error/incomplete variants. No historical token or memory settings invented.

## EA and expert status

EA static acceptance: merged23 requirements/20 Nesting plus OR00812/11, OR0416/5, OR0525/4. XMI, per-case CSV, property/source relations and hashes are in ea/. Native import remains BLOCKED: new64-bit automation server times out (0x80080005; DCOM10010). Both EA installations/registrations exist. Existing EA.App works from32/64-bit Framework PowerShell and current model is revised.qea; it was not switched/closed/modified. No supported native GUI tool in this session. See ea/diagnosis_final.json and read-only logs. audit_import.qea is still a vendor base copy, NOT an imported model. inspection_preview.svg is NOT EA output and has no completed raster visual QA. Cached English translations require human review. No satisfy links invented; current connectors are Nesting, not verified deriveReqt/trace.

Expert packet ready: workbook copy, independent instructions, blinded sample manifest. Coordinator-only expert_integrity_manifest.json binds original files. S1=120, S2=570, S3=50 independent judgments(25RAG A/B+25baseline X), S4=50. Missing answers still block all scoring; no kappa/F1/answers fabricated. S3 item10 exact text maps to OR008.9 and OR008.10; unresolved identity ambiguity must be retained/reviewed. DeepSeek saved Stage1 predictions match v3 pairs; new v4 pair predictions are not recorded. Existing candidate pool is not a complete gold standard without expert missing-pair review.

Coordinator scoring command after real annotations:

    run_py.bat scripts/98_score_expert_workbook.py FILLED.xlsx --coverage-confirmed --integrity-manifest revision_artifacts/audit_20261015/expert_integrity_manifest.json --baseline-manifest revision_artifacts/audit_20261015/baseline_manifest.json --out-dir revision_artifacts/expert_scores_NEW

## Complete source-change list

- cooling_rag_mg/grade_classifier.py
- cooling_rag_mg/review_routing.py
- cooling_rag_mg/revision_audit.py
- cooling_rag_mg/expert_integrity.py
- scripts/59_evaluate_v3.py
- scripts/70b_kb_verification_v4.py
- scripts/92_export_ea_native_xmi.py
- scripts/97_build_expert_workbook.py
- scripts/98_score_expert_workbook.py
- scripts/99_retrieval_sensitivity.py
- scripts/109_revision_audit.py
- tests/test_revision_contracts.py
- tests/test_ea_revision_format.py
- tests/test_evaluation_failure_contract.py
- tests/test_expert_integrity.py
- docs/superpowers/plans/2026-10-15-revision-audit-status.md
- .superpowers/sdd/2026-10-14-se-minor-revision/progress.md

New result files live only in revision_artifacts/audit_20261015; deliverables_manifest.json gives hashes. The git modifications ea_native_sel.xml and ui/pages/evidence_manager.py predate this task and remain user-owned. 178 original data/submission file hashes rechecked unchanged. No commits, push, paid calls, external messages/publication or paper/reply edits.

## Actual remaining items

Expert independent annotation and missing-pair coverage review; resolution of duplicate S3 provenance; authors' decision on metric version adoption; native EA new-model import/render after user-assisted startup; translation/applicability/derivation judgments. No unsupported authority ranking or mathematical proof claimed. Publication checklist remains preparation only, no Zenodo/submission. No pending code test rerun after this final full suite.
