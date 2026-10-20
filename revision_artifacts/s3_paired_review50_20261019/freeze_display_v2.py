"""Record authorized display correction as v2; keep original freeze in archived v1."""
from datetime import datetime,timezone
import shutil,json
import analyze as a
H=a.HERE;C=a.COORD;E=H/'outputs/01a13537-s3/01_仅此目录可发评审'
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
old=a.read(C/'ANALYSIS_FREEZE.json');assert old['version']=='S3-analysis-v1'
p=H/'verify.py';s=p.read_text(encoding='utf8');assert s.count("'unit_tests_passed':14")==1;p.write_text(s.replace("'unit_tests_passed':14","'unit_tests_passed':15"),encoding='utf8')
inspection=E/'数值候选独立评分.xlsx.inspect.ndjson'
shutil.copy2(inspection,C/'artifact_export.inspect.ndjson');inspection.unlink()
dump(C/'WORKBOOK_CONTRACT.json',a.contract(E/'数值候选独立评分.xlsx'))
names=set(old['files'])|{'correct_display.py','freeze_display_v2.py','verify.py','02_协调者_勿发评审/DISPLAY_CORRECTION.json','02_协调者_勿发评审/pre_display_correction_v1/ARCHIVE_HASHES.json'}
dump(C/'ANALYSIS_FREEZE.json',{'version':'S3-analysis-v1-display-v2','frozen_before_ratings_utc':datetime.now(timezone.utc).isoformat(),'real_ratings_present':False,'statistics_protocol_unchanged':True,'original_freeze_archive':'02_协调者_勿发评审/pre_display_correction_v1/02_协调者_勿发评审/ANALYSIS_FREEZE.json','files':{n:a.sha(H/n) for n in sorted(names)}})
print('Display-v2 hashes frozen; original sample and statistical protocol preserved.')
