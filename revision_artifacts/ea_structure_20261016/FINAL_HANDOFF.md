# EA structure correction — 2026-10-16

Project: `D:\cooling_rag_multigranular\cooling_rag_multigranular`

## Delivered

In `revision_artifacts/ea_structure_20261016/`:

- `ea_native_sel_structure.xml`: 23 requirements, 20 original Nesting relationships.
- `ea_native_OR041_structure.xml`: 6 requirements / 5 relationships.
- `ea_native_OR052_structure.xml`: 5 / 4.
- `ea_native_OR008_structure.xml`: 12 / 11.
- `ea_native_OR041_minimal_structure.xml`: actual OR041 + OR041.1 / 1 relationship; minimal import fixture.
- `static_validation.json`: every name/id/full text/metadata, counts, grades, input/output SHA256, previous compact artifact hash verification.
- `tests_final.xml`: **251 passed**, no failures/errors/skips, 11.57 seconds reported by pytest.
- `92_export_ea_native_xmi.before.py`: exporter as found before this change, preserving prior uncommitted work.
- `ea_native_sel1_reference_verified.xml`: supplied reference, SHA256 **b2893c10d44a6154dbdc0d3447e1526cd0847bd0613aaabe68bd4fbaab2bcd89**.

Changed source: `scripts/92_export_ea_native_xmi.py`; new `cooling_rag_mg/ea_structure.py`; new `tests/test_ea_structure_revision.py`. No paper/reply, original experimental result, old export, or EA model changes. No API generation, commits, push, or publication.

## Reference comparison and actual defect

The entire Library XML was read. Its text, restored to CRLF, reproduces the supplied byte hash exactly. Download materialization failed on Windows `os.setxattr`; the hash-verified reconstruction is explicitly from Library read content, not claimed as a successful materialization.

| Field | Supplied reference | Correction |
|---|---|---|
| Class/ClassifierRole | One `EARootClass`; 11 requirements as ClassifierRole under Collaboration | Retained this XMI 1.1/UML1.3 hierarchy, not converted to ordinary UML Class |
| name | ID plus title, e.g. `OR041.1  Low pressure alarm for seawater cooling` | Latest user instruction overrides ID prefix: title only; no status/grade/route |
| id/text | 11 independent pairs, direct children of `/XMI/XMI.content`, linked through `modelElement` | Exactly one pair per requirement, existing business IDs and complete text preserved |
| tag identity | Reference uses distinct random tag xmi.id values | Existing tag IDs retained during transformations; historical stems retained for newly built models, without asserting they are necessary for memo recognition |
| text | `<memo>#NOTES#` plus content, including some criterion/grade annotations | Current audited text already contains the complete normative sentence alone; retained exactly, metadata stays in its own properties |
| documentation | Separate element notes, often content plus metadata | Preserved exactly from audited input, never substituted for text |
| stereotype/xref | `requirement`, `ea_stype=Requirement`, `SysML1.4::requirement`, CLT equals element GUID | Preserved exactly |
| diagram | `Tag=1`, `ShowNotes=0`, rectangular requirement notation | `Tag=1`; diagram `ShowTags=1`, `ShowNotes=0`; DUID and connector endpoints retained |
| color | Reference contains older A examples | Current actual source grades only: 3 source gray, 7 B blue, 13 C orange; no A fabricated |

Reference example: lines 55 and 630–631 associate ClassifierRole `EAID_4A1E3768_A1F1_46D7_8637_5B4CD361AF46` with `id=OR041.1` and its memo text. The ID tag's own GUID is `EAID_75F9EA9C_63F9_43E6_B9A1_0B2DDA60CD0E`, distinct from the requirement GUID. Neither is used as its title.

The previous compact export already stored id/text but hid the compartment using `Tag=0` and `ShowTags=0`, and assembled ID/title/status as a multiline name. That was the observed defect, not absent model fields. Parent conversation directly inspected the supplied screenshot and confirmed this. This executor received its OCR/image pointer; pixel inspection here was blocked by Windows materialization support, so no local pixel inspection is claimed.

