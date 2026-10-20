# EA requirement structure correction — final native acceptance

Final directory: `revision_artifacts/ea_structure_native_final_20261016`.
This report supersedes the pending/failed intermediate status in `ea_core_verified_20261016/CORE_NATIVE_STATUS.md` and earlier all-tag/two-column candidates. Old outputs remain preserved.

## Deliverables

- `ea_native_sel_structure.xml`: final 23-requirement merged model, preserving original audited element/relationship GUIDs.
- `ea_native_OR041_structure.xml`, `ea_native_OR052_structure.xml`, `ea_native_OR008_structure.xml`: separate cases, same transformation; statically verified.
- `native_import_exact/ea_native_sel_isolated.xml`: exact fresh-GUID package successfully imported into the independent EA test repository. `guid_mapping.json` documents only technical GUID remapping; business IDs and all properties remain unchanged. Use this independent copy when importing beside existing packages to avoid identity collisions.
- `native_verified/diagram_5.png`: actual EA-exported 7053×2202 image; whole image and detailed crops visually inspected. Full text remains in id/text compartment; tree branches do not cross sibling boxes.
- `native_verified/field_validation.json`: 23 requirements, 352 properties, 20 relationship endpoints/type checked; zero errors.
- `native_verified/structure_validation.json`: 23 ClassifierRoles, 23 SysML1.4 xrefs, 20 native tree links; zero errors.
- `native_verified/native_roundtrip.xml`: actual EA native re-export, retained in EA's declared encoding. Unicode/property comparison uses lossless native SQL readback, not assumptions about native export encoding.
- `tests_final.xml`: 253 tests passed, 12.04 s. Test cache isolated from original application cache.
- `static_validation.json`: all four cases, exact model-property/identity preservation, examples and grade counts.

## Reference comparison

The actual attachment `ea_native_sel1.xml` was read and reproduced as `reference_ea_native_sel1.xml`. SHA256 exactly equals `b2893c10d44a6154dbdc0d3447e1526cd0847bd0613aaabe68bd4fbaab2bcd89`.

| Field | Reference evidence | Final behavior |
|---|---|---|
| Class / ClassifierRole | EARootClass is a Class; requirements are ClassifierRole inside Collaboration | Same structural roles; no replacement of requirement with arbitrary Class |
| name | Reference mixes ID/title in some labels | User's newer requirement takes precedence: meaningful title only, no ID/status/grade prefix or suffix |
| id / text | Independent XMI.content TaggedValue entries linked by modelElement; text uses `<memo>#NOTES#...` | Independent real business id and full normative text; preserved exactly from audited detailed input |
| documentation | ModelElement.taggedValue documentation/notes differs from SysML text | Existing role children, notes, documentation preserved byte-equivalent at parsed-tree level; never used as replacement for text |
| stereotype / xref | requirement, SysML1.4::requirement | Retained and actual native xrefs checked |
| metadata | Separate tagged properties exist; reference text also contains metadata in places | Latest audited input's criterion/evidence/source/grade/review route/Chinese fields preserved as separate attributes; not appended to text |
| diagram compartments | Tag=1 and ShowTags enable compartments | Header name plus id/text visible. SUPTAG suppresses only all noncore metadata names on this diagram; no property deleted |
| style / geometry | EA diagram element style and connector serialization | Gray sources, B blue, C orange; smaller full-text-sized boxes; tree-vertical routing using native Path and TREE before terminal Hidden |

The screenshot attachment could not be materialized locally due to the Library Windows file-output error; the parent conversation visually inspected it. This executor does not claim direct pixel inspection of that attachment. It did inspect the actual newly exported EA PNG and detailed crops directly.

## Concrete example

name: `Standby Pump Start on Alarm`
id: `OR041.3`
text: `When the seawater cooling system low supply alarm is triggered, the standby pump shall be capable of being started automatically or manually, or changeover to the standby pump shall be possible, to restore the cooling water supply.`

The merged sample has 3 gray sources, 7 B blue requirements, 13 C orange requirements; no A requirement or green legend is invented.

## Implementation

Changed `scripts/92_export_ea_native_xmi.py`; added `cooling_rag_mg/ea_structure.py` and `tests/test_ea_structure_revision.py`. Default CLI now emits the corrected structure, and legacy --compact routes through the correction. Output overwrite is refused. Names preserve full meaningful words. Validation checks business IDs, element/relationship identity, all properties, original notes/stereotype/style and core compartment visibility.

EA build 1628 confirmed SUPTAG filtering. Initial experiments showed that TREE=V alone after Hidden with an empty Path was ignored on import. The final serialization follows the working native export: explicit orthogonal Path and TREE=V before final Hidden=0. The final native acceptance required no post-import routing edits.

## Scope and acceptance limits

Only the user-authorized independent model was imported into:
`D:\cooling_rag_multigranular\cooling_rag_multigranular\revision_artifacts\ea_native_followup_20261016\structure_native_test_EMPTY.qea`.
Every COM mutation checked exact ConnectionString. No user model was switched, closed, deleted or overwritten; no registry/security/process changes. Prior test packages remain as audit evidence. The earlier duplicate-GUID call returned with no merged import; the final test used independent GUIDs and completed successfully.

Native visual acceptance covers the full merged 23 requirements and the earlier two-node minimum. Separate per-case outputs have static validation; their individual native imports were not repeated. The 11-child group makes the merged image wide: inspect at native zoom, or use per-case outputs. Layout supports one source-to-children level and explicitly rejects insufficient columns or unsupported nesting/cycles rather than silently omitting nodes. Font/version differences outside installed EA build 1628 remain untested. Installed EA trial watermark is retained.

Original audit data, legacy compact files (manifest hashes rechecked), paper/reply documents and prior unrelated working-tree changes were preserved. No paid API, publishing, commit or push. No pending native call or remaining task blocker.
