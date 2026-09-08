# VM105 Reversible Profile Pointer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prepare a fresh secret-free VM105 Harness profile from installed-version proof, produce an exact reversible service-pointer packet, and stop at separate cutover and credential gates.

**Architecture:** A single tracked JSON evidence record is the contract between discovery, preparation, cutover review, and post-cutover verification. Installed-version discovery must first prove an absolute, non-merging, whole-profile selector; only then may a bounded initializer create the fixed candidate path, while a separately reviewed controller remains inert until an exact action-time cutover approval.

**Tech Stack:** PowerShell 7 and .NET standard library, Windows OpenSSH client, POSIX shell/coreutils already installed on VM105, systemd, JSON, Git.

## Global Constraints

- Treat the current profile as an opaque object.
- The only allowed pointer is the minimum profile-selection mechanism supported by the installed Harness version. It must isolate every mutable Harness store, not a credential-only or settings-only subset.
- Preparation is secret-free and static. Runtime proof requires a separately approved maintenance restart.
- Missing, ambiguous, deprecated, or content-dependent selector behavior blocks work; no wrapper, symlink, package change, copied config, or guessed environment variable substitutes for proof.
- The candidate remains loopback-only, exposes zero active provider routes, and disables automatic fallback.
- The prior service pointer and old profile root remain available after success. Destruction is never part of this design.
- No data flows from the current profile to the candidate. The only allowed inputs are installed-version evidence, freshly captured sanitized unit/selector metadata, approved settings, and the fixed profile path.
- No state permits automatic retries beyond the one explicit rollback sequence. The controller never proceeds past an ambiguous result.
- Approval of this specification and implementation start authorizes only secret-free discovery and preparation. It does not authorize cutover or any credential-bearing action.
- Keep credentials out of chat, Git, logs, screenshots, and evidence.
- Preserve dirty work, stage exact paths only, and use command-scoped Git identity.
- Never archive old tasks unless the user explicitly asks to archive that exact task.

---

## Planned File Map

| Path | Responsibility | Created in |
| --- | --- | --- |
| `docs/evidence/vm105-profile-pointer.json` | The only new profile-pointer evidence record: sanitized discovery contract, candidate blueprint/result, immutable cutover packet, execution result, mutation ledger, and credential-gate state | Task 1; updated Tasks 2-5 |
| `scripts/Test-VM105ProfilePointer.ps1` | One dependency-free schema, policy, digest, stage, and value-suppressing secret scanner with synthetic self-tests | Task 1 |
| `scripts/Initialize-VM105ProviderProfile.ps1` | Bounded preparer that consumes the accepted selector digest and candidate blueprint, writes only the fixed fresh tree, performs static checks, and never starts Harness | Task 2 |
| `scripts/Invoke-VM105ProfileCutover.ps1` | Inert-until-approved cutover state machine with dry-run/self-test modes, one switch attempt, and at most one automatic rollback sequence | Task 3; executed only in Task 4 |

No existing profile, evidence artifact, service file, firewall rule, package, provider route, credential store, OAuth state, or browser state is a planned repository modification. The systemd drop-in `/etc/systemd/system/deepseek-harness.service.d/90-vm105-provider-profile.conf` is only a future live target after Task 1 proves the installed selector and Task 4 receives action-time approval.

## Shared Evidence Contract

`docs/evidence/vm105-profile-pointer.json` uses `schemaVersion: 1` and these exact top-level properties:

```json
{
  "schemaVersion": 1,
  "workflowId": "vm105-reversible-profile-pointer",
  "target": {},
  "overallVerdict": "BLOCKED",
  "selectorDiscovery": {},
  "candidatePreparation": null,
  "cutoverPacket": null,
  "cutoverExecution": null,
  "credentialGate": {
    "status": "NOT_ELIGIBLE",
    "reason": "Cutover has not been accepted"
  },
  "operationLedger": []
}
```

Exact nested interfaces:

- `target`: `hostname`, `address`, `sshHostKeyIdentity`, `service`, `serviceUser`, `serviceGroup`, `candidateRoot`, `listenerHost`, `listenerPort`.
- `proofRef`: `sourcePath`, `sourceSha256`, `lineStart`, `lineEnd`, `claim`; references may name installed package/help/unit sources or sanitized live metadata/privilege receipts only and must never name a child of the current profile.
- `selectorDiscovery`: `capturedAt`, `installedVersion`, `verdict`, `blockers`, `baseline`, `installedEntrypoint`, `privilegeSeam`, `selector`, `candidateBlueprint`, `selectorDigest`, `review`.
- `installedEntrypoint`: `wrapperPath`, `wrapperOwner`, `wrapperGroup`, `wrapperMode`, `wrapperSha256`, `entrypointPath`, `entrypointOwner`, `entrypointGroup`, `entrypointMode`, `packageRoot`, `packageName`, `packageVersion`, `proofRefs`; `entrypointPath` and `packageRoot` are fixed absolute paths below `/opt/deepseek-harness` discovered from the verified installed wrapper.
- `privilegeSeam`: `verdict`, `capturedAt`, `commands`, `proofRefs`; every command has `id`, absolute `executable`, exact `argv`, `noninteractive`, and `allowed`, and collectively covers drop-in-file install/removal plus `systemctl stop`, `start`, `daemon-reload`, and read-only status. Any missing command makes the discovery `BLOCKED`.
- `selector`: `name`, `precedence`, `absoluteCandidateValue`, `unitDropInPath`, `unitDropInLines`, `unitDropInSha256`, `effectiveProfileProbe`, `proof`.
- `selector.proof`: `absolutePath`, `precedence`, `fullProfileScope`, `nonMerge`, `serviceCompatibility`, `supportedUnitOverride`; each item has `proven: true` plus one or more `proofRef` records. `fullProfileScope` has separate `credentials`, `settings`, `plugins`, `sessionsState`, and `otherMutableStores` proofs.
- `candidateBlueprint`: `directories`, `files`, `policyAssertions`, `staticValidation`; every directory/file uses a safe relative path, an octal mode, and source proof. Each file also has `contentLines` and `sha256` over UTF-8 bytes joined by LF with one terminal LF.
- `candidatePreparation`: `selectorDigest`, `candidateDigest`, `startedAt`, `finishedAt`, `verdict`, `createdPaths`, `metadataChecks`, `staticChecks`, `serviceUnchangedChecks`, `runtimeVerdict`, `blockers`, `review`.
- `cutoverPacket`: `packetId`, `createdAt`, `packetDigest`, `selectorDigest`, `candidateDigest`, `expiresAt`, `maxSwitchAttempts`, `maxRollbackAttempts`, `automaticRetries`, `expectedBaseline`, `pointerMutation`, `rollbackMutation`, `orderedChecks`, `allowedMutationTargets`, `review`.
- `expectedBaseline`: `capturedAt`, `hostname`, `machineIdentity`, `sshHostKeyIdentity`, `service`, `currentSelector`, `listeners`, `httpHealth`, `ufw`, `directLanDenied`, `dropInDirectory`; `service` contains `name`, `activeState`, `subState`, `user`, `group`, `execStartArgv`, `workingDirectory`, `umask`, `restartPolicy`, `hardening`, and `networkPolicy`.
- `commandSpec`: `id`, `target`, `executable`, `argv`, `timeoutSeconds`, `parser`, `acceptedOutputs`, `successTransition`, `failureTransition`, `suppressRawOutput`; `executable` is an absolute installed path or one of the exact in-process values `PowerShell::.NET-TcpClient` and `PowerShell::OperationLedger`, `argv` is an array of atomic strings, timeout is an integer from 1 through 60, accepted outputs are exact parser results, and `suppressRawOutput` is always `true`.
- `pointerMutation`: `steps`, `stdinSha256`, `dropInOwner`, `dropInGroup`, `dropInMode`, and `selectorDelta`; `steps` is an ordered array of complete `commandSpec` records for the fixed file install and one daemon reload. `selectorDelta` has `property`, `beforeTokens`, `afterTokens`, `changedTokenIndexes`, and `proofRefs`. Its only file target is `/etc/systemd/system/deepseek-harness.service.d/90-vm105-provider-profile.conf`, and its standard input is exactly the reviewed `unitDropInLines` bytes.
- `rollbackMutation`: `triggerStates`, `maxAttempts`, `steps`, `terminalSuccess`, `terminalFailure`; `steps` is an ordered array of `commandSpec` records that removes only the new drop-in, reloads systemd, starts the service once, and verifies the prior baseline.
- `orderedChecks`: exactly eleven `commandSpec` records with consecutive `order` values 1 through 11 and the specification's check IDs `identity`, `service-identity`, `effective-profile`, `loopback-listener`, `http-health`, `ufw`, `direct-lan-denial`, `route-fallback-policy`, `candidate-storage`, `old-root-detachment`, and `no-credential-mutation`.
- `cutoverExecution`: `packetDigest`, `resultDigest`, `approvedAt`, `approvalTextSha256`, `startedAt`, `finishedAt`, `terminalState`, `states`, `oldRootLstat`, `checks`, `rollback`, `mutationLedger`, `secretObserved`, `review`.
- `operationLedger` entry: `at`, `actor`, `operation`, `target`, `result`, `secretObserved`. It records no command output or content.
- `review`: `status`, `reviewedAt`, `reviewer`, `reviewedDigest`, `findings`; `status` is `PENDING`, `ACCEPTED`, or `REJECTED`, and `findings` contains nonsecret issue summaries only.