Official supporting documentation: https://www.sparxsystems.com/enterprise_architect_user_guide/17.2/modeling_languages/sysml_requirements_toolbox.html (Notes: SysML requirements contain Text and ID tags). This documents the property model; it does not validate this generated file's rendering.

## Concrete output example

name: `Low Supply Alarm Display Requirement`

id: `OR041.1`

text (after memo marker):

> When the seawater cooling system is configured with a main circulation pump, a low supply alarm function shall be provided. The alarm signal shall be capable of being displayed on the bridge or at the main control station so that operators can promptly start the standby pump or change over to the standby pump.

The criterion retains its complete original TBD placeholder; grade=C, review_route=OPEN_ITEM, evidence_ids=`E-HT-ALARM-001; E-PUMP-ALARM-002`, and evidence sources/tier/verification/original Chinese text remain separate properties. All 23 examples are in static_validation.json. Truncated legacy title words (Requiremen, Complianc, Settin, Sett) are repaired without truncating titles or modifying the requirement text.

## Validation and reproducibility

All four delivered case outputs passed existing XMI validation plus semantic-preservation checks: business IDs, element IDs/types, content-level properties, stereotype/xref/documentation/style, relationship IDs/endpoints, DUID/SOID/EOID, unique IDs, resolved references, nonoverlapping rectangles and enclosing package geometry. Every file in the previous compact manifest still matches its old SHA256. Source XML files were read only.

New regression coverage includes true independent fields rather than label strings, detailed and compact input, Unicode/numbers/whole-word titles, rejection of missing names, hidden tags and content loss, positive layout columns, both CLI flags, and refusal to overwrite. Old `--compact` CLI now redirects to corrected structure view, preventing recurrence. The old compact transformation module remains for historical compatibility/tests; it is not called by the exporter CLI.

Example command from project directory:

```bat
run_py.bat scripts/92_export_ea_native_xmi.py --structure --input-xmi revision_artifacts/audit_20261015/ea/ea_native_sel.xml --out-dir revision_artifacts/ea_structure_NEW
```

For fresh builds the default export is now `_structure.xml`. A fresh OR041 default build also passed. Use run_py.bat (sets UTF-8 and clears unrelated system PYTHONPATH); a direct command without UTF-8 initially failed when printing a Unicode translation warning, then succeeded with the wrapper-equivalent environment.

The full suite was run with Python3.11 in cooling_rag_env, PYTHONPATH cleared, OMP_NUM_THREADS=8, bytecode disabled, isolated diskcache and fresh pytest temporary directory. An initial sandbox run had 248 passes and one unrelated test fixture write permission failure; the final permitted run has 251 passes after adding CLI regression tests. The original disk cache was not cleared. Global git diff whitespace warnings belong to pre-existing user-owned `data/search_results/exp_v4/ea_native_sel.xml`; it was not edited.

## Native acceptance boundary

**Static validation only. No native EA import/readback or rendered screenshot of the new output.** Read-only EA.App attachment succeeded outside the sandbox and reported LibraryVersion=1628 and current connection `revision_artifacts/audit_20261015/ea/audit_import.qea`. The current model was not closed, switched, imported into, or modified. No new EA.Repository activation, DCOM/security changes, registry changes, or process termination was attempted.

The corrected diagram exposes all retained tags rather than guessing an unverified per-tag hide/filter serialization. A wider two-column layout reserves space conservatively for all retained content. It does not delete text, hide all attributes, or promise an exact two-row-only compartment. Actual EA memo rendering, font/line wrapping, tag order, and multirow connector routing still require import into a **new independent empty model**, first using the two-node fixture, then the per-case outputs. Do not import into the user's current model: exported identity intentionally matches the previous audited outputs, including the package ID, to preserve traceability. No claim of a finished native visual acceptance is made.
