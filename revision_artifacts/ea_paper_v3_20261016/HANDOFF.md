# English paper figures v3 — unified acceptance

The default `paper/` folder contains exactly four English small figures, each as PNG, EMF and matching XML (12 files). Audit material, browser downloads and full-batch Chinese tests are excluded from this folder and the paper ZIP. Each XML retains all 23 requirements and 20 Nesting links; only the selected diagram view has 3/4/3/4 nodes.

## Screenshot diagnosis

The supplied screenshot `libfile_072905358d5881918d49f7bd0cf3e6a5` was downloaded with its Library metadata and visually inspected. The bottom text was not an error: `ea_status_view.py` inserted a Comment containing “Coloring by Evidence support. Reported support is unverified; missing status = Not assessed.” followed by the reported-status list and “Nesting = grouping.” The dense Chinese root was its full normative sentence used as its name. That v2 audit figure should not have been presented as a paper deliverable.

The v3 paper exporter removes diagram comments/long legends and validates all root and child English names. It emits exactly four selected figures and puts provenance under audit/. Both root and child full text remains separately in Notes and the independent text memo; only name and id are shown by default.

## Per-figure visual acceptance

All four native PNGs and all four EMF renders were individually viewed. The EA trial watermark is retained unchanged; its vendor text is the sole exception to English-only visible content. EMF and PNG can render fonts/watermark differently, but names, IDs, grouping, selected nodes and colors agree.

| Figure | Nodes | 1 Short English names | 2 Folded Notes + text/id | 3 English | 4 Small view | 5 Dual states retained | 6 Clean figure | 7 Native/XML/vector match |
|---|---:|---|---|---|---|---|---|---|
| Cooling Requirement Scopes | 3 | Pass | Pass | Pass* | Pass | Pass | Pass* | Pass |
| Low Supply Alarm | 4 | Pass | Pass | Pass* | Pass | Pass | Pass* | Pass |
| Pump Maintenance Access | 3 | Pass | Pass | Pass* | Pass | Pass | Pass* | Pass |
| Temperature Control | 4 | Pass | Pass | Pass* | Pass | Pass | Pass* | Pass |

*Legal EA trial watermark retained. All titles are readable; two-line PNG titles are intentional. No debug text, paths, exception traces, status paragraphs or unrelated legends are shown. The root OR008 and child OR008.1 Notes were expanded, visually checked, then refolded; the new diagram cache was closed and rendered again to confirm the compact frame returned. Evidence is under audit/, not paper/.

## Semantics and tests

Rule grade and evidence support remain separate attributes driven by the same shared state layer. The formal English sample retains B7/C13 plus three source nodes; no A was invented. Its 20 children have no reported support status and remain Not assessed, with semantic_verification_state=not_assessed. Neither B/C nor legacy Direct implies verified support. The figures use Rule grade; the real browser also successfully exported Evidence support mode with the same four views and preserved attributes. Long definitions belong in attributes and this report.

277 tests passed (audit/tests.xml). Real browser downloads in both modes contain precisely four small-view XMLs with 3/4/3/4 visible nodes, no english_full file, and no Comment legend (audit/browser/acceptance.json). Every XML retains 23 complete requirements. Native readback checked 92 requirement instances, 2,788 attributes and 80 relationships, plus names/Notes/text and colors. Exact details: audit/native_acceptance.json. No paid generation or translation was used; this is the existing formal English sample, not a translation of the Chinese batch.

## EA safety and previous save differences

Current model: revision_artifacts/ea_native_followup_20261016/111.qea. New packages are Paper v3 - Cooling Requirement Scopes / Low Supply Alarm / Pump Maintenance Access / Temperature Control; diagrams 11–14. Backup: 111_before_v3.qea.

The previous v2 differences already existed in the first readback after ImportPackageXMI, before later per-diagram repairs (audit/prior_save_investigation.json). This associates the change with import-time diagram/cache saving but cannot establish which changes originated in user edits versus EA automatic saving. No old layout was rolled back.

V3 used native per-object creation, not ImportPackageXMI or SaveAllDiagrams. It did not open old diagrams or switch repositories. Only the new temperature diagram cache was closed following its Notes test. All existing rows in eight model/diagram tables are unchanged from the pre-v3 backup and the immediate pre-create snapshot: 439 objects, 11,069 properties, 336 connectors, 9 diagrams, 67 diagram objects, 40 diagram links, 10 packages and 425 xrefs. See audit/backup_to_final_preservation.json and audit/old_content_preservation.json.

All 137 existing data JSON/JSONL/XML hashes are unchanged. The temporary browser fixture has been removed after retention under audit/. Papers, response letter, original exports and user changes were not overwritten; no Git commit or push was made.

## Deliverables

`paper/`: only the four PNG/EMF/XML triplets. `english_paper_v3.zip`: exactly those same 12 files. `audit/`: tests, raw readback, browser proof, original-name/text mapping, code patch and supporting material. No audit output is included in the default paper ZIP.

Remaining limits: trial watermark requires licensed EA for clean publication artwork; the status layer is not an independent semantic verification workflow. Fresh XML import into another repository was not performed this round to avoid the previous global-save side effect; instead native objects were created through EA and every delivered XML was reconciled to the actual native GUIDs and readback.
