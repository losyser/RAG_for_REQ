"""Offline evaluation of every attempted slot; raw output and gated delivery separated."""
import copy,hashlib,json,re,socket,sys
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[2];WORK=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
def blocked(*a,**k):raise RuntimeError('offline analysis only')
socket.socket.connect=socket.socket.connect_ex=socket.create_connection=blocked
from cooling_rag_mg.structured_req_generator import generate_structured_shalls
from cooling_rag_mg.evidence_quarantine import load_review_flags
from cooling_rag_mg.evidence_contracts import validate_shall
read=lambda p:json.loads(p.read_text('utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
plan=read(WORK/'FROZEN_PLAN.json');ledger=read(WORK/'ledger.json')
flags=load_review_flags(ROOT/'revision_artifacts/evidence_quarantine_20261018/development_review_flags.json')
kb={r['id']:r for r in map(json.loads,(ROOT/'data/processed/evidence_units_v3_audited.jsonl').read_text('utf-8').splitlines())}
ors={r['requirement_id']:r['requirement_text'] for r in map(json.loads,(ROOT/'data/processed/original_requirements_v2.jsonl').read_text('utf-8').splitlines())}
v4=read(ROOT/'data/search_results/exp_v4/rag_v4_results.json')
cases=[];cost=Decimal(0)
for i,item in enumerate(plan['requests'],13):
    prefix=f"{i:02d}_{item['case']}_{item['arm']}";path=WORK/(prefix+'_response.json')
    if not path.exists():cases.append({'case':item['case'],'arm':item['arm'],'status':'not_attempted'});continue
    rec=read(path);case={'case':item['case'],'arm':item['arm'],'status':rec['status'],'request_sha256':item['request_sha256'],'response_file_sha256':sha(path)}
    assert read(WORK/(prefix+'_request.json'))==item
    if rec['status']!='completed':cases.append(case);continue
    response=rec['response'];raw=response['choices'][0]['message']['content'];obj=json.loads(raw);rows=obj['shalls']
    saved=next(r for r in v4['result_sets'] if r['source_requirement_id']==item['case'])
    evidence=[{**kb[eid],'_extracted_values':values} for eid,values in saved['_evidence_values'].items() if eid in kb]
    captured=[]
    def completion(**kw):
        captured.append(copy.deepcopy(kw));return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=raw))])
    report={}
    delivered=generate_structured_shalls(ors[item['case']],evidence,
        SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=completion))), 'deepseek-flash',
        max_tokens=8192,selection_policy='numeric-first-reserve-one-nonnumeric-v1',risk_policy='independent-reference-quantity-applicability-v1',
        quarantine_flags=flags if item['arm']=='on' else None,delivery_report=report,schema_policy='isolate-invalid-rows-v1' if item['arm']=='on' else 'legacy')
    assert len(captured)==1
    captured[0]['extra_body']={'thinking':{'type':'disabled'}};assert captured[0]==item['request']
    pattern=r'[-−]\s*100\s*(?:°\s*C|℃)'
    def mentions(items):
        return [{'position':n,'fields':{k:r[k] for k in ('shall_statement','measurable_criterion','acceptance_criteria') if re.search(pattern,str(r.get(k,'')),re.I)}}
            for n,r in enumerate(items,1) if any(re.search(pattern,str(r.get(k,'')),re.I) for k in ('shall_statement','measurable_criterion','acceptance_criteria'))]
    case.update({'returned_model':response['model'],'response_id':response['id'],'usage':response['usage'],
        'finish_reason':response['choices'][0]['finish_reason'],'raw_rows':len(rows),'delivery_rows':len(delivered),
        'withheld_rows':len(report.get('withheld',[])), 'schema_withheld_rows':len(report.get('schema_withheld',[])),'raw_minus100':mentions(rows),'delivery_minus100':mentions(delivered),
        'schema_errors':[{'position':n,'errors':validate_shall(r)} for n,r in enumerate(rows,1) if validate_shall(r)],
        'raw_rows_data':rows,'delivery':delivered,'quarantine_review':report,
        'raw_out_of_scope_ids':sorted({c.get('kb_id') for r in rows for c in r.get('evidence_citations',[]) if c.get('kb_id') not in item['selected_ids']})})
    cost+=Decimal(rec['peak_no_cache_cost_CNY']);cases.append(case)
checks={}
for name,path in [('historical',ROOT/'revision_artifacts/optional_evidence_policies_20261018/protected_before.json'),
                  ('additional',ROOT/'revision_artifacts/followup_integrity_20261018/additional_protected_before.json')]:
    manifest=read(path);changed=[p for p,h in manifest.items() if sha(Path(p))!=h];assert not changed;checks[name]={'count':len(manifest),'changed':changed}
summary={'new_attempts':len(ledger['attempts'])-12,'completed_responses':sum(c['status']=='completed' for c in cases),
    'new_known_usage_peak_estimate_CNY':str(cost),'combined_known_usage_peak_estimate_CNY':str(cost+Decimal('0.429976')),
    'total_reservation_CNY':ledger['reserved_CNY'],'prior_failed_uncertain_reserves_CNY':'4.325376','actual_account_bill':None,
    'protection':checks,'cases':cases}
(WORK/'EVALUATION_ROW_ISOLATION.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps({**{k:v for k,v in summary.items() if k!='cases'},'cases':[{k:v for k,v in c.items() if k not in ('raw_rows_data','delivery','quarantine_review')} for c in cases]},ensure_ascii=False,indent=2))
