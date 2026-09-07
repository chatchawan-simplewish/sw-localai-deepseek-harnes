# Project operating rules design

Date: 2026-09-08  
Repository: `chatchawan-simplewish/sw-localai-deepseek-harnes`

## Goal

Make the root `AGENTS.md` the single authoritative operating contract for this
project. The contract should maximize unattended progress, make updates easy to
read, and preserve only the approval gates that protect against genuinely
critical, irreversible, or materially more expensive changes.

## Recommended design

Use one root rules file rather than duplicating policy across several documents.
It will:

- require an Asia/Bangkok `YYYYMMDD HHMMSS` first line on every user-facing
  message;
- render requested numbered progress as a phase tree with zero-padded
  `completed/total` counts derived from current evidence;
- separate decisions into `Overview`, `What I need from you`, `Choices`,
  `Recommended choice`, and `Exact reply` sections;
- proceed automatically with the recommended option for routine choices and
  record the choice afterward;
- request one approval per topic only for supercritical actions, material
  plan/cost deviations, irreversible deletion, broad security exposure, or
  production data/identity mutation;
- verify independently before asking the owner for manual confirmation;
- use only the `Codex-Chrome-Bell-PC2` Chrome profile for project browser work,
  after checking the actual profile;
- allow project-scoped least-privilege API tokens and required MCP connections,
  while keeping secrets out of chat, Git, logs, and evidence;
- use sub-agent-driven delivery for meaningful implementation/review work, with
  clear ownership and parent verification;
- create a durable handoff and continuation task at or before 85% context, and
  leave predecessor tasks unarchived; and
- summarize completed work, verification, remaining limits, impact, and later
  switchable options.

## Precedence and safety

The owner's advance approvals remove optional workflow confirmation gates. They
cannot override system/platform policies, unavailable permissions, third-party
interactive authentication, or safeguards needed to prevent secret disclosure,
data loss, destructive actions, unauthorized public exposure, or materially
unbounded cost.

When an external confirmation is genuinely unavoidable, the agent first
exhausts safe automated checks and then asks one concise question explaining why
the owner-only step is necessary.

## Acceptance

The root `AGENTS.md` contains every requested rule once, resolves duplicates and
conflicts explicitly, includes the repository identity, and passes a scan for
missing topics, placeholders, and accidental secret material.
