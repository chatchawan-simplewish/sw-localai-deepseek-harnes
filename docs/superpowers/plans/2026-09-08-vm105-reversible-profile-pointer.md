# VM105 Secret-Free Profile Preparation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove or block the installed whole-profile selector, prepare the fixed secret-free candidate only after selector proof, and hand off independently reviewed cutover requirements without building or executing cutover.

**Architecture:** One typed JSON record carries sanitized selector proof, read-only future-cutover prerequisite status, the candidate blueprint, and static preparation results. A dependency-free validator enforces proof-source separation and fail-closed policy; a bounded initializer can write only the fixed candidate tree and can never operate the service or systemd. Cutover code, root mutation commands, maintenance restart, post-cutover evidence, and credential work are deliberately excluded and require a separate follow-up plan after this preparation succeeds and fresh cutover authority is granted.

**Tech Stack:** PowerShell 7 and .NET standard library, Windows OpenSSH client, POSIX shell/coreutils already installed on VM105, JSON, Markdown, Git.

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

The two controller-related constraints above remain requirements for the separate cutover plan. This preparation plan does not create a controller or exercise either constraint.

---

## Scope Decomposition

This plan implements only the currently authorized, independently testable preparation slice:

1. Read-only installed-version selector discovery and read-only future-cutover prerequisite observations.
2. Fixed-path secret-free candidate creation and static validation, gated only by accepted whole-profile selector proof.
3. Independent preparation closeout and a non-executable requirements handoff.

The approved design's future service-pointer switch remains unchanged, but belongs to a separate plan. That follow-up must define and review the exact cutover packet/controller, obtain fresh action-time authority, perform the bounded maintenance restart, collect post-cutover evidence, and then stop at the existing credential gate. Nothing in this plan grants those authorities.

## Planned File Map

| Path | Responsibility | Created in |
| --- | --- | --- |
| `docs/evidence/vm105-profile-pointer-preparation.json` | The only new preparation evidence record: typed selector proof, sanitized unit facts, read-only privilege/drop-in-directory status, candidate blueprint/result, and operation ledger | Task 1; updated Tasks 2-3 |
| `scripts/Test-VM105ProfilePreparation.ps1` | Dependency-free schema, proof-source, digest, stage, and value-suppressing safety validator with synthetic self-tests | Task 1 |
| `scripts/Initialize-VM105ProviderProfile.ps1` | Bounded preparer that consumes an accepted selector digest, writes only the fixed candidate tree, runs static checks, and rejects every service/systemd operation | Task 2 |
| `docs/handoffs/2026-09-08-vm105-profile-cutover-requirements.md` | Human-readable, non-executable readiness handoff for a separately authorized cutover plan | Task 3 |

No existing profile/evidence file, service unit, systemd drop-in, sudoers rule, firewall rule, package, provider route, credential store, OAuth state, or browser state is modified. This plan never stops, starts, restarts, or reloads a service and never writes below `/etc`.

## Shared Preparation Contract

`docs/evidence/vm105-profile-pointer-preparation.json` has `schemaVersion: 1` and these exact top-level properties:

```json
{
  "schemaVersion": 1,
  "workflowId": "vm105-profile-preparation",
  "target": {},
  "overallVerdict": "BLOCKED",
  "selectorDiscovery": {},
  "cutoverPrerequisites": {},
  "candidatePreparation": null,
  "closeout": null,
  "operationLedger": []
}
```

Exact interfaces:

