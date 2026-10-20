# Fixed prompt and provider preflight — no model requests

Supersedes the preliminary 1.2-million-input-token estimate in REPORT.md. Prepared locally on 2026-10-18. **Execution remains blocked.** Public documentation was read using web browsing; no project data was transmitted to DeepSeek, and no authenticated API or model request was made.

## Exact code comparison and sample selection

Old: `07a316ab8fd6e2aff4d78282f556f5fe2c308ae2`. New: `6de9afc02f5f9b524531c3b272ce82d9194a4d79`.

The six IDs were fixed in the prior UI report, before this batch's results:

| ID | Fixed reason |
|---|---|
| OR001 | Previously observed TBD/placeholder handling boundary. |
| OR010 | Previously observed dGH unit-recognition boundary. |
| OR023 | Known suspicious -100°C source value; unmatched original edition. |
| R001 | First of the three preselected consecutive UI records in `batch_20260730_164747`. |
| R002 | Second preselected UI record from the same batch. |
| R003 | Third preselected UI record from the same batch. |

The UI cases were not chosen from new scores and are not a representative evaluation sample. All original requirement text is taken from the saved inputs. V4 uses saved `_evidence_values` with KB records, insertion order preserved, no fresh extraction. UI uses saved retrieval records with their original raw requirement text and stakeholder. The exact request bodies and hashes are in `FROZEN_PROMPT_PLAN.json`; these are local review artifacts, not approved outgoing requests.

`freeze_prompt_plan.py` loads source files from the two exact Git commits, runs the **actual generation entrypoints** with stub clients/completions, captures the request arguments, and blocks socket connections and JSON-repair calls. It checks that UI compaction helpers are byte-identical across commits. It does not manually approximate the prompt templates. The initial capture attempt exposed a dynamic-module type-resolution issue (`Any`); registering the frozen module in `sys.modules` fixed the capture harness. No production file changed.

## Actual prompt sizes and conservative planning envelopes

Characters and bytes are measured across the message content strings. Token counts are **not tokenizer measurements**: each planning envelope is UTF-8 bytes + 4,096 tokens of framing reserve. This is a conservative byte-fallback planning assumption, not a proven bound for an unavailable model/tokenizer. A matching active-model tokenizer/chat template must be established before any executable budget gate is enabled. No other model's tokenizer was substituted.

| Case | Arm | Prompt characters | UTF-8 bytes | Input planning envelope | Output cap |
|---|---|---:|---:|---:|---:|
| OR001 | old | 18,899 | 27,834 | 31,930 | 8,192 |
| OR001 | new | 18,899 | 27,834 | 31,930 | 8,192 |
| OR010 | old | 17,471 | 26,494 | 30,590 | 8,192 |
| OR010 | new | 17,471 | 26,494 | 30,590 | 8,192 |
| OR023 | old | 17,348 | 25,052 | 29,148 | 8,192 |
| OR023 | new | 16,428 | 24,125 | 28,221 | 8,192 |
| R001 | old | 72,825 | 98,567 | 102,663 | 8,192 |
| R001 | new | 72,825 | 98,567 | 102,663 | 8,192 |
| R002 | old | 52,912 | 72,692 | 76,788 | 8,192 |
| R002 | new | 52,912 | 72,692 | 76,788 | 8,192 |
| R003 | old | 9,523 | 15,793 | 19,889 | 8,192 |
| R003 | new | 9,523 | 15,793 | 19,889 | 8,192 |
| **Total** | **12** | **377,036** | **531,937** | **581,089** | **98,304** |

The largest input-plus-output planning allowance is 110,855 tokens for R001. Request JSON bytes and SHA256 are also recorded separately; content-byte counts exclude JSON syntax. The serialized inputs must be hash-identical at execution, or the plan and approval must be revisited.

**Five of six pairs have byte-identical prompts. Only OR023 changes selected evidence/prompt.** OR023 replaces E-TCV-TEMP-022 with E-SYS-COMP-012. OR001/OR010 and all three UI pairs cannot measure a new prompt treatment under this exact baseline. Any different model answers on those pairs would be sampling/provider variability, not evidence of the post-generation policy's effect. A more economical proposal would use seven unique prompts and run both postprocessors on shared completions, but no request count, case IDs, baseline or approved scope has been silently changed. The proposed 12-request design should be reconsidered by the parent before spending.

## Real integration and explicit switches

| Policy | Real entrypoint | Old/default | New explicit option | What this six-case capture exercises |
|---|---|---|---|---|
| Retrieval rescue | `coverage_retrieval.aligned_retrieve` | `policy="existing_hard_pair_filter"` | `policy="zero-hit-unfiltered-rescue-v1"` | **Not exercised**: all evidence is saved. Only mock retrieval tests cover rescue. |
| Nonnumeric reservation | `structured_req_generator.generate_structured_shalls` | default numeric-first | `selection_policy="numeric-first-reserve-one-nonnumeric-v1"` | Actual v4 prompt generation; one changed pair. |
| Independent v4 risks | same generator | `risk_policy="legacy"` | `risk_policy="independent-reference-quantity-applicability-v1"` | Runs after parsing a completion; no prompt change of its own. |
| Independent UI risks | `generate_engineering_requirements_for_requirement` → `build_graph` → normalization/fallback | `risk_policy="legacy"` | same independent-risk string | Actual graph called with option; prompt unchanged, output handling changes. |

The UI batch entrypoint `generate_engineering_requirements` also forwards the risk option. Current `ui/pages/engineering.py`, `experiment_runner.py`, scripts 54/65/77/77q/85/107 and existing callers do not enable these new options. No CLI/env toggle was silently added. Script 77's selection trace is still legacy, so **do not modify only its generator call** and leave its trace inconsistent. An eventual isolated runner must capture the selected IDs, policy strings and request hash consistently and must not run the full experiment scripts.

