"""Offline derivations only: blind review packets, source-paired summaries, blank human sample."""
from collections import Counter,defaultdict
import csv,copy,hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];WORK=Path(__file__).resolve().parent;V2=WORK.parent/'qualitative_5arm_v2_preflight_20261019'
sys.path.insert(0,str(V2));from classifier_v2 import classify
sys.path.insert(0,str(WORK));from runner import digest,atomic,read,sha

def evidence_segments(context):
    block=context['evidence_block'];parts=re.split(r'(?m)^\[([^\]\n]+)\] ',block);out={}
    for i in range(1,len(parts),2):out[parts[i]]=f'[{parts[i]}] '+parts[i+1].rstrip()
    assert set(out)==set(context['selected_ids'])
    return out
def blind_packet(item,row,row_index,context,source):
    review_id=hashlib.sha256(f"q-review-v2-20261019|{item['slot']}|{row_index}".encode()).hexdigest()
    selected=evidence_segments(context) if context else {};mapping={};evidence=[];checks=[]
    cites=row.get('evidence_citations');cites=cites if isinstance(cites,list) else []
    candidate={k:copy.deepcopy(row[k]) for k in ['shall_statement','measurable_criterion','applicable_condition','verification_method','acceptance_criteria'] if k in row}
    candidate['evidence_citations']=[]
    for ci,c in enumerate(cites):
        eid=c.get('kb_id') if isinstance(c,dict) else None
        token=str(eid) if isinstance(eid,str) else f'invalid-position-{ci}'
        if token not in mapping:mapping[token]=f'E{len(mapping)+1:03d}'
        anon=mapping[token];exists=eid in selected if isinstance(eid,str) else False
        if exists and not any(e['evidence_id']==anon for e in evidence):
            text=selected[eid]
            # Only actual supplied excerpt, never expand from the full KB.
            for old,new in mapping.items():text=text.replace('['+old+']','['+new+']')
            evidence.append({'evidence_id':anon,'supplied_excerpt':text,'excerpt_limit_characters':500,'outside_excerpt_conditions':'not_inspected'})
        newcite={k:v for k,v in c.items() if k in ['tier','source','has_clause']} if isinstance(c,dict) else {}
        newcite['kb_id']=anon;candidate['evidence_citations'].append(newcite)
        checks.append({'evidence_id':anon,'in_supplied_context':exists,'citation_schema_valid':isinstance(c,dict) and isinstance(eid,str)})
    # Mask evidence identifiers also if echoed in criterion text; no group/model/OR metadata is included.
    candidate_json=json.dumps(candidate,ensure_ascii=False)
    for old,new in mapping.items():candidate_json=candidate_json.replace(old,new)
    candidate=json.loads(candidate_json)
    packet={'review_id':review_id,'source_requirement':source,'candidate':candidate,'cited_evidence':evidence,'citation_checks':checks,'context_was_empty':not bool(selected),'evidence_policy':'Generation used first500 characters per selected unit; no outside text verified.'}
    key={'review_id':review_id,'slot':item['slot'],'source_id':item['source_id'],'group':item['group'],'row_index':row_index,'evidence_id_map':mapping}
    return packet,key

def load_rows():
    requests=read(V2/'REQUESTS_300_PENDING.json');contexts=read(V2/'CONTEXTS_120.json');cmap={(c['arm'],c['source_id']):c for c in contexts};sources=read(V2/'SOURCE_REQUIREMENTS_60.json')
    manifest=read(V2/'INPUT_MANIFEST.json');kbpath=Path(manifest['KB']['path']);assert sha(kbpath)==manifest['KB']['sha256'];kbids={json.loads(line)['id'] for line in kbpath.read_text(encoding='utf8').splitlines()}
    records=[];source_stats=[];completed=[]
    for idx,item in enumerate(requests,1):
        path=WORK/'generation'/f'{idx:04d}_response.json'
        if not path.exists():continue
        response=read(path)
        if response['status']!='completed':continue
        completed.append(item['slot']);rows=response['parsed']['shalls'];context=None if item['group']=='norag_original' else cmap[item['group'].split('_')[0],item['source_id']]
        selected=set(context['selected_ids']) if context else set();counts=Counter()
        for ri,row in enumerate(rows,1):
            diagnostic=classify(row,kbids,selected,evidence_required=item['group']!='norag_original');counts[diagnostic['class']]+=1
            if diagnostic['q_format']=='pass':counts['q_format_pass']+=1
            records.append({'item':item,'row_index':ri,'row':row,'diagnostic':diagnostic,'context':context,'source':sources[item['source_id']]})
        source_stats.append({'source_id':item['source_id'],'group':item['group'],'n_rows':len(rows),**dict(counts)})
    return records,source_stats,completed

