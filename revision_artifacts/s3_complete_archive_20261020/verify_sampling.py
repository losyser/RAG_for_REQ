"""Verify the frozen draw from frozen inputs in memory; never writes or redraws files."""
import sys,json,random,hashlib,importlib.util
from pathlib import Path
from collections import Counter
F=Path(sys.argv[1]).resolve();C=F/'02_协调者_勿发评审';snap=C/'frozen_inputs'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
digest=lambda x:hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
spec=importlib.util.spec_from_file_location('frozen_classifier',snap/'classifier.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
kb={u['id']:u for u in map(json.loads,(snap/'kb.jsonl').read_text(encoding='utf-8').splitlines())}
req={u['requirement_id']:u['requirement_text'] for u in map(json.loads,(snap/'requirements.jsonl').read_text(encoding='utf-8').splitlines())}
inputs=read(C/'INPUT_MANIFEST.json');pools={}
for arm,grades in [('rag',{'A','B'}),('norag',{'X'})]:
    pool=[]
    for rs in read(snap/(arm+'.json'))['result_sets']:
        for idx,raw in enumerate(rs['engineering_requirements'],1):
            grade=mod.classify_grade(raw.get('measurable_criterion'),raw.get('evidence_citations'),kb,numeric_policy='numeric-ranges-v1')
            if grade not in grades:continue
            identity={'input_sha256':inputs[arm]['sha256'],'source_id':rs['source_requirement_id'],'row_1based':idx,'candidate_sha256':digest(raw)}
            pool.append({'arm':arm,**identity,'stable_id':digest(identity),'grade':grade,'original_requirement':req[identity['source_id']],'candidate':raw})
    pools[arm]=pool
assert pools==read(C/'CANDIDATE_POOL_FROZEN.json')
counts={a:Counter(r['source_id'] for r in rows) for a,rows in pools.items()}
common=sorted(counts['rag'].keys()&counts['norag'].keys());eligible=[s for s in common if min(counts[a][s] for a in counts)>=2]
seed=202610191555;extra=sorted(random.Random(str(seed)+'|extra_sources').sample(eligible,5));selected=[]
for sid in common:
    for arm in ['rag','norag']:
        frame=sorted([r for r in pools[arm] if r['source_id']==sid],key=lambda r:r['row_1based'])
        for slot,r in enumerate(random.Random(f'{seed}|within|{sid}|{arm}').sample(frame,2 if sid in extra else 1),1):
            selected.append(dict(r,pair_slot=slot))
random.Random(str(seed)+'|display_order').shuffle(selected)
for r,n in zip(selected,random.Random(str(seed)+'|blind_ids').sample(range(100000,1000000),50)):r['blind_id']=f'K{n}'
assert selected==read(C/'SAMPLE_FROZEN.json')
print(json.dumps({'pools_equal':True,'pool_sizes':{a:len(v) for a,v in pools.items()},'sample_equal':True,'cards':len(selected),'sources':len(common),'seed':seed}))