## Official provider verification and model blocker

Read on 2026-10-18:

- [Official V4 announcement](https://api-docs.deepseek.com/news/news260424/) states that `deepseek-chat` and `deepseek-reasoner` became inaccessible after **2026-07-24 15:59 UTC**. Their former route was V4 Flash non-thinking/thinking. The local `deepseek-chat` alias is therefore stale, not an established current executable route. No API probe was sent.
- [Official model/pricing page](https://api-docs.deepseek.com/quick_start/pricing/) lists `deepseek-flash` → **DeepSeek-V4.1-Flash-1017**, and `deepseek-v4-pro` → **DeepSeek-V4-Pro-0813**. Both list 1M context, maximum 384K output, and thinking enabled by default. The base URL remains `https://api.deepseek.com`.
- [Official chat API schema](https://api-docs.deepseek.com/api/create-chat-completion/) lists the two current names and a `max_tokens` maximum of 393,216. Input plus generated tokens must fit context. A future non-thinking comparison must explicitly disable thinking for both arms; temperature alone does not do so.

Verified USD prices per million tokens, from the official English pricing page:

| Model | Input cache hit off-peak / peak | Input cache miss off-peak / peak | Output off-peak / peak |
|---|---:|---:|---:|
| deepseek-flash | $0.003 / $0.006 | $0.15 / $0.30 | $0.60 / $1.20 |
| deepseek-v4-pro | $0.022 / $0.044 | $0.66 / $1.32 | $1.98 / $3.96 |

Use peak/cache-miss rates for budgeting regardless of the run time. Under the unverified token planning envelopes, illustrative totals are $0.29229150 for Flash or $1.15632132 for Pro. **Neither is a quotation for deepseek-chat, an RMB estimate, nor an approval to substitute a model.** The Chinese pricing page repeatedly timed out; a search snippet did not establish the complete current CNY tariff. No exchange rate was guessed. RMB execution remains disabled until an applicable current CNY tariff or verified conservative settlement conversion is established.

The official [token usage guide](https://api-docs.deepseek.com/quick_start/token_usage/) provides rough character ratios and a demo tokenizer download. Rough ratios are not hard budget limits, and the guide does not by itself establish that a downloaded tokenizer matches the retired alias/current revision. No model assets were downloaded in this task.

## Required hard RMB 50 controls for any later authorized runner

No executable sender is included. These are concrete acceptance requirements; the current hard execution limit is **zero requests** because approval/model/tokenizer/CNY gates are unresolved.

1. Require the parent's forwarded external-send approval bound to the actual active model, endpoint, frozen manifest hash, case set and allowed request count. Approval mentioning only the retired alias does not authorize a replacement. Recheck official routing/prices at run time; no automatic model fallback.
2. Validate every request hash and its per-row input cap, with the matching tokenizer/template. Reject if measured tokens exceed the row envelope; reject if any maximum input/output/context constraint is unmet. The current planning aggregate is 581,089 input and 98,304 output tokens, not a universal per-call maximum multiplied by 12.
3. Set `max_tokens=8192`, `n=1`, non-streaming, no tools, explicit thinking disabled, sequential calls only. No external extraction, analyzer call, repair completion or judge call. Bypass legacy disk cache to avoid confusing cached outputs with new model results, while retaining raw response usage/model identity in isolated artifacts.
4. Local installed OpenAI SDK is **2.37.0**, with **2 automatic retries** by default. Existing `DeepSeekConfig.make_client` does not override retries (and passes its configured timeout, whose code default is 60 seconds). The SDK's own default timeout is read/write/pool 600 seconds, connect 5 seconds. The later dedicated client MUST use `max_retries=0`; proposed explicit HTTP timeouts: connect 10s, read 120s, write 30s, pool 10s. Disable any outer retry and JSON-repair path too. Unchanged SDK retries could turn 12 logical calls into **36 HTTP attempts**, up to 1,743,267 planning input and 294,912 output tokens; that behavior is prohibited.
5. Before each HTTP attempt, atomically reserve its full worst-case CNY cost using `Decimal`: `(input_cap * peak_cache_miss_CNY + 8192 * peak_output_CNY) / 1_000_000`. Include already charged/unknown attempts and any approved retry reservation in the total. Refuse to start if the total can exceed **RMB 50**. Never reclaim a timed-out or disconnected attempt's reservation without authoritative billing evidence; stop the batch on timeout, missing usage or model-identity drift. A timeout is not proof of zero charges.
6. The proposed retry allowance is **zero**: no retry requests, no retry spending reservation. Keep RMB 10 of the total unallocated as an additional operational margin and require initial scheduled-call reservations ≤ RMB 40; this margin does not authorize retries. Any later retry needs explicit count authorization and a full reservation within the same RMB 50 ceiling. Do not enable the runner when current rates/conversion or tokenizer bounds are unknown.

This cannot guarantee the provider's billing system or prevent account use by other processes; it can bound this dedicated run's planned authorized requests under verified tariffs. No claim is made that the existing production entrypoints already enforce monetary limits.

## Checks and remaining blockers

The freeze harness captured exactly twelve completion calls from real entrypoints using stubs, with zero networking. All 366 protected historical hashes remain unchanged. Prior code verification remains 237 passing tests; this follow-up changes only isolated planning/report artifacts.

Blockers: parent-forwarded external-send approval is absent; configured alias is retired; replacement model must be explicitly chosen/confirmed; matching tokenizer/template and applicable CNY rates remain unverified; five identical pairs weaken the proposed 12-call comparison. No credentials/config/model setting was changed and no paid request was made.