def build_review():
    target=WORK/'QWEN_FROZEN_PLAN.json'
    if target.exists():raise RuntimeError('Preserve existing frozen review plan')
    records,stats,completed=load_rows();prompt=(V2/'QWEN_BLIND_REVIEW_PROMPT.txt').read_text(encoding='utf8');requests=[];keys=[];packets=[]
    for record in records:
        if record['diagnostic']['class']!='q_candidate':continue
        packet,key=blind_packet(record['item'],record['row'],record['row_index'],record['context'],record['source']);packets.append(packet);keys.append(key)
        body={'model':'qwen-max','messages':[{'role':'system','content':prompt},{'role':'user','content':json.dumps(packet,ensure_ascii=False)}],'temperature':0,'max_tokens':2048,'response_format':{'type':'json_object'}}
        requests.append({'slot':packet['review_id'],'review_id':packet['review_id'],'body':body,'body_sha256':digest(body),'message_utf8_bytes':sum(len(m['content'].encode()) for m in body['messages'])})
    requests.sort(key=lambda r:r['review_id']);keys.sort(key=lambda r:r['review_id']);packets.sort(key=lambda r:r['review_id'])
    assert len({r['review_id'] for r in requests})==len(requests)
    gs=read(WORK/'generation/state.json')
    plan={'status':'ready' if gs['status']=='completed' and len(requests)<=1200 else 'blocked','generation_status':gs['status'],'generation_completed_slots':len(completed),'total_Q_candidates':len(requests),'review_cap':1200,'requests_sha256':digest(requests),'prompt_sha256':sha(V2/'QWEN_BLIND_REVIEW_PROMPT.txt'),'requests':requests,'coverage_note':'All literal [Q] candidates, including format failures; no candidate selected by expected quality. Oversize or excess count pauses, never silently truncates all-Q scope.','token_note':'No verified tokenizer; provider enforces30720 input limit; max-cost reserve uses full provider input ceiling, not byte estimate.'}
    atomic(target,plan);atomic(WORK/'QWEN_BLIND_KEY_LOCAL_ONLY.json',keys);atomic(WORK/'QWEN_BLIND_PACKETS.json',packets)
    print(json.dumps({'review_plan_status':plan['status'],'Q_candidates':len(requests),'completed_generation_slots':len(completed)}))

def judge_band(result,anchor_valid):
    if not result or not anchor_valid:return 'other_uncertain_error'
    if result.get('support')=='contradicted' or result.get('applicability')=='explicit_mismatch' or result.get('faithfulness')=='new_inference_or_synthesis' or result.get('verifiability')=='not_verifiable':return 'explicit_negative'
    if result.get('support')=='direct' and result.get('applicability') in ['explicit_match','general_rule_with_basis'] and result.get('verifiability')=='verifiable' and result.get('faithfulness') in ['quote','faithful_paraphrase']:return 'direct_and_applicable'
    return 'other_uncertain_error'

