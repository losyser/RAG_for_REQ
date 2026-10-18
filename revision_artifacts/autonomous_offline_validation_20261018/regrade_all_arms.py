"""Frozen-input, all-arm deterministic sensitivity audit; never update primary data."""
from pathlib import Path
from collections import Counter
import hashlib,json,socket,sys
ROOT=Path(__file__).resolve().parents[2];WORK=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
def blocked(*a,**k):raise RuntimeError('network disabled')
socket.socket.connect=socket.socket.connect_ex=socket.create_connection=blocked
from cooling_rag_mg.grade_classifier import classify_result_set,RANGE_CLASSIFIER_VERSION as CLASSIFIER_VERSION
from cooling_rag_mg.review_routing import derivation_assessment,review_route
from cooling_rag_mg.revision_audit import verify_frozen_arm_inputs
read=lambda p:json.loads(p.read_text('utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ARMS={'rag':'rag_v4_results.json','norag':'norag_v4_results.json','random':'ablation_random_retrieval_results.json','rag_qwen':'rag_v4_qwen_results.json','norag_qwen':'norag_v4_qwen_results.json'}
base=ROOT/'data/search_results/exp_v4';audit=ROOT/'revision_artifacts/audit_20261015'
assert not verify_frozen_arm_inputs(ROOT,ARMS,read(audit/'baseline_manifest.json'))
kbpath=ROOT/'data/processed/evidence_units_v3_audited.jsonl'
kb={r['id']:r for r in map(json.loads,kbpath.read_text('utf-8').splitlines())}
old=read(base/'paper_numbers.json');v2=read(audit/'routing_v2.json')['arms']
frozen={'classifier_version':CLASSIFIER_VERSION,'code_sha256':sha(ROOT/'cooling_rag_mg/grade_classifier.py'),
 'routing_code_sha256':sha(ROOT/'cooling_rag_mg/review_routing.py'),'kb_sha256':sha(kbpath),
 'arms':{arm:{'path':str(base/fn),'sha256':sha(base/fn)} for arm,fn in ARMS.items()},
 'protocol':'All five frozen arms, all rows; compare stored grade, historical registry and prior v2 row audit; no row selection, new generation, new gold or primary adoption.'}
(WORK/'FROZEN_AUDIT_INPUTS.json').write_text(json.dumps(frozen,indent=2),'utf-8')
results={};changes=[]
for arm,fn in ARMS.items():
 data=read(base/fn);prior={x['id']:x for x in v2[arm]['rows']};rows=[]
 for result in data['result_sets']:
  graded=classify_result_set(result,kb,numeric_policy="numeric-ranges-v1")
  for n,(before,after) in enumerate(zip(result['engineering_requirements'],graded['engineering_requirements']),1):
   ident=f"{result['source_requirement_id']}.{n}";previous=prior[ident]
   route,reason=review_route(after,kb,result.get('_evidence_values') or {})
   row={'id':ident,'stored_grade':before.get('_grade'),'v2_grade':previous['grade_v2'],
       'current_grade':after['_grade'],'current_reason':after['_grade_reason'],'valid_citation_ids':after['_valid_citation_ids'],
       'v2_route':previous['route'],'current_route':route,'route_reason':reason,
       'criterion':before.get('measurable_criterion'),'shall_statement':before.get('shall_statement'),
       'applicable_condition':before.get('applicable_condition'),'semantic_support':'not_independently_verified',
       'scope':after['_grade_scope']}
   rows.append(row)
   if row['current_grade']!=row['v2_grade'] or row['current_route']!=row['v2_route']:
    changes.append({'arm':arm,**row})
 assert len(rows)==len(prior)
 counts=Counter(row['current_grade'] for row in rows);routes=Counter(row['current_route'] for row in rows)
 results[arm]={'n_rows':len(rows),'n_sources':len(data['result_sets']),'current_counts':dict(counts),
    'v2_counts':dict(Counter(x['v2_grade'] for x in rows)),'stored_counts':dict(Counter(x['stored_grade'] for x in rows)),
    'current_AB_percent':round(100*(counts['A']+counts['B'])/len(rows),4),
    'current_X_percent':round(100*counts['X']/len(rows),4),'current_routes':dict(routes),
    'historical_registry':old[arm],'changed_vs_v2':sum(x['arm']==arm for x in changes),'rows':rows}
report={'status':'DETERMINISTIC_SENSITIVITY_NOT_ADOPTED','classifier_version':CLASSIFIER_VERSION,'arms':results,'changes':changes,
 'limits':['Grade measures finite unit recognition and citation metadata, not engineering truth.','Current unit/citation fixes are not independent scientific validation.','Routing is a review heuristic, not applicability or authority adjudication.','Historical generation outputs and all unfavorable findings retained.']}
(WORK/'ALL_ARM_REGRADING.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
assert all(sha(Path(v['path']))==v['sha256'] for v in frozen['arms'].values()) and sha(kbpath)==frozen['kb_sha256']
print(json.dumps({'version':CLASSIFIER_VERSION,'changes':len(changes),'arms':{arm:{k:v for k,v in item.items() if k not in ('rows','historical_registry')} for arm,item in results.items()}},ensure_ascii=False,indent=2))