All SHA-256 fields cover nonsecret bytes only. `selectorDigest`, `candidateDigest`, `packetDigest`, and `resultDigest` are uppercase SHA-256 of canonical JSON generated with recursively ordinal-sorted object keys, array order preserved, UTF-8 without BOM, and no insignificant whitespace; each digest excludes its own digest property and the review attached to that digest, and prerequisite digests exclude all later-stage sections.

### Task 1: Prove or block the installed whole-profile selector

**Files:**
- Create: `docs/evidence/vm105-profile-pointer.json`
- Create: `scripts/Test-VM105ProfilePointer.ps1`

**Interfaces:**
- Consumes: installed Harness `0.1.1-rc.2` help, package-shipped documentation/source/package metadata, sanitized effective `deepseek-harness.service` facts, and root-only `lstat` metadata
- Produces: the Shared Evidence Contract with `selectorDiscovery.verdict` equal to `PASS` or `BLOCKED`; a `PASS` record includes a complete `selector`, `candidateBlueprint`, and accepted `selectorDigest`
- Produces: `Test-VM105ProfilePointer.ps1 -EvidencePath [string] -Stage Selector|Candidate|CutoverPacket|PostCutover|Rollback [-SelfTest]`

- [ ] **Step 1: Write the validator and failing synthetic selector tests**

Create `scripts/Test-VM105ProfilePointer.ps1` with this public parameter contract and no external modules:

```powershell
[CmdletBinding()]
param(
    [string]$EvidencePath = 'docs/evidence/vm105-profile-pointer.json',
    [ValidateSet('Selector','Candidate','CutoverPacket','PostCutover','Rollback')]
    [string]$Stage = 'Selector',
    [switch]$SelfTest
)
```

Implement one canonical-JSON function, one uppercase SHA-256 function, schema checks for every property in Shared Evidence Contract, and a value-suppressing line scanner. The scanner reports only relative filename, one-based line, and category; it never emits the matching text. It rejects nonempty assignments for `key`, `api_key`, `token`, `secret`, `password`, `client_secret`, authorization headers, PEM private keys, `sk-`, `sk-or-`, `sess-`, and raw or encoded OAuth `code`, `state`, `access_token`, `refresh_token`, and `id_token` values. Empty values and prose naming a field are allowed.

`-SelfTest` must construct synthetic in-memory evidence and assert these exact failures:

1. `PASS` with one missing whole-profile store proof.
2. `PASS` with an empty proof-reference list.
3. A source path below `/home/dsh/.dsh`.
4. A candidate path other than `/home/dsh/.dsh-profiles/vm105-provider-v1`.
5. A relative path containing `..`, a rooted path, or a duplicate path.
6. A directory mode other than `0700` or file mode wider than `0600`.
7. A symlink, hard-link count above one, mount, broad ACL, provider route, fallback, provider/model selection, OAuth state, Hermes reference, or secret-shaped content.
8. A unit drop-in target other than `/etc/systemd/system/deepseek-harness.service.d/90-vm105-provider-profile.conf`.
9. A digest mismatch or a review whose `reviewedDigest` differs from the current stage digest.
10. A cutover packet with an extra mutation target, reordered check, retry count above zero, or more than one rollback attempt.
11. A post-cutover result with any non-`PASS` acceptance check marked accepted.
12. Suppressed secret reporting: the synthetic secret value itself must not appear in captured validator output.
13. A wrapper that is not a regular root-owned installed file, resolves outside `/opt/deepseek-harness`, contains more than the fixed launch handoff, or names a relative/unowned entrypoint.
14. A missing/noninteractive privilege receipt for drop-in install/removal, `systemctl stop`, `start`, `daemon-reload`, or status.
15. A cutover packet missing typed `maxSwitchAttempts: 1`, `maxRollbackAttempts: 1`, or `automaticRetries: 0`, or containing an incomplete command/check child schema.
16. A missing, linked, non-`root:root`, or non-`0755` drop-in directory.

The positive synthetic case has all five full-profile store proofs, zero provider routes, fallback disabled, the fixed candidate root, the fixed drop-in target, one switch attempt, one possible rollback sequence, and no secret material.

- [ ] **Step 2: Run the self-test and require the intended RED result before implementation is complete**

Run:

```powershell
./scripts/Test-VM105ProfilePointer.ps1 -SelfTest
```

Expected before the validator logic is finished: nonzero exit and a synthetic assertion identifying the first unimplemented rejection. Implement the minimum validator logic, rerun the same command, and require exit 0 with counts for every positive and negative case and no synthetic value in output.

- [ ] **Step 3: Revalidate the repository and VM105 read-only baseline**

Run from the authoritative worktree:

