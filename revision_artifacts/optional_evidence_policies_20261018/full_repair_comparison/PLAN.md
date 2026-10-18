# Full-repair fixed comparison — pending external-send approval

This replaces the narrower 07a316a-versus-6de9afc comparison for the proposed model check. Prior artifacts remain as an explicitly superseded design record. **No model/API requests have been made.** The parent reports updated external-send confirmation is pending for DeepSeek official `https://api.deepseek.com`, model `deepseek-flash`, the six fixed project requirement/evidence samples below, maximum 12 total attempts and RMB 50. Nothing in this artifact constitutes receipt of that confirmation.

## Baselines, switches and capture method

- Old code checkpoint: **3659d37ed21a2f286027f2603b171f2ad22565fe**.
- New code: **6de9afc02f5f9b524531c3b272ce82d9194a4d79**; documentation HEAD **7e4a5aec608e74d69e74da590bd359d74d056916** has identical relevant code.
- Shared transport for this proposed new development comparison: `model=deepseek-flash`, temperature 0, `max_tokens=8192`, JSON object output and `extra_body={"thinking":{"type":"disabled"}}`. This is a deliberate common model/mode override for both arms, not reproduction of the historical provider revision or a silent project-config change. The local default remains unchanged.
- New v4 switches: `selection_policy="numeric-first-reserve-one-nonnumeric-v1"`, `risk_policy="independent-reference-quantity-applicability-v1"`. Fixed evidence count 12 and evidence-body budget 500 characters. Old builder keeps its own numeric-first/character-slice behavior at the same limits.
- New UI switch: `risk_policy="independent-reference-quantity-applicability-v1"`, forwarded through the public single-requirement entrypoint and real graph. The old UI compactor and its original messages expression are read from the old commit.
- Retrieval rescue is **not enabled/exercised** in these calls: evidence is frozen. Its opt-in real entrypoint is `aligned_retrieve(..., policy="zero-hit-unfiltered-rescue-v1")`. No new analyzer, extraction, retrieval, judge or repair call is permitted by this design.

`../freeze_full_repair_plan.py` uses `git show` and AST selection to execute only the old prompt constants and pure evidence compaction/building functions. It does **not** import or execute the old generation/client/graph entrypoints. The old UI messages expression is evaluated separately from the old call function. No checkout/worktree reset occurs. Shared old helper source equality is asserted against the new commit.

New requests are captured from the actual new `generate_structured_shalls` and `generate_engineering_requirements_for_requirement` entrypoints using stub completions and fake client objects. The latter exercises the real graph. Socket connections and JSON repair are blocked. The shared explicit non-thinking option is then added identically to both captured request bodies. A later isolated transport must send these exact bodies, rather than call the unbounded historical experiment scripts.

`FROZEN_PLAN.json` contains all twelve complete request bodies, commits, switch settings, input/source-file SHA256, selected IDs, request SHA256 and sizes. Each `<ID>.diff` records the complete prompt difference. These artifacts are **local**, not uploaded. Counts are derived from actual text, not a maximum budget multiplied by twelve.

## Fixed cases, reasons and actual measurements

No sample was replaced based on outcomes. V4 original text comes from `original_requirements_v2.jsonl`; values and candidate order come from the saved v4 `_evidence_values` mapping joined to the audited KB. Both arms receive that same candidate order. This controls the comparison but does not reconstruct the original script's nondeterministic set order. UI input is the saved `batch_20260730_164747/all_requirements_results.json`, including raw requirement text and stakeholder.

| ID | Fixed reason | Old chars / UTF-8 bytes / input envelope | New chars / UTF-8 bytes / input envelope |
|---|---|---:|---:|
| OR001 | Previously fixed TBD/placeholder boundary | 7,608 / 12,832 / 16,928 | 18,899 / 27,834 / 31,930 |
| OR010 | Previously fixed dGH unit boundary | 7,320 / 13,052 / 17,148 | 17,471 / 26,494 / 30,590 |
| OR023 | Previously fixed suspicious -100°C source case; original edition unmatched | 7,361 / 11,460 / 15,556 | 16,428 / 24,125 / 28,221 |
| R001 | First of three previously selected consecutive UI records | 43,626 / 64,072 / 68,168 | 72,825 / 98,567 / 102,663 |
| R002 | Second selected UI record in same batch | 30,899 / 45,181 / 49,277 | 52,912 / 72,692 / 76,788 |
| R003 | Third selected UI record in same batch | 9,246 / 15,294 / 19,390 | 9,523 / 15,793 / 19,889 |

