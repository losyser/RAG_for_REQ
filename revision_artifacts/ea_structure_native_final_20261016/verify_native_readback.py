import sys,json,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(r'D:\cooling_rag_multigranular\cooling_rag_multigranular')
sys.path.insert(0,str(ROOT))
from cooling_rag_mg.ea_structure import properties,q
case=sys.argv[1]
folder=Path('native_verified_'+case)
source=Path(sys.argv[2]) if len(sys.argv)>2 else Path('native_final23/ea_native_sel_isolated.xml') if case=='final23' else ROOT/'revision_artifacts/ea_native_followup_20261016'/('ea_native_OR041_minimal_core_tags_CANDIDATE.xml' if case=='minimal' else 'ea_native_sel_core_tags_CANDIDATE.xml')
expected=ET.parse(source).getroot();ep=properties(expected)
read=lambda name:ET.fromstring((folder/(name+'.xml')).read_text(encoding='utf-8-sig'))
objects={r.findtext('ea_guid'):{c.tag:c.text or '' for c in r} for r in read('objects').iter('Row')}
actual={}
for row in read('properties').iter('Row'):
 value=row.findtext('Value') or ''
 if value=='<memo>':value+='#NOTES#'+(row.findtext('Notes') or '')
 actual.setdefault(row.findtext('Object_ID'),{})[row.findtext('Property')]=value
errors=[]
object_ids={}
for role in expected.iter(q('ClassifierRole')):
 rid=role.get('xmi.id'); guid='{'+rid.removeprefix('EAID_').replace('_','-')+'}'
 obj=objects.get(guid)
 if not obj:errors.append('missing '+guid);continue
 object_ids[rid]=obj['Object_ID']
 if obj['Name']!=role.get('name'):errors.append('name mismatch '+guid)
 if obj['Stereotype']!='requirement':errors.append('stereotype mismatch '+guid)
 for key,value in ep[rid].items():
  if actual.get(obj['Object_ID'],{}).get(key)!=value:errors.append('property mismatch '+str((ep[rid]['id'],key)))
expected_edges=set()
for edge in expected.iter(q('Association')):
 ends=[object_ids.get(e.get('type')) for e in edge.iter(q('AssociationEnd'))]
 expected_edges.add(tuple(ends)+('Nesting',))
actual_edges={(r.findtext('Start_Object_ID'),r.findtext('End_Object_ID'),r.findtext('Connector_Type')) for r in read('connectors').iter('Row') if r.findtext('Start_Object_ID') in set(object_ids.values()) or r.findtext('End_Object_ID') in set(object_ids.values())}
if actual_edges!=expected_edges:errors.append('relationship endpoint/type mismatch')
result={'case':case,'requirements_checked':len(ep),'property_count_checked':sum(map(len,ep.values())),'relationships_checked':len(expected_edges),'errors':errors,'native_pngs':[p.name for p in folder.glob('*.png')]}
(folder/'field_validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2));assert not errors
