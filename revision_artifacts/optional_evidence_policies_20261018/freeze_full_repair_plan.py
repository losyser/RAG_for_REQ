"""Full-repair prompt comparison: read old builders only, mock current entrypoints."""
import ast
import copy
import difflib
import hashlib
import json
from decimal import Decimal
from pathlib import Path
import socket
import subprocess
import sys
from types import ModuleType, SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
WORK = Path(__file__).resolve().parent / 'full_repair_comparison'
WORK.mkdir(exist_ok=True)
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True


def blocked(*a, **kw):
    raise RuntimeError('offline only: network and model repair disabled')


socket.socket.connect = socket.socket.connect_ex = socket.create_connection = blocked
OLD = '3659d37ed21a2f286027f2603b171f2ad22565fe'
NEW = '6de9afc02f5f9b524531c3b272ce82d9194a4d79'
NEW_DOC_HEAD = '7e4a5aec608e74d69e74da590bd359d74d056916'
MODEL = 'deepseek-flash'
MIXED = 'numeric-first-reserve-one-nonnumeric-v1'
RISK = 'independent-reference-quantity-applicability-v1'
source_hashes = {}


def source_at(commit, filename):
    raw = subprocess.check_output(['git','show',commit+':'+filename], cwd=ROOT)
    source_hashes[commit+':'+filename] = hashlib.sha256(raw).hexdigest()
    return raw.decode('utf-8')


def old_builders(filename, names, namespace):
    tree = ast.parse(source_at(OLD, filename))
    nodes = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in names:
            nodes.append(node)
        elif isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in names for t in node.targets):
            nodes.append(node)
    mod = ModuleType('pure_old_'+Path(filename).stem)
    mod.__dict__.update(namespace)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), 'git:pure-builders:'+filename, 'exec'), mod.__dict__)
    assert not hasattr(mod,'generate_structured_shalls') and not hasattr(mod,'build_graph')
    return mod, tree


def new_module(filename):
    mod = ModuleType('new_'+Path(filename).stem)
    mod.__package__ = 'cooling_rag_mg'
    sys.modules[mod.__name__] = mod
    exec(compile(source_at(NEW,filename),'git:new:'+filename,'exec'),mod.__dict__)
    return mod


from typing import Any
from cooling_rag_mg.schema import normalize_v2_metadata
from cooling_rag_mg.text_utils import safe_text, truncate
for dependency in ('cooling_rag_mg/schema.py','cooling_rag_mg/text_utils.py'):
    assert source_at(OLD,dependency)==source_at(NEW,dependency)
old_gen, _ = old_builders('cooling_rag_mg/structured_req_generator.py',
    {'_STRUCTURED_GEN_PROMPT','_build_evidence_block'}, {'_MAX_EVIDENCE_ITEMS':12,'_EU_TEXT_LIMIT':500})
old_ui, ui_tree = old_builders('cooling_rag_mg/engineering_requirement_agent.py',
    {'ENGINEERING_REQUIREMENT_PROMPT','compact_evidence','_group_evidence_by_type','compact_requirement_context'},
    {'Any':Any,'normalize_v2_metadata':normalize_v2_metadata,'safe_text':safe_text,'truncate':truncate})
# Evaluate ONLY the old messages expression, not call_deepseek or any old client code.
call_node = next(n for n in ast.walk(ui_tree) if isinstance(n,ast.FunctionDef) and n.name=='call_deepseek')
completion_node = next(n for n in ast.walk(call_node) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='cached_completion')
messages_expr = next(k.value for k in completion_node.keywords if k.arg=='messages')
old_ui_messages = compile(ast.Expression(messages_expr),'git:old-ui-messages-expression','eval')
new_gen = new_module('cooling_rag_mg/structured_req_generator.py')
new_contract = new_module('cooling_rag_mg/evidence_contracts.py')
new_gen.select_evidence = new_contract.select_evidence
new_gen._MAX_EVIDENCE_ITEMS, new_gen._EU_TEXT_LIMIT = 12, 500
new_ui = new_module('cooling_rag_mg/engineering_requirement_agent.py')
new_ui.repair_json_with_deepseek = blocked

