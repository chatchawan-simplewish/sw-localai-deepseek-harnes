# Phase 3 provider prerequisites — read-only preparation

Captured 2026-09-08 09:08–09:21 Asia/Bangkok. Repository origin verified as
https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git.
Worktree: `C:\Users\chatc\Projects\sw-localai-deepseek-harnes\.worktrees\vm105-authoritative-roadmap`;
branch `codex/vm105-authoritative-roadmap`; base `36611f447d1f5f827a9f2cf6133381f33e006806`.
Initial tracked/untracked status was empty.

- Total - 08/21
  - Phase 1 - 05/05
  - Phase 2 - 03/03
  - Phase 3 - 00/02
  - Phase 4 - 00/09
  - Phase 5 - 00/02

FW-01: **BLOCKED**. This is preparation evidence, not network release or phase completion.
The packet contains zero additions, three supported existing HTTPS paths, and six
blocked routes. Preflight must fail while those blockers exist. An independent
reviewer and controller must accept a concrete packet digest before any mutation.
No review approval, results receipt, or phase summary is fabricated here.

## Fresh management baseline

Final strict-SSH recheck at 09:20:48 returned the same hostname, eth0 address/MAC,
service state, exclusive loopback listener, UFW defaults/two rules and HTTP200.
Bell-PC2's 09:20:48 check returned the same tunnel listeners/PID and HTTP200;
the direct LAN probe returned HTTP000 with curl exit 28. The packet uses this
final capture for its management baseline.

| Observation | Direct evidence and capture time (+07:00) |
| --- | --- |
| VM105 identity | 09:08:35 verified SSH: hostname `deepseek-harness-01`, eth0 `192.168.1.139/24`; 09:09 MAC `bc:24:11:5c:49:52`. The initially queried ens18 interface did not exist; eth0 was discovered from ip output and checked. |
| SSH identity | StrictHostKeyChecking=yes, BatchMode=yes, IdentitiesOnly=yes, recorded key `C:/Users/chatc/.ssh/codex-prox01-vms-ed25519`. Existing known-host ED25519 identity `SHA256:sUlbmGFvjHrJtyJku/Nmjd7tn+N3xIdX1eL2R6TJMrw`; no host-key enrollment or bypass. |
| Harness | `dsh --version` returned `0.1.1-rc.2`; installed root package pins that release. |
| Service | 09:08:35 `deepseek-harness.service`: enabled, active/running, User dsh, Result success, NRestarts 0. WorkingDirectory `/srv/dsh/workspaces` checked 09:13. |
| Listener | 09:08:35 `ss -lntp`: only Harness listener `127.0.0.1:3080`, PID 829. VM-local HTTP 200. |
| UFW | Active; deny incoming, allow outgoing, disabled routed. Only `22/tcp ALLOW IN 192.168.1.161` comment Bell-PC2 SSH and `22/tcp ALLOW IN 192.168.1.141` comment Hermes VM104 SSH. Rules retained. |
| Owner tunnel | Bell-PC2 address `192.168.1.161`; TCP 3080 listeners `127.0.0.1` and `::1`, PID 42076 process ssh. Local curl HTTP 200 at 09:10. Existing tunnel retained. |
| Direct LAN denial | Bell-PC2 curl to `http://192.168.1.139:3080/` HTTP 000 after bounded five-second probe at 09:10. VM105 self-LAN probe also HTTP 000 at 09:15. This proves no HTTP reachability, not the packet-drop location. |
| State metadata only | `/home/dsh/.dsh` 0700 dsh:dsh; `storages` 0700; `settings.yaml` and `storages/workspace.json` 0600. `.credentials.yaml` absent at the documented default path. No file contents read. |

The SSH fingerprint above is a known-host identity correlated with successful
strict SSH access, not a newly captured secret. DHCP identity must be rechecked
before reusing the address. Historical pnpm drift/RX-drop WARNs and VM104 rule
current-need NOT PROVEN remain open; this task did not diagnose them.

## Installed entry and storage surfaces

Evidence sources below are installed package documentation/code on VM105,
read through the same strict SSH session on 2026-09-08; user settings, environments,
credential documents and service environments were never read.

