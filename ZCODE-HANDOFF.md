# sw-localai-deepseek-harnes — ZCode Handoff (2026-09-30)

Written 2026-09-30 ~15:30 Bangkok by a read-only Claude Code audit. No secret values appear in this file.

## 1. What this project is

- It is the ops and docs repository for **DeepSeek Harness (DSH)**, a web-based agent harness (`@deepseek-ai/dsh-*`, Cordis profile) deployed on **VM105** (192.168.1.139, user `dsh`). The model backends route through OmniRoute. The repo holds:
  - operating rules
  - design specs and plans
  - ops assets: a loopback-only **infrastructure-admin MCP broker** that gives DSH root administration of prox-01/03/04, a DSH systemd drop-in, an nginx loopback proxy, a web profile patch and a team skill
- **Stack:** Node 24 (`/opt/node-v24.19.0-linux-x64` on VM105), MCP SDK 1.30.0, systemd, nginx, OpenSSH. Docs use the superpowers SDD workflow.
- Key directories:
  - `AGENTS.md`: rules
  - `docs/superpowers/{specs,plans}/`
  - `ops/dsh/infra-admin/` (`server.mjs`, unit, `README.md` runbook, `DSH-HANDOFF.md`)
  - `ops/dsh/systemd/`, `ops/dsh/profiles/web/cordis.patch.yml`, `ops/dsh/skills/team-shared/`, `ops/nginx/deepseek-harness.conf`
  - `.superpowers/sdd/2026-09-14-dsh-infra-admin-mcp/`: task briefs, reports and reviews
  - `.worktrees/vm105-authoritative-roadmap`: the long-running VM105 provider/roadmap evidence branch

## 2. Current state snapshot

- **Branch** `main`, **ahead of `origin/main` by 3**. These are unpushed docs commits from 2026-09-15: `f75e842`, `1919792`, `a834e6c` (per-chat effort selector design and verified Qwen effort levels).
- **Dirty:**
  - `M AGENTS.md`: 3 added rule lines about the 30-min overview, exhausting checks before manual asks, and checking open Chrome windows for the profile
  - `?? docs/superpowers/plans/2026-09-14-dsh-infra-admin-mcp.md`
  - `?? ops/`: the whole infra-admin, nginx, systemd and profile asset tree
  - The SDD ledger says "no commit by dirty-worktree policy", so the deployed MCP broker's source is **not committed**.
- **Remote:** `origin` = https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git. `gh` is logged in as `chatchawan-simplewish`.
- **Branches and worktrees:**
  - `codex/vm105-authoritative-roadmap` in `.worktrees/vm105-authoritative-roadmap`: 161 commits not on main, last commit `b7bfec9` on 2026-09-15. Dirty: `M .gitattributes`, untracked R13 contract, script, test and `__pycache__`.
  - `codex/vm105-provider-prerequisites` in `C:\Users\chatc\.codex\worktrees\e6f7\...`: 8 commits, last 2026-09-08. Untracked `.planning/phases/`.
  - A detached worktree at `C:\Users\chatc\.codex\worktrees\42e9\...` at `41b8fe7`, "wip: pause VM105 scoped path recovery" (2026-09-08).
- **Stashes:** none.
- **Deployed:**
  - The infra-admin broker was deployed on VM105 and accepted on 2026-09-14: service `deepseek-harness-infra-admin` on 127.0.0.1:8182, and `deepseek-harness` restarted with the MCP entry (task-3 report PASS).
  - The effort-selector config was applied on VM105 `/home/dsh/.dsh/settings.yaml`, with backups `*.bak-*-qwen-effort-levels`.
- **VM105 is currently stopped by the user's choice**, per SW-LocalAI `.planning/HANDOFF.json` and the ZCode project handoff, 2026-09-30.
- **Last activity:** 2026-09-15 (commits and Codex sessions). No AI session has touched it since.

## 3. Unfinished tasks (prioritized)

