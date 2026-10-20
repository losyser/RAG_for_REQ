# Connection diagnosis and offline routing repair

No additional authenticated/model request was made. The original failure and RMB 2.162688 reservation remain intact: **one model dispatch attempt used, eleven remaining under the original twelve-attempt cap**. This follow-up used two unauthenticated public GETs to `https://api.deepseek.com/`, with no project content, then offline tests only.

## Reproducible evidence

| Check | Observed result | Interpretation / boundary |
|---|---|---|
| Local DNS | `api.deepseek.com` resolved successfully | Not a reproduced DNS-resolution failure. |
| Existing environment routing, ordinary HTTPX client | Public HTTPS GET returned **401** in 0.640s | HTTPS/TLS route reached the service; no Authorization header was sent, so 401 is expected and does not validate the API key. |
| Original custom transport construction | Same public GET failed in 0.047s | `ConnectError → ConnectError → PermissionError`, errno **13**, Windows error **10013**. Socket connection denied by the environment/OS policy; no HTTP response. |
| HTTPX 0.28.1 source | `allow_env_proxies = trust_env and transport is None` | Supplying the run's `GuardedTransport` disabled automatic environment-proxy discovery in the outer client. |
| Original delegate | `httpx.HTTPTransport(retries=0)` without proxy | The delegate did not restore proxy selection and attempted direct connection. |
| Existing proxy metadata | HTTPS/HTTP/ALL proxy: protocol `http`, host `127.0.0.1`, port `7890`; no credentials in configured proxy URL | Already-present routing, not a new endpoint or changed system setting. NO_PROXY values were not dumped. |

Captured evidence is in `readonly_environment.json` and `public_get_comparison.json`. The public GET using existing routing was performed **before** the denied direct-path reproduction. No additional live network test or alternate direct route was attempted after that denial.

This establishes a concrete sender configuration defect: a custom request-count transport inadvertently suppressed the existing proxy route, and the original delegate construction reproducibly encounters socket permission denial. It is strong explanatory evidence for the original immediate APIConnectionError, but its original lower-level exception chain cannot be recovered retrospectively because that first run logged only the SDK wrapper. The reproduced chain is explicitly a separate public-GET diagnostic, not a fabricated original trace.

The Windows error alone **cannot identify whether the controlling restriction is the platform sandbox, a host firewall or another OS network policy**. No explicit tool approval-review rejection was returned. Do not relabel this as a proven sandbox denial or change policy to test it. The direct path is denied; do not retry it. The already-configured proxy path worked in the authorized public read. No certificate error was observed on that path. Authentication/model availability remain untested because no new authenticated request was sent. The `ssl.get_default_verify_paths()` result in the metadata is not evidence of a certificate failure; HTTPX has its own certificate handling, and the default HTTPS request succeeded.

## Local reversible repair, offline verified

Added `../environment_transport.py` and changed the isolated sender's delegate to `EnvironmentRoutingTransport(timeout)`:

- Its inner standard HTTPX client leaves `transport` and `proxy` unspecified, allowing normal `HTTPS_PROXY/ALL_PROXY/NO_PROXY` discovery. It does not choose a new proxy, ignore NO_PROXY, alter VPN/system/environment settings or disable TLS verification.
- The outer `GuardedTransport` remains responsible for endpoint/body verification, pre-dispatch reservation, twelve-attempt limit and rejection of unapproved extra attempts.
- The inner client only permits the exact approved POST completion endpoint; redirects are off. SDK `max_retries=0` remains unchanged, and the installed HTTPX default transport retry count is zero.
- The adapter uses streaming at the transport layer only to preserve HTTPX response handling; the frozen API request is still non-streaming. It does not add model calls, repair, continuation or provider fallback.
- New exception-chain diagnostics retain only type, errno and winerror, without exception message text, URLs, credentials, headers or environment values. The original top-level error is still redacted by the existing sender.

**Nine offline tests passed:** four new route/cause/SDK-wrapper tests plus the previous five budget/dispatch guard tests. New tests assert normal proxy selection, respect for NO_PROXY, zero transport retries, unchanged real SDK serialization through a mock delegate, rejection of a second implicit request, and credential-free cause metadata. Test environment changes are confined to a temporary `patch.dict` in the test process and restored automatically; there is no network I/O in these tests.

The updated sender was **not executed live**. It still refuses to reuse the existing run's ledger through exclusive creation, so running it again is not a supported continuation mechanism. Do not delete or reset the ledger to resume. The original executed sender is preserved at commit `7bb7cdd4c8a0ff1dc45982a19de08161aee8de8e`; its source SHA matches original RUN_METADATA. The updated source hash naturally differs, and the original metadata is intentionally not rewritten.

## Recommended continuation for parent coordination

Do not send automatically. First have the parent fix the remaining plan and require a continuation runner to consume the **existing cumulative ledger**, with original failure reservation retained. A local proxy route being reachable does not prove authenticated generation will work.

Recommended plan: continue original frozen slots **2 through 12**, without retrying OR001-old. This uses the remaining eleven attempts and retains all six originally chosen cases:

1. OR001-new, marked unpaired because OR001-old failed.
2. OR010 old/new.
3. OR023 old/new.
4. R001 old/new.
5. R002 old/new.
6. R003 old/new.

If all succeed, the valid comparison population is **five complete pairs plus one unpaired new output**, not six pairs. Keep the failure in all reporting. Retrying OR001-old and then running every original remaining request would total thirteen attempts and is forbidden under the current cap. No slot can be added or failed result silently replaced to achieve a cleaner table.

Financial reservation remains `1 retained + 11 possible = 12 × RMB 2.162688 = RMB 25.952256`, under RMB 40 initial and RMB 50 total bounds at the verified peak tariff. No uncertain fee is refunded. The continuation must retain zero SDK/outer retries, stop-on-connection/timeout/identity failures, explicit non-thinking Flash, frozen request hashes and full responses/usage/timing. Recheck current tariff/endpoint if execution is delayed. Do not change the supplier or system security settings.

## Preservation

`preservation.json` confirms all **366 historical hashes** and pre-existing dirty tracked-file hashes still match. Original failure artifacts compare unchanged to commit 7bb7cdd after Git line-ending normalization; no recorded response, cost reserve, usage or evaluation outcome was rewritten. The first byte comparison against Git surfaced only normal Windows CRLF/LF normalization and was corrected to account for it.

Current state: routing defect repaired locally and offline-tested; direct socket denial not bypassed; zero additional model attempts; awaiting parent-coordinated remaining-sample plan before any authenticated continuation. No VPN, system proxy, firewall, certificate store, credentials or safety settings were changed.