```powershell
$expectedOrigin = 'https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git'
if ((git remote get-url origin).Trim() -ne $expectedOrigin) { throw 'Unexpected repository origin' }
if ((git branch --show-current).Trim() -ne 'codex/vm105-authoritative-roadmap') { throw 'Unexpected branch' }

$sshArgs = @(
  '-i','C:\Users\chatc\.ssh\codex-prox01-vms-ed25519',
  '-o','BatchMode=yes',
  '-o','IdentitiesOnly=yes',
  '-o','StrictHostKeyChecking=yes',
  'dsh@192.168.1.139'
)
& ssh.exe @sshArgs -- "set -eu; hostname; id -un; id -gn; /usr/local/bin/dsh --version; systemctl is-active deepseek-harness.service; systemctl show deepseek-harness.service -p User -p Group -p ExecStart -p WorkingDirectory -p UMask -p FragmentPath -p DropInPaths -p ActiveState -p SubState -p Result -p NRestarts; ss -lntH '( sport = :3080 )'; stat -c '%n|%F|%U|%G|%a|%h' -- /home/dsh/.dsh /usr/local/bin/dsh"
if ($LASTEXITCODE -ne 0) { throw 'Read-only VM105 baseline failed' }
```

Expected: hostname `deepseek-harness-01`; caller and group `dsh`; version `0.1.1-rc.2`; service active; service identity and command are available; listener remains loopback on port 3080; only root-path `lstat` fields for `/home/dsh/.dsh` are emitted; `/usr/local/bin/dsh` is a regular installed wrapper with safe owner/mode. Do not run `find`, `Get-ChildItem`, `ls`, `tar`, `cp`, `hash`, `du`, `env`, `/proc/*/environ`, or content reads against the old profile.

- [ ] **Step 4: Discover the selector from installed-version sources only**

Read exactly the installed wrapper `/usr/local/bin/dsh` after its root owner, non-writable mode, regular-file type, and SHA-256 are captured. The wrapper is the only pre-entrypoint executable file that may be opened. Parse it as data and require a single fixed absolute entrypoint below `/opt/deepseek-harness`; reject command substitution, environment-derived paths, relative paths, fallback branches, eval, additional executables, or any target outside that root. An unexpected wrapper sets `selectorDiscovery.verdict` to `BLOCKED`.

Verify the extracted entrypoint is a regular installed/package-owned file with safe owner/mode. Starting from that fixed entrypoint, walk upward only within `/opt/deepseek-harness` to its owning `package.json`; verify package name/version and record file digests before reading package-shipped help, README/docs, schema, entrypoint, and state-location source files. Search only those verified installed files for profile/home/state/config/credential/plugin/session/cache selector semantics. Do not follow links outside the package root, run a network package command, or install anything.

For each required claim, record one or more `proofRef` records with exact installed path, SHA-256, line range, and plain nonsecret claim. Prove all of:

- exact selector name and precedence;
- absolute-path support;
- credentials, settings, plugins, sessions/state, and every other mutable store all resolve below the selected profile;
- no merge, inheritance, migration, import, fallback to, or rewrite of the current profile;
- compatibility with the existing service user and command;
- minimum supported systemd drop-in application; and
- a safe installed runtime probe that later reports the effective paths and route/fallback state without emitting secret values.

After the selector name is proven, inspect only that exact effective selector from systemd. Filter on VM105 and emit only the selector key/path or an explicit absence marker; never emit the full service environment. Inspecting the old profile remains limited to the root-only `lstat` record from Step 3.

Before allowing `selectorDiscovery.verdict: PASS`, prove the existing noninteractive privilege seam without changing it. Resolve absolute installed paths for `sudo`, `install` or the proven file writer, `rm`, and `systemctl`; run bounded `sudo -n -l --` permission checks followed by each resolved executable and its exact atomic argv for the one fixed drop-in install, its rollback removal, `systemctl stop deepseek-harness.service`, `start`, `daemon-reload`, and read-only status. Store only allow/deny verdicts, exact nonsecret argv, and proof references; suppress raw sudo policy output. If any exact operation is unavailable, ambiguous, interactive, broader than the reviewed command, or depends on a changed sudoers rule, set `privilegeSeam.verdict` and selector discovery to `BLOCKED`. Never edit sudoers, add privilege, switch users interactively, or invent a workaround.

- [ ] **Step 5: Build the PASS or BLOCKED evidence object without guessing**

If every claim is directly proven, and `installedEntrypoint` plus `privilegeSeam` both validate, populate `selector`, its six proof groups, and a `candidateBlueprint` derived only from installed defaults plus the approved fixed settings. `candidateBlueprint.policyAssertions` must equal:

```json
{
  "bindHost": "127.0.0.1",
  "port": 3080,
  "activeProviderRoutes": 0,
  "automaticFallback": false,
  "providerSelectionConfigured": false,
  "oauthStateConfigured": false,
  "hermesReferences": false
}
```

Every planned candidate file must have exact `contentLines`, `0600` or narrower mode, source proof, and matching SHA-256. Every planned directory must have an exact safe relative path and mode `0700`. The blueprint must not contain credentials, account labels, provider/model selections, native OAuth state, callback data, or copied content.

If any claim, wrapper/entrypoint fact, privilege operation, or safe blueprint field is missing or ambiguous, set `selectorDiscovery.verdict` and `overallVerdict` to `BLOCKED`, list exact nonsecret blockers, set `selector` and `candidateBlueprint` to `null`, and leave later sections `null`. Record the candidate root's preflight existence metadata; an existing/populated/unsafe parent or target is itself `BLOCKED`. This is a valid completed Task 1 outcome.

- [ ] **Step 6: Validate, independently review, and commit Task 1**

Run:

```powershell
./scripts/Test-VM105ProfilePointer.ps1 -SelfTest
if ($LASTEXITCODE -ne 0) { throw 'Profile-pointer validator self-test failed' }
./scripts/Test-VM105ProfilePointer.ps1 -EvidencePath 'docs/evidence/vm105-profile-pointer.json' -Stage Selector
if ($LASTEXITCODE -ne 0) { throw 'Selector evidence validation failed' }
./scripts/Test-Phase03Evidence.ps1 -Stage Network
if ($LASTEXITCODE -ne 0) { throw 'Existing Phase 3 evidence scan failed' }
git diff --check -- 'docs/evidence/vm105-profile-pointer.json' 'scripts/Test-VM105ProfilePointer.ps1'
```

Expected: all commands exit 0. `BLOCKED` is acceptable only when candidate and cutover data are absent and VM105 had no mutation. Dispatch an independent reviewer with the spec, evidence JSON, validator, installed-source proof references, and the exact diff. A reviewer must verify every whole-profile claim or accept the named blocker. Record `review.status`, `reviewedDigest`, and findings, rerun validation, then commit only these paths:

```powershell
git add -- 'docs/evidence/vm105-profile-pointer.json' 'scripts/Test-VM105ProfilePointer.ps1'
git -c user.name='Codex' -c user.email='codex@local' commit -m 'feat: prove VM105 profile selector'
```

Stop the entire workflow if the verdict is `BLOCKED` or review is not `ACCEPTED`. Do not create `/home/dsh/.dsh-profiles` or any candidate file in that outcome.

### Task 2: Create and statically validate the secret-free candidate

**Files:**
- Create: `scripts/Initialize-VM105ProviderProfile.ps1`
- Modify: `docs/evidence/vm105-profile-pointer.json`