input_hashes = {}
def read_input(path, jsonl=False):
    raw=(ROOT/path).read_bytes()
    input_hashes[path]=hashlib.sha256(raw).hexdigest()
    return list(map(json.loads,raw.decode('utf-8').splitlines())) if jsonl else json.loads(raw)

kb={r['id']:r for r in read_input('data/processed/evidence_units_v3_audited.jsonl',True)}
ors={r['requirement_id']:r['requirement_text'] for r in read_input('data/processed/original_requirements_v2.jsonl',True)}
v4=read_input('data/search_results/exp_v4/rag_v4_results.json')
ui=read_input('data/search_results/batch_20260730_164747/all_requirements_results.json')
reasons={'OR001':'Fixed prior TBD placeholder boundary','OR010':'Fixed prior dGH unit boundary',
         'OR023':'Fixed prior suspicious -100 C source value; exact original unmatched',
         'R001':'First preselected UI record in batch_20260730_164747',
         'R002':'Second preselected UI record in same batch','R003':'Third preselected UI record in same batch'}
requests=[]
pairs=[]
for rid in reasons:
    captured=[]
    def completion(*a,**kw):
        captured.append(copy.deepcopy(kw))
        raw='{"shalls":[]}' if rid.startswith('OR') else '{"engineering_requirements":[]}'
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=raw))])
    if rid.startswith('OR'):
        saved=next(r for r in v4['result_sets'] if r['source_requirement_id']==rid)
        evidence=[{**kb[eid],'_extracted_values':values} for eid,values in saved['_evidence_values'].items() if eid in kb]
        old_messages=[{'role':'user','content':old_gen._STRUCTURED_GEN_PROMPT.format(source_requirement=ors[rid],evidence_block=old_gen._build_evidence_block(evidence) or '（无检索证据）')}]
        old_ids=[e['id'] for e in ( [e for e in evidence if e.get('_extracted_values')] + [e for e in evidence if not e.get('_extracted_values')] )[:12]]
        client=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=completion)))
        opts={'selection_policy':MIXED,'risk_policy':RISK}
        new_gen.generate_structured_shalls(ors[rid],evidence,client,MODEL,max_tokens=8192,**opts)
        new_ids=[e['id'] for e in new_contract.select_evidence(evidence,12,policy=MIXED)]
        counts={}
    else:
        saved=next(r for r in ui['requirements'] if r['requirement_id']==rid)
        requirement={'requirement_id':rid,'requirement_text':saved['raw_requirement_text'],'stakeholder':saved.get('stakeholder','')}
        before=old_ui.compact_requirement_context(copy.deepcopy(saved))
        after=new_ui.compact_requirement_context(copy.deepcopy(saved))
        payload={'original_requirement':requirement,'retrieval_context':before}
        old_messages=eval(old_ui_messages,{'json':json,'payload':payload,'ENGINEERING_REQUIREMENT_PROMPT':old_ui.ENGINEERING_REQUIREMENT_PROMPT})
        old_ids,new_ids=([e['id'] for e in ctx['supported_evidence']] for ctx in (before,after))
        counts={'old_evidence_body_chars':sum(len(e['text']) for e in before['supported_evidence']),
                'new_evidence_body_chars':sum(len(e['text']) for e in after['supported_evidence']),
                'old_ellipsis_bodies':sum(e['text']=='...' for e in before['supported_evidence']),
                'new_partial_bodies':sum(e.get('_context_status')=='partial_unknown' for e in after['supported_evidence'])}
        new_ui.get_config=lambda:SimpleNamespace(deepseek=SimpleNamespace(enabled=True,model=MODEL,temperature=0.0,
            max_tokens_requirement_agent=8192,make_client=lambda:object()))
        new_ui.cached_completion=completion
        opts={'risk_policy':RISK}
        new_ui.generate_engineering_requirements_for_requirement(requirement,ui,**opts)
    assert len(captured)==1
    new_request=captured[0]
    old_request={'model':MODEL,'messages':old_messages,'temperature':0,'max_tokens':8192,'response_format':{'type':'json_object'}}
    pair={'case':rid,'messages_identical':old_messages==new_request['messages'],
          'selected_ids_identical':old_ids==new_ids,'old_ids':old_ids,'new_ids':new_ids,**counts}
    texts=[]
    for arm,commit,req,ids in [('old',OLD,old_request,old_ids),('new',NEW,new_request,new_ids)]:
        # Shared transport adapter only: both arms explicitly non-thinking.
        req['extra_body']={'thinking':{'type':'disabled'}}
        blob=json.dumps(req,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
        chars=sum(len(m['content']) for m in req['messages'])
        bytes_=sum(len(m['content'].encode('utf-8')) for m in req['messages'])
        text='\n\n'.join('['+m['role']+']\n'+m['content'] for m in req['messages'])
        texts.append(text)
        requests.append({'case':rid,'arm':arm,'commit':commit,'reason':reasons[rid], 'selected_ids':ids,
            'options':{} if arm=='old' else opts,'prompt_chars':chars,'prompt_utf8_bytes':bytes_,
            'input_token_planning_ceiling':bytes_+4096,'max_output_tokens':8192,
            'request_utf8_bytes':len(blob),'request_sha256':hashlib.sha256(blob).hexdigest(),'request':req})
    (WORK/(rid+'.diff')).write_text(''.join(difflib.unified_diff(texts[0].splitlines(True),texts[1].splitlines(True),fromfile=OLD+'/'+rid,tofile=NEW+'/'+rid,n=2)),'utf-8')
    pairs.append(pair)

total_in=sum(r['input_token_planning_ceiling'] for r in requests)
total_out=sum(r['max_output_tokens'] for r in requests)
usd=(Decimal(total_in)*Decimal('0.3')+Decimal(total_out)*Decimal('1.2'))/Decimal(1000000)
context_reserve_usd=(Decimal(12*1048576)*Decimal('0.3')+Decimal(total_out)*Decimal('1.2'))/Decimal(1000000)
report={'status':'PENDING_EGRESS_APPROVAL_TOKENIZER_AND_CNY_SETTLEMENT_VERIFICATION','model':MODEL,
    'base_url':'https://api.deepseek.com','old_commit':OLD,'new_code_commit':NEW,'new_document_head':NEW_DOC_HEAD,
    'token_method':'UTF8 content bytes + 4096 framing reserve; conservative planning, not matching tokenizer measurement',
    'requests':requests,'pairs':pairs,'source_hashes':source_hashes,'input_file_hashes':input_hashes,
    'controls':{'max_requests_including_retries':12,'sdk_max_retries':0,'outer_retries':0,'json_repair_calls':0,
                'http_timeout_seconds':{'connect':10,'read':120,'write':30,'pool':10},'budget_CNY':'50',
                'initial_reservations_CNY_max':'40','unallocated_margin_CNY':'10','retry_reservation_CNY':'0'},
    'totals':{'requests':len(requests),'prompt_chars':sum(r['prompt_chars'] for r in requests),
              'prompt_utf8_bytes':sum(r['prompt_utf8_bytes'] for r in requests),'input_token_planning_ceiling':total_in,
              'max_output_tokens':total_out,'peak_cache_miss_USD_planning_cost':str(usd),
              'conservative_provider_context_input_cap_per_attempt':1048576,
              'provider_context_peak_USD_reservation':str(context_reserve_usd)}}
(WORK/'FROZEN_PLAN.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
for r in requests:
    print(r['case'],r['arm'],r['prompt_chars'],r['prompt_utf8_bytes'],r['input_token_planning_ceiling'])
print(json.dumps(report['totals']))
print(json.dumps(pairs))
manifest=json.loads((WORK.parent/'protected_before.json').read_text('utf-8'))
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in manifest.items())
dirty=json.loads((WORK.parent/'dirty_before.json').read_text('utf-8'))
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in dirty.items())
print('366 protected hashes and all preexisting dirty tracked hashes match; network blocked.')
