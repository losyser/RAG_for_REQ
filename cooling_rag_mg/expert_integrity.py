"""Fail-closed workbook integrity checks; annotations are never generated here."""
import hashlib
import json
from collections import Counter
from pathlib import Path

SHEETS={'S1':'S1_tagging','S2':'S2_pairs','S3':'S3_values','S4':'S4_extraction'}
EDITABLE={'S1':{'component','intent'},'S2':{'relevant','missing_pairs'},'S3':{'verdict'},'S4':{'n_correct','n_missed'}}

def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def make_contract(template, key, source_hashes):
    """Build from a coordinator-verified blank template, not from returned annotations."""
    contract={'version':'expert-integrity-v1','source_hashes':source_hashes,'sections':{}}
    for section,name in SHEETS.items():
        ws=template[name]; values=list(ws.iter_rows(values_only=True)); header=list(values[0]); rows={}
        for row in values[1:]:
            if not any(v is not None for v in row): continue
            ident=str(row[0])
            if row[0] is None or ident in rows: raise ValueError(section+': template missing/duplicate ID')
            rows[ident]=[None if h in EDITABLE[section] else v for h,v in zip(header,row)]
        if set(rows)!=set(key[section]): raise ValueError(section+': template/key sample IDs differ')
        if section=='S2':
            for ident,row in rows.items():
                vals=[row[header.index(k)] for k in ('or_id','component','intent')]
                if vals!=key[section][ident]: raise ValueError('S2 template/key candidate mismatch')
        contract['sections'][section]={'name':name,'header':header,'rows':rows}
    return contract

def validate_workbook(wb,contract,sections=None):
    errors=[]
    for section in sections or SHEETS:
        spec=contract['sections'][section]; name=spec['name']
        if name not in wb.sheetnames:
            errors.append(section+': missing sheet');continue
        values=list(wb[name].iter_rows(values_only=True))
        if not values or list(values[0])!=spec['header']:
            errors.append(section+': headers/column set changed');continue
        seen=[]
        for row in values[1:]:
            if not any(v is not None for v in row): continue
            item=row[0]; ident=str(item); seen.append(ident)
            if isinstance(item,bool) or not isinstance(item,int):
                errors.append(section+': blank/invalid item ID');continue
            if ident not in spec['rows']:
                errors.append(section+'/'+ident+': unexpected sample ID');continue
            masked=[None if h in EDITABLE[section] else v for h,v in zip(spec['header'],row)]
            if masked!=spec['rows'][ident]: errors.append(section+'/'+ident+': immutable content changed')
            for h,v in zip(spec['header'],row):
                if h in EDITABLE[section] and isinstance(v,str) and v.startswith('='):
                    errors.append(section+'/'+ident+': formula annotation not accepted')
        if any(n>1 for n in Counter(seen).values()): errors.append(section+': duplicate IDs')
        if set(seen)!=set(spec['rows']): errors.append(section+': missing/extra sample IDs')
    return errors

def verify_sources(root,contract,baseline):
    """Bind key/template/predictions to the original audit baseline, not mutable metadata."""
    original={x['path'].replace('\\','/'):x['sha256'] for x in baseline['files'] if not x.get('external')}
    errors=[]
    required={'data/expert_round2/expert_workbook.xlsx','data/expert_round2/expert_key.json','data/search_results/exp_v4/e1_predictions.json'}
    if set(contract.get('source_hashes',{}))!=required: errors.append('integrity manifest source set changed')
    for path in required:
        claimed=contract.get('source_hashes',{}).get(path)
        if claimed!=original.get(path): errors.append(path+': manifest/baseline hash mismatch')
        full=Path(root)/path
        if not full.is_file() or file_hash(full)!=claimed: errors.append(path+': source hash changed')
    return errors
