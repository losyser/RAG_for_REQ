# Project revision audit — stage handoff

Work performed on revision-se-4762284, HEAD 0657f934a932675a4c41d51994996259f46d51c3. No commits, pushes, external publication, API experiments or expert contact. No AGENTS.md was found in the project tree. Handoff, progress ledger and 2026-10-16 EA plan were read. User modifications to ea_native_sel.xml and ui/pages/evidence_manager.py were not edited.

## Implemented and verified

- Baseline manifest: 342 files with SHA256. Final protection check: 178 original data/submission files unchanged. UI was not included in the initial manifest; it was never edited by this task. Its existing git diff remains user-owned.
- Five-arm routing refreshed independently: RAG 513, no-RAG 295, random 485, Qwen RAG 229, Qwen no-RAG 154. Historical RAG routing totaled 409 (104 missing). routing_v2.json contains every output row, source hash, arm labels, denominator, grade, classification, route reason, candidate conflict, and explicit semantic/math verification flags.
- RAG new routes: OPEN_ITEM 369 / ENGINEER_CONFIRM 142 / ADJUDICATE 1 / SPOT_CHECK 1. Conflict flags are rule candidates based on disjoint numbers sharing a unit, not proof of the same parameter or applicability. No automatic authority hierarchy is applied. Human parameter, scope and version adjudication is required.
- Grade v2 recognizes malformed single-brace TBD placeholders and full Unicode KB IDs. It still inspects only measurable_criterion with a finite unit regex plus KB citation tier/clause metadata. It does not prove truth. Original paper_numbers.json is untouched. DeepSeek RAG B changes 73→69, C 439→443, A+B 14.4→13.6%; Qwen citation rate 91.7→92.6%, L1 citation rate 18.3→19.2%. registry_comparison.json records differences; do not silently replace historical metrics.
- Posthoc original judgments reused, no new LLM judgment: RAG 140 selected sentences: all-reported-supported 124, partial 2, contradicted 1, not-found 7, no-numeric 6. No-RAG 204: all-reported-supported 2, partial 8, contradicted 3, not-found 188, no-numeric 3. Historical any-supported totals 126/10 retained. Numeric verdict denominators are 306/489. All-reported support is NOT strict complete sentence support: extraction coverage was not independently validated. Two RAG rows have ambiguous identical final-text matches.
- Script59 unit is extracted claim from shall_statement, excluding measurable_criterion. hhard_audit.json separately reports micro counts and preserves the historical source-level paired test. Historical not_found conflated API/parse failures; impossible to recover offline. Future script59 errors now explicit and excluded from evaluated denominators; full statement and retrieved passages are retained. Script70b parser reads verdict column only.
- Expert scoring blocks blank/invalid values, duplicate/missing/extra IDs, changed S2 candidate identities, invalid missing pairs, incomplete prediction coverage and omitted candidates. Zero-overlap F1 corrected to 0. Second annotator IDs aligned. New independent output directory and explicit whole-source coverage confirmation required. Existing workbook/key protected; blank workbook was actually run and blocked without creating scores. 840 missing-annotation errors; 570 candidate pool matches predictions. S1 120 / S2 570 / S3 50 (25+25 independent, not paired) / S4 50. S3 item10 matches duplicate OR008.9/OR008.10; keep ambiguity and resolve before publication. No expert scores fabricated. Current DeepSeek Stage1 predictions exactly match saved v3 pairs; current v4 does not record new pairs. Qwen paired quality judgments remain separate from experts.
- Sensitivity: boundary results are 25 condition-numeric sentence boundary analysis, not end-to-end window/overlap results. RRF k0 is smoothing. Three valid variants plus default have complete output coverage. Failed trunc_1200 absent at baseline, earlier ledger documents HTTP402; not reconstructed. Removed failed variant from runnable accepted list; summary excludes empty/error/incomplete variants. Historical token settings and memory remain unknown unless recorded.
- EA exporter now has pure build_xmi(), separate properties, single-paragraph text, 160x110 child / 200x110 parent geometry, validated citation IDs, CSV reviews, original Chinese and source-hash translation cache. Offline main makes NO API calls, legacy cache translations marked unverified, numeric/TBD mismatches fall back to source. Legacy helper interfaces remain for compatibility. Merged 23 requirements/20 Nesting edges plus OR041/OR052/OR008 individual exports pass static checks. Nesting denotes grouping only; deriveReqt is not asserted as verified; evidence IDs are traceability properties, not native trace connectors; no satisfy relationships invented.
- Native EA attempt failed at COM construction: 0x80080005 CO_E_SERVER_EXEC_FAILURE. User model was never opened. ea/audit_import.qea is merely an untouched vendor EABase copy, NOT an imported model. inspection_preview.svg is a generated inspection view, NOT an EA screenshot. See ea/import_status.json for exact manual steps. EA native import/render/visual QA remain blocked.

