# Project Operating Rules Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create one authoritative root `AGENTS.md` containing the owner's complete project operating contract without duplicated or conflicting rules.

**Architecture:** Keep policy in a single root file inherited by the whole repository. Encode reporting, autonomy, browser, credential, MCP, context rollover, Git, and sub-agent behavior as testable rules, with explicit non-overridable safety boundaries.

**Tech Stack:** Markdown, Git, PowerShell validation.

## Global Constraints

- Every user-facing message starts with an Asia/Bangkok `YYYYMMDD HHMMSS` timestamp.
- Routine recommendations are pre-approved and should proceed unattended.
- Ask once per topic only for supercritical, irreversible, materially divergent, or materially more expensive actions.
- Use only Chrome profile `Codex-Chrome-Bell-PC2` for project browser work.
- Keep credentials out of chat, Git, logs, screenshots, and evidence.
- At or before 85% context, write a durable handoff, create a continuation task, and leave the predecessor unarchived.
- Use sub-agent-driven delivery for meaningful implementation and review work.
- Preserve system/platform safety requirements that project rules cannot override.

---

### Task 1: Create and validate the project contract

**Files:**
- Create: `AGENTS.md`

**Interfaces:**
- Consumes: `docs/superpowers/specs/2026-09-08-project-operating-rules-design.md`
- Produces: repository-wide instructions inherited by future agents

- [x] **Step 1: Create `AGENTS.md`**

Add these sections: project identity; rule precedence; timestamped
communication; tree-style progress; decision/question separation; completion
summary; unattended authority; mandatory-input minimization; Chrome profile;
API tokens and MCPs; sub-agent workflow; context rollover; Git/session safety;
and a completeness checklist.

- [x] **Step 2: Validate coverage and contradictions**

Run a PowerShell assertion that checks for the exact required concepts:

```powershell
$text = Get-Content -Raw AGENTS.md
@(
  'YYYYMMDD HHMMSS', 'Phase 1 - 05/20', 'Overview', 'What I need from you',
  'Choices', 'Recommended choice', 'Exact reply', 'Codex-Chrome-Bell-PC2',
  'API token', 'MCP', '85%', 'unarchived', 'sub-agent', 'supercritical'
) | ForEach-Object {
  if ($text -notmatch [regex]::Escape($_)) { throw "Missing rule: $_" }
}
if ((Select-String -Path AGENTS.md -Pattern 'pre-approve all future recommendations').Count -gt 1) {
  throw 'Duplicate pre-approval rule'
}
```

Expected: exit code 0 with no missing or duplicated rule.

- [x] **Step 3: Verify formatting and secret safety**

```powershell
git diff --check -- AGENTS.md
$placeholderPattern = @('T' + 'BD', 'T' + 'ODO', 'FIX' + 'ME') -join '|'
if (rg -n $placeholderPattern AGENTS.md) { throw 'Placeholder found' }
if (rg -n 'sk-[A-Za-z0-9_-]{20,}|Bearer\s+[A-Za-z0-9._-]{20,}' AGENTS.md) { throw 'Potential secret found' }
```

Expected: `git diff --check` succeeds and `rg` returns no matches.

- [x] **Step 4: Commit only the contract**

```powershell
git add -- AGENTS.md
git -c user.name='Codex' -c user.email='codex@local' commit -m 'docs: add project operating rules'
```

Expected: the commit contains only `AGENTS.md`.

### Reconciliation Evidence

- Delivery commits: `abbaff9f` (initial contract), `0cbd61a` (repository URL verification), and `927ec51` (rule examples).
- Fresh validation: the complete reconciliation check in tracked `docs/superpowers/plans/2026-09-08-phase-1-authority-evidence.md` exited `0` on 2026-09-08, confirming four checked steps and clean whitespace.
