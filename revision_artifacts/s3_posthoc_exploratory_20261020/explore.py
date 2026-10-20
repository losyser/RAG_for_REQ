"""Explicitly authorized post-hoc revised-rating analysis; never claims frozen process acceptance."""
import sys,json,csv
from pathlib import Path
from collections import Counter
H=Path(__file__).resolve().parent;ROOT=H.parents[1]
sys.path.insert(0,str(ROOT/'revision_artifacts/s3_return_technical_cleanup_20261020'))
import technical_cleanup as tc
read=tc.read;dump=tc.dump;sha=tc.sha
WARNING_ONLY=frozenset([
 '身份/过程字段未填:expertise','身份/过程字段未填:prior_exposure',
 '身份/过程字段未填:record_stage','身份/过程字段未填:start_time','身份/过程字段未填:end_time',
 '身份选项无效','仅分析明确声明独立完成的首判；合议或不独立表不得算独立一致性',
 'start_time:请写含时区ISO时间，例如2026-10-20T09:00:00+08:00（例子不是填写值）',
 'end_time:请写含时区ISO时间，例如2026-10-20T09:00:00+08:00（例子不是填写值）'])

def accept_for_exploration(path):
    check=tc.compatible_validate(path)
    blockers=[x for x in check['issues'] if x not in WARNING_ONLY]
    if blockers:raise ValueError('Score/content validation rejected: '+json.dumps(blockers,ensure_ascii=False))
    sample=read(tc.C/'SAMPLE_FROZEN.json');key={x['blind_id']:x for x in sample}
    wb=tc.ORIGINAL_LOADER(path,read_only=True,data_only=False);rows=[]
    identity=wb['身份与说明']
    if identity['B11'].value not in ('独立完成','是',None,'') or identity['B12'].value not in (None,'','独立首判','修订版'):
        wb.close();raise ValueError('Explicit process declaration conflicts with authorized single-reviewer route')
    if identity['B7'].value not in ('专业硕士研究生','外部非作者领域评审'):
        wb.close();raise ValueError('Reviewer role conflicts with the recorded non-author supplement')
    for i in range(6,56):
        code,c,a,basis,confidence,note=[wb['评分50'].cell(i,j).value for j in range(1,7)]
        rows.append({'blind_id':code,'source_id':key[code]['source_id'],'arm':key[code]['arm'],'correctness':c,'applicability':a,'basis':basis,'confidence':confidence,'note':note})
    wb.close()
    assert len(rows)==50 and len({r['blind_id'] for r in rows})==50
    pairs=Counter((r['source_id'],r['arm']) for r in rows);assert len(pairs)==40 and len({s for s,a in pairs})==20
    return {'score_data_complete':True,'mode':'posthoc_revised_single_reviewer_exploration','claims_frozen_process_acceptance':False,'original_frozen_process_valid':check['valid'],'process_record_complete':not check['issues'],'warnings':check['issues'],'input_sha256':sha(path),'ratings':rows}

def main(output=None):
    policy=read(H/'POSTHOC_AMENDMENT.json');assert policy['declaration_message_id']=='Sentinel_f71f1474bbf08191b6c43c6ecf23786c'
    original=H/'input_archive/v3_original.xlsx';normalized=H/'input_archive/v3_normalized.xlsx'
    manifest=read(H/'ARCHIVE_MANIFEST.json');assert all(sha(H/'input_archive'/n)==v for n,v in manifest.items())
    assert sha(original)=='835122bb35475ac10111330a3cc23c5de72d5f979f274595e96279acdcf50d60'
    accepted=accept_for_exploration(normalized);assert not accepted['original_frozen_process_valid']
    # These are the original frozen functions, source hash-checked by compatible_validate.
    summary=tc.frozen.summarize(accepted['ratings'])
    result={'title':'基于修订评分的探索性分析；评分数据完整，过程记录不完整','status':'posthoc_exploratory_only','original_frozen_acceptance':'failed_process_completeness_retained','amendment':policy,'validation':{k:v for k,v in accepted.items() if k!='ratings'},'original_attachment_sha256':sha(original),'normalized_sha256':sha(normalized),'frozen_analyzer_sha256':sha(tc.F/'analyze.py'),'sample_mapping_sha256':sha(tc.C/'SAMPLE_FROZEN.json'),'reviewer_count':1,'review_stage':'revised_ratings_not_initial_first_pass','agreement':None,'raw_ratings':accepted['ratings'],'summary':summary,'limitations':['Only one reviewer; no inter-rater agreement calculated.','User-declared non-author graduate student; personally read material and made final judgments; AI only searched literature without rating advice.','Detailed experience, prior exposure, and start/end times unrecorded; blinding not independently established.','Some bases are KB excerpts or secondary reproductions, especially K299956; not all original-source verification completed.','Post-hoc process acceptance differs from frozen eligibility; no confirmatory claim.','Many unknown outcomes; neither treating unknown as factual error nor significance alone establishes RAG correctness.']}
    out=(output or H/'delivery').resolve()
    if not out.is_relative_to(H) or out.exists():raise ValueError('Output must be a new directory inside this analysis artifact; no overwrite')
    out.mkdir(parents=True,exist_ok=False);dump(out/'EXPLORATORY_RESULT.json',result)
    with (out/'逐条评分及计算状态_含解盲信息.csv').open('w',encoding='utf-8-sig',newline='') as f:
        enriched=[]
        for r in accepted['ratings']:
            p,u=tc.frozen.status(r);s,v=tc.frozen.status(r,True)
            enriched.append({**r,'primary_confirmed':p,'primary_unresolved_possible':u,'secondary_confirmed':s,'secondary_unresolved_possible':v})
        writer=csv.DictWriter(f,fieldnames=list(enriched[0]));writer.writeheader();writer.writerows(enriched)
    with (out/'20源配对分母与效应.csv').open('w',encoding='utf-8-sig',newline='') as f:
        paired=[]
        for p,s in zip(summary['primary']['per_source'],summary['secondary']['per_source']):
            assert p['source_id']==s['source_id']
            paired.append({'source_id':p['source_id'],'rag_n':p['rag']['n'],'norag_n':p['norag']['n'],'primary_rag_rate':p['rag']['confirmed_success'],'primary_norag_rate':p['norag']['confirmed_success'],'primary_difference_exact':p['difference_exact'],'primary_unfavorable':p['unfavorable_bound'],'primary_favorable':p['favorable_bound'],'secondary_rag_rate':s['rag']['confirmed_success'],'secondary_norag_rate':s['norag']['confirmed_success'],'secondary_difference_exact':s['difference_exact'],'secondary_unfavorable':s['unfavorable_bound'],'secondary_favorable':s['favorable_bound']})
        writer=csv.DictWriter(f,fieldnames=list(paired[0]));writer.writeheader();writer.writerows(paired)
    compact={name:{k:v for k,v in summary[name].items() if k!='per_source'} for name in ['primary','secondary']}
    print(json.dumps(compact,ensure_ascii=False,indent=2))
if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path);args=parser.parse_args();main(args.out)
