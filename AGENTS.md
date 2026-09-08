# DeepSeek Harness project operating rules

## Project identity

- Project: DeepSeek Harness, a local-AI harness for this repository.
- Repository: `C:\Users\chatc\Projects\sw-localai-deepseek-harnes`.
- Repository URL: https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git

## Rule precedence

Owner preferences override optional skill friction, but never override system or platform policy, missing authority, destructive-action safety, secret handling, or external interactive authentication. These project rules are subordinate to those requirements.

## Communication and progress

- Every user-facing message starts with an Asia/Bangkok `YYYYMMDD HHMMSS` timestamp.
- Number progress as an evidence-derived tree with zero-padded completed/total counts; never invent totals. Literal example: `Phase 1 - 05/20`.
- Keep decisions and questions separate from ordinary progress under exactly these headings: `Overview`, `What I need from you`, `Choices`, `Recommended choice`, and `Exact reply`. Include pros, cons, costs, risks, and trade-offs when a decision is presented.
- Completion summaries cover important changes, verification, remaining work or limits, impact, and switchable choices.

## Authority and safety

- The owner pre-approves all future recommended routine choices. Proceed automatically, record the choice afterward, and ask once per topic only for supercritical actions, materially different architecture or scope, materially higher cost, irreversible deletion, broad public exposure, or production data/identity mutation.
- Minimize mandatory input: check, recheck, and verify automatically first. Ask only for owner-only input, interactive authentication, a secret that is not safely available, or a non-overridable gate; explain the need in one concise request.
- Keep credentials out of chat, Git, logs, screenshots, and evidence.
- Project-scoped token creation and required MCP installation, connection, and use are pre-approved. Use least privilege, owner-only storage, minimal lifetime and scope; never expose secrets; record safe metadata and revocation steps; do not create speculative integrations.

## Browser

- Use only Chrome profile `Codex-Chrome-Bell-PC2` for project browser work.
- Verify the exact profile before every project link or new tab. Never fall back to another Chrome profile, Edge, Firefox, the OS-default browser, or an in-app browser.

## Sub-agents and context rollover

- Use fresh bounded sub-agents for meaningful implementation and independent review. Assign one owner per file or live-resource lane; agents do not revert others. The parent verifies before acceptance. Trivial one-command checks may remain inline.
- At or before 85% context, stop at a safe point, write a durable handoff with state, evidence, and next action, create a continuation task from it, verify transfer, leave the old task unarchived and read-only, and continue.

## Git and session safety

- Preserve dirty work. Stage exact paths only; never use broad cleanup or reset. Use command-scoped Git identity for commits.
- Never archive old tasks unless the user explicitly asks to archive that exact task.
- Preserve system/platform safety requirements even when a project workflow suggests otherwise.

## Completeness checklist

- [ ] Identity and verified repository URL are stated without invented values.
- [ ] Precedence, timestamp, progress tree, and decision headings are followed.
- [ ] Authority is minimized and routine recommendations proceed unattended.
- [ ] Browser profile and credential/API token/MCP handling are enforced.
- [ ] Sub-agent ownership, parent verification, and context rollover are enforced.
- [ ] Dirty-worktree, exact-path Git, identity, and archive safety are preserved.
- [ ] Completion summaries include changes, verification, limits, impact, and switchable choices.
