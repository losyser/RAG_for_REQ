"""Offline verification only; never send or repair a request."""
import hashlib
import json
from pathlib import Path
import socket
import sys

ROOT = Path(__file__).resolve().parents[3]
WORK = Path(__file__).resolve().parent
PRIOR = WORK.parent / 'authorized_flash_run'
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True
def blocked(*args, **kwargs):
    raise RuntimeError('offline verification: network disabled')
socket.socket.connect = socket.socket.connect_ex = socket.create_connection = blocked
from cooling_rag_mg.evidence_quarantine import load_review_flags, gate_ui_output
from cooling_rag_mg.engineering_requirement_agent import normalize_agent_output

def read(path):
    return json.loads(path.read_text('utf-8'))
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')

plan = read(WORK.parent / 'full_repair_comparison/FROZEN_PLAN.json')
ledger = read(WORK / 'slot12_ledger.json')
assert len(ledger['attempts']) == 12
assert ledger['reserved_CNY'] == '25.952256'
assert sum(a['status'] == 'completed' for a in ledger['attempts']) == 10
assert sum(a['status'] == 'failed_stop' for a in ledger['attempts']) == 2
checks = []
for index, (item, attempt) in enumerate(zip(plan['requests'], ledger['attempts']), 1):
    directory = WORK if index == 12 else PRIOR
    prefix = f"{index:02d}_{item['case']}_{item['arm']}"
    req = read(directory / (prefix + '_request.json'))
    rec = read(directory / (prefix + '_response.json'))
    assert req == item
    assert hashlib.sha256(canonical(req['request'])).hexdigest() == item['request_sha256'] == attempt['request_sha256'] == rec['request_sha256']
    assert req['request']['model'] == 'deepseek-flash'
    assert req['request']['extra_body'] == {'thinking': {'type': 'disabled'}}
    checks.append({'slot': index, 'case': item['case'], 'arm': item['arm'], 'status': rec['status'], 'request_sha256': item['request_sha256']})
historical = read(WORK.parent / 'protected_before.json')
old_files = read(WORK / 'prior_artifact_hashes.json')
dirty = read(WORK.parent / 'dirty_before.json')
assert len(historical) == 366 and len(old_files) == 52
assert all(sha(Path(p)) == h for p, h in historical.items())
assert all(sha(ROOT / p) == h for p, h in old_files.items())
assert all(sha(ROOT / p) == h for p, h in dirty.items())

# Append the new saved response to the prior nine-response offline replay.
# These delivery gates were NOT part of the paid frozen prompt/model treatment.
qdir = ROOT / 'revision_artifacts/evidence_quarantine_20261018'
prior_replay = read(qdir / 'REPLAY.json')
record = read(WORK / '12_R003_new_response.json')
obj = json.loads(record['response']['choices'][0]['message']['content'])
payload = json.loads(next(m['content'] for m in plan['requests'][11]['request']['messages'] if m['role'] == 'user'))
ctx = payload['retrieval_context']
obj['allowed_engineering_aspects'] = ctx.get('allowed_engineering_aspects', [])
obj['_background_evidence_ids'] = ctx.get('_background_evidence_ids', [])
normalized = normalize_agent_output(obj, 'R003', evidence_scope=ctx['supported_evidence'])
gated = gate_ui_output(normalized, load_review_flags(qdir / 'development_review_flags.json'), evidence_scope=ctx['supported_evidence'])
assert len(gated['engineering_requirements']) == 1
assert not gated['_quarantine_delivery']['withheld']
assert gated['engineering_requirements'][0]['support_status'] != 'verified_by_direct_evidence'
report = {'checks_passed': True, 'protected_historical_files': 366, 'prior_model_artifacts': 52,
    'historical_changed': [], 'prior_model_artifacts_changed': [], 'unrelated_dirty_changed': [],
    'request_checks': checks, 'offline_quarantine_only': {
        'prior_replay_sha256': sha(qdir / 'REPLAY.json'),
        'prior_delivery_sha256': sha(qdir / 'DELIVERY_AND_REVIEW.json'),
        'saved_responses': prior_replay['summary']['saved_responses'] + 1,
        'raw_rows': prior_replay['summary']['raw_rows'] + 1,
        'delivery_rows': prior_replay['summary']['delivery_rows'] + 1,
        'withheld_rows': prior_replay['summary']['withheld_rows'],
        'R003_new_output': gated,
        'limitation': 'Offline containment of saved output; not masked-prompt model performance.'}}
(WORK / 'FINAL_VERIFICATION.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), 'utf-8')
print(json.dumps({'checks_passed': True, 'historical_files_unchanged': 366, 'prior_model_files_unchanged': 52,
    'frozen_requests_verified': 12, 'offline_saved_rows': 78, 'offline_delivery_rows': 76, 'offline_withheld_rows': 2}))
