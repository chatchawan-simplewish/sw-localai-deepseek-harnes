# Roadmap: DeepSeek Harness

## Overview

This milestone turns the existing loopback-only VM105 deployment into a fully evidenced software-development orchestration environment. Work advances through five evidence gates: establish authority, establish network facts, prepare provider prerequisites, prove every route and failure path, then close the evidence loop. Live changes remain sequential and reversible; provider and model selection remains explicit unless black-box attribution proves otherwise.

Evidence states are `PASS`, `WARN`, `BLOCKED`, and `NOT PROVEN`. A checked evidence task means the requirement-sized verification task ran to a recorded conclusion; it does not turn a `WARN` into a `PASS`.

## Phases

- [x] **Phase 1: Authority and Evidence** - Establish current repository, VM105, deployment-record, planning, and governance authority.
- [x] **Phase 2: Network Facts and Owner Access** - Explain the SSH rule, characterize RX drops, and prove tunnel-only Web UI access.
- [ ] **Phase 3: Provider Prerequisites** - Establish fresh owner-only credentials and only the route-specific firewall permissions actually required.
- [ ] **Phase 4: Route Truth and Fail-Closed Attribution** - Prove every requested provider route separately, including failure isolation and routing attribution.
- [ ] **Phase 5: Evidence Closeout and Handoff** - Classify every requirement without overstatement and leave a durable continuation record.

## Evidence Progress Tree

- **Total - 09/21**
  - **Phase 1 - 05/05**
  - **Phase 2 - 03/03**
  - **Phase 3 - 01/02**
  - **Phase 4 - 00/09**
  - **Phase 5 - 00/02**

## Phase Details

### Phase 1: Authority and Evidence
**Goal**: The owner can rely on current, secret-free repository and VM105 evidence as the authoritative basis for all later changes.
**Depends on**: Nothing (first phase)
**Requirements**: BASE-01, BASE-02, EVID-01, PLAN-01, GOV-01
**Success Criteria** (what must be TRUE):
  1. The owner can inspect recorded repository path, GitHub remote, branch, local commit, remote commit, and dirty state from a current revalidation.
  2. The owner can inspect current VM105 identity, address, Harness version, service state, loopback listener, local HTTP response, cloud-init result, and UFW baseline.
  3. The repository contains an expressly redacted deployment record whose provenance is clear and whose secret scan exposes no credential values.
  4. The project files and operating-rule checklist agree with verified Git evidence and expose authoritative phase totals, current state, and continuation context.
**Plans**: TBD

Evidence tasks:
- [x] **BASE-01 — PASS**: Repository and GitHub identity were freshly revalidated.
- [x] **BASE-02 — PASS**: VM105 identity, service, listener, local HTTP, version, cloud-init, and UFW baseline were freshly revalidated.
- [x] **EVID-01 — PASS**: The expressly redacted VM105 deployment record with provenance and secret scan is committed in this repository (`10bd057`).
- [x] **PLAN-01 — PASS**: Authoritative project, requirements, roadmap, state, phase totals, and continuation context are reconciled with the Phase 1 evidence record.
- [x] **GOV-01 — PASS**: Operating-rule checkboxes are reconciled with verified delivery commits `abbaff9f`, `0cbd61a`, and `927ec51`.

### Phase 2: Network Facts and Owner Access
**Goal**: The owner understands the observed network state and can use the Harness UI only through the intended SSH tunnel.
**Depends on**: Phase 1
**Requirements**: NET-01, NET-02, UI-01
**Success Criteria** (what must be TRUE):
  1. The VM104-to-VM105 SSH permission has a recorded origin, exact source/destination/protocol/port scope, and evidence-based keep/change recommendation before any mutation.
  2. Multiple timestamped samples show whether VM105 RX drops are increasing; an increase remains visibly classified `WARN` until its cause and impact are resolved.
  3. Bell-PC2 can load the Harness Web UI through an owner-controlled SSH local forward while a direct LAN connection to TCP 3080 is denied.
**Plans**: TBD
**UI hint**: yes

Evidence tasks:
- [x] **NET-01 — NOT PROVEN**: `dsh` added the VM104-to-VM105 SSH rule through `sudo` at 2026-08-24T15:00:31Z for Hermes administrative access, followed by three `hermes-admin` logins that day. No active session or reference appeared in today's scanned VM104 automation, so current need is not proven; the unchanged rule has no deletion authorization.
- [x] **NET-02 — WARN**: Timestamped observation found 36 additional RX drops in 45 seconds, proving the counter is currently increasing.
- [x] **UI-01 — PASS**: The verified `Codex-Chrome-Bell-PC2` profile visibly loaded the Harness onboarding page through Bell-PC2 SSH forward PID 42076; loopback HTTP returned 200 with Harness identity while direct `192.168.1.139:3080` remained unreachable.

### Phase 3: Provider Prerequisites
**Goal**: VM105 has isolated, owner-controlled provider prerequisites without inherited secrets or overbroad network access.
**Depends on**: Phase 2
**Requirements**: CRED-01, FW-01
**Success Criteria** (what must be TRUE):
  1. VM105 contains only fresh VM105-specific provider credentials or native OAuth state, stored owner-only, with no Hermes material copied or exposed in evidence.
  2. Before each live change, the owner can identify a secret-free baseline, backup or rollback path, and the single provider route the change enables.
  3. Every added firewall permission records the verified source, destination, protocol, port, and rollback, with no generic provider or TCP 3080 LAN allowance.
