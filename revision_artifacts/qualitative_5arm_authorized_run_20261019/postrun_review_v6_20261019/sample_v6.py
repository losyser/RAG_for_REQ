"""Post-run v6: explicit440-valid population revision; no old policy mutation or transport."""
import hashlib
from collections import defaultdict
from copy import deepcopy

def select(records, frozen_ids, policy):
    if not policy.get('approved') or policy.get('required_population')!=440 or policy.get('sample_size')!=30:raise ValueError('policy_not_approved_or_scope_changed')
    ids=[r['review_id'] for r in records]
    if len(ids)!=440 or len(set(ids))!=440 or len(frozen_ids)!=440 or set(ids)!=set(frozen_ids):raise ValueError('population_not_440_unique_frozen')
    if policy['groups']!=['semantic_new','random_new'] or policy['labels']!=['direct','partial','contradicted','insufficient','uncertain']:raise ValueError('strata_changed')
    if policy['initial_quota_per_stratum']!=3 or policy['hash_salt']!='manual-q-v2-20261019':raise ValueError('quota_or_seed_changed')
    if policy['anchor_quality_changes_stratum'] or policy['applicability_changes_stratum']:raise ValueError('quality_cannot_relabel')
    order=[(g,l) for g in policy['groups'] for l in policy['labels']]
    pools=defaultdict(list)
    for r in records:
        j=r.get('machine_judgment')
        if r.get('review_status')!='completed' or not isinstance(j,dict) or j.get('review_id')!=r['review_id']:raise ValueError('incomplete_or_wrong_judgment')
        key=(r['group'],j.get('support'))
        if key not in order:raise ValueError('unexpected_group_or_raw_label')
        hashed=hashlib.sha256(f"{policy['hash_salt']}|{r['slot']}|{r['row_index']}".encode()).hexdigest()
        pools[key].append((hashed,r['review_id'],r))
    if len({(r['slot'],r['row_index']) for r in records})!=440:raise ValueError('duplicate_position')
    sizes={k:len(pools[k]) for k in order}
    for pool in pools.values():pool.sort(key=lambda x:(x[0],x[1]))
    quotas={k:min(3,sizes[k]) for k in order}
    while sum(quotas.values())<30:
        changed=False
        for k in order:
            if quotas[k]<sizes[k] and sum(quotas.values())<30:quotas[k]+=1;changed=True
        if not changed:raise ValueError('insufficient_population')
    selected=[];strata=[]
    for k in order:
        n,N=quotas[k],sizes[k]
        info={'group':k[0],'raw_support':k[1],'population':N,'selected':n,'nominal_inclusion_fraction':n/N if N else None,'nominal_weight':N/n if n else None,'probability_caveat':policy['interpretation']}
        strata.append(info)
        for hashed,_,r in pools[k][:n]:
            item=deepcopy(r);item['sampling']={**info,'hash_order':hashed,'policy_version':policy['version']};selected.append(item)
    return selected,strata
