from pathlib import Path
import sys,json,sqlite3,collections,hashlib,struct,xml.etree.ElementTree as ET
R=Path(r'D:\cooling_rag_multigranular\cooling_rag_multigranular');sys.path.insert(0,str(R))
from cooling_rag_mg.ea_structure import q,properties
O=R/'revision_artifacts/ea_english_small_figures_20261016';F=O/'native_acceptance_111/release';out=O/'native_acceptance_111'
src=R/'revision_artifacts/ea_native_followup_20261016/111.qea'
tables=['t_package','t_object','t_objectproperties','t_connector','t_diagram','t_diagramobjects','t_diagramlinks','t_xref']
preserved={}
with sqlite3.connect((out/'111_before_english_import.qea').as_uri()+'?mode=ro',uri=True) as before,sqlite3.connect(src.as_uri()+'?mode=ro',uri=True) as after:
 for table in tables:
  old=collections.Counter(before.execute('SELECT * FROM '+table).fetchall());new=collections.Counter(after.execute('SELECT * FROM '+table).fetchall())
  missing=old-new;preserved[table]={'before_rows':sum(old.values()),'after_rows':sum(new.values()),'original_rows_changed_or_missing':sum(missing.values())}
  if table=='t_package' and missing:
   columns=[c[1] for c in before.execute('PRAGMA table_info(t_package)')];deltas=[]
   for row in missing:
    current=after.execute('SELECT * FROM t_package WHERE Package_ID=?',(row[0],)).fetchone();assert current is not None
    changes=[{'field':k,'before':a,'after':b} for k,a,b in zip(columns,row,current) if a!=b]
    assert all(c['field']=='LastLoadDate' for c in changes),changes
    deltas+=changes
   preserved[table]['ea_import_metadata_changes']=deltas
   preserved[table]['original_rows_changed_or_missing']=0
 (out/'existing_content_preservation.json').write_text(json.dumps(preserved,indent=2))
 assert all(v['original_rows_changed_or_missing']==0 for v in preserved.values()),preserved
read=lambda name:ET.fromstring((out/'final'/(name+'.xml')).read_text(encoding='utf-8-sig'))
objects={row.findtext('ea_guid'):{c.tag:c.text or '' for c in row} for row in read('objects').iter('Row')}
actual={}
for row in read('properties').iter('Row'):
 v=row.findtext('Value') or ''
 if v=='<memo>':v+='#NOTES#'+(row.findtext('Notes') or '')
 actual.setdefault(row.findtext('Object_ID'),{})[row.findtext('Property')]=v
results=[]
for name in ['english_full','english_scope','english_alarm','english_maintenance','english_temperature']:
 root=ET.parse(F/(name+'.xml')).getroot();props=properties(root);ids={};errors=[]
 for e in root.iter(q('ClassifierRole')):
  rid=e.get('xmi.id');guid='{'+rid[5:].replace('_','-')+'}';obj=objects[guid];ids[rid]=obj['Object_ID']
  assert obj['Name']==e.get('name') and obj['Stereotype']=='requirement'
  for k,v in props[rid].items():
   if actual[obj['Object_ID']].get(k,'').replace('\r\n','\n')!=v.replace('\r\n','\n'):errors.append([props[rid]['id'],k])
 expected={tuple(ids[e.get('type')] for e in edge.iter(q('AssociationEnd')))+('Nesting',) for edge in root.iter(q('Association'))}
 edges={(r.findtext('Start_Object_ID'),r.findtext('End_Object_ID'),r.findtext('Connector_Type')) for r in read('connectors').iter('Row') if r.findtext('Start_Object_ID') in ids.values() or r.findtext('End_Object_ID') in ids.values()}
 assert expected==edges and not errors,(name,errors)
 png=(F/(name+'.png')).read_bytes();w,h=struct.unpack('>II',png[16:24]);emf=(F/(name+'.emf')).read_bytes();assert struct.unpack_from('<I',emf,40)[0]==0x464d4520
 records=collections.Counter();offset=0
 while offset+8<=len(emf):
  typ,size=struct.unpack_from('<II',emf,offset)
  if size<8:break
  records[typ]+=1;offset+=size
 assert records[83]+records[84]>0
 results.append({'name':name,'requirements_checked':len(ids),'properties_checked':sum(map(len,props.values())),'relationships_checked':len(edges),'errors':errors,'png_pixels':[w,h],'emf_text_records':records[83]+records[84],'emf_sha256':hashlib.sha256(emf).hexdigest()})
(out/'native_validation.json').write_text(json.dumps(results,indent=2));print(json.dumps({'preservation':preserved,'native':results},indent=2))
