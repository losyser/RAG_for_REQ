"""One authorized four-slot run. Exclusive ledger; zero retries; no repair."""
from pathlib import Path
import copy,hashlib,json,sys,time
from decimal import Decimal
ROOT=Path(__file__).resolve().parents[2];WORK=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
PRIOR=ROOT/'revision_artifacts/optional_evidence_policies_20261018'
sys.path.insert(0,str(PRIOR/'authorized_flash_run'))
import run_frozen as guard
import httpx
from environment_transport import EnvironmentRoutingTransport,exception_types

class FourSlotTransport(guard.GuardedTransport):
    def handle_request(self, request):
        if request.method!='POST' or str(request.url)!='https://api.deepseek.com/chat/completions':
            raise RuntimeError('Unapproved endpoint')
        if self.expected is None or len(self.ledger['attempts'])>=16:
            raise RuntimeError('No remaining dispatch authorization')
        item=self.expected
        wire={k:v for k,v in item['request'].items() if k!='extra_body'}
        wire.update(item['request']['extra_body'])
        if json.loads(request.content)!=wire:raise RuntimeError('Frozen wire body mismatch')
        total=sum((Decimal(a['reserved_CNY']) for a in self.ledger['attempts']),Decimal(0))+guard.RESERVE
        if total>Decimal('34.603008') or total>Decimal('50'):raise RuntimeError('Budget cap')
        self.expected=None
        self.ledger['attempts'].append({'case':item['case'],'arm':item['arm'],'request_sha256':item['request_sha256'],
            'started_at':guard.now(),'reserved_CNY':str(guard.RESERVE),'status':'dispatched_charge_unknown'})
        self.ledger['reserved_CNY']=str(total);guard.save(self.path,self.ledger)
        print('dispatch',len(self.ledger['attempts']),'of 16 cumulative; reserved_CNY='+str(total),flush=True)
        return self.delegate.handle_request(request)

def main(execute=False):
    plan=json.loads((WORK/'FROZEN_PLAN.json').read_text('utf-8'))
    prior=json.loads((PRIOR/'authorized_flash_slot12/slot12_ledger.json').read_text('utf-8'))
    assert len(prior['attempts'])==12 and prior['reserved_CNY']=='25.952256'
    assert len(plan['requests'])==4
    assert [(i['case'],i['arm']) for i in plan['requests']]==[('OR010','off'),('OR010','on'),('OR023','off'),('OR023','on')]
    for item in plan['requests']:
        req=item['request']
        assert hashlib.sha256(guard.canonical(req)).hexdigest()==item['request_sha256']
        assert req['model']=='deepseek-flash' and req['extra_body']=={'thinking':{'type':'disabled'}}
        assert req['max_tokens']==8192 and req['temperature']==0
    assert Decimal(prior['reserved_CNY'])+guard.RESERVE*4==Decimal('34.603008')<Decimal('50')
    protection=guard.hashes_unchanged()
    if not execute:
        print(json.dumps({'preflight':'passed','additional_dispatch_cap':4,'cumulative_reservation_CNY':'34.603008',**protection}));return
    from cooling_rag_mg.config import DeepSeekConfig
    from openai import OpenAI
    cfg=DeepSeekConfig()
    assert cfg.api_key and cfg.base_url.rstrip('/')=='https://api.deepseek.com'
    clean=lambda obj:json.loads(json.dumps(obj,ensure_ascii=False,default=str).replace(cfg.api_key,'[REDACTED]'))
    ledger_path=WORK/'ledger.json'
    ledger={'status':'running','started_at':guard.now(),'attempts':copy.deepcopy(prior['attempts']),
        'reserved_CNY':prior['reserved_CNY'],'prior_attempts':12,'max_total_attempts':16,'max_new_attempts':4,'max_retries':0,
        'budget_CNY':'50','prior_ledger_sha256':hashlib.sha256((PRIOR/'authorized_flash_slot12/slot12_ledger.json').read_bytes()).hexdigest(),
        'plan_sha256':hashlib.sha256((WORK/'FROZEN_PLAN.json').read_bytes()).hexdigest(),'approval':plan['approval']}
    with ledger_path.open('x',encoding='utf-8') as f:json.dump(ledger,f,indent=2)
    guard.MAX_ATTEMPTS=16  # inherited transport consumes permission once and verifies exact endpoint/body
    timeout=httpx.Timeout(connect=10,read=120,write=30,pool=10)
    transport=FourSlotTransport(EnvironmentRoutingTransport(timeout),ledger,ledger_path)
    client=OpenAI(api_key=cfg.api_key,base_url='https://api.deepseek.com',max_retries=0,
        http_client=httpx.Client(transport=transport,timeout=timeout,follow_redirects=False),timeout=timeout)
    try:
        for i,item in enumerate(plan['requests'],13):
            name=f"{i:02d}_{item['case']}_{item['arm']}"
            guard.save(WORK/(name+'_request.json'),item)
            record={'case':item['case'],'arm':item['arm'],'request_sha256':item['request_sha256'],'started_at':guard.now()}
            transport.expected=item;started=time.monotonic()
            try:
                raw=client.chat.completions.with_raw_response.create(**item['request'])
                record.update({'http_status':raw.status_code,'raw_response_body':raw.text,
                    'response_headers':{k:v for k,v in raw.headers.items() if k.lower() in ('date','x-request-id','request-id','content-type')}})
                payload=raw.parse().model_dump(mode='json');record['response']=payload
                usage=payload['usage'];assert usage['prompt_tokens']<=1048576 and usage['completion_tokens']<=8192
                assert payload['model'].lower() in ('deepseek-flash','deepseek-v4.1-flash-1017')
                assert not any(c.get('message',{}).get('reasoning_content') for c in payload['choices'])
                record['peak_no_cache_cost_CNY']=str((Decimal(usage['prompt_tokens'])*2+Decimal(usage['completion_tokens'])*8)/Decimal(1000000))
                record['status']='completed'
            except Exception as exc:
                record.update({'status':'failed_stop','error_type':type(exc).__name__,'error':str(exc),'exception_chain_types':exception_types(exc)})
                response=getattr(exc,'response',None)
                if response is not None:record.update({'http_status':response.status_code,'error_response_body':response.text})
            record.update({'elapsed_seconds':round(time.monotonic()-started,3),'finished_at':guard.now()});record=clean(record)
            guard.save(WORK/(name+'_response.json'),record)
            if len(ledger['attempts'])==i:ledger['attempts'][-1].update({k:record[k] for k in ('status','elapsed_seconds','finished_at')})
            guard.save(ledger_path,ledger);print(i,item['case'],item['arm'],record['status'],flush=True)
            if record['status']!='completed':ledger['status']='stopped_after_failure';break
        else:ledger['status']='completed_four_new_slots'
    finally:
        client.close();ledger['finished_at']=guard.now();ledger['protection_after']=guard.hashes_unchanged();guard.save(ledger_path,ledger)
        print(json.dumps({'terminal':ledger['status'],'total_attempts':len(ledger['attempts']),'reserved_CNY':ledger['reserved_CNY']}))

if __name__=='__main__':main('--execute-authorized' in sys.argv)
