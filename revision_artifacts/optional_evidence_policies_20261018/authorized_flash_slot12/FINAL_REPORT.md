# Frozen comparison: final authorized slot

Slot 12 (R003 new) succeeded with HTTP 200, `deepseek-flash`, thinking disabled, finish reason `stop`. No failed request was repeated. The full plan is now exhausted: **12 dispatches, 10 successful responses, 2 retained failures, 4 complete pairs**. OR001 and R003 each have a new-only response. R003 old remains the original HTTP 402 failure; therefore this continuation does **not** produce a fifth pair.

Checkpoint: `checkpoint/flash-slot12-20261018` at `4086e04e81bb627336ed365f5b18f95e75cf282c`. Authorization was the parent's forwarded original explicit six-case/12-request/CNY50 approval plus the user's recharge confirmation. Only the previously unattempted final slot was authorized and executed. No recharge, key change, provider change, model substitution or system setting change was performed here.

## Request and preserved records

- Endpoint: `https://api.deepseek.com/chat/completions`.
- Exact slot-12 request SHA256: `484aa2ddffb52a9f6d07b6a32f65f227a8e5c6facbf4768a9da324dc1a13c483`.
- Original frozen messages/configuration were used, including 8,192 output-token cap; SDK retries zero, redirects disabled. The transport checks the exact wire body, reserves before dispatch, consumes its one-use permission and enforces the cumulative 12-request/budget limits.
- Latest code's quarantine prompt was **not** sent. This is completion of the original comparison, not generation under the quarantine strategy.
- `12_R003_new_request.json`, `12_R003_new_response.json`, `slot12_ledger.json` and execution log preserve prompt, raw response, returned model, usage, status and timings. The ledger includes all previous attempts without changing their original files.
- All **12 request bodies and hashes** match the frozen plan. All **366 historical protected files**, **52 prior model-run files**, and previously recorded unrelated dirty files remain unchanged. `FINAL_VERIFICATION.json` records checks; `prior_artifact_hashes.json` is the pre-run snapshot.

## All results, without selecting favorable outputs

| Case | Old | New | Interpretation |
|---|---|---|---|
| OR001 | Connection failure | 10 rows | New-only; no causal comparison |
| OR010 | 18 rows | 9 rows | Repeated hardness/chloride statements consolidated; some storage/freezing/service values deferred to TBD; new rows 6–8 explicitly retain applicability unknowns. Fewer rows can also lose useful content; recall not measured. Both already generated dGH. |
| OR023 | 9 rows | 8 rows | **Both fourth rows propagate -100°C** into measurable criteria. The new verification note does not cure this defect. Selection/prompt changes are bundled; no single-change attribution. |
| R001 | 8 rows | 5 rows | Reorganized overlapping pump/protection/tropical/control statements with restored real body text. Completeness remains unverified and context can remain partial. |
| R002 | 5 rows | 5 rows | Old first row asserts a 36°C difference; new first row defers limits to manufacturer documents. This task does not adjudicate the 36°C value or silently flag it. Other requirements are reorganized, not independently validated. |
| R003 | HTTP 402 failure | 1 row | New-only evidence-gap draft; no comparative improvement claim |

R003 new explicitly reports no effective supporting evidence, leaves `evidence_ids` empty and uses `support_status=evidence_gap`. It restates the required HT/LT/seawater boundary and schematic responsibilities, while its acceptance criterion requires supplementary evidence before acceptance can be determined. This avoids inventing numerical limits or claiming direct support in this sample, but **does not deliver an executable, evidence-supported acceptance criterion**. Its risk rationale is also unverified. No old response exists for comparison.

All 10 successful responses passed the same common structural checks. This is not engineering accuracy. The four complete pairs remain old 40/new 27 rows, citation-field completeness 79/79 and 68/68, and zero citations outside supplied selected contexts. Literal quantity mismatch diagnostics remain 3/40 versus 2/27: these are not correctness/error rates. Some references exist in the saved UI context but not the current KB; that alone does not establish fabricated citations. There are no gold labels, significance estimates, new human reviews or correctness rates.

`CONTINUATION_EVALUATION.json` aggregates every planned slot, including both failures and both unpaired successful arms. `POSTPROCESS_DIAGNOSTICS.json` separately preserves the offline risk-normalized new outputs; it is not raw model performance. Historical reports are retained as earlier snapshots rather than overwritten.

## Costs and limits

Slot 12 usage: **3,839 input / 646 output tokens**; peak all-input-cache-miss tariff estimate **CNY 0.012846**. It returned 2,944 cache-hit input tokens, so this estimate deliberately does not treat cache savings as verified billing.

All ten known usage records total **103,296 input / 27,923 output tokens**, conservative peak/cache-miss estimate **CNY 0.429976**. This is not an account debit confirmation. The two failed-attempt uncertain reserves remain **CNY 4.325376**. They are already included in the cumulative twelve-attempt reservation **CNY 25.952256**, not an additional charge. Even adding the known usage estimate to that full reservation conservatively stays below CNY50 (CNY26.382232); doing so is not an actual-spend calculation. Actual account billing is **unknown**; no billing query was made.

The approved 12-dispatch plan is exhausted. There is no automatic retry or thirteenth request. Additional generation would require a new explicitly scoped authorization, irrespective of account balance.

## Offline quarantine replay and validation

The previously completed quarantine replay remains immutable (nine responses, 77 rows, two OR023 rows withheld). The new offline verifier applies the actual normalizer and quarantine gate to saved R003 new; its one nonnumeric evidence-gap row is retained without a verified-direct claim. Combined saved-response replay totals are **10 responses / 78 raw rows / 76 retained / 2 withheld**. Prior replay and delivery hashes link those nine records; the new R003 output is recorded in `FINAL_VERIFICATION.json`.

These counts demonstrate containment of the known flagged source, **not** engineering correctness or generation improvement. Unflagged sources may still be wrong; missing or model-declared bindings do not prove semantic support/applicability. Review-channel originals must not be exported as formal delivery requirements.

Validation performed: frozen-plan preflight; all-12 exact request/config/hash assertions; cumulative attempts/status/budget assertions; 366+52 preservation checks and unrelated-dirty preservation; network-disabled aggregate evaluation and final offline replay. The preceding code commit's **251 passing offline tests** remain applicable; no production code was changed in this continuation. Scripts and diagnostics are additive in this directory only. No KB/results/manuscript/human-review edits or main-experiment replacement occurred.

Reproduce only the offline checks (do not rerun the exhausted request plan):

```powershell
$env:PYTHONIOENCODING='utf-8'
$py='D:\Users\yando\miniconda3\envs\cooling_rag_env\python.exe'
& $py -B revision_artifacts/optional_evidence_policies_20261018/authorized_flash_slot12/evaluate_all12.py
& $py -B revision_artifacts/optional_evidence_policies_20261018/authorized_flash_slot12/verify_final.py
```