- `target`: `hostname`, `address`, `sshHostKeyIdentity`, `service`, `serviceUser`, `serviceGroup`, `candidateRoot`, `listenerHost`, `listenerPort`, `futureDropInDirectory`, `futureDropInFile`.
- `installedSourceRef`: `sourceClass: "installed-source"`, `path`, `sha256`, `lineStart`, `lineEnd`, `claim`; `path` must be the verified wrapper, fixed entrypoint, or a package-owned help/docs/source file below `/opt/deepseek-harness`.
- `sanitizedUnitRef`: `sourceClass: "sanitized-unit"`, `observationId`, `capturedAt`, `propertyNames`, `valuesSha256`, `claim`; only explicitly allowlisted nonsecret effective-unit properties are observed, and full environment/log output is forbidden.
- `privilegeReceiptRef`: `sourceClass: "privilege-receipt"`, `operationId`, `capturedAt`, `executable`, `argvSha256`, `noninteractive`, `allowed`, `claim`; it records a read-only `sudo -n -l` verdict and never raw policy output.
- `selectorDiscovery`: `capturedAt`, `installedVersion`, `verdict`, `blockers`, `installedEntrypoint`, `baseline`, `selector`, `candidateBlueprint`, `selectorDigest`, `review`.
- `installedEntrypoint`: `wrapperPath`, `wrapperOwner`, `wrapperGroup`, `wrapperMode`, `wrapperSha256`, `entrypointPath`, `entrypointOwner`, `entrypointGroup`, `entrypointMode`, `packageRoot`, `packageName`, `packageVersion`, `proofRefs`.
- `selector`: `name`, `precedence`, `absoluteCandidateValue`, `futureUnitSelectorLines`, `effectiveProfileProbe`, `proof`.
- `selector.proof`: `absolutePath`, `precedence`, `fullProfileScope`, `nonMerge`, `serviceCompatibility`; semantic claims use `installedSourceRef` only. `serviceCompatibility` requires installed-source proof and may additionally use narrowly scoped `sanitizedUnitRef`. `fullProfileScope` has separate installed-source proofs for credentials, settings, plugins, sessions/state, and other mutable stores.
- `candidateBlueprint`: `directories`, `files`, `policyAssertions`, `staticValidation`; every directory/file has a safe relative path, octal mode, and installed-source provenance. Files additionally have exact `contentLines` and SHA-256 over UTF-8 bytes joined by LF with one terminal LF.
- `cutoverPrerequisites`: `observedAt`, `verdict`, `privilegeSeam`, `dropInDirectory`, `blockers`. This status never gates candidate creation and never authorizes cutover.
- `privilegeSeam`: `verdict`, `receipts`; receipts cover only read-only proof of whether existing narrow permissions would allow future fixed-file install/removal and exact `systemctl stop`, `start`, `daemon-reload`, and status operations.
- `dropInDirectory`: `path`, `exists`, `realDirectory`, `owner`, `group`, `mode`, `linkStatus`, `broadAcl`, `unexpectedMount`, `verdict`.
- `candidatePreparation`: `selectorDigest`, `candidateDigest`, `startedAt`, `finishedAt`, `verdict`, `createdPaths`, `metadataChecks`, `staticChecks`, `serviceUnchangedChecks`, `runtimeVerdict`, `blockers`, `review`.
- `closeout`: `closedAt`, `verdict`, `selectorDigest`, `candidateDigest`, `cutoverPrerequisiteVerdict`, `handoffPath`, `handoffSha256`, `review`.
- `review`: `status`, `reviewedAt`, `reviewer`, `reviewedDigest`, `findings`; status is `PENDING`, `ACCEPTED`, or `REJECTED`.
- `operationLedger` entry: `at`, `actor`, `operation`, `target`, `result`, `secretObserved`; it contains no raw command output or file contents.

Reference classes are not interchangeable. The validator rejects an unknown `sourceClass`, a `privilegeReceiptRef` or `sanitizedUnitRef` used for selector semantics, an `installedSourceRef` used as a privilege receipt, a unit reference used for whole-profile/non-merge proof, and any reference whose fields do not exactly match its class schema.

`selectorDigest`, `candidateDigest`, and closeout review digests cover nonsecret canonical JSON only: recursively ordinal-sort object keys, preserve array order, encode UTF-8 without BOM, and omit insignificant whitespace. Each digest excludes itself and its attached review; earlier-stage digests exclude later-stage sections.

### Task 1: Discover or block the installed whole-profile selector

**Files:**
- Create: `docs/evidence/vm105-profile-pointer-preparation.json`
- Create: `scripts/Test-VM105ProfilePreparation.ps1`

