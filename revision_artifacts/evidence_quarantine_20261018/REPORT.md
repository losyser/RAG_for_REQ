# Explicit evidence quarantine — offline repair and saved-response replay

**Outcome:** an opt-in source-review layer now removes quarantined evidence content before generation and withholds affected rows from the canonical delivery list after generation. Replaying all nine saved model responses retains 75 of 77 rows for further review; both OR023 fourth rows are withheld as `blocked_numeric`. Their raw model text is preserved. This demonstrates containment of the explicitly flagged source, **not improved model accuracy or correctness of the other 75 rows**.

No model/API call, recharge, new credential, system change, paper/main-experiment edit, new human review or KB factual edit occurred in this batch. All diagnostics are under this new directory. Existing paid-run artifacts are unchanged.

## Checkpoint, activation and traceable review record

Checkpoint tag `checkpoint/evidence-quarantine-20261018` points to `64946f55cb616c0479a87265511410f197fa0994`. Existing unrelated dirty work was retained.

Registry: `development_review_flags.json`, version `evidence-quarantine-v1`. It is **not automatically loaded** by the UI, experiment scripts or configuration. This development replay explicitly loads and passes it. No flags, an empty list, or no active quarantine preserves legacy behavior. `released` is an explicit registry state; no numerical observation automatically releases a source.

The only development flag is **E-HT-COMP-036**:

- Reason: the previously reviewed official MAN 49/60 **Revision 12.2025/3.0, dated 2025-12-03**, printed/PDF page **134**, does not support the recorded engine-inlet preheat `-100°C`; the original local source edition is **unknown/unmatched**.
- Official URL: https://man-es.com/applications/projectguides/4stroke/Propulsion/PG_P-II_4960.pdf
- Previously reported official-document SHA256: `29da4ba210bc2bba9b3f00d6f4f0aee15c6c7847568d5dd69355b3028692ffc1`.
- Origin: the prior coordinator verification documented in `revision_artifacts/bounded_optimization_20261018/OPTIMIZATION_REPORT.md`. This task did not refetch or independently inspect that PDF, nor invent a matching local original.
- The flag includes the local evidence text SHA256, explicit scope/reason and review ID. Replay asserts that the current local text matches that recorded hash. The flag remains conservative at the evidence-ID level; text changes do not silently release it.

This is **not** a claim that every field on the page has been verified, that all editions disagree, that -100°C is impossible in every application, or that negative temperatures are generally invalid. Reliable per-parameter binding is absent, so the whole unit is quarantined rather than guessing which table fragments can safely remain. No replacement value is invented.

## Implementation and delivery boundary

New pure module: `cooling_rag_mg/evidence_quarantine.py`.

**Before prompting:** `mask_prompt_evidence` replaces each flagged identity-bearing evidence record with a small background-only/TBD warning. It removes that record's body, extracted values, metadata, summaries and all copies in UI topic groups. It does not merely append a warning next to the original numeric values. V4 selects using the existing explicit selection policy first, then masks selected records; it does not silently rerank them. Healthy records remain unchanged. Source IDs/review IDs are provenance identifiers, not engineering values.

**After generation:** `gate_delivery` checks the union of all citation channels and any declared parameter-binding evidence IDs. An extra model-provided schema field cannot hide a flagged ID in another channel. It does not infer the originating source from matching numeric values. Model-declared bindings are unverified declarations, even when their shape is complete; malformed bindings still expose any flagged evidence ID they contain.

- Any row referencing a quarantined source is removed from the canonical delivery list. If possible numeric content is present, its review status is `blocked_numeric`; otherwise it is `needs_review` background material.
- Mixed healthy/quarantined references conservatively withhold the **whole row**, even if it also declares a healthy parameter binding. Matching numbers or untrusted bindings cannot override a flagged reference. This may withhold valid healthy content; no automatic claim splitting is attempted.
- Numeric-looking rows with no usable in-scope citation are withheld as `needs_review`; their origin is unknown, not attributed to the flagged source by coincidence.
- Healthy source IDs carrying legitimate negative temperatures, including the same numeric string as a quarantined value, are not blocked merely for that number. The result still reports unknown semantic support/applicability and unknown or unverified binding provenance. `no_known_flag_not_verified` never means “validated.”
- The digit detector is deliberately conservative and is only used to label potential numeric content; TBD placeholders are removed before that check. It can overflag identifiers/quantities and is not a scientific numeric parser. It never determines source attribution.

The removed rows remain in the review report as `original_row` (the input to this gate; for UI this is after the existing normalizer). Saved raw model responses remain separately untouched. No model value is edited in place to a guessed value. The layer provides safe background warnings and TBD instructions, not invented replacement requirements.

