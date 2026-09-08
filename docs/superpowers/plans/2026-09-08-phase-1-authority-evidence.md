# Phase 1 Authority and Evidence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make this repository the verified authority for the existing VM105 deployment and close every Phase 1 requirement with secret-free evidence.

**Architecture:** Recreate the historical deployment record as an expressly redacted, provenance-linked repository artifact, then reconcile the already-delivered operating contract and planning state against Git and live read-only evidence. Do not mutate VM105 or any firewall, credential, provider, service, or browser setting.

**Tech Stack:** Markdown, Git, PowerShell validation, read-only SSH evidence.

## Global Constraints

- Repository: `C:\Users\chatc\Projects\sw-localai-deepseek-harnes`; GitHub: `https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git`.
- Target only VM105 `deepseek-harness-01` at the currently verified address `192.168.1.139`.
- Harness stays pinned to `0.1.1-rc.2` and the Web listener stays `127.0.0.1:3080`.
- Keep credentials out of chat, Git, logs, screenshots, and evidence.
- Preserve the VM104 SSH rule unchanged; its origin is proven and its current need is `NOT PROVEN`.
- Record the RX-drop observation as `WARN`: `234093` to `234129` over 45 seconds on 2026-09-08 UTC.
- Preserve dirty work, stage exact paths only, and use command-scoped Git identity.
- Every completion claim requires fresh parent verification.

---

### Task 1: Recreate the expressly redacted VM105 deployment record

**Files:**
- Create: `docs/evidence/vm105-deployment-2026-08-23-redacted.md`

**Interfaces:**
- Consumes: `C:\Users\chatc\Projects\SW-LocalAI\worktrees\deepseek-harness-vm105\DeepSeek-Harness\deployment-2026-08-23.md` at source commit `a3fcfc3f141fe54719598335d28358b6a681ebb7`
- Produces: secret-free historical deployment facts plus a current 2026-09-08 revalidation section used by planning and handoff records

- [ ] **Step 1: Recreate the record with explicit provenance and redaction**

Preserve the safe deployment facts, acceptance matrix, tunnel command, switchable choices, and rollback notes. Add an opening notice that the file contains no credential values or OAuth state and identifies the source path, source commit, and source SHA-256 `127DD18DFD6978E504ED1DE54951533CFF1F15DA23FD5EE4FA7D322C538A89BF`.

- [ ] **Step 2: Add current revalidation evidence**

Record the 2026-09-08 results: Git checkpoint `927ec51ec4c6bdd69f5fd50ecd4a6eb5ec73e7c1`; VM/service/listener/local HTTP/cloud-init PASS; pnpm `11.22.0` version drift WARN; exact two UFW SSH rules; RX drops `+36/45s` WARN; VM104-rule provenance CONFIRMED with current need `NOT PROVEN`; Bell-PC2 tunnel/UI/direct-denial PASS; all provider credentials and routes `NOT PROVEN`.

- [ ] **Step 3: Verify redaction, formatting, and provenance**

Run:

```powershell
$path = 'docs/evidence/vm105-deployment-2026-08-23-redacted.md'
$text = Get-Content -Raw $path
@('Expressly redacted', 'a3fcfc3f141fe54719598335d28358b6a681ebb7', '127DD18DFD6978E504ED1DE54951533CFF1F15DA23FD5EE4FA7D322C538A89BF', '0.1.1-rc.2', '127.0.0.1:3080', '234093', '234129', 'NOT PROVEN') | ForEach-Object {
  if ($text -notmatch [regex]::Escape($_)) { throw "Missing evidence marker: $_" }
}
if ($text -match 'Bearer\s+[A-Za-z0-9._-]{20,}|-----BEGIN .*PRIVATE KEY-----') { throw 'Potential secret material found' }
git diff --check -- $path
```

Expected: exit code 0 with every evidence marker present and no secret-pattern match.

- [ ] **Step 4: Commit only the redacted record**

