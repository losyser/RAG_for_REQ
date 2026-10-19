"""Offline, fail-closed sampler. No filesystem writer, API client or production imports."""
from collections import defaultdict, Counter
from copy import deepcopy
import hashlib

class NotReady(ValueError):
    pass

def anchor_quality(judgment, evidence):
    """Lexical anchor diagnostics only; never changes the model's support label."""
    anchors=judgment.get('anchors')
    if not isinstance(anchors,list) or not anchors:
        return {'status':'unavailable','checked_anchors':0,'mismatches':[]}
    errors=[]
    for index,a in enumerate(anchors):
        if not isinstance(a,dict):errors.append({'index':index,'reason':'invalid_anchor_shape'});continue
        eid=a.get('evidence_id');quote=a.get('exact_quote')
        if not isinstance(eid,str) or eid not in evidence:errors.append({'index':index,'reason':'unknown_evidence_id'})
        elif not isinstance(quote,str) or not quote or quote not in evidence[eid]:errors.append({'index':index,'reason':'quote_not_exact_substring'})
    return {'status':'fail' if errors else 'pass','checked_anchors':len(anchors),'mismatches':errors}

def original_composite_stratum(record):
    """Replay PLAN.md line49 raw-field precedence for diagnostics, not v4 selection."""
    j=record.get('machine_judgment')
    if not j:return 'other_uncertain_error'
    if j.get('support')=='contradicted' or j.get('applicability')=='explicit_mismatch' or j.get('faithfulness')=='new_inference_or_synthesis' or j.get('verifiability')=='not_verifiable':return 'explicit_negative'
    if j.get('support')=='direct' and j.get('applicability') in ['explicit_match','general_rule_with_basis']:return 'direct_and_applicable'
    return 'other_uncertain_error'

def readiness(records, frozen_ids, policy):
    reasons=[];expected=list(frozen_ids);ids=[r.get('review_id') for r in records]
    if policy.get('required_review_population')!=441:reasons.append('policy_population_must_be_441')
    if policy.get('group_order')!=['semantic_old','semantic_new','random_old','random_new','norag_original']:reasons.append('group_order_changed')
    if policy.get('stratum_order')!=['support','not_supported','uncertain']:reasons.append('stratum_order_changed')
    if len(expected)!=441 or len(set(expected))!=441:reasons.append('frozen_population_must_be_441_unique_ids')
    if len(ids)!=len(set(ids)):reasons.append('duplicate_review_ids')
    if set(ids)!=set(expected):reasons.append('review_population_mismatch')
    incomplete=[r.get('review_id') for r in records if r.get('review_status')!='completed' or not isinstance(r.get('machine_judgment'),dict)]
    if incomplete:reasons.append('all_441_reviews_must_be_completed')
    if any(r.get('machine_judgment',{}).get('review_id')!=r.get('review_id') for r in records if isinstance(r.get('machine_judgment'),dict)):reasons.append('judgment_id_mismatch')
    if not policy.get('finalized'):reasons.append('policy_not_finalized')
    mapping=policy.get('raw_support_to_stratum',{});strata=policy.get('stratum_order',[])
    unresolved=sorted(k for k,v in mapping.items() if v is None)
    if unresolved:reasons.append('unresolved_label_mapping')
    if policy.get('quality_flags_affect_stratum') or policy.get('applicability_affects_stratum'):reasons.append('quality_or_applicability_must_not_redefine_support')
    if any(v is not None and v not in strata for v in mapping.values()):reasons.append('invalid_stratum_mapping')
    unknown_labels=sorted({str(r['machine_judgment'].get('support')) for r in records if isinstance(r.get('machine_judgment'),dict) and r['machine_judgment'].get('support') not in mapping})
    if unknown_labels:reasons.append('unknown_raw_support_label')
    if any(r.get('group') not in policy.get('group_order',[]) for r in records):reasons.append('unknown_group')
    if len({(r.get('slot'),r.get('row_index')) for r in records})!=len(records):reasons.append('duplicate_candidate_positions')
    return {'ready':not reasons,'reasons':reasons,'expected':len(expected),'completed':len(records)-len(incomplete),'incomplete':len(incomplete),'unresolved_labels':unresolved,'unknown_labels':unknown_labels,'formal_sample_generated':False}

def select_formal(records, frozen_ids, policy):
    status=readiness(records,frozen_ids,policy)
    if not status['ready']:raise NotReady(';'.join(status['reasons']))
    if policy.get('target_sample_size')!=30:raise NotReady('target_sample_size_must_be_30')
    pools=defaultdict(list)
    for r in records:
        raw=r['machine_judgment']['support'];stratum=policy['raw_support_to_stratum'][raw]
        order=hashlib.sha256(f"manual-q-v2-20261019|{r['slot']}|{r['row_index']}".encode()).hexdigest()
        pools[(r['group'],stratum)].append((order,r))
    sizes={key:len(pool) for key,pool in pools.items()}
    for pool in pools.values():pool.sort(key=lambda x:(x[0],x[1]['review_id']))
    order=[(g,s) for g in policy['group_order'] for s in policy['stratum_order']];selected=[]
    while len(selected)<30:
        progressed=False
        for key in order:
            if pools[key] and len(selected)<30:
                _,row=pools[key].pop(0);copy=deepcopy(row)
                copy['sampling']={'policy_version':policy['version'],'raw_support_label':row['machine_judgment']['support'],'stratum':key[1],'population_in_stratum':sizes[key],'quality_flags_used_for_selection':False}
                selected.append(copy);progressed=True
        if not progressed:raise NotReady('insufficient_population')
    selected_counts=Counter((r['group'],r['sampling']['stratum']) for r in selected)
    for row in selected:
        row['sampling']['selected_in_stratum']=selected_counts[(row['group'],row['sampling']['stratum'])]
    return selected