**Interfaces:**
- Consumes: accepted `selectorDigest`, `candidateBlueprint`, fixed candidate root, and exact `proofRef` records from Task 1
- Produces: `Initialize-VM105ProviderProfile.ps1 -EvidencePath [string] -AcceptedSelectorDigest [64-hex string] -SshTarget [user@host string] -SshKey [path string] -Prepare [-SelfTest]`
- Produces: populated `candidatePreparation` and `candidateDigest`; it never changes `deepseek-harness.service`

- [ ] **Step 1: Write the initializer's failing guard tests**

Use this public interface:

```powershell
[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$EvidencePath = 'docs/evidence/vm105-profile-pointer.json',
    [Parameter(Mandatory)][string]$AcceptedSelectorDigest,
    [string]$SshTarget = 'dsh@192.168.1.139',
    [string]$SshKey = 'C:\Users\chatc\.ssh\codex-prox01-vms-ed25519',
    [switch]$Prepare,
    [switch]$SelfTest
)
```

The initializer must call the Task 1 validator before constructing a remote operation. It must reject a nonaccepted review, digest mismatch, non-`PASS` selector, target drift, unsafe path, unexpected existing parent/target, content hash mismatch, nonempty credential/provider/OAuth field, any shell metacharacter in a relative path, and any destination outside `/home/dsh/.dsh-profiles/vm105-provider-v1`. `-SelfTest` uses a fake SSH adapter injected only inside the script's self-test branch and asserts that zero operations are emitted for every preflight rejection.

The same injected adapter must fail each post-create operation in turn: parent creation, candidate-root creation, each directory/file write, metadata verification, static validation, value-suppressing scan, and service/network unchanged check. After the first injected failure, assert `candidatePreparation.verdict: BLOCKED`, no later write or service command, no cleanup/remove/repair command, and no operation against the old profile. The candidate paths already created before the injected failure remain untouched for review. A positive injected run must execute every planned candidate write once and zero service commands.

- [ ] **Step 2: Implement the minimum bounded preparation sequence**

The `-Prepare` path performs one strict-SSH preflight and then one sequential writer lane. It must:

1. Revalidate hostname, SSH host identity, service identity/state/listener, selector digest, parent/target absence, ancestor owners/modes, ACLs, link count, and mount boundaries.
2. Require the parent and target to be absent. Never adopt, empty, normalize, repair, rename, or delete an existing object.
3. As `dsh`, set `umask 077`, create exactly `/home/dsh/.dsh-profiles` and `/home/dsh/.dsh-profiles/vm105-provider-v1` as real directories mode `0700`, then create only blueprint directories/files below the target.
4. Transfer each reviewed secret-free file body through standard input, never by shell evaluation; verify its reviewed SHA-256 before transfer and VM-side SHA-256 after write. Paths are selected from the validated blueprint, not interpolated unchecked text.
5. Set each regular file to `dsh:dsh` and `0600` or narrower, with no hard/symbolic links. Set each directory to `dsh:dsh` and `0700`.
6. Run only the installed static-validation argv proved in `candidateBlueprint.staticValidation`. If no safe syntax validator exists, record syntax as `NOT PROVEN`; if syntax uncertainty weakens loopback/zero-route/fallback isolation, set `BLOCKED`.
7. Read only newly created candidate files with a value-suppressing scan. Emit paths/categories/verdicts, never matching values.
8. Revalidate the original service remains active, unchanged, loopback-only, locally healthy, UFW active with no TCP 3080 grant, and direct LAN TCP 3080 denied. Never start Harness against the candidate.

On any post-create failure, leave the new candidate in place for review, set `candidatePreparation.verdict` to `BLOCKED`, record the exact safe discrepancy, and stop. Do not delete or repair it automatically.

- [ ] **Step 3: Run initializer self-tests and the approved preparation**

Run:

```powershell
$record = Get-Content -Raw 'docs/evidence/vm105-profile-pointer.json' | ConvertFrom-Json
$selectorDigest = [string]$record.selectorDiscovery.selectorDigest
if ($selectorDigest -notmatch '^[A-F0-9]{64}$') { throw 'Accepted selectorDigest is absent or malformed' }
./scripts/Initialize-VM105ProviderProfile.ps1 -AcceptedSelectorDigest $selectorDigest -SelfTest
```

Expected: exit 0; rejected cases emit zero fake SSH mutations; the positive case emits only fixed candidate-root operations and no service command.

Then rerun the Task 1 selector validator and, only if it still reports `PASS` with an accepted matching digest, run:

```powershell
$record = Get-Content -Raw 'docs/evidence/vm105-profile-pointer.json' | ConvertFrom-Json
$selectorDigest = [string]$record.selectorDiscovery.selectorDigest
if ($selectorDigest -notmatch '^[A-F0-9]{64}$') { throw 'Accepted selectorDigest is absent or malformed' }
./scripts/Initialize-VM105ProviderProfile.ps1 `
  -EvidencePath 'docs/evidence/vm105-profile-pointer.json' `
  -AcceptedSelectorDigest $selectorDigest `
  -SshTarget 'dsh@192.168.1.139' `
  -SshKey 'C:\Users\chatc\.ssh\codex-prox01-vms-ed25519' `
  -Prepare
