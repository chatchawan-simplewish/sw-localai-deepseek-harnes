# Phase 3 independent firewall packet review

Reviewer: fresh Codex sub-agent `/root/phase3_task2_packet_reviewer`, assigned by
controller `/root`; not the packet author. Review date: 2026-09-08 Asia/Bangkok.
Scope: immutable Task 1 packet and supplied evidence/validators; no live mutation.

Repository origin verified:
https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git.
Worktree: `C:\Users\chatc\Projects\sw-localai-deepseek-harnes\.worktrees\vm105-authoritative-roadmap`.
Branch: `codex/vm105-authoritative-roadmap`.
Review base: `4188d633797cc6b476247862e0f3733cabfecf7e`; initial status empty.

## Immutable decision

- Packet: `docs/evidence/phase-03-firewall-packet.json`.
- SHA-256 of current working bytes: `FF91A5E0D0FB29F7CAFEFFF32B8B3A1A7DD2A76CC087A38E4939435532D361A1`.
- Review findings: **0**; unresolved blocking review findings: **0**.
- Operationally blocked routes: **6**; existing transport paths: **3**.
- Proposed rules: **0**; `approvedRuleIds: []`; `releasableRuleIds: []`.
- Verdict: **NO MUTATION RELEASE / FW-01 BLOCKED**.
- Controller acceptance: **RECORDED** in [Controller acceptance](#controller-acceptance)
  for this exact digest and empty rule lists as a reviewed non-releasable state only.

The packet is internally consistent and complete for its declared blocked state.
Zero review findings does not resolve any operational prerequisite, release a
rule, complete FW-01, or complete the Plan 03-01 mutation checkpoint. Any packet
byte change invalidates this review and requires fresh independent review.

## Identity and management provenance

The 09:20:48 +07:00 packet baseline agrees with the prerequisites record:
`deepseek-harness-01`, eth0 `192.168.1.139`, MAC `bc:24:11:5c:49:52`, and known-host
ED25519 fingerprint `SHA256:sUlbmGFvjHrJtyJku/Nmjd7tn+N3xIdX1eL2R6TJMrw`, correlated
by successful strict SSH. The fingerprint is public identity metadata.
The reviewer checked consistency of supplied observations, not a new live SSH session.

Harness is recorded active under dsh, listening only on `127.0.0.1:3080`; local
and owner-tunnel HTTP probes returned 200. Bell-PC2's existing SSH tunnel listens
on loopback IPv4/IPv6. Direct LAN HTTP000 records unreachability, not an established
firewall drop location. UFW remains active with deny incoming, allow outgoing,
disabled routed, and the two existing TCP22 source rules for `.161` and `.141`.
The unresolved current need for the VM104 rule is preserved; its deletion is not
proposed. DHCP identity and baseline need fresh verification before later execution.

All nine routes retain inference NOT PROVEN. Explicit routing is required;
`automaticEnabled=false` is the packet policy, while `runtimeSettingInspected=false`
and automatic attribution NOT PROVEN prevent claiming verified runtime behavior.
The documented credential default is absent; no effective override, storage
isolation, authentication, or account access is asserted as proven.

## Every route decision

| Route | Review of exact decision and supporting limits |
| --- | --- |
| OR-AUTO | NO_FIREWALL_CHANGE. VM105 `.139` to observed OpenRouter peer `104.18.3.115`, TCP443, HTTPS `/api/v1/models` HTTP200 and exit 0 at 09:16:15. Tuple matches its proof. `openrouter/auto` is an explicit router ID; authentication and selected-child inference remain unproven. |
| OR-PARETO-CODE | NO_FIREWALL_CHANGE. Same explicitly shared OpenRouter transport probe and exact tuple; `openrouter/pareto-code` is separately inventoried. Shared HTTPS transport does not establish model availability or child attribution. |
| VM1201-QWEN | BLOCKED, releaseEligible false. Historical `.143:8000` is described only as a candidate; strict SSH timed out. Current machine/listener/model, auth, firewall owner, destination-observed VM105 source and valid unauthorized control are missing. No mutable target tuple or rule is present. |
| BELL-WORKER | BLOCKED, releaseEligible false. Caddy gateway `.161:11435` ownership/listener metadata and owner HTTP403 do not establish upstream service/model/auth. Recorded allowlist `.142/.146/.147` excludes VM105 but is not exhaustive rejection attribution; those sources cannot be negative controls. Destination-observed source and valid unauthorized control are missing. No rule is present. |
| TYPHOON-TEXT | NO_FIREWALL_CHANGE. VM105 `.139` to observed peer `74.125.200.121`, TCP443, HTTPS `/v1/models` HTTP200 and exit 0 at 09:16:15. Tuple matches proof. Named text model and custom-provider surface are inventory only; no authenticated inference is claimed. |
| TYPHOON-OCR | BLOCKED, releaseEligible false. Base transport cannot establish the exact OCR wire path, image/request translation or compatibility with installed Harness. Shared credential scope is unproven. No helper installation or invented adapter is proposed. |
| CODEX-LUNA | BLOCKED, releaseEligible false. Installed backend/catalog identifies native OAuth and `gpt-5.6-luna`, but usable human login entry and effective isolated state remain unproven. HTTPS403 is transport evidence only. No API credential substitution or login is released. |
| CODEX-TERRA | BLOCKED, releaseEligible false. `gpt-5.6-terra` uses the same inventoried native backend and shared transport evidence; the same login/storage blockers apply independently to this route. |
| CODEX-SOL | BLOCKED, releaseEligible false. `gpt-5.6-sol` uses the same inventoried native backend and shared transport evidence; the same login/storage blockers apply independently to this route. |

Public peer addresses are capture-time observations, not permanent provider IP
grants. Documented provider/model surfaces were cross-checked against the supplied
prerequisites, without repeating external documentation retrieval or live probes.
No credential, provider registration, route enabling, or inference is authorized.

## Exact absence of permissions and validator behavior

`rules` is exactly an empty array. There is no add/inverse command, target rule,
positive/negative rule probe, or execution receipt to approve. All six blocked
routes omit mutation tuples, rule IDs, commands, permissions and target identity.
Top-level releaseStatus and fw01Verdict are BLOCKED, releaseEligible is false,
and both approved/releasable rule lists are empty.

The validator checks nine unique named routes, baseline identity/provenance,
timestamps, loopback service and LAN denial, existing-path tuple/exit consistency,
and blocked-route reasons/absence of mutable targets. Any blocked route forces
zero rules and empty release lists. Preflight explicitly grants no mutation release.
The blocked packet cannot satisfy releasable postflight/rollback receipts.

For a future rule, the code requires canonical inbound TCP UFW add/exact inverse,
host-only tuples, no TCP3080, listener/service and destination-observed source,
a distinct unauthorized negative source, canonical bounded TCP probes, and
before/after state and digest-linked command receipts. These are structural and
receipt-consistency checks; they do not execute commands, prove live provenance,
or replace independent review/controller acceptance. Windows mutation syntax is
unsupported and rejected. That is sufficient for this zero-rule packet; a future
Bell-PC2 rule requires appropriate validation and renewed review.

## Fresh verification

PowerShell 7.6.5; all commands run in the named worktree.

| Command | Observed result |
| --- | --- |
| `./scripts/Test-Phase03FirewallPacket.ps1 -Stage Preflight` | Exit 0: Preflight PASS (structural validation only; no mutation release; independent review and controller acceptance remain required). |
| `./scripts/Test-Phase03FirewallPacket.ps1 -SelfTest` | Exit 0: valid blocked, mixed, no-change, rule, postflight and rollback structures; 37 rejection cases. Synthetic cases are in memory only. |
| `./scripts/Test-Phase03Evidence.ps1 -SelfTest` | Exit 0: 23 detection cases; 14 continuation cases; clean, required-file, allowlist and exact suppressed-report checks. |
| `Get-FileHash -Algorithm SHA256 docs/evidence/phase-03-firewall-packet.json` | Exact digest recorded above. |

`./scripts/Test-Phase03Evidence.ps1 -Stage Network` returned exit 1 with exactly:

```text
docs/evidence/phase-03-firewall-results.json:1:missing-required-file
.planning/phases/03-provider-prerequisites/03-01-SUMMARY.md:1:missing-required-file
```

There were zero secret-category findings in currently existing allowlisted files.
The full Network stage remains incomplete; missing future artifacts are not review
defects and were not fabricated. `git diff --check --
docs/evidence/phase-03-firewall-review.md` returned exit 0 with no output. Packet
SHA-256 was rechecked unchanged after writing this review. Manual redaction review
confirmed only public identity/provenance metadata, paths, digests and credential-free
observations; no secret values, OAuth parameters or authentication headers appear.

## Remaining work and impact

The six operational blockers remain as recorded above. The Network stage cannot
complete until genuine results and the 03-01 summary exist. Controller acceptance
is recorded below for the blocked state and cannot turn the empty rule lists into permission.
No firewall, credential, OAuth, service, VM, browser, package, route or inference
mutation occurred during this review. The routine choice is to preserve the
blocked state; only new evidence and a refreshed independently reviewed packet
can change a route decision.

## Controller acceptance

Accepted by controller `/root` on 2026-09-08 Asia/Bangkok after independently
rechecking the current packet bytes, validator result, VM105 management baseline,
direct TCP 3080 denial, route count, and release fields.

- Accepted packet SHA-256: `FF91A5E0D0FB29F7CAFEFFF32B8B3A1A7DD2A76CC087A38E4939435532D361A1`.
- Accepted approved rule IDs: `[]`.
- Accepted releasable rule IDs: `[]`.
- Controller decision: **accept the reviewed non-releasable blocked state only**.
- Mutation authority: **none**; no add, inverse, postflight, rollback, credential,
  OAuth, route, or inference action is released by this acceptance.

Any packet-byte, identity, baseline, route, endpoint, source, destination, protocol,
port, ownership, command, probe, or verdict change invalidates this acceptance and
requires a new independent review before any live action.
