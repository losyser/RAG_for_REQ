"""Authorized serial transport. No retry, redirect, repair, or speculative dispatch."""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
from decimal import Decimal
import hashlib,json,os,re,sys,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];WORK=Path(__file__).resolve().parent
V2=WORK.parent/'qualitative_5arm_v2_preflight_20261019'
PRIOR=Decimal('4.888538');CAP=Decimal('50');BUFFER=Decimal('1')
PROVIDERS={
 'generation':{'endpoint':'https://api.deepseek.com/chat/completions','model':'deepseek-flash','returned_models':['deepseek-flash','deepseek-v4.1-flash-1017'],'input_limit':1048576,'output_limit':8192,'input_rate':'2','output_rate':'8','max_attempts':300},
 'review':{'endpoint':'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions','model':'qwen-max','returned_models':['qwen-max','qwen-max-2025-01-25'],'input_limit':30720,'output_limit':2048,'input_rate':'2.4','output_rate':'9.6','max_attempts':1200}}
def now():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf8'))
def atomic(p,x):
    p=Path(p);t=p.with_name(p.name+'.tmp')
    with t.open('w',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
    os.replace(t,p)
def exclusive(p,x):
    with Path(p).open('x',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
def redact(x,secrets=()):
    s=json.dumps(x,ensure_ascii=False,default=str)
    for secret in secrets:
        if secret:s=s.replace(secret,'[REDACTED]')
    s=re.sub(r'sk-[A-Za-z0-9_-]{12,}','[REDACTED]',s)
    return json.loads(s)
def reserve(provider):
    return (Decimal(provider['input_limit'])*Decimal(provider['input_rate'])+Decimal(provider['output_limit'])*Decimal(provider['output_rate']))/1000000
def usage_cost(payload,p):
    if payload.get('model','').lower() not in p['returned_models']:raise ValueError('unexpected_model')
    u=payload.get('usage') or {}
    for k,limit in [('prompt_tokens',p['input_limit']),('completion_tokens',p['output_limit'])]:
        if type(u.get(k)) is not int or not 0<=u[k]<=limit:raise ValueError('invalid_or_missing_usage_'+k)
    if type(u.get('total_tokens')) is not int or u['total_tokens']!=u['prompt_tokens']+u['completion_tokens']:raise ValueError('usage_total_mismatch')
    return (Decimal(u['prompt_tokens'])*Decimal(p['input_rate'])+Decimal(u['completion_tokens'])*Decimal(p['output_rate']))/1000000
def validate_request(item,phase):
    p=PROVIDERS[phase];b=item['body']
    if digest(b)!=item['body_sha256']:raise ValueError('request_hash_mismatch')
    if b['model']!=p['model'] or b['temperature']!=0 or b['max_tokens']!=p['output_limit'] or b['response_format']!={'type':'json_object'}:raise ValueError('request_parameter_drift')
    if not b.get('messages') or any(m.get('role') not in ['user','system'] for m in b['messages']):raise ValueError('message_shape')
    allowed={'model','messages','temperature','max_tokens','response_format','extra_body'}
    if set(b)-allowed:raise ValueError('extra_request_parameters')
    if phase=='generation' and b.get('extra_body')!={'thinking':{'type':'disabled'}}:raise ValueError('thinking_parameter_drift')
    if phase=='review' and b.get('extra_body'):raise ValueError('review_extra_body')
    return p
def decode_content(payload,phase):
    choices=payload.get('choices')
    if not isinstance(choices,list) or len(choices)!=1:raise ValueError('unexpected_choices')
    c=choices[0]
    if c.get('finish_reason')!='stop':raise ValueError('non_stop_finish_'+str(c.get('finish_reason')))
    m=c.get('message') or {}
    if m.get('refusal') or m.get('tool_calls') or m.get('reasoning_content'):raise ValueError('refusal_tools_or_unexpected_reasoning')
    parsed=json.loads(m.get('content') or '')
    if not isinstance(parsed,dict):raise ValueError('non_object_json')
    if phase=='generation':
        if not isinstance(parsed.get('shalls'),list) or any(not isinstance(r,dict) for r in parsed['shalls']):raise ValueError('invalid_shalls_schema')
    return parsed

class Engine:
    def __init__(self,folder,phase,items,client,key,prior_debit=PRIOR,secrets=()):
        self.folder=Path(folder);self.folder.mkdir(exist_ok=True);self.phase=phase;self.items=items;self.client=client;self.key=key;self.secrets=tuple(secrets)+(key,);self.prior=Decimal(prior_debit)
        if len(items)>PROVIDERS[phase]['max_attempts'] or len({x['slot'] for x in items})!=len(items):raise ValueError('attempt_cap_or_duplicate_slots')
        for x in items:validate_request(x,phase)
        self.plan_hash=digest(items);self.p=PROVIDERS[phase]
    def debit(self):
        total=self.prior
        for p in self.folder.glob('*_attempt.json'):
            a=read(p);rp=p.with_name(p.name.replace('_attempt','_response'))
            if rp.exists() and read(rp).get('status')=='completed':total+=Decimal(read(rp)['usage_cost_CNY'])
            else:total+=Decimal(a['reserved_CNY'])
        return total
    def check_resume(self):
        attempts=sorted(self.folder.glob('*_attempt.json'));completed=0
        if len(attempts)>len(self.items):raise RuntimeError('more_attempts_than_plan')
        for index,path in enumerate(attempts):
            a=read(path);item=self.items[index]
            if a['plan_hash']!=self.plan_hash or a['slot']!=item['slot'] or a['body_sha256']!=item['body_sha256']:raise RuntimeError('resume_plan_mismatch')
            rp=path.with_name(path.name.replace('_attempt','_response'))
            if not rp.exists() or read(rp).get('status')!='completed':raise RuntimeError('unresolved_or_failed_attempt_no_automatic_resume')
            completed+=1
        return completed
    def run(self):
        lock=self.folder/'RUNNING.lock'
        with lock.open('x',encoding='utf8') as f:f.write(now())
        state={'phase':self.phase,'plan_hash':self.plan_hash,'status':'running','started_at':now(),'attempt_cap':len(self.items),'budget_cap_CNY':str(CAP),'buffer_CNY':str(BUFFER),'prior_debit_CNY':str(self.prior),'max_retries':0}
        try:
            start=self.check_resume();first_identity=None
            if start:
                first_identity=read(self.folder/'0001_response.json')['identity']
            atomic(self.folder/'state.json',state)
            for idx,item in enumerate(self.items[start:],start+1):
                if self.debit()+reserve(self.p)+BUFFER>CAP:
                    state.update(status='paused_budget',stop_reason='next_max_reservation_plus_buffer_exceeds_50',next_slot=item['slot']);break
                stem=f'{idx:04d}';attempt={'slot':item['slot'],'body_sha256':item['body_sha256'],'plan_hash':self.plan_hash,'endpoint':self.p['endpoint'],'started_at':now(),'reserved_CNY':str(reserve(self.p)),'status':'dispatch_may_have_occurred','item':item}
                exclusive(self.folder/(stem+'_attempt.json'),attempt)
                print(json.dumps({'event':'dispatch','phase':self.phase,'index':idx,'total':len(self.items),'slot':item['slot'],'debit_including_reservation_CNY':str(self.debit())}),flush=True)
                t=time.monotonic();record={'slot':item['slot'],'started_at':attempt['started_at'],'status':'failed_stop'}
                try:
                    wire={k:v for k,v in item['body'].items() if k!='extra_body'};wire.update(item['body'].get('extra_body',{}))
                    response=self.client.post(self.p['endpoint'],json=wire,headers={'Authorization':'Bearer '+self.key,'Content-Type':'application/json'})
                    record.update(http_status=response.status_code,raw_response_body=response.text,response_headers={k:v for k,v in response.headers.items() if k.lower() in ['date','x-request-id','request-id','content-type']})
                    if response.status_code!=200:raise RuntimeError('HTTP_'+str(response.status_code))
                    payload=response.json();record['response']=payload
                    cost=usage_cost(payload,self.p);record['observed_usage_cost_CNY']=str(cost)
                    identity={'model':payload['model'],'system_fingerprint':payload.get('system_fingerprint')}
                    record['identity']=identity
                    if first_identity is not None and identity!=first_identity:raise RuntimeError('observable_model_identity_drift')
                    parsed=decode_content(payload,self.phase)
                    if self.phase=='review' and parsed.get('review_id')!=item['review_id']:raise ValueError('review_id_mismatch')
                    record.update(status='completed',usage_cost_CNY=str(cost),parsed=parsed)
                    first_identity=identity
                except Exception as exc:
                    record.update(error_type=type(exc).__name__,error=str(exc))
                record.update(finished_at=now(),elapsed_seconds=round(time.monotonic()-t,3))
                record=redact(record,self.secrets);exclusive(self.folder/(stem+'_response.json'),record)
                state.update(last_index=idx,last_slot=item['slot'],debit_CNY=str(self.debit()),last_finished_at=now())
                atomic(self.folder/'state.json',state)
                print(json.dumps({'event':'result','phase':self.phase,'index':idx,'status':record['status'],'debit_CNY':str(self.debit()),'error':record.get('error')}),flush=True)
                if record['status']!='completed':state.update(status='paused_failure',stop_reason=record.get('error','failed'),next_slot=self.items[idx]['slot'] if idx<len(self.items) else None);break
            else:state['status']='completed'
        except Exception as exc:
            state.update(status='paused_local_guard',stop_reason=redact(str(exc),self.secrets));raise
        finally:
            attempted={read(p)['slot'] for p in self.folder.glob('*_attempt.json')}
            atomic(self.folder/'UNSENT_QUEUE.json',[x for x in self.items if x['slot'] not in attempted])
            state.update(finished_at=now(),debit_CNY=str(self.debit()),attempted=len(attempted),unsent=len(self.items)-len(attempted))
            atomic(self.folder/'state.json',state);lock.unlink()
        return state

def verify_frozen():
    expected=read(WORK/'RUN_PREFLIGHT.json')
    for p,h in expected['frozen_hashes'].items():
        if sha(p)!=h:raise RuntimeError('frozen_input_or_code_changed:'+p)
    for p,h in expected['protected_hashes'].items():
        if sha(p)!=h:raise RuntimeError('protected_file_changed:'+p)
    return expected

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=PROVIDERS,default='generation');ap.add_argument('--execute-authorized',action='store_true');args=ap.parse_args()
    pre=verify_frozen()
    if args.phase=='generation':items=read(V2/'REQUESTS_300_PENDING.json');prior=PRIOR
    else:
        gs=read(WORK/'generation/state.json')
        if gs['status']!='completed':raise RuntimeError('generation_not_completed_no_review_dispatch')
        rp=read(WORK/'QWEN_FROZEN_PLAN.json');items=rp['requests'];prior=Decimal(gs['debit_CNY'])
        if digest(items)!=rp['requests_sha256']:raise RuntimeError('Qwen_plan_hash_mismatch')
        if len(items)>1200:raise RuntimeError('Q_count_exceeds1200')
    for item in items:validate_request(item,args.phase)
    if not args.execute_authorized:print(json.dumps({'preflight':'pass','phase':args.phase,'requests':len(items),'prior_debit_CNY':str(prior)}));return
    # Credentials only enter memory after all offline gates; no config mutation or key logging.
    sys.path.insert(0,str(ROOT));from cooling_rag_mg.config import DeepSeekConfig,QwenConfig
    import httpx
    cfg=DeepSeekConfig() if args.phase=='generation' else QwenConfig()
    p=PROVIDERS[args.phase]
    if cfg.base_url.rstrip('/')!=p['endpoint'].rsplit('/chat/completions',1)[0]:raise RuntimeError('configured_provider_endpoint_mismatch')
    if args.phase=='review' and cfg.model!=p['model']:raise RuntimeError('configured_Qwen_model_mismatch')
    if not cfg.api_key:raise RuntimeError('missing_existing_credential')
    # HTTPX default transport uses zero retries and existing environment routing. No proxy/security changes.
    with httpx.Client(timeout=httpx.Timeout(connect=15,read=180,write=30,pool=15),follow_redirects=False,trust_env=True) as client:
        state=Engine(WORK/args.phase,args.phase,items,client,cfg.api_key,prior_debit=prior).run()
    print(json.dumps(state),flush=True)

if __name__=='__main__':main()
