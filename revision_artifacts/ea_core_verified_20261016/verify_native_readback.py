import sys,json,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(r'D:\cooling_rag_multigranular\cooling_rag_multigranular')
sys.path.insert(0,str(ROOT))
from cooling_rag_mg.ea_structure import properties,q
case=sys.argv[1]
folder=Path('native_verified_'+case)
source=ROOT/'revision_artifacts/ea_native_followup_20261016'/('ea_native_OR041_minimal_core_tags_CANDIDATE.xml' if case=='minimal' else 'ea_native_sel_core_tags_CANDIDATE.xml')
expected=ET.parse(source).getroot();ep=properties(expected)
read=lambda name:ET.fromstring((folder/(name+'.xml')).read_text(encoding='utf-8-sig'))
objects={r.findtext('ea_guid'):{c.tag:c.text or '' for c in r} for r in read('objects').iter('Row')}
actual={}
for row in read('properties').iter('Row'):
 value=row.findtext('Value') or ''
 if value=='<memo>':value+='#NOTES#'+(row.findtext('Notes') or '')
 actual.setdefault(row.findtext('Object_ID'),{})[row.findtext('Property')]=value
errors=[]
for role in expected.iter(q('ClassifierRole')):
 rid=role.get('xmi.id'); guid='{'+rid.removeprefix('EAID_').replace('_','-')+'}'
 obj=objects.get(guid)
 if not obj:errors.append('missing '+guid);continue
 if obj['Name']!=role.get('name'):errors.append('name mismatch '+guid)
 if obj['Stereotype']!='requirement':errors.append('stereotype mismatch '+guid)
 for key,value in ep[rid].items():
  if actual.get(obj['Object_ID'],{}).get(key)!=value:errors.append('property mismatch '+str((ep[rid]['id'],key)))
result={'case':case,'requirements_checked':len(ep),'property_count_checked':sum(map(len,ep.values())),'errors':errors,'native_pngs':[p.name for p in folder.glob('*.png')]}
(folder/'field_validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2));assert not errors