**Interfaces:**
- Consumes: installed Harness `0.1.1-rc.2` wrapper/entrypoint/package sources and narrowly sanitized effective-unit observations
- Produces: accepted `selectorDigest` with a complete secret-free candidate blueprint, or a reviewed `BLOCKED` record with candidate fields absent
- Produces: independent read-only `cutoverPrerequisites.verdict`; this observation neither gates Task 2 nor grants cutover authority
- Produces: `Test-VM105ProfilePreparation.ps1 -EvidencePath [string] -Stage Selector|Candidate|Closeout [-SelfTest]`

- [ ] **Step 1: Write the typed validator and failing synthetic tests**

Use this public interface and no external modules:

```powershell
[CmdletBinding()]
param(
    [string]$EvidencePath = 'docs/evidence/vm105-profile-pointer-preparation.json',
    [ValidateSet('Selector','Candidate','Closeout')]
    [string]$Stage = 'Selector',
    [switch]$SelfTest
)
```

Implement canonical JSON, uppercase SHA-256, exact schema checks, and a value-suppressing scanner. The scanner reports only relative filename, one-based line, and category; it never emits matching text. Reject nonempty assignments for `key`, `api_key`, `token`, `secret`, `password`, `client_secret`, authorization headers, PEM private keys, `sk-`, `sk-or-`, `sess-`, and raw or encoded OAuth `code`, `state`, `access_token`, `refresh_token`, and `id_token` values. Empty values and prose naming a field are allowed.

`-SelfTest` must cover one positive synthetic record and these exact rejections:

1. Selector `PASS` with missing absolute-path, precedence, non-merge, service-compatibility, or any of the five full-profile store proofs.
2. Selector semantic proof containing `sanitized-unit`, `privilege-receipt`, unknown, or structurally mixed reference data.
3. Privilege receipts placed outside `cutoverPrerequisites.privilegeSeam`, or an installed/unit reference substituted for a privilege receipt.
4. Installed reference outside the verified wrapper/entrypoint/package root, a source digest/line-range mismatch, or a child path below `/home/dsh/.dsh`.
5. Wrapper that is not a regular root-owned non-writable installed file, resolves outside `/opt/deepseek-harness`, or contains more than one fixed launch handoff.
6. Candidate root other than `/home/dsh/.dsh-profiles/vm105-provider-v1`, relative path traversal/rooting/duplication, directory mode other than `0700`, or file mode wider than `0600`.
7. Blueprint with provider/model selection, active route count above zero, fallback enabled, OAuth state, Hermes reference, or secret-shaped content.
8. Digest mismatch or review digest mismatch.
9. Candidate `PASS` with runtime verdict other than `NOT PROVEN`, service/systemd operation, path outside the candidate root, or a post-create failure followed by another write/cleanup/repair.
10. Closeout handoff containing executable/argv/command/script fields or implying cutover/credential authority.
11. Suppressed scanner output accidentally containing the synthetic secret value.

Run the self-test before completing validator logic and require a nonzero assertion for an unimplemented rejection. Implement the minimum logic, rerun, and require exit 0 with case counts and no synthetic value in output.

