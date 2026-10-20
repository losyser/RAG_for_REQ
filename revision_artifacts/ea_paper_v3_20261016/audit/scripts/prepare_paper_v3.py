from pathlib import Path
import sys,json,xml.etree.ElementTree as ET,re
R=Path(r'D:\cooling_rag_multigranular\cooling_rag_multigranular');O=R/'revision_artifacts/ea_paper_v3_20261016';sys.path.insert(0,str(R))
from cooling_rag_mg.ea_paper_figures import paper_bundle
from cooling_rag_mg.ea_status_view import status_view
from cooling_rag_mg.ea_structure import q,properties
from cooling_rag_mg.ea_presentation import serialize
src=R/'revision_artifacts/ea_english_small_figures_20261016';mapping=json.loads((src/'selection_translation_map.json').read_text(encoding='utf-8'))
for f in mapping['figures']:f['name']=f['name'].replace('english_','paper_v3_')
source=(src/'source.xml').read_text(encoding='utf-8')
for mode,dirname in [('Rule grade','paper'),('Evidence support','audit/support_mode_static')]:
 files=paper_bundle(status_view(source,mode,batch_id='exp_v4_OR041_OR052_OR008'),mapping)
 for name,data in files.items():
  dest=O/(name if name.startswith('audit/') else dirname+'/'+name);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
spec=[];titles=['Cooling Requirement Scopes','Low Supply Alarm','Pump Maintenance Access','Temperature Control']
for f,title in zip(mapping['figures'],titles):
 path=O/'paper'/(f['name']+'.xml');root=ET.parse(path).getroot();pkg=next(root.iter(q('Package')));pkg.set('name',title);d=next(root.iter(q('Diagram')));d.set('name',title);path.write_text(serialize(root),encoding='utf-8')
 p=properties(root);roles=[{'xml_id':e.get('xmi.id'),'name':e.get('name'),'notes':p[e.get('xmi.id')]['text'].removeprefix('<memo>#NOTES#'),'tags':p[e.get('xmi.id')]} for e in root.iter(q('ClassifierRole'))]
 tags={e.get('tag'):e.get('value') for e in d.find(q('ModelElement.taggedValue'))}
 spec.append({'file':f['name'],'package_name':'Paper v3 - '+title,'package_xml_id':pkg.get('xmi.id'),'diagram_name':title,'diagram_xml_id':d.get('xmi.id'),'styleex':tags['styleex'],'eastyle':tags['EAStyle'],'roles':roles,'edges':[{'xml_id':e.get('xmi.id'),'ends':[x.get('type') for x in e.iter(q('AssociationEnd'))]} for e in root.iter(q('Association'))],'view':[dict(e.attrib) for e in d.iter(q('DiagramElement'))]})
(O/'audit/native_spec.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding='utf-8');(O/'audit/current_mapping.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2),encoding='utf-8')
print('Four English paper XMLs; separate audit/support-mode views.')
