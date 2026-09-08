# VM105 v1 resume preflight

Recorded: 2026-09-08, Asia/Bangkok. Parent read-only observations approximately 23:50–23:52; this document records those observations, not a new deployment or final approval.

Independent review of this record and addendum: `/root/switch_review`, **ACCEPTED, no blocking findings**, 2026-09-08 23:54:53 Asia/Bangkok. Parent checked the record against the fresh tool results and verified both prerequisite links. Acceptance is limited to preflight documentation; action-time revalidation, owner readiness and runtime acceptance remain required.

## Authority and ownership

- Repository: `C:\Users\chatc\Projects\sw-localai-deepseek-harnes`; verified remote `https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git`.
- Actual worktree: `C:\Users\chatc\Projects\sw-localai-deepseek-harnes\.worktrees\vm105-authoritative-roadmap`, established by `git worktree list`; the supplied path omitted the separator before `.worktrees`.
- Parent verified clean branch `codex/vm105-authoritative-roadmap` at `1c63b623da0f12b70d46f5cfcc48e8549a9795cc`, equal to its remote, before this record.
- Task `01a081ea-69a3-7d50-b56b-e8fe3614a98a` owns coordination and the sequential live lane. Predecessor `Resume VM105 Scoped Path Recovery` was idle, with no shared-worktree edits observed; it remains unarchived. The bounded writer owns only this new record; parent verification remains required.
- Governing switch contract: [owner-review packet](../superpowers/plans/2026-09-08-vm105-candidate-cutover.md). Routine preapproval does not replace owner readiness to leave the provider-less candidate active pending interactive credentials.

## Evidence progress

Unchanged from [the authoritative roadmap](../../.planning/ROADMAP.md); these are completed evidence tasks, not deployment PASS counts.

- Total - 09/21
  - Phase 1 - 05/05
  - Phase 2 - 03/03
  - Phase 3 - 01/02
  - Phase 4 - 00/09
  - Phase 5 - 00/02

## Fresh read-only observations

| Check | Parent observation |
| --- | --- |
| VM and service | Strict SSH reached `deepseek-harness-01`; active service PID `829`, start `2026-09-08 14:41:13 UTC`, `NRestarts=0`. |
| Service execution | `dsh:dsh`, `UMask=0077`; `/usr/local/bin/dsh web --host 127.0.0.1 --port 3080`; working directory `/srv/dsh/workspaces`; selector remains `/home/dsh/.dsh`. |
| Environment boundary | Unit environment names only `DSH_HOME`, `HOME`, `PATH`; process names contained baseline system names and no provider credential names. Workspace `.env` absent; `DropInPaths` and `PassEnvironment` empty. `EnvironmentFiles` was omitted even by `systemctl show --all`; the parent resolved this at 23:54:06 by parsing `systemctl cat` inside Python: zero `EnvironmentFile` or `PassEnvironment` directives, with no drop-ins. Only directive names/counts were emitted, not raw unit text or values. This proves no configured environment-file input within the inspected unit source; it does not turn the omitted property into a returned empty value. |
| Existing lifecycle policy | `Restart=on-failure`, `RestartUSec=5s`, `TimeoutStartUSec=1min30s`, `TimeoutStopUSec=1min30s`; preserve these policies. |
| Destination trust | `/etc`, `/etc/systemd`, `/etc/systemd/system` are real `root:root` 0755 directories. Exact packet drop-in directory and destination are absent. |
| Access | VM loopback HTTP 200; UFW active without explicit 3080 rule. Windows tunnel HTTP 200, listener `127.0.0.1:3080`, PID `33528`; named reconnect task Running. Direct LAN connection failed within three seconds. |
| Reconnect artifact | Installed SHA-256 `59E1E77B9C9C308E8DF89E2E8E2494B417FFA0BE255DF6CCF228B1EBF4FFF571`. This does not prove Windows-login or Prox-01-reboot recovery. |
| Static candidate | Read-only functions from the hash-pinned preparation helper verified the amended five-row expected bytes: exactly four directories and four files, every hash equal to the [existing JSON receipt](vm105-provider-candidate.json), `dsh:dsh`, directories 0700, files 0600, single-link files, no ACL/capabilities, stable identities through held nofollow descriptors and checked ancestor trust. |
| Python | `/usr/bin/python3.12 -I` reports optimization level 0. |

