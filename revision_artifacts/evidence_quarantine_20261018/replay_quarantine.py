"""Replay all nine saved responses through actual generation entries with mocks.

No network/model call. Existing paid artifacts and historical data are read-only.
"""
import copy
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import socket
import sys
from types import SimpleNamespace
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2];WORK=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
def offline(*a,**kw):raise RuntimeError('quarantine replay: network forbidden')
socket.socket.connect=socket.socket.connect_ex=socket.create_connection=offline
from cooling_rag_mg.evidence_quarantine import load_review_flags,gate_delivery
from cooling_rag_mg.structured_req_generator import generate_structured_shalls
from cooling_rag_mg import engineering_requirement_agent as agent

flags=load_review_flags(WORK/'development_review_flags.json')
PAID=ROOT/'revision_artifacts/optional_evidence_policies_20261018/authorized_flash_run'
plan=json.loads((PAID.parent/'full_repair_comparison/FROZEN_PLAN.json').read_text('utf-8'))
kb={r['id']:r for r in map(json.loads,(ROOT/'data/processed/evidence_units_v3_audited.jsonl').read_text('utf-8').splitlines())}
assert hashlib.sha256(kb['E-HT-COMP-036']['text'].encode('utf-8')).hexdigest()==flags[0]['local_text_sha256']
v4=json.loads((ROOT/'data/search_results/exp_v4/rag_v4_results.json').read_text('utf-8'))
values={r['source_requirement_id']:r['_evidence_values'] for r in v4['result_sets']}
texts={r['requirement_id']:r['requirement_text'] for r in map(json.loads,(ROOT/'data/processed/original_requirements_v2.jsonl').read_text('utf-8').splitlines())}
rows=[];audits=[];known_usage=[]
for i,item in enumerate(plan['requests'],1):
    request_file=PAID/f"{i:02d}_{item['case']}_{item['arm']}_request.json"
    response_file=PAID/f"{i:02d}_{item['case']}_{item['arm']}_response.json"
    if request_file.exists():
        recorded=json.loads(request_file.read_text('utf-8'))
        canonical=json.dumps(recorded['request'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
        assert hashlib.sha256(canonical).hexdigest()==item['request_sha256']
        assert recorded['request']==item['request']
        assert recorded['request']['model']=='deepseek-flash' and recorded['request']['extra_body']=={'thinking':{'type':'disabled'}}
    if not response_file.exists():continue
    response=json.loads(response_file.read_text('utf-8'))
    if not response.get('response'):continue
    paid_response=response['response'];known_usage.append(paid_response['usage'])
    content=paid_response['choices'][0]['message']['content']
    raw=json.loads(content);rid=item['case'];captured=[]
    def completion(*a,**kw):
        captured.append(kw['messages'])
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])
    if rid.startswith('OR'):
        evidence=[{**kb[eid],'_extracted_values':values[rid].get(eid,[])} for eid in item['selected_ids'] if eid in kb]
        client=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=completion)))
        legacy=generate_structured_shalls(texts[rid],evidence,client,'offline')
        assert legacy==raw['shalls']
        report={}
        delivery=generate_structured_shalls(texts[rid],evidence,client,'offline',quarantine_flags=flags,delivery_report=report)
        raw_rows=raw['shalls']
        # These canned completions were generated before quarantine. This tests
        # containment, not how a future model would respond to the masked prompt.
    else:
        payload=json.loads(next(m['content'] for m in item['request']['messages'] if m['role']=='user'))
        compact=payload['retrieval_context']
        config=SimpleNamespace(deepseek=SimpleNamespace(enabled=True,make_client=lambda:object(),model='offline',temperature=0,max_tokens_requirement_agent=8192))
        with patch.object(agent,'get_config',return_value=config),patch.object(agent,'cached_completion',side_effect=completion),\
             patch.object(agent,'repair_json_with_deepseek',side_effect=offline),patch.object(agent,'compact_requirement_context',return_value=copy.deepcopy(compact)):
            out=agent.generate_engineering_requirements_for_requirement(payload['original_requirement'],{'requirements':[compact]},quarantine_flags=flags)
        delivery=out['engineering_requirements'];report=out['_quarantine_delivery'];raw_rows=raw['engineering_requirements']
    masked_prompt=captured[-1]
    flag_selected='E-HT-COMP-036' in item['selected_ids']
    if flag_selected:
        assert '-100' not in json.dumps(masked_prompt,ensure_ascii=False)
        assert 'QUARANTINED' in json.dumps(masked_prompt,ensure_ascii=False)
    # No formal delivery row may carry a quarantined support/reference/binding.
    for delivered in delivery:
        check={};assert len(gate_delivery([delivered],flags,report=check))==1
    record={'case':rid,'arm':item['arm'],'raw_response_sha256':hashlib.sha256(response_file.read_bytes()).hexdigest(),
        'raw_rows':len(raw_rows),'delivery_rows':len(delivery),'withheld_rows':len(report['withheld']),
        'statuses':[r['status'] for r in report['withheld']],
        'withheld_positions':[r.get('position') for r in report['withheld']],
        'flagged_evidence_in_selected_input':flag_selected,
        'masked_prompt_sha256':hashlib.sha256(json.dumps(masked_prompt,ensure_ascii=False,sort_keys=True).encode('utf-8')).hexdigest()}
    rows.append(record);audits.append({'case':rid,'arm':item['arm'],'delivery':delivery,'review':report,'masked_prompt':masked_prompt})

