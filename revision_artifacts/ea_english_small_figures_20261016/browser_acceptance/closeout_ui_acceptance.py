from pathlib import Path
import json,hashlib,shutil
R=Path(r'D:\cooling_rag_multigranular\cooling_rag_multigranular');out=Path(__file__).parent
baseline=json.loads((out/'original_json_hashes.json').read_text())
changes=[p for p,h in baseline.items() if not Path(p).exists() or hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h]
assert not changes,changes
batch=R/'data/search_results/batch_ui_english_acceptance_20261016'
assert batch.resolve().parent==(R/'data/search_results').resolve()
expected=[batch/'engineering_requirements_acceptance/engineering_requirements.json',batch/'all_requirements_results.json']
assert {p for p in batch.rglob('*') if p.is_file()}==set(expected)
for p in expected:p.unlink()
(batch/'engineering_requirements_acceptance').rmdir();batch.rmdir()
record=json.loads((out/'browser_acceptance.json').read_text(encoding='utf-8'))
record['existing_json_files_hash_checked']=len(baseline);record['existing_json_files_changed']=changes;record['temporary_fixture_removed']=not batch.exists();record['ea_write_attempts']=0
(out/'browser_acceptance.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
target=R/'revision_artifacts/ea_english_small_figures_20261016/browser_acceptance';target.mkdir(exist_ok=False)
names=['browser_acceptance.json','browser_english_acceptance.py','prepare_ui_fixture.py','closeout_ui_acceptance.py','actual_original_before.xml','actual_original_after.xml','fixture_original_before.xml','fixture_original_after.xml','downloaded_mapping_template.json','ui_reviewed_mapping.json','browser_english_paper_figures.zip','original_json_hashes.json','fixture_engineering_requirements.json','fixture_all_requirements_results.json','01_loader.txt','02_original_loaded.txt','03_fixture_loaded.txt','04_template_downloaded.txt','05_wrong_mapping_rejected.txt','06_english_downloaded.txt','english_download.png']
for name in names:shutil.copy2(out/name,target/name)
report='''# Real browser acceptance — completed

Local Streamlit http://127.0.0.1:8501, real headless Chromium 148.0.7778.96 controlled through Playwright. A separate browser session was used; no paid generation button was clicked and EA was never accessed.

Actual clicks completed: Engineering requirements -> select existing saved batch -> load saved results -> original EA XMI download; load a uniquely named source-derived English offline fixture -> original XMI download -> English paper figures expander -> mapping-template download -> wrong-batch mapping upload and visible rejection -> current-model mapping upload -> English paper ZIP download -> original XMI download again -> reload original real batch -> original XMI download again.

The existing real batch returned 128 requirements and 98 relationships before and after; all properties and business-ID relationship endpoints are semantically identical (fresh technical GUIDs intentionally differ). The UI acceptance fixture has 9 requirements and 6 relationships drawn from the existing English source. Its ZIP contains one full view plus three 3-node views; all four packages preserve all 9 requirements, 6 relationships, independent id/text and every original property. English titles match the uploaded mapping. The mismatched 23-node production mapping was visibly rejected rather than silently applied. No browser page errors were reported.

This is a browser workflow fixture, not a replacement for the delivered 23-node journal model or its four figures. The fixture's displayed grades are recomputed by the live configured KB; they are not asserted to reproduce audited paper grades. The temporary batch was removed after acceptance. Existing source/result JSON files were SHA256 checked against the pre-test baseline with zero changes. See browser_acceptance.json for the exact count and download evidence.

Two initial automation attempts exposed script synchronization problems: clicking before Streamlit finished loading returned the old payload, and blindly toggling the loader collapsed an already-open expander. The script now waits for current content and render completion and checks the expander's actual state. The completed rerun passed. No product code fix was needed or applied during this round, so the previously completed 272-test suite was not needlessly repeated.

The screenshot is internal acceptance evidence only. Nothing in this browser test was published or uploaded to Library. The prior user-delivered ZIP and Library identity remain unchanged. EA 111.qea was not written or switched; new native PNG/EMF import, readback and visual acceptance remain pending explicit approval.
'''
(target/'BROWSER_HANDOFF.md').write_text(report,encoding='utf-8')
with (R/'revision_artifacts/ea_english_small_figures_20261016/FINAL_HANDOFF.md').open('a',encoding='utf-8') as f:f.write('\n\nUpdate: real browser workflow acceptance is now complete; see browser_acceptance/BROWSER_HANDOFF.md and browser_acceptance.json. This supersedes the earlier browser-not-tested limitation only. EA native acceptance remains pending.\n')
print(json.dumps({'evidence':str(target),'original_json_count':len(baseline),'changes':changes,'fixture_removed':not batch.exists()},indent=2))
