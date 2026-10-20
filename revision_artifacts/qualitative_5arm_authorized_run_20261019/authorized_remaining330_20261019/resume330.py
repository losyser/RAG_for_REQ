"""Explicit continuation of only330 never-sent frozen requests; ID anomaly excluded."""
import sys
from decimal import Decimal
from pathlib import Path
HERE=Path(__file__).resolve().parent
WORK=HERE.parent
PREVIOUS=WORK/'authorized_resume_20261019'
ROOT=WORK.parents[1]
sys.path.insert(0,str(PREVIOUS))
import transport as t
import resume as prior_resume

def reconcile(items, attempts, responses, prior):
    if len(items)!=441 or len({x['review_id'] for x in items})!=441:raise ValueError('frozen_population')
    if len(attempts)!=34 or len(responses)!=34:raise ValueError('previous_attempt_count')
    debit=Decimal(prior);success=set();failed=[]
    for index,(a,r) in enumerate(zip(attempts,responses)):
        x=items[77+index]
        if a['slot']!=x['review_id'] or a['body_sha256']!=x['body_sha256'] or r['slot']!=x['review_id']:raise ValueError('previous_request_mismatch')
        if r['status']=='completed':
            if r['parsed']['review_id']!=x['review_id']:raise ValueError('successful_id_mismatch')
            success.add(x['review_id']);debit+=Decimal(r['usage_cost_CNY'])
        else:failed.append(index);debit+=Decimal(a['reserved_CNY'])
    if len(success)!=33 or failed!=[33] or responses[33].get('error')!='review_id_mismatch':raise ValueError('unexpected_previous_failure')
    pending=items[111:]
    if len(pending)!=330 or set(x['review_id'] for x in pending)&(success|{items[110]['review_id']}|{x['review_id'] for x in items[:77]}):raise ValueError('scope_overlap')
    return pending,debit

def preflight():
    _,old_debit,identity,_=prior_resume.preflight()
    manifest=t.read(HERE/'PREVIOUS_ARTIFACT_HASHES.json')
    for name,digest in manifest.items():
        if t.sha(PREVIOUS/name)!=digest:raise ValueError('previous_material_changed:'+name)
    if (PREVIOUS/'review/RUNNING.lock').exists():raise ValueError('previous_active')
    items=t.read(WORK/'QWEN_FROZEN_PLAN.json')['requests']
    attempts=[t.read(p) for p in sorted((PREVIOUS/'review').glob('*_attempt.json'))]
    responses=[t.read(p) for p in sorted((PREVIOUS/'review').glob('*_response.json'))]
    pending,prior=reconcile(items,attempts,responses,old_debit)
    if prior!=Decimal('10.4038132') or prior!=Decimal(t.read(PREVIOUS/'review/state.json')['debit_CNY']):raise ValueError('ledger_mismatch')
    if pending!=t.read(PREVIOUS/'review/UNSENT_QUEUE.json'):raise ValueError('unsent_queue_mismatch')
    if any(r['identity']!=identity for r in responses if r.get('identity')):raise ValueError('identity_drift')
    for x in pending:t.validate_request(x,'review')
    report={'pending':330,'prior_debit_CNY':str(prior),'excluded_invalid_review_id':items[110]['review_id'],'preserved_successful_review_count':110,'preserved_generation_count':300,'pending_digest':t.digest(pending),'endpoint':t.PROVIDERS['review']['endpoint'],'model':'qwen-max','baseline_identity':identity,'previous_artifacts_verified':len(manifest),'global_attempt_numbers':'113..442','new_attempt_namespace':'authorized_remaining330_20261019/review','max_retries':0,'budget_cap_CNY':'50','formal_sampling_gate_unchanged':'all441_valid_completed'}
    return pending,prior,identity,report

def main():
    pending,prior,identity,report=preflight();t.atomic(HERE/'PREFLIGHT.json',report)
    if '--execute-authorized' not in sys.argv:print(report);return
    sys.path.insert(0,str(ROOT))
    from cooling_rag_mg.config import QwenConfig
    import httpx
    cfg=QwenConfig()
    if cfg.base_url.rstrip('/')!=t.PROVIDERS['review']['endpoint'].rsplit('/chat/completions',1)[0] or cfg.model!='qwen-max' or not cfg.api_key:raise ValueError('existing_config_mismatch')
    t.exclusive(HERE/'EXECUTION_AUTHORIZATION.json',{'at':t.now(),'scope':'Continue330 never-sent packets in previously user-confirmed364; exclude quarantined ID mismatch; no replay110 or generation300; stop at next anomaly','pending_digest':t.digest(pending)})
    t.exclusive(HERE/'ATTEMPT_LINKS.json',[{'local_attempt':i+1,'global_attempt':i+113,'review_id':x['review_id'],'body_sha256':x['body_sha256']} for i,x in enumerate(pending)])
    with httpx.Client(timeout=httpx.Timeout(connect=15,read=180,write=30,pool=15),follow_redirects=False,trust_env=True) as client:
        state=t.Engine(HERE/'review','review',pending,client,cfg.api_key,prior_debit=prior,baseline_identity=identity).run()
    print(state,flush=True)

if __name__=='__main__':main()
