from pathlib import Path
import json,shutil,sqlite3,zipfile,hashlib
R=Path(r'D:\cooling_rag_multigranular\cooling_rag_multigranular');O=R/'revision_artifacts/ea_paper_v4_20261016';A=O/'audit'
# Re-run only preservation comparisons from the previous handoff helper.
s=Path(__file__).with_name('audit_v4_finish.py').read_text(encoding='utf-8');exec(s.split("for p in ['cooling_rag_mg")[0])
assert not checks['changed_data_files']
assert all(v['missing_or_changed']==v['added_or_changed']==0 for tables in checks['models'].values() for v in tables.values())
paper=O/'paper';paper.mkdir(exist_ok=True)
for p in (O/'candidate').glob('*.xml'):shutil.copy2(p,paper/p.name)
for p in (A/'native_render').iterdir():shutil.copy2(p,paper/p.name)
assert len(list(paper.iterdir()))==10
result=json.loads((A/'native_acceptance.json').read_text());result['visual_png_and_emf_review']='All three PNGs and all three EMF renders inspected; English names/IDs, 5 nodes, hierarchy and colors agree; trial watermark retained.'
result['browser_comparison_normalization']='Ignores random GUID/DUID, JSON object key ordering and source locator batch-directory versus exact file; all semantic data, node coordinates and displayed colors match.'
(A/'native_acceptance.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
with sqlite3.connect((O/'v4_independent_import.qea').as_uri()+'?mode=ro',uri=True) as src,sqlite3.connect(O/'v4_validated_saved.qea') as dst:src.backup(dst)
shutil.copy2(O/'HANDOFF.txt',A/'HANDOFF_before_native_validation.txt')
(O/'HANDOFF.txt').write_text('''V4 NATIVE IMPORT AND IMAGE VALIDATION COMPLETED

Test model: v4_independent_import.qea. Saved consistent snapshot: v4_validated_saved.qea.
Actual operation: one ImportPackageXMI call on candidate/paper_v4_combined.xml into the independent blank model; 15 requirements, 12 original Nesting edges, all three diagrams imported. No native AddNew reconstruction substituted for XML import.

Safety: exact ROT object !Sparx.EA.App:3688 was used for the test model, with full path and instance guards. Original !Sparx.EA.App:2880 remains on C:\\Users\\yando\\Desktop\\4x.qea. The new process initially waited behind normal EA registration/evaluation prompts; the built-in enabled Continue Trial entry opened the model. No registry, license, clock or security changes. Trial watermark retained. No old diagrams saved, closed or switched.

All three PNGs and all three EMF renderings visually inspected. R001/R004 each show the real root centered above four horizontal children. R002 retains two children and two actual grandchildren. Names are concise English titles; independent id is visible; complete English text remains in both Notes and text memo, folded by default. Original Chinese and every additional source attribute retained. Native readback confirms names, all tags, complete Notes, exact hierarchy and shared Evidence support colors. Direct/indirect claims remain explicitly unverified in stored properties.

Selected statuses excluding roots: R001 direct2/indirect1/gap1; R002 direct1/indirect1/review2; R004 direct1/indirect3. Grade independent: C4; B1/C2/X1; B2/C1/X1 respectively. Purposeful thematic/status selection, not population proportions. Assistant translation still awaits independent domain review.

Browser download and final XML agree in semantic content, hierarchy, coordinates and colors. Comparison normalizes random technical IDs, JSON key ordering, and batch-directory versus exact-file provenance locators. Browser ZIP retained in audit/browser/. Full tests: 285 passed (audit/tests.xml); no source code change after that run. 137 original data files and 8 core tables in each of 111.qea and 4x.qea unchanged (audit/preservation_check.json).

Deliverables: paper/ contains only 3 PNG + 3 EMF + 3 split XML + 1 combined XML (10 files). english_paper_v4_validated.zip contains these same 10 files. Use paper_v4_combined.xml for one-import all-three-diagrams. QEA files remain separate. Audit contains readback, mapping, browser proof and validation results.

Limitations: legal trial watermark remains; color labels represent reported support, not independent verification; English translation requires domain review. New test model remains open. Earlier blank probe process 21608 may remain at its registration prompt; original user process was never terminated.
''',encoding='utf-8')
with zipfile.ZipFile(O/'english_paper_v4_validated.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(paper.iterdir()):z.write(p,p.name)
(A/'final_delivery_hashes.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paper.iterdir()},indent=2))
for name in ['import_v4_targeted.ps1','validate_v4_import.py','finalize_v4_native.py','start_v4_test_model.ps1']:
    shutil.copy2(Path(__file__).parent/name,A/'scripts'/name)
print('Native validation completed; 10 final paper files; original data/models unchanged.')
