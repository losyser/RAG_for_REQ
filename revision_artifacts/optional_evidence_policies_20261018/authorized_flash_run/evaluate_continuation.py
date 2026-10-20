"""Read saved untrusted model text only; no execution, repair or model calls."""
import collections
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import socket
import sys

WORK=Path(__file__).resolve().parent
ROOT=WORK.parents[2]
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
def blocked(*a,**kw):raise RuntimeError('evaluation networking disabled')
socket.socket.connect=socket.socket.connect_ex=socket.create_connection=blocked
from cooling_rag_mg.evidence_contracts import validate_shall
from cooling_rag_mg.generation_risks import assess_generation_risks, annotate_generation_risks, RISK_POLICY
from cooling_rag_mg.engineering_requirement_agent import normalize_agent_output
import copy

plan=json.loads((WORK.parent/'full_repair_comparison/FROZEN_PLAN.json').read_text('utf-8'))
kb={r['id']:r for r in map(json.loads,(ROOT/'data/processed/evidence_units_v3_audited.jsonl').read_text('utf-8').splitlines())}
v4=json.loads((ROOT/'data/search_results/exp_v4/rag_v4_results.json').read_text('utf-8'))
value_map={r['source_requirement_id']:r.get('_evidence_values',{}) for r in v4['result_sets']}
unknown=re.compile(r'TBD|unknown|待确认|需确认|未知|未明确|未提供|未记录|无法确定|待补充|不明确|待定',re.I)
suspicious=re.compile(r'[-−－]\s*100\s*(?:°\s*[Cc]|℃|摄氏度)')
cases=[]
postprocessed=[]
for index,item in enumerate(plan['requests'],1):
    rid,arm=item['case'],item['arm']
    result={'case':rid,'arm':arm,'request_sha256':item['request_sha256'],'status':'not_attempted',
            'raw_json_valid':None,'common_schema_valid':None,'rows':[]}
    path=WORK/f'{index:02d}_{rid}_{arm}_response.json'
    if not path.exists():cases.append(result);continue
    record=json.loads(path.read_text('utf-8'))
    result.update({'status':record['status'],'elapsed_seconds':record['elapsed_seconds'],
                   'error_type':record.get('error_type'),'error':record.get('error')})
    response=record.get('response')
    if not response:cases.append(result);continue
    result['returned_model']=response.get('model');result['usage']=response.get('usage')
    choices=response.get('choices') or []
    content=(choices[0].get('message') or {}).get('content','') if choices else ''
    result['finish_reason']=choices[0].get('finish_reason') if choices else None
    result['content_sha256']=hashlib.sha256(content.encode('utf-8')).hexdigest()
    try:
        obj=json.loads(content)
        result['raw_json_valid']=True
    except Exception as exc:
        result.update({'raw_json_valid':False,'common_schema_valid':False,'parse_error_type':type(exc).__name__})
        cases.append(result);continue
    field='shalls' if rid.startswith('OR') else 'engineering_requirements'
    rows=obj.get(field) if isinstance(obj,dict) else None
    if not isinstance(rows,list):
        result['common_schema_valid']=False;result['schema_error']='missing/non-list '+field
        cases.append(result);continue
    if rid.startswith('OR'):
        scope=[{**kb[eid],'_extracted_values':value_map[rid].get(eid,[])} for eid in item['selected_ids'] if eid in kb]
        result['scope_limit']='selected full saved candidate text/value records; not every final prompt budget omission reconstructed'
    else:
        payload=json.loads(next(m['content'] for m in item['request']['messages'] if m['role']=='user'))
        scope=payload['retrieval_context']['supported_evidence']
        result['scope_limit']='exact supported_evidence objects serialized in this prompt'
    errors=[]
    ids=[]
    for n,row in enumerate(rows,1):
        if not isinstance(row,dict):
            errors.append([n,['not_object']]);continue
        if rid.startswith('OR'):
            schema_errors=validate_shall(row)
            citations=row.get('evidence_citations',[])
            citation_ids=[c.get('kb_id') for c in citations if isinstance(c,dict)] if isinstance(citations,list) else []
            complete_citations=sum(isinstance(c,dict) and all(isinstance(c.get(k),str) and bool(c[k].strip()) for k in ('kb_id','source'))
                and c.get('tier') in ('L1','L2','L3') and isinstance(c.get('has_clause'),bool) for c in citations) if isinstance(citations,list) else 0
            citation_count=len(citations) if isinstance(citations,list) else 0
        else:
            schema_errors=[]
            if not isinstance(row.get('id'),str) or not row['id'].strip():schema_errors.append('id_missing')
            else:ids.append(row['id'])
            if not isinstance(row.get('shall_statement'),str) or not row['shall_statement'].strip():schema_errors.append('shall_statement_missing')
            for key in ('acceptance_criteria','evidence_ids'):
                if not isinstance(row.get(key),list) or any(not isinstance(v,str) or not v.strip() for v in row.get(key,[]) if isinstance(row.get(key),list)):
                    schema_errors.append(key+'_not_string_list')
            citation_ids=row.get('evidence_ids',[]) if isinstance(row.get('evidence_ids'),list) else []
            citation_count=len(citation_ids);complete_citations=sum(isinstance(c,str) and bool(c.strip()) for c in citation_ids)
        if schema_errors:errors.append([n,schema_errors])
        try:risk=assess_generation_risks(row,scope)
        except Exception as exc:risk={'assessment_error':type(exc).__name__,'semantic_support':'unknown','applicability':'unknown'}
        condition_fields={k:row[k] for k in ('applicable_condition','applicability_constraints') if k in row}
        condition_text=json.dumps(condition_fields,ensure_ascii=False)
        stated_conditions='absent' if not condition_fields else 'explicit_unknown' if unknown.search(condition_text) else 'recorded_unverified'
        criterion_text='\n'.join(str(row.get(k,'')) for k in ('shall_statement','measurable_criterion','acceptance_criteria'))
        all_text=json.dumps(row,ensure_ascii=False)
        matches=[{'context':criterion_text[max(0,m.start()-100):m.end()+160],'location':'shall_or_criterion_fields'} for m in suspicious.finditer(criterion_text)]
        row_report={'position':n,'id':row.get('id'),'schema_errors':schema_errors,'citation_count':citation_count,
            'complete_citation_field_count':complete_citations,'citation_ids':citation_ids,
            'ids_missing_from_kb':[c for c in citation_ids if isinstance(c,str) and c not in kb],
            'ids_outside_selected_scope':[c for c in citation_ids if isinstance(c,str) and c not in item['selected_ids']],
            'condition_field_state':stated_conditions,'condition_fields':condition_fields,
            'any_explicit_uncertainty':bool(unknown.search(all_text)),
            'reported_direct_status':row.get('support_status')=='verified_by_direct_evidence',
            'risk':risk,'suspicious_minus100_mentions':matches,
            'suspicious_minus100_anywhere':bool(suspicious.search(all_text))}
        result['rows'].append(row_report)
    if len(ids)!=len(set(ids)):errors.append(['set',['duplicate_requirement_ids']])
    result['schema_errors']=errors;result['common_schema_valid']=not errors
    result['row_count']=len(rows)
    if arm=='new':
        post={'case':rid,'raw_row_count':len(rows),'raw_response_sha256':result['content_sha256']}
        try:
            if rid.startswith('OR'):
                out={'shalls':annotate_generation_risks(rows,scope,policy=RISK_POLICY)}
                outrows=out['shalls']
            else:
                candidate=copy.deepcopy(obj)
                candidate['allowed_engineering_aspects']=payload['retrieval_context'].get('allowed_engineering_aspects',[])
                candidate['_background_evidence_ids']=payload['retrieval_context'].get('_background_evidence_ids',[])
                out=normalize_agent_output(candidate,rid,evidence_scope=scope,risk_policy=RISK_POLICY)
                outrows=out['engineering_requirements']
            post.update({'postprocessed_row_count':len(outrows),
                'raw_direct_status_count':sum(r.get('support_status')=='verified_by_direct_evidence' for r in rows),
                'postprocessed_direct_status_count':sum(r.get('support_status')=='verified_by_direct_evidence' for r in outrows),
                'output':out})
        except Exception as exc:post['error_type']=type(exc).__name__;post['error']=str(exc)
        postprocessed.append(post)
    cases.append(result)

