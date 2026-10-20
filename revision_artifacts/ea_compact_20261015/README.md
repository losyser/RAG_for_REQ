# Compact EA delivery

Uploaded ea_native_sel.xml exactly matches data/search_results/exp_v4/ea_native_sel.xml: SHA256 85aaf0c1561172efc8faaa7569aa060b4e391bf93edc7eb9d2206489a768198f, 143384 bytes. This is the old/user working export, not the audit detailed export (0789a5ff2b7efd25e064b2d8cc3581716c5f834a38ee40340589867fba98cc17,184203 bytes). Both files remain byte-identical. Reference sel1 was not located locally; its hash/content comparison is supplied by the parent, not independently rehashed here.

Open ea_native_sel_compact.xml in a NEW test EA model only. Same requirement/relationship IDs as detailed model are intentional, so importing into the user's existing model may update presentation. Do not import into revised.qea. No native import performed this turn due to established automation activation blocker; no user model or registry changed.

23 requirements,20 Nesting edges. Colors: Source3 grey#E8E8E8; C13 amber#FFF5D2; B7 blue#D2E6FF. A green#C8FFC8 remains available but no selected A exists; no grade fabricated. Grade colors are provenance/format, not EA lifecycle/status or correctness.

Each box: ID, short topic title, [grade | review marker]; maximum66 characters/4 lines. Full SysML text, criterion, source/evidence fields, reason and original Chinese stay unchanged. Original long notes stored as audit_notes_full; visible notes only hold a short marker. Additional display_notice explicitly separates presentation labels from engineering requirements. Compact XML is206262 bytes (larger because full content and display metadata are retained); compact describes rendering, not file compression.

Layout: two small groups side-by-side; OR008 across4 columns below. Canvas1040x1150 in the inspection PNG. Full diagram legend explains grades, review markers and Nesting. Each model element AND diagram instance gets actual grade colors. DUIDs/other style fields preserved; only targeted fields merged. Object Tag=0, diagram ShowNotes=0 and EAStyle ShowTags=0. Short notes bound any unexpected instance note display. No guessed per-object Notes serialization key. BCol/LCol/LWth are documented by Sparx:
https://news.sparxsystems.com/enterprise_architect_user_guide/17.2/add-ins___scripting/diagramobjects.html

The original display/no-color root cause is not established without EA import. Theme/instance overrides and note rendering need native verification. Legend Comment serialization also awaits native rendering. compact_inspection_preview.png was actually opened and visually checked; it is a deterministic XMI inspection rendering, NOT EA output.

Separate OR008/OR041/OR052 compact and detailed XMLs are provided for focused review. They are alternate standalone exports sharing business/model IDs, not instructions to import every file sequentially into one existing package. The full CSV is ea_review_sel_full.csv. Detailed originals preserved in audit_20261015/ea.

Reproduce byte-identical compact XMI in a NEW destination:

    run_py.bat scripts/92_export_ea_native_xmi.py --compact --input-xmi revision_artifacts/audit_20261015/ea/ea_native_sel.xml --out-dir revision_artifacts/ea_compact_NEW

Other supported mode: normal --sets export plus --compact and optional --identity-map. --input-xmi gives exact preservation of existing DUIDs as well as IDs. The CLI reproduction was verified byte-identical.

Tests:244 passed,0 failures,0 skips. Exact final command/log: tests_final.log; JUnit: tests_final.xml. New tests verify short labels/full-text preservation, grade instance color, unchanged IDs/endpoints/DUID, style field preservation and rejection of semantic data loss.

Changed code: scripts/92_export_ea_native_xmi.py; new cooling_rag_mg/ea_compact.py; new tests/test_ea_compact_revision.py. No original outputs, papers, response files or user models edited; no paid APIs.
