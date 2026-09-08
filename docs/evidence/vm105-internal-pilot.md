# VM105 internal pilot

Status: ACCEPTED WITH LIMITATIONS for disposable internal use. Pilot 04/04; authoritative full roadmap remains 09/21.

## Authority

On 2026-09-08 the owner explicitly approved the existing-instance internal pilot, native provider configuration in the current profile, and existing interpreter ownership for this trial. Access remains SSH-only. This is a new pilot scope; it does not reclassify the prior strict preparation BLOCKED outcome or complete its goal.

## Checks

- [x] 1. UI reachable through existing authenticated SSH forwarding. See vm105-internal-pilot-readiness.md; browser profile Codex-Chrome-Bell-PC2, existing tab DeepSeek Harness at http://127.0.0.1:3080/.
- [x] 2. One provider/model and harmless response. Original OmniRoute model request failed503. Owner then explicitly added OpenRouter for testing at21:17 Bangkok. Harness returned PILOT_OK at21:18, reported4s, TTFT3.9s. Parent initially selected GPT-5.4 Mini; post-response UI showed Auto Router, so exact served model is NOT PROVEN. Coding request was explicitly verified with Auto Router selected. Do not claim a fixed backend or local-only inference for this successful route.
- [x] 3. Disposable coding task and output check. Harness created slugify.py and executed python3 slugify.py. Parent found an ASCII/Unicode boundary issue and sent one focused correction with a Kelvin-sign regression case. Parent read final source and reran self-check over strict SSH:5 cases passed, exit0, SHA256 a3afba54e8d94090fe18b340c5565beb3af345dcae1e010ebe55a61952887021. Actual UI tool output reports landlock-run: partial enforcement (older Landlock ABI); full sandbox enforcement is NOT PROVEN. Use only this disposable internal workspace for the trial.
- [x] 4. Focused independent result review and final handoff. See vm105-internal-pilot-review.md: independent code/self-check/hash and service/listener verification accepted with limitations. Parent closed the stale historical pending sentence before publication.

## Continuation

Parent browser handle harness refers to tab435371600, Chrome browser2, profile Codex-Chrome-Bell-PC2. Reverify profile for any project link/new tab. Owner confirmed provider saved; UI verified OmniRoute VM1205 API key configured. Do not capture credential field values, clipboard, screenshots containing secrets, or raw current-profile files.

Disposable workspace created and verified by readiness agent: /srv/dsh/workspaces/internal-pilot-20260908, dsh:dsh mode0700. Selected in UI on 2026-09-08 approximately21:09 Bangkok. First prompt: Reply with exactly PILOT_OK. Do not call tools or read files. Selected llama-cpp/qwen3.8-27b through OmniRoute VM1205. No successful local answer. Native retries reached4/5 before parent stopped generation; UI then showed Send message disabled and1 turns/1 steps. Error503: local rate-limit queue maxWaitMs5000, job timed out after5000ms. This identifies the observed failure, not confirmed root cause or queue contention. Read-only agent verified VM1205 SSH works but VM1201 HTTP health and SSH connections time out. Current provider UI Base URL matches http://192.168.1.143:8000/v1. No shared queue settings changed. The subsequent OpenRouter coding task passed as recorded above.

Owner requested opening key-management page to create a dedicated key. Management SSH tunnel created on Bell-PC2, PID4356, local bind127.0.0.1:20128 -> belladmin@192.168.1.68 remote127.0.0.1:20128. Used existing project key, BatchMode/IdentitiesOnly/StrictHostKeyChecking/ExitOnForwardFailure/ConnectTimeout10/ServerAliveInterval15. Verified sole listener belongs to that PID and is loopback-only; rootHTTP307 redirects to login. No remote service/firewall/network changes. This is the only new local background process started by the pilot. Retain while management UI is needed; close only this exact owned process when finished.

Management browser handle omni: tab435371650 in verified Chrome profile Codex-Chrome-Bell-PC2, http://127.0.0.1:20128/dashboard/api-manager. Owner signed in and created VM105 Internal Pilot 20260908, then privately entered its key in Harness. Safe key identifier: 2117b688-3826-4e0e-bb13-09fb9c72aee3. Parent saved and reopened permissions: one model llama-cpp/qwen3.8-27b, one connection VM1201 Qwen3.8-27B Q6, two endpoints Chat / Messages and Models, No-Log enabled, management/own usage/shared quota/local usage command disabled. No reasoning routing rules. Empty combo restriction persisted as any combo, so do not claim a combo deny-all; only the explicit local model will be used. No expiration configured; revoke this dedicated key in API Keys after the trial. Existing Hermes key untouched. Before any new credential entry/confirmation/submission, hand off to owner per browser policy; no secret capture. Both browser tabs marked for handoff.

No service restart, ownership repair, package upgrade, firewall/network mutation, or broader exposure is part of this pilot. Existing strict preparation evidence and handoff remain intact as historical scope records.

## Final trial route and limits

- Owner-added OpenRouter with Auto Router is the working route; usage may incur provider charges. No exact cost or served backend has been established.
- Briefly replaced the dedicated OmniRoute allowlist with the existing LM Studio model/connection after confirming its gateway returned401 from OmniRoute's container. No inference was sent to that route. After owner selected OpenRouter, restored the OmniRoute key to its original single llama-cpp/qwen3.8-27b model and VM1201 connection to match the saved Harness provider; keep the local route marked unavailable, not accepted.
- VM105 final read-only service check:active/running, NRestarts0, sole service listener127.0.0.1:3080. The browser remains reached via SSH forwarding.
- Demo output stays only at /srv/dsh/workspaces/internal-pilot-20260908/slugify.py. It validates file-write, shell execution and result flow; it is not production acceptance or a comprehensive sandbox audit.
