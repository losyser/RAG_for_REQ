from pathlib import Path
import sys,json,re,collections,hashlib,struct,xml.etree.ElementTree as ET
R=Path(r'D:\cooling_rag_multigranular\cooling_rag_multigranular');sys.path.insert(0,str(R));O=R/'revision_artifacts/ea_paper_v3_20261016';A=O/'audit'
from cooling_rag_mg.ea_structure import q,properties
from cooling_rag_mg.ea_presentation import serialize
from cooling_rag_mg.requirement_status import display_colors,colorref
read=lambda name:ET.fromstring((A/(name+'.xml')).read_text(encoding='utf-8-sig'))
oldcheck={}
for p in A.glob('immediately_before_*.xml'):
 old=collections.Counter(ET.tostring(r) for r in read(p.stem).iter('Row'));new=collections.Counter(ET.tostring(r) for r in read(p.stem.replace('immediately_before_','final_')).iter('Row'));missing=sum((old-new).values());assert missing==0,(p.name,missing);oldcheck[p.stem.removeprefix('immediately_before_')]={'old_rows':sum(old.values()),'changed_or_missing':missing}
(A/'old_content_preservation.json').write_text(json.dumps(oldcheck,indent=2))
objects={r.findtext('ea_guid').upper():{e.tag:e.text or '' for e in r} for r in read('final_t_object').iter('Row')}
tags={}
for r in read('final_t_objectproperties').iter('Row'):
 v=r.findtext('Value') or ''
 if v=='<memo>':v+='#NOTES#'+(r.findtext('Notes') or '')
 tags.setdefault(r.findtext('Object_ID'),{})[r.findtext('Property')]=v
created=json.loads((A/'native_created.json').read_text(encoding='utf-8-sig'));spec=json.loads((A/'native_spec.json').read_text(encoding='utf-8'));results=[]
for rec,s in zip(created,spec):
 p=O/'paper'/(s['file']+'.xml');xml=p.read_text(encoding='utf-8')
 for old,guid in rec['guid_map'].items():
  new=('EAPK_' if old.startswith('EAPK_') else 'EAID_')+guid.strip('{}').upper().replace('-','_');xml=xml.replace(old,new)
  if old.startswith('EAID_'):xml=xml.replace('{'+old[5:].replace('_','-')+'}',guid.upper())
 root=ET.fromstring(xml);next(root.iter(q('Package'))).set('name',s['package_name']);props=properties(root);ids={}
 for role in root.iter(q('ClassifierRole')):
  rid=role.get('xmi.id');obj=objects['{'+rid[5:].replace('_','-')+'}'];ids[rid]=obj['Object_ID'];v=props[rid]
  assert obj['Name']==role.get('name') and obj['Stereotype']=='requirement';assert obj['Note'].replace('\r\n','\n')==v['text'].removeprefix('<memo>#NOTES#').replace('\r\n','\n')
  assert all(tags[obj['Object_ID']].get(k,'').replace('\r\n','\n')==value.replace('\r\n','\n') for k,value in v.items()),v['id']
 expected={tuple(ids[e.get('type')] for e in edge.iter(q('AssociationEnd')))+('Nesting',) for edge in root.iter(q('Association'))}
 actual={(r.findtext('Start_Object_ID'),r.findtext('End_Object_ID'),r.findtext('Connector_Type')) for r in read('final_t_connector').iter('Row') if r.findtext('Start_Object_ID') in ids.values()};assert actual==expected
 dobjs={r.findtext('Object_ID'):r for r in read('final_t_diagramobjects').iter('Row') if r.findtext('Diagram_ID')==str(rec['diagram_id'])};visible=[]
 for rid,oid in ids.items():
  if oid not in dobjs:continue
  row=dobjs[oid];v=props[rid];visible.append(v['id']);style=row.findtext('ObjectStyle')
  assert 'Notes=0;' not in style
  for field,col in zip(['BCol','LCol'],display_colors(v,'Rule grade')):assert field+'='+str(colorref(col))+';' in style
 assert len(visible) in [3,4];assert not list(root.iter(q('Comment')));p.write_text(serialize(root),encoding='utf-8')
 emf=p.with_suffix('.emf').read_bytes();texts=[];offset=0
 while offset+8<=len(emf):
  typ,n=struct.unpack_from('<II',emf,offset)
  if n<8:break
  if typ==84:
   chars,pos=struct.unpack_from('<II',emf,offset+44);texts.append(emf[offset+pos:offset+pos+chars*2].decode('utf-16-le'))
  offset+=n
 assert texts;joined=' '.join(texts)
 assert not any(x in joined for x in ['Coloring by','Reported support','Traceback','NOTES#','D:\\','C:\\'])
 for rid in ids:
  if props[rid]['id'] in visible:assert props[rid]['id'] in joined
 (A/(s['file']+'_emf_text.json')).write_text(json.dumps(texts,ensure_ascii=False,indent=2),encoding='utf-8')
 results.append({'figure':s['file'],'diagram_id':rec['diagram_id'],'visible_ids':visible,'requirements':len(props),'properties':sum(map(len,props.values())),'relations':len(actual),'native_notes_text_names_match':True,'visible_colors_match':True,'emf_text_records':len(texts),'seven_conditions':[True]*7,'watermark_exception':'EA trial watermark retained unchanged'})
(A/'native_acceptance.json').write_text(json.dumps(results,indent=2));print(json.dumps({'old_content':oldcheck,'figures':results},indent=2))