- [ ] **Step 2: Revalidate repository, VM, service, listener, and wrapper metadata read-only**

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
& ssh.exe @sshArgs -- "set -eu; hostname; id -un; id -gn; /usr/local/bin/dsh --version; systemctl is-active deepseek-harness.service; systemctl show deepseek-harness.service -p User -p Group -p ExecStart -p WorkingDirectory -p UMask -p FragmentPath -p DropInPaths -p ActiveState -p SubState -p Result -p NRestarts; ss -lntH '( sport = :3080 )'; stat -c '%n|%F|%U|%G|%a|%h' -- /usr/local/bin/dsh"
if ($LASTEXITCODE -ne 0) { throw 'Read-only baseline failed' }
```

Expected: repository/branch match; hostname `deepseek-harness-01`; caller/group `dsh`; version `0.1.1-rc.2`; service active; listener loopback-only on port 3080; wrapper a safe regular installed file. Do not inspect the old profile root or children, service environments, logs, or secret-bearing configuration.

- [ ] **Step 3: Verify the wrapper and discover only from its fixed installed entrypoint**

After capturing owner/mode/SHA-256, read exactly `/usr/local/bin/dsh` as data. Require one fixed absolute entrypoint below `/opt/deepseek-harness`; reject command substitution, environment-derived/relative/fallback paths, eval, extra executable branches, writable owner/mode, or a target outside that root. Verify the extracted entrypoint is a regular installed/package-owned safe file. Walk upward only inside `/opt/deepseek-harness` to its owning `package.json`, verify package name/version, and record digests before reading package help/docs/schema/state-location sources. Do not follow links outside the package root, run network package commands, or install anything.

Build selector semantic proof exclusively from `installedSourceRef` records. Prove exact selector name/precedence, absolute-path support, non-merge/non-inherit/non-migrate behavior, and full-profile coverage for credentials, settings, plugins, sessions/state, and every other mutable store. Service compatibility requires installed-source proof; a `sanitizedUnitRef` may additionally establish that the unchanged installed command/user can consume the selector. Query only the proven selector key from effective unit metadata and suppress all other environment values.

- [ ] **Step 4: Observe future-cutover prerequisites without changing them**

Resolve existing absolute installed executables and use bounded `sudo -n -l --` permission queries that execute no privileged operation. Check only whether a pre-existing noninteractive seam would permit future fixed drop-in file install/removal and exact `systemctl stop deepseek-harness.service`, `start`, `daemon-reload`, and status operations. Record one typed `privilegeReceiptRef` per operation with allow/deny and hashed argv; suppress raw sudo policy output. Never edit sudoers or invent a broader command.

Read only metadata for `/etc/systemd/system/deepseek-harness.service.d`: existence, real-directory/link status, owner/group, mode, ACL broadness, and mount relationship. `cutoverPrerequisites.verdict` is `PASS` only when all narrow privilege receipts are allowed/noninteractive and the directory already exists as `root:root` `0755`, real/non-link, without broad ACL or unexpected mount. Otherwise record exact `BLOCKED` reasons. Do not create or repair the directory and do not write a drop-in.

- [ ] **Step 5: Emit a reviewed PASS or BLOCKED selector record**

For selector `PASS`, create `candidateBlueprint` only from installed defaults and the approved fixed settings. Its policy must be exactly:

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

Every blueprint directory/file has exact safe relative path, mode, installed-source provenance, and file content/digest. No provider/account/model/credential/OAuth/callback value is present. If selector proof is missing or ambiguous, set selector and blueprint to `null`, verdict/overall verdict to `BLOCKED`, list exact safe blockers, and leave Task 2 data absent. `cutoverPrerequisites` may independently be `PASS` or `BLOCKED`; its status does not change selector semantics.

Run:

```powershell
./scripts/Test-VM105ProfilePreparation.ps1 -SelfTest
if ($LASTEXITCODE -ne 0) { throw 'Preparation validator self-test failed' }
./scripts/Test-VM105ProfilePreparation.ps1 -EvidencePath 'docs/evidence/vm105-profile-pointer-preparation.json' -Stage Selector
if ($LASTEXITCODE -ne 0) { throw 'Selector evidence validation failed' }
./scripts/Test-Phase03Evidence.ps1 -Stage Network
if ($LASTEXITCODE -ne 0) { throw 'Existing Phase 3 evidence scan failed' }
git diff --check -- 'docs/evidence/vm105-profile-pointer-preparation.json' 'scripts/Test-VM105ProfilePreparation.ps1'
```

Expected: exit 0. A fresh independent reviewer verifies every installed semantic proof, reference-class boundary, sanitized unit claim, privilege receipt, directory observation, blueprint, and blocker. Record acceptance against `selectorDigest`, rerun all checks, and commit only:

```powershell
git add -- 'docs/evidence/vm105-profile-pointer-preparation.json' 'scripts/Test-VM105ProfilePreparation.ps1'
git -c user.name='Codex' -c user.email='codex@local' commit -m 'feat: record VM105 profile selector proof'
```

If selector verdict is `BLOCKED`, stop the plan. VM105 remains unchanged. A blocked future-cutover prerequisite alone does not block secret-free candidate preparation when the selector itself passed.

### Task 2: Create and statically validate the fixed secret-free candidate

**Files:**
- Create: `scripts/Initialize-VM105ProviderProfile.ps1`
- Modify: `docs/evidence/vm105-profile-pointer-preparation.json`

**Interfaces:**
- Consumes: independently accepted `selectorDigest` and exact `candidateBlueprint`
- Produces: `Initialize-VM105ProviderProfile.ps1 -EvidencePath [string] -AcceptedSelectorDigest [64-hex string] -SshTarget [user@host string] -SshKey [path string] -Prepare|-SelfTest`
- Produces: `candidatePreparation` and accepted `candidateDigest`; runtime remains `NOT PROVEN`

- [ ] **Step 1: Write initializer fail-closed tests before the write path**

Use this public interface:

```powershell
[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$EvidencePath = 'docs/evidence/vm105-profile-pointer-preparation.json',
    [Parameter(Mandatory)][string]$AcceptedSelectorDigest,
    [string]$SshTarget = 'dsh@192.168.1.139',
    [string]$SshKey = 'C:\Users\chatc\.ssh\codex-prox01-vms-ed25519',
    [switch]$Prepare,
    [switch]$SelfTest
)
```

Require exactly one mode. Before constructing SSH, reject a non-`PASS`/unaccepted selector, digest drift, unsafe or existing target/parent, blueprint/hash/path/mode/reference failure, provider/OAuth/secret content, and every destination outside `/home/dsh/.dsh-profiles/vm105-provider-v1`. Inject a fake SSH adapter only in self-test.

Fail each post-create operation in turn: parent creation, candidate-root creation, each directory/file write, metadata verification, static validation, secret scan, and unchanged-service/network check. After the first failure, assert `candidatePreparation.verdict: BLOCKED`, no later write, no cleanup/remove/repair, no service/systemd command, and no old-profile operation. Preserve candidate paths already created before failure for review. The positive synthetic run executes every planned candidate write once and zero service/systemd operations.

- [ ] **Step 2: Implement the fixed-path preparation lane**

The `-Prepare` path first reruns the Task 1 selector validator and revalidates VM/SSH identity, service active baseline, listener, selector digest, candidate ancestor metadata, and exact parent/target absence. It then uses one sequential `dsh` writer lane with `umask 077` to:

1. Create exactly `/home/dsh/.dsh-profiles` and `/home/dsh/.dsh-profiles/vm105-provider-v1` as real `dsh:dsh` mode `0700` directories.
2. Create only blueprint directories/files below the candidate; transfer reviewed secret-free file bytes through standard input without shell evaluation.
3. Verify local and VM-side nonsecret file SHA-256, `dsh:dsh` ownership, 0700 directories, 0600-or-narrower regular files, link count one, no symbolic links, no broad ACL, and no unexpected mount.
4. Run only the installed static-validation argv proved in the blueprint. If no safe static syntax validator exists, record syntax `NOT PROVEN`; if the uncertainty weakens loopback/zero-route/fallback isolation, set `BLOCKED`.
5. Read only newly created candidate files through the value-suppressing scanner.
6. Revalidate the existing service is active and unchanged, loopback-only, locally healthy, UFW unchanged with no TCP 3080 allowance, and direct LAN TCP 3080 denied.

The initializer has no service/systemd/sudo command and rejects such an operation in evidence or adapter input. It never starts Harness against the candidate. Any post-create failure records `BLOCKED`, stops remaining writes, and leaves the candidate untouched for review; it does not delete, repair, or normalize it.

- [ ] **Step 3: Run self-tests and prepare only after selector acceptance**

```powershell
$record = Get-Content -Raw 'docs/evidence/vm105-profile-pointer-preparation.json' | ConvertFrom-Json
$selectorDigest = [string]$record.selectorDiscovery.selectorDigest
if ($selectorDigest -notmatch '^[A-F0-9]{64}$') { throw 'Accepted selector digest missing' }
./scripts/Initialize-VM105ProviderProfile.ps1 -AcceptedSelectorDigest $selectorDigest -SelfTest
if ($LASTEXITCODE -ne 0) { throw 'Initializer self-test failed' }
./scripts/Test-VM105ProfilePreparation.ps1 -EvidencePath 'docs/evidence/vm105-profile-pointer-preparation.json' -Stage Selector
if ($LASTEXITCODE -ne 0) { throw 'Selector gate failed' }
./scripts/Initialize-VM105ProviderProfile.ps1 `
  -EvidencePath 'docs/evidence/vm105-profile-pointer-preparation.json' `
  -AcceptedSelectorDigest $selectorDigest `
  -SshTarget 'dsh@192.168.1.139' `
  -SshKey 'C:\Users\chatc\.ssh\codex-prox01-vms-ed25519' `
  -Prepare
```

