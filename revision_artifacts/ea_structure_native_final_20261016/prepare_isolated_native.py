from pathlib import Path
import xml.etree.ElementTree as ET,uuid,json,sys
ROOT=Path(r'D:\cooling_rag_multigranular\cooling_rag_multigranular')
sys.path.insert(0,str(ROOT))
from cooling_rag_mg.ea_structure import structure_xml,q
import importlib.util
spec=importlib.util.spec_from_file_location('ea',ROOT/'scripts/92_export_ea_native_xmi.py');ea=importlib.util.module_from_spec(spec);spec.loader.exec_module(ea)
run=sys.argv[1] if len(sys.argv)>1 else 'native_final23'
source=ROOT/'revision_artifacts/audit_20261015/ea/ea_native_sel.xml'
xml=structure_xml(source.read_text(encoding='utf-8'),ea.GRADE_STYLE)
root=ET.fromstring(xml);mapping={}
for e in root.iter():
 old=e.get('xmi.id')
 if old:
  prefix='EAPK_' if old.startswith('EAPK_') else 'EAID_'
  mapping[old]=prefix+str(uuid.uuid4()).upper().replace('-','_')
for old,new in mapping.items():
 xml=xml.replace(old,new)
 if old.startswith('EAID_'):
  xml=xml.replace('{'+old[5:].replace('_','-')+'}','{'+new[5:].replace('_','-')+'}')
xml=xml.replace(' 01_Requirements','CoreTag_23_'+run).replace('REQ_Selected_Requirements_Structure','REQ_'+run)
out=Path(run);out.mkdir(exist_ok=True)
(out/'ea_native_sel_isolated.xml').write_text(xml,encoding='utf-8')
(out/'guid_mapping.json').write_text(json.dumps(mapping,indent=2),encoding='utf-8')
print(out.resolve())