**UI delivery:** canonical `engineering_requirements` excludes withheld rows and their dependent descendants. Relationships to removed rows are withheld rather than silently reparented. If rows were withheld, model-written summary/assumption/confirmation/gap text is moved to the audit channel and the ordinary summary becomes a safe TBD/review notice, so a summary cannot continue to present a removed threshold as a formal requirement. The root delivery status is `needs_review`. Review metadata may intentionally contain original suspect text; it must not be exported as the canonical requirement list.

**V4 delivery:** the list-returning generator returns only retained rows. When active flags are supplied it requires a mutable `delivery_report` before any client call, so blocked outputs have an explicit review destination. This does not change the default no-flag return shape.

## Actual entrypoints and explicit development use

```python
flags = load_review_flags("revision_artifacts/evidence_quarantine_20261018/development_review_flags.json")
review = {}
rows = generate_structured_shalls(
    requirement, evidence, client, model,
    quarantine_flags=flags, delivery_report=review,
)
ui_output = generate_engineering_requirements_for_requirement(
    requirement_object, retrieval_payload, quarantine_flags=flags,
)
```

This example describes integration, not an invocation made in this batch: replay clients/completions are mocks and socket connections are disabled. UI batch generation forwards the flag option; direct normalization also accepts it. The real UI graph masks prepared context and gates normal, repaired and fallback outputs. The outer fallback is gated too. A conservative fallback may retain a nonnumeric citation-free TBD draft, but cannot recover quarantined numbers or claim direct verification. Existing legacy repair behavior is not changed by this source-isolation feature; the offline tests mock/block it and no repair API was called.

Main experiment scripts, user-modified UI pages and global defaults are not silently switched. This opt-in changes delivery policy and must be recorded as a separate development strategy. Undo via a scoped revert, not a hard reset of the dirty working tree.

## Tests and all-nine-response replay

Final selected offline suite: **251 passed, no skips**. It includes the prior 237 cases plus 14 quarantine cases/parameterized paths. The launcher isolates the legacy cache and disables sockets. Initial quarantine-only run had 11 passes/2 failures because tests incorrectly demanded an empty output for safe fallback drafts. Assertions were corrected to require no quarantined value and no direct-support claim in those fallback paths; the failed log is retained. Later checks added mixed-schema ID union and unknown-ID containment.

Coverage includes flagged and mixed-source references, missing IDs, malformed/declared bindings, duplicate/invalid review states, released/no-flag identity behavior, legitimate negative values and same-number healthy evidence, hidden metadata/group copies, UI hierarchy/summary isolation, actual v4 completion entry and UI graph normal/repaired/failure/budget paths.

`replay_quarantine.py` runs the actual generation entrypoints using **all nine saved responses as canned completions**, never new generation. It writes new prompt hashes and separated delivery/review artifacts. V4 no-flag outputs are asserted equal to the saved raw shall rows. UI applies the existing current normalizer before the new delivery gate. This is a containment replay of pre-quarantine outputs, not a prediction of how a model would answer the new masked prompts.

| Saved case / arm | Raw rows | Delivery rows | Withheld |
|---|---:|---:|---:|
| OR001 new, unpaired | 10 | 10 | 0 |
| OR010 old | 18 | 18 | 0 |
| OR010 new | 9 | 9 | 0 |
| OR023 old | 9 | 8 | **row 4, blocked_numeric** |
| OR023 new | 8 | 7 | **row 4, blocked_numeric** |
| R001 old | 8 | 8 | 0 |
| R001 new | 5 | 5 | 0 |
| R002 old | 5 | 5 | 0 |
| R002 new | 5 | 5 | 0 |
| Total | **77** | **75** | **2** |

For both OR023 contexts, the actual captured quarantine prompt no longer contains `-100`; it includes the quarantine warning. Both saved offending rows cite the flagged source and are removed from the canonical list, regardless of the new output's extra “verify first” note. Other values in those same mixed-purpose rows are also withheld; this is the documented conservative cost of whole-row quarantine.

Artifacts: `REPLAY.json` contains counts, request/billing audit and hashes; `DELIVERY_AND_REVIEW.json` contains the separate delivery rows, withheld originals and mocked masked prompts; `tests_final.txt` and `replay_log.txt` contain verification output.

## Reanalysis of the four actual completed pairs

The completed model run still has **four**, not five, complete pairs: OR010, OR023, R001, R002. OR001-new remains unpaired because its old request failed; R003-old received 402 and R003-new was not sent. Historical forecasts of five possible pairs were conditional plans, not actual results.

