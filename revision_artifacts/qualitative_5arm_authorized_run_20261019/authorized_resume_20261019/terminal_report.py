"""Offline terminal aggregation and approved sampling; no API calls, no old writes."""
import csv,json,sys
from collections import Counter
from decimal import Decimal
from pathlib import Path
import transport as t
import resume
from sample_v5 import select
sys.path.insert(0,str(resume.WORK/'sampling_correction_v4_20261019'))
from sampler_v4 import anchor_quality
HERE=Path(__file__).resolve().parent
WORK=HERE.parent

def main():
    if (HERE/'review/RUNNING.lock').exists():raise ValueError('still_running')
    state=t.read(HERE/'review/state.json')
    if state['status']=='running':raise ValueError('state_still_running')
    resume.preflight()
    items=t.read(WORK/'QWEN_FROZEN_PLAN.json')['requests']
    packets={x['review_id']:x for x in t.read(WORK/'QWEN_BLIND_PACKETS.json')}
    keys={x['review_id']:x for x in t.read(WORK/'QWEN_BLIND_KEY_LOCAL_ONLY.json')}
    records={};attempts=[];response_ids=[];cost=Decimal(0);risk=Decimal(0);tokens=Counter();identities=set()
    for folder,plan in [(WORK/'review',items),(HERE/'review',items[77:])]:
        for i,path in enumerate(sorted(folder.glob('*_attempt.json'))):
            a=t.read(path);x=plan[i]
            assert a['slot']==x['review_id'] and a['body_sha256']==x['body_sha256'] and a['endpoint']==t.PROVIDERS['review']['endpoint']
            rp=path.with_name(path.name.replace('_attempt','_response'))
            r=t.read(rp) if rp.exists() else {'status':'unresolved'}
            attempts.append({'attempt_file':str(path.relative_to(WORK)),'review_id':x['review_id'],'status':r['status'],'started_at':a['started_at'],'finished_at':r.get('finished_at'),'provider_request_id':r.get('response',{}).get('id'),'http_status':r.get('http_status'),'error':r.get('error')})
            if r['status']!='completed':risk+=Decimal(a['reserved_CNY']);continue
            assert x['review_id'] not in records,'duplicate successful review'
            assert r['parsed']['review_id']==x['review_id']
            assert t.usage_cost(r['response'],t.PROVIDERS['review'])==Decimal(r['usage_cost_CNY'])
            cost+=Decimal(r['usage_cost_CNY']);response_ids.append(r['response']['id']);tokens.update({k:r['response']['usage'][k] for k in ['prompt_tokens','completion_tokens','total_tokens']});identities.add(json.dumps(r['identity'],sort_keys=True))
            evidence={e['evidence_id']:e['supplied_excerpt'] for e in packets[x['review_id']]['cited_evidence']}
            records[x['review_id']]={**keys[x['review_id']],'review_status':'completed','machine_judgment':r['parsed'],'anchor_quality':anchor_quality(r['parsed'],evidence),'response_file':str(rp.relative_to(WORK))}
    assert len(response_ids)==len(set(response_ids))
    all_records=[records.get(x['review_id'],{**keys[x['review_id']],'review_status':'no_successful_judgment','machine_judgment':None}) for x in items]
    previous=t.read(WORK/'FINAL_AUDIT.json')
    known=Decimal('0.563162')+Decimal(previous['phases']['generation']['usage_estimate_CNY'])+cost
    risk_total=Decimal('4.325376')+risk
    assert known+risk_total==Decimal(state['debit_CNY']) and known+risk_total<=50
    policy=t.read(HERE/'sampling_policy_v5.json');selection=[];strata=[];sample_block=None
    if len(records)==441:
        try:selection,strata=select(all_records,[x['review_id'] for x in items],policy)
        except ValueError as exc:sample_block=str(exc)
    else:sample_block='all441_not_completed'
    source_stats=[]
    sources=sorted({x['source_id'] for x in t.read(WORK/'SOURCE_LEVEL_COUNTS.json')})
    for sid in sources:
        for group in policy['groups']:
            rows=[r for r in all_records if r['source_id']==sid and r['group']==group];done=[r for r in rows if r['machine_judgment']]
            source_stats.append({'source_id':sid,'group':group,'Q_total':len(rows),'review_completed':len(done),'raw_support_counts':dict(Counter(r['machine_judgment'].get('support','missing') for r in done)),'raw_applicability_counts':dict(Counter(r['machine_judgment'].get('applicability','missing') for r in done))})
    index={(r['source_id'],r['group']):r for r in source_stats};paired=[]
    for sid in sources:
        a=index[sid,'semantic_new'];b=index[sid,'random_new']
        paired.append({'source_id':sid,'semantic_Q':a['Q_total'],'random_Q':b['Q_total'],'raw_label_count_difference_semantic_minus_random':{label:a['raw_support_counts'].get(label,0)-b['raw_support_counts'].get(label,0) for label in policy['labels']},'raw_label_rate_difference_semantic_minus_random':{label:(a['raw_support_counts'].get(label,0)/a['Q_total']-b['raw_support_counts'].get(label,0)/b['Q_total']) if a['Q_total'] and b['Q_total'] and a['review_completed']==a['Q_total'] and b['review_completed']==b['Q_total'] else None for label in policy['labels']},'limitation':'Different generated Q candidate sets; descriptive source pairing, no causal quality conclusion'})
    by_group={g:{'completed':sum(r['group']==g for r in records.values()),'raw_support':dict(Counter(r['machine_judgment'].get('support','missing') for r in records.values() if r['group']==g)),'raw_applicability':dict(Counter(r['machine_judgment'].get('applicability','missing') for r in records.values() if r['group']==g))} for g in policy['groups']}
    protected=t.read(WORK/'RUN_PREFLIGHT.json')
    report={'created_at':t.now(),'state':state,'generation_success_preserved':300,'unique_review_candidates':441,'unique_successful_reviews':len(records),'total_review_attempts_including_old_failure':len(attempts),'old_failure_preserved':True,'missing_successful_review_ids':[x['review_id'] for x in items if x['review_id'] not in records],'Qwen_usage_estimate_CNY':str(cost),'known_usage_estimate_including_history_CNY':str(known),'risk_reserve_including_history_CNY':str(risk_total),'cumulative_ledger_CNY':str(known+risk_total),'headroom_CNY':str(50-known-risk_total),'billing_verified':False,'Qwen_successful_tokens':dict(tokens),'Qwen_identities':[json.loads(i) for i in sorted(identities)],'group_raw_labels':by_group,'raw_support':dict(Counter(r['machine_judgment'].get('support','missing') for r in records.values())),'anchor_quality':dict(Counter(r['anchor_quality']['status'] for r in records.values())),'old_artifact_hashes_verified':827,'protected_files_verified':len(protected['protected_hashes']),'frozen_files_verified':len(protected['frozen_hashes']),'formal_sample_count':len(selection),'sample_block':sample_block,'human_judgments_completed':0,'sampling_policy':policy,'limitations':['Qwen judgments are not human truth; direct does not imply known applicability.','Anchor checks are lexical, not semantic proof.','One generation per source/group; no stochastic variability estimate.','Sampling revision after observing77; stratified30 audit cannot be reported as unweighted population accuracy.']}
    out=HERE/'terminal_results';out.mkdir(exist_ok=False)
    for name,value in [('FINAL_REPORT.json',report),('REVIEW_DIAGNOSTICS_441.json',all_records),('ALL_ATTEMPTS.json',attempts),('SOURCE_LEVEL_REVIEW_COUNTS.json',source_stats),('PAIRED_SOURCE_REVIEW_DIFFERENCES.json',paired),('SAMPLE_STRATA.json',strata),('MANUAL_SAMPLE_KEY_LOCAL_ONLY.json',selection),('GENERATION_PAIRED_SOURCE_DIFFERENCES.json',t.read(WORK/'PAIRED_SOURCE_DIFFERENCES.json'))]:t.exclusive(out/name,value)
    if selection:
        folder=out/'manual_sample';folder.mkdir()
        for r in selection:t.exclusive(folder/(r['review_id']+'.json'),packets[r['review_id']])
        with (folder/'BLANK_HUMAN_JUDGMENTS.csv').open('x',encoding='utf-8-sig',newline='') as stream:
            w=csv.DictWriter(stream,fieldnames=['review_id','human_support','human_applicability','human_faithfulness','human_verifiability','human_reason']);w.writeheader();w.writerows({'review_id':r['review_id']} for r in selection)
        (folder/'阅读说明.txt').write_text('这30条为五原标签×两臂分层抽查，非总体准确率估计。抽样规则在已见77条结果后补充。人工判定全部留空。单独packet隐藏生成组及Qwen标签；不要向盲审者提供本地key或strata文件。锚点与适用性独立，不改变支持标签。旧临时30条仍保留，不能与本目录混用。',encoding='utf8')
    lines=['Qwen续跑终态与五组补充实验结果','',f"生成300次成功保持不变。Qwen唯一候选441，成功{len(records)}，总尝试{len(attempts)}（含原Arrearage失败）。",'续跑状态：'+state['status'],f"累计估算账本¥{known+risk_total}，其中已知usage估价¥{known}、历史及失败风险预留¥{risk_total}；距离50元上限¥{50-known-risk_total}。不是核验后的账单。",'Qwen原始支持标签：'+json.dumps(report['raw_support'],ensure_ascii=False),'各组原标签：'+json.dumps(by_group,ensure_ascii=False),'锚点字面核验：'+json.dumps(report['anchor_quality'],ensure_ascii=False),f"正式抽样{len(selection)}条，人工判断0条；阻塞：{sample_block}。",'抽样规则：五原标签×两臂，每层初始3条，固定hash排序及轮转补足；每层总数、配额和名义抽样比例见SAMPLE_STRATA.json。规则补充发生在已见77条结果后，不伪称预注册。','旧827文件、保护文件及冻结输入哈希已核验不变。旧失败、旧临时材料、原日志全部保留。','Qwen跨模型标签不是人工真值；partial、insufficient、uncertain独立。direct不代表机型工况已知或工程适用性成立。','源配对统计已保存，不能把同源多个条目当独立样本，也不能将格式改善直接当作语义质量提升。','项目新结果目录：'+str(out)]
    (out/'续跑最终摘要.txt').write_text('\n'.join(lines)+'\n',encoding='utf8')
    # Existing secrets only inspected in memory; never printed or written.
    sys.path.insert(0,str(resume.ROOT))
    from cooling_rag_mg.config import QwenConfig,DeepSeekConfig
    secrets=[QwenConfig().api_key,DeepSeekConfig().api_key]
    leaked=[str(p.relative_to(HERE)) for p in HERE.rglob('*') if p.is_file() and any(s and s.encode() in p.read_bytes() for s in secrets)]
    if leaked:raise ValueError('credential_leak_do_not_deliver')
    t.exclusive(out/'INTEGRITY.json',{'secret_scan_leaks':0,'old_materials_unchanged':True,'output_hashes':{str(p.relative_to(out)):t.sha(p) for p in out.rglob('*') if p.is_file()}})
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
