from pathlib import Path
import sys,json,hashlib,xml.etree.ElementTree as ET
R=Path(r'D:\cooling_rag_multigranular\cooling_rag_multigranular');sys.path.insert(0,str(R))
from cooling_rag_mg.ea_structure import properties,q
out=Path(__file__).parent;data=R/'data/search_results'
batch=data/'batch_ui_english_acceptance_20261016';assert not batch.exists()
baseline={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in data.rglob('*.json')}
(out/'original_json_hashes.json').write_text(json.dumps(baseline,indent=2))
root=ET.parse(R/'revision_artifacts/ea_english_small_figures_20261016/source.xml').getroot();props=properties(root)
by={props[e.get('xmi.id')]['id']:(e.get('name'),props[e.get('xmi.id')]) for e in root.iter(q('ClassifierRole'))}
groups=[('OR041',['OR041.1','OR041.2']),('OR052',['OR052.1','OR052.4']),('OR008',['OR008.1','OR008.5'])]
payload={'acceptance_fixture':True,'requirement_sets':[]};retrieval={'requirements':[]}
for sid,children in groups:
 text=by[sid][1]['text'].removeprefix('<memo>#NOTES#')
 retrieval['requirements'].append({'requirement_id':sid,'stakeholder':'Offline UI acceptance fixture','raw_requirement_text':text,'results':[]})
 rs={'source_requirement_id':sid,'requirement_set_id':'RS-'+sid,'engineering_requirements':[],'relationships':[],'evidence_gaps':[]}
 for bid in children:
  name,p=by[bid]
  rs['engineering_requirements'].append({'id':bid,'parent_id':'RS-'+sid,'topic':name,'shall_statement':p['text'].removeprefix('<memo>#NOTES#'),'measurable_criterion':p.get('criterion',''),'evidence_citations':[{'kb_id':s.strip()} for s in p.get('evidence_ids','').split(';') if s.strip()],'support_status':'need_confirmation','review_route':p.get('review_route','')})
 payload['requirement_sets'].append(rs)
folder=batch/'engineering_requirements_acceptance';folder.mkdir(parents=True)
for name,value,target in [('engineering_requirements.json',payload,folder),('all_requirements_results.json',retrieval,batch)]:
 body=json.dumps(value,ensure_ascii=False,indent=2);(target/name).write_text(body,encoding='utf-8');(out/('fixture_'+name)).write_text(body,encoding='utf-8')
print('Created isolated UI acceptance fixture:',batch)
