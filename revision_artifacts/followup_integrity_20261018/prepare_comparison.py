"""Freeze requests with mocked entrypoints. No client/network/model execution."""
import copy
import hashlib
import json
from pathlib import Path
import socket
import sys
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[2]
WORK=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
def blocked(*a,**k):raise RuntimeError('offline preparation only')
socket.socket.connect=socket.socket.connect_ex=socket.create_connection=blocked
from cooling_rag_mg import engineering_requirement_agent as ui
from cooling_rag_mg import structured_req_generator as gen
from cooling_rag_mg.evidence_quarantine import load_review_flags
read=lambda p:json.loads(p.read_text('utf-8'))
old=read(ROOT/'revision_artifacts/optional_evidence_policies_20261018/full_repair_comparison/FROZEN_PLAN.json')
flags=load_review_flags(ROOT/'revision_artifacts/evidence_quarantine_20261018/development_review_flags.json')
kb={r['id']:r for r in map(json.loads,(ROOT/'data/processed/evidence_units_v3_audited.jsonl').read_text('utf-8').splitlines())}
ors={r['requirement_id']:r['requirement_text'] for r in map(json.loads,(ROOT/'data/processed/original_requirements_v2.jsonl').read_text('utf-8').splitlines())}
v4=read(ROOT/'data/search_results/exp_v4/rag_v4_results.json')
requests=[]
for item in [i for i in old['requests'] if i['arm']=='new']:
 rid=item['case']
 for arm in ('off','on'):
  captured=[]
  def completion(*a,**kw):
   captured.append(copy.deepcopy(kw))
   return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='{"shalls":[],"engineering_requirements":[]}'))])
  opts={'risk_policy':'independent-reference-quantity-applicability-v1','quarantine_flags':flags if arm=='on' else None}
  if rid.startswith('OR'):
   saved=next(r for r in v4['result_sets'] if r['source_requirement_id']==rid)
   ev=[{**kb[eid],'_extracted_values':values} for eid,values in saved['_evidence_values'].items() if eid in kb]
   gen.generate_structured_shalls(ors[rid],ev,SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=completion))),
       'deepseek-flash',max_tokens=8192,selection_policy='numeric-first-reserve-one-nonnumeric-v1',delivery_report={},**opts)
  else:
   payload=json.loads(next(m['content'] for m in item['request']['messages'] if m['role']=='user'))
   ui.compact_requirement_context=lambda x:copy.deepcopy(payload['retrieval_context'])
   ui.cached_completion=completion;ui.repair_json_with_deepseek=blocked
   ui.get_config=lambda:SimpleNamespace(deepseek=SimpleNamespace(enabled=True,model='deepseek-flash',temperature=0,max_tokens_requirement_agent=8192,make_client=lambda:object()))
   ui.generate_engineering_requirements_for_requirement(payload['original_requirement'],{'requirements':[]},**opts)
  assert len(captured)==1
  req=captured[0];req['extra_body']={'thinking':{'type':'disabled'}}
  if arm=='off':assert req==item['request'],rid+' off prompt unexpectedly changed'
  blob=json.dumps(req,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
  byte_count=sum(len(m['content'].encode('utf-8')) for m in req['messages'])
  requests.append({'case':rid,'arm':arm,'selected_ids':item['selected_ids'],'request_sha256':hashlib.sha256(blob).hexdigest(),
      'prompt_utf8_bytes':byte_count,'planning_input_tokens':byte_count+4096,'request':req})
focus=[r for r in requests if r['case'] in ('OR023','OR010')]
assert len(focus)==4
report={'status':'PREPARED_NOT_AUTHORIZED_NOT_SENT','base_url':'https://api.deepseek.com','model':'deepseek-flash',
    'focus_cases':['OR023','OR010'],'focus_requests':focus,'all_six_case_candidates':requests,
    'selection_rule':'OR023 is the already identified flagged failure; OR010 is the previously fixed unit-boundary case and unflagged control, chosen without new generation. No verified healthy negative-temperature real control found.',
    'negative_control_limit':'67 regex hits in KB are unverified candidates, not 67 true negative limits. Synthetic healthy-negative regression tests are offline only.',
    'max_focus_requests_including_failures':4,'max_retries':0,'repair_calls':0,
    'focus_output_cap_tokens':32768,'focus_input_planning_tokens':sum(r['planning_input_tokens'] for r in focus),
    'prior_reservations_CNY':'25.952256','additional_full_context_reserve_CNY':'8.650752','cumulative_reservation_CNY':'34.603008',
    'budget_CNY':'50','pricing_basis':'Prior frozen official peak CNY rates, input miss 2/M output 8/M; not new billing verification.',
    'authorization_limit':'Only four requests proposed; the other eight candidates are not part of this proposed authorization. No executor is included.'}
(WORK/'PENDING_COMPARISON.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ('focus_requests','all_six_case_candidates')},ensure_ascii=False))
