# VM105 post-smoke cutover amendment — draft for independent review

Prepared 2026-09-09 02:50:33 Asia/Bangkok. Repository: https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git.

**Draft only. No execution is granted.** This amends the [September 8 cutover packet](2026-09-08-vm105-candidate-cutover.md) where its DSH_HOME-only drop-in and pristine-candidate assumptions no longer describe the proven isolated launch. All other restrictions remain. An independently reviewed, frozen execution helper and completed release evidence must exist before asking the owner for private-credential readiness.

## What changed and what did not

The [v3 result](../../evidence/vm105-candidate-smoke-v3-result-2026-09-09.json) establishes isolated API mounting, zero active adapters, the expected dormant native default, and owned process/namespace cleanup. The [generated inventory](../../evidence/vm105-candidate-v3-generated-inventory-2026-09-09.json) records post-start state. Neither proves ordinary service compatibility, owner-tunnel candidate access, fresh credentials, native OAuth, provider routes or full-v1 acceptance. Full-plan progress remains09/21.

V3 used the pinned Node executable directly, with `--no-global-search-paths` and `--no-open`. A selector-only service change would omit those flags. This amendment proposes one exact drop-in that changes both the selector and ExecStart, leaving the installed wrapper and base unit untouched. The normal service keeps its existing reviewed hardening/restart policy; this is not permission to transplant or relax the isolated unit's namespace/resource controls. Ordinary-service behavior requires its own acceptance checks.

Keep the usable pilot until owner readiness for fresh private credential entry. The candidate still has no active provider; leaving it active otherwise suspends usable provider access. The readiness question concerns that consequence and owner-only authentication, not a new gate for routine reversible preparation. No current profile data may be read, copied, migrated or deleted; `/home/dsh/.dsh` remains opaque except the original packet's single permitted root-only lstat baseline.

## Exact launch and source evidence

A guarded read of `/usr/local/bin/dsh` at `2026-09-08T19:50:31.239946+00:00`, SSH exit0, receipt `de1866`, confirmed its sole meaningful command is an exec of the following Node and CLI tokens followed by the original arguments:

- Node: `/opt/node-v24.19.0-linux-x64/bin/node`.
- CLI argument spelling: `/opt/deepseek-harness/node_modules/@deepseek-ai/dsh/lib/bin.js`.
- Wrapper SHA256: `553ca65c989274e30583bfa56b08a3bca1a9b613e6647680f57558b19406dd14`.

This is the reviewed v3 wrapper parser's `match[2]` spelling, not an invented canonical substitute. Fresh execution checks must revalidate the wrapper bytes, pinned Node, CLI logical/canonical mapping and all reviewed source pins; drift blocks. The read used the unchanged trusted Inspection helper, root-owned non-writable ancestors, held nofollow descriptors, stable metadata and double hashes. No wrapper execution or profile read occurred in this drafting lane.

Create exclusively `/etc/systemd/system/deepseek-harness.service.d/90-vm105-provider-profile.conf`, regular nonlinked root:root0644, with these exact UTF-8/LF bytes and final LF:

```ini
[Service]
Environment=DSH_HOME=/home/dsh/.dsh-profiles/vm105-provider-v1
ExecStart=
ExecStart=/opt/node-v24.19.0-linux-x64/bin/node --no-global-search-paths /opt/deepseek-harness/node_modules/@deepseek-ai/dsh/lib/bin.js web --host 127.0.0.1 --port 3080 --no-open
```

The parent directory must be real root:root0755; create only that exact directory if absent and record creation. Existing unexpected objects or any conflicting drop-in block; never overwrite. The helper must derive and freeze the exact content hash before execution. This sole file replaces the older selector-only payload. ExecStart's empty assignment intentionally clears the base command; removing this owned file restores the unchanged base wrapper automatically after daemon-reload.

## Mandatory release evidence — complete before owner readiness

Update 2026-09-09 02:57 Asia/Bangkok: fresh [post-smoke receipt](../../evidence/vm105-post-smoke-evidence-2026-09-09.json), SSH0 receipt882270, reports POST_SMOKE_EVIDENCE_PASS,432 exact closure mappings,2011 edges,463 inventory entries, root equality/hash below, three original input hashes, FD restoration and unchanged pilot identity. This supersedes the PENDING live-capture labels in items2–3; independent receipt review is pending. Independent amendment review found no substantive design blocker before helper implementation. The actual execution helper remains pending and no cutover is released.