Each input envelope = measured UTF-8 message-content bytes + 4,096 framing reserve. This is a conservative **planning assumption**, not an exact tokenizer count or verified chat-template upper bound. Each output cap is 8,192 tokens.

Totals: **294,118 characters; 427,396 UTF-8 content bytes; 476,548 planning input tokens; 98,304 maximum output tokens; 12 requests**. The largest per-request input-plus-output planning envelope is 110,855.

## Separate the treatment groups and controls

All six old/new prompts differ under the requested full-repair baseline; there is **no identical-prompt pair in this revised plan**. This supersedes the five-identical-pairs finding for the narrower optional-policy comparison.

- **V4 prompt/record repair group (OR001/OR010/OR023):** old prompts contain extracted value text alone and raw character slices; new prompts include preserved operator/unit records, explicit missing applicability, bounded whole records/context and stronger uncertainty instructions. OR001/OR010 keep selected IDs and order. OR023 additionally changes one selected item through the opt-in nonnumeric reservation: E-TCV-TEMP-022 is replaced by E-SYS-COMP-012. Any outcome difference is a combined treatment effect; it cannot isolate a single change.
- **UI actual-evidence recovery group (R001/R002):** selected IDs/order remain equal. Old R001 has 13 bodies of `...` (39 characters total), versus 5,296 source-body characters now; 11 current bodies are partial. Old R002 has nine `...` bodies (27 characters), versus 4,505 source-body characters now; four current bodies are partial. Metadata/budget markers and instructions also change. More retained text is not proof of semantic support, correct conditions or quality improvement.
- **No-supported-evidence negative case (R003):** both versions have zero supported evidence. The prompt still changes because instructions/context bookkeeping changed. It is a negative case for evidence recovery, **not** an identical-prompt stochastic control. Its generated values must not be credited to recovered supporting evidence.
- **Post-generation checks:** citation/schema/risk/grade rule changes are checked offline and can be applied to shared saved completions. A grade change is not an output-quality metric. Do not use the extra diagnostic tags as evidence of engineering correctness.

This small proposed check does not evaluate extraction recall, mapping rescue recall, full-pipeline historical order, model generalization, main-experiment performance, or human scoring. Existing extracted values are held fixed, so the extraction-model prompt/response change is not measured. A later report must distinguish raw generated text from postprocessor effects and document all changed prompt groups. No claim of improvement can be made merely from prompt length, token count or grade uplift.

## Provider, USD cost and a fail-closed RMB 50 budget

