from pathlib import Path
import collections,hashlib,json,sqlite3,shutil,zipfile
R=Path(r'D:\cooling_rag_multigranular\cooling_rag_multigranular');O=R/'revision_artifacts/ea_paper_v4_20261016';A=O/'audit'
hashes=json.loads((A/'data_hashes_before.json').read_text(encoding='utf-8'))
changed=[p for p,h in hashes.items() if not (R/p).exists() or hashlib.sha256((R/p).read_bytes()).hexdigest()!=h]
checks={'data_files_checked':len(hashes),'changed_data_files':changed,'models':{}}
for name,old,new in [('111',O/'111_before_v4.qea',R/'revision_artifacts/ea_native_followup_20261016/111.qea'),('4x',A/'4x_before_v4.qea',Path(r'C:\Users\yando\Desktop\4x.qea'))]:
    tables={}
    with sqlite3.connect(old.as_uri()+'?mode=ro',uri=True) as before,sqlite3.connect(new.as_uri()+'?mode=ro',uri=True) as after:
        for table in ['t_package','t_object','t_objectproperties','t_connector','t_diagram','t_diagramobjects','t_diagramlinks','t_xref']:
            a=collections.Counter(before.execute('SELECT * FROM '+table));b=collections.Counter(after.execute('SELECT * FROM '+table))
            tables[table]={'before':sum(a.values()),'missing_or_changed':sum((a-b).values()),'added_or_changed':sum((b-a).values())}
    checks['models'][name]=tables
(A/'preservation_check.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
for p in ['cooling_rag_mg/ea_landscape_paper.py','cooling_rag_mg/ea_paper_figures.py','ui/pages/engineering.py','tests/test_ea_landscape_paper_v4.py']:
    dest=A/'code_after'/p;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/p,dest)
for name in ['prepare_paper_v4.py','browser_paper_v4.py','independent_ea_v4.ps1','audit_v4_finish.py']:
    dest=A/'scripts'/name;dest.parent.mkdir(exist_ok=True);shutil.copy2(Path(__file__).parent/name,dest)
(O/'HANDOFF.txt').write_text('''V4 CANDIDATE — EA import/render acceptance BLOCKED

Screenshot finding: the fourth v3 image was an overview of unrelated source requirements, not a root-and-children diagram. OR008 is present in the temperature image. Replace the unsuitable overview with three purposeful five-node thematic views.

Selected actual batch: batch_20260730_164747 / engineering_requirements_20260730_164801.
R001: root plus four children. R002: root, two children and two grandchildren; original hierarchy retained. R004: root plus four children.
Selected child status coverage: reported direct 4, reported indirect 5, gap 1, needs review 2. This purposefully includes all non-gap cases; it is not a population-proportion sample. Raw direct remains unverified. Default Evidence support matches the shared UI status layer; grades remain independent.

Short English semantic name, independent real id, full English text memo and Notes retained. Original Chinese names/text, raw JSON, source provenance, criteria and status properties retained. New paper_translation_status is separate from original translation_status. Assistant translations remain pending independent domain review.

Candidates: candidate/paper_v4_reliability.xml, paper_v4_parameters.xml, paper_v4_installation.xml (five requirements each); paper_v4_combined.xml (15 requirements, 12 original edges, 3 diagrams). No accepted paper/ deliverables exist yet.

Validation: 285 full-suite tests passed, including 8 new v4 tests for content/status preservation, original relationship endpoints, root position, independent properties, combined/split counts and rejection of invalid maps. See audit/tests.xml. Browser result, if completed, is audit/browser/acceptance.json; absence means browser acceptance is unfinished.

Blocker: independent EA.Repository COM activation failed with 0x80080005 CO_E_SERVER_EXEC_FAILURE. Existing active EA is 4x.qea, not 111.qea. Its connection was not switched. The own blank probe EA process PID 21608 could not be acquired independently through EA.App; it may remain running. Do not terminate user PID 2880. No candidate was imported and no native v4 PNG/EMF was generated. Independent native import/readback, combined one-import validation, visual acceptance and Library PNG/ZIP delivery remain incomplete.

Original EA/data preservation comparisons: audit/preservation_check.json. No paper/reply edits, paid APIs, external publishing, git commit/push or registry/security changes. Resume with an independently controllable test repository; do not import into user 4x/111 as a workaround.
''',encoding='utf-8')
with zipfile.ZipFile(O/'v4_candidate_xml_only_NOT_EA_VALIDATED.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted((O/'candidate').glob('*.xml')):z.write(p,'candidate/'+p.name)
    for p in [O/'HANDOFF.txt',A/'selection_translation_map.json']:z.write(p,p.relative_to(O))
print(json.dumps(checks,indent=2))
