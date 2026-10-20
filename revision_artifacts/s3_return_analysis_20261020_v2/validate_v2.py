"""Read-only comparison of authenticated return versions; frozen validator unchanged."""
import json,hashlib,subprocess,sys,shutil
from pathlib import Path
from collections import Counter
import openpyxl
H=Path(__file__).resolve().parent;ROOT=H.parents[1];OLD=ROOT/'revision_artifacts/s3_return_analysis_20261020';F=ROOT/'revision_artifacts/s3_paired_review50_20261019';C=F/'02_协调者_勿发评审'
read=lambda p:json.loads(p.read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf8')
def main():
    raw=H/'raw/评分表.xlsx';prev=OLD/'raw/数值候选独立评分.xlsx'
    assert sha(raw)=='f5f14e175f255495c2187b00311a0348bc4a977e8b5532308cf10f3fa9b5773b' and raw.stat().st_size==35023
    assert sha(prev)=='87f3153b7ddb329efd528a45621135a812298c0ca812d42eb59caae6a03a173f'
    protected={p:sha(Path(p)) for p in read(OLD/'PROTECTED_AT_RETURN_START.json')}
    protected.update({str(p):sha(p) for p in OLD.rglob('*') if p.is_file()})
    if not (H/'PROTECTED_BEFORE.json').exists():dump(H/'PROTECTED_BEFORE.json',protected)
    else:protected=read(H/'PROTECTED_BEFORE.json')
    freeze=read(C/'ANALYSIS_FREEZE.json');assert all(sha(F/n)==h for n,h in freeze['files'].items())
    a=openpyxl.load_workbook(prev,read_only=True);b=openpyxl.load_workbook(raw,read_only=True);changes=[];identity=[];counts=Counter()
    for s in b.sheetnames:
        for row in b[s].iter_rows():
            for cell in row:
                old=a[s].cell(cell.row,cell.column).value
                if old!=cell.value:
                    entry={'sheet':s,'cell':cell.coordinate,'old':old,'new':cell.value}
                    if s=='身份与说明':identity.append(cell.coordinate)
                    else:changes.append(entry)
    rating=[x for x in changes if x['sheet']=='评分50'];fixed=[x for x in changes if x['sheet']!='评分50']
    assert len(fixed)==150 and all(x['sheet']=='完整原文' and x['old'] in (None,'') and str(x['new'])=='136' for x in fixed)
    ws=b['评分50'];labels=Counter();positives=[];errors=[]
    for i in range(6,56):
        code,c,app,basis,confidence,note=[ws.cell(i,j).value for j in range(1,7)];labels[c]+=1
        for name,value in [('correctness',c),('applicability',app),('basis',basis),('confidence',confidence),('note',note)]:counts[name]+=value not in (None,'')
        if c in ['正确','可接受']:positives.append({'blind_id':code,'row':i,'basis':basis,'note':note})
        if c=='错误':errors.append({'blind_id':code,'basis_filled':bool(basis),'note_filled':bool(note)})
    ids=[ws.cell(i,1).value for i in range(6,56)];assert len(set(ids))==50 and set(ids)=={x['blind_id'] for x in read(C/'SAMPLE_FROZEN.json')}
    a.close();b.close()
    r=subprocess.run([sys.executable,'-E','-B','-X','utf8',str(F/'analyze.py'),str(raw)],capture_output=True,text=True,encoding='utf8');(H/'FROZEN_VALIDATION.json').write_text(r.stdout,encoding='utf8')
    response=json.loads(r.stdout);assert r.returncode==2 and response['status']=='blocked'
    dump(H/'CELL_DIFF.json',changes)
    dump(H/'COMPARISON.json',{'attachment_sha256':sha(raw),'attachment_bytes':35023,'file_id':'file_00000000d56c820ea672a2a23593b72b','library_file_id':'libfile_be985033d2d08191a3dc31d750d0e342','previous_sha256':sha(prev),'rating_changed_cells':len(rating),'identity_changed_cells':identity,'separator_changed_cells':len(fixed),'separator_change':'150 formerly empty A/B/C separator cells now literal 136; no cleaning performed','ids_match':True,'correctness_labels_changed':sum(x['cell'].startswith('B') for x in rating),'submitted_correctness_counts':dict(labels),'filled_counts':dict(counts),'positive_basis_nonempty':len(positives),'positive_basis_verified':False,'error_basis_completeness':errors,'formal_statistics':'blocked, not computed','reviewer_identity_author_relationship_ai_assistance':'unconfirmed','frozen_validator_exit_code':r.returncode})
    dump(H/'POSITIVE_BASIS_SUBMITTED.json',positives)
    assert all(sha(Path(p))==h for p,h in protected.items())
    dump(H/'PROTECTION_CHECK.json',{'protected_count':len(protected),'changed':[],'v1_and_v2_raw_unchanged':True,'normalization_copy_created':False,'frozen_script_changed':False})
    print(json.dumps({'rating_changes':len(rating),'separator_changes':len(fixed),'identity_changes':identity,'filled':dict(counts),'validator_issues':response['validation'][0]['issues']},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