```

The command reads the 64-hex `selectorDigest` already present and independently accepted in the evidence record; it does not invent selector syntax. Expected on success: exactly the protected parent/profile tree is created; no service restart, pointer, route, firewall, package, provider, credential, OAuth, inference, or old-tree mutation occurs.

- [ ] **Step 4: Record and validate the candidate result**

Populate `candidatePreparation` from safe command receipts only. `runtimeVerdict` must remain `NOT PROVEN`. Set `candidatePreparation.verdict` to `PASS` only when metadata, file digest, static safety, service-unchanged, loopback, UFW, and direct-denial checks all pass. Set `overallVerdict` to `CANDIDATE_STATIC_PASS` only for that case; otherwise set it to `BLOCKED`.

Run:

```powershell
./scripts/Test-VM105ProfilePointer.ps1 -EvidencePath 'docs/evidence/vm105-profile-pointer.json' -Stage Candidate
if ($LASTEXITCODE -ne 0) { throw 'Candidate evidence validation failed' }
./scripts/Test-Phase03Evidence.ps1 -Stage Network
if ($LASTEXITCODE -ne 0) { throw 'Existing Phase 3 evidence scan failed' }
git diff --check -- 'docs/evidence/vm105-profile-pointer.json' 'scripts/Initialize-VM105ProviderProfile.ps1'
```

Expected: exit 0; runtime/provider/credential/native-OAuth verdicts remain `NOT PROVEN` and no secret scanner finding exists.

- [ ] **Step 5: Independently review and commit Task 2**

Give a fresh reviewer the spec, accepted selector contract, candidate blueprint, initializer, safe receipts, operation ledger, and diff. The reviewer must verify exact-path confinement, no old-profile data flow, no start/restart path, all modes, static policy, value suppression, and runtime `NOT PROVEN`. Record an accepted review against `candidateDigest`, rerun Step 4, and commit only:

```powershell
git add -- 'scripts/Initialize-VM105ProviderProfile.ps1' 'docs/evidence/vm105-profile-pointer.json'
git -c user.name='Codex' -c user.email='codex@local' commit -m 'feat: prepare secret-free VM105 profile'
```

If Task 2 is `BLOCKED`, stop with the existing service active and unchanged. Do not produce or approve a cutover packet from a blocked candidate.

### Task 3: Build and independently accept the exact cutover packet

**Files:**
- Create: `scripts/Invoke-VM105ProfileCutover.ps1`
- Modify: `docs/evidence/vm105-profile-pointer.json`

**Interfaces:**
- Consumes: accepted `selectorDigest`, accepted `candidateDigest`, and selector-provided `unitDropInLines` plus runtime probes
- Produces: immutable `cutoverPacket.packetDigest` and an independently accepted packet review
- Produces: `Invoke-VM105ProfileCutover.ps1 -EvidencePath [string] -ApprovedPacketDigest [64-hex string] -OwnerReply [string] -ApprovalTimestamp [ISO-8601 string] -ApprovalTextSha256 [64-hex string] -SshTarget [user@host string] -SshKey [path string] -Execute|-DryRun|-SelfTest [-ResultPath [scratch JSON path]]`

- [ ] **Step 1: Write the controller state-machine tests before its live path**

Use this public parameter contract:

```powershell
[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$EvidencePath = 'docs/evidence/vm105-profile-pointer.json',
    [string]$ApprovedPacketDigest,
    [string]$OwnerReply,
    [string]$ApprovalTimestamp,
    [string]$ApprovalTextSha256,
    [string]$SshTarget = 'dsh@192.168.1.139',
    [string]$SshKey = 'C:\Users\chatc\.ssh\codex-prox01-vms-ed25519',
    [string]$ResultPath = '.superpowers/sdd/vm105-profile-pointer/cutover-result.json',
    [switch]$Execute,
    [switch]$DryRun,
    [switch]$SelfTest
)
```

Before creating an SSH adapter or resolving a remote command, require exactly one of `-Execute`, `-DryRun`, or `-SelfTest`. The controller loads `packetDigest`, derives the exact required reply string itself, compares `OwnerReply` ordinally, recomputes uppercase SHA-256 from the exact UTF-8 reply, compares it with `ApprovalTextSha256`, parses `ApprovalTimestamp` as ISO-8601 UTC, and requires it is not more than 30 seconds in the future or 10 minutes old. Only `-Execute` requires valid action-time approval; `-DryRun` remains mutation-free and prints the derived required reply.

The controller uses an injected command adapter only for `-SelfTest`. Test these exact terminal flows:

- all checks pass: `CURRENT_ACTIVE → CUTOVER_REVALIDATED → SERVICE_STOPPED → OLD_ROOT_BASELINED → POINTER_APPLIED → CANDIDATE_RUNNING → SWITCH_ACCEPTED`;
- pre-stop drift: terminal `BLOCKED`, zero stop/pointer/start commands;
- stop failure or ambiguous stop state: one rollback sequence, then `ROLLED_BACK` or `ROLLBACK_FAILED`;
- pointer write/reload/start/check failure: one rollback sequence only;
- any `WARN`, empty, timeout, or unrecognized result after stop: rollback;
- successful switch with selector mismatch, route count nonzero, fallback enabled, nonloopback listener, UFW drift, direct-LAN reachability, candidate permission drift, old-root root-metadata drift, or secret observation: rollback;
- rollback failure: terminal `ROLLBACK_FAILED`, no retry or speculative repair; and
- missing, altered, wrong-digest, stale, future, or hash-mismatched action-time approval: zero adapter commands;
- conflicting/no modes (`Execute+DryRun`, `Execute+SelfTest`, `DryRun+SelfTest`, or none): zero adapter commands; and
- malformed/expired packet digest or a derived-reply mismatch: zero adapter commands.

`-DryRun` validates and prints only ordered command identifiers and targets, never command bodies that could contain dynamic data. It performs no SSH or filesystem mutation.

- [ ] **Step 2: Construct the immutable packet from accepted evidence**

Populate `cutoverPacket` only when selector and candidate reviews are `ACCEPTED`, both digests still match, candidate revalidation passes, the current service baseline has not drifted, and `privilegeSeam.verdict` still passes fresh `sudo -n -l` checks for every exact root operation. Before packet acceptance, require `/etc/systemd/system/deepseek-harness.service.d` already exists as a real non-link directory owned `root:root`, mode `0755`, with no broad ACL and no unexpected mount boundary. If the directory is absent or noncompliant, set `overallVerdict: BLOCKED`; do not create/repair it, change sudoers, or add a directory mutation lifecycle.

Set:

- `pointerMutation.steps[0].target` exactly `/etc/systemd/system/deepseek-harness.service.d/90-vm105-provider-profile.conf`;
- the bytes identified by `pointerMutation.stdinSha256` exactly equal the selector-proven, independently reviewed `unitDropInLines` joined by LF with one terminal LF;
- drop-in directory owner/mode `root:root`/`0755` and file owner/mode `root:root`/`0644`;
- `allowedMutationTargets` to only the new drop-in file and systemd manager state; no directory or profile path is mutable during cutover;
- one `rollbackMutation` that removes only this newly created drop-in, reloads systemd, and starts/verifies the prior service baseline;
- `maxSwitchAttempts: 1`, `maxRollbackAttempts: 1`, and `automaticRetries: 0`;
- an expiry no more than 24 hours after packet creation; and
- the eleven cutover checks from the approved specification in their exact order.

`expectedBaseline` is fully materialized, not a prose label. It records the freshly observed hostname/machine/SSH identities; service active/substate, user/group, tokenized `ExecStart`, working directory, `UMask`, restart-policy properties, every effective hardening property, and every effective network-policy property; current selector; exact loopback listener set; local HTTP status; UFW defaults/rules; direct-LAN denial; and drop-in-directory metadata. Property maps are ordinal-sorted name/value objects, and their canonical digests are part of `packetDigest`.

Every `pointerMutation` and rollback step is a complete `commandSpec`. `pointerMutation.selectorDelta` identifies the sole allowed effective-unit delta. For an environment selector, `ExecStart` must remain byte-for-byte equal; for a proven argument selector, `beforeTokens`, `afterTokens`, and exact changed token indexes define the only allowed `ExecStart` difference. In both cases, `WorkingDirectory`, `UMask`, all restart-policy properties, every hardening property, and every network-policy property must equal `expectedBaseline`. An added/removed/changed unit property outside `selectorDelta` is `ROLLBACK_REQUIRED`.

The ordered checks use these exact child contracts; each child contains its own executable, atomic argv, timeout, parser, accepted output, transitions, and `suppressRawOutput: true`:

| Order / ID | Executable and argv source | Parser and only accepted output | Failure transition |
| --- | --- | --- | --- |
| 1 `identity` | Resolved absolute `ssh.exe`; strict SSH argv plus installed `/usr/bin/hostname` and approved machine-identity probe | `ExactIdentityV1`; exact packet hostname, machine identity, SSH host key | `ROLLBACK_REQUIRED` after stop, otherwise `BLOCKED` |
| 2 `service-identity` | Resolved absolute `ssh.exe`; strict SSH argv plus `/usr/bin/systemctl show deepseek-harness.service` with the exact property allowlist | `SystemdUnitDeltaV1`; active/running `dsh:dsh`, selector-only delta, and exact equality for normalized `ExecStart`, `WorkingDirectory`, `UMask`, restart policy, hardening, and network policy | `ROLLBACK_REQUIRED` |
| 3 `effective-profile` | Resolved absolute `ssh.exe`; strict SSH argv plus the selector-proven absolute `effectiveProfileProbe.executable` and atomic argv | `EffectiveProfileV1`; credentials, settings, plugins, sessions/state, and all other mutable stores resolve below the fixed candidate with no merge/fallback | `ROLLBACK_REQUIRED` |
| 4 `loopback-listener` | Resolved absolute `ssh.exe`; strict SSH argv plus installed `/usr/bin/ss` atomic filter argv | `ListenerSetV1`; exact approved loopback sockets on port 3080 and no nonloopback socket | `ROLLBACK_REQUIRED` |
| 5 `http-health` | Resolved absolute `ssh.exe`; strict SSH argv plus installed `/usr/bin/curl` bounded argv for `http://127.0.0.1:3080/` | `HttpStatusV1`; exit 0 and exact accepted status from packet | `ROLLBACK_REQUIRED` |
| 6 `ufw` | Resolved absolute `ssh.exe`; strict SSH argv plus installed `/usr/sbin/ufw status verbose` | `UfwPolicyV1`; active, exact baseline defaults/rules, no TCP 3080 allowance | `ROLLBACK_REQUIRED` |
| 7 `direct-lan-denial` | `PowerShell::.NET-TcpClient`; argv is exact address, `3080`, and bounded millisecond timeout | `TcpDeniedV1`; connection denied/timed out within bound | `ROLLBACK_REQUIRED` |
| 8 `route-fallback-policy` | Resolved absolute `ssh.exe`; strict SSH argv plus selector-proven safe route-status probe executable/argv | `RoutePolicyV1`; active route count `0`, automatic fallback `false`, no provider/model selection | `ROLLBACK_REQUIRED` |
| 9 `candidate-storage` | Resolved absolute `ssh.exe`; strict SSH argv plus the reviewed candidate metadata/ACL/link/mount validator executable/argv | `CandidateStorageV1`; exact root, `dsh:dsh`, 0700 directories, 0600-or-narrower regular files, no links/broad ACL/unexpected mount | `ROLLBACK_REQUIRED` |
| 10 `old-root-detachment` | Resolved absolute `ssh.exe`; strict SSH argv plus installed `/usr/bin/stat` root-only argv | `OldRootDetachedV1`; exact post-stop root `lstat` match plus check 3 proves no effective store below it | `ROLLBACK_REQUIRED` |
| 11 `no-credential-mutation` | `PowerShell::OperationLedger`; argv is the current packet/workflow ID | `NoCredentialMutationV1`; zero old-tree write/move/delete and zero credential/OAuth/provider/inference/route mutation | `ROLLBACK_REQUIRED` |