- `@deepseek-ai/dsh-llm-pi-ai@0.1.1-rc.2/README.md`: provider catalog plus custom
  `baseURL`, protocol and model-list support; explicit provider/model resolution;
  one credential per provider route can serve its documented models. Missing
  explicitly referenced credentials fail closed. Ambient authentication exists,
  so future VM105 isolation must be verified before enabling a route.
- `@deepseek-ai/dsh-client-ui-settings-models@0.1.1-rc.2/README.md`: API input writes
  through credentials.set; settings describe is redacted; empty draft input keeps
  native authentication possible. Custom-provider fields are Provider ID, display
  name, Base URL, protocol and model rows.
- `@deepseek-ai/dsh-settings-file@0.1.1-rc.2/README.md`: default settings document is
  `/home/dsh/.dsh/settings.yaml` for the observed home. That file exists at 0600;
  the effective plugin override is not established because user configuration was
  deliberately not opened.
- `@deepseek-ai/dsh-credentials-local@0.1.1-rc.2/README.md`: documented default
  `/home/dsh/.dsh/.credentials.yaml`; writes 0600 under 0700 directory. It stores
  references and native records including `llm-pi-ai/openai-codex`. The default
  path is absent; effective path/override remains NOT PROVEN. Same-UID processes
  can read this store according to its documentation: owner-only modes are not
  isolation from Harness tools.
- Installed `@earendil-works/pi-ai@0.82.1` provider
  `dist/providers/openai-codex.js` uses `https://chatgpt.com/backend-api` and native
  OAuth. Its `dist/providers/data/openai-codex.json` contains all three requested
  gpt-5.6 identifiers. Harness pi-ai source registers authorization flows when the
  authorization seam is mounted, and `dsh-authorization/README.md` documents the
  seam. This is backend capability, not proof of an available human login surface.

Exact installed README provenance:

```text
/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-llm-pi-ai@0.1.1-rc.2_236ec8963c16cce3286da2b293de8170/node_modules/@deepseek-ai/dsh-llm-pi-ai/README.md
SHA256 d148c2d2a9ec511a96dca00a4798f5d7e632f1f47af8ff7151f18f7675728621
/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-credentials-local@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai+ds_7bb67d14430a2d1ff3cabd2ed2468913/node_modules/@deepseek-ai/dsh-credentials-local/README.md
SHA256 f67b9286a68faa71feeb42760d41bc2ebabbd10e288c5a0432a5d0d1fb64670b
```

Browser verification at 09:09 and immediately before claiming existing tab:
Chrome browser ID 2, profile exactly `Codex-Chrome-Bell-PC2`, extension identity
`dfd27eec-84b9-446f-81ec-a134992060a6`, tab 435371600, URL
`http://127.0.0.1:3080/`, title DeepSeek Harness. No new tab/link opened.

Onboarding showed only official DeepSeek API input. Configure later dismissed the
coordinator pass; Models showed Add provider and Add a custom provider. Add
provider offered openrouter and openai-codex. Selecting openai-codex in an unsaved
draft still showed API input and no native sign-in control. The custom draft
offered openai-completions, openai-responses and anthropic-messages. Both drafts
were cancelled; no Apply/Create/Save, model selection, credential entry, login,
consent, or endpoint interrogation occurred. No screenshot was taken.

## Nine-route inventory

All source access dates are **2026-09-08**. S1–S8 refer to exact official sources
below; I1 refers to the installed surfaces above; H1/H2 refer to host evidence
below. “No firewall change” is a transport decision only; inference remains
NOT PROVEN and no route was enabled.

