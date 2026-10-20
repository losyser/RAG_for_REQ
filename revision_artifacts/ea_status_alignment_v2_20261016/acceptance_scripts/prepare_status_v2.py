from pathlib import Path
import sys,json,hashlib,xml.etree.ElementTree as ET,re,uuid
R=Path(r'D:\cooling_rag_multigranular\cooling_rag_multigranular');sys.path.insert(0,str(R))
from cooling_rag_mg.ea_ui_export import export_ea_payload_bytes,load_kb,native_exporter
from cooling_rag_mg.ea_presentation import presentation_xml,fresh_ids,serialize
from cooling_rag_mg.ea_structure import q,properties
from cooling_rag_mg.ea_status_view import status_view
from cooling_rag_mg.requirement_status import normalize_status,display_colors
from cooling_rag_mg.config import AppConfig
O=R/'revision_artifacts/ea_status_alignment_v2_20261016'
batch=R/'data/search_results/batch_20260730_164747';payload=json.loads((batch/'engineering_requirements_20260730_164801/engineering_requirements.json').read_text(encoding='utf-8'))
retrieval=json.loads((batch/'all_requirements_results.json').read_text(encoding='utf-8'))
sources=[{'requirement_id':x['requirement_id'],'requirement_text':x['raw_requirement_text'],'stakeholder':x.get('stakeholder','')} for x in retrieval['requirements']]
from ui.state import DEFAULT_REQUIREMENTS,normalize_df
import pandas as pd
merged={x['requirement_id']:x for x in normalize_df(pd.DataFrame(DEFAULT_REQUIREMENTS))}
for x in sources:
 if x['requirement_id'] in merged:assert merged[x['requirement_id']]['requirement_text']==x['requirement_text']
 merged[x['requirement_id']]=x
sources=list(merged.values())
kbpath=AppConfig().paths.evidence_units_jsonl;kb=load_kb(kbpath)
english=R/'revision_artifacts/ea_english_small_figures_20261016/native_acceptance_111/release/english_temperature.xml'
comparisons=[]
for dataset in ['cn98','en23']:
 for mode,short in [('Rule grade','rule'),('Evidence support','support')]:
  name='status_v2_'+dataset+'_'+short
  if dataset=='cn98':
   xml=export_ea_payload_bytes(payload,source_requirements=sources,kb_index=kb,coloring_by=mode,batch_id=batch.name,source_path=str(batch)).decode()
   visible=['R001','ER-R001-01','ER-R001-02','ER-R001-04']
  else:
   xml=status_view(english.read_text(encoding='utf-8'),mode,batch_id='exp_v4_selected_OR041_OR052_OR008',source_path=str(english));visible=['OR008','OR008.1','OR008.5','OR008.8']
  full=xml
  xml=presentation_xml(xml,native_exporter().GRADE_STYLE,visible_ids=visible,name='REQ_'+name)
  xml=status_view(xml,mode)
  root=ET.fromstring(xml);diagram=next(root.iter(q('Diagram')));els=diagram.find(q('Diagram.element'))
  for obj in els:
   g=obj.get('geometry','')
   if 'Top=' in g:g=re.sub(r'(Top|Bottom)=(\d+);',lambda m:m[1]+'='+str(int(m[2])+50)+';',g)
   else:g=re.sub(r'Path=([^;]*);',lambda m:'Path='+re.sub(r'(-?\d+):(-?\d+)\$',lambda p:p[1]+':'+str(int(p[2])-50)+'$',m[1])+';',g)
   obj.set('geometry',g)
  # Give the English legend enough height, leaving framing to EA.
  comments={e.get('xmi.id') for e in root.iter(q('Comment'))}
  for obj in els:
   if obj.get('subject') in comments:
    g=obj.get('geometry');top=int(re.search('Top=(\d+)',g)[1]);obj.set('geometry',re.sub('Bottom=\d+;',f'Bottom={top+110};',g))
  xml,m=fresh_ids(serialize(root))
  # Restore provenance pointers changed by global technical-GUID rewriting.
  root=ET.fromstring(xml)
  for t in root.iter(q('TaggedValue')):
   if t.get('tag')=='paper_source_guid':
    reverse={v:k for k,v in m.items()};t.set('value',reverse.get(t.get('value'),t.get('value')))
  xml=serialize(root);(O/(name+'.xml')).write_text(xml,encoding='utf-8');(O/(name+'_full.xml')).write_text(full,encoding='utf-8')
  p=properties(root)
  for v in p.values():
   comparisons.append({'dataset':dataset,'mode':mode,'id':v['id'],'grade':v['rule_grade'],'support_raw':v['reported_support_status'],'support':v['evidence_support_state'],'label':v['evidence_support_label'],'verification':v['semantic_verification_state'],'color':display_colors(v,mode)[0],'visible':v['id'] in visible})
(O/'same_batch_alignment.json').write_text(json.dumps(comparisons,ensure_ascii=False,indent=2),encoding='utf-8')
(O/'input_provenance.json').write_text(json.dumps({'cn_batch':str(batch),'en_source':str(english),'kb_path':str(kbpath),'kb_sha256':hashlib.sha256(kbpath.read_bytes()).hexdigest()},indent=2))
print('Prepared four independent packages; KB:',kbpath)
