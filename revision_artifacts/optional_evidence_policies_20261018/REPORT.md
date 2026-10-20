# Optional evidence policies — offline delivery, 2026-10-18

This is a local code repair, not a paper experiment. No model/API calls, external requests, paid inference, new human review, KB corrections, historical result writes, manuscript edits or publication occurred. Network connections are blocked in both delivered launchers. No secrets are included.

## Configuration and external-send gate

Read-only configuration resolution followed the actual main-chain precedence: process environment over `.env`, `base_url` over `DEEPSEEK_BASE_URL`. Configured recipient: **DeepSeek**, baseURL **https://api.deepseek.com**, model alias **deepseek-chat**. This establishes local configuration, not a remotely verified model revision, account owner, tariff or price guarantee. No client was instantiated for this check. URL credentials/query components were excluded from the displayed endpoint.

Proposed later diagnostic inputs: v4 OR001/OR010/OR023 and saved UI R001/R002/R003 from `batch_20260730_164747`. Each request would contain one requirement, selected evidence text, source/location identifiers, existing extracted values/operators/units, recorded model/conditions/applicability metadata and generation instructions. It would not upload whole KBs, manuscripts, human workbooks or secrets. Two variants per case means **12 completions**, no fresh extraction, no automatic retry/JSON-repair request. Proposed output cap: 8,192 per call, **98,304 output tokens** total. Preliminary input planning allowance: roughly 100,000 tokens per request / 1.2 million total, based on the existing large UI prompt envelope; this is deliberately loose, **not a tokenizer measurement or enforced limit**. Final serialized prompts, model tokenizer count and applicable price must be frozen before execution. No cost claim is made from the RMB 50 budget.

**BLOCKED pending parent-thread forwarding of explicit recipient/data-egress confirmation.** The RMB 50 authorization does not approve external transmission. No confirmation has been received in this execution. An eventual runner must enforce the approved request count, no retries and the monetary budget; this repair does not implement or execute that runner.

## Checkpoint and preservation

- Work began on existing branch `fix/optional-evidence-policies-20261018`, HEAD `07a316ab8fd6e2aff4d78282f556f5fe2c308ae2`.
- Existing checkpoint tag `checkpoint/optional-evidence-policies-20261018` was verified to reference that exact HEAD; it was not overwritten. No applicable AGENTS.md was found in checked project ancestors or source/test/script directories.
- Pre-existing user changes were not staged. `dirty_before.json` records their tracked-file hashes. All still match.
- `protected_before.json` and `protected_after.json` contain the same **366 matching hashes** from the earlier protection manifest: KB/processed inputs, results/archives, manuscripts and human workbooks. No historical value was changed.
- Whole-repository `git diff --check` reports pre-existing XML trailing whitespace. Scoped checks for this repair pass; the XML was preserved.

## Implemented, explicitly optional behavior

1. `aligned_retrieve(..., policy="zero-hit-unfiltered-rescue-v1")`: only a **nonempty mapping with zero aggregate filtered candidates** triggers one unfiltered vector plus one BM25 search, fused and bounded by existing limits. Results carry `_retrieval_origin=unfiltered_zero_hit_rescue` and `_mapping_applicability=unknown`. Original mapping pairs are retained, not rewritten to suggest that rescue was mapped. Diagnostics preserve zero-filter-hit and rescue-attempt flags, including an empty rescue result. Nonempty filtered results, partial missing pairs, exceptions and wrong-but-nonempty results are not rescued. Default `existing_hard_pair_filter` is unchanged.

2. `select_evidence(..., policy="numeric-first-reserve-one-nonnumeric-v1")`: reserve the final slot for the first nonnumeric evidence only when the legacy bounded selection would otherwise contain exclusively numeric evidence and capacity is at least two. Remaining order is stable. Limit one retains legacy numeric priority. This is a coverage hypothesis, not authority/relevance scoring. `generate_structured_shalls(..., selection_policy=...)` uses the same policy for its prompt and risk scope and records the optional selection version on returned rows. Default remains `numeric-first-stable-first-reference-v1`.

