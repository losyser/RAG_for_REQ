"""Build explicitly unverified core-tag display candidates from native evidence."""
import sys, json, sqlite3, xml.etree.ElementTree as ET, importlib.util
from pathlib import Path
ROOT=Path(r'D:\cooling_rag_multigranular\cooling_rag_multigranular')
sys.path.insert(0,str(ROOT))
from cooling_rag_mg.ea_structure import properties, q, validate_structure
from cooling_rag_mg.ea_compact import merge_style
spec=importlib.util.spec_from_file_location('ea',ROOT/'scripts/92_export_ea_native_xmi.py')
ea=importlib.util.module_from_spec(spec);spec.loader.exec_module(ea)
out=Path('native_attempt')
c=sqlite3.connect('file:D:/Program Files/Sparx Systems/EA Trial/EAExample.qea?mode=ro',uri=True)
sample=c.execute("select Diagram_ID,Name,StyleEx from t_diagram where StyleEx like '%SUPTAG=%'").fetchall()
(out/'native_suptag_evidence.json').write_text(json.dumps(sample,ensure_ascii=False,indent=2),encoding='utf-8')
assert sample and any('SUPTAG=quantityKind' in r[2] for r in sample)
for case in ['OR041_minimal','sel']:
 p=ROOT/f'revision_artifacts/ea_structure_20261016/ea_native_{case}_structure.xml'
 original=p.read_text(encoding='utf-8');root=ET.fromstring(original)
 props=properties(root);hidden=sorted({k for v in props.values() for k in v if k not in {'id','text'}})
 for diagram in root.iter(q('Diagram')):
  for tv in diagram.find(q('ModelElement.taggedValue')):
   if tv.get('tag')=='styleex':
    tv.set('value',merge_style(tv.get('value',''),{'SUPTAG':','.join(hidden)}))
  diagram.set('name',diagram.get('name')+'_CoreTags_CANDIDATE')
  nodes={e.get('subject'):e for e in diagram.iter(q('DiagramElement')) if e.get('subject') in props}
  children={}
  for edge in root.iter(q('Association')):
   a,b=[e.get('type') for e in edge.iter(q('AssociationEnd'))]
   children.setdefault(a,[]).append(b)
  child_ids={c for cs in children.values() for c in cs};y=40
  def place(rid,x,y):nodes[rid].set('geometry',f'Left={x};Top={y};Right={x+300};Bottom={y+180};')
  for rid in nodes:
   if rid in child_ids:continue
   cs=children.get(rid,[]);place(rid,220 if len(cs)>1 else 40,y);y+=260
   for start in range(0,len(cs),2):
    for j,cid in enumerate(cs[start:start+2]):place(cid,40+j*360,y)
    y+=260
  for node in diagram.iter(q('DiagramElement')):
   if 'NSL=1;' in node.get('style',''):node.set('geometry',f'Left=10;Top=10;Right=740;Bottom={y};')
 xml='<?xml version="1.0" encoding="UTF-8"?>\n'+ET.tostring(root,encoding='unicode').replace(' />','/>')
 assert not validate_structure(original,xml)
 assert not ea.validate_xmi(xml,n_reqs=len(props),n_edges=len(list(root.iter(q('Association')))))
 (out/f'ea_native_{case}_core_tags_CANDIDATE.xml').write_text(xml,encoding='utf-8')
 (out/'suppressed_tag_names.txt').write_text(','.join(hidden),encoding='utf-8')
print('Created two UNVERIFIED candidates; all model properties preserved; id/text not in SUPTAG')