Parsers consume raw output only in memory, reject unknown fields/extra lines, and persist only named safe fields and verdicts. Raw stdout/stderr, service environments, matching secret text, credential-shaped data, and exception payloads are never logged or copied into scratch/evidence output.

The mutation arrays are also exact and ordered:

| Structure / step | Executable and atomic argv | Timeout / parser / accepted output | Transition |
| --- | --- | --- | --- |
| `pointerMutation.steps[0]` `install-pointer` | Resolved absolute `ssh.exe`; strict SSH argv, `sudo -n`, proven absolute `install`, `-o root -g root -m 0644 /dev/stdin`, fixed drop-in path; reviewed bytes supplied on stdin | 30 seconds; `DropInReceiptV1`; exit 0, exact SHA-256, `root:root`, `0644`, regular file, link count 1 | `POINTER_WRITTEN`; otherwise `ROLLBACK_REQUIRED` |
| `pointerMutation.steps[1]` `reload-pointer` | Resolved absolute `ssh.exe`; strict SSH argv, `sudo -n`, `/usr/bin/systemctl daemon-reload` | 30 seconds; `ExitCodeV1`; exit 0 | `POINTER_APPLIED`; otherwise `ROLLBACK_REQUIRED` |
| `rollbackMutation.steps[0]` `remove-new-pointer` | Resolved absolute `ssh.exe`; strict SSH argv, `sudo -n`, proven absolute `rm`, `-f --`, fixed drop-in path | 30 seconds; `AbsentPathV1`; exit 0 and exact path absent | `ROLLBACK_POINTER_REMOVED`; otherwise `ROLLBACK_FAILED` |
| `rollbackMutation.steps[1]` `reload-prior-pointer` | Resolved absolute `ssh.exe`; strict SSH argv, `sudo -n`, `/usr/bin/systemctl daemon-reload` | 30 seconds; `ExitCodeV1`; exit 0 | `ROLLBACK_RELOADED`; otherwise `ROLLBACK_FAILED` |
| `rollbackMutation.steps[2]` `start-prior-service` | Resolved absolute `ssh.exe`; strict SSH argv, `sudo -n`, `/usr/bin/systemctl start deepseek-harness.service` | 60 seconds; `ExitCodeV1`; exit 0 | `ROLLBACK_STARTED`; otherwise `ROLLBACK_FAILED` |
| `rollbackMutation.steps[3]` `verify-prior-baseline` | Resolved absolute `ssh.exe`; strict SSH argv plus `/usr/bin/systemctl show deepseek-harness.service` exact allowlist; followed by fixed read-only baseline check handlers | 60 seconds; `PriorBaselineV1`; exact pre-packet service/unit/listener/HTTP/UFW/direct-denial state restored | `ROLLED_BACK`; otherwise `ROLLBACK_FAILED` |

The stop and candidate-start commands are separate complete `commandSpec` records in the controller's state sequence: proven `sudo -n /usr/bin/systemctl stop deepseek-harness.service` accepts only confirmed inactive state and transitions to `SERVICE_STOPPED`; proven `sudo -n /usr/bin/systemctl start deepseek-harness.service` accepts exit 0 and transitions to `CANDIDATE_RUNNING`. Either failure enters the single rollback sequence. No command field contains a shell program, redirection, expansion, pipeline, or concatenated packet text.

The packet stores command identifiers and structured argv, not shell snippets. Every executable and argument is a separate JSON array item; the validator rejects shell metacharacters, redirections, pipelines, command substitutions, broad paths, and unlisted mutations. The fixed controller constructs its own safe command sequence from these structured fields and never calls `Invoke-Expression`, `bash -c` with packet text, or an unreviewed wrapper.

- [ ] **Step 3: Implement the bounded live controller**

The live `-Execute` path must first complete the controller-owned mode, derived-reply, reply-hash, and bounded-timestamp validation with zero SSH commands on failure. It then requires the accepted packet digest and approval metadata, and only then:

