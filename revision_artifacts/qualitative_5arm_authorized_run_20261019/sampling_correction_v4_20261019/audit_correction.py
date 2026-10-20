"""Read-only audit of original materials; writes only a new correction audit."""
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from sampler_v4 import anchor_quality, original_composite_stratum, readiness, select_formal, NotReady

HERE = Path(__file__).resolve().parent
WORK = HERE.parent
def read(path):
    return json.loads(path.read_text(encoding='utf-8'))
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def diagnostic_sample(records, raw, groups):
    pools = defaultdict(list)
    for r in records:
        band = original_composite_stratum(r) if raw else r['band']
        order = hashlib.sha256(f"manual-q-v2-20261019|{r['slot']}|{r['row_index']}".encode()).hexdigest()
        pools[r['group'], band].append((order, r['review_id']))
    for pool in pools.values():
        pool.sort()
    order = [(g,b) for g in groups for b in ['direct_and_applicable','explicit_negative','other_uncertain_error']]
    selected = []
    while len(selected) < 30:
        progressed = False
        for key in order:
            if pools[key] and len(selected) < 30:
                selected.append(pools[key].pop(0)[1]); progressed = True
        if not progressed:
            break
    return selected

def main():
    hashes = read(WORK/'ARTIFACT_HASHES_FINAL.json')
    changed = [name for name, digest in hashes.items() if not (WORK/name).is_file() or sha(WORK/name) != digest]
    records = read(WORK/'REVIEW_DIAGNOSTICS.json')
    packets = {r['review_id']:r for r in read(WORK/'QWEN_BLIND_PACKETS.json')}
    frozen = [r['review_id'] for r in read(WORK/'QWEN_FROZEN_PLAN.json')['requests']]
    policy = read(HERE/'sampling_policy_draft.json')
    sample = read(WORK/'MANUAL_SAMPLE_KEY_LOCAL_ONLY.json')
    quality = []
    differences = []
    for r in records:
        if r.get('machine_judgment'):
            evidence = {e['evidence_id']:e['supplied_excerpt'] for e in packets[r['review_id']]['cited_evidence']}
            quality.append({'review_id':r['review_id'], 'original_support':r['machine_judgment']['support'], 'anchor_quality':anchor_quality(r['machine_judgment'], evidence)})
        raw = original_composite_stratum(r)
        if raw != r['band']:
            differences.append({'review_id':r['review_id'], 'old_effective_band':r['band'], 'original_raw_composite_band':raw})
    old_ids = [r['review_id'] for r in sample]
    replay = diagnostic_sample(records, False, policy['group_order'])
    raw_ids = diagnostic_sample(records, True, policy['group_order'])
    status = readiness(records, frozen, policy)
    try:
        select_formal(records, frozen, policy)
    except NotReady as exc:
        blocked = str(exc)
    else:
        raise AssertionError('Formal sampler unexpectedly accepted incomplete reviews')
    delivery = read(WORK/'DESKTOP_DELIVERY.json')
    desktop_unchanged = sha(Path(delivery['path'])) == delivery['sha256']
    audit = {
        'created_utc':datetime.now(timezone.utc).isoformat(),
        'revision_timing':'after_observing_77_successful_Qwen_reviews_not_preregistered',
        'checkpoint_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=WORK,text=True).strip(),
        'old_manifest_files_checked':len(hashes), 'old_manifest_changed_files':changed,
        'old_desktop_summary_unchanged':desktop_unchanged,
        'old_sample_status':dict(Counter(r['review_status'] for r in sample)),
        'old_sample_replayed_exactly':replay == old_ids,
        'independent_anchor_quality_counts':dict(Counter(r['anchor_quality']['status'] for r in quality)),
        'independent_quality_diagnostics':quality,
        'composite_band_differences':differences,
        'diagnostic_only_not_a_new_formal_sample':{
            'old_selected_only':sorted(set(old_ids)-set(raw_ids)),
            'raw_composite_replay_only':sorted(set(raw_ids)-set(old_ids))},
        'formal_readiness':status, 'formal_sampler_rejection':blocked,
        'formal_sample_generated':False, 'api_calls':0,
        'resume_status':'API paused; 77 completed, 1 Arrearage failure, 363 unsent. No retry or credentials changes.'
    }
    assert not changed and desktop_unchanged and replay == old_ids
    with (HERE/'CORRECTION_AUDIT.json').open('x',encoding='utf-8') as stream:
        json.dump(audit,stream,ensure_ascii=False,indent=2)
    print(json.dumps({k:v for k,v in audit.items() if k not in ['independent_quality_diagnostics']},ensure_ascii=False,indent=2))

if __name__ == '__main__':
    main()
