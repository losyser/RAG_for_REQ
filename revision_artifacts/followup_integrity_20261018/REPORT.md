# Offline follow-up: containment, provenance, comparison preparation and manuscript technical copy

Checkpoint: `checkpoint/followup-integrity-20261018` at `e1d94b563889f567a5511cd0787df36163b24457`. No model/API call, recharge, key/provider/security-setting change, main-experiment replacement, publication or human review occurred. Existing KB/results/manuscript/human-review inputs remain unchanged.

## Completed code repairs

The explicit opt-in delivery policy is now **evidence-quarantine-v2**. Existing v1 review registries remain loadable as input records; no registry is automatically loaded. No active flags preserves the legacy path. The policy version is present in the prompt, so v1/v2 and enabled/disabled prompts occupy different cache keys.

Two actual boundaries were strengthened:

1. UI JSON repair formerly resent untrusted raw model text, including potentially quarantined values, to a repair model. With quarantine enabled, invalid JSON now uses the conservative local fallback and stores the raw text only in `_quarantine_delivery.raw_model_text`. No repair request occurs. Legacy repair behavior remains unchanged when disabled. Normalization failures also preserve raw text with the fallback.
2. UI normalization can strip background IDs or sanitize numeric acceptance text before the final gate. A trusted local pre-normalization snapshot now lets the gate inspect original reference channels and original numeric content. Thus a numeric criterion with no usable citation cannot disappear through sanitization and leave a seemingly safe delivery row. Flagged background references remain visible to the gate even after reference filtering. Retained rows do not carry this temporary snapshot.

V4 explicitly preserves raw model text in the review destination before parsing, including malformed JSON. Source attribution is still based on explicit IDs/bindings, never numerical coincidence. Healthy-looking/unflagged rows still have unknown semantic support and applicability. The policy does not prove engineering correctness.

**257 offline tests passed**, sockets disabled. This includes six additional regression cases beyond the prior 251: pre-normalization numeric-only criteria, flagged background references, no remote JSON repair/raw preservation, malformed V4 raw preservation, real cache hit/different enabled key, and normalization-failure fallback. Actual UI/v4 entrypoints are exercised with mocks. No new model quality test is claimed.

All ten saved successful responses were replayed through current gates: **78 raw rows, 76 retained, two OR023 fourth rows withheld**. Both failed calls remain preserved elsewhere. `QUARANTINE_REPLAY_V2.json` contains every successful case/arm, retained output and withheld audit material. This demonstrates containment of the known flag, not improved generation or accuracy. Audit originals must not be exported as formal requirements.

## Local MAN source search and proposed source action

Scanned all **743 PDFs** under `D:\cooling_rag_multigranular` (**546 distinct hashes**). Inventory records exact SHA256, page count and duplicates. For each distinct PDF the first five pages were text-scanned for `49/60`; 508-page documents and the known official SHA were separately considered. Three text hits were one-page manuscript diagrams, not source guides. There was **no 508-page PDF and no match** for official SHA `29da4ba210bc2bba9b3f00d6f4f0aee15c6c7847568d5dd69355b3028692ffc1`. No candidate P134 existed to render. This scope does not exclude an unlabelled scan/image-only edition elsewhere on the machine or inside an archive.

The prior coordinator's official Revision 12.2025/3.0, 2025-12-03, P134 visual finding remains attributed to that prior verification: engine-inlet preheating min 60/max 80°C, adjacent separate dash/max 100°C row. This batch did not refetch or independently verify that official page. Local original-edition identity remains unresolved; **no KB number was replaced**.

`SOURCE_PATCH_PROPOSAL.json` provides a text-hash-preconditioned review-metadata sidecar proposal for E-HT-COMP-036. It explicitly does not substitute 60–80 for -100 in the old evidence. A future verified official edition should be a separate source/version-bound evidence unit; exact original row, conditions and applicability must be resolved first. Existing development quarantine remains the concrete containment mechanism.

## Entire-KB integrity screening

`KB_INTEGRITY.json` examines **all 1,208 active audited units**, plus duplicate/missing-ID checks independently for all four stored evidence-unit versions (1,349 / 1,307 / 1,364 / 1,208 rows). No version contains duplicate or missing IDs. No active unit lacks a source-document name.

| Finding | Units | Interpretation / priority |
|---|---:|---|
| Missing location | 4 | Prioritize source locator recovery: E-IACS-M73-001, E-IACS-M51-001, E-WAR46DF-PARAM-001, E-SOLAS-INCL-001 |
| Parent chunk absent from current source-chunk snapshot | 43 | Resolve snapshot provenance before declaring broken lineage or inventing parent links |
| Numeric-unit text without structured parameters | 386 | Prioritize explicit value/unit/operator/condition bindings; text may already contain valid facts |
| Manufacturer numeric evidence without model field | 129 | Applicability remains unknown; do not infer a model from manufacturer alone |
| Numeric text without condition field | 1 | L1-CCS2025-3.3.3.1-040, P1428; inspect source context before supplying a condition |
| No recognized page-form locator | 37 | Includes four missing locations; some may have valid clause-only locators |
| No explicit edition/revision/date field | 1,208 | Structured provenance gap; source titles can still contain edition/year information |