| # | Task | Status | Next concrete step | Pointers |
|---|---|---|---|---|
| 1 | Commit the deployed infra-admin MCP assets and the plan (currently untracked) | NOT STARTED. The work is DONE and deployed but uncommitted | Review `ops/` for secrets (none expected). Then stage the exact paths `ops/` and `docs/superpowers/plans/2026-09-14-dsh-infra-admin-mcp.md` and commit with a command-scoped identity. Ask the user before pushing | `.superpowers/sdd/2026-09-14-dsh-infra-admin-mcp/progress.md` |
| 2 | Commit or decide on the `AGENTS.md` rule edits (3 lines) | NOT STARTED | Commit together with, or separately from, task 1 | `git diff AGENTS.md` |
| 3 | Push the 3 ahead commits on `main` | NOT STARTED | `git push origin main` once the user approves | `git log origin/main..main` |
| 4 | VM105 provider roadmap: Phase 3 "Provider Prerequisites" (09/21 evidence tasks overall) | **BLOCKED** | R10 is spent. R11 says no source-only path exists. An R13 read-only policy-shape diagnostic contract was drafted (untracked) and needs two independent PASS reviews plus an action-time binding before any contact with VM105. Other blockers are owner decisions: fresh interactive credentials, the inherited-listener supervisor architecture, and the PROV-04 scope conflict | `.worktrees/vm105-authoritative-roadmap/.planning/STATE.md`, `.planning/HANDOFF.json`, `docs/handoffs/2026-09-15-vm105-r11-source-only-terminal-boundary.md`, `docs/contracts/vm105-r13-policy-shape-diagnostic-contract-20260915.md` |
| 5 | The effort-selector spec's final UI check (Qwen levels visible in the DSH UI) | Unknown. The commits say "verified" | Re-verify after VM105 is started again | `docs/superpowers/specs/2026-09-15-per-chat-effort-selector-design.md` |
| 6 | The old `codex/vm105-provider-prerequisites` branch and the detached WIP worktree | Stale since 2026-09-08 | Leave them. Do not delete without asking | `C:\Users\chatc\.codex\worktrees\{e6f7,42e9}` |
| 7 | Revocation and rotation runbook for broker keys and token | Documented, not needed now | Use only if access must be revoked | `ops/dsh/infra-admin/README.md` |

## 4. How to run / test / deploy

There is no build or test suite on `main`. The roadmap worktree has Python tests under `scripts/tests/` (for example `test_vm105_r13_policy_shape_diagnostic.py`). Run them with `py -m pytest scripts/tests` from that worktree. That exact command is not recorded, so treat it as a suggestion.

Status-only checks on VM105 (from `ops/dsh/infra-admin/README.md`):
```sh
systemctl is-active deepseek-harness deepseek-harness-infra-admin
curl --silent --show-error --output /dev/null --write-out '%{http_code}\n' http://127.0.0.1:8182/mcp   # expect 401
ssh -F /etc/dsh-infra-admin/ssh_config -o BatchMode=yes prox-01 hostname   # also prox-03, prox-04
```
Deploying the broker means copying `server.mjs` to `/opt/dsh-infra-admin/` and the unit to systemd, symlinking the SDK and zod (no `npm install`), then `systemctl daemon-reload` and a restart (see Task 3 in the plan). You reach the DSH web UI from Bell-PC2 through the SSH tunnel at `http://127.0.0.1:3080`. The tunnel is set up by `C:\Users\chatc\Projects\DeepSeekHarnessRuntime\Start-VM105PilotTunnel.ps1`. On VM105, nginx listens on 127.0.0.1:8181 and proxies to 3080.

## 5. Infrastructure and hosts

| Host | Address | Notes |
|---|---|---|
| VM105 DSH | 192.168.1.139, user `dsh` (and root via sudo) | Currently stopped. Services `deepseek-harness`, `deepseek-harness-infra-admin`. Web on 127.0.0.1:3080 and nginx on 127.0.0.1:8181 |
| prox-01 / prox-03 / prox-04 | 192.168.1.201 / .203 / .204 | Broker aliases (root) |
| OmniRoute | 192.168.1.68:20128 | Model gateway (`omniroute-vm1205` profile in DSH settings) |
| Bell-PC2 | 192.168.1.161 | Runs the tunnel scheduled task "DeepSeek Harness VM105 SSH Tunnel" |

No SSH alias for VM105 exists in `C:\Users\chatc\.ssh\config`. The tunnel script uses `-i codex-prox01-vms-ed25519 dsh@192.168.1.139` directly.

