from pathlib import Path
import sys,shutil,json,hashlib,xml.etree.ElementTree as ET,importlib.util,collections
R=Path(r'D:\cooling_rag_multigranular\cooling_rag_multigranular');W=Path.cwd();O=R/'revision_artifacts/ea_structure_native_final_20261016'
sys.path.insert(0,str(R))
from cooling_rag_mg.ea_structure import structure_xml,validate_structure,properties,q
sp=importlib.util.spec_from_file_location('ea',R/'scripts/92_export_ea_native_xmi.py');ea=importlib.util.module_from_spec(sp);sp.loader.exec_module(ea)
report={}
for case in ['sel','OR041','OR052','OR008']:
 src=R/f'revision_artifacts/audit_20261015/ea/ea_native_{case}.xml';dest=O/f'ea_native_{case}_structure.xml'
 a=src.read_text(encoding='utf-8');b=structure_xml(a,ea.GRADE_STYLE);assert not dest.exists();dest.write_text(b,encoding='utf-8');t=ET.fromstring(b);p=properties(t)
 errors=validate_structure(a,b)+ea.validate_xmi(b,n_reqs=len(p),n_edges=len(list(t.iter(q('Association')))));assert not errors
 report[case]={'requirements':len(p),'relationships':len(list(t.iter(q('Association')))),'properties':sum(map(len,p.values())),'errors':errors,'grades':dict(collections.Counter(x.get('grade','source') for x in p.values())),'examples':[{'name':e.get('name'),'id':p[e.get('xmi.id')]['id'],'text':p[e.get('xmi.id')]['text'].removeprefix('<memo>#NOTES#')} for e in t.iter(q('ClassifierRole'))]}
shutil.copytree(W/'native_verified_routed',O/'native_verified')
shutil.copytree(W/'native_routed',O/'native_import_exact')
for n in ['ea_import_current_test.ps1','verify_native_readback.py','prepare_isolated_native.py','native_tree_export.xml']:
 shutil.copy2(W/n,O/n)
shutil.copy2(W/'references/ea_native_sel1_verified.xml',O/'reference_ea_native_sel1.xml')
assert hashlib.sha256((O/'reference_ea_native_sel1.xml').read_bytes()).hexdigest()=='b2893c10d44a6154dbdc0d3447e1526cd0847bd0613aaabe68bd4fbaab2bcd89'
for x in json.loads((R/'revision_artifacts/ea_compact_20261015/manifest.json').read_text()):
 assert hashlib.sha256((R/'revision_artifacts/ea_compact_20261015'/x['path']).read_bytes()).hexdigest()==x['sha256']
(O/'static_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:{x:v[x] for x in ['requirements','relationships','properties','grades']} for k,v in report.items()},indent=2))