| Route | Explicit provider / model | Endpoint | Authentication / Harness surface | State path / resource owner | Transport and verdict |
| --- | --- | --- | --- | --- | --- |
| OpenRouter Auto | openrouter / openrouter/auto (S1,S3,I1) | https://openrouter.ai/api/v1 | Provider bearer authentication; Models → Add provider → openrouter, custom model list | Documented default credentials path above; effective override NOT PROVEN. Remote service OpenRouter; VM105 storage dsh. One fresh VM105-isolated OpenRouter credential may serve both named routes. | VM105 HTTPS GET /models 200, exit 0, source .139, remote 104.18.3.115 at 09:16:15. NO_FIREWALL_CHANGE; route inference NOT PROVEN. |
| OpenRouter Pareto Code | openrouter / openrouter/pareto-code (S2,S3,I1) | https://openrouter.ai/api/v1 | Same provider and write-only surface; no separate credential per model required | Same isolated provider store; OpenRouter remote owner | Same explicitly shared provider transport probe; NO_FIREWALL_CHANGE; child-model attribution NOT PROVEN. |
| VM1201 Qwen | Local Qwen; exact served identifier BLOCKED (H1,I1) | Current endpoint BLOCKED; .143:8000 is historical candidate only | Supported custom OpenAI-compatible surface; actual worker auth BLOCKED | Effective worker owner, credential path and current model BLOCKED | Strict SSH to recorded .143:22 timed out; VM105 historical .143:8000 GET /v1/models HTTP000. BLOCKED: current identity/listener/model/firewall/source-seen-by-destination not available. |
| Bell-PC2 local worker | Local provider/model identifier BLOCKED (H2,I1) | Confirmed gateway http://192.168.1.161:11435; exact upstream model endpoint BLOCKED | Custom OpenAI-compatible surface possible; actual gateway/worker auth policy BLOCKED | Caddy process owner BELL-PC2\\chatc; Windows firewall host Bell-PC2; actual backend/credential path BLOCKED | VM105 GET /v1/models HTTP000; owner host unauthenticated GET returns 403. BLOCKED: upstream listener/model/auth and destination-observed VM105 identity/valid negative control missing. |
| Typhoon Thai text | Typhoon / typhoon-v2.5-30b-a3b-instruct (S4,S5,I1) | https://api.opentyphoon.ai/v1 | Provider bearer authentication; custom openai-completions provider and explicit model | Documented VM105 default above; effective override NOT PROVEN. Remote service OpenTyphoon; VM105 storage dsh | VM105 GET /models 200, exit 0, source .139, remote 74.125.200.121 at 09:16:15. NO_FIREWALL_CHANGE; inference NOT PROVEN. |
| Typhoon OCR | Typhoon / typhoon-ocr (S4–S6) | Official API base https://api.opentyphoon.ai/v1; exact OCR wire path/request contract BLOCKED | Official docs use typhoon-ocr helper; Harness-compatible OCR request/image support not established | Candidate same VM105 store only if same provider credential scope confirmed; remote OpenTyphoon | Base HTTPS /models 200 proves transport only. BLOCKED: exact OCR endpoint/request translation and supported Harness route required; no package installed or adapter invented. |
| Codex Luna | openai-codex / gpt-5.6-luna (S7,S8,I1) | https://chatgpt.com/backend-api (installed catalog) | Native OAuth only; backend flow present; usable installed human sign-in surface BLOCKED | Documented default store, native record llm-pi-ai/openai-codex; effective location NOT PROVEN. OpenAI remote, dsh local | VM105 HTTPS GET base 403 at 09:15; TLS transport available, no authenticated access. BLOCKED: supported installed login entry and isolated effective OAuth path. |
| Codex Terra | openai-codex / gpt-5.6-terra (S7,S8,I1) | https://chatgpt.com/backend-api | Same native OAuth requirement and observed surface blocker | Same provider-native record; no per-model OAuth copy | Same provider transport probe; BLOCKED on human sign-in entry/effective isolated state. |
| Codex Sol | openai-codex / gpt-5.6-sol (S7,S8,I1) | https://chatgpt.com/backend-api | Same native OAuth requirement and observed surface blocker | Same provider-native record; no per-model OAuth copy | Same provider transport probe; BLOCKED on human sign-in entry/effective isolated state. |

OpenRouter Auto/Pareto are explicitly selected provider router IDs, not permission
to enable Harness automatic child routing. Their selected backend models may vary;
Phase 4 attribution remains required. Harness explicit routing remains the required
policy; automatic routing remains disabled/NOT PROVEN. No runtime setting was
changed or secret-bearing config inspected to assert more.

### Local host provenance

