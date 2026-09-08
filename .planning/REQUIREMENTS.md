# Requirements: DeepSeek Harness

**Defined:** 2026-09-08  
**Core Value:** Every configured provider route must be secure, explicit, independently attributable, and fail closed before it is trusted.

## v1 Requirements

### Authority and evidence

- [x] **BASE-01**: The owner can verify the repository path, GitHub remote, branch, local commit, remote commit, and dirty state from recorded evidence.
- [x] **BASE-02**: The owner can verify VM105 identity, address, Harness version, service state, listener scope, and local HTTP response from current evidence.
- [x] **EVID-01**: The repository contains an expressly redacted VM105 deployment record with provenance and no credential values.
- [x] **PLAN-01**: The repository contains authoritative project, configuration, requirements, roadmap, state, numbered phase totals, and continuation records.
- [x] **GOV-01**: The operating-rules implementation checklist reflects verified Git evidence rather than stale unchecked steps.

### Network and access

- [ ] **NET-01**: The origin, exact scope, and current need of the VM104-to-VM105 SSH firewall permission are established before any change is proposed.
- [ ] **NET-02**: Multiple timestamped VM105 RX-drop samples establish whether the counter is increasing during observation or only historical.
- [ ] **UI-01**: Bell-PC2 can open the Harness Web UI through an owner-controlled SSH local forward while direct LAN TCP 3080 remains denied.
- [ ] **FW-01**: Every added firewall permission is limited to the verified source, destination, protocol, and port required by one proven provider route, with rollback recorded.

### Provider configuration

- [ ] **CRED-01**: VM105 stores only fresh owner-only provider credentials or native OAuth state; no Hermes credential or OAuth material is copied.
- [ ] **PROV-01**: OpenRouter Auto is configured and independently verified with a harmless attributed prompt.
- [ ] **PROV-02**: OpenRouter Pareto Code is configured and independently verified with a harmless attributed prompt.
- [ ] **PROV-03**: The VM1201 local Qwen worker is configured and independently verified with a harmless attributed prompt.
- [ ] **PROV-04**: The Bell-PC2 local model worker is configured and independently verified with a harmless attributed prompt.
- [ ] **PROV-05**: Typhoon Thai text is configured and independently verified with a harmless attributed prompt.
- [ ] **PROV-06**: Typhoon OCR is configured and independently verified with a harmless attributed input.
- [ ] **PROV-07**: Codex Luna, Terra, and Sol are configured through native OAuth and each is independently verified with a harmless attributed prompt.

### Failure and attribution

- [ ] **FAIL-01**: A deliberately invalid credential for each applicable provider fails closed without silently selecting another route.
- [ ] **ATTR-01**: Automatic child routing remains disabled unless black-box tests attribute provider, model, and reasoning for every child; otherwise explicit routing is documented as required.
- [ ] **SAFE-01**: Secret-free evidence classifies each requirement as `PASS`, `WARN`, `BLOCKED`, or `NOT PROVEN` without overstating indirect proof.
- [ ] **HAND-01**: A durable handoff records current Git/live state, evidence paths, open risks, exact next actions, and leaves predecessor tasks unarchived.

## v2 Requirements

- **AUTO-01**: Automatic provider selection may be enabled after stable child-level provider/model/reasoning attribution is demonstrated across repeated black-box tests.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Public or LAN Harness Web exposure | SSH tunneling already supplies narrow access; broader exposure adds avoidable risk. |
| Credential reuse from Hermes | Violates isolation and cannot prove VM105-specific ownership or revocation. |
| Automatic deletion of firewall rules or VM resources | Irreversible changes require an explicit owner decision. |
| Unrelated host or VM configuration | This milestone is limited to DeepSeek Harness VM105 and verified provider paths. |

## Traceability

Every v1 requirement maps to exactly one authoritative roadmap phase.

| Requirement | Phase | Completion Status |
|-------------|-------|-------------------------|
| BASE-01 | Phase 1 | Complete |
| BASE-02 | Phase 1 | Complete |
| EVID-01 | Phase 1 | Complete |
| PLAN-01 | Phase 1 | Complete |
| GOV-01 | Phase 1 | Complete |
| NET-01 | Phase 2 | NOT PROVEN |
| NET-02 | Phase 2 | WARN |
| UI-01 | Phase 2 | PASS |
| CRED-01 | Phase 3 | NOT PROVEN |
| FW-01 | Phase 3 | NOT PROVEN |
| PROV-01 | Phase 4 | NOT PROVEN |
| PROV-02 | Phase 4 | NOT PROVEN |
| PROV-03 | Phase 4 | NOT PROVEN |
| PROV-04 | Phase 4 | NOT PROVEN |
| PROV-05 | Phase 4 | NOT PROVEN |
| PROV-06 | Phase 4 | NOT PROVEN |
| PROV-07 | Phase 4 | NOT PROVEN |
| FAIL-01 | Phase 4 | NOT PROVEN |
| ATTR-01 | Phase 4 | NOT PROVEN |
| SAFE-01 | Phase 5 | NOT PROVEN |
| HAND-01 | Phase 5 | NOT PROVEN |

**Coverage:**
- v1 requirements: 21 total
- Mapped to phases: 21
- Unmapped: 0
- Duplicated mappings: 0
- Evidence tasks complete: 8/21 (`PASS`: 6, `WARN`: 1, completed with `NOT PROVEN` outcome: 1)
- Evidence tasks remaining: 13/21 (`NOT PROVEN`: 13, `BLOCKED`: 0)

---
*Requirements defined: 2026-09-08*
*Last updated: 2026-09-08 after Phase 1 authority-and-evidence reconciliation*