assert len(rows)==9
or23=[r for r in rows if r['case']=='OR023']
assert len(or23)==2 and all(r['withheld_positions']==[4] and r['statuses']==['blocked_numeric'] for r in or23)
ledger=json.loads((PAID/'continuation_ledger.json').read_text('utf-8'))
usage_peak=sum((Decimal(u['prompt_tokens'])*2+Decimal(u['completion_tokens'])*8 for u in known_usage),Decimal(0))/Decimal(1000000)
uncertain=sum((Decimal(a['reserved_CNY']) for a in ledger['attempts'] if a['status']!='completed'),Decimal(0))
audit={'attempts':len(ledger['attempts']),'responses':len(known_usage),'failed_attempts':sum(a['status']!='completed' for a in ledger['attempts']),
    'known_usage_peak_no_cache_CNY':str(usage_peak),'uncertain_failed_reservations_CNY':str(uncertain),
    'all_dispatch_reservations_CNY':ledger['reserved_CNY'],'actual_bill_CNY':None,
    'frozen_request_body_checks':'all 11 stored request bodies hash-identical to frozen plan; Flash/non-thinking unchanged',
    'scope':'four completed pairs plus unpaired OR001 new; R003 has no response'}
manifest=json.loads((WORK/'protected_before.json').read_text('utf-8'))
after={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in manifest};assert after==manifest
model_manifest=json.loads((WORK/'model_artifacts_before.json').read_text('utf-8'))
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in model_manifest.items())
dirty=json.loads((PAID.parent/'dirty_before.json').read_text('utf-8'))
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in dirty.items())
(WORK/'protected_after.json').write_text(json.dumps(after,indent=2),'utf-8')
summary={'saved_responses':len(rows),'raw_rows':sum(r['raw_rows'] for r in rows),'delivery_rows':sum(r['delivery_rows'] for r in rows),
    'withheld_rows':sum(r['withheld_rows'] for r in rows),'protected_count':len(after),'protected_changed':[],
    'prior_model_artifacts_count':len(model_manifest),'prior_model_artifacts_changed':[],'unrelated_dirty_changed':[]}
(WORK/'REPLAY.json').write_text(json.dumps({'summary':summary,'cases':rows,'billing_and_request_audit':audit},ensure_ascii=False,indent=2),'utf-8')
(WORK/'DELIVERY_AND_REVIEW.json').write_text(json.dumps(audits,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2));print(json.dumps(rows,ensure_ascii=False,indent=2));print(json.dumps(audit,ensure_ascii=False,indent=2))
