# UI / EA folding / paper figures — final handoff

Artifact directory: `D:\cooling_rag_multigranular\cooling_rag_multigranular\revision_artifacts\ea_folded_paper_20261016`.

## Actual UI route and code

Before: `ui/pages/engineering.py` download button -> `cooling_rag_mg.sysml_exporter.export_payload_bytes`. This was project-specific SysML-inspired XML, explicitly not standard importable XMI. It never called script 92.

Now: same UI download button -> `cooling_rag_mg.ea_ui_export.export_ea_payload_bytes` -> pure native builder in `scripts/92_export_ea_native_xmi.py` -> `cooling_rag_mg.ea_presentation.presentation_xml`. Download filename is `requirements_ea_folded.xml`. This uses the UI's current normalized source requirements and configured `cfg.paths.evidence_units_jsonl`; no paid API or translation request. Every UI download uses fresh technical GUIDs. Real source/child business IDs, topic titles, exact multiline text and parent IDs are retained. The full original payload/individual records (including explicit relationship descriptions, gaps, scores and confidence if present) remain memo JSON attributes. Native connectors visualize parent grouping, not an unverified formal refine/satisfy claim.

`ui/pages/evidence_manager.py` is not the export route and was not modified; byte equality with the start-of-round backup is checked. The old custom XML API remains available for existing callers.

New files: `cooling_rag_mg/ea_ui_export.py`, `cooling_rag_mg/ea_presentation.py`, `scripts/93_ea_text_visibility.ps1`, `tests/test_ea_folded_ui.py`. Minimal edits: `ui/pages/engineering.py`, `scripts/92_export_ea_native_xmi.py`. Script92 now defaults to folded output; explicit --structure retains the previous full id/text structure. --compact remains its existing compatibility alias for --structure. No paper/reply edits, commit or push.

## What A/B/C/X actually means

The existing `cooling_rag_mg.grade_classifier.classify_grade` uses a finite regex on **measurable_criterion**, followed by KB citation validation. It is neither a probability nor an estimate of semantic correctness.

1. C: a TBD placeholder is present, OR no recognized number+unit pattern exists.
2. Otherwise X: numeric/unit criterion exists but no valid cited ID exists in the supplied KB.
3. Otherwise A: at least one valid citation is L1 and has clause-location metadata/text matching the classifier pattern.
4. Otherwise B: valid citations exist but the A condition is not met.

The UI adapter explicitly maps acceptance_criteria (joined) to measurable_criterion only when the latter is absent, and evidence_ids to evidence_citations when absent. Existing support_status, review_route, quality-gate scores and reported confidence remain distinct. Confidence has no influence on color. Citation provenance/format is not a semantic approval; even A still requires applicability review.

Examples explain why numeric-looking text need not be B/A: OR008.5 is C because `10 to 15 times the pipe diameter` does not match the finite number+unit regex; OR008.8 is C because its criterion is a TBD placeholder; OR008.1 is B with `79°C nominal; mechanical thermostatic element range 77-85°C`. Their routes are separately ENGINEER_CONFIRM, OPEN_ITEM and ENGINEER_CONFIRM respectively. No classifier rule was changed to improve the figure colors.

## Folded display and actual operations

name remains a pure complete title; id and canonical SysML text are independent fields. Default folded diagrams show title + id and hide the **long text tag** via diagram SUPTAG. They do not render a fake `text=<memo>` label. The actual text memo remains accessible in Properties > Tags > text (memo editor).

To support a native per-element display toggle, element Notes is an explicit copy of canonical full text, while the previous documentation is retained verbatim in `original_documentation`. Criterion, citations, sources, grade and routing remain separate. Text is suppressed in the tag compartment while Notes is shown, so the diagram never repeats the same paragraph twice. This is **Notes display**, not a claimed automatic expansion of the memo tag. If canonical text changes later, re-export to refresh this display projection; the helper refuses inconsistent text/Notes rather than overwriting edits.

Manual EA operation: select a node -> right-click Compartment Visibility (Ctrl+Shift+Y) -> enable Notes to show the complete paragraph; disable Notes to fold. Set Maximum high enough for the full text (e.g. 10000). Selecting an element and opening its Tags text memo reads the canonical value. The menu procedure is documented by Sparx; this environment verified the corresponding native ShowNotes API rather than claiming GUI clicks.

For reliable single-node/all-node toggling **with automatic reflow**, first open one of the new Presentation_ diagrams, then run in Windows PowerShell:

```powershell
& 'D:\cooling_rag_multigranular\cooling_rag_multigranular\scripts\93_ea_text_visibility.ps1' -RepositoryPath 'D:\cooling_rag_multigranular\cooling_rag_multigranular\revision_artifacts\ea_native_followup_20261016\structure_native_test_EMPTY.qea' -Mode Expand -Ids OR008.1
```