The [official current pricing page](https://api-docs.deepseek.com/quick_start/pricing/) identifies `deepseek-flash` as **DeepSeek-V4.1-Flash-1017**, 1M context and maximum 384K output; thinking defaults on. Peak cache-miss input is **$0.30/M tokens**, peak output **$1.20/M tokens**. Off-peak is half price. Budgeting below deliberately ignores discounts/cache hits. The [chat schema](https://api-docs.deepseek.com/api/create-chat-completion/) says input plus output must fit context; the proposed 8,192 output cap is well below its documented maximum. Both sources were checked during the preparation task; the parent independently confirmed the current route and tariff. Recheck at execution because aliases/prices can change.

1. **Text-specific planning cost:** `476548 * 0.30 / 1e6 + 98304 * 1.20 / 1e6 = $0.2609292`. This is not an RMB quotation and relies on the unverified token planning envelopes.
2. **Tokenizer-independent conservative transport reservation:** for budgeting each accepted request at the published 1M context ceiling, use 1,048,576 input tokens per attempt (the larger binary interpretation), *plus* the separate 8,192 output allowance, even though their sum cannot actually exceed context. Twelve attempts then reserve **$3.8928384** at peak/cache-miss rates. This intentionally overcounts context/output and is much larger than the measured-text estimate. It is valid only while the verified model limits and tariff remain in force, with no tools or hidden extra requests. Rejected requests, provider billing behavior or another process's account use are not under local control.
3. **CNY/settlement gate remains unresolved:** the official Chinese pricing page repeatedly failed to load, and a reliable applicable settlement conversion was not obtained. No CNY rate or arbitrary exchange rate is invented. Neither USD figure establishes the RMB cap by itself. Before enabling transport, obtain a verified applicable CNY tariff or a conservative verified all-in USD→CNY settlement bound including fees/taxes if applicable. Use `Decimal`; reserve at the worse current price, not a projected discount.
4. Require total initial reservations ≤ **RMB 40**, leaving **RMB 10 unallocated** within the user's RMB 50 maximum. Using the context-based USD reservation above, the all-in conversion bound must satisfy `3.8928384 * bound <= 40`; this is an admission condition, **not** a claimed exchange rate. If the verified calculation does not fit, do not send. The unallocated margin does not authorize extra attempts.
5. Maintain a persistent ledger before every attempt, keyed by request hash. Maximum **12 HTTP attempts total**, including any retries; the planned retries are **zero**. Reserve the full worst-case cost atomically before dispatch. On timeout, disconnect, missing usage or ambiguous billing, retain the reservation as fully consumed and halt the batch. Never treat timeout as zero cost. No automatic model fallback, repair, continuation, analyzer or judge call.

The installed OpenAI SDK 2.37.0 defaults to two retries. A future dedicated client must set **`max_retries=0`**, and all outer retry/repair wrappers must be bypassed. Proposed explicit HTTP timeouts: connect 10 seconds, read 120 seconds, write 30 seconds, pool 10 seconds. Timeouts are I/O limits, not billing cancellation guarantees. SDK retries left unchanged could produce 36 attempts; such execution is prohibited by the request cap even if a financial allowance remained.

Proposed request validation: hash-identical body; fixed model/baseURL; explicit thinking disabled; `max_tokens=8192`; one completion; no tools; sequential transport; no default disk cache. Input content must not exceed its frozen byte/character caps. Matching tokenizer validation is desirable for the tight estimate; the larger context-ceiling reservation avoids relying on that estimate for financial safety. Store raw usage and returned model identity in isolated artifacts. Stop on identity/price drift or any constraint failure.

**No sender is included or enabled.** This is a concrete execution contract, not a claim that existing production code already enforces it. Current executable allowance remains zero until the parent's external-send confirmation and CNY/settlement budget gates are satisfied. Approval for the stale `deepseek-chat` alias is not reused; the parent is requesting the active `deepseek-flash` scope explicitly.

## Verification and retained files

The offline freeze completed successfully: six pure-old-builder preparations, six new real-entrypoint captures using stubs, twelve serialized requests and six diffs. Protected-file checks confirm **366 historical hashes unchanged**; pre-existing dirty tracked-file hashes also remain unchanged. Earlier production code tests remain **237 passed**. This follow-up changes only isolated planning artifacts, not KB/results/papers/human files or application configuration.

The `.diff` artifacts intentionally preserve original prompt whitespace, including unified-diff blank context lines; Git's whitespace checker reports those as trailing spaces. They are retained for exact review. Scoped whitespace checks for the Python harness, report, log and JSON pass; no source prompt was trimmed to silence the artifact warnings.

Reproduce locally, without networking:

```powershell
$env:PYTHONPATH=''
$env:PYTHONIOENCODING='utf-8'
$env:OMP_NUM_THREADS='8'
& 'D:\Users\yando\miniconda3\envs\cooling_rag_env\python.exe' -B revision_artifacts\optional_evidence_policies_20261018\freeze_full_repair_plan.py
```

Outstanding: updated external-send confirmation; verified CNY tariff/all-in settlement bound; eventual isolated transport and budget ledger verification before sending. No paid calls, historical rerun, manuscript change or new human review occurred.
