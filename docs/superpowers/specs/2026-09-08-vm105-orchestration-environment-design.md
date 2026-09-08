# VM105 orchestration environment design

Date: 2026-09-08
Repository: `chatchawan-simplewish/sw-localai-deepseek-harnes`

## Goal

Turn the existing loopback-only DeepSeek Harness deployment on VM105 into a fully evidenced software-development orchestration environment without weakening its isolation or importing credentials from Hermes.

## Design

Work proceeds through five gates:

1. Establish authority: revalidate Git, VM105, and source evidence; import a redacted deployment record; reconcile stale governance checkboxes.
2. Establish network facts: explain the VM104 SSH rule, observe RX drops, and prove the Bell-PC2 tunnel plus direct-port denial.
3. Establish provider prerequisites: verify endpoints and model IDs, create owner-only backups, configure fresh credentials/native OAuth, and add only route-specific firewall permissions.
4. Establish route truth: test every requested route separately, then use invalid credentials to prove fail-closed behavior and black-box tests to decide whether automatic attribution is safe.
5. Close the evidence loop: classify every requirement, update the numbered progress tree, and write a durable handoff.

Live changes are sequential and reversible. Read-only discovery and independent review may run in parallel when they own disjoint files or resources. Provider/model selection remains explicit unless automatic child attribution proves provider, model, and reasoning without ambiguity.

## Data and secret handling

Credential values are entered only through a write-only UI or native OAuth flow and never appear in chat, Git, commands, screenshots, reports, or test prompts. Evidence records only provider name, route identifier, safe credential fingerprint metadata when available, file ownership/mode, timestamps, response attribution, and revocation steps.

## Failure handling

Any identity drift, unexpected listener, broad firewall permission, secret exposure risk, ambiguous fallback, or failed rollback check stops that lane. Existing working state remains in place. Results are recorded as `PASS`, `WARN`, `BLOCKED`, or `NOT PROVEN`.

## Verification

Each route receives an isolated harmless prompt containing a unique nonce and a request to report its provider/model identity. Evidence correlates the UI/session selection, response attribution, relevant server/provider logs, and network path. Invalid credentials must produce an error with no successful child response and no evidence of another provider invocation.

## Pre-approved choices recorded

- Standard five-phase roadmap.
- Quality-focused planning and independent verification.
- Sequential live mutations; parallel disjoint read-only/review work.
- Explicit routing by default.
- No generic domain research because the owner supplied exact infrastructure, routes, constraints, and success criteria.
