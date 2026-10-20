"""Offline audit contracts. These checks neither generate judgments nor prove truth."""
from collections import Counter
import math
import re

VERSION = 'revision-audit-v1'

def strict_numeric_label(verdicts, raw=''):
    """Unit: existing reported numeric verdict, not an independently verified claim.

    All-reported support does NOT establish complete extraction/coverage of the sentence.
    Historical any-supported/no-conflict labels remain in the original artifacts.
    """
    if raw.startswith('ERROR:'): return 'error'
    if raw == 'NO_EVIDENCE': return 'no_evidence'
    s, c, u = (len(verdicts.get(k, [])) for k in ('supported','contradicted','unverifiable'))
    if c: return 'contradicted'
    if s and u: return 'partial_support'
    if s: return 'all_reported_supported'
    if u: return 'not_found'
    return 'no_numeric' if raw.strip().upper() == 'NO_NUMERIC_CLAIMS' else 'unparsed'

def validate_expert_rows(sheets, key):
    from cooling_rag_mg.evidence_taxonomy import COMPONENTS, INTENTS, valid_pair
    errors=[]
    for section, expected in key.items():
        if section not in ('S1','S2','S3','S4'): continue
        rows=sheets.get(section, [])
        ids=[str(r.get('item')) for r in rows]
        if len(ids)!=len(set(ids)): errors.append(f'{section}: duplicate item IDs')
        if set(ids)!=set(expected): errors.append(f'{section}: missing/extra IDs: missing={sorted(set(expected)-set(ids))}, extra={sorted(set(ids)-set(expected))}')
        for r in rows:
            ident=str(r.get('item')); prefix=f'{section}/{ident}'
            if ident not in expected: continue
            if section=='S1':
                c,i=r.get('component'),r.get('intent')
                if c not in COMPONENTS or i not in INTENTS or not valid_pair(c,i): errors.append(prefix+': missing/invalid component-intent pair')
            elif section=='S2':
                v=r.get('relevant')
                if isinstance(v,bool) or str(v).strip() not in ('0','1'): errors.append(prefix+': relevant must be explicit 0 or 1')
                if 'or_id' in r and [r.get('or_id'),r.get('component'),r.get('intent')]!=expected[ident]: errors.append(prefix+': candidate identity changed')
                for tok in str(r.get('missing_pairs') or '').split(';'):
                    if not tok.strip(): continue
                    p=[x.strip() for x in tok.split(':')]
                    if len(p)!=2 or not valid_pair(*p): errors.append(prefix+': invalid missing_pairs token '+tok)
            elif section=='S3':
                if r.get('verdict') not in ('correct','approx','wrong','unknown'): errors.append(prefix+': missing/invalid verdict')
            elif section=='S4':
                for field in ('n_correct','n_missed'):
                    n=r.get(field)
                    if isinstance(n,bool) or not isinstance(n,(int,float)) or not math.isfinite(n) or n<0 or int(n)!=n: errors.append(prefix+': invalid '+field)
                n=r.get('n_correct')
                if isinstance(n,(int,float)) and n>expected[ident]['n_extracted']: errors.append(prefix+': n_correct exceeds n_extracted')
    return errors

def validate_prediction_pool(predictions, s2key):
    from cooling_rag_mg.evidence_taxonomy import valid_pair
    pool=[tuple(x) for x in s2key.values()]
    errors=[]
    if len(pool)!=len(set(pool)): errors.append('S2 duplicate candidate tuples')
    ids={r for r,c,i in pool}
    for system, rows in predictions.items():
        if set(rows)!=ids: errors.append(system+': source coverage differs from S2')
        for rid, pairs in rows.items():
            if len(pairs)!=len({tuple(p) for p in pairs}): errors.append(system+'/'+rid+': duplicate predicted pairs')
            for p in pairs:
                if len(p)!=2 or not valid_pair(*p): errors.append(system+'/'+rid+': invalid predicted pair')
                elif (rid,*p) not in pool: errors.append(system+'/'+rid+': predicted candidate absent from S2')
    return errors

def successful_variant(data):
    """Fail closed on absent, empty, error, or duplicate-source outputs."""
    rows=data.get('result_sets',[])
    reasons=[]
    if not rows: reasons.append('no result sets')
    ids=[r.get('source_requirement_id') for r in rows]
    if None in ids or len(ids)!=len(set(ids)): reasons.append('missing/duplicate source IDs')
    for r in rows:
        if not r.get('engineering_requirements'): reasons.append(str(r.get('source_requirement_id'))+': empty output; cause requires run log')
        if any(r.get(k) for k in ('error','_error','errors')): reasons.append(str(r.get('source_requirement_id'))+': error recorded')
    return not reasons, reasons


def verify_frozen_arm_inputs(root, filenames, baseline):
    """Arm names alone cannot distinguish generator families; bind each file to baseline."""
    import hashlib
    from pathlib import Path
    hashes={x["path"].replace("\\", "/"):x["sha256"] for x in baseline["files"] if not x.get("external")}
    errors=[]
    for arm, filename in filenames.items():
        rel="data/search_results/exp_v4/"+filename
        path=Path(root)/rel
        if rel not in hashes or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=hashes[rel]:
            errors.append(arm+": input differs from frozen source profile (possible cross-arm mix or new run)")
    return errors
