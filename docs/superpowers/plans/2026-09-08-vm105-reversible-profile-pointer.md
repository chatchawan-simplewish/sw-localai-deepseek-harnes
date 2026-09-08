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
- `sanitizedUnitRef`: `sourceClass: "sanitized-unit"`, `observationId`, `capturedAt`, `propertyAllowlist`, `observations`, `claim`; `propertyAllowlist` is a nonempty subset of `User`, `Group`, `ExecStart`, `WorkingDirectory`, `UMask`, `FragmentPath`, `DropInPaths`, `ActiveState`, `SubState`, `Result`, and `NRestarts`. Each observation is exactly `{ name, value }`, names are unique and in the declared allowlist, and the selector-specific observation may additionally contain only the already validated selector key plus its absolute nonsecret path. Full environment/log output is forbidden.
- `privilegeReceiptRef`: `sourceClass: "privilege-receipt"`, `operationId`, `capturedAt`, `queryUser`, `sudoPath`, `targetExecutable`, `targetArgv`, `noninteractive`, `result`, `exitCode`, `rawOutputStored`, `claim`; `queryUser` is `dsh`, paths are absolute installed paths, `targetArgv` is an atomic string array for one fixed future operation, `result` is `ALLOWED` or `DENIED`, `exitCode` is the observed integer, and `rawOutputStored` is always `false`.
- `selectorDiscovery`: `capturedAt`, `installedVersion`, `verdict`, `blockers`, `installedEntrypoint`, `baseline`, `selector`, `candidateBlueprint`, `selectorDigest`, `review`.
- `installedEntrypoint`: `wrapperPath`, `wrapperType`, `wrapperSymlink`, `wrapperOwner`, `wrapperGroup`, `wrapperMode`, `wrapperLinkCount`, `wrapperSha256`, `entrypointPath`, `entrypointType`, `entrypointSymlink`, `entrypointOwner`, `entrypointGroup`, `entrypointMode`, `entrypointLinkCount`, `entrypointSha256`, `packageRoot`, `packageName`, `packageVersion`, `proofRefs`. Both paths are absolute regular files, both symlink flags are `false`, wrapper owner/group are `root:root`, link counts are `1`, neither mode is group/world writable, and `packageRoot` is an absolute ancestor of `entrypointPath` below `/opt/deepseek-harness`.
- `selectorDiscovery.baseline`: `repositoryOrigin`, `branch`, `capturedAt`, `hostname`, `address`, `sshHostKeyIdentity`, `installedVersion`, `service`, `listeners`, `localHttp`, `ufw`, `directLanDenied`. `service` contains the exact allowlisted `sanitizedUnitRef`; listeners are `{ address, port, protocol }`; local HTTP is `{ url, statusCode, exitCode }`; UFW is `{ active, defaults, ruleIds, tcp3080Allowed }`; direct denial is `{ source, destination, port, denied, timeoutMs }`.
- `selector`: `name`, `precedence`, `absoluteCandidateValue`, `futureUnitSelectorLines`, `effectiveProfileProbe`, `proof`.
- `selector.proof`: `absolutePath`, `precedence`, `fullProfileScope`, `nonMerge`, `serviceCompatibility`; semantic claims use `installedSourceRef` only. `serviceCompatibility` requires installed-source proof and may additionally use narrowly scoped `sanitizedUnitRef`. `fullProfileScope` has separate installed-source proofs for credentials, settings, plugins, sessions/state, and other mutable stores.
- `candidateBlueprint.directories[]`: `relativePath`, `owner`, `group`, `mode`, `contentSource`, `sourceRefs`; relative paths are normalized POSIX paths without root/traversal, owner/group are `dsh:dsh`, mode is `0700`, `contentSource` is `installed-default` or `approved-setting`, and `sourceRefs` contains `installedSourceRef` only.
- `candidateBlueprint.files[]`: `relativePath`, `owner`, `group`, `mode`, `contentLines`, `contentSha256`, `contentSource`, `sourceRefs`; mode is `0600` or narrower, content is nonsecret UTF-8/LF, digest covers one terminal LF, content source is `installed-default` or `approved-setting`, and source refs are installed-source only.
- `candidateBlueprint.staticValidation`: `supported`, `executable`, `argv`, `timeoutSeconds`, `parser`, `acceptedResults`, `sourceRefs`; when supported, executable is the validated installed entrypoint or package-owned validator, argv is an atomic array whose candidate/profile value equals the fixed root, timeout is 1-60, parser is a named safe parser, accepted results are exact nonsecret parsed values, and source refs are installed-source only. Unknown selector or validator syntax enters this structure only after Task 1 directly proves and validates it.
- `candidateBlueprint.policyAssertions`: exactly the seven fixed fields shown in Task 1 Step 5.
- `cutoverPrerequisites`: `observedAt`, `verdict`, `privilegeSeam`, `dropInDirectory`, `blockers`. This status never gates candidate creation and never authorizes cutover.
- `privilegeSeam`: `verdict`, `receipts`; receipts cover only read-only proof of whether existing narrow permissions would allow future fixed-file install/removal and exact `systemctl stop`, `start`, `daemon-reload`, and status operations.
- `dropInDirectory`: `path`, `exists`, `realDirectory`, `owner`, `group`, `mode`, `linkStatus`, `broadAcl`, `unexpectedMount`, `verdict`.
- `candidatePreparation`: `selectorDigest`, `candidateDigest`, `startedAt`, `finishedAt`, `verdict`, `checks`, `mutationLedger`, `runtimeVerdict`, `blockers`, `review`.
- `candidatePreparation.checks[]`: `order`, `id`, `result`, `observedAt`, `parser`, `safeObservation`, `failureState`; orders are consecutive and IDs are `selector-gate`, `target-preflight`, `create-parent`, `create-root`, `write-blueprint`, `metadata`, `static-validation`, `secret-scan`, `service-unchanged`, `network-unchanged`. Result is `PASS`, `BLOCKED`, or `NOT PROVEN`; `safeObservation` follows that check's fixed parser schema and contains no raw output.
- `candidatePreparation.mutationLedger[]`: `order`, `operation`, `path`, `contentSha256`, `result`, `at`, `secretObserved`; operation is `CREATE_DIRECTORY` or `WRITE_FILE`, path is the fixed parent/root or a validated child, directory digest is `null`, result is `PASS` or `BLOCKED`, and `secretObserved` is always `false`.
- `closeout`: `closedAt`, `verdict`, `selectorDigest`, `candidateDigest`, `cutoverPrerequisiteVerdict`, `handoffPath`, `handoffSha256`, `review`.
- `review`: `status`, `reviewedAt`, `reviewer`, `reviewedDigest`, `findings`; status is `PENDING`, `ACCEPTED`, or `REJECTED`.
- `operationLedger` entry: `at`, `actor`, `operation`, `target`, `result`, `secretObserved`; it contains no raw command output or file contents.

Reference classes are not interchangeable. The validator rejects an unknown `sourceClass`, a `privilegeReceiptRef` or `sanitizedUnitRef` used for selector semantics, an `installedSourceRef` used as a privilege receipt, a unit reference used for whole-profile/non-merge proof, and any reference whose fields do not exactly match its class schema.

Candidate check parsers return only these typed safe results:

