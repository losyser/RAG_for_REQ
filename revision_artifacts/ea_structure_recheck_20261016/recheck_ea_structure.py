import os, sys, json, hashlib, importlib.util
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(r'D:\cooling_rag_multigranular\cooling_rag_multigranular')
OUT=ROOT/'revision_artifacts/ea_structure_recheck_20261016'
sys.path.insert(0,str(ROOT)); os.chdir(ROOT)
from cooling_rag_mg.ea_structure import structure_xml, validate_structure, properties
from cooling_rag_mg.ea_compact import q
spec=importlib.util.spec_from_file_location('exporter',ROOT/'scripts/92_export_ea_native_xmi.py')
ea=importlib.util.module_from_spec(spec);spec.loader.exec_module(ea)
OUT.mkdir(exist_ok=False)
ref=ROOT/'revision_artifacts/ea_structure_native_final_20261016/reference_ea_native_sel1.xml'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(ref)=='b2893c10d44a6154dbdc0d3447e1526cd0847bd0613aaabe68bd4fbaab2bcd89'
rt=ET.parse(ref).getroot();rp=properties(rt)
report={'reference_sha256':sha(ref),'reference_class_count':len(list(rt.iter(q('Class')))),'reference_roles':[],'outputs':[]}
for r in rt.iter(q('ClassifierRole')):
    report['reference_roles'].append({'name':r.get('name'),'properties':rp.get(r.get('xmi.id'),{}),'element_tags':{v.get('tag'):v.get('value') for v in r.iter(q('TaggedValue'))}})
for name in ['sel','OR041','OR052','OR008']:
    src=ROOT/f'revision_artifacts/audit_20261015/ea/ea_native_{name}.xml'
    before=sha(src); original=src.read_text(encoding='utf-8')
    revised=structure_xml(original,ea.GRADE_STYLE);tree=ET.fromstring(revised)
    roles=list(tree.iter(q('ClassifierRole')));edges=list(tree.iter(q('Association')))
    assert validate_structure(original,revised)==[]
    assert ea.validate_xmi(revised,n_reqs=len(roles),n_edges=len(edges))==[]
    dest=OUT/f'ea_native_{name}_structure.xml';dest.write_text(revised,encoding='utf-8')
    p=properties(tree)
    previous=ROOT/f'revision_artifacts/ea_structure_native_final_20261016/ea_native_{name}_structure.xml'
    assert ET.tostring(ET.fromstring(previous.read_text(encoding='utf-8')))==ET.tostring(tree)
    assert before==sha(src)
    report['outputs'].append({'file':str(dest),'sha256':sha(dest),'source_sha256':before,'requirements':len(roles),'relationships':len(edges),'identical_to_previous_native_final':True,'examples':[{'name':r.get('name'),**p[r.get('xmi.id')]} for r in roles]})
(OUT/'recheck.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
import cooling_rag_mg.llm_cache as lc
lc._CACHE_DIR=OUT/'isolated_test_cache'
import pytest
sys.exit(pytest.main(['-q','tests','-p','no:cacheprovider','--basetemp',str(OUT/'pytest_tmp'),'--junitxml',str(OUT/'tests_full.xml')]))