Rules are deterministic screening heuristics, not factual adjudication. Numeric detection looked for a digit followed by °C/℃/bar/MPa/kPa/%/mm/mg/l/mg/L/dGH/ppm; it does not exhaust all quantities. Per-parameter value/unit/condition omissions were checked where parameter dictionaries existed. Lack of a field does not establish a wrong requirement. Reference-ID traversal of the fixed V4 and saved UI retrieval snapshots found no absent-current-KB references in the scanned `evidence_ids`/`selected_ids`/`kb_id` channels; this is not an audit of every historical output or every possible reference schema.

Negative-temperature regex screening produced 67 **candidate occurrences**, including hyphenated positive ranges such as 80–82°C. They are not 67 confirmed negative limits, and no candidate was promoted to a verified healthy control. No global negative-temperature ban or automatic factual correction was applied.

## Concrete next comparison, prepared but not sent

`PENDING_COMPARISON.json` freezes all six prior sample identities with quarantine off/on, using actual entrypoint prompt builders and mocked completions. Every off request is asserted identical to that case's prior frozen new-arm request. The **proposed execution subset is only four requests**: OR023 off/on plus OR010 off/on. OR023 is the already identified flagged failure; OR010 is the previously fixed dGH/unit-boundary case and an unflagged control. Selection precedes any new model outcome. A genuinely verified negative-temperature real control is unavailable; synthetic healthy-negative cases remain offline tests only.

Recipient: DeepSeek official `https://api.deepseek.com/chat/completions`; model `deepseek-flash`, thinking disabled; temperature and other settings unchanged. Outgoing content is exactly the saved original requirement text and selected evidence bodies/parameters/source metadata in those frozen requests; on arms mask flagged records and add the explicit policy rule. No manuscript, human-review files or secret is part of the prompts. Exact hashes and full bodies are included for review.

- Maximum **4 additional dispatches**, no retry or JSON repair calls; 8,192 output tokens each, total output cap 32,768.
- Planning input allowance **116,331 tokens** (UTF-8 bytes + 4,096 framing per request; not tokenizer measurement).
- At the prior frozen peak tariff, byte-planning estimate is **CNY 0.494806**; full-provider-context conservative reservation is **CNY 8.650752**.
- Previous 12-dispatch reservation CNY25.952256 plus proposed reservation gives **CNY34.603008**, below CNY50. This is reservation accounting, not actual spending; prior known-usage estimate and failed uncertainty remain separately documented.
- The other eight prepared candidates are **not proposed for execution**. No executor was created. The prior authorization is exhausted; this exact four-request scope requires the parent's forwarded new authorization before any call.

## Manuscript technical work completed independently

`paper_technical_delivery/` is an independent review copy. Original current manuscript, tables, figures, desktop and adopted version were not overwritten. Research text/results/conclusions are byte-preserved copies.

- Reconstructed a **cumulative textual diff** from saved original-submission TeX plus its four `_orig.tex` tables to the current expanded source. This avoids using a recent per-round baseline as if it were the original submission. Baseline and all expanded input hashes are in `PAPER_TECHNICAL_CHECK.json`.
- Created a separate original-input flattened review snapshot and set its local filesystem read-only flag. It is not an original-figure restoration or an adopted manuscript replacement. Git does not preserve the Windows read-only attribute.
- Added `build_review.ps1` with manuscript/response/mapping-supplement targets, dependency checks, checked exit codes, and outputs confined to this copy. `-CheckOnly` passed. Existing vector figures are reused; no SVG conversion or shell escape is introduced.
- Verified local STIX2 package resolution. `USG.cls` requires `stix2`; bundled TTF/OTF files alone do not provide the pdfLaTeX package. No font substitution was made.
- Flattened-current-source check found **zero duplicate labels and zero unresolved ref/eqref/pageref targets**. Existing current log has no undefined-reference/missing-character matches in the inspected patterns. No numbering was guessed or changed.

No new PDF was compiled or visually accepted; this delivery is a technical source/review package, not a publication-ready marked PDF. Historical marked TeX is stale relative to current text and clearly labelled in the delivery README. The exact earlier **P1–P6 list was not located** in local handoff/revision reports; a clarification request remains pending, so no invented identifier mapping is asserted. A full P1–P6 closeout needs that list. Adoption of a baseline/version, scientific content changes, unverified original figures and publication remain author decisions; they do not block the completed technical checks and copy.

## Preservation and remaining limits

After checks: **366 historical protected hashes unchanged**, plus **256 additional hashes unchanged**, covering both existing model runs, prior quarantine artifacts, current manuscript and editable package. Pre-existing unrelated dirty tracked files also match. No history file was repaired in place.

Remaining substantive gaps are exact MAN original-edition provenance, parameter-level semantic/applicability verification, an independently verified healthy-negative real control, and the missing exact P1–P6 list. The containment mechanism cannot detect a model that hides a risky source or incorrectly cites a healthy one. Those are explicit limitations, not claims that unknown means correct.