| Check | Parser | `safeObservation` fields |
| --- | --- | --- |
| `selector-gate` | `SelectorGateV1` | `selectorDigest`, `selectorVerdict`, `reviewStatus`, `reviewedDigest` |
| `target-preflight` | `TargetPreflightV1` | `parentAbsent`, `rootAbsent`, `ancestorsSafe` |
| `create-parent`, `create-root`, `write-blueprint`, `metadata` | `CandidateMetadataV1` | `path`, `objectType`, `symlink`, `owner`, `group`, `mode`, `linkCount`, `aclBroad`, `unexpectedMount`, `contentSha256` |
| `static-validation` | `StaticValidationV1` | `supported`, `exitCode`, `parsedResult`; unsupported is `NOT PROVEN` unless it weakens isolation, then `BLOCKED` |
| `secret-scan` | `SecretScanV1` | `filesScanned`, `findingCount`, `categories`; matching values are never present |
| `service-unchanged` | `ServiceBaselineV1` | `activeState`, `subState`, `user`, `group`, `execStart`, `workingDirectory`, `umask`, `result`, `nRestarts`, `matchesBaseline` |
| `network-unchanged` | `NetworkBaselineV1` | `listeners`, `localHttpStatus`, `ufwActive`, `tcp3080Allowed`, `directLanDenied`, `matchesBaseline` |

Every `PASS` field is compared to the accepted baseline/blueprint, not accepted from a self-reported label. Empty, extra, malformed, timed-out, or unknown parser results are `BLOCKED`.

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

Implement the core assertions and source-class gate with these exact signatures and behavior:

