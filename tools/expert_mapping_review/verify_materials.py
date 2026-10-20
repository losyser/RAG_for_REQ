"""Validate prepared real packages without creating expert records or labels."""
import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location('review', Path(__file__).with_name('server.py'))
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)

def verify(project, materials):
    pilot = json.loads((materials/'expert_packet/calibration_2_sources.pilot.json').read_text(encoding='utf8'))
    library = json.loads((materials/'coordinator/source_library_unlabelled.json').read_text(encoding='utf8'))
    verification = json.loads((materials/'coordinator/UPSTREAM_VERIFICATION.json').read_text(encoding='utf8'))
    checks = {}
    review.validate_package(pilot)
    checks['pilot_valid_and_explicitly_not_formal'] = pilot['kind'] == 'pilot' and 'exclude-formal' in pilot['protocol']
    checks['pilot_sources_and_counts'] = [(s['id'],len(s['candidates'])) for s in pilot['sources']] == [('OR002',9),('OR001',17)]
    rebuilt = review.build_assignment(project,'OR002,OR001',pilot['protocol'],'pilot')
    checks['deterministic_conversion'] = rebuilt == pilot
    definitions = {}
    for node in ast.parse((project/'cooling_rag_mg/evidence_taxonomy.py').read_text(encoding='utf8')).body:
        if isinstance(node,ast.AnnAssign) and isinstance(node.target,ast.Name) and node.target.id in ('INTENTS','TAXONOMY'):
            definitions[node.target.id] = ast.literal_eval(node.value)
    checks['original_legal_taxonomy_unchanged'] = pilot['taxonomy'] == definitions['TAXONOMY']
    missing = set().union(*map(set,definitions['TAXONOMY'].values())) - set(definitions['INTENTS'])
    checks['missing_labels_explicitly_marked'] = len(missing)==14 and all(pilot['intents'][i].startswith('[原目录行注释] ') for i in missing)
    checks['original_45_labels_unchanged'] = all(pilot['intents'][k]==v for k,v in definitions['INTENTS'].items())
    checks['library_all_60_unlabelled'] = len(library['sources'])==60 and library['not_an_assignment'] is True
    try:
        review.validate_package(library)
        checks['library_rejected_as_assignment'] = False
    except review.ReviewError:
        checks['library_rejected_as_assignment'] = True
    banned = {'answers','predictions','model_labels','expert_key','PRIVATE','gold','method','methods'}
    def clean(value):
        if isinstance(value,dict): return not (set(value)&banned) and all(clean(v) for v in value.values())
        if isinstance(value,list): return all(clean(v) for v in value)
        return True
    checks['no_answers_or_method_predictions_in_packages'] = clean(pilot) and clean(library)
    checks['all_60_source_checks_pass'] = len(verification['per_source'])==60 and all(all(s['checks'].values()) for s in verification['per_source'])
    checks['all_frozen_checks_pass'] = all(f.get('equals_frozen',True) for f in verification['files'])
    checks['no_formal_sample_or_answers'] = verification['formal_sample_selected'] is False and verification['expert_answers_created'] is False
    if not all(checks.values()): raise ValueError(checks)
    return {'passed':True,'checks':checks,'file_hashes':{p.relative_to(materials).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(materials.rglob('*')) if p.is_file()}}

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--project',type=Path,required=True)
    parser.add_argument('--materials',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=verify(args.project,args.materials)
    with args.output.open('x',encoding='utf8') as handle:json.dump(result,handle,ensure_ascii=False,indent=2)
    print(json.dumps({'passed':True,'checks':len(result['checks']),'output':str(args.output)}))
