# English compact paper views — handoff

Project: `D:\cooling_rag_multigranular\cooling_rag_multigranular`.
New artifacts: `revision_artifacts/ea_english_small_figures_20261016/`.

## Completed

- New exporter `cooling_rag_mg/ea_paper_figures.py`, CLI `scripts/94_export_english_paper_figures.py`, tests `tests/test_ea_english_paper.py`.
- Minimal UI addition in `ui/pages/engineering.py`: **English paper figures / 英文论文分图** expander. Download a mapping template for the current UI model, upload reviewed English titles/text and 3–4 selections of 3–5 IDs, then download **Export English paper figures + full EA model**. The button uses the current `xml_bytes`; it never substitutes the audited example data. No translation API is called.
- The latest offline loading/source restoration logic and parent mapping in ea_ui_export remain unchanged. The exact pre-export UI region is regression-tested against this round's backup. evidence_manager.py is byte-identical to its backup.
- Five independent XMI packages plus matching GUID maps, `selection_translation_map.json`, `provenance.json`, `static_validation.json`, and `english_paper_bundle.zip`. ZIP contents match the loose deliverables byte for byte.

| Package/file stem | Visible IDs | Purpose |
| --- | --- | --- |
| english_full | All 23 | Complete engineering view, not a small journal figure |
| english_scope | OR041, OR052, OR008 | Three compact independent scopes, no invented edges |
| english_alarm | OR041, OR041.1, OR041.2, OR041.5 | Alarm display, redundancy, configuration scope |
| english_maintenance | OR052, OR052.1, OR052.4 | Direct removal and manufacturer access requirements |
| english_temperature | OR008, OR008.1, OR008.5, OR008.8 | Actual B/C criterion outcomes |

All diagram titles/labels/legends are English. Root titles are `Low Supply Alarm`, `Pump Maintenance Access`, and `Temperature Control`; root rectangles are 180 units wide instead of 240. Source scopes use a compact horizontal row. Child titles are short complete English phrases (maximum 48 characters). Bodies/Notes are hidden by default; title and independent id are visible. Canonical independent text remains a full memo; native Notes is its display projection. Selecting fewer diagram nodes does not delete model elements or relationships.

The audited sample already has English normative text, so **every canonical text is unchanged verbatim**, including numbers, units, shall/must, references and conditions. No automated translation was needed. Hidden criterion/source/evidence/routing attributes remain in their original language and unchanged; the English-only requirement applies to the displayed figure, not to deletion of original metadata. Other UI batches can supply human-reviewed English translations; the adapter checks original content identity and rejects changed numeric/literal TBD tokens, but these checks cannot certify semantic, unit or modality equivalence. Existing English normative text cannot be rewritten by this exporter.

Example: name=`High-Temperature Valve Setpoint`; id=`OR008.1`; text=`The setpoint of the temperature control valve shall be checked against the main engine manufacturer's technical data. The high-temperature cooling water engine outlet temperature setpoint shall be 79°C nominal, and the mechanical thermostatic element adjustment range shall be 77-85°C.` Criterion, grade B, citations and route remain separate fields. Original name is `High Temperature Cooling Valve Setting` in paper_original_name; original text, source technical GUID and input SHA256 are independent provenance fields and are also in the external map.

Each package retains 23 requirements, 20 relationships and all 352 original property values. Added provenance/display backup brings the total to 467 independent properties. Technical GUIDs are fresh per package, business IDs remain unchanged; `paper_source_guid` deliberately retains the original GUID. Full source colors remain 3 gray sources, 7 blue B and 13 orange C; no A is invented. Legends list only grades present in the selected diagram. Selection is illustrative, not statistically representative.

## Reference and structure

The locally retained supplied reference is `C:\Users\yando\Documents\Codex\2026-10-16\task\references\ea_native_sel1_verified.xml`; SHA256 was rechecked as `b2893c10d44a6154dbdc0d3447e1526cd0847bd0613aaabe68bd4fbaab2bcd89`.
This builds on the earlier verified structure: requirements are ClassifierRole elements nested in Collaboration, the support EARootClass is Class, id/text are content-level TaggedValues, text uses `<memo>#NOTES#`, requirement stereotype/xref is retained. Name is a meaningful title rather than an ID/grade/audit string. Original documentation survives as original_documentation; Notes is the explicit complete-text display projection. Diagram ShowNotes=0 and SUPTAG hide the long memo/metadata visually without deleting any fields. Source GUID/property count/readback evidence from earlier rounds remains in ea_structure_native_final_20261016 and ea_folded_paper_20261016; it does not establish native acceptance of this new round.

The newest screenshot Library ID `libfile_9f25edc10264819188fd9fa130d4c56d` returned only “Action completed” with no pixels. It was not visually inspected.

## Reproduction

From the project root, with PYTHONPATH cleared and the project Python environment:

```powershell
$env:PYTHONPATH=''
& 'D:\Users\yando\miniconda3\envs\cooling_rag_env\python.exe' scripts/94_export_english_paper_figures.py --source revision_artifacts/ea_english_small_figures_20261016/source.xml --mapping revision_artifacts/ea_english_small_figures_20261016/selection_translation_map.json --output revision_artifacts/ea_english_REGENERATED
```

The CLI refuses an existing output directory. Omit --mapping to create a template for another source. Fresh GUIDs mean a new run has different technical identifiers; compare business IDs, content and manifest mappings.

## Acceptance limitation — native export pending

The native import helper checked the repository **before any write** and refused because EA is now connected to `revision_artifacts/ea_native_followup_20261016/111.qea`, rather than the previously authorized `structure_native_test_EMPTY.qea`. No new package was imported, no model was switched, and no user process was stopped. Permission to append these five new packages to 111.qea was requested and is pending. Without it, this round has **static XML and automated test validation only**, no new EA PNG/EMF or native readback/visual QA. Do not describe these figures as publication-ready or reuse prior round PNGs as evidence of the new English layouts. Native image export and wrap/legend inspection remain outstanding. Trial watermarks must remain when EA exports them.

Original results, old XML/accepted figures, source data, papers/replies and models were not overwritten. No paid APIs, publication, Git commit or push.

Final full test suite: 272 passed in 7.90s; see tests_final.xml. Cache and pytest temporary directories were isolated from application caches.


Update: real browser workflow acceptance is now complete; see browser_acceptance/BROWSER_HANDOFF.md and browser_acceptance.json. This supersedes the earlier browser-not-tested limitation only. EA native acceptance remains pending.

Native acceptance completed after explicit approval for 111.qea. See native_acceptance_111/release/NATIVE_HANDOFF.md. Final caption-safe XML/PNG/EMF are in that release folder; all earlier outputs remain retained.