```powershell
function Assert-True {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) { throw $Message }
}

function Assert-ExactKeys {
    param([object]$Value, [string[]]$Expected, [string]$Label)
    $actual = @($Value.psobject.Properties.Name | Sort-Object)
    $wanted = @($Expected | Sort-Object)
    Assert-True (($actual -join "`n") -ceq ($wanted -join "`n")) "$Label keys differ"
}

function Assert-Throws {
    param([scriptblock]$Action, [string]$Pattern)
    try { & $Action; throw 'Expected rejection was not raised' }
    catch { Assert-True ($_.Exception.Message -match $Pattern) "Wrong rejection category" }
}

function Copy-SyntheticRecord {
    param([object]$Value)
    return ($Value | ConvertTo-Json -Depth 100 | ConvertFrom-Json)
}

function Get-UpperSha256 {
    param([byte[]]$Bytes)
    return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($Bytes))
}

function Assert-InstalledSourceRef {
    param([object]$Ref, [string]$PackageRoot)
    Assert-ExactKeys $Ref @('sourceClass','path','sha256','lineStart','lineEnd','claim') 'installedSourceRef'
    Assert-True ($Ref.sourceClass -ceq 'installed-source') 'proof-source-class'
    Assert-True ([IO.Path]::IsPathFullyQualified([string]$Ref.path)) 'installed-source-path'
    Assert-True (($Ref.path -ceq '/usr/local/bin/dsh') -or $Ref.path.StartsWith("$PackageRoot/", [StringComparison]::Ordinal)) 'installed-source-root'
    Assert-True ($Ref.sha256 -match '^[A-F0-9]{64}$') 'installed-source-digest'
    Assert-True (($Ref.lineStart -ge 1) -and ($Ref.lineEnd -ge $Ref.lineStart)) 'installed-source-lines'
}

function Assert-SanitizedUnitRef {
    param([object]$Ref,[string]$SelectorKey)
    $allowed = @('User','Group','ExecStart','WorkingDirectory','UMask','FragmentPath','DropInPaths','ActiveState','SubState','Result','NRestarts')
    if($SelectorKey -match '^[A-Z][A-Z0-9_]{1,63}$'){$allowed += $SelectorKey}
    Assert-ExactKeys $Ref @('sourceClass','observationId','capturedAt','propertyAllowlist','observations','claim') 'sanitizedUnitRef'
    Assert-True ($Ref.sourceClass -ceq 'sanitized-unit') 'proof-source-class'
    foreach ($item in @($Ref.observations)) {
        Assert-ExactKeys $item @('name','value') 'sanitizedUnitObservation'
        Assert-True ($allowed -ccontains [string]$item.name) 'unit-property-allowlist'
    }
}

function Assert-PrivilegeReceiptRef {
    param([object]$Ref)
    Assert-ExactKeys $Ref @('sourceClass','operationId','capturedAt','queryUser','sudoPath','targetExecutable','targetArgv','noninteractive','result','exitCode','rawOutputStored','claim') 'privilegeReceiptRef'
    Assert-True ($Ref.sourceClass -ceq 'privilege-receipt') 'proof-source-class'
    Assert-True (($Ref.queryUser -ceq 'dsh') -and $Ref.noninteractive -and -not $Ref.rawOutputStored) 'privilege-receipt-safety'
    Assert-True (@('ALLOWED','DENIED') -ccontains [string]$Ref.result) 'privilege-receipt-result'
}

function Test-PreparationEvidence {
    param([object]$Evidence, [ValidateSet('Selector','Candidate','Closeout')][string]$Stage)
    Assert-True ($Evidence.schemaVersion -eq 1) 'schema-version'
    Assert-True ($Evidence.workflowId -ceq 'vm105-profile-preparation') 'workflow-id'
    Assert-True ($Evidence.target.candidateRoot -ceq '/home/dsh/.dsh-profiles/vm105-provider-v1') 'candidate-root'
    Assert-True (-not $Evidence.selectorDiscovery.installedEntrypoint.wrapperSymlink -and -not $Evidence.selectorDiscovery.installedEntrypoint.entrypointSymlink) 'installed-symlink'
    $packageRoot = [string]$Evidence.selectorDiscovery.installedEntrypoint.packageRoot
    foreach ($proofName in @('absolutePath','precedence','nonMerge')) {
        foreach ($ref in @($Evidence.selectorDiscovery.selector.proof.$proofName)) {
            Assert-InstalledSourceRef $ref $packageRoot
        }
    }
    foreach ($store in @('credentials','settings','plugins','sessionsState','otherMutableStores')) {
        $refs=@($Evidence.selectorDiscovery.selector.proof.fullProfileScope.$store)
        Assert-True ($refs.Count -gt 0) "missing-$store"
        foreach ($ref in $refs) {
            Assert-InstalledSourceRef $ref $packageRoot
        }
    }
    $compatibility=$Evidence.selectorDiscovery.selector.proof.serviceCompatibility
    foreach($ref in @($compatibility.installed)){Assert-InstalledSourceRef $ref $packageRoot}
    foreach($ref in @($compatibility.unit)){Assert-SanitizedUnitRef $ref ([string]$Evidence.selectorDiscovery.selector.name)}
    $policy=$Evidence.selectorDiscovery.candidateBlueprint.policyAssertions
    Assert-True ($policy.bindHost -ceq '127.0.0.1' -and $policy.port -eq 3080 -and $policy.activeProviderRoutes -eq 0 -and -not $policy.automaticFallback -and -not $policy.providerSelectionConfigured -and -not $policy.oauthStateConfigured -and -not $policy.hermesReferences) 'candidate-policy'
    foreach($directory in @($Evidence.selectorDiscovery.candidateBlueprint.directories)){Assert-True ($directory.mode -ceq '0700' -and $directory.relativePath -notmatch '(^|/)\.\.(/|$)|^/') 'candidate-directory'}
    foreach($file in @($Evidence.selectorDiscovery.candidateBlueprint.files)){Assert-True (([Convert]::ToInt32($file.mode,8) -band 63) -eq 0 -and $file.relativePath -notmatch '(^|/)\.\.(/|$)|^/') 'candidate-file'}
    Assert-True ($Evidence.selectorDiscovery.selectorDigest -ceq $Evidence.selectorDiscovery.review.reviewedDigest) 'selector-review-digest'
    foreach ($ref in @($Evidence.cutoverPrerequisites.privilegeSeam.receipts)) {
        Assert-PrivilegeReceiptRef $ref
    }
    if ($Stage -in @('Candidate','Closeout')) {
        Assert-True ($Evidence.candidatePreparation.runtimeVerdict -ceq 'NOT PROVEN') 'runtime-verdict'
        $blocked=$false
        foreach($check in @($Evidence.candidatePreparation.checks)){
            if($blocked){throw 'continued-after-block'}
            if($check.result -ceq 'BLOCKED'){$blocked=$true}
        }
    }
}

function Test-NonExecutableHandoff {
    param([string]$Text)
    Assert-True ($Text -notmatch '(?m)^```|\b(argv|Invoke-|systemctl\s+(stop|start|restart)|daemon-reload|sudo\s)\b') 'executable-handoff'
    Assert-True ($Text -match 'no authority' -and $Text -match 'NOT PROVEN') 'handoff-boundary'
}
```

Use this complete positive-record factory; its selector name is explicitly synthetic and must never be copied into live evidence:

```powershell
function New-SyntheticPreparationRecord {
    $time = '2026-09-08T00:00:00Z'
    $digest = 'A' * 64
    $source = [pscustomobject]@{
        sourceClass = 'installed-source'; path = '/opt/deepseek-harness/package/index.js'
        sha256 = $digest; lineStart = 1; lineEnd = 2; claim = 'synthetic installed proof'
    }
    $unit = [pscustomobject]@{
        sourceClass = 'sanitized-unit'; observationId = 'synthetic-unit'; capturedAt = $time
        propertyAllowlist = @('User','Group','ActiveState','SubState')
        observations = @(
            [pscustomobject]@{name='User';value='dsh'}, [pscustomobject]@{name='Group';value='dsh'},
            [pscustomobject]@{name='ActiveState';value='active'}, [pscustomobject]@{name='SubState';value='running'}
        )
        claim = 'synthetic safe unit facts'
    }
    $privilege = [pscustomobject]@{
        sourceClass = 'privilege-receipt'; operationId = 'synthetic-install'; capturedAt = $time
        queryUser = 'dsh'; sudoPath = '/usr/bin/sudo'; targetExecutable = '/usr/bin/install'
        targetArgv = @('-m','0644','/dev/stdin','/etc/systemd/system/deepseek-harness.service.d/90-vm105-provider-profile.conf')
        noninteractive = $true; result = 'DENIED'; exitCode = 1; rawOutputStored = $false
        claim = 'synthetic denied privilege'
    }
    $contentLines = @('server:','  host: 127.0.0.1','  port: 3080','providers: []','automaticFallback: false')
    $contentBytes = [Text.Encoding]::UTF8.GetBytes(($contentLines -join "`n") + "`n")
    return [pscustomobject]@{
        schemaVersion = 1; workflowId = 'vm105-profile-preparation'
        target = [pscustomobject]@{
            hostname='deepseek-harness-01';address='192.0.2.105';sshHostKeyIdentity='SHA256:synthetic'
            service='deepseek-harness.service';serviceUser='dsh';serviceGroup='dsh'
            candidateRoot='/home/dsh/.dsh-profiles/vm105-provider-v1';listenerHost='127.0.0.1';listenerPort=3080
            futureDropInDirectory='/etc/systemd/system/deepseek-harness.service.d'
            futureDropInFile='/etc/systemd/system/deepseek-harness.service.d/90-vm105-provider-profile.conf'
        }
        overallVerdict = 'SELECTOR_PASS'
        selectorDiscovery = [pscustomobject]@{
            capturedAt=$time;installedVersion='0.1.1-rc.2';verdict='PASS';blockers=@()
            installedEntrypoint=[pscustomobject]@{
                wrapperPath='/usr/local/bin/dsh';wrapperType='regular file';wrapperSymlink=$false
                wrapperOwner='root';wrapperGroup='root';wrapperMode='0755';wrapperLinkCount=1;wrapperSha256=$digest
                entrypointPath='/opt/deepseek-harness/package/index.js';entrypointType='regular file';entrypointSymlink=$false
                entrypointOwner='root';entrypointGroup='root';entrypointMode='0644';entrypointLinkCount=1;entrypointSha256=$digest
                packageRoot='/opt/deepseek-harness/package';packageName='synthetic-harness';packageVersion='0.1.1-rc.2';proofRefs=@($source)
            }
            baseline=[pscustomobject]@{
                repositoryOrigin='https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git'
                branch='codex/vm105-authoritative-roadmap';capturedAt=$time;hostname='deepseek-harness-01'
                address='192.0.2.105';sshHostKeyIdentity='SHA256:synthetic';installedVersion='0.1.1-rc.2'
                service=$unit;listeners=@([pscustomobject]@{address='127.0.0.1';port=3080;protocol='tcp'})
                localHttp=[pscustomobject]@{url='http://127.0.0.1:3080/';statusCode=200;exitCode=0}
                ufw=[pscustomobject]@{active=$true;defaults='deny-in-allow-out';ruleIds=@('synthetic-ssh');tcp3080Allowed=$false}
                directLanDenied=[pscustomobject]@{source='192.0.2.10';destination='192.0.2.105';port=3080;denied=$true;timeoutMs=1000}
            }
            selector=[pscustomobject]@{
                name='SYNTHETIC_PROFILE_ROOT';precedence='synthetic installed proof';absoluteCandidateValue='/home/dsh/.dsh-profiles/vm105-provider-v1'
                futureUnitSelectorLines=@('synthetic selector line');effectiveProfileProbe=[pscustomobject]@{executable='/opt/deepseek-harness/package/index.js';argv=@('synthetic-safe-paths')}
                proof=[pscustomobject]@{
                    absolutePath=@($source);precedence=@($source);nonMerge=@($source)
                    fullProfileScope=[pscustomobject]@{credentials=@($source);settings=@($source);plugins=@($source);sessionsState=@($source);otherMutableStores=@($source)}
                    serviceCompatibility=[pscustomobject]@{installed=@($source);unit=@($unit)}
                }
            }
            candidateBlueprint=[pscustomobject]@{
                directories=@([pscustomobject]@{relativePath='state';owner='dsh';group='dsh';mode='0700';contentSource='installed-default';sourceRefs=@($source)})
                files=@([pscustomobject]@{relativePath='settings.yaml';owner='dsh';group='dsh';mode='0600';contentLines=$contentLines;contentSha256=(Get-UpperSha256 $contentBytes);contentSource='approved-setting';sourceRefs=@($source)})
                staticValidation=[pscustomobject]@{supported=$false;executable=$null;argv=@();timeoutSeconds=1;parser='NoneV1';acceptedResults=@();sourceRefs=@($source)}
                policyAssertions=[pscustomobject]@{bindHost='127.0.0.1';port=3080;activeProviderRoutes=0;automaticFallback=$false;providerSelectionConfigured=$false;oauthStateConfigured=$false;hermesReferences=$false}
            }
            selectorDigest=$digest;review=[pscustomobject]@{status='ACCEPTED';reviewedAt=$time;reviewer='synthetic-reviewer';reviewedDigest=$digest;findings=@()}
        }
        cutoverPrerequisites=[pscustomobject]@{
            observedAt=$time;verdict='BLOCKED';privilegeSeam=[pscustomobject]@{verdict='BLOCKED';receipts=@($privilege)}
            dropInDirectory=[pscustomobject]@{path='/etc/systemd/system/deepseek-harness.service.d';exists=$false;realDirectory=$false;owner=$null;group=$null;mode=$null;linkStatus='absent';broadAcl=$null;unexpectedMount=$null;verdict='BLOCKED'}
            blockers=@('Synthetic privilege seam denied')
        }
        candidatePreparation=$null;closeout=$null;operationLedger=@()
    }
}