- **OR010, 18 → 9 rows:** repeated hardness/chloride rows were consolidated, while some storage/freezing/service-life numbers became TBD-oriented criteria with applicability qualifications. New rows 6–8 explicitly say manufacturer/model/concentration or coolant type remains pending. Some numeric values still occur inside TBD hints, which are not validated thresholds. Both versions already use dGH in generated text; this run does not prove that classifier support for dGH improved generation. Fewer rows may also omit useful content; recall was not measured.
- **OR023, 9 → 8 rows:** both versions put -100°C in fourth-row measurable criteria. The newer acceptance text asks for verification but did not prevent propagation. The new eighth row concerns system interfaces rather than the older temperature-setpoint row; selection and instructions changed together, so this is a combined treatment, not a one-change causal test. The new quarantine gate now withholds the fourth rows offline; it does not retroactively make the original model generation successful.
- **R001, 8 → 5 rows:** the newer output reorganizes pump/protection, tropical-design and control requirements after real body text was restored. The old output had repeated or overlapping high-level statements. That observation is not a completeness/authority judgment, and new real text still includes partial context. Raw new direct-status self-reports are not evidence of independent verification.
- **R002, 5 → 5 rows:** the old first row asserts a 36°C difference; the new first row instead defers temperature/pressure/flow limits to manufacturer documents. The new text reorganizes monitoring, manual fallback and thermal-balance requirements. This task does not verify whether 36°C is correct or diagnose its provenance; it is not silently added to the quarantine registry. It illustrates that unflagged sources/output can still need review.

All nine original responses passed the previously documented common structural checks, not an engineering-correctness test. Four-pair raw outputs total old 40/new 27 rows, with 79/79 and 68/68 required citation shapes complete. Zero rows cite outside their supplied selected contexts. Some cited IDs are absent from the current audited KB but present in the saved UI context: historical snapshot differences are not fabricated-citation findings. Literal quantity mismatch counts 3/40 and 2/27 are parser diagnostics, not error rates or quality gains. Different denominators, no gold labels and a bundled treatment preclude an engineering correctness rate or causal-improvement conclusion.

## Frozen-config and accounting reconciliation

Every one of the **11 stored dispatched request bodies** matches its frozen request SHA256 and contents. Model remains `deepseek-flash`; `thinking.type=disabled`, output cap 8,192 and the common generation configuration are unchanged. No quarantine prompt was sent to the provider. Paid-run immutable artifact hashes cover **52 files** and all still match.

Separate the money categories:

| Category | CNY | Meaning |
|---|---:|---|
| Nine known usage records at peak/cache-miss rates | **0.41713** | Conservative tariff estimate, not reconciled account debit |
| Two failed-attempt uncertain reserves | **4.325376** | 2 × 2.162688 retained; no assumption of zero charge |
| Ledger reservations for all eleven dispatches | **23.789568** | Includes successful and failed reservations; do not add the failed reserve again |
| Actual account bill | **unknown** | No account-billing query or recharge performed |

The complete original twelve-slot reservation ceiling was 25.952256, but only eleven slots were dispatched. The ledger total is not actual spend and the known usage estimate does not include an invented failed-request charge. No arithmetic inconsistency was found in those earlier numerical reports. This reconciliation clarifies the different categories and supersedes any interpretation of the planning ceiling as incurred cost. The existing HTTP 402 blocker remains; no additional model call is attempted.

## Preservation and limits

- **366 historical protected hashes match** before/after: KB/results/manuscript/human files unchanged.
- **52 prior model-run artifact hashes match**, preserving raw successful responses, both failures, usage, configs and prior reports. Unrelated dirty tracked-file hashes also match.
- Registry knowledge covers exactly one flagged evidence unit. All other evidence remains **unverified**, not implicitly approved.
- Whole-evidence masking and whole-row withholding can discard correct values/requirements. Fine-grained release needs traceable parameter binding and appropriate source review; a model-declared binding alone is insufficient.
- A model could omit the risky ID or cite a healthy source incorrectly. The gate cannot infer hidden provenance or prove semantic support from numbers; it reports unknown, and existing reference/numeric checks remain limited. This is not a universal hallucination blocker.
- Review/audit JSON intentionally preserves suspect originals. Consumers must use canonical `shalls`/returned row lists or `engineering_requirements`, not export `_quarantine_delivery.withheld` as usable requirements.
- New masked-prompt generation has **not** been tested with a model. No quality or accuracy improvement is asserted.

Reproduce offline:

```powershell
$env:PYTHONPATH=''
$env:PYTHONIOENCODING='utf-8'
$env:OMP_NUM_THREADS='8'
$py='D:\Users\yando\miniconda3\envs\cooling_rag_env\python.exe'
& $py -B revision_artifacts\evidence_quarantine_20261018\run_offline_tests.py
& $py -B revision_artifacts\evidence_quarantine_20261018\replay_quarantine.py
```