3. `risk_policy="independent-reference-quantity-applicability-v1"`: independent, versioned per-row `_independent_risks` for structured generation and UI normalization/generation. It reports citation absence/ambiguity, finite-vocabulary numeric/value-unit-operator tuple mismatches, and missing model/condition fields. Exact numeric tuples only produce `lexical_tuple_match_only`; semantic support and applicability **always remain unknown**. UI direct-status claims become `need_confirmation` while retaining `_reported_support_status`. The UI graph carries the option through normal parse, repaired JSON and conservative fallback paths. Original reported IDs remain available to detect citations removed by UI normalization. No grade changes are introduced. Default `legacy` adds no new policy fields or downgrades.

Explicit Python API options are deliberate; historical experiment scripts and default UI settings were not silently switched. Invalid policy names fail rather than falling back silently. Future experiments must record these policy strings and use new isolated output paths.

## Evidence and verification

- **237 tests passed**, no skips: the previous selected 216-case regression plus 21 new cases, including parameterized boundaries. See `tests_final.txt`. This is the selected suite, not the entire repository.
- Tests cover legacy no-rescue, zero-result rescue, nonempty-result no-rescue, cap/deduplication, stable selection at limits 1/2/12/20, invalid policies/duplicate evidence, missing/ambiguous citations, sign/unit/operator mismatches, same-number-but-unknown-support, real structured generation with mocked completion, and UI graph normal/repaired/failure/budget paths with mocked completions.
- Fixed replay: **six saved source records, 56 output rows**, unchanged acceptance criteria. The three v4 and three UI cases were selected before new measurements. No regeneration or new labels.
- Selection comparison: **60 saved v4 candidate sets**, **4 changed selections** with the opt-in nonnumeric reservation. This does not contradict the prior 25 sets with at least one omitted nonnumeric item: most already included some nonnumeric evidence and are not changed by this narrow policy. Replay order comes from saved `_evidence_values` insertion order, not recovered retrieval rank.
- Full diagnostics: `SAVED_REPLAY.json`; input files identified with SHA256. Hash assertions are part of replay. Both historical and pre-existing dirty tracked files match their initial snapshots.

Reproduce using the existing project environment (no installation required):

```powershell
$env:PYTHONPATH=''
$env:PYTHONIOENCODING='utf-8'
$env:OMP_NUM_THREADS='8'
$py='D:\Users\yando\miniconda3\envs\cooling_rag_env\python.exe'
& $py -B revision_artifacts\optional_evidence_policies_20261018\run_offline_tests.py
& $py -B revision_artifacts\optional_evidence_policies_20261018\replay_saved.py
```

## Limits and remaining risks

Numeric checking has finite units and literal tuples; no unit conversion, general inequality/range reasoning, parameter-role alignment, manufacturer conflict resolution or semantic entailment. It may miss unsupported units and can flag harmless formatting differences. Presence is checked in supplied selected evidence, not an authoritative-source verification; v4 uses selected candidate bodies/records rather than reconstructing every final budget omission. Metadata presence is never sufficient to infer project applicability. Missing-field diagnostics do not declare the source erroneous.

Mapping rescue is only mock-validated at the code boundary; no index/model recall study was performed. Nonnumeric reservation can displace a relevant numeric item. Neither option is claimed to improve output quality. The paired model comparison remains blocked by the external-send gate.

`E-HT-COMP-036` / OR023 `-100°C` remains a separately known source risk: the earlier official MAN 49/60 P134 check did not support it, but the local original edition is still unmatched. A local tuple match can repeat the same KB error. No factual KB correction was guessed, and no new official-source verification was performed in this batch.

Rollback should revert this batch's scoped code commit, not reset the dirty working tree or restore historical data from Git.
