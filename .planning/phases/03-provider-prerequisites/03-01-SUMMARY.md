# 03-01 summary — provider firewall prerequisites

Captured: 2026-09-08 10:09:44 Asia/Bangkok
Repository: `https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git`
Worktree: `C:\Users\chatc\Projects\sw-localai-deepseek-harnes\.worktrees\vm105-authoritative-roadmap`
Branch: `codex/vm105-authoritative-roadmap`
Task 3 base: `e1d416f5a57e12552bc35607100932260c9a091f`

- Total - 09/21
  - Phase 1 - 05/05
  - Phase 2 - 03/03
  - Phase 3 - 01/02
  - Phase 4 - 00/09
  - Phase 5 - 00/02

## Verdict

FW-01: **BLOCKED / NOT PROVEN**. Plan 03-01 and Phase 3 are not PASS.
Plan 03-01 is complete with this blocked outcome; Phase 3 plans complete: 1/2.

The independently reviewed and controller-accepted packet digest is
`FF91A5E0D0FB29F7CAFEFFF32B8B3A1A7DD2A76CC087A38E4939435532D361A1`.
It contains zero rules, `approvedRuleIds=[]`, `releasableRuleIds=[]` and no
mutation authority. Task 3 therefore executed zero add, inverse, postflight or
rollback commands. No firewall or other live state was changed.

## Current evidence

- [Provider prerequisite inventory](../../../docs/evidence/phase-03-provider-prerequisites.md)
- [Immutable firewall packet](../../../docs/evidence/phase-03-firewall-packet.json)
- [Independent review and controller acceptance](../../../docs/evidence/phase-03-firewall-review.md)
- [Zero-mutation result](../../../docs/evidence/phase-03-firewall-results.json)

At 10:09:20–10:09:44 +07:00, strict read-only checks matched the accepted
baseline: VM105 remained `deepseek-harness-01` at `192.168.1.139`, eth0 MAC
`bc:24:11:5c:49:52`, with the accepted ED25519 SSH identity. The Harness service
was enabled and active with zero restarts, its only TCP 3080 listener remained
`127.0.0.1:3080`, and VM-local HTTP returned 200. UFW remained active with deny
incoming, allow outgoing, disabled routed, and only the two retained TCP 22 rules
for Bell-PC2 `.161` and Hermes VM104 `.141`. The owner ssh tunnel still listened
on loopback IPv4/IPv6 and returned HTTP 200; direct TCP 3080 access returned false.

## Route disposition

Explicit routing remains required. Automatic routing is disabled as packet policy;
runtime enforcement and automatic attribution remain NOT PROVEN.

| Route | Network result | Remaining status |
| --- | --- | --- |
| OpenRouter Auto | NO_FIREWALL_CHANGE | Inference NOT PROVEN |
| OpenRouter Pareto Code | NO_FIREWALL_CHANGE | Child-model attribution NOT PROVEN |
| VM1201 Qwen | BLOCKED | Current machine/listener/model, authentication, ownership, destination-seen source and negative control missing |
| Bell-PC2 local worker | BLOCKED | Upstream service/model/authentication, destination-seen source and negative control missing |
| Typhoon Thai text | NO_FIREWALL_CHANGE | Inference NOT PROVEN |
| Typhoon OCR | BLOCKED | Exact OCR wire contract and installed Harness compatibility missing |
| Codex Luna | BLOCKED | Supported human OAuth entry and effective isolated storage missing |
| Codex Terra | BLOCKED | Supported human OAuth entry and effective isolated storage missing |
| Codex Sol | BLOCKED | Supported human OAuth entry and effective isolated storage missing |

The VM104 SSH rule current need remains NOT PROVEN and the rule is unchanged.
Historical pnpm and RX-drop WARNs remain open. No credential, OAuth, provider,
route, inference, service, VM, browser, package or model action occurred.

## Validation

| Check | Result |
| --- | --- |
| Firewall packet SHA-256 against accepted review | PASS |
| `Test-Phase03FirewallPacket.ps1 -SelfTest` | PASS — 43 rejection cases |
| `Test-Phase03FirewallPacket.ps1 -Stage Preflight` | PASS — structural only, no mutation release |
| Postflight / Rollback stages | NOT APPLICABLE — no approved or executed rule ID |
| `Test-Phase03Evidence.ps1 -SelfTest` | PASS — 23 detection and 16 continuation cases |
| `Test-Phase03Evidence.ps1 -Stage Network` | PASS — exit 0, no findings |
| Manual redaction review of five network outputs | PASS — no secret material found |

## Next credential-preparation action

Plan 03-02 is the next action. It may consume the three no-firewall-change
transport results only as network prerequisites. Begin with a read-only metadata
inventory of the effective
VM105 credential storage path plus safe consumer-disconnect and backup eligibility.
Keep all six blocked routes blocked. Do not create a key, start OAuth, type a secret,
or begin an owner credential session from this blocked packet.