function New-SyntheticCandidateResult {
    param([string]$FailAt, [switch]$ContinueAfterFailure)
    $ids = @('selector-gate','target-preflight','create-parent','create-root','write-blueprint','metadata','static-validation','secret-scan','service-unchanged','network-unchanged')
    $checks = [Collections.Generic.List[object]]::new()
    $blocked = $false
    for ($i = 0; $i -lt $ids.Count; $i++) {
        if ($blocked -and -not $ContinueAfterFailure) { break }
        $result = if ($ids[$i] -ceq $FailAt) { 'BLOCKED' } else { 'PASS' }
        $checks.Add([pscustomobject]@{order=$i+1;id=$ids[$i];result=$result;observedAt='2026-09-08T00:00:00Z';parser='SyntheticV1';safeObservation=[pscustomobject]@{};failureState='BLOCKED'})
        if ($result -ceq 'BLOCKED') { $blocked = $true }
    }
    $verdict = if ($blocked) { 'BLOCKED' } else { 'PASS' }
    return [pscustomobject]@{selectorDigest=('A'*64);candidateDigest=('B'*64);startedAt='2026-09-08T00:00:00Z';finishedAt='2026-09-08T00:00:01Z';verdict=$verdict;checks=@($checks);mutationLedger=@();runtimeVerdict='NOT PROVEN';blockers=@();review=[pscustomobject]@{status='PENDING';reviewedAt=$null;reviewer=$null;reviewedDigest=$null;findings=@()}}
}
```

The self-test body uses only synthetic values and must include concrete cross-class and continuation assertions:

```powershell
$good = New-SyntheticPreparationRecord
Test-PreparationEvidence $good 'Selector'

$wrongSelectorClass = Copy-SyntheticRecord $good
$wrongSelectorClass.selectorDiscovery.selector.proof.nonMerge[0] = $wrongSelectorClass.cutoverPrerequisites.privilegeSeam.receipts[0]
Assert-Throws { Test-PreparationEvidence $wrongSelectorClass 'Selector' } 'proof-source-class'

$wrongPrivilegeClass = Copy-SyntheticRecord $good
$wrongPrivilegeClass.cutoverPrerequisites.privilegeSeam.receipts[0] = $wrongPrivilegeClass.selectorDiscovery.selector.proof.absolutePath[0]
Assert-Throws { Test-PreparationEvidence $wrongPrivilegeClass 'Selector' } 'privilegeReceiptRef'

$partialScope = Copy-SyntheticRecord $good
$partialScope.selectorDiscovery.selector.proof.fullProfileScope.sessionsState = @()
Assert-Throws { Test-PreparationEvidence $partialScope 'Selector' } 'sessionsState'

$unsafeBlueprint = Copy-SyntheticRecord $good
$unsafeBlueprint.selectorDiscovery.candidateBlueprint.policyAssertions.automaticFallback = $true
Assert-Throws { Test-PreparationEvidence $unsafeBlueprint 'Selector' } 'candidate-policy'

$continuedAfterFailure = Copy-SyntheticRecord $good
$continuedAfterFailure.candidatePreparation = New-SyntheticCandidateResult -FailAt 'write-blueprint' -ContinueAfterFailure
Assert-Throws { Test-PreparationEvidence $continuedAfterFailure 'Candidate' } 'continued-after-block'

$outsideSource = Copy-SyntheticRecord $good
$outsideSource.selectorDiscovery.selector.proof.absolutePath[0].path = '/tmp/unowned.js'
Assert-Throws { Test-PreparationEvidence $outsideSource 'Selector' } 'installed-source-root'

$linkedWrapper = Copy-SyntheticRecord $good
$linkedWrapper.selectorDiscovery.installedEntrypoint.wrapperSymlink = $true
Assert-Throws { Test-PreparationEvidence $linkedWrapper 'Selector' } 'installed-symlink'

$wrongRoot = Copy-SyntheticRecord $good
$wrongRoot.target.candidateRoot = '/home/dsh/other'
Assert-Throws { Test-PreparationEvidence $wrongRoot 'Selector' } 'candidate-root'

$wideFile = Copy-SyntheticRecord $good
$wideFile.selectorDiscovery.candidateBlueprint.files[0].mode = '0644'
Assert-Throws { Test-PreparationEvidence $wideFile 'Selector' } 'candidate-file'

$digestDrift = Copy-SyntheticRecord $good
$digestDrift.selectorDiscovery.review.reviewedDigest = 'B' * 64
Assert-Throws { Test-PreparationEvidence $digestDrift 'Selector' } 'selector-review-digest'

$runtimeClaim = Copy-SyntheticRecord $good
$runtimeClaim.candidatePreparation = New-SyntheticCandidateResult -FailAt ''
$runtimeClaim.candidatePreparation.runtimeVerdict = 'PASS'
Assert-Throws { Test-PreparationEvidence $runtimeClaim 'Candidate' } 'runtime-verdict'

Assert-Throws { Test-NonExecutableHandoff "systemctl stop deepseek-harness.service`nNOT PROVEN`nno authority" } 'executable-handoff'
$safeHandoff = "Preparation ready; no authority granted.`nRuntime remains NOT PROVEN."
Test-NonExecutableHandoff $safeHandoff

$captured = & { Test-SyntheticSecretScanner 'api_key: synthetic_nonempty_value' } 2>&1 | Out-String
Assert-True ($captured -notmatch 'synthetic_nonempty_value') 'secret-output-suppression'
```

`New-SyntheticPreparationRecord`, `New-SyntheticCandidateResult`, and `Test-SyntheticSecretScanner` are private functions in the same script. The record factory must populate every Shared Preparation Contract field with the fixed synthetic hostname `deepseek-harness-01`, documentation address `192.0.2.105`, `/opt/deepseek-harness/package/index.js`, all five installed-source store proofs, zero routes, fallback false, one denied privilege receipt, and no secret-shaped data; the candidate-result factory emits the ten ordered check IDs and stops its ledger at the requested failed check.

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

Run `./scripts/Test-VM105ProfilePreparation.ps1 -SelfTest` before completing validator logic. Expected RED: nonzero exit with `Expected rejection was not raised`. After implementing the private factories plus all assertions, expected GREEN: exit 0 with `SELF_TEST_PASS positive=2 negative=13`, and no synthetic value in output.

- [ ] **Step 2: Revalidate repository, VM, service, listener, and wrapper metadata read-only**

Run from the authoritative worktree:

```powershell
$expectedOrigin = 'https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git'
if ((git remote get-url origin).Trim() -ne $expectedOrigin) { throw 'Unexpected repository origin' }
if ((git branch --show-current).Trim() -ne 'codex/vm105-authoritative-roadmap') { throw 'Unexpected branch' }
$sshBaseArgs = @(
  '-i','C:\Users\chatc\.ssh\codex-prox01-vms-ed25519',
  '-o','BatchMode=yes',
  '-o','IdentitiesOnly=yes',
  '-o','StrictHostKeyChecking=yes',
  'dsh@192.168.1.139'
)