## 6. Credentials and secrets (locations only)

| What | Where | Env var | Used by |
|---|---|---|---|
| SSH key to VM105 (`dsh@`) | `C:\Users\chatc\.ssh\codex-prox01-vms-ed25519` | — | tunnel script, admin work |
| Proxmox root key (operator) | `C:\Users\chatc\.ssh\id_ed25519_pvediag` | — | initial public-key install only |
| Broker SSH identities | `/etc/dsh-infra-admin/keys/prox-0{1,3,4}_ed25519` on VM105 (root) | — | broker to Proxmox |
| Broker SSH config | `/etc/dsh-infra-admin/ssh_config` on VM105 | — | broker |
| Broker bearer token | `/etc/dsh-infra-admin/broker.env` on VM105 (root 0600) | `MCP_INFRA_ADMIN_TOKEN` | broker |
| DSH MCP client env | `/etc/deepseek-harness/mcp.env` on VM105 (root 0600) | `MCP_INFRA_ADMIN_TOKEN` (and possibly others: unknown) | `deepseek-harness` service drop-in |
| DSH settings (model profiles, provider keys) | `/home/dsh/.dsh/settings.yaml` on VM105 | unknown | DSH |
| OmniRoute key used by DSH | unknown (inside the VM105 DSH settings or env) | unknown | DSH to OmniRoute |
| GitHub | `gh` keyring, account `chatchawan-simplewish` | — | push |

## 7. Things outside this folder that ZCode needs

- `C:\Users\chatc\.ssh\` (key and `known_hosts` with VM105's host key, since the tunnel uses `StrictHostKeyChecking=yes`).
- `C:\Users\chatc\Projects\DeepSeekHarnessRuntime` (tunnel script and its scheduled task).
- `C:\Users\chatc\Projects\SW-LocalAI` (the VM105 on/off state, prox-01 constraints and infra memory). `SW-LocalAI\worktrees\deepseek-harness-vm105` is a worktree of the SW-Selfhosted-Network repo with the VM105 deployment record (`DeepSeek-Harness/deployment-2026-08-23.md`).
- `C:\Users\chatc\Projects\SW-OmniRoute` (the gateway the models route through).
- Codex worktrees under `C:\Users\chatc\.codex\worktrees\{e6f7,42e9}\sw-localai-deepseek-harnes`, and Codex sessions from 2026-09-08 to 09-15 in `C:\Users\chatc\.codex\sessions\2026\09\`.
- `gh` CLI auth. The Chrome profile is `Codex-Chrome-Bell-PC2` only.

## 8. Gotchas and rules (from AGENTS.md)

- Every message starts with an Asia/Bangkok `YYYYMMDD HHMMSS` timestamp. Use evidence-derived `Phase N - xx/yy` trees and a 30-min overview during active work.
- Decisions use exactly: Overview / What I need from you / Choices / Recommended choice / Exact reply.
- Routine choices are pre-approved. Ask once only for supercritical items, a big architecture or scope change, higher cost, irreversible deletion, public exposure, or production identity/data mutation.
- **Git:** preserve dirty work. Stage exact paths only. Never broad cleanup or reset. Use a command-scoped identity for commits. Never archive old tasks.
- Use a sub-agent workflow with one owner per file or live lane, and verify as the parent. At 85% context, write a durable handoff and one continuation.
- The roadmap branch uses the verdicts PASS / WARN / BLOCKED / NOT PROVEN only. Spent attempts (R4-R10) must not be retried or replayed.
- The broker is full Proxmox root. Treat its output as sensitive. Never read or print keys or tokens.

## 9. Suggested first prompt for ZCode

```text
Read C:\Users\chatc\Projects\sw-localai-deepseek-harnes\ZCODE-HANDOFF.md and AGENTS.md (follow its timestamp/decision/git rules). Read-only first: git status, git log origin/main..main, and review the untracked ops/ tree for any secret values. Then propose (decision format) committing ops/ + docs/superpowers/plans/2026-09-14-dsh-infra-admin-mcp.md + the AGENTS.md edits with exact-path staging, and pushing the 3 ahead commits. Do not contact VM105 (it is stopped) and do not act on the blocked VM105 roadmap branch without my decision.
```