1. Revalidate repository/VM/SSH identities, packet expiry/digests/reviews, service active baseline, candidate static state, tunnel assumption, UFW baseline, direct-LAN denial, and absence of the new drop-in.
2. Confirm the prior selector metadata and exact rollback are observable without reading profile content.
3. Stop `deepseek-harness.service` once and require confirmed inactive state.
4. Only after confirmed stop, capture exactly one old-root `lstat` record: path, object type, owner, group, mode, link status. Do not traverse children, follow links, read content, hash, count, or size the tree.
5. Write the reviewed nonsecret drop-in bytes to the fixed absent path as `root:root` `0644`, verify its SHA-256, and run one `systemctl daemon-reload`.
6. Start `deepseek-harness.service` once.
7. Run the eleven ordered checks. The effective-profile probe must resolve credentials, settings, plugins, sessions/state, and all other mutable stores below the candidate without merge/fallback.
8. Accept only eleven `PASS` results. Any failure, ambiguity, timeout, empty result, or `WARN` enters the one rollback sequence.
9. Rollback removes only the new drop-in, reloads once, starts once, and verifies the exact prior baseline. Failure is terminal `ROLLBACK_FAILED`; no retry or repair follows.
10. Write a value-suppressed scratch result even when the command exits nonzero. No credential/provider/OAuth/inference action exists in the controller.

- [ ] **Step 4: Validate the packet and controller without cutover**

Run:

```powershell
$record = Get-Content -Raw 'docs/evidence/vm105-profile-pointer.json' | ConvertFrom-Json
$packetDigest = [string]$record.cutoverPacket.packetDigest
if ($packetDigest -notmatch '^[A-F0-9]{64}$') { throw 'packetDigest is absent or malformed' }
./scripts/Invoke-VM105ProfileCutover.ps1 `
  -ApprovedPacketDigest $packetDigest `
  -SelfTest
if ($LASTEXITCODE -ne 0) { throw 'Cutover controller self-test failed' }

./scripts/Test-VM105ProfilePointer.ps1 -EvidencePath 'docs/evidence/vm105-profile-pointer.json' -Stage CutoverPacket
if ($LASTEXITCODE -ne 0) { throw 'Cutover packet validation failed' }

./scripts/Invoke-VM105ProfileCutover.ps1 `
  -ApprovedPacketDigest $packetDigest `
  -DryRun
git diff --check -- 'docs/evidence/vm105-profile-pointer.json' 'scripts/Invoke-VM105ProfileCutover.ps1'
```

Expected: self-tests and packet validator exit 0; dry-run shows only allowlisted identifiers/targets and performs zero mutations; `cutoverExecution` remains `null`; `credentialGate.status` remains `NOT_ELIGIBLE`.

- [ ] **Step 5: Obtain independent packet/controller acceptance and commit**

Give a fresh independent reviewer the approved spec, evidence JSON, both prerequisite digests/reviews, controller, self-test output, dry-run output, and exact diff. The reviewer must verify the packet bytes, unique absent drop-in target, structured-argv safety, one switch/no retry/one rollback limit, post-stop old-root `lstat` ordering, all eleven checks, and the absence of credential actions. Record acceptance against the exact `packetDigest`; any edit invalidates acceptance and requires a new digest and review.

Run Task 3 validation again, then commit only:

```powershell
git add -- 'scripts/Invoke-VM105ProfileCutover.ps1' 'docs/evidence/vm105-profile-pointer.json'
git -c user.name='Codex' -c user.email='codex@local' commit -m 'feat: prepare VM105 profile cutover packet'
```

Stop here. Task 3 does not authorize or execute a stop, pointer write, daemon reload, start, or credential action.

### Task 4: Gate and execute one bounded cutover attempt

**Files:**
- Modify: `docs/evidence/vm105-profile-pointer.json`
- Runtime write after approval only: `/etc/systemd/system/deepseek-harness.service.d/90-vm105-provider-profile.conf`
- Scratch output, never staged: `.superpowers/sdd/vm105-profile-pointer/cutover-result.json`

**Interfaces:**
- Consumes: unexpired independently accepted `packetDigest` and a new explicit owner reply naming that digest
- Produces: `cutoverExecution.terminalState` equal to `SWITCH_ACCEPTED`, `ROLLED_BACK`, or `ROLLBACK_FAILED`
- Gate: current design approval and standing development recommendations do not release this task

- [ ] **Step 1: Revalidate the packet before asking for authority**

Run the selector, candidate, and cutover-packet stages again plus controller `-DryRun`. Recheck VM identity, service state, candidate metadata, local tunnel, UFW, direct-LAN denial, packet expiry, and exact absence of the new drop-in. Any drift sets `overallVerdict` to `BLOCKED`, invalidates the packet, and stops without asking for cutover approval.

- [ ] **Step 2: Stop at the blocking action-time cutover gate**

Present the owner with the exact packet digest, fixed drop-in target, candidate path, expected brief outage, one switch attempt, one automatic rollback sequence, eleven checks, residual `ROLLBACK_FAILED` risk, zero provider cost, and explicit exclusion of credentials/routes/inference. Use the project-required headings. Obtain the exact required reply from the controller's validated dry-run output; do not compose it separately:

```powershell
$record = Get-Content -Raw 'docs/evidence/vm105-profile-pointer.json' | ConvertFrom-Json
$packetDigest = [string]$record.cutoverPacket.packetDigest
./scripts/Invoke-VM105ProfileCutover.ps1 -ApprovedPacketDigest $packetDigest -DryRun
```

Expected: mutation-free output includes one controller-derived approval sentence containing the current 64-hex digest, one bounded switch attempt, one automatic rollback sequence, and `No credentials.`, plus only safe command identifiers/targets.

Silence, previous specification approval, standing routine preapproval, an automated marker, or a reply naming a different digest does not authorize execution. Do not manufacture approval metadata. If approval is absent, stop with the current service active.

- [ ] **Step 3: Execute the accepted packet once**

Hash the exact owner reply locally without recording its text, record the safe timestamp and digest, and run:

```powershell
$record = Get-Content -Raw 'docs/evidence/vm105-profile-pointer.json' | ConvertFrom-Json
$packetDigest = [string]$record.cutoverPacket.packetDigest
if ($ownerReply -ne "Approve cutover packet $packetDigest for one bounded switch attempt and one automatic rollback sequence. No credentials.") { throw 'Exact action-time approval is absent' }
$approvalTimestamp = $ownerReplyReceivedAt.ToUniversalTime().ToString('o')
$approvalTextSha256 = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes($ownerReply)))
./scripts/Invoke-VM105ProfileCutover.ps1 `
  -EvidencePath 'docs/evidence/vm105-profile-pointer.json' `
  -ApprovedPacketDigest $packetDigest `
  -OwnerReply $ownerReply `
  -ApprovalTimestamp $approvalTimestamp `
  -ApprovalTextSha256 $approvalTextSha256 `
  -SshTarget 'dsh@192.168.1.139' `
  -SshKey 'C:\Users\chatc\.ssh\codex-prox01-vms-ed25519' `
  -ResultPath '.superpowers/sdd/vm105-profile-pointer/cutover-result.json' `
  -Execute