Expected on success: only the fixed protected candidate tree exists; service/pointer/drop-in/sudoers/firewall/provider/credential/OAuth/route/VM-power state is unchanged. No inference or network provider call occurs.

- [ ] **Step 4: Record, validate, independently review, and commit candidate readiness**

Populate `candidatePreparation` from safe receipts only. Set `candidatePreparation.verdict: PASS` and `overallVerdict: CANDIDATE_STATIC_PASS` only if every static safety and unchanged-baseline check passes; set `runtimeVerdict: NOT PROVEN` unconditionally. On failure, set both applicable verdicts to `BLOCKED` and preserve the discrepancy.

Run:

```powershell
./scripts/Test-VM105ProfilePreparation.ps1 -EvidencePath 'docs/evidence/vm105-profile-pointer-preparation.json' -Stage Candidate
if ($LASTEXITCODE -ne 0) { throw 'Candidate evidence validation failed' }
./scripts/Test-Phase03Evidence.ps1 -Stage Network
if ($LASTEXITCODE -ne 0) { throw 'Existing Phase 3 evidence scan failed' }
git diff --check -- 'scripts/Initialize-VM105ProviderProfile.ps1' 'docs/evidence/vm105-profile-pointer-preparation.json'
```

A fresh independent reviewer checks exact-path confinement, selector digest, blueprint equivalence, ownership/modes/links/ACL/mounts, value suppression, zero service/systemd operations, no old-profile data flow, zero routes, fallback disabled, and runtime `NOT PROVEN`. Record acceptance against `candidateDigest`, rerun checks, and commit only:

