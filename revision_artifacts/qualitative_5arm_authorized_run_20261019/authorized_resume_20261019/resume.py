"""Explicitly authorized continuation; old journals remain immutable."""
import sys
from pathlib import Path
from decimal import Decimal
import transport as t

HERE=Path(__file__).resolve().parent
WORK=HERE.parent
ROOT=WORK.parents[1]
sys.path.insert(0,str(WORK))
import runner as original

def reconcile(items, attempts, responses, prior):
    if len(items)!=441 or len({x['review_id'] for x in items})!=441:raise ValueError('frozen_population')
    if len(attempts)!=78 or len(responses)!=78:raise ValueError('old_attempt_count')
    debit=Decimal(prior);completed=set();failed=[]
    for i,(a,r) in enumerate(zip(attempts,responses)):
        x=items[i]
        if a['slot']!=x['slot'] or a['body_sha256']!=x['body_sha256'] or r['slot']!=x['slot']:raise ValueError('old_request_mismatch')
        if r['status']=='completed':
            if r['parsed']['review_id']!=x['review_id']:raise ValueError('old_judgment_mismatch')
            completed.add(x['review_id']);debit+=Decimal(r['usage_cost_CNY'])
        else:
            failed.append(i);debit+=Decimal(a['reserved_CNY'])
    if len(completed)!=77 or failed!=[77] or 'Arrearage' not in responses[77]['raw_response_body']:raise ValueError('unexpected_old_failure')
    pending=[x for x in items if x['review_id'] not in completed]
    if len(pending)!=364 or pending!=items[77:]:raise ValueError('pending_scope')
    return pending,debit

def preflight():
    original.verify_frozen()
    for name,h in t.read(WORK/'ARTIFACT_HASHES_FINAL.json').items():
        if t.sha(WORK/name)!=h:raise ValueError('old_artifact_changed:'+name)
    plan=t.read(WORK/'QWEN_FROZEN_PLAN.json');items=plan['requests']
    if t.digest(items)!=plan['requests_sha256']:raise ValueError('plan_hash')
    attempts=[t.read(p) for p in sorted((WORK/'review').glob('*_attempt.json'))]
    responses=[t.read(p) for p in sorted((WORK/'review').glob('*_response.json'))]
    pending,prior=reconcile(items,attempts,responses,t.read(WORK/'generation/state.json')['debit_CNY'])
    if prior!=Decimal(t.read(WORK/'review/state.json')['debit_CNY']):raise ValueError('ledger_mismatch')
    if (WORK/'review/RUNNING.lock').exists() or (WORK/'generation/RUNNING.lock').exists():raise ValueError('old_running_lock')
    for x in pending:t.validate_request(x,'review')
    identity=responses[0]['identity']
    if any(r['identity']!=identity for r in responses[:77]):raise ValueError('old_identity_drift')
    report={'authorized_scope':'resubmit prior Arrearage candidate once plus 363 unsent; never repeat 77 successes or 300 generations','pending':364,'prior_debit_CNY':str(prior),'old_failure_reservation_retained_CNY':attempts[77]['reserved_CNY'],'old_failure_request_id':'c9bcb96f-0080-9316-bafe-a601d05a4a27','old_failed_review_id':items[77]['review_id'],'endpoint':t.PROVIDERS['review']['endpoint'],'model':'qwen-max','baseline_identity':identity,'pending_digest':t.digest(pending),'new_attempt_namespace':'authorized_resume_20261019/review/0001..0364; global attempts 79..442','max_automatic_retries':0,'budget_cap_CNY':'50','old_artifacts_unchanged':True}
    return pending,prior,identity,report

def main():
    pending,prior,identity,report=preflight()
    t.atomic(HERE/'PREFLIGHT.json',report)
    if '--execute-authorized' not in sys.argv:
        print(t.redact(report));return
    sys.path.insert(0,str(ROOT))
    from cooling_rag_mg.config import QwenConfig
    import httpx
    cfg=QwenConfig()
    if cfg.base_url.rstrip('/')!=t.PROVIDERS['review']['endpoint'].rsplit('/chat/completions',1)[0] or cfg.model!='qwen-max' or not cfg.api_key:raise ValueError('existing_config_mismatch')
    t.exclusive(HERE/'EXECUTION_AUTHORIZATION.json',{'at':t.now(),'instruction':'User states Qwen recharged and requests continuation; delegated scope exactly 364 candidates, cap50, stop on first failure','pending_digest':t.digest(pending)})
    t.exclusive(HERE/'ATTEMPT_LINKS.json',[{'local_attempt':i+1,'global_attempt':i+79,'review_id':x['review_id'],'body_sha256':x['body_sha256'],'previous_failed_attempt':78 if i==0 else None,'previous_request_id':report['old_failure_request_id'] if i==0 else None} for i,x in enumerate(pending)])
    with httpx.Client(timeout=httpx.Timeout(connect=15,read=180,write=30,pool=15),follow_redirects=False,trust_env=True) as client:
        state=t.Engine(HERE/'review','review',pending,client,cfg.api_key,prior_debit=prior,baseline_identity=identity).run()
    print(state,flush=True)

if __name__=='__main__':main()
