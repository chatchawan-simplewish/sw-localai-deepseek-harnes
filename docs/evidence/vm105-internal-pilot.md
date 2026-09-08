# VM105 internal pilot

Status: in progress, awaiting owner-only OmniRoute management login, then dedicated key creation/private entry. Pilot 01/04; authoritative full roadmap remains 09/21.

## Authority

On 2026-09-08 the owner explicitly approved the existing-instance internal pilot, native provider configuration in the current profile, and existing interpreter ownership for this trial. Access remains SSH-only. This is a new pilot scope; it does not reclassify the prior strict preparation BLOCKED outcome or complete its goal.

## Checks

- [x] 1. UI reachable through existing authenticated SSH forwarding. See vm105-internal-pilot-readiness.md; browser profile Codex-Chrome-Bell-PC2, existing tab DeepSeek Harness at http://127.0.0.1:3080/.
- [ ] 2. One provider/model and harmless response. Owner selected OmniRoute API on VM1205. VM105 reachability PASS: http://192.168.1.68:20128/v1 returns401; native Harness /v1/models request also returns401. Native custom-provider form has ID omniroute-vm1205, display name OmniRoute VM1205, base URL http://192.168.1.68:20128/v1, protocol openai-completions. No credential entered or provider saved; model remains unselected.
- [ ] 3. Disposable coding task and output check.
- [ ] 4. Focused independent result review and final handoff.

## Continuation

Parent browser handle harness refers to tab435371600, Chrome browser2, profile Codex-Chrome-Bell-PC2. Reverify profile for any project link/new tab. Native custom-provider form awaits verified OmniRoute endpoint/model followed by owner private credential entry/submission. Do not capture credential field values, clipboard, screenshots containing secrets, or raw current-profile files. Wait for owner to confirm submission before reading post-save state; suppress/redact credential-field values if needed.

Disposable workspace created and verified by readiness agent: /srv/dsh/workspaces/internal-pilot-20260908, dsh:dsh mode0700. UI selection and coding task remain pending.

Owner requested opening key-management page to create a dedicated key. Management SSH tunnel created on Bell-PC2, PID4356, local bind127.0.0.1:20128 -> belladmin@192.168.1.68 remote127.0.0.1:20128. Used existing project key, BatchMode/IdentitiesOnly/StrictHostKeyChecking/ExitOnForwardFailure/ConnectTimeout10/ServerAliveInterval15. Verified sole listener belongs to that PID and is loopback-only; rootHTTP307 redirects to login. No remote service/firewall/network changes. This is the only new local background process started by the pilot. Retain while management UI is needed; close only this exact owned process when finished.

Management browser handle omni: tab435371650 in verified Chrome profile Codex-Chrome-Bell-PC2, http://127.0.0.1:20128/login. Password required. Do not try the displayed default or inspect password stores. Owner must sign in privately; then navigate actual UI to key management. No key has been created. Before any new credential entry/confirmation/submission, hand off to owner per browser policy; no secret capture. Both browser tabs marked for handoff.

No service restart, ownership repair, package upgrade, firewall/network mutation, or broader exposure is part of this pilot. Existing strict preparation evidence and handoff remain intact as historical scope records.
