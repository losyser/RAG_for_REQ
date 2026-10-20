# EA structure request: current-state reconciliation and fresh verification

This invocation found the requested repair already implemented in the current working tree, with later structure/native acceptance artifacts. It did not reapply or roll back those changes. No source code, manuscript, response, original experimental files, old exports, or EA repositories were modified by this invocation. New outputs only were generated, offline, with no paid APIs, external publication, Git commit or push.

Project: `D:\cooling_rag_multigranular\cooling_rag_multigranular`.
New deliverable directory: `revision_artifacts/ea_structure_recheck_20261016`.

## Fresh results

- `ea_native_sel_structure.xml`: 23 requirements / 20 Nesting relationships.
- `ea_native_OR041_structure.xml`: 6 / 5.
- `ea_native_OR052_structure.xml`: 5 / 4.
- `ea_native_OR008_structure.xml`: 12 / 11.
- `recheck.json`: reference comparison fields, full output name/id/text and all metadata, hashes, preservation results.
- `tests_full.xml`: **285 passed in 13.80 s**, isolated test cache, no original cache clearing.

All four generated XML trees exactly match their existing counterparts in `revision_artifacts/ea_structure_native_final_20261016`. The original audited inputs were hash-checked before and after transformation. The validator checks identities, business IDs, independent properties, notes/stereotypes, relation endpoints, diagram identities and visible core compartments. No new implementation changes were necessary for the explicitly selected structure export.

## Reference actually read

The supplied Library XML was resolved and read; its full local verified copy was parsed and compared. SHA256 is exactly `b2893c10d44a6154dbdc0d3447e1526cd0847bd0613aaabe68bd4fbaab2bcd89`.

Reference: `revision_artifacts/ea_structure_native_final_20261016/reference_ea_native_sel1.xml`.

| Aspect | Reference | Structure output |
|---|---|---|
| Class / ClassifierRole | One EARootClass; 11 requirement ClassifierRoles under Collaboration | Retains these structural roles; 23 current sample requirements |
| name | ID plus title, sometimes truncated | Meaningful complete title alone; newer user requirement supersedes reference labels |
| independent id/text | Present: direct XMI.content TaggedValues linked by modelElement | One real business id and full memo text per requirement |
| text content | Some old reference text includes criterion/grade annotations | Complete audited normative sentence preserved; metadata retained as independent properties |
| documentation | Separate element tagged value | Preserved; not used as substitute for SysML text |
| stereotype/xref | requirement and SysML1.4::requirement | Preserved |
| diagram | Tag=1 in reference; previous compact export hid tags | Name header plus id/text compartment; SUPTAG hides only noncore metadata on the diagram, without deleting it |
| colors | Reference includes old A samples | Current sample: 3 gray source / 7 B blue / 13 C orange; no invented A |

The screenshot `libfile_d2a60ea829008191bf20daec469813bf` was successfully read through Library (filename image(20261016-005131).png, 1106x928, 141433 bytes). Its returned OCR describes the old OR041 ID/title/status labels. Direct pixel access remains blocked: the current official materialization helper fails on Windows at `os.setxattr`. This invocation does not claim to have visually inspected that attachment. It did directly view the existing actual EA native output detail images.

## Example

- name: `Standby Pump Start on Alarm`
- id: `OR041.3`
- text: `When the seawater cooling system low supply alarm is triggered, the standby pump shall be capable of being started automatically or manually, or changeover to the standby pump shall be possible, to restore the cooling water supply.`

Criterion, evidence IDs/sources, tier, grade, routing and Chinese source fields remain separate properties. They are not injected into the name or normative sentence.

## Implementation and invocation

Existing implementation: `scripts/92_export_ea_native_xmi.py`, `cooling_rag_mg/ea_structure.py`, `tests/test_ea_structure_revision.py`.

IMPORTANT: current CLI defaults to a later folded mode; earlier reports saying structure is the default are stale. Use the explicit flag for this request:

```bat
run_py.bat scripts/92_export_ea_native_xmi.py --structure --input-xmi revision_artifacts/audit_20261015/ea/ea_native_sel.xml --out-dir revision_artifacts/ea_structure_NEW
```

Existing output files are refused rather than overwritten. This invocation preserves the newer folded/UI behavior instead of reverting unrelated work.

## Native acceptance boundary

This invocation performed static regeneration and the current full test suite; it did not connect to or mutate EA. Prior native acceptance evidence exists in `revision_artifacts/ea_structure_native_final_20261016/native_verified`: field_validation.json reports 23 requirements / 352 properties / 20 relationships, zero errors; structure_validation.json reports 23 ClassifierRoles / 23 SysML1.4 xrefs / 20 tree links, zero errors. Native PNGs show the visible name/id/text compartments. Fresh outputs are XML-tree-identical to those previously validated inputs.

The prior import used an independent fresh-GUID variant (`native_import_exact/ea_native_sel_isolated.xml`) to avoid collisions. Use that existing validated copy for imports beside other packages; do not import identity-preserving artifacts into user models with matching GUIDs. No new native acceptance is claimed. Separate case imports were not repeated; installed EA build 1628, fonts, wide 11-child layout and one-level hierarchy remain the documented limits. Trial watermark remains intact.

Remaining blocker: direct pixel inspection of the supplied screenshot in this Windows execution environment. There is no test failure or outstanding structure-generation change in this invocation.