## Tests and commands

Use run_py.bat from repository root (clears contaminated PYTHONPATH and pins OMP_NUM_THREADS=8).

    run_py.bat -m pytest -q tests -p no:cacheprovider --basetemp revision_artifacts/audit_20261015/pytest_temp_run2 --junitxml revision_artifacts/audit_20261015/tests.xml

Result: 227 passed, 7.52 seconds, no deselections. Earlier run: 220 passed, 1 deselected, 4 tmp_path permission errors; resolved using a new basetemp, without security-setting changes. Subsequent minor changes added coverage-confirmed CLI gate and classifier version constant; blank-workbook integration passed, but full suite not rerun after those two small changes. Test failures before fixes were observed for single-brace TBD, missing EA builder/translation guard, and API-error misclassification.

    run_py.bat scripts/109_revision_audit.py --out-dir revision_artifacts/audit_20261015
    run_py.bat scripts/92_export_ea_native_xmi.py --sets OR041 OR052 OR008 --out-dir revision_artifacts/audit_20261015/ea
    run_py.bat scripts/92_export_ea_native_xmi.py --sets OR052 --out-dir revision_artifacts/audit_20261015/ea
    run_py.bat scripts/98_score_expert_workbook.py data/expert_round2/expert_workbook.xlsx --out-dir revision_artifacts/audit_20261015/blocked_scores_must_not_exist

Last command intentionally fails (SCORING BLOCKED); no scores produced. Reproduction should choose a fresh pytest temporary directory. Do not run scripts100/108 during the manuscript freeze: they write submission artifacts.

## Next work / decisions

1. Run final full suite after the minor coverage/version changes; inspect git diff and add arm-label/cross-mixing regression cases (hash/source-arm labels are recorded, but generic metadata alone cannot distinguish Qwen vs DeepSeek because historical tags are identical). Consider explicit source-profile allowlists.
2. Full expert gate does not yet hash-check immutable S1/S3/S4 text against original workbook; hashes are supplied in sample_manifest.csv for coordinator checking. Add immutable-text integration validation before using filled workbooks. Do not score until genuine complete annotations and coverage confirmation arrive.
3. Resolve S3 duplicate-text provenance and independently review extraction completeness before claiming strict full support. Historical labels and rates remain retained.
4. Open licensed EA normally, resolve startup/activation, then use a NEW model to import. Verify tags, endpoints, nesting and native rendering, export clear merged view. Native deriveReqt/trace template needs verified round trip and semantic approval; satisfy requires actual design-to-requirement evidence.
5. Native merged view remains blocked; generated SVG preview has not been raster-rendered for visual QA. English cache translations remain human-review items; numeric preservation alone is not translation fidelity.
6. Do not publish raw/private expert key, logs containing provider errors, licensed source documents, or private mappings. Prepare publication only after license/consent and provenance review. No Zenodo upload or submission performed.

## Publication preparation only

Candidate bundle: source code diff, tests, README/metric definitions, hash manifests, routing_v2, posthoc_v2, hhard_audit, registry_comparison, sensitivity_audit, stage1 provenance, EA XMI/CSV/static checks and completed expert aggregate results when available. Exclude expert_readiness_PRIVATE.json and original key from annotator/public packets. expert_packet contains workbook copy, instructions and blinded row hashes only. No publication action taken.
