"""Authorized pre-release display-only removal; never mutate sampled originals."""
import json,re
from datetime import datetime,timezone
import analyze as a
H=a.HERE;C=a.COORD;E=H/'outputs/01a13537-s3/01_仅此目录可发评审'
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
report=C/'DISPLAY_CORRECTION.json'
if report.exists():raise SystemExit('Already corrected; refusing repeat')
original='温度监测参数可追溯至S30 MAN Energy Solutions 49/60 Project Guide'
replacement='温度监测参数可追溯至 MAN Energy Solutions 49/60 Project Guide'
b=a.read(H/'blind_input.json');hits=[]
for r in b:
    for field,value in r.items():
        for token in re.findall(r'(?<![A-Za-z0-9])S[0-9]{1,3}(?![A-Za-z0-9])',str(value)):
            hits.append({'blind_id':r['blind_id'],'field':field,'token':token,'decision':'remove pure internal source identifier' if token=='S30' else 'retain technical EMS/S6 controller designation'})
assert sum(x['token']=='S30' for x in hits)==1
assert all(x['token'] in ['S30','S6'] for x in hits)
target=next(r for r in b if r['blind_id']=='K849074');assert target['acceptance_criteria'][4]==original
target['acceptance_criteria'][4]=replacement;dump(H/'blind_input.json',b)
html=E/'50条原文只读阅读.html';text=html.read_text(encoding='utf8');assert text.count(original)==1;html.write_text(text.replace(original,replacement),encoding='utf8')
diffs=a.read(C/'DISPLAY_DIFFS.json');r=next(r for r in diffs if r['blind_id']=='K849074')
r['display']['acceptance_criteria'][4]=replacement;r['technical_fields_exact']=False
r['technical_meaning_preserved']=True
r['text_rewrites']=[{'field':'acceptance_criteria','index_0based':4,'before':original,'after':replacement,'reason':'Pre-release display anonymization: remove pure internal source ID S30; retain traceability requirement, maker, model and guide title.'}]
dump(C/'DISPLAY_DIFFS.json',diffs)
dump(report,{'utc':datetime.now(timezone.utc).isoformat(),'authorization':'Parent delegated P2 correction before sending; no Library upload','version':'display-v2','sample_and_protocol_unchanged':True,'sample_sha256':a.sha(C/'SAMPLE_FROZEN.json'),'protocol_sha256':a.sha(C/'PROTOCOL_FROZEN.json'),'removed_internal_token_count':1,'changed_cards':1,'unchanged_cards':49,'technical_designation_S6_retained':True,'token_review':hits,'change':r['text_rewrites'][0],'original_archive':'02_协调者_勿发评审/pre_display_correction_v1','original_snapshot_hashes':'02_协调者_勿发评审/pre_display_correction_v1/ARCHIVE_HASHES.json'})
print('Removed one pure source identifier S30; all technical S6 designations retained.')