No old-profile content was read; no live mutation, candidate startup or candidate API probe occurred. Installed-source pins were **not freshly revalidated in this pass**. Static preparation remains accepted; runtime and full-plan credentials/routes remain **NOT PROVEN**.

Follow-up at 2026-09-09 00:10 Asia/Bangkok: [fresh source receipt](vm105-v1-source-revalidation-2026-09-09.json) verifies 28 package identities/dependency mappings and 56 file pins with retained SSH exit 0; independent review accepted source/transport proof only. The [earlier source attempt](vm105-v1-source-revalidation-2026-09-08.json) retains its missing-exit qualification. [The bounded checker](../../scripts/Test-VM105SourcePins.ps1) passed four offline rejection cases and four nonzero-exit checks. Its fixed receipt destination now exists, so reuse stops before SSH; any future source check needs a separately reviewed fresh receipt destination. Immediate action-time revalidation and owner cutover readiness remain required. Full-plan progress remains 09/21.

## Bounded execution addendum

Independent review `/root/switch_review` found the switch conditionally ready, requiring a fixed timeout execution receipt and an unoptimized interpreter pin. This record fixes the proposed bounds; it does not grant execution authority. Revalidate all mutable baseline facts, including the scoped environment-input proof, candidate integrity and packet installed-source pins immediately before any authorized stop.

| Operation | Fixed bound |
| --- | --- |
| Strict SSH connection | `ConnectTimeout=10` seconds |
| Read-only subprocess | 10 seconds |
| Each systemctl stop/start/restart | 110 seconds, allowing the existing 90-second systemd bound plus margin; parent polls at most 30 seconds at a time and provides commentary within 60 seconds |
| systemctl daemon-reload | 15 seconds |
| Each root HTTP check | 5 seconds |
| Each exact candidate API read | One request, 5 seconds, at most 64 KiB; no redirect, proxy or retry |
| Direct LAN connection | 3 seconds |

Use `subprocess.run(timeout=...)` and check return codes. Run the packet probe only with `/usr/bin/python3.12 -I`, without `-O` or `-OO`; explicitly fail when `sys.flags.optimize != 0` before any probe so its assertion checks cannot silently disappear. The two allowlisted API reads remain candidate-only, after independently proving the candidate process selector; never issue them against the pilot.

A timeout after a stop attempt is ambiguous and triggers exactly the packet's single rollback path. Resolve and verify pending systemd jobs within that bounded path before issuing another control operation; never issue a competing switch/start. Inability to establish the state ends `ROLLBACK_FAILED`, with no second switch, rollback attempt, speculative repair or policy change. Record command bounds, sanitized results and ledger in the actual execution receipt.

## Remaining work and limits

Keep the pilot active pending owner readiness. Once readiness and immediate release checks hold, the packet permits one reversible switch and one rollback on failure; successful runtime acceptance ends at `CREDENTIAL_GATE`. Credential entry, OAuth and inference are not part of the switch.

The existing [provider prerequisites](phase-03-provider-prerequisites.md) and [firewall review](phase-03-firewall-review.md) still govern route release: VM1201 identity/listener/model/auth and verified network controls; Bell-PC2 upstream model/auth and valid network controls; Typhoon OCR request compatibility; and a usable native Codex login surface with isolated state. No current local-worker readiness or hardware/load proof is inferred from this VM105 preflight. No hardware, VM-power, firewall or provider change is released here.

All seven provider requirement groups, invalid-credential failure isolation and child provider/model/reasoning attribution still need their separate roadmap evidence. Explicit routing remains required. Fresh-profile credentials, final classification and final handoff remain pending; the earlier RX-drop WARN and unresolved current need for the unchanged VM104 SSH rule remain open. The switchable operational choices remain the packet's existing two: keep the usable pilot, or leave the verified candidate active when the owner is ready for fresh credentials.
