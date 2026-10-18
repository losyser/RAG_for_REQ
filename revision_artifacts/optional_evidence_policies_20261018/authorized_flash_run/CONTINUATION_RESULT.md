# Authorized remaining-call run — stopped at insufficient balance

**Terminal outcome:** the corrected transport received nine model responses, then request slot 11 (R003-old) returned **HTTP 402, Insufficient Balance**. Slot 12 was not sent. Cumulative accounting includes the original failed OR001-old connection attempt: **11 attempts, 9 model responses, 2 failures, 1 unattempted slot, zero retries**. No recharge, new credential, provider/model change or extra sample was attempted.

The parent explicitly coordinated continuation of original frozen slots 2–12. This did not authorize replacing the failed first slot. A separate `continuation_ledger.json` starts with the original failure/reservation and appends new attempts; `ledger.json`, original failure records and the first failure evaluation remain unchanged. The original exclusive-create stop still prevents accidental rerunning, and the continuation ledger also uses exclusive creation.

## Fixed inputs, actual execution and money

All request bodies match `../full_repair_comparison/FROZEN_PLAN.json`: old checkpoint **3659d37**, new code **6de9afc** (the 7e4a5ae documentation head has the same relevant code). Same `deepseek-flash`, thinking explicitly disabled (non-thinking mode), temperature 0, max output 8,192, JSON output. The official alias route was documented as V4.1-Flash-1017; returned model fields are `deepseek-flash`, which confirms the alias but does not independently attest a pinned internal model revision.

The repaired transport honors the existing environment proxy without changing system settings; it retains exact endpoint/body validation, zero SDK/HTTP retries, no redirects and connect/read/write/pool timeouts of 10/120/30/10 seconds. No project text was sent anywhere except the approved official completion endpoint through that existing HTTPS proxy route. No model output instruction was executed.

The frozen CNY tariff snapshot lists peak cache-miss input RMB 2/M and output RMB 8/M. Cumulative conservative reservation is **RMB 23.789568**, below the RMB 40 initial and RMB 50 total guard. Each failed/unknown attempt retains RMB 2.162688; no failure is treated as free.

Nine returned usage records total **99,457 prompt tokens and 27,277 completion tokens**. Charging those known tokens at peak/cache-miss rates gives **RMB 0.41713**, a conservative usage-based estimate before any cache/off-peak discount. This is **not** account billing reconciliation. The actual account debit and fee treatment of failures are unknown. A user-approved budget does not imply that the configured account has that balance: the provider explicitly refused R003-old for insufficient balance. No balance/top-up endpoint was called after the 402.

## Every planned slot retained

| Slot | Case / arm | Outcome | Seconds | Generated rows |
|---|---|---|---:|---:|
| 1 | OR001 old | Prior connection failure; retained | 0.328 | — |
| 2 | OR001 new | Response, unpaired | 14.234 | 10 |
| 3 | OR010 old | Response | 15.235 | 18 |
| 4 | OR010 new | Response | 11.171 | 9 |
| 5 | OR023 old | Response | 8.641 | 9 |
| 6 | OR023 new | Response | 9.422 | 8 |
| 7 | R001 old | Response | 15.188 | 8 |
| 8 | R001 new | Response | 13.609 | 5 |
| 9 | R002 old | Response | 8.328 | 5 |
| 10 | R002 new | Response | 11.516 | 5 |
| 11 | R003 old | HTTP 402 Insufficient Balance; retained | 0.469 | — |
| 12 | R003 new | Not attempted after stop | — | — |

All nine model responses have `finish_reason=stop`; no length truncation was reported. Complete request bodies, raw response bodies, parsed response objects, response headers limited to non-secret diagnostic fields, usage, returned model, request hashes and elapsed/UTC times are stored in the numbered files. The slot-11 error body and SDK/cause types are saved. No unsuccessful response was replaced by a successful rerun.

## Structural checks: four complete pairs only

Paired summaries include **OR010, OR023, R001 and R002**. OR001-new is retained and evaluated separately but excluded from paired summaries. R003 has no generated output and is not silently treated as a valid/invalid generated requirement. The intended no-evidence negative case therefore remains untested.

| Observable check | Old, four paired cases | New, four paired cases |
|---|---:|---:|
| Strict JSON parse / common structure valid | 4/4 | 4/4 |
| Generated rows | 40 | 27 |
| Required citation field shapes complete | 79/79 citations | 68/68 citations |
| Rows citing outside their supplied selected scope | 0/40 | 0/27 |
| Rows with a recognized quantity tuple absent from cited material | 3/40 | 2/27 |
| Rows with lexical tuple matches only | 12/40 | 10/27 |
| Rows with no recognized quantity | 25/40 | 15/27 |
| Explicit unknown wording in condition fields | 0/40 | 3/27 |
| Any explicit uncertainty wording anywhere in row | 10/40 | 8/27 |

