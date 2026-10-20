"""Single authorized, bounded run. No retries, repair, continuation or resume."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sys
import time

import httpx
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'authorized_flash_run'))
from environment_transport import EnvironmentRoutingTransport, exception_types

ROOT = Path(__file__).resolve().parents[3]
WORK = Path(__file__).resolve().parent.parent/'authorized_flash_run'
OUT = Path(__file__).resolve().parent
PLAN_PATH = WORK.parent / 'full_repair_comparison/FROZEN_PLAN.json'
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True
MAX_ATTEMPTS = 12
RESERVE = (Decimal(1048576)*2+Decimal(8192)*8)/Decimal(1000000)
EXPECTED_PRICE_SHA = '7428747bd2fe3a0b1935a3454d1f29640c1d863a5a14be0a5f8bcb873f407b49'


def now():
    return datetime.now(timezone.utc).isoformat()


def canonical(obj):
    return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')


def save(path, obj):
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(obj,ensure_ascii=False,indent=2),'utf-8')
    temp.replace(path)


def hashes_unchanged():
    protected=json.loads((WORK.parent/'protected_before.json').read_text('utf-8'))
    dirty=json.loads((WORK.parent/'dirty_before.json').read_text('utf-8'))
    bad=[p for p,h in protected.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h]
    unrelated=[p for p,h in dirty.items() if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h]
    if bad or unrelated:
        raise RuntimeError('Protected or pre-existing dirty files changed')
    return {'protected_count':len(protected),'protected_changed':bad,'unrelated_dirty_changed':unrelated}


def preflight():
    plan=json.loads(PLAN_PATH.read_text('utf-8'))
    assert plan['model']=='deepseek-flash' and plan['base_url']=='https://api.deepseek.com'
    assert len(plan['requests'])==MAX_ATTEMPTS
    assert [(r['case'],r['arm']) for r in plan['requests']]==[(rid,arm) for rid in ('OR001','OR010','OR023','R001','R002','R003') for arm in ('old','new')]
    assert hashlib.sha256((WORK/'pricing_cny.html').read_bytes()).hexdigest()==EXPECTED_PRICE_SHA
    assert RESERVE*MAX_ATTEMPTS<=Decimal('40')<Decimal('50')
    for item in plan['requests']:
        req=item['request']
        assert hashlib.sha256(canonical(req)).hexdigest()==item['request_sha256']
        assert req['model']=='deepseek-flash' and req['max_tokens']==8192
        assert req['extra_body']=={'thinking':{'type':'disabled'}}
        assert set(req)=={'model','messages','temperature','max_tokens','response_format','extra_body'}
        assert sum(len(m['content'].encode('utf-8')) for m in req['messages'])==item['prompt_utf8_bytes']
    return plan


class GuardedTransport(httpx.BaseTransport):
    """Counts real HTTP dispatches, reserves before sending, rejects implicit extras."""
    def __init__(self, delegate, ledger, path):
        self.delegate,self.ledger,self.path=delegate,ledger,path
        self.expected=None

    def handle_request(self, request):
        if request.method!='POST' or str(request.url)!='https://api.deepseek.com/chat/completions':
            raise RuntimeError('Unapproved endpoint or method')
        if self.expected is None:
            raise RuntimeError('Unapproved extra attempt')
        item=self.expected
        wire={k:v for k,v in item['request'].items() if k!='extra_body'}
        wire.update(item['request']['extra_body'])
        if json.loads(request.content)!=wire:
            raise RuntimeError('Wire body differs from frozen request')
        if len(self.ledger['attempts'])>=MAX_ATTEMPTS:
            raise RuntimeError('12 actual request cap reached')
        total=sum((Decimal(a['reserved_CNY']) for a in self.ledger['attempts']),Decimal(0))+RESERVE
        if total>Decimal('40') or total>Decimal('50'):
            raise RuntimeError('CNY budget cap reached')
        self.expected=None  # Never permit an SDK retry, redirect or duplicate.
        self.ledger['attempts'].append({'case':item['case'],'arm':item['arm'],'request_sha256':item['request_sha256'],
            'started_at':now(),'reserved_CNY':str(RESERVE),'status':'dispatched_charge_unknown'})
        self.ledger['reserved_CNY']=str(total)
        save(self.path,self.ledger)
        print(f"dispatch {len(self.ledger['attempts'])}/12 {item['case']} {item['arm']} reserved_CNY={total}",flush=True)
        return self.delegate.handle_request(request)

    def close(self):
        self.delegate.close()


def main(execute=False, continue_remaining=False):
    plan=preflight()
    protection=hashes_unchanged()
    if not execute:
        print(json.dumps({'preflight':'passed','requests':12,'peak_reservation_CNY':str(RESERVE*12),**protection}))
        return
    from cooling_rag_mg.config import DeepSeekConfig
    from openai import OpenAI
    cfg=DeepSeekConfig()
    if cfg.base_url.rstrip('/')!='https://api.deepseek.com' or not cfg.api_key:
        raise RuntimeError('Configured endpoint/credential precondition failed')
    # Do not expose the key, headers, environment, or SDK client representation.
    def clean(value):
        return json.loads(json.dumps(value,ensure_ascii=False,default=str).replace(cfg.api_key,'[REDACTED]'))
    ledger_path=OUT/'slot12_ledger.json'
    prior = None
    if continue_remaining:
        prior = json.loads((WORK/'continuation_ledger.json').read_text('utf-8'))
        assert prior['status']=='stopped_after_failure' and len(prior['attempts'])==11
        assert prior['attempts'][0]['case']=='OR001' and prior['attempts'][0]['arm']=='old'
        assert prior['attempts'][0]['status']=='failed_stop'
        assert prior['reserved_CNY']==str(RESERVE*11)
        assert prior['attempts'][-1]['case']=='R003' and prior['attempts'][-1]['arm']=='old' and prior['attempts'][-1]['status']=='failed_stop'
        assert [(a['case'],a['arm'],a['request_sha256']) for a in prior['attempts']]==[(i['case'],i['arm'],i['request_sha256']) for i in plan['requests'][:11]]
        assert plan['requests'][11]['case']=='R003' and plan['requests'][11]['arm']=='new'
        assert prior['plan_sha256']==hashlib.sha256(PLAN_PATH.read_bytes()).hexdigest()
    # Exclusive create prevents restarting/reusing this run after partial execution.
    with ledger_path.open('x',encoding='utf-8') as f:
        ledger={'status':'running','started_at':now(),'base_url':'https://api.deepseek.com','model':'deepseek-flash',
            'approval':'Parent-forwarded explicit user approval for six frozen cases, max 12 attempts, RMB 50.',
            'plan_sha256':hashlib.sha256(PLAN_PATH.read_bytes()).hexdigest(),'pricing_sha256':EXPECTED_PRICE_SHA,
            'rates_CNY_per_million':{'input_cache_miss_peak':'2','input_cache_hit_peak':'0.04','output_peak':'8'},
            'max_retries':0,'max_attempts':12,'max_output_tokens':8192,'attempts':[],'reserved_CNY':'0',
            'initial_reservation_ceiling_CNY':'40','total_ceiling_CNY':'50','protection_before':protection}
        if prior is not None:
            ledger['attempts']=prior['attempts']
            ledger['reserved_CNY']=prior['reserved_CNY']
            ledger['prior_ledger_sha256']=hashlib.sha256((WORK/'continuation_ledger.json').read_bytes()).hexdigest()
            ledger['continuation_authorization']='Parent forwarded recharge and authorization for previously unattempted frozen slot 12 only; no failed-slot replacement; cumulative cap 12 and RMB 50.'
            ledger['run_script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        json.dump(ledger,f,ensure_ascii=False,indent=2)
    timeout=httpx.Timeout(connect=10,read=120,write=30,pool=10)
    transport=GuardedTransport(EnvironmentRoutingTransport(timeout),ledger,ledger_path)
    http_client=httpx.Client(transport=transport,timeout=timeout,follow_redirects=False)
    client=OpenAI(api_key=cfg.api_key,base_url='https://api.deepseek.com',max_retries=0,timeout=timeout,http_client=http_client)
    try:
        offset=len(ledger['attempts'])
        for index,item in enumerate(plan['requests'][offset:],offset+1):
            filename=f"{index:02d}_{item['case']}_{item['arm']}"
            save(OUT/(filename+'_request.json'),item)
            transport.expected=item
            started=time.monotonic()
            record={'case':item['case'],'arm':item['arm'],'request_sha256':item['request_sha256'],'started_at':now()}
            try:
                raw=client.chat.completions.with_raw_response.create(**item['request'])
                record['http_status']=raw.status_code
                record['response_headers']={k:v for k,v in raw.headers.items() if k.lower() in ('date','x-request-id','request-id','content-type')}
                record['raw_response_body']=raw.text
                response=raw.parse()
                payload=response.model_dump(mode='json')
                record['response']=payload
                record['status']='response_received'
                usage=payload.get('usage')
                model=str(payload.get('model',''))
                choices=payload.get('choices') or []
                if not usage or any(not isinstance(usage.get(k),int) for k in ('prompt_tokens','completion_tokens')):
                    raise RuntimeError('Missing or invalid usage; stop without retry')
                if usage['prompt_tokens']>1048576 or usage['completion_tokens']>8192:
                    raise RuntimeError('Provider usage exceeds reserved limits')
                if model.lower() not in ('deepseek-flash','deepseek-v4.1-flash-1017'):
                    raise RuntimeError('Returned model identity differs from verified route: '+model)
                if any((c.get('message') or {}).get('reasoning_content') for c in choices):
                    raise RuntimeError('Unexpected thinking content with thinking disabled')
                record['peak_no_cache_cost_CNY']=str((Decimal(usage['prompt_tokens'])*2+Decimal(usage['completion_tokens'])*8)/Decimal(1000000))
                record['status']='completed'
            except Exception as exc:
                record['status']='failed_stop'
                record['error_type']=type(exc).__name__
                record['error']=str(exc)
                record['exception_chain_types']=exception_types(exc)
                response=getattr(exc,'response',None)
                if response is not None:
                    record['http_status']=response.status_code
                    record['error_response_body']=response.text
            record['elapsed_seconds']=round(time.monotonic()-started,3)
            record['finished_at']=now()
            record=clean(record)
            save(OUT/(filename+'_response.json'),record)
            if ledger['attempts'] and ledger['attempts'][-1]['request_sha256']==item['request_sha256']:
                ledger['attempts'][-1].update({k:record[k] for k in ('status','elapsed_seconds','finished_at')})
            save(ledger_path,ledger)
            print(f"result {index}/12 {item['case']} {item['arm']} {record['status']} seconds={record['elapsed_seconds']}",flush=True)
            if record['status']!='completed':
                ledger['status']='stopped_after_failure'
                ledger['stop_reason']=record.get('error','unknown')
                break
        else:
            ledger['status']='completed_slot12_with_two_prior_failures' if continue_remaining else 'completed_12_attempts'
    finally:
        client.close()
        ledger['finished_at']=now()
        ledger['protection_after']=hashes_unchanged()
        save(ledger_path,ledger)
        print(json.dumps({'terminal':ledger['status'],'actual_attempts':len(ledger['attempts']),'reserved_CNY':ledger['reserved_CNY']}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--execute-authorized',action='store_true')
    parser.add_argument('--continue-authorized',action='store_true')
    args=parser.parse_args()
    if args.execute_authorized and args.continue_authorized:
        parser.error('choose one execution mode')
    main(args.execute_authorized or args.continue_authorized,args.continue_authorized)
