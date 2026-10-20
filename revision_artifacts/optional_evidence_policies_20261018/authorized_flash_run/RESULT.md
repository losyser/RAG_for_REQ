# Authorized Flash comparison — terminal connection failure

**Outcome: stopped after the first dispatch attempt. No model output was received.** This is a complete failure record, not a successful model evaluation and not a basis for claiming improvement.

The parent forwarded the user's explicit permission to send the fixed six project requirement/evidence cases to official `https://api.deepseek.com` using `deepseek-flash`, at most 12 requests and RMB 50, for development validation only. Although the user mentioned a better model could be considered, this run deliberately retained the specifically planned Flash model and did not add Pro or another provider.

## Billing gate verified before dispatch

The official [Chinese model/pricing page](https://api-docs.deepseek.com/zh-cn/quick_start/pricing/) was successfully fetched directly as a public documentation page. The web browsing renderer had failed on this URL previously; a normal public-document HTTPS fetch succeeded. No authentication or project data was sent for that read.

Saved snapshot: `pricing_cny.html`, SHA256 **7428747bd2fe3a0b1935a3454d1f29640c1d863a5a14be0a5f8bcb873f407b49**, with extracted text in `pricing_cny_text.txt`. It lists Flash peak prices per million tokens as **RMB 2 input cache miss, RMB 0.04 input cache hit, RMB 8 output**, with off-peak half those prices. It identifies Flash as DeepSeek-V4.1-Flash-1017, 1M context. No guessed FX conversion was used.

Conservative reservation uses the full context ceiling rather than the unverified tokenizer estimate:

`(1,048,576 input * RMB 2 + 8,192 output * RMB 8) / 1,000,000 = RMB 2.162688 per attempt`.

Twelve attempts reserve **RMB 25.952256**, within the RMB 40 initial-reservation threshold and RMB 50 total cap. The smaller frozen-text planning estimate is RMB 1.739528 for twelve calls, but it is not used to establish the hard financial reservation. No cache or off-peak discount is assumed. These are tariff-based bounds for this run under the documented limits, not account billing reconciliation.

## Executed controls

- Exact approved comparison: checkpoint `3659d37` versus new code `6de9afc`, six fixed IDs OR001/OR010/OR023/R001/R002/R003, using `../full_repair_comparison/FROZEN_PLAN.json`.
- Both arms use the same model and explicit `thinking.type=disabled`; `max_tokens=8192`; JSON output; no tools, extraction, analyzer, judge, repair or continuation requests.
- Installed SDK OpenAI 2.37.0; `max_retries=0`. Underlying HTTP transport also has `retries=0`; redirects disabled.
- Explicit HTTP timeouts: connect 10s, read 120s, write 30s, pool 10s.
- `GuardedTransport` verifies the exact endpoint and serialized frozen request, counts dispatch attempts, reserves before dispatch and rejects unexpected extra attempts. Its per-attempt allowance is cleared before delegation, so an implicit retry cannot reuse it.
- A persistent ledger is created exclusively. Re-executing the sender against this run directory is rejected; no resume/automatic retry is implemented. Prior uncertain reservations are never silently refunded.
- Five offline tests passed, including real SDK serialization through a mock transport, thirteenth-attempt rejection, request mutation rejection, timeout reservation/no retry and budget rejection. The `dispatch` lines in `guard_tests.txt` are mock-only; the real run is recorded separately in `ledger.json` and `execution_log.txt`.

## Terminal record

| Item | Result |
|---|---|
| First planned request | OR001, old builder prompt |
| Dispatch attempts counted | **1 of maximum 12** |
| SDK result | **APIConnectionError: Connection error.** |
| Elapsed | **0.328 seconds** |
| HTTP status / provider response | None received |
| Returned model / usage | None received |
| Automatic or manual retries | **0** |
| Later requests | **11 not attempted after stop** |
| Retained uncertain reservation | **RMB 2.162688** |
| Actual billed amount | **Unknown**, not assumed zero |

The endpoint/body/budget guard had passed and reserved the attempt before the delegated transport failed. A dispatch attempt does not prove that the remote server received or processed the request. The SDK-level exception was recorded; its chained lower-level connection cause was not captured, so no specific DNS/TLS/proxy/firewall diagnosis is asserted. No authenticated diagnostic request, transport substitution or retry was performed after the failure. This was a runtime connection failure, not a reported automatic-approval rejection.

All eleven remaining planned bodies are retained in the frozen manifest. The first request's individual request/response files are `01_OR001_old_request.json` and `01_OR001_old_response.json`. The latter preserves the failure type/message and timing with null HTTP/usage/model fields. `RUN_METADATA.json` records source hashes, pricing, SDK versions, effective transport settings and authorization scope. Credentials, authorization headers and environment values were not logged.

## Requested quality diagnostics

**There are zero generated outputs.** `EVALUATION.json` enumerates all twelve planned slots and marks the first failure and eleven unattempted slots. Schema-validity and evidence-field-completeness rates are null with generated-output denominator zero; citation/numeric-unit/operator risk and condition-retention measures are unmeasurable. Missing outputs are not counted as schema-invalid generated requirements or silently excluded to improve a score.

OR023 was **not sent**, so this run cannot establish whether either prompt propagates the known suspicious `E-HT-COMP-036` -100°C value or preserves uncertainty. The earlier KB provenance concern remains unchanged. No model-quality improvement, human correctness rate, grade improvement or paper result is claimed. No failed output was replaced by a selected successful rerun.

## Preservation and next boundary

Before and after execution, all **366 protected historical hashes match**, and all pre-existing dirty tracked-file hashes match. `protected_after.json` and the ledger protection fields record this. Existing production repair verification remains 237 passing tests; this isolated sender has five additional offline gate tests. KB, historical experiment results, manuscripts, human-review data, credentials and project default configuration were not changed.

The authorized run has reached its defined failure terminal state. Continuing would require diagnosing the connection separately and defining a new explicit retry/reservation plan within the same overall user budget; this task did not bypass the stop condition or spend the remaining request allowance automatically. No recharge, new key, security-setting change, public publication or additional model comparison occurred.
