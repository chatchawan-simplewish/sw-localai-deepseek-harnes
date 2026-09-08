# VM105 internal pilot proposal

Status: owner approved on 2026-09-08 for the current-instance pilot: native provider writes to the current profile, existing interpreter ownership accepted for this trial, SSH-only access. The original strict preparation goal remains BLOCKED and is not reclassified.

## Tonight's outcome

Use the existing Harness Web UI through the existing SSH access pattern with one explicitly selected provider/model. Demonstrate one harmless response and one small coding task in a disposable workspace. Admit additional internal testers only through authenticated, restricted access already available; a new shared-network exposure is a separate decision.

## Recommended fast route

Reuse the current VM105 instance and installed runtime. Perform a short read-only availability check, then use the native UI to configure one fresh VM105-specific provider credential and select a model. The owner enters the credential privately. Do not copy credentials from Hermes or another host, or display/export existing secrets. Do not install or upgrade packages, change runtime ownership, restart or cut over the service, or change firewall/network policy as part of this proposal. If the running UI cannot support the pilot without one of those changes, report the concrete obstacle before expanding scope.

This route requires an explicit owner change to the earlier current-profile-preservation instruction: native provider configuration will write to the current profile. It also treats the observed dsh:dsh-owned interpreter as an accepted internal-pilot limitation, not a satisfied root:root discovery requirement. The prior BLOCKED evidence and roadmap are retained unchanged.

## Acceptance checklist

1. UI reachable through an authenticated SSH forward; no public or generic LAN listener.
2. One provider/model explicitly selected; one successful harmless prompt.
3. One small coding task succeeds in a disposable workspace and its output is checked.
4. A short record identifies what worked and what remains unverified; no secrets retained.

Routine work proceeds directly. Use one focused independent review of actual changes and results; avoid repeated general plan-review loops. Fix concrete blockers, retaining only the smallest meaningful tests for code changes.

## Deferred

Full profile-selector proof and migration; interpreter ownership hardening; all remaining provider routes; native OAuth unless it is the chosen first provider; automatic routing/fallback attribution; comprehensive failure matrix; RX-drop investigation; final 21-requirement closeout. Internal-pilot success does not mark these complete.

## Alternative preserving the current profile

Prepare a separate isolated pilot instance/account instead. This preserves current-profile opacity but adds setup and requires verification of its storage separation and runtime launch. No container runtime, spare port, or complete DSH_HOME isolation has yet been verified, so no exact launch command or timing is promised.

## Scope decision required

Owner selected the recommended current-instance pilot and explicitly allowed native provider writes to the current profile and accepted existing interpreter ownership for this trial. Credentials remain owner-entered. Service restart, package upgrade, ownership repair, broad network exposure, and unrelated profile/secret inspection remain outside the pilot.