Use `-Mode Expand -All` for all visible nodes, or `-Mode Collapse -All` to restore the compact view. Explicit repository equality and Presentation_ package guards protect existing user diagrams. The helper does not open/switch models or alter text/properties. Native single/all expansion and collapse were exercised; the final reflow handles long paragraphs and refreshes orthogonal paths. The selected-view graph stays the same when toggling.

Official API/menu evidence:
- https://sparxsystems.com/enterprise_architect_user_guide/17.1/modeling_fundamentals/setfeaturevisibility.html
- https://sparxsystems.com/enterprise_architect_user_guide/17.1/add-ins___scripting/diagramobjects.html
- https://sparxsystems.com/enterprise_architect_user_guide/17.1/add-ins___scripting/project_2.html

## Deliverables and native location

The open test repository is the exact path above. Existing `CoreTag_23_native_routed / REQ_native_routed` (diagram5) and the original two-node test remain preserved.

| File stem | Package / diagram | Diagram ID | Intended use |
|---|---|---:|---|
| folded_all | Presentation_folded_all / REQ_folded_all | 8 | All23 nodes,20 links, engineering/appendix; tall, do not squeeze onto a main-text page |
| paper_overview | Presentation_paper_overview / REQ_paper_overview | 9 | Four visible nodes,3 links: OR008 plus OR008.1/.5/.8 |
| detail_b | Presentation_detail_b / REQ_detail_b | 10 | Two expanded nodes: OR008 and OR008.1 |
| detail_c | Presentation_detail_c / REQ_detail_c | 11 | Two expanded nodes: OR008 and OR008.8; validates long complete paragraph |

Each stem has `.xml`, **native `.emf` vector**, and native `.png`. All four XML packages retain all23 model requirements/20 relationships; selection affects only diagram visibility. Fresh GUID maps are supplied. All original352 properties plus23 original-documentation backups survive native readback:375 fields per package, zero mismatches. SysML stereotype and independent id/text are preserved. Counts/colors for the full model:3 gray sources,7 blue B,13 orange C; no invented green A.

Selection is illustrative, not statistically representative: OR008 offers actual B/C variation in one family; .1 is a numeric setting, .5 illustrates a dimensionless-ratio classification limitation, and .8 illustrates deferred criterion plus a long body. Figure legends include only grades actually present in that view.

The diagrams use complete titles with wrapping, Arial font setting100, modest margins, direct tree-horizontal routes and a real legend. The selected figures are roughly1069px wide; at about150–160mm paper width their main labels/body are approximately9–10pt. Verify in the final typeset document; do not halve them to a narrow single column. The full engineering graph is intentionally tall. There is no large empty PDF page: native exports fit diagram extents.

## Verification and limits

- Final suite: **265 passed, 12.19s**, `tests_final.xml`.
- Native four-package readback: each23 requirements,375 properties,20 relationship endpoints/types; zero mismatches (`native_*/field_validation.json`).
- Actual UI adapter also imported as an explicitly synthetic regression package (diagram12, three nodes,50 fields,two nested parent edges). This fixture is not a paper figure and not evidence of real project grades. Readback preserved original non-OR IDs, Unicode and full JSON; EA normalizes LF to CRLF in memo fields, documented in its comparison result.
- After toggling,115 projected Notes fields across new probe/final packages were checked against their canonical memo texts; no mismatch. User evidence-manager file byte-identical.
- EMF signatures and native text drawing records verified; selected EMFs independently rasterized to `*_emf_render.png` and inspected. These are actual EA exports, not redrawn illustrations. Raw LOGFONT heights include coordinate transforms/watermarks, so they are not claimed to be final document point sizes.
- Initial standalone new-test invocation hit the existing test fixture's inaccessible default cache; the final suite used an isolated writable test cache. Early metadata namespace and native reflow issues were repaired before final verification.
- The referenced PDFs were visually assessed by the parent conversation, not falsely claimed to have been locally rendered here. Their static Notes expansion was not treated as proof of clickable memo behavior.
- **EA trial watermark remains in PNG and EMF; the EMF renderer makes it especially prominent. These are verified layout/vector deliverables, not clean publication-ready figures. A licensed EA export is required for clean final journal artwork. No watermark removal or licensing bypass was attempted.**
- Browser-level Streamlit clicking was not exercised; the actual button call is covered by an AST route test and its exact adapter has native import/readback coverage.
- Original datasets, old exports, already accepted diagram5 and user models were not overwritten. No active import remains. Repeat import of an identical XML reuses its technical GUIDs; use a freshly generated independent package or a new empty repository when another independent copy is needed.
