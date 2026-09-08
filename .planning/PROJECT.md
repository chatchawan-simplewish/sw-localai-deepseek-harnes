# DeepSeek Harness

## What This Is

DeepSeek Harness is the owner-operated software-development orchestration environment on Prox-01 VM105 (`deepseek-harness-01`). This repository is the authoritative source for its redacted deployment evidence, operating rules, roadmap, verification state, and continuation handoffs.

## Core Value

Every configured provider route must be secure, explicit, independently attributable, and fail closed before it is trusted for software-development orchestration.

## Requirements

### Validated

- ✓ **BASE-01 (Phase 1)**: Repository path, GitHub remote, branch, local and remote commits, and dirty state are recorded in the tracked [VM105 evidence record](../docs/evidence/vm105-deployment-2026-08-23-redacted.md#repository-source-baseline--captured-2026-09-08-0748-asiabangkok).
- ✓ **BASE-02 (Phase 1)**: VM105 identity, service, loopback listener, local HTTP response, Harness version, cloud-init, and UFW baseline are recorded in the tracked [VM105 evidence record](../docs/evidence/vm105-deployment-2026-08-23-redacted.md#vm105-current-measurements--2026-09-08).
- ✓ **EVID-01 (Phase 1)**: An expressly redacted VM105 deployment record with provenance and no credential values is committed — `10bd057`.
- ✓ **PLAN-01 (Phase 1)**: Authoritative project, requirements, roadmap, state, phase totals, and continuation context are established — `8ccf3df` and this reconciliation.
- ✓ **GOV-01 (Phase 1)**: Operating-rules checklist matches verified Git delivery evidence — `abbaff9f`, `0cbd61a`, and `927ec51`.

### Active

- [ ] Explain the VM104-to-VM105 SSH firewall rule before deciding whether it stays.
- [ ] Determine whether VM105 RX drops are current or historical.
- [x] Re-establish the Bell-PC2 SSH tunnel and verify the Web UI; automatic reconnect is installed and process-exit recovery verified (`docs/evidence/vm105-pilot-auto-reconnect.md`).
- [ ] Configure fresh owner-only credentials and native OAuth without copying Hermes secrets.
- [ ] Add only route-proven, source-specific firewall permissions.
- [ ] Verify each route separately, verify invalid credentials fail closed, and keep routing explicit unless black-box attribution passes.
- [ ] Publish secret-free status evidence and a durable continuation handoff.

### Out of Scope

- Copying credentials or OAuth state from Hermes or another host — credentials must be fresh and VM105-specific.
- LAN/public exposure of TCP 3080, reverse proxying, or a public Harness endpoint — access remains through the Bell-PC2 SSH tunnel.
- Automatic provider selection without black-box provider/model/reasoning attribution — explicit selection is the safe default.
- Deleting firewall rules, VM105, disks, credentials, or predecessor tasks — irreversible changes require an explicit owner decision.
- Unrelated VM, Proxmox, firewall, model, or repository changes — each live-resource lane stays literal and narrow.

## Context

- Repository: `C:\Users\chatc\Projects\sw-localai-deepseek-harnes`
- GitHub: `https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git`
- Verified starting commit: `927ec51ec4c6bdd69f5fd50ecd4a6eb5ec73e7c1`
- VM105: `deepseek-harness-01`, last known address `192.168.1.139`
- Harness: `0.1.1-rc.2`; Web listener must remain `127.0.0.1:3080`
- Historical deployment source: `C:\Users\chatc\Projects\SW-LocalAI\worktrees\deepseek-harness-vm105`
- Provider credentials and inference routes start as `NOT PROVEN` until fresh route-specific tests pass.

## Constraints

- **Security**: Keep credentials out of chat, Git, logs, screenshots, and evidence; owner-only files must be mode `0600` or narrower.
- **Network**: No TCP 3080 LAN rule; provider permissions must name the verified source, destination, port, and rollback.
- **Verification**: Use `PASS`, `WARN`, `BLOCKED`, and `NOT PROVEN`; never promote inherited or indirect evidence to current proof.
- **Routing**: Select provider and model explicitly unless automatic child provider/model/reasoning attribution passes black-box tests.
- **Operations**: Live mutations are sequential and reversible; take secret-free baselines and backups before changes.
- **Browser**: Use only Chrome profile `Codex-Chrome-Bell-PC2`, verified before every project tab.
- **Git**: Preserve dirty work and stage exact paths only.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Five evidence-gated phases | Separates authority, network facts, credentials, route proof, and closeout | — Pending |
| Sequential live-resource changes | Makes firewall and credential rollback attributable | — Pending |
| Parallel work only for disjoint read-only/review lanes | Preserves sole ownership per file or live resource | ✓ Good |
| Explicit routing by default | Automatic attribution is not yet proven | ✓ Good |
| No generic ecosystem research | Existing deployment evidence and the owner's exact route list define the scope | ✓ Good |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition**:
1. Move verified requirements to Validated with their phase reference.
2. Move invalidated requirements to Out of Scope with a reason.
3. Add newly discovered requirements to Active.
4. Record decisions and update current-state context.

**After each milestone**:
1. Recheck the core value and all explicit exclusions.
2. Reconcile roadmap, requirements, evidence, and live state.
3. Record remaining `WARN`, `BLOCKED`, and `NOT PROVEN` items.

---
*Last updated: 2026-09-08 after the internal pilot, automatic SSH reconnect, and owner's full-plan resume. Full roadmap remains 09/21.*
