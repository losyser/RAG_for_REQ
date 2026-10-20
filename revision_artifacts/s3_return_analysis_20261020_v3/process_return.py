"""Authenticated v3: exact technical cleanup, frozen validation, descriptive-only fallback."""
import sys,copy,csv,json,re,zipfile,subprocess
from pathlib import Path
from collections import Counter,defaultdict
H=Path(__file__).resolve().parent;ROOT=H.parents[1]
sys.path.insert(0,str(ROOT/'revision_artifacts/s3_return_technical_cleanup_20261020'))
import technical_cleanup as tc
sha=tc.sha;read=tc.read;dump=tc.dump
RAW=H/'raw/评审表修改版.xlsx';NORM=H/'normalized/评审表修改版_仅分隔格整理.xlsx'

def main():
    assert sha(RAW)==read(H/'ATTACHMENT.json')['sha256']
    before=tc.snapshot(RAW);previous=tc.snapshot(tc.RAW);differences=[]
    for sheet in before:
        for cell in sorted(set(before[sheet])|set(previous[sheet])):
            if before[sheet].get(cell)!=previous[sheet].get(cell):differences.append({'sheet':sheet,'cell':cell,'old':previous[sheet].get(cell),'new':before[sheet].get(cell)})
    assert len(differences)==12 and all(x['sheet']=='评分50' for x in differences)
    dump(H/'V2_TO_V3_DIFF.json',differences)
    targets=[x['cell'] for x in read(ROOT/'revision_artifacts/s3_return_technical_cleanup_20261020/NORMALIZATION_LOG.json')['cells']]
    template=tc.snapshot(tc.TEMPLATE)
    assert len(targets)==150
    for cell in targets:assert cell not in template['完整原文'] and str(before['完整原文'][cell][0])=='136'
    assert not NORM.exists();NORM.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(RAW) as a,zipfile.ZipFile(NORM,'w') as b:
        for info in a.infolist():
            payload=a.read(info.filename)
            if info.filename=='xl/worksheets/sheet4.xml':
                text=payload.decode('utf8')
                for cell in targets:
                    pattern=r'(<(?:\w+:)?c\b[^>]*\br="'+re.escape(cell)+r'"[^>]*>)(.*?)(</(?:\w+:)?c>)';matches=list(re.finditer(pattern,text,re.S));assert len(matches)==1
                    m=matches[0];text=text[:m.start()]+re.sub(r'\s+t="[^"]*"','',m[1])+m[3]+text[m.end():]
                payload=text.encode('utf8')
            b.writestr(info,payload)
    expected=copy.deepcopy(before)
    for cell in targets:del expected['完整原文'][cell]
    assert tc.snapshot(NORM)==expected
    with zipfile.ZipFile(RAW) as a,zipfile.ZipFile(NORM) as b:assert [n for n in a.namelist() if a.read(n)!=b.read(n)]==['xl/worksheets/sheet4.xml']
    dump(H/'NORMALIZATION_LOG.json',{'input_sha256':sha(RAW),'output_sha256':sha(NORM),'only_changed_zip_part':'xl/worksheets/sheet4.xml','all_other_cell_values_and_types_unchanged':True,'cells':[{'sheet':'完整原文','cell':cell,'before':'136','after':None} for cell in targets]})
    for label,path in [('raw',RAW),('normalized',NORM)]:
        run=subprocess.run([sys.executable,'-E','-B','-X','utf8',str(tc.F/'analyze.py'),str(path)],capture_output=True,text=True,encoding='utf8')
        (H/f'FROZEN_{label.upper()}_VALIDATION.json').write_text(run.stdout,encoding='utf8')
        assert run.returncode==2 and json.loads(run.stdout)['status']=='blocked'
    compat=tc.compatible_validate(NORM)
    dump(H/'COMPATIBLE_VALIDATION.json',{k:compat[k] for k in ['valid','issues','input_sha256']})
    assert not compat['valid'] # No official outcome path permitted while frozen validation blocks.
    sample=read(tc.C/'SAMPLE_FROZEN.json');key={x['blind_id']:x for x in sample};rows=[]
    wb=tc.ORIGINAL_LOADER(NORM,read_only=True,data_only=False);ws=wb['评分50']
    for i in range(6,56):
        code,c,a,basis,confidence,note=[ws.cell(i,j).value for j in range(1,7)]
        assert code in key and c in tc.frozen.CORRECTNESS and a in tc.frozen.APPLICABILITY and str(confidence) in ['1','2','3'] and basis
        rows.append({'blind_id':code,'source_id':key[code]['source_id'],'arm':key[code]['arm'],'correctness':c,'applicability':a,'basis':basis,'confidence':confidence,'note':note,'input_row':i})
    wb.close();assert len({r['blind_id'] for r in rows})==50
    d=H/'交付_最新返表描述性核验';d.mkdir();coord=d/'协调者逐条数据_勿发评审';coord.mkdir()
    with (coord/'submitted_labels_with_frozen_mapping.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    descriptions={};per_source=[]
    for arm in ['rag','norag']:
        rs=[r for r in rows if r['arm']==arm]
        descriptions[arm]={'n':len(rs),'source_count':len({r['source_id'] for r in rs}),'correctness_counts':dict(Counter(r['correctness'] for r in rs)),'applicability_counts':dict(Counter(r['applicability'] for r in rs)),'joint_label_counts':[{'correctness':c,'applicability':a,'count':sum(r['correctness']==c and r['applicability']==a for r in rs)} for c in tc.frozen.CORRECTNESS for a in tc.frozen.APPLICABILITY]}
    for source in sorted({r['source_id'] for r in rows}):
        item={'source_id':source}
        for arm in ['rag','norag']:
            rs=[r for r in rows if r['source_id']==source and r['arm']==arm];assert rs
            item[arm]={'denominator':len(rs),'blind_ids':[r['blind_id'] for r in rs],'correctness_counts':dict(Counter(r['correctness'] for r in rs)),'applicability_counts':dict(Counter(r['applicability'] for r in rs))}
        per_source.append(item)
    assert len(per_source)==20 and all(v['n']==25 for v in descriptions.values())
    result={'status':'read_only_descriptive_labels_only_frozen_validation_blocked','attachment_sha256':sha(RAW),'reviewers':1,'sample_items':50,'paired_source_count':20,'arms':descriptions,'per_source_denominators_and_labels':per_source,'formal_primary':None,'formal_secondary':None,'unknown_sensitivity_bounds':None,'source_cluster_interval':None,'sign_test':None,'agreement':None,'not_computed_reason':'Unchanged frozen validator and strict technical compatibility wrapper reject missing/invalid process declarations. No bypass or outcomes from incomplete forms.','interpretation':'Counts are submitted labels, not verified correctness, official frozen outcomes or evidence of RAG advantage. No source excluded.'}
    dump(d/'DESCRIPTIVE_RESULT.json',result)
    dump(H/'ALL_SUBMITTED_LABELS.json',rows)
    dump(H/'PROTECTION_CHECK.json',{'protected_files':len(read(H/'PROTECTED_BEFORE.json')),'changed':[p for p,h in read(H/'PROTECTED_BEFORE.json').items() if sha(Path(p))!=h]})
    assert not read(H/'PROTECTION_CHECK.json')['changed']
    print(json.dumps({'arms':descriptions,'validation_issues':compat['issues'],'formal_outcomes':'not computed'},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
