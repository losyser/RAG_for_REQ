"""Capture real entrypoint requests with fake clients. No runnable API sender."""
import copy
import hashlib
import json
from pathlib import Path
import socket
import subprocess
import sys
from types import ModuleType, SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
WORK = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True


def blocked(*a, **kw):
    raise RuntimeError('offline prompt freeze: networking/repair blocked')


socket.socket.connect = socket.socket.connect_ex = socket.create_connection = blocked
OLD = '07a316ab8fd6e2aff4d78282f556f5fe2c308ae2'
NEW = '6de9afc02f5f9b524531c3b272ce82d9194a4d79'
MIXED = 'numeric-first-reserve-one-nonnumeric-v1'
RISK = 'independent-reference-quantity-applicability-v1'
CURRENT_MODEL = 'deepseek-chat'  # Frozen configured alias, retired; NOT runnable.


def module_at(commit, filename):
    mod = ModuleType('frozen_' + commit[:7] + '_' + Path(filename).stem)
    mod.__package__ = 'cooling_rag_mg'
    sys.modules[mod.__name__] = mod
    code = subprocess.check_output(['git', 'show', commit + ':' + filename], cwd=ROOT).decode('utf-8')
    exec(compile(code, 'git:' + commit + ':' + filename, 'exec'), mod.__dict__)
    return mod


kb = {r['id']:r for r in map(json.loads,(ROOT/'data/processed/evidence_units_v3_audited.jsonl').read_text('utf-8').splitlines())}
v4 = json.loads((ROOT/'data/search_results/exp_v4/rag_v4_results.json').read_text('utf-8'))
ors = {r['requirement_id']:r['requirement_text'] for r in map(json.loads,(ROOT/'data/processed/original_requirements_v2.jsonl').read_text('utf-8').splitlines())}
batch = ROOT/'data/search_results/batch_20260730_164747/all_requirements_results.json'
ui = json.loads(batch.read_text('utf-8'))
reasons = {'OR001':'Previously frozen TBD placeholder defect; no reselection using new scores.',
           'OR010':'Previously frozen dGH unit-recognition defect.',
           'OR023':'Previously frozen -100 C source-risk case; local original edition unmatched.',
           'R001':'First of three consecutively preselected saved UI cases in batch_20260730_164747.',
           'R002':'Second preselected UI case in the same saved batch; no quality-based selection.',
           'R003':'Third preselected UI case in the same saved batch; no quality-based selection.'}
captured = []
for commit, arm in ((OLD,'old'), (NEW,'new')):
    contract = module_at(commit, 'cooling_rag_mg/evidence_contracts.py')
    gen = module_at(commit, 'cooling_rag_mg/structured_req_generator.py')
    gen.select_evidence = contract.select_evidence
    gen._MAX_EVIDENCE_ITEMS, gen._EU_TEXT_LIMIT = 12, 500
    agent = module_at(commit, 'cooling_rag_mg/engineering_requirement_agent.py')
    # The UI compaction helper is byte-identical across these two commits.
    assert subprocess.check_output(['git','show',OLD+':cooling_rag_mg/ui_evidence_contracts.py']) == subprocess.check_output(['git','show',NEW+':cooling_rag_mg/ui_evidence_contracts.py'])
    agent.repair_json_with_deepseek = blocked
    for rid in ('OR001','OR010','OR023','R001','R002','R003'):
        requests = []
        def completion(*a, **kw):
            requests.append(copy.deepcopy(kw))
            raw = '{"shalls":[]}' if rid.startswith('OR') else '{"engineering_requirements":[]}'
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=raw))])
        if rid.startswith('OR'):
            saved = next(r for r in v4['result_sets'] if r['source_requirement_id']==rid)
            evidence = [{**kb[eid], '_extracted_values':values} for eid,values in saved['_evidence_values'].items() if eid in kb]
            client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=completion)))
            opts = {} if arm=='old' else {'selection_policy':MIXED, 'risk_policy':RISK}
            gen.generate_structured_shalls(ors[rid], evidence, client, CURRENT_MODEL, max_tokens=8192, **opts)
            entry = 'generate_structured_shalls'
            selected = contract.select_evidence(evidence,12,**({'policy':MIXED} if arm=='new' else {}))
            source_ids = [e['id'] for e in selected]
        else:
            saved = next(r for r in ui['requirements'] if r['requirement_id']==rid)
            requirement = {'requirement_id':rid,'requirement_text':saved['raw_requirement_text'], 'stakeholder':saved.get('stakeholder','')}
            agent.get_config = lambda: SimpleNamespace(deepseek=SimpleNamespace(enabled=True, model=CURRENT_MODEL,
                temperature=0.0, max_tokens_requirement_agent=8192, make_client=lambda:object()))
            agent.cached_completion = completion  # bypass disk cache; no network; no API client
            opts = {} if arm=='old' else {'risk_policy':RISK}
            agent.generate_engineering_requirements_for_requirement(requirement, ui, **opts)
            entry = 'generate_engineering_requirements_for_requirement -> build_graph'
            source_ids = [e['id'] for e in agent.compact_requirement_context(saved)['supported_evidence']]
        assert len(requests)==1, (rid,arm,len(requests))
        req = requests[0]
        # Stub completion's positional client is deliberately not part of this serializable body.
        blob = json.dumps(req,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
        chars = sum(len(m['content']) for m in req['messages'])
        byte_count = sum(len(m['content'].encode('utf-8')) for m in req['messages'])
        captured.append({'case':rid,'arm':arm,'commit':commit,'reason':reasons[rid], 'entrypoint':entry,
            'explicit_options':opts,'selected_ids':source_ids,'prompt_chars':chars,'prompt_utf8_bytes':byte_count,
            'request_utf8_bytes':len(blob),'request_sha256':hashlib.sha256(blob).hexdigest(),
            'input_token_planning_ceiling':byte_count+4096,'max_output_tokens':8192,'request':req})

pairs=[]
for rid in reasons:
    old,new=[next(r for r in captured if r['case']==rid and r['arm']==arm) for arm in ('old','new')]
    pairs.append({'case':rid,'messages_identical':old['request']['messages']==new['request']['messages'],
                  'selected_ids_identical':old['selected_ids']==new['selected_ids']})
report={'status':'BLOCKED_RETIRED_MODEL_AND_PENDING_EGRESS_APPROVAL','base_url':'https://api.deepseek.com',
        'model':CURRENT_MODEL, 'old_commit':OLD,'new_commit':NEW,
        'token_method':'Not measured. Conservative byte-fallback planning envelope = UTF-8 message bytes + 4096 framing reserve per request. Not a verified tokenizer bound for the retired alias; active-model tokenizer/template must be verified before execution.',
        'requests':captured,'pairs':pairs,'totals':{'requests':len(captured),
        'prompt_chars':sum(r['prompt_chars'] for r in captured),'prompt_utf8_bytes':sum(r['prompt_utf8_bytes'] for r in captured),
        'input_token_planning_ceiling':sum(r['input_token_planning_ceiling'] for r in captured),
        'max_output_tokens':sum(r['max_output_tokens'] for r in captured)}}
(WORK/'FROZEN_PROMPT_PLAN.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
for r in captured:
    print(r['case'],r['arm'],r['prompt_chars'],r['prompt_utf8_bytes'],r['input_token_planning_ceiling'],r['request_sha256'][:12])
print(json.dumps(report['totals']))
print(json.dumps(pairs))
manifest=json.loads((WORK/'protected_before.json').read_text('utf-8'))
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in manifest.items())
print('Protected hashes unchanged; no model/API calls.')
