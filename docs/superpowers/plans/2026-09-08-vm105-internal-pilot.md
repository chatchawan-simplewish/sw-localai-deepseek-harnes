# VM105 Internal Pilot Implementation Plan

> Use bounded sub-agent readiness work and one focused independent review of actual results. Owner approved a fast four-check pilot; no repeated general plan-review loop.

**Goal:** One working provider/model and one disposable coding task through the existing SSH-only UI tonight.

**Architecture:** Reuse the running VM105 instance and native provider settings. Owner enters fresh credentials privately. Existing dsh-owned interpreter is a documented trial limitation, not a passed strict preparation gate.

**Tech Stack:** Existing Harness 0.1.1-rc.2, Windows SSH forwarding, verified Chrome profile Codex-Chrome-Bell-PC2.

## Global Constraints

Current-profile provider configuration is explicitly approved. Do not export/read existing credential values or copy Hermes credentials. No service restart, systemd change, package install/upgrade, ownership repair, firewall/network mutation, or public/LAN endpoint. Stop for an actual new requirement rather than silently expand authority. Preserve the prior roadmap and accepted BLOCKED record.

### Task 1: Establish the four pilot results

Files: accepted pilot proposal, this plan, docs/evidence/vm105-internal-pilot-readiness.md (readiness agent), and docs/evidence/vm105-internal-pilot.md (parent result/handoff).

- [ ] 1. Verify live service, SSH forward and visible UI with minimal secret-free reads.
- [ ] 2. Select one provider/model; owner completes fresh credential entry/submission privately; verify one harmless response.
- [ ] 3. Create/select a disposable workspace through supported UI, run a small coding task, and check its output with one meaningful runnable check.
- [ ] 4. One focused independent results review, then publish a concise secret-free pilot handoff and exact unresolved limits.

Browser/provider changes are parent-owned; the readiness agent owns only read-only readiness and its evidence file. No TDD scaffolding for native configuration; any nontrivial code created for the demo must have a runnable check. Pilot 00/04 initially; full roadmap remains 09/21.
