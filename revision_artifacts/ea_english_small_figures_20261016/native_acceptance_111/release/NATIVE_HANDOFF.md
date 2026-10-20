# Native EA acceptance — 111.qea, completed

Authorized target: D:\cooling_rag_multigranular\cooling_rag_multigranular\revision_artifacts\ea_native_followup_20261016\111.qea

A consistent SQLite backup was made before importing: native_acceptance_111/111_before_english_import.qea. Integrity check: ok. The original database had one root package and zero requirements/connectors/diagrams. Its content was preserved; EA changed only the existing root package LastLoadDate to the import timestamp. This timestamp change is explicitly recorded in existing_content_preservation.json.

Five official packages were appended, not the browser UI fixture:
- Diagram 2: REQ_english_full / Presentation_english_full — all 23 requirements.
- Diagram 3: REQ_english_scope — OR041, OR052, OR008 (3 nodes).
- Diagram 4: REQ_english_alarm — OR041, OR041.1, OR041.2, OR041.5 (4 nodes).
- Diagram 5: REQ_english_maintenance — OR052, OR052.1, OR052.4 (3 nodes).
- Diagram 6: REQ_english_temperature — OR008, OR008.1, OR008.5, OR008.8 (4 nodes).

All five packages passed real EA readback: 23 requirements, 467 independent properties, 20 relationships per package; names/stereotypes/complete property values and relationship endpoints/types match, zero mismatches. Memo comparisons normalize EA CRLF versus XML LF only. id/text are independent, canonical English text is unchanged, original names/text/source GUIDs and full selection maps remain included. Criterion, evidence, source, grade and route stay separate. The full model retains three gray sources, seven blue B and thirteen orange C; no green A was invented. Diagrams show title and ID, with long text/Notes folded. Only diagram visibility differs between selections.

Actual native PNG and EMF exports are in this release folder. All four small PNGs were visually inspected, and all four EMFs were independently rasterized and inspected. Source rectangles are 180 logical units wide, children 240; titles are complete English phrases. An initial native-only problem was found: EA added a package frame whose caption overlapped top nodes. The new exporter now reserves a 40-unit caption band and explicitly serializes the frame. Only the five new diagrams were adjusted. Final XML incorporates geometry read back from EA, including its title-driven sizing. Existing initial exports were retained separately.

Final PNG sizes: scope 1132×469; alarm 1069×837; maintenance 1069×662; temperature 1069×837. Full engineering view 1069×3894 is for inspection/appendix, not a small main-text figure. Small figures should be placed at approximately 150–160 mm width: main labels are roughly 9–10 pt at that width, based on visible raster text size, not a claim about final typesetter font metrics. Do not shrink them to half-column width. Native vector EMF permits resolution-independent placement, but renderer-dependent font wrapping/clipping and prominent trial watermark appearance were observed in independent EMF rasterization; inspect the final Word/PDF placement. PNGs are the native EA visual baseline, not 300-dpi artwork at that width.

All requirement titles, IDs and legends are English. The EA trial watermark contains Chinese and remains untouched in both PNG and EMF. It is a licensing overlay, not a translated model label. These are native-verified layouts with trial watermarks, not clean publication-ready artwork. A licensed EA re-export remains necessary for final journal figures. No watermark removal was attempted.

Full test suite after frame fix: 273 passed in 15.03s (tests_final.xml). Existing browser-click acceptance remains documented in the parent browser_acceptance folder; this round changes native figure geometry only and does not claim an additional browser rerun. No paper/reply edits, paid APIs, external publication, Git commit or push.

Use this release and english_paper_native_verified_bundle.zip for the revised caption-safe layout. Prior English ZIP/XML remain preserved as earlier versions. The new ZIP includes revised XML, PNG, EMF, GUID maps, translation/selection provenance, test results and native acceptance evidence; it excludes the database backup and browser test fixture.
