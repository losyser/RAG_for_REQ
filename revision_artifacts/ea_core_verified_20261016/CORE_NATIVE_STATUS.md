# Core id/text display — native validation status

Updated after user opened the designated independent test model.

## Verified native result

EA.App connection was checked for exact equality with:

`D:\cooling_rag_multigranular\cooling_rag_multigranular\revision_artifacts\ea_native_followup_20261016\structure_native_test_EMPTY.qea`

InstanceGUID=3FC4E5BCE81A; LibraryVersion=1628. Only this test repository was used. The two-node core-tags candidate imported successfully. The real EA-exported `native_minimal/diagram_1.png` was visually inspected: meaningful title header; independent id; full normative text displayed and wrapped; no visible criterion/TBD, source, route or other extra metadata. Source gray and child C orange are correct. Image contains the installed EA trial watermark; it has not been removed.

Native SQL readback checked both names/stereotypes and **all 21 model properties**, with zero mismatches, including full Chinese fields and criterion/TBD. EA stores text Value=`<memo>` and the full normative text in Notes. Native diagram StyleEx retains SUPTAG with the comma-separated non-core tag list. Evidence: native_minimal/field_validation.json, objects.xml, properties.xml, xref.xml, diagrams.xml, diagramobjects.xml, connectors.xml and original PNG.

This supersedes the earlier claim that core-tag filtering was entirely unverified. It does NOT establish merged-diagram acceptance.

## Exporter implementation and tests

`cooling_rag_mg/ea_structure.py` now writes SUPTAG for all model metadata tags except id/text. It retains Tag=1 and ShowTags=1 and never deletes metadata or truncates text. Geometry now uses 300-wide boxes with height estimated from the complete normative text rather than all suppressed metadata. All prior names, business IDs, element GUIDs, original properties and endpoints remain retained. Core-tag suppression of id/text is rejected by validation.

`tests/test_ea_structure_revision.py` adds a regression that ensures criterion/route/source/Chinese tags are suppressed only for display, id/text remain visible, and all original property values remain identical.

Final full suite: **252 passed, 10.46 seconds**, report tests_final.xml. Original exporter before this geometry/filter change is backed up as ea_structure.before.py. No paper/reply/original experiment/old export changes.

## New output status

The four `ea_native_*_structure.xml` files in this directory are newly generated with the native-validated SUPTAG mechanism. The earlier `ea_structure_20261016` output that displayed all metadata is superseded for presentation purposes. However, these new files' final merged dimensions and routes still require native visual acceptance.

## Current blocker

After the successful minimal import, ImportPackageXMI was called for the 23-requirement merged candidate, preserving GUIDs in the same authorized test repository. This call has not returned. A read-only SQLite inspection still found three t_object rows (package + two requirements) and one diagram. Therefore the merged import is NOT claimed successful and no merged native picture has been obtained.

The working hypothesis is a pending replacement/import confirmation because the package GUID already exists, but no GUI observation confirms that hypothesis. Computer-use skill was read; no callable node_repl/sky tool is exposed in this session. No blind click, Enter key, model switch, deletion, process termination or second import was issued. The existing import call remains pending.

User assistance needed: inspect the EA window for this exact test model and report any dialog's full text. A model switch is not requested. Once the pending call is resolved, check the actual database and continue with all 23 properties/relationships, native PNG and layout inspection. This document is an intermediate status, not final native merged acceptance.