function Invoke-StrictSsh {
    param([string[]]$RemoteArgv, [int]$TimeoutSeconds = 30)
    $psi = [Diagnostics.ProcessStartInfo]::new((Get-Command ssh.exe).Source)
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    foreach ($arg in @($sshBaseArgs + '--' + $RemoteArgv)) { [void]$psi.ArgumentList.Add($arg) }
    $process = [Diagnostics.Process]::Start($psi)
    if (-not $process.WaitForExit($TimeoutSeconds * 1000)) { $process.Kill($true); throw 'SSH timeout' }
    $stdout = $process.StandardOutput.ReadToEnd()
    [void]$process.StandardError.ReadToEnd()
    if ($process.ExitCode -ne 0) { throw "SSH exit $($process.ExitCode)" }
    return @($stdout -split "`r?`n" | Where-Object Length)
}

$hostname = (Invoke-StrictSsh @('/usr/bin/hostname')) -join ''
$user = (Invoke-StrictSsh @('/usr/bin/id','-un')) -join ''
$group = (Invoke-StrictSsh @('/usr/bin/id','-gn')) -join ''
$version = (Invoke-StrictSsh @('/usr/local/bin/dsh','--version')) -join ''
$unitLines = Invoke-StrictSsh @('/usr/bin/systemctl','show','deepseek-harness.service','--property=User,Group,ExecStart,WorkingDirectory,UMask,FragmentPath,DropInPaths,ActiveState,SubState,Result,NRestarts','--no-pager')
$listenerLines = Invoke-StrictSsh @('/usr/bin/ss','-lntH','sport = :3080')
$wrapperStat = (Invoke-StrictSsh @('/usr/bin/stat','-c','%n|%F|%U|%G|%a|%h','--','/usr/local/bin/dsh')) -join ''

if ($hostname -cne 'deepseek-harness-01' -or $user -cne 'dsh' -or $group -cne 'dsh') { throw 'VM identity mismatch' }
if ($version -notmatch '0\.1\.1-rc\.2') { throw 'Harness version mismatch' }
```

Expected: repository/branch match; hostname `deepseek-harness-01`; caller/group `dsh`; version `0.1.1-rc.2`; service active; listener loopback-only on port 3080; wrapper a safe regular installed file. Do not inspect the old profile root or children, service environments, logs, or secret-bearing configuration.

Parse the unit output into the typed allowlist instead of storing raw text:

```powershell
function ConvertFrom-SanitizedUnitLines {
    param([string[]]$Lines)
    $allow = @('User','Group','ExecStart','WorkingDirectory','UMask','FragmentPath','DropInPaths','ActiveState','SubState','Result','NRestarts')
    $seen = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    $items = foreach ($line in $Lines) {
        if ($line -notmatch '^([A-Za-z][A-Za-z0-9]*)=(.*)$') { throw 'Malformed unit observation' }
        $name = $Matches[1]; $value = $Matches[2]
        if ($allow -cnotcontains $name -or -not $seen.Add($name)) { throw 'Unexpected unit property' }
        [pscustomobject]@{name=$name;value=$value}
    }
    if ($seen.Count -ne $allow.Count) { throw 'Missing unit property' }
    return [pscustomobject]@{
        sourceClass='sanitized-unit';observationId='vm105-effective-unit';capturedAt=(Get-Date).ToUniversalTime().ToString('o')
        propertyAllowlist=$allow;observations=@($items);claim='Allowlisted effective service baseline'
    }
}

$unitRef = ConvertFrom-SanitizedUnitLines $unitLines
$unitMap = @{}; foreach ($item in $unitRef.observations) { $unitMap[$item.name] = $item.value }
if ($unitMap.User -cne 'dsh' -or $unitMap.Group -cne 'dsh' -or $unitMap.ActiveState -cne 'active' -or $unitMap.SubState -cne 'running') { throw 'Unexpected service baseline' }
```

Expected parsed result: eleven unique allowlisted observations; `User=dsh`, `Group=dsh`, `ActiveState=active`, `SubState=running`, and no environment or unknown property.

- [ ] **Step 3: Verify the wrapper and discover only from its fixed installed entrypoint**

After capturing owner/mode/SHA-256, read exactly `/usr/local/bin/dsh` as data. Require one fixed absolute entrypoint below `/opt/deepseek-harness`; reject command substitution, environment-derived/relative/fallback paths, eval, extra executable branches, writable owner/mode, or a target outside that root. Verify the extracted entrypoint is a regular installed/package-owned safe file. Walk upward only inside `/opt/deepseek-harness` to its owning `package.json`, verify package name/version, and record digests before reading package help/docs/schema/state-location sources. Do not follow links outside the package root, run network package commands, or install anything.

Build selector semantic proof exclusively from `installedSourceRef` records. Prove exact selector name/precedence, absolute-path support, non-merge/non-inherit/non-migrate behavior, and full-profile coverage for credentials, settings, plugins, sessions/state, and every other mutable store. Service compatibility requires installed-source proof; a `sanitizedUnitRef` may additionally establish that the unchanged installed command/user can consume the selector. Query only the proven selector key from effective unit metadata and suppress all other environment values.

Use this fail-closed parser and package-root walk; it returns `BLOCKED` instead of guessing:

```powershell
function Get-VerifiedInstalledEntrypoint {
    $statLine = (Invoke-StrictSsh @('/usr/bin/stat','-c','%n|%F|%U|%G|%a|%h','--','/usr/local/bin/dsh')) -join ''
    $parts = $statLine -split '\|',6
    if ($parts.Count -ne 6 -or $parts[0] -cne '/usr/local/bin/dsh' -or $parts[1] -cne 'regular file' -or $parts[2] -cne 'root' -or $parts[3] -cne 'root' -or [int]$parts[5] -ne 1) { throw 'BLOCKED wrapper metadata' }
    if (([Convert]::ToInt32($parts[4],8) -band 18) -ne 0) { throw 'BLOCKED writable wrapper' }
    $wrapperLines = Invoke-StrictSsh @('/usr/bin/cat','--','/usr/local/bin/dsh')
    $meaningful = @($wrapperLines | Where-Object { $_ -and $_ -notmatch '^#!' -and $_ -notmatch '^set -e(?:u)?$' })
    if ($meaningful.Count -ne 1) { throw 'BLOCKED wrapper shape' }
    $match = [regex]::Match($meaningful[0], '^exec\s+(?:(/[A-Za-z0-9._/-]+)\s+)?(/opt/deepseek-harness/[A-Za-z0-9._/-]+)(?:\s+"\$@")?\s*$')
    if (-not $match.Success -or $meaningful[0] -match '\$\(|`|\$\{') { throw 'BLOCKED wrapper entrypoint' }
    $entrypoint = $match.Groups[2].Value
    $entryStat = (Invoke-StrictSsh @('/usr/bin/stat','-c','%n|%F|%U|%G|%a|%h','--',$entrypoint)) -join ''
    $entryParts = $entryStat -split '\|',6
    if ($entryParts.Count -ne 6 -or $entryParts[0] -cne $entrypoint -or $entryParts[1] -cne 'regular file' -or [int]$entryParts[5] -ne 1) { throw 'BLOCKED entrypoint metadata' }
    if (([Convert]::ToInt32($entryParts[4],8) -band 18) -ne 0) { throw 'BLOCKED writable entrypoint' }
    $current = $entrypoint.Substring(0,$entrypoint.LastIndexOf('/'))
    $packageRoot = $null
    while ($current.StartsWith('/opt/deepseek-harness/',[StringComparison]::Ordinal) -or $current -ceq '/opt/deepseek-harness') {
        try { [void](Invoke-StrictSsh @('/usr/bin/stat','-c','%F','--',"$current/package.json")); $packageRoot=$current; break } catch {}
        $slash = $current.LastIndexOf('/'); if ($slash -le 0) { break }; $current = $current.Substring(0,$slash)
    }
    if (-not $packageRoot) { throw 'BLOCKED package root' }
    $package = ((Invoke-StrictSsh @('/usr/bin/cat','--',"$packageRoot/package.json")) -join "`n") | ConvertFrom-Json
    if (-not $package.name -or $package.version -cne '0.1.1-rc.2') { throw 'BLOCKED package identity' }
    $wrapperSha=((Invoke-StrictSsh @('/usr/bin/sha256sum','--','/usr/local/bin/dsh')) -join '').Split(' ')[0].ToUpperInvariant()
    $entrySha=((Invoke-StrictSsh @('/usr/bin/sha256sum','--',$entrypoint)) -join '').Split(' ')[0].ToUpperInvariant()
    return [pscustomobject]@{
        wrapperPath='/usr/local/bin/dsh';wrapperType=$parts[1];wrapperSymlink=$false;wrapperOwner=$parts[2];wrapperGroup=$parts[3];wrapperMode=$parts[4];wrapperLinkCount=[int]$parts[5];wrapperSha256=$wrapperSha
        entrypointPath=$entrypoint;entrypointType=$entryParts[1];entrypointSymlink=$false;entrypointOwner=$entryParts[2];entrypointGroup=$entryParts[3];entrypointMode=$entryParts[4];entrypointLinkCount=[int]$entryParts[5];entrypointSha256=$entrySha
        packageRoot=$packageRoot;packageName=$package.name;packageVersion=$package.version
    }
}

