"""Offline freezer only. No SDK, network, credentials, or execution path."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
from decimal import Decimal

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
BASE = ROOT.parent / 'local_git_baselines/before_paper_minor_revision_20261017_005236/project/cooling_rag_mg/structured_req_generator.py'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(name, obj): (OUT/name).write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
def git(*args): return subprocess.check_output(['git', *args], cwd=ROOT).decode('utf8').strip()
def digest(obj): return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True).encode()).hexdigest()

def main():
    assert not (OUT/'VALIDATION.json').exists(), 'Frozen output already exists; do not overwrite'
    historical = json.loads((ROOT/'revision_artifacts/bounded_optimization_20261018/protected_before.json').read_text())
    paths = [Path(p) for p in historical]
    paths += [ROOT/p for p in git('ls-files').splitlines() if (ROOT/p).is_file()]
    before = {str(p):sha(p) for p in paths}
    dump('CHECKPOINT.json', {'head':git('rev-parse','HEAD'), 'branch':git('branch','--show-current'), 'status':git('status','--short'), 'hashes':before})
    dump('HISTORICAL_BASELINE_COMPARISON.json', {'count':len(historical), 'preexisting_differences':[p for p,h in historical.items() if sha(p)!=h]})
    tree=ast.parse(BASE.read_text(encoding='utf8'))
    template=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='_STRUCTURED_GEN_PROMPT' for t in n.targets))
    fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_build_evidence_block')
    env={'_MAX_EVIDENCE_ITEMS':12,'_EU_TEXT_LIMIT':500}
    exec(compile(ast.Module(body=[fn],type_ignores=[]),str(BASE),'exec'),env)
    addition='3. 来自所引证据直接支持、可通过检查或试验验证的非数值定性判据；明确对象、行为及证据给出的适用条件，在 evidence_citations 中引用对应证据。不得把数字相同视为语义支持，不得推断未记录的机型或工况；缺失的数值仍用TBD，适用性未知须明确写未知。\n'
    new=template.replace('只有两种合法内容：','只有三种合法内容：').replace('\n\n严禁写入', '\n'+addition+'\n严禁写入')
    assert new.replace('只有三种合法内容：','只有两种合法内容：').replace(addition,'')==template
    (OUT/'prompt_old.txt').write_text(template,encoding='utf8')
    (OUT/'prompt_new.txt').write_text(new,encoding='utf8')
    kbpath=ROOT/'data/processed/evidence_units_v3_audited.jsonl'
    origpath=ROOT/'data/processed/original_requirements_v2.jsonl'
    kb={r['id']:r for r in map(json.loads,kbpath.read_text(encoding='utf8').splitlines())}
    orig={r['requirement_id']:r['requirement_text'] for r in map(json.loads,origpath.read_text(encoding='utf8').splitlines())}
    inputs={'historical_generator':{'path':str(BASE),'sha256':sha(BASE)},'KB':{'path':str(kbpath),'sha256':sha(kbpath)},'source_requirements':{'path':str(origpath),'sha256':sha(origpath)}}
    contexts=[];requests=[];idsets=[]
    for arm,file in [('semantic','rag_v4_results.json'),('random','ablation_random_retrieval_results.json')]:
        p=ROOT/'data/search_results/exp_v4'/file
        inputs[arm]={'path':str(p),'sha256':sha(p)}
        rows=json.loads(p.read_text(encoding='utf8'))['result_sets'];idsets.append({r['source_requirement_id'] for r in rows})
        for r in sorted(rows,key=lambda r:r['source_requirement_id']):
            sid=r['source_requirement_id']; vals=r['_evidence_values']
            assert all(e in kb for e in vals)
            annotated=[dict(kb[e],_extracted_values=v) for e,v in vals.items()]
            selected=([e for e in annotated if e['_extracted_values']]+[e for e in annotated if not e['_extracted_values']])[:12]
            block=env['_build_evidence_block'](annotated) or '（无检索证据）'
            context={'arm':arm,'source_id':sid,'source_requirement':orig[sid],'saved_evidence_values':vals,'saved_id_order':list(vals),'selected_ids':[e['id'] for e in selected],'evidence_block':block}
            context['sha256']=digest(context); contexts.append(context)
            for variant,t in [('old',template),('new',new)]:
                body={'model':'deepseek-flash','messages':[{'role':'user','content':t.format(source_requirement=orig[sid],evidence_block=block)}],'temperature':0,'max_tokens':8192,'response_format':{'type':'json_object'},'extra_body':{'thinking':{'type':'disabled'}}}
                requests.append({'slot':f'{arm}-{sid}-{variant}','arm':arm,'source_id':sid,'variant':variant,'context_sha256':context['sha256'],'body':body,'body_sha256':digest(body),'utf8_message_bytes':len(body['messages'][0]['content'].encode('utf8'))})
    assert idsets[0]==idsets[1] and len(idsets[0])==60
    assert len(contexts)==120 and len(requests)==240
    assert [c['source_id'] for c in contexts if c['arm']=='semantic' and not c['saved_id_order']]==['OR035','OR058']
    pilot_id=sorted(idsets[0])[0]
    pilot=[r for r in requests if r['source_id']==pilot_id]
    assert len(pilot)==4
    for a,b in zip(requests[::2],requests[1::2]):
        assert a['context_sha256']==b['context_sha256']
        assert a['body']['messages'][0]['content']==b['body']['messages'][0]['content'].replace('只有三种合法内容：','只有两种合法内容：').replace(addition,'')
        assert {k:v for k,v in a['body'].items() if k!='messages'}=={k:v for k,v in b['body'].items() if k!='messages'}
    ledger=ROOT/'revision_artifacts/quarantine_flash_comparison_20261018/ledger.json'
    reserved=Decimal(json.loads(ledger.read_text())['reserved_CNY']); per=Decimal(1048576*2+8192*8)/1000000
    costs={'pricing_date':'2026-10-18','provider':'DeepSeek','base_url':'https://api.deepseek.com','endpoint':'/chat/completions','model':'deepseek-flash','historical_snapshot_version':'DeepSeek-V4.1-Flash-1017','rates_CNY_per_million':{'input_cache_miss':2,'output':8},'input_ceiling_per_attempt':1048576,'output_ceiling_per_attempt':8192,'per_attempt_reserved_CNY':str(per),'prior_ledger_sha256':sha(ledger),'prior_reservation_CNY':str(reserved),'remaining_CNY':str(50-reserved),'full_240_input_ceiling':240*1048576,'full_240_output_ceiling':240*8192,'full_240_CNY':str(240*per),'pilot_source_id':pilot_id,'pilot_attempts':4,'pilot_CNY':str(4*per),'pilot_cumulative_CNY':str(reserved+4*per),'pilot_remaining_CNY':str(50-reserved-4*per),'max_retries':0,'failure_policy':'A failed attempt consumes its full reservation; stop immediately, no replacement or repair calls. Existing failures retain reservations.','token_estimation':'UTF-8 lengths are inventory only, NOT verified tokenizer counts. Financial bound uses full documented context ceiling; no cache/offpeak credit. Rates/context must be reconfirmed before an authorized run.','full_utf8_message_bytes':sum(r['utf8_message_bytes'] for r in requests),'pilot_utf8_message_bytes':sum(r['utf8_message_bytes'] for r in pilot)}
    dump('INPUT_MANIFEST.json',inputs);dump('CONTEXTS_120.json',contexts);dump('REQUESTS_240_PENDING.json',requests);dump('PILOT_4_PENDING.json',pilot);dump('COST_BOUND.json',costs)
    dump('SOURCE_REQUIREMENTS_60.json',{k:orig[k] for k in sorted(idsets[0])})
    changed=[p for p,h in before.items() if sha(p)!=h]
    assert not changed, changed
    dump('VALIDATION.json',{'status':'PASS_OFFLINE_PENDING_AUTHORIZATION','assertions':['60 identical source IDs in both arms','120 frozen contexts / 240 request bodies','4 pilot slots selected by lexicographic source ID only','all saved evidence IDs exist in frozen KB','OR035 and OR058 semantic evidence empty','all 120 old/new pairs differ only in category heading and third-category text','all other request parameters identical','no protected or tracked existing file changed'],'protected_and_tracked_unique_files':len(before),'changed':changed,'network_calls':0,'model_calls':0,'sdk_imports':0,'historical_manifest_count':len(historical)})
    dump('ARTIFACT_HASHES.json',{p.name:sha(p) for p in OUT.iterdir() if p.is_file() and p.name!='ARTIFACT_HASHES.json'})
    print(json.dumps(costs,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