pairs=[]
for rid in ('OR010','OR023','R001','R002','R003'):
    old,new=[next(c for c in cases if c['case']==rid and c['arm']==arm) for arm in ('old','new')]
    pairs.append({'case':rid,'complete_model_response_pair':all(c.get('returned_model') for c in (old,new)),
        'old_schema_valid':old['common_schema_valid'],'new_schema_valid':new['common_schema_valid'],
        'old_rows':old.get('row_count'),'new_rows':new.get('row_count')})
summaries={}
for arm in ('old','new'):
    eligible=[c for c in cases if c['arm']==arm and c['case']!='OR001' and any(p['case']==c['case'] and p['complete_model_response_pair'] for p in pairs)]
    rows=[r for c in eligible for r in c['rows']]
    summaries[arm]={'paired_cases':len(eligible),'json_valid_cases':sum(c['raw_json_valid'] is True for c in eligible),
        'schema_valid_cases':sum(c['common_schema_valid'] is True for c in eligible),'rows':len(rows),
        'citation_fields_complete':sum(r['complete_citation_field_count'] for r in rows),'citation_fields_total':sum(r['citation_count'] for r in rows),
        'rows_with_unknown_citation_ids':sum(bool(r['ids_missing_from_kb']) for r in rows),
        'rows_with_out_of_scope_citations':sum(bool(r['ids_outside_selected_scope']) for r in rows),
        'rows_with_quantity_tuple_risk':sum(r['risk'].get('numeric_consistency')=='unmatched_requires_review' for r in rows),
        'rows_with_no_recognized_quantity':sum(r['risk'].get('numeric_consistency')=='unknown_no_recognized_quantity' for r in rows),
        'rows_with_lexical_tuple_match_only':sum(r['risk'].get('numeric_consistency')=='lexical_tuple_match_only' for r in rows),
        'condition_field_states':dict(collections.Counter(r['condition_field_state'] for r in rows)),
        'rows_with_any_explicit_uncertainty':sum(r['any_explicit_uncertainty'] for r in rows),
        'reported_direct_status_rows':sum(r['reported_direct_status'] for r in rows)}