$installed = Get-VerifiedInstalledEntrypoint
$allPackageFiles = Invoke-StrictSsh @('/usr/bin/find',$installed.packageRoot,'-xdev','-type','f','-print')
$sourcePaths = @($allPackageFiles | Where-Object { $_ -match '/package\.json$|/README[^/]*$|/(docs|src|dist)/' })
foreach ($path in $sourcePaths) {
    if (-not $path.StartsWith("$($installed.packageRoot)/",[StringComparison]::Ordinal) -and $path -cne "$($installed.packageRoot)/package.json") { throw 'BLOCKED package walk escape' }
}
```

Expected parsed result: one absolute regular entrypoint and one package root below `/opt/deepseek-harness`, package version `0.1.1-rc.2`, and only package-owned candidate source paths. If the wrapper or package shape differs, write a `BLOCKED` record and stop discovery.

After installed-source proof identifies a selector key matching `^[A-Z][A-Z0-9_]{1,63}$`, a VM-side fixed filter may inspect only that key from `systemctl show --property=Environment`; it emits either one `KEY=/absolute/path` observation or `KEY=ABSENT` and discards all other values. The validator accepts this `sanitizedUnitRef` only for service compatibility/current precedence, never for whole-profile or non-merge semantics.

- [ ] **Step 4: Observe future-cutover prerequisites without changing them**

Resolve existing absolute installed executables and use bounded `sudo -n -l --` permission queries that execute no privileged operation. Check only whether a pre-existing noninteractive seam would permit future fixed drop-in file install/removal and exact `systemctl stop deepseek-harness.service`, `start`, `daemon-reload`, and status operations. Record one typed `privilegeReceiptRef` per operation with allow/deny and hashed argv; suppress raw sudo policy output. Never edit sudoers or invent a broader command.

Read only metadata for `/etc/systemd/system/deepseek-harness.service.d`: existence, real-directory/link status, owner/group, mode, ACL broadness, and mount relationship. `cutoverPrerequisites.verdict` is `PASS` only when all narrow privilege receipts are allowed/noninteractive and the directory already exists as `root:root` `0755`, real/non-link, without broad ACL or unexpected mount. Otherwise record exact `BLOCKED` reasons. Do not create or repair the directory and do not write a drop-in.

Use a status-only SSH runner so denied privilege queries never surface raw sudo policy text:

```powershell
function Invoke-StrictSshStatus {
    param([string[]]$RemoteArgv, [int]$TimeoutSeconds = 15)
    $psi = [Diagnostics.ProcessStartInfo]::new((Get-Command ssh.exe).Source)
    $psi.UseShellExecute=$false; $psi.RedirectStandardOutput=$true; $psi.RedirectStandardError=$true
    foreach ($arg in @($sshBaseArgs + '--' + $RemoteArgv)) { [void]$psi.ArgumentList.Add($arg) }
    $process=[Diagnostics.Process]::Start($psi)
    if (-not $process.WaitForExit($TimeoutSeconds*1000)) { $process.Kill($true); return 124 }
    [void]$process.StandardOutput.ReadToEnd(); [void]$process.StandardError.ReadToEnd()
    return $process.ExitCode
}

function New-PrivilegeReceipt {
    param([string]$Id,[string]$Executable,[string[]]$Argv)
    $query = @('/usr/bin/sudo','-n','-l','--',$Executable) + $Argv
    $exit = Invoke-StrictSshStatus $query
    $argvBytes = [Text.Encoding]::UTF8.GetBytes(($Argv -join "`0"))
    [pscustomobject]@{
        sourceClass='privilege-receipt';operationId=$Id;capturedAt=(Get-Date).ToUniversalTime().ToString('o')
        queryUser='dsh';sudoPath='/usr/bin/sudo';targetExecutable=$Executable;targetArgv=$Argv
        noninteractive=$true;result=$(if($exit -eq 0){'ALLOWED'}else{'DENIED'});exitCode=$exit
        rawOutputStored=$false;claim='Read-only existing privilege query'
    }
}

$futureFile = '/etc/systemd/system/deepseek-harness.service.d/90-vm105-provider-profile.conf'
$privilegeReceipts = @(
    New-PrivilegeReceipt 'future-install' '/usr/bin/install' @('-o','root','-g','root','-m','0644','/dev/stdin',$futureFile)
    New-PrivilegeReceipt 'future-remove' '/usr/bin/rm' @('-f','--',$futureFile)
    New-PrivilegeReceipt 'future-stop' '/usr/bin/systemctl' @('stop','deepseek-harness.service')
    New-PrivilegeReceipt 'future-start' '/usr/bin/systemctl' @('start','deepseek-harness.service')
    New-PrivilegeReceipt 'future-reload' '/usr/bin/systemctl' @('daemon-reload')
    New-PrivilegeReceipt 'future-status' '/usr/bin/systemctl' @('show','deepseek-harness.service')
)

function Get-DropInDirectoryObservation {
    $path='/etc/systemd/system/deepseek-harness.service.d'
    try { $stat=(Invoke-StrictSsh @('/usr/bin/stat','-c','%n|%F|%U|%G|%a|%h','--',$path)) -join '' }
    catch { return [pscustomobject]@{path=$path;exists=$false;realDirectory=$false;owner=$null;group=$null;mode=$null;linkStatus='absent';broadAcl=$null;unexpectedMount=$null;verdict='BLOCKED'} }
    $parts=$stat -split '\|',6
    if ($parts.Count -ne 6) { throw 'Malformed drop-in directory metadata' }
    $acl=Invoke-StrictSsh @('/usr/bin/getfacl','-cp','--',$path)
    $mount=(Invoke-StrictSsh @('/usr/bin/findmnt','-n','-o','TARGET','--target',$path)) -join ''
    $broadAcl=@($acl | Where-Object { $_ -match '^(group|other|mask)::.*w' }).Count -gt 0
    $safe=($parts[1] -ceq 'directory' -and $parts[2] -ceq 'root' -and $parts[3] -ceq 'root' -and $parts[4] -ceq '755' -and [int]$parts[5] -eq 1 -and -not $broadAcl -and $mount -ceq '/')
    [pscustomobject]@{path=$path;exists=$true;realDirectory=($parts[1] -ceq 'directory');owner=$parts[2];group=$parts[3];mode=$parts[4];linkStatus='not-link';broadAcl=$broadAcl;unexpectedMount=($mount -cne '/');verdict=$(if($safe){'PASS'}else{'BLOCKED'})}
}