H1: Windows SSH config metadata maps prox01-local-ai to `192.168.1.143`, belladmin,
recorded key. One strict BatchMode connection with ConnectTimeout=10 timed out.
No current VM1201 identity can therefore be assigned to this address. No alternate
host or VM-power action was attempted.

H2: Bell-PC2 `Get-NetIPAddress`, `Get-NetTCPConnection`, `Get-Process`,
`Get-CimInstance Win32_Process` plus GetOwner returned address .161, Caddy PID17684
and BELL-PC2\\chatc. No Win32_Service row owned this PID. Active Windows firewall
Domain/Private/Public profiles are enabled with Block inbound and Allow outbound;
Ethernet is Public. Rule `{062fee3f-0b42-4016-b816-09c96ec6bd7c}`, display name
Bell-PC2 Local AI Gateway, enabled inbound Allow/Public, program Any, TCP local
11435, local address .161, remote addresses .142/.146/.147. Rule metadata alone
does not prove the intended model listener behind Caddy. Other broad/program rules
were not exhaustively adjudicated; rejection attribution is NOT PROVEN.

No rule is proposed. There is no proven destination-seen VM105 source or suitable
unauthorized negative control for either local worker. The existing .142/.146/.147
allowlist sources must not be treated as unauthorized controls. Bell-PC2's local
403 is application-layer evidence only.

## Official sources

All accessed 2026-09-08 via read-only web retrieval; no account pages or login used.

- S1: https://openrouter.ai/docs/guides/routing/routers/auto-router
- S2: https://openrouter.ai/docs/guides/routing/routers/pareto-router
- S3: https://openrouter.ai/docs/api_reference/authentication
- S4: https://docs.opentyphoon.ai/en/api-reference/
- S5: https://docs.opentyphoon.ai/en/models/
- S6: https://docs.opentyphoon.ai/en/ocr/
- S7: https://learn.chatgpt.com/docs/models (redirect from https://developers.openai.com/codex/models)
- S8: https://learn.chatgpt.com/docs/auth (redirect from https://developers.openai.com/codex/auth)

S5 also lists typhoon-v2.1-12b-instruct; v2.5 is the selected documented agentic text
candidate. This is switchable before configuration and inference, with no added
cost incurred here. API base/model documentation does not establish account access.

## Safe repeatable observation commands

Use strict SSH options from the baseline with these nonsecret remote commands:

```sh
date -Is
hostname
ip -brief address
cat /sys/class/net/eth0/address
systemctl show deepseek-harness.service -p ActiveState -p SubState -p UnitFileState -p Result -p NRestarts -p User -p WorkingDirectory
ss -lntp
sudo -n ufw status verbose
curl --max-time 10 -s -o /dev/null -w '%{http_code} %{local_ip} %{remote_ip}\n' https://openrouter.ai/api/v1/models
curl --max-time 10 -s -o /dev/null -w '%{http_code} %{local_ip} %{remote_ip}\n' https://api.opentyphoon.ai/v1/models
```

HTTP response bodies were discarded during transport probes. No credential values,
credential files, environments, full service environments, raw logs, OAuth state,
inference, firewall writes, package/runtime/model changes or service/VM power actions
were used. Installed documentation examples were not copied as credential values.

## Verification and remaining gate

Run both in-memory self-tests, then Preflight and the Network scanner. Self-tests
must pass. The current Preflight must reject blocked routes, and Network scanning
must report the missing independent-review/results/03-01-summary outputs without
secret findings. These nonzero stage exits deliberately prevent Task 1/Phase 3
acceptance; they must not be bypassed by manufactured receipts or relaxed checks.
Manual redaction review includes this file, packet and both scripts before staging.

The validator requires installed PowerShell 7.5 or newer (7.6.5 was used), supports
only canonical inbound TCP UFW additions and refuses other mutation platforms.
That is sufficient for this zero-addition blocked packet; a future Windows rule
would need platform-specific validation and renewed independent review.

Next work: resolve exact read-only VM1201 access, prove Bell-PC2 upstream service
and auth without reading secret configuration, locate a supported installed native
Codex human sign-in surface, and verify OCR wire compatibility. Then refresh the
packet, rerun validators, and obtain fresh independent review. No owner credential
session should begin from this blocked packet.
