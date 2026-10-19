"""Read saved usage and frozen requests; generate transparent budgets, never call APIs."""
from pathlib import Path
import hashlib,json,statistics
from decimal import Decimal

ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
V2=OUT.parent/'qualitative_5arm_v2_preflight_20261019'
def read(p):return json.loads(Path(p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(n,d):(OUT/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def main():
    assert not (OUT/'BUDGET_RECONCILIATION.json').exists(),'Preserve frozen budget revision'
    prior_hashes={str(p):sha(p) for folder in [V2,OUT.parent/'qualitative_2x2_preflight_20261019'] for p in folder.iterdir() if p.is_file()}
    success=[];failure=[]
    for folder in ['optional_evidence_policies_20261018/authorized_flash_run','optional_evidence_policies_20261018/authorized_flash_slot12','quarantine_flash_comparison_20261018']:
        for p in sorted((OUT.parent/folder).glob('*_response.json')):
            d=read(p)
            if d.get('status')!='completed':
                failure.append({'path':str(p),'sha256':sha(p),'status':d.get('status'),'max_risk_reservation_CNY':'2.162688'});continue
            u=d['response']['usage'];req=read(p.with_name(p.name.replace('_response','_request')))['request']
            bs=sum(len(m['content'].encode('utf8')) for m in req['messages'])
            value=(Decimal(u['prompt_tokens'])*2+Decimal(u['completion_tokens'])*8)/1000000
            success.append({'path':str(p),'sha256':sha(p),'prompt_tokens':u['prompt_tokens'],'completion_tokens':u['completion_tokens'],'message_utf8_bytes':bs,'peak_uncached_usage_estimate_CNY':str(value)})
    assert len(success)==14 and len(failure)==2
    known=sum(Decimal(s['peak_uncached_usage_estimate_CNY']) for s in success);risk=sum(Decimal(f['max_risk_reservation_CNY']) for f in failure)
    assert known==Decimal('0.563162') and risk==Decimal('4.325376')
    requests=read(V2/'REQUESTS_300_PENDING.json');bs=sum(r['utf8_message_bytes'] for r in requests)
    ratios=[s['message_utf8_bytes']/s['prompt_tokens'] for s in success];ratio=statistics.median(ratios);outmean=statistics.mean(s['completion_tokens'] for s in success)
    emp_input=bs/ratio;emp_out=300*outmean;emp_cost=(emp_input*2+emp_out*8)/1e6
    byte_tokens=bs+4096*300;byte_cost=Decimal(byte_tokens*2+300*8192*8)/1000000
    perq=Decimal('0.0933888');q_scenarios=[]
    for n in [0,300,600,1200]:
        q_scenarios.append({'N_Q':n,'assumed_input_tokens_per_review':2000,'assumed_output_tokens_per_review':600,'assumption_not_measured':True,'illustrative_Q_cost_CNY':str(Decimal(n)*(Decimal(2000)*Decimal('2.4')+Decimal(600)*Decimal('9.6'))/1000000),'full_context_Q_ceiling_CNY':str(n*perq)})
    result={'version':'five-arm-budget-v3-20261019','supersedes':'v1/v2 budget interpretation only; frozen five-arm inputs/prompts/classifier unchanged',
      'prior_successful_attempts':14,'prior_usage_input_tokens':sum(s['prompt_tokens'] for s in success),'prior_usage_output_tokens':sum(s['completion_tokens'] for s in success),'prior_usage_estimate_CNY':str(known),'prior_failed_attempts':2,'prior_failed_max_risk_CNY':str(risk),'prior_modeled_cost_plus_failure_risk_CNY':str(known+risk),'unexecuted_budget_after_usage_reconciliation_CNY':str(50-known-risk),'billing_verified':False,'old_full_reservation_not_actual_spend_CNY':'34.603008',
      'frozen_generation_count':300,'frozen_utf8_message_bytes':bs,'matching_official_tokenizer_found':False,'tokenizer_search_scope':['D:/models','D:/cooling_rag_multigranular (excluding inaccessible old pytest directories)'],'nonmatching_models_not_used':['Qwen2.5-VL-3B-Instruct','BGE/MPNet/rerankers'],
      'empirical_scenario':{'reference':'14 prior successful DeepSeek Flash responses, different tasks and prompt lengths; not a confidence bound','bytes_per_input_token_min':min(ratios),'bytes_per_input_token_median':ratio,'bytes_per_input_token_max':max(ratios),'estimated_input_tokens':emp_input,'mean_output_tokens_per_call':outmean,'estimated_output_tokens':emp_out,'generation_estimate_CNY':emp_cost},
      'conditional_byte_scenario':{'input_tokens_proxy':byte_tokens,'message_bytes':bs,'assumed_protocol_and_json_allowance_per_request':4096,'generation_output_tokens_max':300*8192,'generation_CNY':str(byte_cost),'assumptions':'Only if the exact provider tokenizer has <=1 token per UTF-8 input byte, normalization does not expand this bound, and provider serialization overhead fits4096 tokens per request. Not verified for current model; NOT a dispatch guarantee or actual-token claim.'},
      'provider_context_theoretical_ceiling':{'generation_per_attempt_CNY':'2.162688','generation_all_300_CNY':'648.806400','purpose':'Sum of maximum possible requests, not expected spend, not a reason alone to reject complete execution. Use next-attempt reservation and usage reconciliation.'},
      'Qwen':{'provider':'Alibaba Cloud Model Studio Beijing','model':'qwen-max','price_date':'2026-10-19','input_CNY_per_million':'2.4','output_CNY_per_million':'9.6','actual_N_Q':None,'attempt_cap_proposed':1200,'max_output_tokens_per_attempt':2048,'full_context_per_attempt_CNY':str(perq),'scenarios':q_scenarios,'all_Q_rule':'If N_Q exceeds1200 or cumulative affordability, pause; no silent sampling while claiming all-Q coverage.'},
      'hard_stop_accounting':{'cap_CNY':'50','safety_buffer_CNY':'1.000000','formula':'known_usage_estimates + all_unresolved_failed_or_inflight_reservations + next_provider_max_reservation + safety_buffer <= 50','no_concurrent_calls':True,'max_retries':0,'success':'On valid usage, model and price confirmation, replace only that attempt reservation with peak uncached usage cost estimate; retain response evidence. This is a tariff ledger, not verified provider billing.','failure':'Retain full attempt reservation; immediate stop. Unknown/missing usage, timeout or identity drift also stop. No automatic retries, repair or continuation.','other_usage':'Before run include any intervening account/task spend; cap cannot govern unrelated processes without account reconciliation.','guarantee':'Bounds this dedicated serial run under verified provider limits/rates and complete usage accounting; does not guarantee all300+allQ finish or authoritative invoice total.'},
      'generation_success_records':success,'failure_records':failure}
    dump('BUDGET_RECONCILIATION.json',result)
    dump('PER_REQUEST_SIZE_INVENTORY.json',[{'slot':r['slot'],'group':r['group'],'message_bytes':r['utf8_message_bytes'],'byte_proxy_plus4096':r['utf8_message_bytes']+4096,'output_token_cap':8192,'request_sha256':r['body_sha256']} for r in requests])
    assert all(sha(p)==h for p,h in prior_hashes.items())
    dump('PRESERVATION.json',{'old_preflight_files_checked':len(prior_hashes),'changed':[],'old_hashes':prior_hashes})
    print(json.dumps({k:v for k,v in result.items() if k not in ['generation_success_records','failure_records']},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
