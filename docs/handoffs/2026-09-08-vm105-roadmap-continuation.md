# DeepSeek Harness VM105 continuation handoff

Generated: 2026-09-08 08:12 Asia/Bangkok
Repository: `C:\Users\chatc\Projects\sw-localai-deepseek-harnes`
GitHub: `https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git`

## Git state

- Isolated worktree: `C:\Users\chatc\Projects\sw-localai-deepseek-harnes\.worktrees\vm105-authoritative-roadmap`
- Branch: `codex/vm105-authoritative-roadmap`
- Base: `927ec51ec4c6bdd69f5fd50ecd4a6eb5ec73e7c1`
- Current reviewed-work head before this handoff: `2ecadabfff92fa5a41135ce0dc3223594bb4ea1d`
- Commits: `8ccf3df` planning initialization; `a74dc9a` Phase 1 plan; `10bd057` redacted evidence; `4f449e1` reconciliation; `f376de3` durable resume-pointer fix; `2ecadab` final-review evidence fixes.
- Do not archive this predecessor task.

## Authoritative progress

- Total - 08/21
  - Phase 1 - 05/05 — authority and evidence accepted after final review, one fix wave, scoped re-review, and fresh parent verification
  - Phase 2 - 03/03 — network/access observations complete
  - Phase 3 - 00/02 — provider prerequisites and credentials
  - Phase 4 - 00/09 — route, fail-closed, and attribution tests
  - Phase 5 - 00/02 — final evidence and handoff

## Verified live state

- VM105 `deepseek-harness-01` is reachable at `192.168.1.139`.
- `deepseek-harness.service`: enabled, active, `Result=success`, `NRestarts=0`.
- Harness `0.1.1-rc.2`; listener exactly `127.0.0.1:3080`; VM-local HTTP 200.
- Node `v24.19.0`, Corepack `0.35.0`; pnpm drifted to `11.22.0` from recorded `11.7.0` (`WARN`).
- UFW permits SSH from Bell-PC2 `192.168.1.161` and VM104 `192.168.1.141` only.
- VM104 rule origin is confirmed: added 2026-08-24 for `hermes-admin`; current need is `NOT PROVEN`; rule is unchanged and removal is not authorized.
- RX dropped increased `234093` to `234129` in 45 seconds (`WARN`, current increase).
- Bell-PC2 SSH tunnel is running as local PID `42076`; local HTTP 200 and visible Harness UI were verified; direct LAN TCP 3080 was denied.
- Browser profile was exactly `Codex-Chrome-Bell-PC2`; handoff tab `435371600` shows the Harness onboarding page.

## Evidence

- `.planning/PROJECT.md`
- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `.planning/STATE.md`
- `docs/evidence/vm105-deployment-2026-08-23-redacted.md`
- `docs/superpowers/plans/2026-09-08-phase-1-authority-evidence.md`
- SDD ledger: `.superpowers/sdd/2026-09-08-phase-1-authority-evidence/progress.md` (ignored scratch; do not use as a durable resume pointer)

## Open gates

- All provider credentials, native OAuth sessions, inference routes, invalid-credential tests, and automatic child attribution are `NOT PROVEN`.
- Provider credential/API-key creation and native OAuth require action-time confirmation immediately before persistent access is created; authentication dialogs require owner takeover.
- No provider endpoint or model ID may be assumed from older Hermes state.
- No new firewall rule may be added until its exact route source, destination, protocol, port, and rollback are verified.

## Exact next actions

1. Inspect the Harness onboarding/settings UI without entering credentials; record supported provider configuration surfaces.
2. Verify current official endpoint/model IDs and reachability for OpenRouter, VM1201, Bell-PC2 worker, Typhoon text/OCR, and native Codex OAuth.
3. Prepare backups, least-privilege firewall changes, and credential-entry steps; stop at the single action-time confirmation gate before creating persistent keys/OAuth access or typing secrets.
4. Test routes separately and preserve explicit routing unless provider/model/reasoning attribution passes black-box tests.

## Safety boundaries

Keep secrets out of chat, Git, logs, screenshots, and evidence. Do not copy Hermes credentials/OAuth. Do not expose TCP 3080 to LAN/public networks. Do not delete the VM104 rule, VM105, disks, credentials, or predecessor tasks. Preserve exact-path Git scope and use command-scoped identity.
