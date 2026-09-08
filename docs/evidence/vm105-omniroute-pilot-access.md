# VM105 OmniRoute pilot access discovery

Recorded 2026-09-08 20:45 Asia/Bangkok. Read-only infrastructure discovery; no inference, credentials, provider configuration or network changes.

## Result

| Item | Evidence and confidence |
| --- | --- |
| VM1205 private API | `http://192.168.1.68:20128/v1`; historical September 4 deployment metadata, corroborated today by HTTP response from that address. |
| VM105 access | **PASS**: strict known-host SSH as `dsh@192.168.1.139`, existing `C:/Users/chatc/.ssh/codex-prox01-vms-ed25519`; one unauthenticated GET to the exact base URL returned HTTP **401**, remote IP `192.168.1.68`, SSH/curl exit 0 at 20:45:28. |
| Transport | Private LAN HTTP, not TLS. No public endpoint was used. This check proves HTTP reachability only; no broader firewall/ACL assertion. |
| Protocol | Historical project source/contract documents identify OpenAI-compatible chat completions and Responses. `openai-completions` is the documented DSH adapter candidate. Neither inference endpoint was called today. |
| Explicit model candidate | `llama-cpp/qwen3.8-27b`, recorded September 4 under active llama-cpp connection `eb57393b-f559-4acf-aac6-3eb4612e6d1f`. Current availability, access permissions and coding/tool capability are **NOT PROVEN**. Select only after current safe model/permission confirmation. |
| Avoid assumed route behavior | Historical `agent-normal` and `agent-high` combos include cloud/subscription fallback; they do not establish a single explicit-model trial. Proposed slash aliases `agent/normal` and `agent/high` belong to a separate reviewed rollout and must not be presumed deployed. |
| Authentication | Required by today's 401 response. No usable Harness key was discovered or read. Authenticated access and inference remain **NOT PROVEN**. |

## Safe check

The first delegated SSH identity was mistakenly spelled `userdsh`; it returned `Permission denied (publickey)` before any HTTP request. Parent explicitly corrected its authorization typo to independently verified `dsh` and authorized one corrected attempt. This was not an OmniRoute access failure. The corrected command discarded response bodies and emitted only status/IP:

```powershell
ssh -i C:/Users/chatc/.ssh/codex-prox01-vms-ed25519 -o StrictHostKeyChecking=yes -o BatchMode=yes -o ConnectTimeout=10 dsh@192.168.1.139 "curl --silent --output /dev/null --connect-timeout 5 --max-time 10 --write-out 'http_status=%{http_code}\nremote_ip=%{remote_ip}\n' http://192.168.1.68:20128/v1"
```

## Key onboarding boundary

The September 4 credential contract is explicitly a candidate, not execution authority. It preserves existing Hermes keys and requires a dedicated client key, permission PATCH plus metadata readback before delivery, no-log behavior, no management permission, secure in-memory transfer over strict-host SSH, and private native credential storage. Its DSH destination is `/home/dsh/.dsh/.credentials.yaml`, with exact native schema still to be pinned. Do not execute its old gate or copy its broad multi-provider allowlist for this minimal pilot.

For this pilot, the remaining credential-owner action is to provision or explicitly bind a dedicated no-log Harness key to the chosen exact model/connection and deliver it through the approved secret channel to the verified native credential format. Never paste it in chat, inspect an existing secret store, borrow the Hermes key, or put secret bytes in arguments/logs/evidence. Parent must establish its current authorized onboarding method; this discovery does not require user action merely to reapprove the endpoint.

The recorded management sequence is native `POST /api/auth/login`, then `POST /api/keys`, permission `PATCH`, and metadata `GET` (contract lines 89-91). These are documented API paths, not a newly authorized execution contract. No exact dashboard page URL was found in the targeted project documents; the API origin is known, but a dashboard route must be established from current UI/source rather than invented. Parent reports an independent native Harness Fetch available models check at `/v1/models` also returned 401. After private key entry, fetch the current model list and select a returned explicit model; do not auto-select the historical Qwen candidate.

## Source references

All paths below are in `C:/ChatGPT Projects/SW-Selfhosted-Network/`, read-only. These are historical September 4 receipts/designs, not freshly inspected VM1205 configuration.

- `AGENTS.md`: project authority, credential handling, independent review and ownership rules read before discovery.
- `docs/handoffs/omniroute-live-metadata-20260904.md:7-9`: VM1205 running container and published port; `14-28`: provider status, IDs and concrete combo models; `37`: private endpoint; `71`: verified VM105 identity/start receipt; `77-78`: existing Hermes endpoint and historical absent DSH provider surfaces.
- `docs/handoffs/omniroute-live-discovery-scope-20260904.md:11-18`: exact VM1205 SSH address and metadata-only/no-secret boundaries.
- `docs/handoffs/omniroute-routing-completion-20260904.md:15,44`: OpenAI-compatible target and private/public lane separation.
- `docs/handoffs/deepseek-client-step-fix-review-20260904.md:34,45,55`: actual adapter fixture using `openai-completions` (offline verification only).
- `docs/handoffs/omniroute-harness-credentials-contract-20260904.md:3-16,69-84,88-97`: draft status, dedicated storage, protocol/permissions, preconditions and secure onboarding.

Memory registry `C:/Users/chatc/.codex/memories/MEMORY.md:1806-1829` was used only to locate VM1205 context; final endpoint/access findings rely on the project documents and today's HTTP check. No secret files, credential stores, .env files or full logs were read. No changes were made in SW-Selfhosted-Network. Sole output is this evidence file; no commit performed.
