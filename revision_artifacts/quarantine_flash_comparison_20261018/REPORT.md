# Authorized four-request quarantine comparison and separate offline repair

The parent forwarded explicit user approval for exactly four additional OR010/OR023 quarantine-off/on requests, cumulative CNY50 cap. **All four completed**, HTTP 200, returned `deepseek-flash`, thinking disabled, finish reason `stop`. SDK retries, repair calls and replacement attempts were zero. These are cumulative slots 13–16; the previous two failures remain retained. This authorization is exhausted.

Frozen policy/code at dispatch was the quarantine-v2 implementation from `38baa8aa3a9abf64032dd21b677650b345614602` (paper-only commit `005e8c29f0d77544682c3e7bcb57bd6c86711e24` preceded dispatch). Prompts come from the committed pending plan. Both arms use identical selection, model, temperature, output limit and risk policy; only the quarantine prompt treatment changes. No KB facts, old results or scientific manuscript content were changed.

## Results under the frozen policy

| Slot | Case/arm | Input/output tokens | Raw rows | Actual frozen-policy delivery | Result |
|---|---|---:|---:|---:|---|
| 13 | OR010 off | 7,177 / 2,183 | 5 | 5 | No out-of-scope citation IDs or structural errors |
| 14 | OR010 on | 7,247 / 3,372 | 10 | 10 | No rows blocked; applicability/semantic support still unknown |
| 15 | OR023 off | 6,525 / 2,302 | 8 | 8 | Row 4 still uses flagged E-HT-COMP-036 for other temperature ranges, but does not emit -100°C this time |
| 16 | OR023 on | 6,052 / 2,041 | 9 | **0** | Row 9 cites the quarantined source with tier `?`; strict whole-list schema parsing rejects the entire response |

Both OR023 raw outputs contain **zero -100°C occurrences** in shall/measurable/acceptance fields. Therefore this run cannot establish a reduction in -100°C propagation, even though the enabled prompt contains no quarantined numeric body. Earlier occurrences remain preserved in earlier runs. A single repeat may differ even at temperature zero; no failed or unfavorable response was replaced.

OR023-on row 9 is a nonnumeric TBD/background statement that explicitly says the evidence is quarantined. It is not a directly supported numeric requirement, but its invented `?` tier breaks the schema. The requested end-to-end usable-delivery acceptance **did not fully pass** under the frozen code: zero output is safe from numeric leakage but is not a successful usable requirement set. `EVALUATION.json` preserves this original result and is not rewritten after the repair below.

OR010-on has no accidental gate removal, and both arms retain -37°C/-52°C only in TBD explanatory hints. These are unverified source-attributed examples, not verified healthy controls. The on arm also changes from consolidated TBD-oriented rows to separate concrete hardness/pH/chloride criteria (including 10 dGH, pH 6.5–8/7.5, and 50/25 mg/l). That can increase specificity but does **not** establish applicability or correctness; it may create a greater need for review. Hence “no false blocking in this sample” is not “no quality regression.”

The enabled OR023 output separates interface TBDs, flow limits, alarm thresholds and preheat ranges; two flow requirements overlap. This is not evidence of improved completeness or engineering accuracy. All field checks and quantities are diagnostics, not gold-label adjudication. There are only two samples and one output per arm; no correctness rate, statistical significance or generalization claim is made.

## New gap fixed offline, with explicit separate policy

Added **`schema_policy="isolate-invalid-rows-v1"`** to the V4 generator. It requires explicit active quarantine flags plus a review destination. It keeps valid rows, moves invalid rows unchanged into `delivery_report.schema_withheld` with schema errors/position and `needs_review`, then applies the existing evidence gate to the valid remainder. It never guesses or repairs `tier='?'`. Raw response text remains preserved.

Default `schema_policy="legacy"` retains strict whole-response rejection, including with quarantine enabled, so the frozen experiment is reproducible and this new strategy is not silently adopted. No prompt change or additional model call was needed for the offline repair.

Separate `EVALUATION_ROW_ISOLATION.json` and `replay_row_isolation.py` replay the **same four raw responses** through the opt-in postprocessor. OR010 off/on remain 5/10; OR023 off remains 8; OR023 on now yields **8 valid rows plus 1 unchanged invalid row for review**. This is a counterfactual offline processing result, not another successful generation or a replacement for the frozen-policy failure. Flagged citations cannot escape via the invalid row because that entire row is excluded from formal delivery.

**259 offline tests pass**, including strict-default whole-list rejection, opt-in retention of valid healthy negative-temperature rows, unchanged invalid tier/original-text preservation, and rejection of unsupported policy or missing quarantine setup before any client call. The prior quarantine/UI tests remain included. No cache or historical output is rewritten by these tests.

## Accounting, identity and evidence

Before execution, official Chinese [DeepSeek pricing](https://api-docs.deepseek.com/zh-cn/quick_start/pricing/) was rechecked: Flash peak cache-miss input CNY2/M and output CNY8/M, consistent with the previous conservative reservation. `PRICING_VERIFICATION.json` records the source/rates. Returned usage totals for this batch: **27,001 input / 9,898 output tokens**.

- New known-usage peak/cache-miss estimate: **CNY0.133186**.
- Combined known-usage estimate for all 14 successful responses: **CNY0.563162**.
- Total conservative reservation across all 16 attempts: **CNY34.603008**.
- Earlier two failed-attempt uncertain reserves: **CNY4.325376**, already included in that reservation; not an extra charge.
- Actual account debit remains **unknown**. Cache hits/off-peak billing may lower charges; reservations and tariff estimates are not a billing reconciliation.

Every request body, full SHA256, model response ID, raw body, usage, elapsed time and terminal state is preserved in numbered request/response JSON and `ledger.json`. Actual generator entrypoints were replayed with mocks and asserted to reproduce all four frozen messages exactly. `EVALUATION.json` contains original-policy outputs; the separate row-isolation evaluation contains the post-fix counterfactual.

Response IDs: OR010-off `344cf248-a11f-45e0-8a22-2e34b134db36`; OR010-on `1233e1bb-cb72-42ff-a8f9-522e55910dd5`; OR023-off `7efcc6fa-2467-4d30-a8a1-d3f9fee4791d`; OR023-on `2da09a8c-02be-497d-89ca-9bca56962934`.

Post-run checks confirm **366 historical + 256 additional protected hashes unchanged**. Prior failures/outputs, KB/results/human-review files and current scientific manuscript are preserved. The separately completed paper technical validation is in `revision_artifacts/paper_build_validation_20261018/REPORT.md`; its successful 24-page clean/28-page cumulative builds remain a technical review package, not an adopted submission version.