```

`$ownerReply` is the exact user response captured by the executor without alteration, and `$ownerReplyReceivedAt` is recorded immediately when that response arrives; do not synthesize either value. The controller independently derives the required text, recomputes the hash, and rejects timestamps outside its bounded freshness window before opening SSH. Do not add a second execution call. Expected terminal results:

- `SWITCH_ACCEPTED`: all eleven checks passed and the service uses the candidate.
- `ROLLED_BACK`: a cutover check failed, the new pointer was removed, and the original service baseline was restored.
- `ROLLBACK_FAILED`: restoration could not be proven; stop all mutation and report an incident immediately.

- [ ] **Step 4: Import only safe result fields and independently verify live state**

Copy the scratch result's schema-approved safe fields into `cutoverExecution`; never copy raw stdout/stderr. Recompute the packet digest and require it unchanged. Compute `cutoverExecution.resultDigest` immediately from the canonical execution result excluding `resultDigest` and `review`. A fresh independent read-only reviewer re-runs identity/service/listener/HTTP/UFW/direct-denial checks and either effective candidate-path checks after `SWITCH_ACCEPTED` or prior-baseline checks after `ROLLED_BACK`. The reviewer may inspect only candidate content through the value-suppressing validator and old-root root-only `lstat` metadata.

Record `cutoverExecution.review.status: ACCEPTED`, reviewer identity, time, zero unresolved findings, and `reviewedDigest` exactly equal to the pre-review `resultDigest`. Any result edit invalidates the review: recompute `resultDigest`, return review to `PENDING`, and obtain a new independent review before commit.

Run:

```powershell
$stage = if ((Get-Content -Raw 'docs/evidence/vm105-profile-pointer.json' | ConvertFrom-Json).cutoverExecution.terminalState -eq 'SWITCH_ACCEPTED') { 'PostCutover' } else { 'Rollback' }
./scripts/Test-VM105ProfilePointer.ps1 -EvidencePath 'docs/evidence/vm105-profile-pointer.json' -Stage $stage
if ($LASTEXITCODE -ne 0) { throw 'Cutover result validation failed' }
git diff --check -- 'docs/evidence/vm105-profile-pointer.json'
```

Expected: exit 0 for `SWITCH_ACCEPTED` or proven `ROLLED_BACK`; current recomputed `resultDigest` equals `cutoverExecution.review.reviewedDigest`. A `ROLLBACK_FAILED` result is intentionally not normalized into success; preserve evidence, stop, and escalate without a commit claiming acceptance.

- [ ] **Step 5: Commit the bounded result without claiming credentials**

After independent review of a `SWITCH_ACCEPTED` or `ROLLED_BACK` result, commit only:

```powershell
git add -- 'docs/evidence/vm105-profile-pointer.json'
git -c user.name='Codex' -c user.email='codex@local' commit -m 'ops: record VM105 profile cutover result'
```

Do not delete the old profile or candidate, retire the prior pointer metadata, create credentials, initiate OAuth, enable routes, run inference, or repeat a failed cutover.

### Task 5: Close profile-pointer evidence and stop at the credential gate

**Files:**
- Modify: `docs/evidence/vm105-profile-pointer.json`

**Interfaces:**
- Consumes: independently reviewed Task 4 terminal result
- Produces: final profile-pointer evidence verdict and a credential-gate state; it produces no credential or OAuth state

- [ ] **Step 1: Record the final safe profile-pointer outcome**

For `SWITCH_ACCEPTED`, set `overallVerdict` to `SWITCH_ACCEPTED`; record selector detachment from the old root, eleven `PASS` checks, empty old-tree mutation ledger, retained old profile, runtime service identity/listener/network facts, and provider/credential/native-OAuth/inference verdicts as `NOT PROVEN`. Set:

```json
{
  "status": "REQUIRED_NOT_REQUESTED",
  "reason": "Profile switch accepted; Phase 3 owner credential gate remains separate"
}
```

For `ROLLED_BACK`, set `overallVerdict` to `ROLLED_BACK`, keep `credentialGate.status` as `NOT_ELIGIBLE`, record the exact failed cutover check and restored baseline, and stop. For `ROLLBACK_FAILED`, preserve `ROLLBACK_FAILED`, do not amend evidence into a normal completion, and escalate.

- [ ] **Step 2: Run the final secret and consistency checks**

Run:

```powershell
./scripts/Test-VM105ProfilePointer.ps1 -SelfTest
if ($LASTEXITCODE -ne 0) { throw 'Profile-pointer self-test failed' }

$record = Get-Content -Raw 'docs/evidence/vm105-profile-pointer.json' | ConvertFrom-Json
$stage = if ($record.cutoverExecution.terminalState -eq 'SWITCH_ACCEPTED') { 'PostCutover' } else { 'Rollback' }
./scripts/Test-VM105ProfilePointer.ps1 -EvidencePath 'docs/evidence/vm105-profile-pointer.json' -Stage $stage
if ($LASTEXITCODE -ne 0) { throw 'Final profile-pointer evidence validation failed' }

./scripts/Test-Phase03Evidence.ps1 -Stage Network
if ($LASTEXITCODE -ne 0) { throw 'Existing Phase 3 evidence scan failed' }
git diff --check -- 'docs/evidence/vm105-profile-pointer.json'
```

Expected: exit 0; no sensitive value; packet and prerequisite digests remain stable; successful cutover has eleven `PASS` checks and an empty old-tree mutation ledger; provider routes remain zero; fallback remains disabled; credentials/OAuth/inference remain `NOT PROVEN`.

- [ ] **Step 3: Verify the Task 4 digest-backed review still governs the result**

Recompute the canonical Task 4 execution result without `resultDigest` and `review`; require exact equality with both `cutoverExecution.resultDigest` and `cutoverExecution.review.reviewedDigest`, and require `review.status: ACCEPTED` with zero unresolved findings. Confirm the closing edits changed only `overallVerdict` and `credentialGate`, not the Task 4 result, packet, selector, candidate, mutation ledger, or live-state claims. If any governed field changed, return to Task 4 for a new digest-backed independent review before closing.

- [ ] **Step 4: Commit final evidence and stop before credentials**

```powershell
git add -- 'docs/evidence/vm105-profile-pointer.json'
git -c user.name='Codex' -c user.email='codex@local' commit -m 'docs: close VM105 profile pointer evidence'
```

If `credentialGate.status` is `REQUIRED_NOT_REQUESTED`, stop and hand control back to the existing Phase 3 credential workflow. This implementation plan never creates API access, opens a login/consent flow, types a credential, inspects a secret, enables a provider route, runs inference, or treats standing development preapproval as the credential gate.

## End-to-End Completion Conditions

- Task 1 may complete safely as `BLOCKED`; Tasks 2-5 then do not run.
- Task 2 may complete as `CANDIDATE_STATIC_PASS` while runtime, provider, credential, and native OAuth behavior remain `NOT PROVEN`.
- Task 3 produces an exact independently accepted packet but no live service mutation.
- Task 4 cannot run without a fresh owner reply naming the current packet digest.
- One approved cutover produces only `SWITCH_ACCEPTED`, proven `ROLLED_BACK`, or terminal `ROLLBACK_FAILED`; no retry follows.
- Task 5 stops at `REQUIRED_NOT_REQUESTED` before every credential-bearing action.
- The current profile remains untouched and retained; the candidate and drop-in are never used as authority to delete it.
