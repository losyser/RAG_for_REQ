# Native EA attempt — 2026-10-16, follow-up

This supplements (does not replace) ea_structure_20261016/FINAL_HANDOFF.md.

## Actual attempt and blocker

At 01:08:59 UTC, read-only EA.App connection returned session `3FC4E5BCE81A`, with existing model `D:\cooling_rag_multigranular\cooling_rag_multigranular\revision_artifacts\audit_20261015\ea\audit_import.qea`.

Exactly one independent `New-Object -ComObject EA.Repository` activation was attempted outside the sandbox, using Windows Framework PowerShell. At 01:10:59 UTC it failed with **0x80080005 (CO_E_SERVER_EXEC_FAILURE)**, CLSID `{67F4E0FA-46A7-4255-B084-69A9433D08C3}`. This is a new observed failure, not a historical assumption. See attempt.log and ea_native_attempt.ps1.

The script would only open a new test file after confirming a distinct InstanceGUID and empty ConnectionString. Activation failed before those operations. No import, native readback, PNG export or renderer acceptance occurred. The existing model connection was checked afterward and remained unchanged. No activation retry, registry/security modification, process termination, or model switch was performed.

## Display mechanism grounded in official and local evidence

Official EA documentation describes Diagram Properties > Features > Suppress Compartment Items > Tag Names: listed names are suppressed in the diagram's tags compartment. This is a display filter, not deletion of model properties:

https://sparxsystems.com/enterprise_architect_user_guide/17.1/modeling_fundamentals/appearance_options_feat.html

Official Feature Visibility documentation also states that the tags compartment normally lists all nonempty tagged values, confirming that simply enabling all tags can expose verbose criterion/TBD metadata:

https://sparxsystems.com/enterprise_architect_user_guide/17.1/modeling_fundamentals/setfeaturevisibility.html

The installed vendor `D:\Program Files\Sparx Systems\EA Trial\EAExample.qea` was queried through SQLite **mode=ro**. Native diagram StyleEx contains `SUPTAG=quantityKind`. Exact native diagram rows/styles are in native_suptag_evidence.json; broader inspected style keys are in vendor_styles_readonly.json. This supports the SUPTAG serialization, but is not a native import test of our generated file or proof that a comma-separated list behaves identically in this installed build.

## Explicitly unverified candidates

- ea_native_OR041_minimal_core_tags_CANDIDATE.xml
- ea_native_sel_core_tags_CANDIDATE.xml

These candidates retain `Tag=1`, `ShowTags=1`, `ShowNotes=0`; add `SUPTAG` containing all non-core property names; never suppress `id` or `text`. All existing model properties, including full memo text and full criterion/TBD, remain equal to the structure-version input. Only diagram styling/geometry changes. They use 300×180 boxes and two child columns as an initial visual-test configuration. They pass semantic-preservation and existing XMI static checks.

**These are not accepted production output, and not verified native images.** The prior all-tags structure view must also not be represented as readability-approved. Core-tag filtering, memo recognition, text/ID visibility, label wrapping, actual node size and connector routes remain to be checked in EA.

The exporter code and its 251-pass test result were not changed during this follow-up. The exploratory candidate builder is included for reproducibility, not installed as the default exporter path.

## Concrete next action requiring user-assisted setup

A fresh copy of vendor EABase.qea is supplied as `structure_native_test_EMPTY.qea` in this follow-up directory. It has no imported requirements. Do not import into or switch the currently open audit_import.qea.

Ask the user to launch a **separate EA application window/process** and open this new empty test file there, retaining the original window/model. Once the new instance is independently identifiable, import the minimal CANDIDATE file, inspect Name and separate id/text plus complete memo/criterion values, and export the actual diagram image. If it passes, use another independent test copy for the merged candidate. If the only available route requires switching/closing the existing model, obtain explicit confirmation before doing so.

No additional model changes have been made. Native acceptance remains BLOCKED by this observed independent-server activation failure.