The common v4 structural check is the current `validate_shall` required-field/type contract, applied equally to raw old/new outputs. The UI check requires object/list structure, unique nonempty row IDs, nonempty shall statements, and string-list criteria/references; it is not a complete engineering/schema ontology validator. Citation shape means kb_id/source/tier/has_clause for v4 and nonempty reference IDs for UI. Nine responses including the unpaired OR001-new passed these structural checks, producing 77 raw rows total. These checks do not establish traceability correctness, source authority, applicability or engineering correctness.

Raw citation references absent from the current audited KB occur in 10 old and 9 new paired rows, but **all are present in their saved supplied context**. Examples are E-CCS-COOL-001, E-CTRL-COOL-001, E-DNV-COOL-001 and E-IACS-M3-002. This is a historical-snapshot mismatch, not evidence of fabricated IDs. The report deliberately separates current-KB lookup from in-prompt existence.

Numeric checking uses a finite unit vocabulary and literal value/unit/operator tuples. It does not solve ranges, recognize all prose operators, convert units, align parameter roles or prove entailment. Some mismatch flags may be formatting/parser artifacts. For v4, the comparison scope uses selected full saved candidate bodies/value records, not an exact reconstruction of every prompt omission; UI uses the exact compacted support records serialized in each prompt. Neither the 3-to-2 count nor the reduction in row count establishes improvement: denominators differ, recall was not assessed and no gold labels/human adjudication exist.

## OR023: the known source-value risk remains

Both versions' **fourth row** include `发动机进口启动前预热-100°C` in `measurable_criterion`, associated with the selected E-HT-COMP-036 source. The old output presents it as a temperature range requirement. The new output **still retains the same value in the quantitative criterion**, while adding this acceptance-criterion qualification:

> 启动前预热工况（-100°C记录值）需核实其量纲与含义后方可作为量程依据

That qualification is observable additional uncertainty, but it does **not** remove the suspect value from the engineering criterion or prove that a downstream consumer will respect it. The new output cannot be counted as having prevented propagation. Both rows receive `lexical_tuple_match_only` from the independent diagnostic because the same suspect value exists in the KB. This is the concrete boundary that **same number is not semantic support**. Semantic support/applicability remain unknown. No KB value, source provenance or historical output was corrected by guessing; the original-edition match remains unresolved.

## Unknown conditions and post-generation guard

OR010-new rows 6–8 explicitly retain pending manufacturer/model/concentration or coolant-type conditions. One example is `具体厂家、机型与乙二醇比例条件待确认`. The other paired rows' condition text is recorded but unverified; counts do not imply that those conditions were established for the project. There is no defensible denominator for “all unknown conditions correctly preserved” without source adjudication.

Raw new UI model outputs for R001/R002 report **nine** `verified_by_direct_evidence` rows (4 + 5), versus six raw old rows. These self-reported statuses are **not** independent verification. Applying the new optional normalizer/risk policy offline reduces all nine new direct-status claims to non-direct/confirmation states, while keeping all ten new UI rows. This is a deterministic guard effect, not model correctness.

`POSTPROCESS_DIAGNOSTICS.json` stores the offline application of the new policy separately, with hashes linking to untouched raw responses. New v4 rows are retained (OR001 10, OR010 9, OR023 8), and new UI rows are retained (5 + 5). No repair API was called; postprocessed artifacts do not replace raw outputs. The source-backed -100°C lexical match remains a limitation even after these annotations.

## Validation, protection and blocker

- Existing production-code regression evidence remains 237 passing offline tests. Sender verification comprises the prior five budget tests, four proxy/route tests and a new mocked continuation integration test: original one failure + eleven mock replies gives twelve cumulative attempts, preserves the original ledger and rejects another execution. The five guard tests were rerun for this continuation change.
- All **366 protected historical hashes** match after continuation; all pre-existing dirty tracked-file hashes match. `protected_after_continuation.json` records the historical hashes. Original failure records compare unchanged to their commit after Git line-ending normalization.
- `CONTINUATION_EVALUATION.json` and `evaluation_log.txt` contain the full structural diagnostics; `evaluate_continuation.py` blocks networking and only reads model text as data.
- No full experiment, paper change, human-review task, API repair, provider upgrade, recharge, new key or system network/security change occurred.

**Remaining blocker is provider-reported insufficient balance (HTTP 402).** One attempt remains in the original numerical cap, but the batch is stopped and no additional request is authorized by the stop policy alone. Continuing after funding/account resolution would require explicit parent coordination of the remaining single slot; it cannot restore the missing R003 pair under this cap. The result supports specific diagnostic observations only, not a small-sample engineering correctness rate or causal quality-improvement claim.