```powershell
git add -- 'scripts/Initialize-VM105ProviderProfile.ps1' 'docs/evidence/vm105-profile-pointer-preparation.json'
git -c user.name='Codex' -c user.email='codex@local' commit -m 'feat: prepare VM105 secret-free profile'
```

Stop live preparation if candidate verdict or review is not accepted. Do not build or execute cutover as a recovery action.

### Task 3: Independently close preparation and hand off cutover requirements

**Files:**
- Create: `docs/handoffs/2026-09-08-vm105-profile-cutover-requirements.md`
- Modify: `docs/evidence/vm105-profile-pointer-preparation.json`

**Interfaces:**
- Consumes: accepted `selectorDigest`, accepted `candidateDigest`, candidate/static verdicts, and read-only cutover-prerequisite status
- Produces: a non-executable handoff with fixed targets, residual verdicts, and requirements for a separate cutover plan
- Produces: `closeout.verdict: PREPARATION_READY` or `BLOCKED`; it grants no live authority

- [ ] **Step 1: Write the non-executable requirements handoff**

Record:

- repository URL, branch, preparation commit SHAs, VM hostname/address, service identity, fixed candidate root, future drop-in directory, and fixed future drop-in file;
- accepted selector/candidate digests and review status;
- selector proof result and static candidate result;
- observed pre-existing narrow privilege-seam and drop-in-directory verdicts, including exact safe blockers but no root command bodies;
- runtime candidate behavior, effective selected-store paths, service startup, post-switch network posture, provider routes, credentials, native OAuth, inference, attribution, maintenance duration, and rollback behavior as `NOT PROVEN`;
- confirmation that current profile contents were never inspected/copied and no service/systemd/drop-in/firewall/provider/credential/OAuth mutation occurred; and
- the exact requirements a separately authorized cutover plan must consume: fresh baseline/drift checks, independently reviewed immutable packet, selector-only service delta, post-stop/pre-pointer old-root root-only `lstat`, one switch attempt, one automatic rollback sequence, eleven ordered acceptance checks, `ROLLBACK_FAILED` handling, retained old profile, then a separate credential gate.