usage=[c['usage'] for c in cases if c.get('usage')]
peak_cost=sum((Decimal(u['prompt_tokens'])*2+Decimal(u['completion_tokens'])*8 for u in usage),Decimal(0))/Decimal(1000000)
ledger=json.loads((WORK/'continuation_ledger.json').read_text('utf-8'))
report={'terminal':ledger['status'],'actual_attempts':len(ledger['attempts']),'retained_total_reservation_CNY':ledger['reserved_CNY'],
    'model_responses':len(usage),'response_usage_totals':{'prompt_tokens':sum(u['prompt_tokens'] for u in usage),'completion_tokens':sum(u['completion_tokens'] for u in usage)},
    'known_usage_peak_no_cache_cost_CNY':str(peak_cost),'prior_failed_attempt_reserved_CNY':'2.162688',
    'actual_account_bill_CNY':None,'pairs':pairs,'paired_summary':summaries,'cases':cases,
    'limitations':['No gold labels, human correctness rate, significance or causal quality estimate.',
        'Unequal row counts are reported with denominators; lexical risks are not semantic adjudications.',
        'OR001 excluded from paired summaries because old failed; new retained separately.',
        'All generated text treated as untrusted data; no output instructions executed.']}
(WORK/'CONTINUATION_EVALUATION.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
(WORK/'POSTPROCESS_DIAGNOSTICS.json').write_text(json.dumps({'note':'Offline application of new policy only; raw saved model outputs remain untouched; no replacement or repair call.','cases':postprocessed},ensure_ascii=False,indent=2),'utf-8')
print(json.dumps({k:report[k] for k in ('terminal','actual_attempts','model_responses','response_usage_totals','known_usage_peak_no_cache_cost_CNY','pairs','paired_summary')},ensure_ascii=False,indent=2))
