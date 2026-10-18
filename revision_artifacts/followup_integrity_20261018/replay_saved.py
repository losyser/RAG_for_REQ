"""Replay all ten saved completions through current gates, offline only."""
import copy, hashlib, json, socket, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];WORK=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
def blocked(*a,**k):raise RuntimeError('offline replay')
socket.socket.connect=socket.socket.connect_ex=socket.create_connection=blocked
from cooling_rag_mg.evidence_quarantine import load_review_flags,gate_delivery
from cooling_rag_mg.engineering_requirement_agent import normalize_agent_output
read=lambda p:json.loads(p.read_text('utf-8'))
base=ROOT/'revision_artifacts/optional_evidence_policies_20261018'
plan=read(base/'full_repair_comparison/FROZEN_PLAN.json')
flags=load_review_flags(ROOT/'revision_artifacts/evidence_quarantine_20261018/development_review_flags.json')
cases=[]
for i,item in enumerate(plan['requests'],1):
 directory=base/('authorized_flash_slot12' if i==12 else 'authorized_flash_run')
 path=directory/f"{i:02d}_{item['case']}_{item['arm']}_response.json"
 rec=read(path)
 if rec['status']!='completed':continue
 raw=rec['response']['choices'][0]['message']['content'];obj=json.loads(raw)
 if item['case'].startswith('OR'):
  rows=obj['shalls'];review={};delivered=gate_delivery(rows,flags,report=review,evidence_scope=[{'id':eid} for eid in item['selected_ids']])
  out={'shalls':delivered,'review':review}
 else:
  payload=json.loads(next(m['content'] for m in item['request']['messages'] if m['role']=='user'))
  ctx=payload['retrieval_context'];rows=copy.deepcopy(obj['engineering_requirements'])
  obj['allowed_engineering_aspects']=ctx.get('allowed_engineering_aspects',[])
  obj['_background_evidence_ids']=ctx.get('_background_evidence_ids',[])
  out=normalize_agent_output(obj,item['case'],evidence_scope=ctx['supported_evidence'],quarantine_flags=flags)
  delivered=out['engineering_requirements'];review=out['_quarantine_delivery']
 cases.append({'case':item['case'],'arm':item['arm'],'raw_response_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
  'raw_rows':len(rows),'delivered_rows':len(delivered),'withheld_rows':len(review['withheld']),'output':out})
summary={'saved_responses':len(cases),'raw_rows':sum(c['raw_rows'] for c in cases),'delivered_rows':sum(c['delivered_rows'] for c in cases),'withheld_rows':sum(c['withheld_rows'] for c in cases)}
assert summary['saved_responses']==10
(WORK/'QUARANTINE_REPLAY_V2.json').write_text(json.dumps({'summary':summary,'cases':cases},ensure_ascii=False,indent=2),'utf-8')
checks={}
for name,path in [('historical',base/'protected_before.json'),('additional',WORK/'additional_protected_before.json')]:
 manifest=read(path);changed=[p for p,h in manifest.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h]
 assert not changed,changed
 checks[name]={'count':len(manifest),'changed':changed}
dirty=read(base/'dirty_before.json')
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in dirty.items())
checks['unrelated_dirty_changed']=[]
(WORK/'PROTECTION_AFTER.json').write_text(json.dumps(checks,indent=2),'utf-8')
print(json.dumps({'replay':summary,'protection':checks}))