1. Independently review this amendment and freeze the actual execution helper, including rejection tests and checked SSH exits. It must have bounded command/probe deadlines, exclusive-file handling, identity-safe rollback, separate primary/rollback failures, and no unbounded restart loop. Do not reuse consumed smoke apply modes.
2. **Post-smoke graph/config receipt PENDING:** obtain the separate worker's durable exact fallback graph, manifest hashes/logical targets, and protected candidate inventory proof. The aggregate432 fallback links/463 entries alone is not a durable graph pin. Preserve all four exact optional-peer tuples, native no-global path equality with scoped/unscoped counts derived correctly, trusted absent `/opt/node_modules` and `/node_modules` parents, current512-package/4096-edge/30-second/1MiB bounds and verifier-local FD restoration. No broader skip/global-content inspection.
3. Validate candidate `profiles/web/cordis.yml` against the deterministic public-source root constant:223 UTF-8 bytes, no BOM, four LF characters including final LF, SHA256 `c300dcf2ebc5f02062d6591268d29d3db6fe45e0cb138f5467276fe2ba06076e`. Source `profile-boot-DG5t9aNs.js` SHA256 `f83ffea6a4d30cfbe02b41dabcc05104c4ad27bf79c74f601f0ddb6ccdf88969`, lines102–108 and140–143. This expected hash is derived, not a claim that current bytes match; protected live validation receipt remains PENDING. Later Loader write-back is possible, so mismatch blocks rather than being normalized.
4. Preserve the three other original candidate-file pins and the exact [five reviewed overrides and active composition](2026-09-08-vm105-candidate-cutover.md): candidate spill root, telemetry DISABLED, disabled llm-deepseek and web-search-deepseek, empty llm-pi-ai providers. Retain settings, credentials, registry, native default and provider UI. Bind the29 package mappings/63 source pins from the reviewed smoke. Unknown generated private files retain metadata-only classification; do not read them to infer semantics.
5. Complete normal-service activation/source verification described below and review its helper. Establish exact base-unit pin, expected baseline ExecStart, preserved User/Group/UMask/WorkingDirectory/HOME/PATH/restart/hardening, no unapproved drop-ins and the absent destination. Existing unexpected environment names, envfiles, profile/home dotenv/patch inputs, socket activation or conflicting units block. Capture only allowlisted selector metadata, never secret values.
6. Immediately before any switch, refresh pilot/tunnel identity, HTTP200, active UFW, loopback-only3080 and direct-LAN denial. Do not reuse historical PIDs as control authority. Confirm exact normal-service ownership and the candidate post-smoke pins remain unchanged.

## Normal-service source proof is a different composition

Fresh public [base-contract receipt](../../evidence/vm105-cutover-base-contract-2026-09-09.json), SSH0 at03:01:29 Bangkok, independently verifies source SHA256 `5019702FA48EA6067DE59B5071297F80450B90BD759A813236B71DB7E4BF6EC0` and39 allowlisted properties. Artifact SHA256 `286E05565C12CDAAE886A3907500932B07E239277AFE60DA2F251777967761D3`. The normal base has90-second start/stop timeouts, Restart=on-failure with5-second delay, journal/inherit output, host networking and ProtectSystem=full. Control deadlines must accommodate pending systemd jobs and reserve rollback; the isolated smoke's shorter bounds do not apply. Effective Environment was not included in this receipt and needs fresh allowlisted verification. Historical PID/InvocationID are not control authority.

Independent receipt review accepted complete on-disk JSON SHA256 `F41FF7A8ED958F0BAF262F043D9CEE6E19FD56A97D2513A6770CC8D505B2D73B`, with432 unique package rows,463 unique inventory paths, exact fallback-name correspondence,2011 edges,four contained peers,root equality,three input pins,restored FD limits and unchanged pilot. This closes items2–3 at capture time; fresh execution-time revalidation remains required. No independent live rerun occurred.

The isolated helper's no-drop-in predicate cannot be reused unchanged: after cutover the intended normal-service composition is the exact verified base fragment plus the sole owned drop-in above. The execution helper must verify both held root-owned files, expected exact contents, directory/link/ACL/mount identity, no other drop-ins, no `.include` or unsupported source syntax, and no EnvironmentFile/Sockets assignments in either source. The owned Environment and ExecStart directives are allowed only as the exact payload.

Handle missing EnvironmentFiles and missing Sockets independently; neither is silently converted into an empty emitted value. Require each distinct source-proof marker. If either property is emitted it must satisfy its exact empty condition. Independently emitted TriggeredBy must be empty. Check `deepseek-harness.socket` is not-found before switching and activation remains absent afterward; an existing or uncertain same-stem socket blocks, never deletes it. Keep PassEnvironment empty, clean launch names, direct normal systemd service activation without pipe/pty/socket passing and the preserved base null/stream policy as freshly verified. No service/journal content probe may stand in for these checks.

Revalidate actual post-reload base-plus-owned-drop-in identity and effective properties before API probes. Pilot-only source proof validates the mechanism, not the future composition. This draft deliberately does not claim ordinary-service startup is already proven.

## One switch, all acceptance checks, one rollback

### Reviewed cross-host gate and rollback lineage