**Plans**: 2 plans

Plans:
- [x] 03-01-PLAN.md — Completed with `BLOCKED / NOT PROVEN` outcome after read-only verification and zero firewall mutations (wave 1).
- [ ] 03-02-PLAN.md — Task 1 independently accepted after one fix round with the protected backup destination still empty; Task 2 did not start and no credential/OAuth gate was presented because the effective store, native Codex login surface, provider identities, and six route blockers remain unresolved (wave 2).

Evidence tasks:
- [ ] **CRED-01 — NOT PROVEN**: All fresh provider credentials and native OAuth state remain unconfigured or unverified.
- [x] **FW-01 — BLOCKED**: The evidence task completed with three verified no-change routes, six blocked routes, and zero firewall additions; the blocked outcome does not make Phase 3 `PASS`.

### Phase 4: Route Truth and Fail-Closed Attribution
**Goal**: Every requested provider path is independently attributable, fails closed, and is trusted only to the level directly proven.
**Depends on**: Phase 3
**Requirements**: PROV-01, PROV-02, PROV-03, PROV-04, PROV-05, PROV-06, PROV-07, FAIL-01, ATTR-01
**Success Criteria** (what must be TRUE):
  1. OpenRouter Auto and OpenRouter Pareto Code each return a harmless nonce-bearing response that is correlated to the explicitly selected route and model.
  2. The VM1201 Qwen worker and Bell-PC2 local model worker each return an independently attributable harmless response over their own proven network path.
  3. Typhoon Thai text and Typhoon OCR each handle their route-appropriate harmless input with source-specific attribution.
  4. Codex Luna, Terra, and Sol each complete an independently attributable harmless prompt through native OAuth.
  5. An invalid credential for every applicable provider produces an error without fallback, and automatic child routing stays disabled unless provider, model, and reasoning are unambiguously attributed in black-box tests.
**Plans**: TBD

Evidence tasks:
- [ ] **PROV-01 — NOT PROVEN**: OpenRouter Auto route.
- [ ] **PROV-02 — NOT PROVEN**: OpenRouter Pareto Code route.
- [ ] **PROV-03 — NOT PROVEN**: VM1201 local Qwen route.
- [ ] **PROV-04 — NOT PROVEN**: Bell-PC2 local model route.
- [ ] **PROV-05 — NOT PROVEN**: Typhoon Thai text route.
- [ ] **PROV-06 — NOT PROVEN**: Typhoon OCR route.
- [ ] **PROV-07 — NOT PROVEN**: Codex Luna, Terra, and Sol native OAuth routes.
- [ ] **FAIL-01 — NOT PROVEN**: Invalid-credential fail-closed behavior for every applicable provider.
- [ ] **ATTR-01 — NOT PROVEN**: Automatic child provider/model/reasoning attribution; explicit routing remains required.

### Phase 5: Evidence Closeout and Handoff
**Goal**: The owner has a secret-free final verdict for every v1 requirement and can resume safely from one durable handoff.
**Depends on**: Phase 4
**Requirements**: SAFE-01, HAND-01
**Success Criteria** (what must be TRUE):
  1. Every v1 requirement has exactly one evidence-backed `PASS`, `WARN`, `BLOCKED`, or `NOT PROVEN` verdict with no inherited or indirect evidence promoted to current proof.
  2. The numbered phase tree, roadmap, requirements traceability, and project state agree on completed and total counts.
  3. A durable handoff records current Git and live state, evidence paths, open risks, rollback information, and exact next actions while predecessor tasks remain unarchived.
**Plans**: TBD

Evidence tasks:
- [ ] **SAFE-01 — NOT PROVEN**: Final secret-free requirement classification and count reconciliation are pending.
- [ ] **HAND-01 — NOT PROVEN**: Final durable continuation handoff is pending.

## Requirement Coverage

| Phase | Requirement Count | Requirement IDs |
|-------|-------------------|-----------------|
| 1. Authority and Evidence | 5 | BASE-01, BASE-02, EVID-01, PLAN-01, GOV-01 |
| 2. Network Facts and Owner Access | 3 | NET-01, NET-02, UI-01 |
| 3. Provider Prerequisites | 2 | CRED-01, FW-01 |
| 4. Route Truth and Fail-Closed Attribution | 9 | PROV-01, PROV-02, PROV-03, PROV-04, PROV-05, PROV-06, PROV-07, FAIL-01, ATTR-01 |
| 5. Evidence Closeout and Handoff | 2 | SAFE-01, HAND-01 |
| **Total** | **21** | **21/21 mapped once; 0 unmapped; 0 duplicated** |

## Progress

**Execution Order:** Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5. Evidence captured before roadmap creation remains credited but does not waive phase dependencies.

| Phase | Evidence Tasks Complete | Plans Complete | Status | Completed |
|-------|-------------------------|----------------|--------|-----------|
| 1. Authority and Evidence | 05/05 | TBD | Complete | 2026-09-08 |
| 2. Network Facts and Owner Access | 03/03 | TBD | Complete (pre-roadmap evidence) | 2026-09-08 |
| 3. Provider Prerequisites | 01/02 | 1/2 | Blocked; 03-01 complete with FW-01 `BLOCKED`, 03-02 Task 1 accepted but CRED-01 `BLOCKED / NOT PROVEN` and Task 2 not started | - |
| 4. Route Truth and Fail-Closed Attribution | 00/09 | TBD | Not started | - |
| 5. Evidence Closeout and Handoff | 00/02 | TBD | Not started | - |