```powershell
git add -- 'docs/evidence/vm105-deployment-2026-08-23-redacted.md'
git -c user.name='Codex' -c user.email='codex@local' commit -m 'docs: import redacted VM105 deployment evidence'
```

### Task 2: Reconcile governance and close Phase 1 state

**Files:**
- Modify: `docs/superpowers/plans/2026-09-08-project-operating-rules.md`
- Modify: `.planning/PROJECT.md`
- Modify: `.planning/REQUIREMENTS.md`
- Modify: `.planning/ROADMAP.md`
- Modify: `.planning/STATE.md`

**Interfaces:**
- Consumes: commits `abbaff9f`, `0cbd61a`, `927ec51`, planning commit `8ccf3df`, and Task 1's redacted record
- Produces: checked operating-rules evidence and authoritative Phase 1 `05/05`, total `08/21` state

- [ ] **Step 1: Reconcile the operating-rules checklist**

Mark its four implementation steps complete and add an evidence note that names the delivering commits and the fresh validation command/result. Do not rewrite the contract or change the original expected commands.

- [ ] **Step 2: Promote verified Phase 1 requirements**

Mark `BASE-01`, `BASE-02`, `EVID-01`, `PLAN-01`, and `GOV-01` complete in requirements and traceability. Move their project-level statements from Active to Validated with Phase 1 references. Keep every provider requirement pending.

- [ ] **Step 3: Update authoritative progress and next action**

Set Phase 1 to `05/05`, keep Phase 2 `03/03`, and set total to `08/21` in ROADMAP and STATE. Current focus becomes Phase 3. The exact next action is to verify provider endpoint/model prerequisites and prepare owner-only credential/native-OAuth entry without exposing values.

- [ ] **Step 4: Run the complete reconciliation check**

Run:

```powershell
$rules = Get-Content -Raw 'docs/superpowers/plans/2026-09-08-project-operating-rules.md'
if (([regex]::Matches($rules, '(?m)^- \[x\] \*\*Step [1-4]:')).Count -ne 4) { throw 'Operating-rule checklist not reconciled' }
$req = Get-Content -Raw '.planning/REQUIREMENTS.md'
@('BASE-01','BASE-02','EVID-01','PLAN-01','GOV-01') | ForEach-Object {
  if ($req -notmatch "(?m)^- \[x\] \*\*$($_)\*\*:") { throw "Requirement not complete: $_" }
  if ($req -notmatch "(?m)^\| $($_) \| Phase 1 \| Complete \|") { throw "Traceability not complete: $_" }
}
$road = Get-Content -Raw '.planning/ROADMAP.md'
$state = Get-Content -Raw '.planning/STATE.md'
if ($road -notmatch 'Total - 08/21' -or $road -notmatch 'Phase 1 - 05/05') { throw 'Roadmap totals incorrect' }
if ($state -notmatch 'Total - 08/21' -or $state -notmatch 'Phase 1 - 05/05') { throw 'State totals incorrect' }
if ($state -notmatch 'Current Phase:\s*3') { throw 'Current phase is not 3' }
git diff --check -- 'docs/superpowers/plans/2026-09-08-project-operating-rules.md' '.planning/PROJECT.md' '.planning/REQUIREMENTS.md' '.planning/ROADMAP.md' '.planning/STATE.md'
```

Expected: exit code 0; four checked rule steps; five completed Phase 1 requirements; Phase 1 `05/05`; total `08/21`; current phase 3.

- [ ] **Step 5: Commit only the reconciliation files**

```powershell
git add -- 'docs/superpowers/plans/2026-09-08-project-operating-rules.md' '.planning/PROJECT.md' '.planning/REQUIREMENTS.md' '.planning/ROADMAP.md' '.planning/STATE.md'
git -c user.name='Codex' -c user.email='codex@local' commit -m 'docs: reconcile Phase 1 evidence state'
```