The execution helper runs on Bell-PC2 and uses one strict-SSH child for VM controls, with stdin reserved for a finite protocol. A fresh cryptographic per-run nonce and explicit PREFLIGHT/CANDIDATE stage bind each exact-schema, single-use message. Extra fields, replay, wrong stage, EOF or timeout fail closed. Parent checks the existing task/listener identity within5s, tunneled HTTP within5s and direct-LAN denial within5s; the complete parent gate is bounded20s, remote gate30s monotonic. PREFLIGHT failure makes no service mutation. Any failure after the stop attempt invokes the single rollback. Parent retains SSH through the separately bounded rollback; remote rollback does not depend on successfully writing stdout. The global deadline must reserve rollback time instead of killing the channel at the main-attempt deadline. Rollback verification also includes fresh parent-side checks before reporting restoration PASS; an unavailable parent means restoration remains NOT PROVEN even if VM restoration succeeds.

A systemd automatic restart is always acceptance failure. For rollback only, a replacement invocation may be controlled when the exact unchanged base plus owned drop-in, candidate selector/argv and exact service cgroup independently prove the same owned candidate lineage. Recapture immediately before control; restart races or unrelated source/process drift are ambiguity and block control. No broad PID kill or acceptance of a restarted candidate. These narrow rules were independently reviewed as defensible for implementation; they do not release execution or owner readiness.

Remote SIGHUP/SIGTERM and EOF after the stop attempt enter guarded rollback; BrokenPipe while emitting a receipt must not bypass it. Offline checks cover these failures, timeout, malformed/wrong-stage messages and restart races at mutation boundaries. SIGKILL or host loss cannot guarantee automatic restoration; no new watchdog/service is introduced to imply otherwise.

After all release evidence, frozen-helper acceptance and owner readiness, follow the original ordered single stop/switch sequence. One switch attempt is allowed; any failure or ambiguity after attempting the stop enters the single rollback. Take only the original permitted root-only old-profile lstat baseline after stop; do not traverse its children. Create the exact drop-in exclusively, record inode/device/content hash/owner/mode, daemon-reload, and start once.

Acceptance requires all original checks plus these amended proofs:

- Record the initial InvocationID, MainPID/start identity and NRestarts baseline. Any invocation, process or restart-count change before acceptance fails the switch; the preserved Restart=on-failure policy must not conceal multiple candidate invocations. Bind every stop/rollback control to the verified service invocation and exact source composition; unrelated drift blocks control.

- Systemd effective ExecStart tokens and the actual owned process argv exactly equal the reviewed Node/flag/CLI/web/host/port/no-open vector above. Bind MainPID/start identity, UID/GID and cgroup to `deepseek-harness.service`; recheck identity before reads/probes.
- Effective process `DSH_HOME` is exactly the candidate, HOME and WorkingDirectory match the baseline, and the allowlisted environment/activation proof passes without exposing values. Preserve source-proven no old-home merge and the five active composition overrides.
- Listener belongs to that service and is only127.0.0.1:3080; the existing SSH tunnel and HTTP root work. UFW/rules remain unchanged and direct LAN access remains denied. No port3081, new tunnel, browser launch or public listener is introduced.
- Use the original exact candidate-only `llm.providers` and `host.describe` requests and envelope validation: one request each, five-second wall cap,64KiB body cap, no redirect/proxy/retry. Require zero active adapters and native dormant default equality. Emit only sanitized counts/booleans, never raw response fields. No model discovery, inference or credential calls.
- Revalidate the pinned fallback map, original files and source-derived root under their separate policies; classify new generated private state by metadata only. Old-root lstat remains unchanged from its post-stop baseline. Any mismatch or missing proof fails the switch.

Rollback first stops the same owned service if necessary within the fixed reviewed bound. Remove only the drop-in created by this attempt and only while its recorded identity, exact content, owner/mode and held trusted parents still match. No created file means no deletion. Unexpected identity/content means fail closed: do not remove another file. Leave any newly created empty drop-in directory and both profile trees intact. Daemon-reload and restart the normal service once; the unchanged base unit again invokes `/usr/local/bin/dsh web --host 127.0.0.1 --port 3080`, restoring the prior selector without manually rewriting ExecStart or copying configuration.

Verify effective old selector and original wrapper/process tokens, preserved hardening, loopback/tunnel HTTP, UFW and LAN denial. Successful restoration records ROLLED_BACK and the failed check; no repeat switch. Failed/ambiguous rollback records BLOCKED with exact safe primary/rollback codes and no further service attempt. Old-root comparison ends when rollback resumes ordinary pilot use.

If every switch check passes, record SWITCH_ACCEPTED and pause at the existing CREDENTIAL_GATE. No key creation/copy, login, OAuth consent, route configuration, provider tests or fees belong to this cutover. Owner readiness and all credential/route acceptance remain separate. This draft is ready for independent review, not execution.