def summarize():
    records,stats,completed=load_rows();atomic(WORK/'ROW_DIAGNOSTICS.json',[{'slot':r['item']['slot'],'source_id':r['item']['source_id'],'group':r['item']['group'],'row_index':r['row_index'],'diagnostic':r['diagnostic'],'row':r['row']} for r in records]);atomic(WORK/'SOURCE_LEVEL_COUNTS.json',stats)
    groups=['semantic_old','semantic_new','random_old','random_new','norag_original'];group_stats={}
    for g in groups:
        rows=[s for s in stats if s['group']==g];keys=set().union(*(r.keys() for r in rows)) if rows else set()
        group_stats[g]={'planned_sources':60,'completed_sources':len(rows),**{k:sum(r.get(k,0) for r in rows) for k in keys-{'source_id','group'}}}
    index={(r['source_id'],r['group']):r for r in stats};paired=[]
    for sid in sorted({s['source_id'] for s in stats}):
        for arm in ['semantic','random']:
            old=index.get((sid,arm+'_old'));new=index.get((sid,arm+'_new'))
            if old is not None and new is not None:
                paired.append({'source_id':sid,'arm':arm,'old_rows':old['n_rows'],'new_rows':new['n_rows'],'Q_count_difference_new_minus_old':new.get('q_candidate',0)-old.get('q_candidate',0),'format_pass_difference_new_minus_old':new.get('q_format_pass',0)-old.get('q_format_pass',0),'TBD_candidate_difference_new_minus_old':new.get('tbd_or_mixed_candidate',0)-old.get('tbd_or_mixed_candidate',0),'semantic_effect_not_inferred':True})
    atomic(WORK/'PAIRED_SOURCE_DIFFERENCES.json',paired)
    review_results=[];sample=[]
    if (WORK/'QWEN_FROZEN_PLAN.json').exists():
        plan=read(WORK/'QWEN_FROZEN_PLAN.json');keys={k['review_id']:k for k in read(WORK/'QWEN_BLIND_KEY_LOCAL_ONLY.json')};packets={p['review_id']:p for p in read(WORK/'QWEN_BLIND_PACKETS.json')}
        for idx,item in enumerate(plan['requests'],1):
            rid=item['review_id'];p=WORK/'review'/f'{idx:04d}_response.json';response=read(p) if p.exists() else None;result=response.get('parsed') if response and response['status']=='completed' else None
            evidence={e['evidence_id']:e['supplied_excerpt'] for e in packets[rid]['cited_evidence']};anchors=result.get('anchors',[]) if result else []
            valid=bool(result) and isinstance(anchors,list) and all(isinstance(a,dict) and a.get('exact_quote') and a.get('evidence_id') in evidence and a['exact_quote'] in evidence[a['evidence_id']] for a in anchors)
            if result and result.get('support')=='direct' and not anchors:valid=False
            enums={'support':{'direct','partial','contradicted','insufficient','uncertain'},'applicability':{'explicit_match','explicit_mismatch','unknown','general_rule_with_basis'},'faithfulness':{'quote','faithful_paraphrase','new_inference_or_synthesis','unsupported','uncertain'},'verifiability':{'verifiable','not_verifiable','uncertain'}}
            valid=valid and all(result.get(k) in choices for k,choices in enums.items())
            record={**keys[rid],'review_status':response.get('status') if response else 'not_sent','machine_judgment':result,'anchor_and_enum_checks_pass':valid,'band':judge_band(result,valid)};review_results.append(record)
        strata=defaultdict(list)
        for r in review_results:
            order=hashlib.sha256(f"manual-q-v2-20261019|{r['slot']}|{r['row_index']}".encode()).hexdigest();strata[(r['group'],r['band'])].append((order,r))
        for pool in strata.values():pool.sort(key=lambda pair:pair[0])
        bands=['direct_and_applicable','explicit_negative','other_uncertain_error'];ordered=[(g,b) for g in groups for b in bands];target=min(30,len(review_results))
        # Round robin two initial passes gives two per nonempty stratum; further passes redistribute deficits.
        while len(sample)<target:
            progress=False
            for key in ordered:
                if strata[key] and len(sample)<target:sample.append(strata[key].pop(0)[1]);progress=True
            if not progress:break
        material=WORK/'manual_sample';material.mkdir(exist_ok=True)
        for r in sample:atomic(material/(r['review_id']+'.json'),packets[r['review_id']])
        with (material/'BLANK_HUMAN_JUDGMENTS.csv').open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=['review_id','human_support','human_applicability','human_faithfulness','human_verifiability','human_reason']);w.writeheader();w.writerows({'review_id':r['review_id']} for r in sample)
        atomic(WORK/'MANUAL_SAMPLE_KEY_LOCAL_ONLY.json',sample)
    atomic(WORK/'REVIEW_DIAGNOSTICS.json',review_results)
    summary={'generation_state':read(WORK/'generation/state.json'),'groups':group_stats,'paired_source_comparisons':len(paired),'Q_candidates_total':sum(g.get('q_candidate',0) for g in group_stats.values()),'reviewed_completed':sum(r['review_status']=='completed' for r in review_results),'review_bands':dict(Counter(r['band'] for r in review_results)),'manual_sample_prepared':len(sample),'human_judgments_completed':0,'quality_boundary':'Format and machine labels are not semantic/engineering truth. One trial does not estimate stochastic variation. Source-paired exploratory summaries, no main experiment changes.'}
    atomic(WORK/'RESULT_SUMMARY.json',summary);print(json.dumps(summary,ensure_ascii=False))

if __name__=='__main__':
    if '--build-review' in sys.argv:build_review()
    if '--summarize' in sys.argv:summarize()
