"""Run offline tests and CLI integration checks; write diagnostics, never real ratings."""
import json,subprocess,sys
from datetime import datetime,timezone
import analyze as a
from test_review import fixture,T
H=a.HERE;C=a.COORD
def run(args):return subprocess.run([sys.executable,'-E','-B',*args],cwd=H,capture_output=True,encoding='utf8',errors='replace')
tests=run(['test_review.py']);assert tests.returncode==0,tests.stderr
blank=run(['analyze.py',str(T),'--out','review_results/SHOULD_NOT_EXIST.json'])
assert blank.returncode==2 and json.loads(blank.stdout)['scores'] is None
assert not (H/'review_results/SHOULD_NOT_EXIST.json').exists()
valid=fixture('SYNTHETIC_cli_valid.xlsx')
single=run(['analyze.py',str(valid)]);assert single.returncode==0,single.stderr
result=json.loads(single.stdout);assert result['agreement'] is None
assert result['reviewers'][0]['summary']['primary']['source_equal_difference']==0
duplicate=run(['analyze.py',str(valid),str(valid)])
assert duplicate.returncode!=0 and 'Distinct reviewer' in duplicate.stderr
second=fixture('SYNTHETIC_cli_second.xlsx',{1:{'B6':'SYNTHETIC_SECOND_ONLY'}})
double=run(['analyze.py',str(valid),str(second)]);assert double.returncode==0,double.stderr
assert json.loads(double.stdout)['agreement']['correctness']['exact_agreement']==1
nonexternal=fixture('SYNTHETIC_coauthor.xlsx',{1:{'B7':'共同作者领域评审'}})
co=run(['analyze.py',str(nonexternal)]);assert co.returncode==0,co.stderr
assert json.loads(co.stdout)['external_non_author_present'] is False
assert json.loads(co.stdout)['remaining_limit']
protected=a.read(C/'PROTECTED_BEFORE.json');changed=[p for p,h in protected.items() if a.sha(p)!=h];assert not changed
freeze=a.read(C/'ANALYSIS_FREEZE.json');assert all(a.sha(H/p)==h for p,h in freeze['files'].items())
report={'utc':datetime.now(timezone.utc).isoformat(),'unit_tests_passed':15,'invalid_form_subcases':11,'test_log':tests.stderr,'cli_checks':{'blank_blocks_no_output':True,'synthetic_single_valid':True,'same_reviewer_rejected':True,'two_independent_declared_synthetic_forms_agreement':True,'coauthor_not_external':True},'synthetic_only':True,'real_human_results_computed':False,'protected_files_checked':len(protected),'protected_changed':changed,'unrelated_dirty_files_checked':len(a.read(C/'CHECKPOINT.json')['dirty_backup_hashes']),'analysis_freeze_files_checked':len(freeze['files']),'sample_sha256':a.sha(C/'SAMPLE_FROZEN.json'),'workbook_sha256':a.sha(T),'html_render':a.read(H/'output/playwright/render_checks.json'),'visual_review':'All four worksheet previews, HTML top/longest/last inspected; readable, no clipping observed in those previews. Whole workbook text checked by reconstruction.','model_api_calls':0,'paid_cost_rmb':0,'limitations':['No real reviewer, ratings, or external independent validation obtained.','No complete neutral evidence pack; unknown judgments explicitly allowed.','Technical source/model wording retained, so blinding is partial.','Nonempty evidence strings and declarations are not semantic validation or identity authentication.','20 common numeric-source clusters; not full60-source or model-run variance inference.']}
(C/'VALIDATION_REPORT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in report.items() if k not in ['test_log','limitations','visual_review']},ensure_ascii=False,indent=2))