$dropInDirectory=Get-DropInDirectoryObservation
```

Expected parsed result: six typed privilege receipts, each `ALLOWED` or `DENIED` with no raw output, plus one exact directory observation. Any denial or noncompliant/absent directory makes only `cutoverPrerequisites.verdict` `BLOCKED`; it does not rewrite selector proof or authorize repair.

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

Use an injected adapter only inside self-test; production always binds it to strict SSH:

```powershell
function Assert-Initializer {
    param([bool]$Condition,[string]$Message)
    if(-not $Condition){throw $Message}
}

function Invoke-Preparation {
    param([object]$Evidence,[scriptblock]$Adapter,[string]$FailAt)
    $operations=[Collections.Generic.List[string]]::new()
    $ids=@('selector-gate','target-preflight','create-parent','create-root','write-blueprint','metadata','static-validation','secret-scan','service-unchanged','network-unchanged')
    foreach($id in $ids){
        if($id -ceq $FailAt){return [pscustomobject]@{verdict='BLOCKED';checks=@($operations);failedAt=$id}}
        & $Adapter $id $Evidence
        $operations.Add($id)
    }
    return [pscustomobject]@{verdict='PASS';checks=@($operations);failedAt=$null}
}

function Invoke-InitializerSelfTest {
    $evidence=[pscustomobject]@{selectorDiscovery=[pscustomobject]@{verdict='PASS';selectorDigest=('A'*64);candidateBlueprint=[pscustomobject]@{directories=@();files=@();policyAssertions=[pscustomobject]@{activeProviderRoutes=0;automaticFallback=$false}}}}
    foreach($failAt in @('create-parent','create-root','write-blueprint','metadata','static-validation','secret-scan','service-unchanged','network-unchanged')){
        $calls=[Collections.Generic.List[string]]::new()
        $fake={param($id,$record)$calls.Add($id)}
        $result=Invoke-Preparation $evidence $fake $failAt
        Assert-Initializer ($result.verdict -ceq 'BLOCKED') 'failure must block'
        Assert-Initializer ($calls -cnotcontains 'cleanup') 'cleanup forbidden'
        Assert-Initializer (@($calls | Where-Object {$_ -match 'service-(stop|start|restart)|daemon-reload|systemd'}).Count -eq 0) 'service command forbidden'
        $index=[Array]::IndexOf(@('selector-gate','target-preflight','create-parent','create-root','write-blueprint','metadata','static-validation','secret-scan','service-unchanged','network-unchanged'),$failAt)
        Assert-Initializer ($calls.Count -eq $index) 'continued after failure'
    }
    $positiveCalls=[Collections.Generic.List[string]]::new()
    $positive=Invoke-Preparation $evidence {param($id,$record)$positiveCalls.Add($id)} ''
    Assert-Initializer ($positive.verdict -ceq 'PASS' -and $positiveCalls.Count -eq 10) 'positive sequence incomplete'
}
```

Require exactly one mode. Before constructing SSH, reject a non-`PASS`/unaccepted selector, digest drift, unsafe or existing target/parent, blueprint/hash/path/mode/reference failure, provider/OAuth/secret content, and every destination outside `/home/dsh/.dsh-profiles/vm105-provider-v1`. Inject a fake SSH adapter only in self-test.

Fail each post-create operation in turn: parent creation, candidate-root creation, each directory/file write, metadata verification, static validation, secret scan, and unchanged-service/network check. After the first failure, assert `candidatePreparation.verdict: BLOCKED`, no later write, no cleanup/remove/repair, no service/systemd command, and no old-profile operation. Preserve candidate paths already created before failure for review. The positive synthetic run executes every planned candidate write once and zero service/systemd operations.

Expected RED from `./scripts/Initialize-VM105ProviderProfile.ps1 -AcceptedSelectorDigest ('A'*64) -SelfTest`: nonzero exit with `continued after failure` until stop-on-first-failure is implemented. Expected GREEN: exit 0 with `SELF_TEST_PASS failures=8 positive=1` and zero SSH calls.

- [ ] **Step 2: Implement the fixed-path preparation lane**

The `-Prepare` path first reruns the Task 1 selector validator and revalidates VM/SSH identity, service active baseline, listener, selector digest, candidate ancestor metadata, and exact parent/target absence. It then uses one sequential `dsh` writer lane with `umask 077` to:

1. Create exactly `/home/dsh/.dsh-profiles` and `/home/dsh/.dsh-profiles/vm105-provider-v1` as real `dsh:dsh` mode `0700` directories.
2. Create only blueprint directories/files below the candidate; transfer reviewed secret-free file bytes through standard input without shell evaluation.
3. Verify local and VM-side nonsecret file SHA-256, `dsh:dsh` ownership, 0700 directories, 0600-or-narrower regular files, link count one, no symbolic links, no broad ACL, and no unexpected mount.
4. Run only the installed static-validation argv proved in the blueprint. If no safe static syntax validator exists, record syntax `NOT PROVEN`; if the uncertainty weakens loopback/zero-route/fallback isolation, set `BLOCKED`.
5. Read only newly created candidate files through the value-suppressing scanner.
6. Revalidate the existing service is active and unchanged, loopback-only, locally healthy, UFW unchanged with no TCP 3080 allowance, and direct LAN TCP 3080 denied.

The initializer has no service/systemd/sudo command and rejects such an operation in evidence or adapter input. It never starts Harness against the candidate. Any post-create failure records `BLOCKED`, stops remaining writes, and leaves the candidate untouched for review; it does not delete, repair, or normalize it.

Implement path confinement and atomic SSH/stdin transfer with these concrete functions:

```powershell
$candidateRoot='/home/dsh/.dsh-profiles/vm105-provider-v1'
$sshBaseArgs=@('-i',$SshKey,'-o','BatchMode=yes','-o','IdentitiesOnly=yes','-o','StrictHostKeyChecking=yes',$SshTarget)

function Resolve-CandidatePath {
    param([string]$RelativePath)
    if(-not $RelativePath -or $RelativePath.StartsWith('/') -or $RelativePath -match '(^|/)\.\.(/|$)|[\x00-\x1f;&|`$<>]'){throw 'unsafe candidate path'}
    $normalized=($RelativePath -replace '\\','/').Trim('/')
    $absolute="$candidateRoot/$normalized"
    if(-not $absolute.StartsWith("$candidateRoot/",[StringComparison]::Ordinal)){throw 'candidate path escape'}
    return $absolute
}

function Invoke-SshProcess {
    param([string[]]$RemoteArgv,[byte[]]$StandardInput,[int]$TimeoutSeconds=30)
    $deny=@('sudo','systemctl','service','initctl','shutdown','reboot')
    if($deny -contains [IO.Path]::GetFileNameWithoutExtension($RemoteArgv[0])){throw 'service/systemd/sudo command forbidden'}
    $psi=[Diagnostics.ProcessStartInfo]::new((Get-Command ssh.exe).Source)
    $psi.UseShellExecute=$false;$psi.RedirectStandardInput=$true;$psi.RedirectStandardOutput=$true;$psi.RedirectStandardError=$true
    foreach($arg in @($sshBaseArgs+'--'+$RemoteArgv)){[void]$psi.ArgumentList.Add($arg)}
    $p=[Diagnostics.Process]::Start($psi)
    if($StandardInput){$p.StandardInput.BaseStream.Write($StandardInput,0,$StandardInput.Length)}
    $p.StandardInput.Close()
    if(-not $p.WaitForExit($TimeoutSeconds*1000)){$p.Kill($true);throw 'SSH timeout'}
    $stdout=$p.StandardOutput.ReadToEnd();[void]$p.StandardError.ReadToEnd()
    if($p.ExitCode -ne 0){throw "SSH exit $($p.ExitCode)"}
    return @($stdout -split "`r?`n"|Where-Object Length)
}

