"""Read local journals only; never controls or restarts an execution process."""
from datetime import datetime,timezone
from decimal import Decimal
from pathlib import Path
import json
from runner import WORK,PROVIDERS,reserve,atomic,read

def main():
    result={'checked_at_UTC':datetime.now(timezone.utc).isoformat(),'cap_CNY':'50','safety_buffer_CNY':'1','source':'local durable journals; monitor separately polls existing process session'}
    for phase in ['generation','review']:
        folder=WORK/phase;attempts=sorted(folder.glob('*_attempt.json'));files=sorted(folder.glob('*_response.json'));responses=[]
        for p in files:
            try:responses.append(read(p))
            except json.JSONDecodeError:pass  # A file may still be receiving its first exclusive write.
        try:last=read(attempts[-1]) if attempts else {}
        except json.JSONDecodeError:last={}
        state=read(folder/'state.json') if (folder/'state.json').exists() else {}
        inflight=len(attempts)-len(responses)
        result[phase]={'sent_or_reserved':len(attempts),'success':sum(r['status']=='completed' for r in responses),'failed':sum(r['status']!='completed' for r in responses),'inflight':inflight,'last_dispatch_UTC':last.get('started_at'),'last_response_UTC':responses[-1].get('finished_at') if responses else None,'state':state.get('status','not_started'),'last_recorded_debit_CNY':state.get('debit_CNY',state.get('prior_debit_CNY')),'lock_present':(folder/'RUNNING.lock').exists()}
    atomic(WORK/'LIVE_STATUS.json',result);print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
