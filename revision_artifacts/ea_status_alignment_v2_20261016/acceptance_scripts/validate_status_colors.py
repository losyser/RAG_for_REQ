from pathlib import Path
import sys,json,re,collections,xml.etree.ElementTree as ET
R=Path(r'D:\cooling_rag_multigranular\cooling_rag_multigranular');sys.path.insert(0,str(R));O=R/'revision_artifacts/ea_status_alignment_v2_20261016';F=O/'final'
from cooling_rag_mg.ea_structure import q,properties
from cooling_rag_mg.requirement_status import display_colors,colorref
read=lambda n:ET.fromstring((F/(n+'.xml')).read_text(encoding='utf-8-sig'))
objects={r.findtext('ea_guid'):r.findtext('Object_ID') for r in read('objects').iter('Row')}
dobs={r.findtext('Object_ID'):r for r in read('diagramobjects').iter('Row')}
rows=[]
for ds in ['cn98','en23']:
 previous=None
 for mode,short in [('Rule grade','rule'),('Evidence support','support')]:
  name='status_v2_'+ds+'_'+short;root=ET.parse(F/(name+'.xml')).getroot();p=properties(root);basis={v['id']:{k:v.get(k,'') for k in ['text','grade','support_status','criterion','evidence_ids','review_route','derivation']} for v in p.values()}
  if previous is not None:assert basis==previous
  previous=basis;checked=0
  for e in root.iter(q('ClassifierRole')):
   key=e.get('xmi.id');v=p[key];oid=objects['{'+key[5:].replace('_','-')+'}'];assert v['semantic_verification_state']=='not_assessed';assert e.get('name')!=v['id'];assert v['text']
   if oid in dobs:
    style=dobs[oid].findtext('ObjectStyle');colors=display_colors(v,mode)
    for field,col in zip(['BCol','LCol'],colors):assert re.search(field+'=(\\d+)',style)[1]==str(colorref(col))
    checked+=1
  rows.append({'dataset':ds,'mode':mode,'all_requirements':len(p),'native_visible_colors_matched':checked,'grade_counts':dict(collections.Counter(v['rule_grade'] for v in p.values())),'support_counts':dict(collections.Counter(v['evidence_support_state'] for v in p.values())),'mode_change_preserves_content_grade_raw_status':True})
(F/'status_semantic_validation.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