function Write-CandidateFile {
    param([object]$File)
    $path=Resolve-CandidatePath $File.relativePath
    $bytes=[Text.Encoding]::UTF8.GetBytes((@($File.contentLines)-join "`n")+"`n")
    $digest=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))
    if($digest -cne $File.contentSha256){throw 'candidate content digest mismatch'}
    [void](Invoke-SshProcess @('/usr/bin/install','-m',[string]$File.mode,'/dev/stdin',$path) $bytes)
}

[void](Invoke-SshProcess @('/usr/bin/install','-d','-m','0700','--','/home/dsh/.dsh-profiles','/home/dsh/.dsh-profiles/vm105-provider-v1') $null)
foreach($directory in @($record.selectorDiscovery.candidateBlueprint.directories)){
    [void](Invoke-SshProcess @('/usr/bin/install','-d','-m','0700','--',(Resolve-CandidatePath $directory.relativePath)) $null)
}
foreach($file in @($record.selectorDiscovery.candidateBlueprint.files)){Write-CandidateFile $file}
```

Preflight must establish both fixed directories are absent before the single `install -d` call; if either exists, do not call it. Unknown selector or static-validator syntax is never embedded above. After the validator confirms `staticValidation.executable` is package-owned and its atomic argv contains the fixed candidate value, invoke exactly:

```powershell
$static=$record.selectorDiscovery.candidateBlueprint.staticValidation
if($static.supported){
    $staticArgv=@([string]$static.executable)+@($static.argv)
    $parsed=Invoke-SshProcess $staticArgv $null ([int]$static.timeoutSeconds)
    if(@($static.acceptedResults) -cnotcontains ($parsed -join "`n")){throw 'static validation result rejected'}
}
```

Collect metadata with fixed `/usr/bin/stat -c %n|%F|%U|%G|%a|%h`, `/usr/bin/getfacl -cp`, `/usr/bin/findmnt -n -o TARGET --target`, and `/usr/bin/sha256sum --` argv for each newly created path. Parse into `CandidateMetadataV1`; never persist raw output. Reuse the Task 1 allowlisted `systemctl show`, listener, HTTP, UFW, and bounded `.NET TcpClient` readers without any lifecycle command. Expected result is ten ordered checks: checks 1-8 `PASS`, service/network equality checks `PASS`, `runtimeVerdict=NOT PROVEN`, and a mutation ledger containing only fixed-path `CREATE_DIRECTORY`/`WRITE_FILE` entries.

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

Build the exact non-executable Markdown body from accepted fields, inspect it for unsafe sections, then create the handoff with `apply_patch`:

```powershell
$record=Get-Content -Raw 'docs/evidence/vm105-profile-pointer-preparation.json'|ConvertFrom-Json
$selectorDigest=[string]$record.selectorDiscovery.selectorDigest
$candidateDigest=[string]$record.candidatePreparation.candidateDigest
$privilegeVerdict=[string]$record.cutoverPrerequisites.privilegeSeam.verdict
$directoryVerdict=[string]$record.cutoverPrerequisites.dropInDirectory.verdict
$handoff=@"
# VM105 profile cutover requirements handoff

Status: preparation only; no cutover or credential authority
Repository: https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git
Branch: codex/vm105-authoritative-roadmap
VM: deepseek-harness-01 at $($record.target.address)
Service: deepseek-harness.service as dsh:dsh
Candidate: /home/dsh/.dsh-profiles/vm105-provider-v1
Future drop-in directory: /etc/systemd/system/deepseek-harness.service.d
Future drop-in file: /etc/systemd/system/deepseek-harness.service.d/90-vm105-provider-profile.conf
Selector digest: $selectorDigest
Candidate digest: $candidateDigest
Privilege seam: $privilegeVerdict
Drop-in directory: $directoryVerdict

## Preparation verdicts

Selector: $($record.selectorDiscovery.verdict)
Candidate static validation: $($record.candidatePreparation.verdict)
Candidate runtime: NOT PROVEN

## Residual NOT PROVEN facts

Effective selected-store paths at runtime; candidate service startup; post-switch listener, HTTP, UFW, and direct-LAN posture; provider routes; credentials; native OAuth; inference; attribution; measured maintenance duration; rollback execution.

## Preservation boundary

The current profile was never read or copied. Preparation made no service, systemd, drop-in, firewall, provider, credential, OAuth, package, or VM-power change.

## Requirements for a separate cutover plan

Fresh baseline and drift proof; independently reviewed immutable packet; selector-only service delta; one post-stop/pre-pointer old-root root-only lstat; one switch attempt; one automatic rollback sequence; all eleven approved acceptance checks; terminal ROLLBACK_FAILED handling; old-profile retention; separate credential gate after accepted cutover.

This handoff is requirements input only and grants no authority.
"@
if($handoff -match '(?m)^```|\b(argv|Invoke-|systemctl\s+(stop|start|restart)|daemon-reload|sudo\s)\b'){throw 'Executable handoff content rejected'}
$handoff
```

Expected parsed result: exact accepted digests and fixed targets, bounded prerequisite verdicts, all residual facts present as `NOT PROVEN`, and no executable command content. Use the printed body as the exact `apply_patch` content; do not write it with shell redirection.

- [ ] **Step 2: Populate closeout and validate the handoff boundary**

Compute the handoff's nonsecret SHA-256. Populate `closeout` with `PREPARATION_READY` only when selector and candidate verdicts/reviews/digests remain accepted; otherwise use `BLOCKED`. The validator's Closeout stage must reject executable command blocks, command/argv/controller schemas, action-time approval markers, credential authority, digest drift, omitted residual verdicts, or disagreement between handoff and JSON.

Use this exact closeout shape and then apply it to the JSON with `apply_patch`:

```powershell
$handoffPath='docs/handoffs/2026-09-08-vm105-profile-cutover-requirements.md'
$handoffBytes=[IO.File]::ReadAllBytes((Resolve-Path $handoffPath))
$handoffSha=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($handoffBytes))
$ready=($record.selectorDiscovery.verdict -ceq 'PASS' -and $record.selectorDiscovery.review.status -ceq 'ACCEPTED' -and $record.candidatePreparation.verdict -ceq 'PASS' -and $record.candidatePreparation.review.status -ceq 'ACCEPTED')
$closeout=[ordered]@{
    closedAt=(Get-Date).ToUniversalTime().ToString('o')
    verdict=$(if($ready){'PREPARATION_READY'}else{'BLOCKED'})
    selectorDigest=[string]$record.selectorDiscovery.selectorDigest
    candidateDigest=[string]$record.candidatePreparation.candidateDigest
    cutoverPrerequisiteVerdict=[string]$record.cutoverPrerequisites.verdict
    handoffPath=$handoffPath
    handoffSha256=$handoffSha
    review=[ordered]@{status='PENDING';reviewedAt=$null;reviewer=$null;reviewedDigest=$null;findings=@()}
}
```

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

Expected RED before creating the handoff and closeout object: nonzero exit with `Missing closeout handoff`. Expected GREEN after both agree: exit 0 with `CLOSEOUT_PASS verdict=PREPARATION_READY` or the exact reviewed `BLOCKED` verdict.

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