The handoff must not contain shell/PowerShell commands, executable names paired with argv, a cutover controller interface, owner-approval reply text, or language claiming that preparation authorizes stop/start/reload/drop-in/credential actions.

- [ ] **Step 2: Populate closeout and validate the handoff boundary**

Compute the handoff's nonsecret SHA-256. Populate `closeout` with `PREPARATION_READY` only when selector and candidate verdicts/reviews/digests remain accepted; otherwise use `BLOCKED`. The validator's Closeout stage must reject executable command blocks, command/argv/controller schemas, action-time approval markers, credential authority, digest drift, omitted residual verdicts, or disagreement between handoff and JSON.

Run:

```powershell
./scripts/Test-VM105ProfilePreparation.ps1 -SelfTest
if ($LASTEXITCODE -ne 0) { throw 'Preparation validator self-test failed' }
./scripts/Test-VM105ProfilePreparation.ps1 -EvidencePath 'docs/evidence/vm105-profile-pointer-preparation.json' -Stage Closeout
if ($LASTEXITCODE -ne 0) { throw 'Preparation closeout validation failed' }
./scripts/Test-Phase03Evidence.ps1 -Stage Network
if ($LASTEXITCODE -ne 0) { throw 'Existing Phase 3 evidence scan failed' }
git diff --check -- 'docs/evidence/vm105-profile-pointer-preparation.json' 'docs/handoffs/2026-09-08-vm105-profile-cutover-requirements.md'
```

- [ ] **Step 3: Obtain independent closeout review**

Give a fresh reviewer the approved design, preparation evidence, validator, initializer, handoff, all task SHAs, and current read-only baseline. Require confirmation that proof classes cannot substitute for one another, selector/candidate digests match, old profile stayed opaque, candidate readiness is static only, cutover-prerequisite status is accurately bounded, the handoff is non-executable, and no current authority is widened.

Record closeout review against the canonical closeout digest, rerun Step 2 after the review edit, and reject any digest mismatch or unresolved finding.

- [ ] **Step 4: Commit exact closeout paths and stop**

```powershell
git add -- 'docs/evidence/vm105-profile-pointer-preparation.json' 'docs/handoffs/2026-09-08-vm105-profile-cutover-requirements.md'
git -c user.name='Codex' -c user.email='codex@local' commit -m 'docs: close VM105 profile preparation'
```

Stop after this commit. Do not create a cutover controller, exact root mutation packet, service restart flow, post-cutover evidence, provider credential, OAuth session, route, or inference test in this plan. The next plan starts only after preparation is independently accepted and fresh cutover authority is granted.

## Completion Conditions

- Selector discovery can finish safely as reviewed `BLOCKED`; no candidate is then created.
- Candidate creation occurs only with an accepted whole-profile selector digest and writes only the fixed secret-free tree.
- Candidate `PASS` means static eligibility only; runtime stays `NOT PROVEN`.
- Missing privilege or drop-in-directory prerequisites are recorded for the later cutover plan and never repaired here.
- Closeout produces one non-executable handoff and grants no cutover or credential authority.
- VM105's current service, profile, pointer, firewall, routes, credentials, OAuth state, and packages remain unchanged by Tasks 1 and 3; Task 2 can change only the fixed candidate tree.
