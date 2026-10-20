from pathlib import Path
import xml.etree.ElementTree as E,json
O=Path(r'D:\cooling_rag_multigranular\cooling_rag_multigranular\revision_artifacts\ea_structure_native_final_20261016');N=O/'native_verified'
read=lambda n:E.fromstring((N/n).read_text(encoding='utf-8-sig'))
r=E.parse(N/'native_roundtrip.xml').getroot();q=lambda n:'{omg.org/UML1.3}'+n
roles=list(r.iter(q('ClassifierRole')))
assert len(roles)==23
links=list(read('diagramlinks.xml').iter('Row'));assert len(links)==20
assert all('TREE=V;' in (x.findtext('Style') or '') for x in links)
guids={'{'+x.get('xmi.id')[5:].replace('_','-')+'}' for x in roles}
xrefs=[x for x in read('xref.xml').iter('Row') if x.findtext('Client') in guids and 'SysML1.4::requirement' in (x.findtext('Description') or '')]
assert len(xrefs)==23,len(xrefs)
result={'native_classifier_roles':len(roles),'native_sysml14_xrefs':len(xrefs),'native_tree_vertical_links':len(links),'errors':[]}
(N/'structure_validation.json').write_text(json.dumps(result,indent=2));print(result)
