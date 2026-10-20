from pathlib import Path
import xml.etree.ElementTree as ET,json,hashlib,shutil,sys
R=Path(r'D:\cooling_rag_multigranular\cooling_rag_multigranular');sys.path.insert(0,str(R))
from cooling_rag_mg.ea_structure import q
O=R/'revision_artifacts/ea_english_small_figures_20261016';A=O/'native_acceptance_111';F=A/'release'
geo=ET.fromstring((F/'native_geometry.xml').read_text(encoding='utf-8-sig'))
manifest=json.loads((O/'provenance.json').read_text(encoding='utf-8'))
for i,name in enumerate(['english_full','english_scope','english_alarm','english_maintenance','english_temperature'],2):
 r=ET.parse(A/'final'/(name+'.xml')).getroot();elements=next(r.iter(q('Diagram'))).find(q('Diagram.element'));package=next(r.iter(q('Package')))
 for row in geo.iter('Row'):
  if row.findtext('Diagram_ID')!=str(i):continue
  guid='EAID_'+row.findtext('ea_guid').strip('{}').replace('-','_')
  subject=package.get('xmi.id') if row.findtext('Object_Type')=='Package' else guid
  obj=next((e for e in elements if e.get('subject')==subject),None)
  if obj is None:obj=ET.SubElement(elements,q('DiagramElement'),{'subject':subject})
  obj.set('geometry',f"Left={row.findtext('RectLeft')};Top={-int(row.findtext('RectTop'))};Right={row.findtext('RectRight')};Bottom={-int(row.findtext('RectBottom'))};")
  obj.set('style',row.findtext('ObjectStyle') or '')
 (F/(name+'.xml')).write_text('<?xml version="1.0" encoding="UTF-8"?>\n'+ET.tostring(r,encoding='unicode'),encoding='utf-8')
 shutil.copy2(O/(name+'_guid_map.json'),F/(name+'_guid_map.json'))
 item=next(p for p in manifest['packages'] if p['name']==name);item['sha256']=hashlib.sha256((F/(name+'.xml')).read_bytes()).hexdigest();item['ea_diagram_id']=i
(F/'provenance.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
shutil.copy2(O/'selection_translation_map.json',F/'selection_translation_map.json')
print(F)
