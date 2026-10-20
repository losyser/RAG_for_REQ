"""Freeze five arms. Stdlib only; no model/API executor or credential access."""
import ast
import hashlib
import json
from pathlib import Path
from decimal import Decimal
import statistics
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
V1=OUT.parent/'qualitative_2x2_preflight_20261019'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(x): return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
def read(p): return json.loads(Path(p).read_text(encoding='utf8'))
def dump(n,x): (OUT/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def git(*args): return subprocess.check_output(['git',*args],cwd=ROOT).decode('utf8').strip()
def prohibit_network(event,args):
    if event.startswith('socket.'): raise RuntimeError('Offline preparation prohibits network')

def main():
    sys.addaudithook(prohibit_network)
    assert not (OUT/'VALIDATION.json').exists(),'Do not overwrite frozen v2'
    hist=read(ROOT/'revision_artifacts/bounded_optimization_20261018/protected_before.json')
    paths=[Path(p) for p in hist]+[ROOT/p for p in git('ls-files').splitlines() if (ROOT/p).is_file()]+[p for p in V1.iterdir() if p.is_file()]
    before={str(p):sha(p) for p in paths}
    dump('CHECKPOINT.json',{'head':git('rev-parse','HEAD'),'branch':git('branch','--show-current'),'status':git('status','--short'),'existing_file_hashes':before})
    manifest=read(V1/'INPUT_MANIFEST.json')
    assert all(sha(item['path'])==item['sha256'] for item in manifest.values())
    dump('INPUT_MANIFEST.json',dict(manifest,previous_v1_artifacts={p.name:sha(p) for p in V1.iterdir() if p.is_file()}))
    contexts=read(V1/'CONTEXTS_120.json');orig=read(V1/'SOURCE_REQUIREMENTS_60.json')
    dump('CONTEXTS_120.json',contexts);dump('SOURCE_REQUIREMENTS_60.json',orig)
    old=(V1/'prompt_old.txt').read_text(encoding='utf8')
    addition=('3. 以固定前缀[Q]开头的可检验定性判据：必须有evidence_citations中的有效引用，明确applicable_condition，内容仅限可对应证据原文的摘录或忠实转述，不许可新推导或跨证据综合。不得根据相同数字推断语义支持；机型或工况未知须明确写未知，不能声称适用。无证据或证据不能支持时仍用TBD；空证据不得生成[Q]。\n')
    new=old.replace('只有两种合法内容：','只有三种合法内容：').replace('\n\n严禁写入','\n'+addition+'\n严禁写入')
    tree=ast.parse(Path(manifest['historical_generator']['path']).read_text(encoding='utf8'))
    norag=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='_NORAG_PROMPT' for t in n.targets))
    for n,s in [('prompt_old.txt',old),('prompt_new_q.txt',new),('prompt_norag_original.txt',norag)]: (OUT/n).write_text(s,encoding='utf8')
    assert new.replace('只有三种合法内容：','只有两种合法内容：').replace(addition,'')==old
    reqs={}; groups=['semantic_old','semantic_new','random_old','random_new','norag_original']
    cmap={(c['arm'],c['source_id']):c for c in contexts}
    for sid in sorted(orig):
        for group in groups:
            if group=='norag_original': prompt=norag.format(source_requirement=orig[sid]);context_hash=None
            else:
                arm,variant=group.split('_');c=cmap[arm,sid]
                prompt=(old if variant=='old' else new).format(source_requirement=orig[sid],evidence_block=c['evidence_block']);context_hash=c['sha256']
            body={'model':'deepseek-flash','messages':[{'role':'user','content':prompt}],'temperature':0,'max_tokens':8192,'response_format':{'type':'json_object'},'extra_body':{'thinking':{'type':'disabled'}}}
            reqs[(sid,group)]={'slot':f'{sid}-{group}','source_id':sid,'group':group,'context_sha256':context_hash,'body':body,'body_sha256':digest(body),'utf8_message_bytes':len(prompt.encode())}
    # Rotate five groups over each five sources: each appears equally in each position.
    schedule=[]
    for index,sid in enumerate(sorted(orig)):
        order=groups[index%5:]+groups[:index%5]
        for group in order: schedule.append(dict(reqs[sid,group],execution_index=len(schedule)+1))
    assert len(schedule)==300 and len({r['slot'] for r in schedule})==300
    for group in groups:
        for position in range(5): assert sum(r['group']==group for r in schedule[position::5])==12
    for sid in orig:
        for arm in ['semantic','random']:
            a=reqs[sid,arm+'_old'];b=reqs[sid,arm+'_new']
            assert a['context_sha256']==b['context_sha256']
            assert a['body']['messages'][0]['content']==b['body']['messages'][0]['content'].replace('只有三种合法内容：','只有两种合法内容：').replace(addition,'')
        assert reqs[sid,'norag_original']['body']['messages'][0]['content']==norag.format(source_requirement=orig[sid])
    dump('REQUESTS_300_PENDING.json',schedule)
    dump('SCHEDULE_300.json',[{k:r[k] for k in ['execution_index','slot','source_id','group','body_sha256']} for r in schedule])
    ids=sorted(orig);dump('PILOT_5_PENDING.json',[r for r in schedule if r['source_id']==ids[0]])
    # Match previously frozen tariffs, with independent public Qwen documentation metadata.
    prior=read(ROOT/'revision_artifacts/quarantine_flash_comparison_20261018/ledger.json');reserve=Decimal(prior['reserved_CNY'])
    ds=Decimal(1048576*2+8192*8)/1000000
    qw=(Decimal(30720)*Decimal('2.4')+Decimal(2048)*Decimal('9.6'))/1000000
    costs={'budget_CNY':'50','prior_reserved_CNY':str(reserve),'remaining_CNY':str(50-reserve),'deepseek_pricing_snapshot_date':'2026-10-18',
           'generation_requests':300,'generation_input_tokens_ceiling':300*1048576,'generation_output_tokens_ceiling':300*8192,'generation_per_attempt_CNY':str(ds),'generation_CNY':str(300*ds),
           'qwen_actual_candidate_count':None,'qwen_actual_candidate_count_reason':'No new outputs exist; count ALL literal [Q] candidates including malformed ones across five arms after generation.',
           'qwen_proposed_attempt_cap':1200,'qwen_cap_is_not_row_count_estimate':True,'qwen_input_ceiling_per_attempt':30720,'qwen_output_max_tokens':2048,'qwen_output_tokens_cap':1200*2048,'qwen_per_attempt_CNY':str(qw),'qwen_CNY_formula':f'{qw} * N_Q; N_Q<=1200 required before any judge dispatch',
           'qwen_cap_CNY':str(1200*qw),'combined_new_cap_CNY':str(300*ds+1200*qw),'combined_cumulative_cap_CNY':str(reserve+300*ds+1200*qw),
           'full_design_fits_remaining_budget':False,'max_retries_both_providers':0,
           'failures':'Full reservation retained; stop on first failure, unknown usage or identity drift. No repair/replacement/continuation calls.',
           'qwen_overflow':'If N_Q>1200, block whole judging phase pending revised scope/budget. Do not sample/truncate Q while claiming all-Q review.',
           'pilot_source':ids[0],'pilot_generation_attempts':5,'pilot_generation_CNY':str(5*ds),'pilot_cumulative_generation_CNY':str(reserve+5*ds),'pilot_budget_remaining_after_generation_CNY':str(50-reserve-5*ds),
           'pilot_max_affordable_Q_attempts':int((50-reserve-5*ds)//qw),
           'pilot_Q_note':'Conditional upper budget only, not authorization. Count candidates and freeze actual review bodies first; if above affordable cap, do not start all-Q judge phase.',
           'full_utf8_message_bytes_inventory_only':sum(r['utf8_message_bytes'] for r in schedule)}
    dump('COST_BOUND.json',costs)
    rows=read(ROOT/'data/search_results/exp_v4/rag_v4_results.json')['result_sets'];times=[r['_timing']['generation_s'] for r in rows]
    dump('TIMING_AUDIT.json',{'n':len(times),'mean_seconds':statistics.mean(times),'min_seconds':min(times),'max_seconds':max(times),'refilled_sets':sum(bool(r.get('_refilled_max_tokens')) for r in rows),'registry_mean':read(ROOT/'data/search_results/exp_v4/paper_numbers.json')['timing_s_mean']['generation_s'],'300_times_mean_minutes':statistics.mean(times)*300/60,'source':'Frozen rag_v4_results.json _timing.generation_s; scripts/107_fill_truncated_sets.py overwrites timing for six refill sets','scope':'Historical single RAG generation latency, not full pipeline, not new five-arm latency. Excludes Qwen and manual review; not SLA or randomized variance estimate.'})
    run=subprocess.run([sys.executable,'-B','-m','unittest','-v','test_classifier_v2.py'],cwd=OUT,capture_output=True,text=True,encoding='utf8')
    (OUT/'TEST_RESULTS.txt').write_text(run.stdout+run.stderr,encoding='utf8');assert run.returncode==0,run.stdout+run.stderr
    changed=[p for p,h in before.items() if sha(p)!=h];assert not changed,changed
    dump('VALIDATION.json',{'status':'PASS_OFFLINE_PENDING_APPROVAL','unit_tests':21,'sources':60,'saved_contexts':120,'generation_slots':300,'groups':{g:60 for g in groups},'paired_prompt_only_differences_checked':120,'each_group_each_execution_position_count':12,'semantic_empty_context_sources':[c['source_id'] for c in contexts if c['arm']=='semantic' and not c['saved_id_order']],'old_v1_unchanged':True,'existing_protected_files_checked':len(before),'changed':changed,'model_calls':0,'Qwen_calls':0,'human_tasks_started':0,'note':'Public official Qwen documentation read separately, without project content; no model API access.'})
    dump('ARTIFACT_HASHES.json',{p.name:sha(p) for p in OUT.iterdir() if p.is_file() and p.name!='ARTIFACT_HASHES.json'})
    print(json.dumps(costs,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
