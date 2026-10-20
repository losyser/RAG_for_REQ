"""Frozen saved-output diagnostics only. No model, retrieval index or historical writes."""
import copy
import hashlib
import json
from pathlib import Path
import socket
import sys

ROOT = Path(__file__).resolve().parents[2]
WORK = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True


def offline(*a, **kw):
    raise RuntimeError('network disabled')


socket.socket.connect = socket.socket.connect_ex = socket.create_connection = offline
from cooling_rag_mg.evidence_contracts import select_evidence, MIXED_SELECTION_POLICY
from cooling_rag_mg.generation_risks import annotate_generation_risks, RISK_POLICY
from cooling_rag_mg.engineering_requirement_agent import compact_requirement_context, normalize_agent_output

kb_path = ROOT / 'data/processed/evidence_units_v3_audited.jsonl'
kb = {e['id']: e for e in map(json.loads, kb_path.read_text('utf-8').splitlines())}
v4_path = ROOT / 'data/search_results/exp_v4/rag_v4_results.json'
v4 = json.loads(v4_path.read_text('utf-8'))
selection = []
fixed = []
for record in v4['result_sets']:
    ev = [{**kb[eid], '_extracted_values': values} for eid, values in record.get('_evidence_values', {}).items() if eid in kb]
    old, new = select_evidence(ev), select_evidence(ev, policy=MIXED_SELECTION_POLICY)
    old_ids, new_ids = [e['id'] for e in old], [e['id'] for e in new]
    selection.append({'source': record['source_requirement_id'], 'legacy': old_ids, 'optional': new_ids,
                      'removed': [i for i in old_ids if i not in new_ids], 'added': [i for i in new_ids if i not in old_ids]})
    if record['source_requirement_id'] in ('OR001', 'OR010', 'OR023'):
        rows = copy.deepcopy(record['engineering_requirements'])
        annotated = annotate_generation_risks(rows, new, policy=RISK_POLICY)
        assert all({k: v for k, v in r.items() if k != '_independent_risks'} == old
                   for r, old in zip(annotated, rows))
        fixed.append({'source': record['source_requirement_id'], 'kind': 'saved_v4',
                      'input_sha256': hashlib.sha256(v4_path.read_bytes()).hexdigest(),
                      'risks': [r['_independent_risks'] for r in annotated], 'rows': len(rows),
                      'criteria_unchanged': True})

batch = ROOT / 'data/search_results/batch_20260730_164747'
retrieval = json.loads((batch / 'all_requirements_results.json').read_text('utf-8'))
contexts = {r['requirement_id']: compact_requirement_context(r)['supported_evidence'] for r in retrieval['requirements']}
for path in sorted(batch.glob('engineering_requirements_*/engineering_requirements.json')):
    data = json.loads(path.read_text('utf-8'))
    for record in data['requirement_sets']:
        rid = record['source_requirement_id']
        if rid not in ('R001', 'R002', 'R003'):
            continue
        old = normalize_agent_output(copy.deepcopy(record), rid, evidence_scope=contexts.get(rid))
        new = normalize_agent_output(copy.deepcopy(record), rid, evidence_scope=contexts.get(rid), risk_policy=RISK_POLICY)
        assert len(old['engineering_requirements']) == len(new['engineering_requirements'])
        assert [r['acceptance_criteria'] for r in old['engineering_requirements']] == [r['acceptance_criteria'] for r in new['engineering_requirements']]
        fixed.append({'source': rid, 'kind':'saved_ui', 'path':str(path.relative_to(ROOT)),
                      'input_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                      'rows':len(new['engineering_requirements']), 'criteria_unchanged':True,
                      'risks':[r['_independent_risks'] for r in new['engineering_requirements']]})

manifest = json.loads((WORK / 'protected_before.json').read_text('utf-8'))
after = {p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in manifest}
assert manifest == after
dirty = json.loads((WORK / 'dirty_before.json').read_text('utf-8'))
assert all(hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h for p,h in dirty.items())
(WORK / 'protected_after.json').write_text(json.dumps(after, indent=2), 'utf-8')
report = {'no_network':True, 'no_generation':True, 'selection_input_order':'saved _evidence_values insertion order; not reconstructed retrieval rank',
          'selection':selection, 'fixed_cases':fixed, 'protected_files':len(after), 'protected_changed':[],
          'unrelated_dirty_changed':[], 'summary':{'selection_sets':len(selection),
          'selection_changed':sum(s['legacy'] != s['optional'] for s in selection),
          'fixed_saved_records':len(fixed), 'fixed_sources':sorted({r['source'] for r in fixed}),
          'fixed_rows':sum(r['rows'] for r in fixed)}}
assert set(report['summary']['fixed_sources']) == {'OR001','OR010','OR023','R001','R002','R003'}
(WORK / 'SAVED_REPLAY.json').write_text(json.dumps(report, ensure_ascii=False, indent=2),'utf-8')
print(json.dumps(report['summary'], ensure_ascii=False))
print('366 historical hashes and all pre-existing dirty tracked hashes unchanged')
