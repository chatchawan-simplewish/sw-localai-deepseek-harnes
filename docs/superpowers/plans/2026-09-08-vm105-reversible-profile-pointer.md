# VM105 Secret-Free Profile Preparation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove or block the installed whole-profile selector, prepare the fixed secret-free candidate only after selector proof, and hand off independently reviewed cutover requirements without building or executing cutover.

**Architecture:** One typed JSON record carries sanitized selector proof, read-only future-cutover prerequisite status, the candidate blueprint, and static preparation results. A dependency-free validator enforces proof-source separation and fail-closed policy; a bounded initializer can write only the fixed candidate tree and can never mutate the service or systemd. Cutover code, root mutation commands, maintenance restart, post-cutover evidence, and credential work are deliberately excluded and require a separate follow-up plan after this preparation succeeds and fresh cutover authority is granted.

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
| `create-parent`, `create-root` | `CandidateDirectoryMutationV1` | `path`, `attempted`, `completed`, `metadata`; `metadata` is `null` before/after a failed create or the exact `CandidateDirectoryMetadataV1` object below |
| `write-blueprint` | `BlueprintWriteV1` | `plannedWrites`, `completedWrites`, `lastOperationOrder`; counts are nonnegative, completed never exceeds planned, and a `PASS` completes every planned write |
| `metadata` | `CandidateMetadataSetV1` | `available`, `directories`, `files`, `allSafe`, `allDigestsMatch`; arrays contain only exact directory/file metadata objects, and `PASS` requires availability plus both booleans |
| `static-validation` | `StaticValidationV1` | `supported`, `exitCode`, `parsedResult`; `NOT PROVEN` is permitted only when the blueprint declares the validator unsupported and the already parsed loopback/zero-route/fallback assertions remain exact; otherwise uncertainty is `BLOCKED` |
| `secret-scan` | `SecretScanV1` | `available`, `filesScanned`, `findingCount`, `categories`; matching values are never present and `PASS` requires zero findings |
| `service-unchanged` | `ServiceBaselineV1` | `available`, `activeState`, `subState`, `user`, `group`, `execStart`, `workingDirectory`, `umask`, `result`, `nRestarts`, `matchesBaseline` |
| `network-unchanged` | `NetworkBaselineV1` | `available`, `listeners`, `localHttpStatus`, `ufwActive`, `tcp3080Allowed`, `directLanDenied`, `matchesBaseline` |

`CandidateDirectoryMetadataV1` is exactly `path`, `objectType`, `symlink`, `owner`, `group`, `mode`, `aclBroad`, and `unexpectedMount`. `CandidateFileMetadataV1` is exactly those fields plus `linkCount` and `contentSha256`. No safe parser may return an opaque or additional property.

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
    Assert-True ($null -ne $Value -and $Value -isnot [string] -and $Value -isnot [Collections.IEnumerable]) "$Label object"
    $actual = @($Value.psobject.Properties.Name | Sort-Object)
    $wanted = @($Expected | Sort-Object)
    Assert-True (($actual -join "`n") -ceq ($wanted -join "`n")) "$Label keys differ"
}

function Assert-String { param([object]$Value,[string]$Label,[switch]$AllowEmpty) Assert-True ($Value -is [string] -and ($AllowEmpty -or -not [string]::IsNullOrWhiteSpace($Value)) -and $Value -notmatch '[\x00-\x08\x0b\x0c\x0e-\x1f]') "$Label string" }
function Assert-Bool { param([object]$Value,[string]$Label) Assert-True ($Value -is [bool]) "$Label bool" }
function Assert-Int { param([object]$Value,[string]$Label,[int64]$Min=([int64]::MinValue),[int64]$Max=([int64]::MaxValue)) Assert-True ($Value -is [byte] -or $Value -is [int16] -or $Value -is [int32] -or $Value -is [int64]) "$Label integer"; Assert-True ([int64]$Value -ge $Min -and [int64]$Value -le $Max) "$Label range" }
function Assert-Array { param([object]$Value,[string]$Label) Assert-True ($null -ne $Value -and $Value -is [Collections.IEnumerable] -and $Value -isnot [string] -and $Value -isnot [Collections.IDictionary]) "$Label array" }
function Assert-IsoTime { param([object]$Value,[string]$Label,[switch]$AllowNull) if($AllowNull -and $null-eq$Value){return}; Assert-String $Value $Label; $parsed=[DateTimeOffset]::MinValue; Assert-True ([DateTimeOffset]::TryParseExact($Value,'o',[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::None,[ref]$parsed)) "$Label timestamp" }
function Assert-Digest { param([object]$Value,[string]$Label,[switch]$AllowNull) if($AllowNull -and $null-eq$Value){return}; Assert-True ($Value -is [string] -and $Value -cmatch '^[A-F0-9]{64}$') "$Label digest" }
function Assert-StringArray { param([object]$Value,[string]$Label,[switch]$RequireAny) Assert-Array $Value $Label; if($RequireAny){Assert-True (@($Value).Count-gt0) "$Label empty"}; foreach($item in @($Value)){Assert-String $item "$Label item"} }
function Assert-Blockers { param([object]$Value,[bool]$Required,[string]$Label) Assert-StringArray $Value $Label; Assert-True ((@($Value).Count-gt0)-eq$Required) "$Label count" }

function Assert-Throws {
    param([scriptblock]$Action, [string]$Pattern)
    try { & $Action; throw 'Expected rejection was not raised' }
    catch { Assert-True ($_.Exception.Message -match $Pattern) "Wrong rejection category"; $script:NegativeTestCount++ }
}

function Copy-SyntheticRecord {
    param([object]$Value)
    return ($Value | ConvertTo-Json -Depth 100 | ConvertFrom-Json)
}

function Get-UpperSha256 {
    param([byte[]]$Bytes)
    return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($Bytes))
}

function Assert-StrictPosixPath {
    param([string]$Path,[string]$Root,[switch]$AllowRoot)
    Assert-True (-not [string]::IsNullOrWhiteSpace($Path)) 'posix-path-empty'
    Assert-True ($Path[0] -ceq '/') 'posix-path-relative'
    Assert-True ($Path -notmatch '\\|//|(^|/)\.\.?(/|$)|[\x00-\x1f]') 'posix-path-shape'
    Assert-True ($Root -match '^/(?:[A-Za-z0-9._-]+/)*[A-Za-z0-9._-]+$') 'posix-root-shape'
    $inside = $Path.StartsWith("$Root/",[StringComparison]::Ordinal)
    Assert-True ($inside -or ($AllowRoot -and $Path -ceq $Root)) 'posix-path-root'
}

function Assert-StrictPosixRelativePath {
    param([string]$Path)
    Assert-True (-not [string]::IsNullOrWhiteSpace($Path)) 'relative-path-empty'
    Assert-True ($Path[0] -cne '/') 'relative-path-rooted'
    Assert-True ($Path -notmatch '\\|//|(^|/)\.\.?(/|$)|[\x00-\x1f;&|`$<>]') 'relative-path-shape'
}

function ConvertTo-CanonicalNode {
    param([object]$Value)
    if ($null -eq $Value) { return $null }
    if ($Value -is [string] -or $Value -is [ValueType]) { return $Value }
    if ($Value -is [Collections.IDictionary]) {
        $ordered=[ordered]@{}; foreach($key in @($Value.Keys | Sort-Object)){ $ordered[[string]$key]=ConvertTo-CanonicalNode $Value[$key] }; return $ordered
    }
    if ($Value -is [Collections.IEnumerable]) { return @($Value | ForEach-Object { ConvertTo-CanonicalNode $_ }) }
    $object=[ordered]@{}; foreach($property in @($Value.psobject.Properties.Name | Sort-Object)){ $object[$property]=ConvertTo-CanonicalNode $Value.$property }; return $object
}

function Get-CanonicalStageDigest {
    param([object]$Stage,[string[]]$OmitTopLevelKeys)
    $copy=[ordered]@{}
    foreach($property in @($Stage.psobject.Properties.Name | Sort-Object)){
        if($OmitTopLevelKeys -ccontains $property){continue}
        $copy[$property]=ConvertTo-CanonicalNode $Stage.$property
    }
    return Get-UpperSha256 ([Text.Encoding]::UTF8.GetBytes(($copy | ConvertTo-Json -Depth 100 -Compress)))
}

function Assert-InstalledSourceRef {
    param([object]$Ref, [string]$PackageRoot)
    Assert-True ($Ref.sourceClass -ceq 'installed-source') 'proof-source-class'
    Assert-ExactKeys $Ref @('sourceClass','path','sha256','lineStart','lineEnd','claim') 'installedSourceRef'
    Assert-String $Ref.path 'installed-source-path'; Assert-Digest $Ref.sha256 'installed-source'
    Assert-Int $Ref.lineStart 'installed-source-lineStart' 1; Assert-Int $Ref.lineEnd 'installed-source-lineEnd' $Ref.lineStart
    if($Ref.path -ceq '/usr/local/bin/dsh'){Assert-StrictPosixPath $Ref.path '/usr/local/bin' }
    else { Assert-StrictPosixPath $Ref.path $PackageRoot -AllowRoot }
    Assert-True (($Ref.path -ceq '/usr/local/bin/dsh') -or $Ref.path.StartsWith("$PackageRoot/", [StringComparison]::Ordinal)) 'installed-source-root'
    Assert-String $Ref.claim 'installed-source-claim'
}

function Assert-SanitizedUnitRef {
    param([object]$Ref,[string]$SelectorKey)
    $allowed = @('User','Group','ExecStart','WorkingDirectory','UMask','FragmentPath','DropInPaths','ActiveState','SubState','Result','NRestarts')
    if($SelectorKey -match '^[A-Z][A-Z0-9_]{1,63}$'){$allowed += $SelectorKey}
    Assert-ExactKeys $Ref @('sourceClass','observationId','capturedAt','propertyAllowlist','observations','claim') 'sanitizedUnitRef'
    Assert-True ($Ref.sourceClass -ceq 'sanitized-unit') 'proof-source-class'
    Assert-String $Ref.observationId 'unit-observation-id'; Assert-IsoTime $Ref.capturedAt 'unit-capturedAt'
    Assert-Array $Ref.propertyAllowlist 'unit-property-allowlist'; Assert-Array $Ref.observations 'unit-observations'
    Assert-True (@($Ref.propertyAllowlist).Count -gt 0) 'unit-property-allowlist-empty'
    Assert-True (@($Ref.propertyAllowlist | Select-Object -Unique).Count -eq @($Ref.propertyAllowlist).Count) 'unit-property-allowlist-duplicate'
    foreach($name in @($Ref.propertyAllowlist)){Assert-True ($allowed -ccontains [string]$name) 'unit-property-allowlist'}
    $seen=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach ($item in @($Ref.observations)) {
        Assert-ExactKeys $item @('name','value') 'sanitizedUnitObservation'
        Assert-True ($Ref.propertyAllowlist -ccontains [string]$item.name) 'unit-property-allowlist'
        Assert-True ($seen.Add([string]$item.name)) 'unit-property-duplicate'
        Assert-String $item.name 'unit-property-name'; Assert-String $item.value 'unit-property-value' -AllowEmpty
        Assert-True ($item.value -notmatch "`r|`n") 'unit-property-value-shape'
        if($item.name -ceq 'User' -or $item.name -ceq 'Group'){Assert-True ($item.value -ceq 'dsh') 'unit-identity'}
        if($item.name -ceq 'ActiveState'){Assert-True ($item.value -ceq 'active') 'unit-active'}
        if($item.name -ceq 'SubState'){Assert-True ($item.value -ceq 'running') 'unit-running'}
        if($item.name -ceq 'NRestarts'){Assert-True ($item.value -cmatch '^\d+$') 'unit-restarts'}
        if($item.name -ceq $SelectorKey){Assert-True ($item.value -ceq 'ABSENT' -or $item.value -cmatch '^/[A-Za-z0-9._/-]+$') 'unit-selector-value'}
    }
    Assert-True ($seen.Count -eq @($Ref.propertyAllowlist).Count) 'unit-property-incomplete'
    Assert-String $Ref.claim 'unit-claim'
}

function Assert-PrivilegeReceiptRef {
    param([object]$Ref)
    Assert-ExactKeys $Ref @('sourceClass','operationId','capturedAt','queryUser','sudoPath','targetExecutable','targetArgv','noninteractive','result','exitCode','rawOutputStored','claim') 'privilegeReceiptRef'
    Assert-True ($Ref.sourceClass -ceq 'privilege-receipt') 'proof-source-class'
    Assert-String $Ref.operationId 'privilege-operation'; Assert-IsoTime $Ref.capturedAt 'privilege-capturedAt'
    Assert-String $Ref.queryUser 'privilege-user'; Assert-String $Ref.sudoPath 'privilege-sudo'; Assert-String $Ref.targetExecutable 'privilege-executable'; Assert-StringArray $Ref.targetArgv 'privilege-argv'
    Assert-Bool $Ref.noninteractive 'privilege-noninteractive'; Assert-String $Ref.result 'privilege-result'; Assert-Int $Ref.exitCode 'privilege-exitCode'; Assert-Bool $Ref.rawOutputStored 'privilege-raw-output'
    Assert-True (($Ref.queryUser -ceq 'dsh') -and $Ref.noninteractive -and -not $Ref.rawOutputStored) 'privilege-receipt-safety'
    Assert-True ($Ref.sudoPath -ceq '/usr/bin/sudo') 'privilege-receipt-sudo'
    Assert-True (@('ALLOWED','DENIED') -ccontains [string]$Ref.result) 'privilege-receipt-result'
    Assert-True (($Ref.exitCode -eq 0) -eq ($Ref.result -ceq 'ALLOWED')) 'privilege-receipt-exit'
    Assert-String $Ref.claim 'privilege-receipt-claim'
}

function Assert-PrivilegeSeam {
    param([object[]]$Receipts,[string]$FutureFile)
    $expected=[ordered]@{
        'future-install'=@('/usr/bin/install','-o','root','-g','root','-m','0644','/dev/stdin',$FutureFile)
        'future-remove'=@('/usr/bin/rm','-f','--',$FutureFile)
        'future-stop'=@('/usr/bin/systemctl','stop','deepseek-harness.service')
        'future-start'=@('/usr/bin/systemctl','start','deepseek-harness.service')
        'future-reload'=@('/usr/bin/systemctl','daemon-reload')
        'future-status'=@('/usr/bin/systemctl','show','deepseek-harness.service')
    }
    Assert-True ($Receipts.Count -eq 6) 'privilege-receipt-count'
    Assert-True (@($Receipts.operationId | Select-Object -Unique).Count -eq 6) 'privilege-receipt-duplicate'
    foreach($receipt in $Receipts){
        Assert-PrivilegeReceiptRef $receipt
        Assert-True ($expected.Contains([string]$receipt.operationId)) 'privilege-receipt-id'
        $spec=$expected[[string]$receipt.operationId]
        Assert-True ($receipt.targetExecutable -ceq $spec[0]) 'privilege-receipt-executable'
        Assert-True ((@($receipt.targetArgv) -join "`0") -ceq (@($spec[1..($spec.Count-1)]) -join "`0")) 'privilege-receipt-argv'
    }
}

function Assert-Review {
    param([object]$Review,[string]$Digest,[string[]]$AllowedStatus)
    Assert-ExactKeys $Review @('status','reviewedAt','reviewer','reviewedDigest','findings') 'review'
    Assert-String $Review.status 'review-status'; Assert-True ($AllowedStatus -ccontains $Review.status) 'review-status-value'; Assert-Array $Review.findings 'review-findings'
    foreach($finding in @($Review.findings)){Assert-String $finding 'review-finding'}
    if($Review.status-ceq'PENDING'){Assert-True ($null-eq$Review.reviewedAt -and $null-eq$Review.reviewer -and $null-eq$Review.reviewedDigest -and @($Review.findings).Count-eq0) 'review-pending-fields'}
    else {Assert-IsoTime $Review.reviewedAt 'reviewedAt';Assert-String $Review.reviewer 'reviewer';Assert-Digest $Review.reviewedDigest 'reviewedDigest';Assert-True ($Review.reviewedDigest-ceq$Digest) 'review-digest';if($Review.status-ceq'ACCEPTED'){Assert-True (@($Review.findings).Count-eq0) 'accepted-review-findings'}else{Assert-True (@($Review.findings).Count-gt0) 'rejected-review-findings'}}
}

function Assert-Target {
    param([object]$Target)
    Assert-ExactKeys $Target @('hostname','address','sshHostKeyIdentity','service','serviceUser','serviceGroup','candidateRoot','listenerHost','listenerPort','futureDropInDirectory','futureDropInFile') 'target'
    foreach($name in @('hostname','address','sshHostKeyIdentity','service','serviceUser','serviceGroup','candidateRoot','listenerHost','futureDropInDirectory','futureDropInFile')){Assert-String $Target.$name "target-$name"}
    Assert-Int $Target.listenerPort 'target-listenerPort' 1 65535
    Assert-True ($Target.hostname-ceq'deepseek-harness-01' -and $Target.address-ceq'192.168.1.139' -and $Target.service-ceq'deepseek-harness.service' -and $Target.serviceUser-ceq'dsh' -and $Target.serviceGroup-ceq'dsh' -and $Target.candidateRoot-ceq'/home/dsh/.dsh-profiles/vm105-provider-v1' -and $Target.listenerHost-ceq'127.0.0.1' -and $Target.listenerPort-eq3080 -and $Target.futureDropInDirectory-ceq'/etc/systemd/system/deepseek-harness.service.d' -and $Target.futureDropInFile-ceq'/etc/systemd/system/deepseek-harness.service.d/90-vm105-provider-profile.conf') 'target-values'
}

function Assert-InstalledEntrypoint {
    param([object]$Installed)
    Assert-ExactKeys $Installed @('wrapperPath','wrapperType','wrapperSymlink','wrapperOwner','wrapperGroup','wrapperMode','wrapperLinkCount','wrapperSha256','entrypointPath','entrypointType','entrypointSymlink','entrypointOwner','entrypointGroup','entrypointMode','entrypointLinkCount','entrypointSha256','packageRoot','packageName','packageVersion','proofRefs') 'installedEntrypoint'
    foreach($name in @('wrapperPath','wrapperType','wrapperOwner','wrapperGroup','wrapperMode','entrypointPath','entrypointType','entrypointOwner','entrypointGroup','entrypointMode','packageRoot','packageName','packageVersion')){Assert-String $Installed.$name "installed-$name"}
    Assert-Bool $Installed.wrapperSymlink 'wrapperSymlink';Assert-Bool $Installed.entrypointSymlink 'entrypointSymlink';Assert-Int $Installed.wrapperLinkCount 'wrapperLinkCount' 1 1;Assert-Int $Installed.entrypointLinkCount 'entrypointLinkCount' 1 1;Assert-Digest $Installed.wrapperSha256 'wrapperSha256';Assert-Digest $Installed.entrypointSha256 'entrypointSha256';Assert-Array $Installed.proofRefs 'installed-proofRefs'
    Assert-StrictPosixPath $Installed.packageRoot '/opt/deepseek-harness' -AllowRoot;Assert-StrictPosixPath $Installed.entrypointPath $Installed.packageRoot
    Assert-True ($Installed.wrapperPath-ceq'/usr/local/bin/dsh' -and $Installed.wrapperType-ceq'regular file' -and -not$Installed.wrapperSymlink -and $Installed.wrapperOwner-ceq'root' -and $Installed.wrapperGroup-ceq'root' -and ([Convert]::ToInt32($Installed.wrapperMode,8)-band18)-eq0 -and $Installed.entrypointType-ceq'regular file' -and -not$Installed.entrypointSymlink -and $Installed.entrypointOwner-ceq'root' -and $Installed.entrypointGroup-ceq'root' -and ([Convert]::ToInt32($Installed.entrypointMode,8)-band18)-eq0) 'installed-entrypoint-fields'
    Assert-True (@($Installed.proofRefs).Count-gt0) 'installed-proof-empty';foreach($ref in @($Installed.proofRefs)){Assert-InstalledSourceRef $ref $Installed.packageRoot}
}

function Assert-Baseline {
    param([object]$Baseline,[string]$SelectorKey)
    Assert-ExactKeys $Baseline @('repositoryOrigin','branch','capturedAt','hostname','address','sshHostKeyIdentity','installedVersion','service','listeners','localHttp','ufw','directLanDenied') 'selectorBaseline'
    foreach($name in @('repositoryOrigin','branch','hostname','address','sshHostKeyIdentity','installedVersion')){Assert-String $Baseline.$name "baseline-$name"};Assert-IsoTime $Baseline.capturedAt 'baseline-capturedAt'
    Assert-True ($Baseline.repositoryOrigin-ceq'https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git' -and $Baseline.branch-ceq'codex/vm105-authoritative-roadmap' -and $Baseline.hostname-ceq'deepseek-harness-01' -and $Baseline.address-ceq'192.168.1.139' -and $Baseline.installedVersion-match'0\.1\.1-rc\.2') 'baseline-identity'
    Assert-SanitizedUnitRef $Baseline.service $SelectorKey;Assert-Array $Baseline.listeners 'baseline-listeners';Assert-True (@($Baseline.listeners).Count-gt0) 'baseline-listeners-empty'
    foreach($listener in @($Baseline.listeners)){Assert-ExactKeys $listener @('address','port','protocol') 'baselineListener';Assert-String $listener.address 'listener-address';Assert-Int $listener.port 'listener-port' 3080 3080;Assert-String $listener.protocol 'listener-protocol';Assert-True (@('127.0.0.1','::1')-ccontains$listener.address -and $listener.protocol-ceq'tcp') 'baseline-listener'}
    Assert-ExactKeys $Baseline.localHttp @('url','statusCode','exitCode') 'baselineHttp';Assert-String $Baseline.localHttp.url 'http-url';Assert-Int $Baseline.localHttp.statusCode 'http-status' 200 200;Assert-Int $Baseline.localHttp.exitCode 'http-exit' 0 0;Assert-True ($Baseline.localHttp.url-ceq'http://127.0.0.1:3080/') 'http-url-value'
    Assert-ExactKeys $Baseline.ufw @('active','defaults','ruleIds','tcp3080Allowed') 'baselineUfw';Assert-Bool $Baseline.ufw.active 'ufw-active';Assert-String $Baseline.ufw.defaults 'ufw-defaults';Assert-StringArray $Baseline.ufw.ruleIds 'ufw-ruleIds';Assert-Bool $Baseline.ufw.tcp3080Allowed 'ufw-tcp3080';Assert-True ($Baseline.ufw.active -and -not$Baseline.ufw.tcp3080Allowed) 'baseline-ufw'
    Assert-ExactKeys $Baseline.directLanDenied @('source','destination','port','denied','timeoutMs') 'baselineDirectLan';Assert-String $Baseline.directLanDenied.source 'direct-source';Assert-String $Baseline.directLanDenied.destination 'direct-destination';Assert-Int $Baseline.directLanDenied.port 'direct-port' 3080 3080;Assert-Bool $Baseline.directLanDenied.denied 'direct-denied';Assert-Int $Baseline.directLanDenied.timeoutMs 'direct-timeout' 1 5000;Assert-True ($Baseline.directLanDenied.denied) 'baseline-direct-denial'
}

function Assert-CandidateBlueprint {
    param([object]$Blueprint,[string]$PackageRoot,[string]$CandidateRoot)
    Assert-ExactKeys $Blueprint @('directories','files','staticValidation','policyAssertions') 'candidateBlueprint';Assert-Array $Blueprint.directories 'candidate-directories';Assert-Array $Blueprint.files 'candidate-files'
    $paths=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach($directory in @($Blueprint.directories)){Assert-ExactKeys $directory @('relativePath','owner','group','mode','contentSource','sourceRefs') 'candidateDirectory';Assert-StrictPosixRelativePath $directory.relativePath;Assert-True ($paths.Add($directory.relativePath)) 'candidate-path-duplicate';foreach($name in @('owner','group','mode','contentSource')){Assert-String $directory.$name "candidate-directory-$name"};Assert-True ($directory.owner-ceq'dsh' -and $directory.group-ceq'dsh' -and $directory.mode-ceq'0700' -and @('installed-default','approved-setting')-ccontains$directory.contentSource) 'candidate-directory';Assert-Array $directory.sourceRefs 'candidate-directory-sourceRefs';Assert-True (@($directory.sourceRefs).Count-gt0) 'candidate-source-empty';foreach($ref in @($directory.sourceRefs)){Assert-InstalledSourceRef $ref $PackageRoot}}
    foreach($file in @($Blueprint.files)){Assert-ExactKeys $file @('relativePath','owner','group','mode','contentLines','contentSha256','contentSource','sourceRefs') 'candidateFile';Assert-StrictPosixRelativePath $file.relativePath;Assert-True ($paths.Add($file.relativePath)) 'candidate-path-duplicate';foreach($name in @('owner','group','mode','contentSource')){Assert-String $file.$name "candidate-file-$name"};Assert-True ($file.owner-ceq'dsh' -and $file.group-ceq'dsh' -and ([Convert]::ToInt32($file.mode,8)-band63)-eq0 -and @('installed-default','approved-setting')-ccontains$file.contentSource) 'candidate-file';Assert-StringArray $file.contentLines 'candidate-contentLines';Assert-Digest $file.contentSha256 'candidate-contentSha256';$bytes=[Text.Encoding]::UTF8.GetBytes((@($file.contentLines)-join"`n")+"`n");Assert-True ((Get-UpperSha256 $bytes)-ceq$file.contentSha256) 'candidate-content-digest';Assert-Array $file.sourceRefs 'candidate-file-sourceRefs';Assert-True (@($file.sourceRefs).Count-gt0) 'candidate-source-empty';foreach($ref in @($file.sourceRefs)){Assert-InstalledSourceRef $ref $PackageRoot}}
    $static=$Blueprint.staticValidation;Assert-ExactKeys $static @('supported','executable','argv','timeoutSeconds','parser','acceptedResults','sourceRefs') 'staticValidation';Assert-Bool $static.supported 'static-supported';Assert-Int $static.timeoutSeconds 'static-timeout' 1 60;Assert-String $static.parser 'static-parser';Assert-Array $static.argv 'static-argv';Assert-Array $static.acceptedResults 'static-results';Assert-Array $static.sourceRefs 'static-sourceRefs';foreach($ref in @($static.sourceRefs)){Assert-InstalledSourceRef $ref $PackageRoot}
    if($static.supported){Assert-String $static.executable 'static-executable';Assert-StrictPosixPath $static.executable $PackageRoot;Assert-StringArray $static.argv 'static-argv' -RequireAny;Assert-StringArray $static.acceptedResults 'static-results' -RequireAny;Assert-True (@($static.argv|Where-Object{$_-ceq$CandidateRoot}).Count-eq1) 'static-candidate-argv';Assert-True ($static.parser-cmatch'^[A-Za-z][A-Za-z0-9]{1,31}V1$' -and $static.parser-cne'NoneV1') 'static-parser-value'}else{Assert-True ($null-eq$static.executable -and @($static.argv).Count-eq0 -and $static.parser-ceq'NoneV1' -and @($static.acceptedResults).Count-eq0) 'static-disabled-contract'}
    $policy=$Blueprint.policyAssertions;Assert-ExactKeys $policy @('bindHost','port','activeProviderRoutes','automaticFallback','providerSelectionConfigured','oauthStateConfigured','hermesReferences') 'policyAssertions';Assert-String $policy.bindHost 'policy-bindHost';Assert-Int $policy.port 'policy-port' 3080 3080;Assert-Int $policy.activeProviderRoutes 'policy-routes' 0 0;foreach($name in @('automaticFallback','providerSelectionConfigured','oauthStateConfigured','hermesReferences')){Assert-Bool $policy.$name "policy-$name"};Assert-True ($policy.bindHost-ceq'127.0.0.1' -and -not$policy.automaticFallback -and -not$policy.providerSelectionConfigured -and -not$policy.oauthStateConfigured -and -not$policy.hermesReferences) 'candidate-policy'
}

function Assert-SelectorDiscovery {
    param([object]$Discovery,[string]$CandidateRoot)
    Assert-ExactKeys $Discovery @('capturedAt','installedVersion','verdict','blockers','installedEntrypoint','baseline','selector','candidateBlueprint','selectorDigest','review') 'selectorDiscovery';Assert-IsoTime $Discovery.capturedAt 'selector-capturedAt';Assert-String $Discovery.installedVersion 'selector-version';Assert-String $Discovery.verdict 'selector-verdict';Assert-True (@('PASS','BLOCKED')-ccontains$Discovery.verdict) 'selector-verdict-value';Assert-Blockers $Discovery.blockers ($Discovery.verdict-ceq'BLOCKED') 'selector-blockers';Assert-Digest $Discovery.selectorDigest 'selectorDigest'
    $selectorKey=if($null-ne$Discovery.selector){[string]$Discovery.selector.name}else{''};Assert-Baseline $Discovery.baseline $selectorKey
    if($Discovery.verdict-ceq'BLOCKED'){if($null-ne$Discovery.installedEntrypoint){Assert-InstalledEntrypoint $Discovery.installedEntrypoint};Assert-True ($null-eq$Discovery.selector -and $null-eq$Discovery.candidateBlueprint) 'blocked-selector-artifacts'}
    else {
        Assert-True ($null-ne$Discovery.installedEntrypoint -and $null-ne$Discovery.selector -and $null-ne$Discovery.candidateBlueprint) 'pass-selector-artifacts';Assert-InstalledEntrypoint $Discovery.installedEntrypoint;$packageRoot=$Discovery.installedEntrypoint.packageRoot
        $selector=$Discovery.selector;Assert-ExactKeys $selector @('name','precedence','absoluteCandidateValue','futureUnitSelectorLines','effectiveProfileProbe','proof') 'selector';Assert-String $selector.name 'selector-name';Assert-True ($selector.name-cmatch'^[A-Z][A-Z0-9_]{1,63}$') 'selector-name-value';Assert-String $selector.precedence 'selector-precedence';Assert-String $selector.absoluteCandidateValue 'selector-value';Assert-True ($selector.absoluteCandidateValue-ceq$CandidateRoot) 'selector-candidate-value';Assert-StringArray $selector.futureUnitSelectorLines 'selector-unit-lines' -RequireAny
        Assert-ExactKeys $selector.effectiveProfileProbe @('executable','argv') 'effectiveProfileProbe';Assert-String $selector.effectiveProfileProbe.executable 'probe-executable';Assert-StrictPosixPath $selector.effectiveProfileProbe.executable $packageRoot;Assert-StringArray $selector.effectiveProfileProbe.argv 'probe-argv' -RequireAny;Assert-True (@($selector.effectiveProfileProbe.argv|Where-Object{$_-ceq$CandidateRoot}).Count-eq1) 'probe-candidate-argv'
        $proof=$selector.proof;Assert-ExactKeys $proof @('absolutePath','precedence','fullProfileScope','nonMerge','serviceCompatibility') 'selectorProof';foreach($name in @('absolutePath','precedence','nonMerge')){Assert-Array $proof.$name "proof-$name";Assert-True (@($proof.$name).Count-gt0) "missing-$name";foreach($ref in @($proof.$name)){Assert-InstalledSourceRef $ref $packageRoot}}
        Assert-ExactKeys $proof.fullProfileScope @('credentials','settings','plugins','sessionsState','otherMutableStores') 'fullProfileScope';foreach($store in @('credentials','settings','plugins','sessionsState','otherMutableStores')){Assert-Array $proof.fullProfileScope.$store "scope-$store";Assert-True (@($proof.fullProfileScope.$store).Count-gt0) "missing-$store";foreach($ref in @($proof.fullProfileScope.$store)){Assert-InstalledSourceRef $ref $packageRoot}}
        Assert-ExactKeys $proof.serviceCompatibility @('installed','unit') 'serviceCompatibility';Assert-Array $proof.serviceCompatibility.installed 'compat-installed';Assert-Array $proof.serviceCompatibility.unit 'compat-unit';Assert-True (@($proof.serviceCompatibility.installed).Count-gt0 -and @($proof.serviceCompatibility.unit).Count-gt0) 'missing-service-compatibility';foreach($ref in @($proof.serviceCompatibility.installed)){Assert-InstalledSourceRef $ref $packageRoot};foreach($ref in @($proof.serviceCompatibility.unit)){Assert-SanitizedUnitRef $ref $selector.name}
        Assert-CandidateBlueprint $Discovery.candidateBlueprint $packageRoot $CandidateRoot
    }
    $expected=Get-CanonicalStageDigest $Discovery @('selectorDigest','review');Assert-True ($Discovery.selectorDigest-ceq$expected) 'selector-stage-digest';Assert-Review $Discovery.review $Discovery.selectorDigest @('ACCEPTED','REJECTED');Assert-True ($Discovery.review.status-ceq'ACCEPTED') 'selector-review-not-accepted'
}

function Assert-CutoverPrerequisites {
    param([object]$Value,[string]$FutureFile)
    Assert-ExactKeys $Value @('observedAt','verdict','privilegeSeam','dropInDirectory','blockers') 'cutoverPrerequisites';Assert-IsoTime $Value.observedAt 'prerequisite-observedAt';Assert-String $Value.verdict 'prerequisite-verdict';Assert-True (@('PASS','BLOCKED')-ccontains$Value.verdict) 'prerequisite-verdict-value';Assert-Blockers $Value.blockers ($Value.verdict-ceq'BLOCKED') 'prerequisite-blockers'
    Assert-ExactKeys $Value.privilegeSeam @('verdict','receipts') 'privilegeSeam';Assert-String $Value.privilegeSeam.verdict 'privilege-seam-verdict';Assert-True (@('PASS','BLOCKED')-ccontains$Value.privilegeSeam.verdict) 'privilege-seam-verdict-value';Assert-Array $Value.privilegeSeam.receipts 'privilege-receipts';Assert-PrivilegeSeam @($Value.privilegeSeam.receipts) $FutureFile;$allAllowed=@($Value.privilegeSeam.receipts|Where-Object{$_.result-cne'ALLOWED'}).Count-eq0;Assert-True (($Value.privilegeSeam.verdict-ceq'PASS')-eq$allAllowed) 'privilege-seam-consistency'
    $drop=$Value.dropInDirectory;Assert-ExactKeys $drop @('path','exists','realDirectory','owner','group','mode','linkStatus','broadAcl','unexpectedMount','verdict') 'dropInDirectory';Assert-String $drop.path 'dropin-path';Assert-True ($drop.path-ceq'/etc/systemd/system/deepseek-harness.service.d') 'dropin-path-value';Assert-Bool $drop.exists 'dropin-exists';Assert-Bool $drop.realDirectory 'dropin-real';Assert-String $drop.linkStatus 'dropin-linkStatus';Assert-String $drop.verdict 'dropin-verdict';Assert-True (@('PASS','BLOCKED')-ccontains$drop.verdict) 'dropin-verdict-value'
    if($drop.exists){Assert-String $drop.owner 'dropin-owner';Assert-String $drop.group 'dropin-group';Assert-String $drop.mode 'dropin-mode';Assert-Bool $drop.broadAcl 'dropin-acl';Assert-Bool $drop.unexpectedMount 'dropin-mount';$safe=$drop.realDirectory-and$drop.owner-ceq'root'-and$drop.group-ceq'root'-and$drop.mode-ceq'0755'-and$drop.linkStatus-ceq'not-link'-and-not$drop.broadAcl-and-not$drop.unexpectedMount}else{Assert-True (-not$drop.realDirectory -and $null-eq$drop.owner -and $null-eq$drop.group -and $null-eq$drop.mode -and $drop.linkStatus-ceq'absent' -and $null-eq$drop.broadAcl -and $null-eq$drop.unexpectedMount) 'dropin-absent-fields';$safe=$false};Assert-True (($drop.verdict-ceq'PASS')-eq$safe) 'dropin-consistency';Assert-True (($Value.verdict-ceq'PASS')-eq($allAllowed-and$safe)) 'prerequisite-consistency'
}

function Assert-DirectoryMetadata { param([object]$Value,[string]$ExpectedPath) Assert-ExactKeys $Value @('path','objectType','symlink','owner','group','mode','aclBroad','unexpectedMount') 'CandidateDirectoryMetadataV1';foreach($name in @('path','objectType','owner','group','mode')){Assert-String $Value.$name "directory-$name"};foreach($name in @('symlink','aclBroad','unexpectedMount')){Assert-Bool $Value.$name "directory-$name"};Assert-True ($Value.path-ceq$ExpectedPath -and $Value.objectType-ceq'directory' -and -not$Value.symlink -and $Value.owner-ceq'dsh' -and $Value.group-ceq'dsh' -and $Value.mode-ceq'0700' -and -not$Value.aclBroad -and -not$Value.unexpectedMount) 'directory-metadata-values' }
function Assert-FileMetadata { param([object]$Value,[hashtable]$Expected) Assert-ExactKeys $Value @('path','objectType','symlink','owner','group','mode','linkCount','aclBroad','unexpectedMount','contentSha256') 'CandidateFileMetadataV1';foreach($name in @('path','objectType','owner','group','mode')){Assert-String $Value.$name "file-$name"};foreach($name in @('symlink','aclBroad','unexpectedMount')){Assert-Bool $Value.$name "file-$name"};Assert-Int $Value.linkCount 'file-linkCount' 1 1;Assert-Digest $Value.contentSha256 'file-contentSha256';Assert-True ($Expected.ContainsKey($Value.path) -and $Value.objectType-ceq'regular file' -and -not$Value.symlink -and $Value.owner-ceq'dsh' -and $Value.group-ceq'dsh' -and ([Convert]::ToInt32($Value.mode,8)-band63)-eq0 -and -not$Value.aclBroad -and -not$Value.unexpectedMount -and $Value.contentSha256-ceq$Expected[$Value.path]) 'file-metadata-values' }

function Assert-SafeObservation {
    param([object]$Check,[object]$Evidence)
    $o=$Check.safeObservation;$id=$Check.id;$root=$Evidence.target.candidateRoot;$blueprint=$Evidence.selectorDiscovery.candidateBlueprint
    switch($id){
        'selector-gate'{Assert-True ($Check.parser-ceq'SelectorGateV1') 'check-parser';Assert-ExactKeys $o @('selectorDigest','selectorVerdict','reviewStatus','reviewedDigest') 'SelectorGateV1';Assert-Digest $o.selectorDigest 'gate-selectorDigest';Assert-String $o.selectorVerdict 'gate-verdict';Assert-String $o.reviewStatus 'gate-review';Assert-Digest $o.reviewedDigest 'gate-reviewedDigest';if($Check.result-ceq'PASS'){Assert-True ($o.selectorDigest-ceq$Evidence.selectorDiscovery.selectorDigest -and $o.selectorVerdict-ceq'PASS' -and $o.reviewStatus-ceq'ACCEPTED' -and $o.reviewedDigest-ceq$o.selectorDigest) 'selector-gate-values'}}
        'target-preflight'{Assert-True ($Check.parser-ceq'TargetPreflightV1') 'check-parser';Assert-ExactKeys $o @('parentAbsent','rootAbsent','ancestorsSafe') 'TargetPreflightV1';foreach($name in @('parentAbsent','rootAbsent','ancestorsSafe')){Assert-Bool $o.$name "preflight-$name"};if($Check.result-ceq'PASS'){Assert-True ($o.parentAbsent-and$o.rootAbsent-and$o.ancestorsSafe) 'preflight-values'}}
        {$_-in@('create-parent','create-root')}{Assert-True ($Check.parser-ceq'CandidateDirectoryMutationV1') 'check-parser';Assert-ExactKeys $o @('path','attempted','completed','metadata') 'CandidateDirectoryMutationV1';Assert-String $o.path 'directory-mutation-path';Assert-Bool $o.attempted 'directory-attempted';Assert-Bool $o.completed 'directory-completed';$expected=if($id-ceq'create-parent'){'/home/dsh/.dsh-profiles'}else{$root};Assert-True ($o.path-ceq$expected) 'directory-mutation-path-value';if($null-ne$o.metadata){Assert-DirectoryMetadata $o.metadata $expected};if($Check.result-ceq'PASS'){Assert-True ($o.attempted-and$o.completed-and$null-ne$o.metadata) 'directory-mutation-values'}}
        'write-blueprint'{Assert-True ($Check.parser-ceq'BlueprintWriteV1') 'check-parser';Assert-ExactKeys $o @('plannedWrites','completedWrites','lastOperationOrder') 'BlueprintWriteV1';Assert-Int $o.plannedWrites 'planned-writes' 0;Assert-Int $o.completedWrites 'completed-writes' 0 $o.plannedWrites;Assert-Int $o.lastOperationOrder 'last-operation-order' 0;Assert-True ($o.plannedWrites-eq(@($blueprint.directories).Count+@($blueprint.files).Count)) 'planned-write-count';if($Check.result-ceq'PASS'){Assert-True ($o.completedWrites-eq$o.plannedWrites) 'completed-write-count'}}
        'metadata'{Assert-True ($Check.parser-ceq'CandidateMetadataSetV1') 'check-parser';Assert-ExactKeys $o @('available','directories','files','allSafe','allDigestsMatch') 'CandidateMetadataSetV1';Assert-Bool $o.available 'metadata-available';Assert-Array $o.directories 'metadata-directories';Assert-Array $o.files 'metadata-files';Assert-Bool $o.allSafe 'metadata-safe';Assert-Bool $o.allDigestsMatch 'metadata-digests';$expectedFiles=@{};foreach($f in @($blueprint.files)){$expectedFiles["$root/$($f.relativePath)"]=$f.contentSha256};foreach($d in @($o.directories)){Assert-DirectoryMetadata $d $d.path;Assert-True ($d.path-ceq'/home/dsh/.dsh-profiles' -or $d.path-ceq$root -or $d.path.StartsWith("$root/",[StringComparison]::Ordinal)) 'metadata-directory-path'};foreach($f in @($o.files)){Assert-FileMetadata $f $expectedFiles};if($Check.result-ceq'PASS'){Assert-True ($o.available-and$o.allSafe-and$o.allDigestsMatch -and @($o.files).Count-eq@($blueprint.files).Count) 'metadata-values'}}
        'static-validation'{Assert-True ($Check.parser-ceq'StaticValidationV1') 'check-parser';Assert-ExactKeys $o @('supported','exitCode','parsedResult') 'StaticValidationV1';Assert-Bool $o.supported 'static-observation-supported';Assert-String $o.parsedResult 'static-observation-result';if($null-ne$o.exitCode){Assert-Int $o.exitCode 'static-observation-exit'};if($Check.result-ceq'NOT PROVEN'){Assert-True (-not$o.supported -and $null-eq$o.exitCode -and $o.parsedResult-ceq'NOT PROVEN' -and -not$blueprint.staticValidation.supported) 'static-not-proven-contract'}elseif($Check.result-ceq'PASS'){Assert-True ($o.supported -and $o.exitCode-eq0 -and @($blueprint.staticValidation.acceptedResults)-ccontains$o.parsedResult) 'static-pass-values'}}
        'secret-scan'{Assert-True ($Check.parser-ceq'SecretScanV1') 'check-parser';Assert-ExactKeys $o @('available','filesScanned','findingCount','categories') 'SecretScanV1';Assert-Bool $o.available 'scan-available';Assert-Int $o.filesScanned 'scan-files' 0;Assert-Int $o.findingCount 'scan-findings' 0;Assert-StringArray $o.categories 'scan-categories';if($Check.result-ceq'PASS'){Assert-True ($o.available-and$o.filesScanned-eq@($blueprint.files).Count-and$o.findingCount-eq0-and@($o.categories).Count-eq0) 'scan-values'}}
        'service-unchanged'{Assert-True ($Check.parser-ceq'ServiceBaselineV1') 'check-parser';Assert-ExactKeys $o @('available','activeState','subState','user','group','execStart','workingDirectory','umask','result','nRestarts','matchesBaseline') 'ServiceBaselineV1';Assert-Bool $o.available 'service-available';foreach($name in @('activeState','subState','user','group','execStart','workingDirectory','umask','result')){Assert-String $o.$name "service-$name" -AllowEmpty};Assert-Int $o.nRestarts 'service-restarts' 0;Assert-Bool $o.matchesBaseline 'service-match';if($Check.result-ceq'PASS'){Assert-True ($o.available-and$o.activeState-ceq'active'-and$o.subState-ceq'running'-and$o.user-ceq'dsh'-and$o.group-ceq'dsh'-and$o.matchesBaseline) 'service-values'}}
        'network-unchanged'{Assert-True ($Check.parser-ceq'NetworkBaselineV1') 'check-parser';Assert-ExactKeys $o @('available','listeners','localHttpStatus','ufwActive','tcp3080Allowed','directLanDenied','matchesBaseline') 'NetworkBaselineV1';Assert-Bool $o.available 'network-available';Assert-Array $o.listeners 'network-listeners';foreach($listener in @($o.listeners)){Assert-ExactKeys $listener @('address','port','protocol') 'network-listener'};Assert-Int $o.localHttpStatus 'network-http' 0 599;foreach($name in @('ufwActive','tcp3080Allowed','directLanDenied','matchesBaseline')){Assert-Bool $o.$name "network-$name"};if($Check.result-ceq'PASS'){Assert-True ($o.available-and$o.localHttpStatus-eq200-and$o.ufwActive-and-not$o.tcp3080Allowed-and$o.directLanDenied-and$o.matchesBaseline) 'network-values'}}
        default{throw 'unknown-check-id'}
    }
}

function Assert-CandidatePreparation {
    param([object]$Candidate,[object]$Evidence,[string[]]$ReviewStatuses)
    Assert-ExactKeys $Candidate @('selectorDigest','candidateDigest','startedAt','finishedAt','verdict','checks','mutationLedger','runtimeVerdict','blockers','review') 'candidatePreparation';Assert-Digest $Candidate.selectorDigest 'candidate-selectorDigest';Assert-Digest $Candidate.candidateDigest 'candidateDigest';Assert-IsoTime $Candidate.startedAt 'candidate-startedAt';Assert-IsoTime $Candidate.finishedAt 'candidate-finishedAt';Assert-String $Candidate.verdict 'candidate-verdict';Assert-True (@('PASS','BLOCKED')-ccontains$Candidate.verdict) 'candidate-verdict-value';Assert-True ($Candidate.runtimeVerdict-ceq'NOT PROVEN') 'runtime-verdict';Assert-Blockers $Candidate.blockers ($Candidate.verdict-ceq'BLOCKED') 'candidate-blockers';Assert-Array $Candidate.checks 'candidate-checks';Assert-Array $Candidate.mutationLedger 'mutationLedger';Assert-True ($Candidate.selectorDigest-ceq$Evidence.selectorDiscovery.selectorDigest) 'candidate-selector-digest'
    $ids=@('selector-gate','target-preflight','create-parent','create-root','write-blueprint','metadata','static-validation','secret-scan','service-unchanged','network-unchanged');$blocked=$false;$index=0
    foreach($check in @($Candidate.checks)){if($blocked){throw 'continued-after-block'};Assert-ExactKeys $check @('order','id','result','observedAt','parser','safeObservation','failureState') 'candidateCheck';Assert-Int $check.order 'check-order' 1 10;Assert-String $check.id 'check-id';Assert-String $check.result 'check-result';Assert-IsoTime $check.observedAt 'check-observedAt';Assert-String $check.parser 'check-parser';Assert-String $check.failureState 'check-failureState';Assert-True ($check.order-eq$index+1 -and $check.id-ceq$ids[$index] -and @('PASS','BLOCKED','NOT PROVEN')-ccontains$check.result -and $check.failureState-ceq'BLOCKED') 'candidate-check-fields';Assert-True ($check.result-cne'NOT PROVEN' -or $check.id-ceq'static-validation') 'not-proven-check';Assert-SafeObservation $check $Evidence;if($check.result-ceq'BLOCKED'){$blocked=$true};$index++}
    if($Candidate.verdict-ceq'PASS'){Assert-True (-not$blocked -and $index-eq10) 'candidate-check-count'}else{Assert-True ($blocked -and @($Candidate.checks)[-1].result-ceq'BLOCKED') 'candidate-blocked-check'}
    $last=0;$ledgerBlocked=$false;foreach($entry in @($Candidate.mutationLedger)){Assert-ExactKeys $entry @('order','operation','path','contentSha256','result','at','secretObserved') 'mutationLedgerEntry';Assert-Int $entry.order 'mutation-order' 1;Assert-String $entry.operation 'mutation-operation';Assert-String $entry.path 'mutation-path';Assert-String $entry.result 'mutation-result';Assert-IsoTime $entry.at 'mutation-at';Assert-Bool $entry.secretObserved 'mutation-secret';Assert-True ($entry.order-eq++$last -and @('CREATE_DIRECTORY','WRITE_FILE')-ccontains$entry.operation -and @('PASS','BLOCKED')-ccontains$entry.result -and -not$entry.secretObserved) 'mutation-ledger-fields';if($ledgerBlocked){throw 'mutation-after-block'};if($entry.result-ceq'BLOCKED'){$ledgerBlocked=$true};if($entry.path-ceq'/home/dsh/.dsh-profiles'){Assert-True ($entry.operation-ceq'CREATE_DIRECTORY' -and $null-eq$entry.contentSha256) 'mutation-parent'}elseif($entry.path-ceq$Evidence.target.candidateRoot){Assert-True ($entry.operation-ceq'CREATE_DIRECTORY' -and $null-eq$entry.contentSha256) 'mutation-root'}else{Assert-StrictPosixPath $entry.path $Evidence.target.candidateRoot;if($entry.operation-ceq'CREATE_DIRECTORY'){Assert-True ($null-eq$entry.contentSha256) 'mutation-directory'}else{Assert-Digest $entry.contentSha256 'mutation-file'}}}
    if($Candidate.verdict-ceq'PASS'){Assert-True (@($Candidate.mutationLedger).Count-eq(2+@($Evidence.selectorDiscovery.candidateBlueprint.directories).Count+@($Evidence.selectorDiscovery.candidateBlueprint.files).Count) -and @($Candidate.mutationLedger|Where-Object{$_.result-cne'PASS'}).Count-eq0) 'mutation-ledger-complete'}
    $expected=Get-CanonicalStageDigest $Candidate @('candidateDigest','review');Assert-True ($Candidate.candidateDigest-ceq$expected) 'candidate-stage-digest';Assert-Review $Candidate.review $Candidate.candidateDigest $ReviewStatuses
}

function Assert-OperationLedger {
    param([object]$Entries,[object]$Evidence)
    Assert-Array $Entries 'operationLedger';$blocked=$false
    foreach($entry in @($Entries)){Assert-ExactKeys $entry @('at','actor','operation','target','result','secretObserved') 'operationLedgerEntry';Assert-IsoTime $entry.at 'operation-at';Assert-String $entry.actor 'operation-actor';Assert-String $entry.operation 'operation-name';Assert-String $entry.target 'operation-target';Assert-String $entry.result 'operation-result';Assert-Bool $entry.secretObserved 'operation-secret';Assert-True (@('controller','dsh')-ccontains$entry.actor -and @('READ_INSTALLED','READ_BASELINE','READ_PREREQUISITE','CREATE_DIRECTORY','WRITE_FILE','STATIC_VALIDATE','SCAN_CANDIDATE','WRITE_EVIDENCE','WRITE_HANDOFF')-ccontains$entry.operation -and @('PASS','BLOCKED')-ccontains$entry.result -and -not$entry.secretObserved) 'operation-ledger-values';Assert-True ($entry.operation-notmatch'SERVICE|SYSTEMD|DROPIN|CREDENTIAL|OAUTH|FIREWALL|POWER|ROUTE') 'operation-forbidden';if($entry.operation-in@('CREATE_DIRECTORY','WRITE_FILE','STATIC_VALIDATE','SCAN_CANDIDATE')){Assert-True ($entry.target-ceq'/home/dsh/.dsh-profiles' -or $entry.target-ceq$Evidence.target.candidateRoot -or $entry.target.StartsWith("$($Evidence.target.candidateRoot)/",[StringComparison]::Ordinal)) 'operation-target-scope'}elseif($entry.operation-ceq'WRITE_EVIDENCE'){Assert-True ($entry.target-ceq'docs/evidence/vm105-profile-pointer-preparation.json') 'operation-evidence-target'}elseif($entry.operation-ceq'WRITE_HANDOFF'){Assert-True ($entry.target-ceq'docs/handoffs/2026-09-08-vm105-profile-cutover-requirements.md') 'operation-handoff-target'}}
}

function Assert-Closeout {
    param([object]$Closeout,[object]$Evidence)
    Assert-ExactKeys $Closeout @('closedAt','verdict','selectorDigest','candidateDigest','cutoverPrerequisiteVerdict','handoffPath','handoffSha256','review') 'closeout';Assert-IsoTime $Closeout.closedAt 'closeout-closedAt';Assert-String $Closeout.verdict 'closeout-verdict';Assert-True (@('PREPARATION_READY','BLOCKED')-ccontains$Closeout.verdict) 'closeout-verdict-value';Assert-Digest $Closeout.selectorDigest 'closeout-selectorDigest';Assert-Digest $Closeout.candidateDigest 'closeout-candidateDigest';Assert-String $Closeout.cutoverPrerequisiteVerdict 'closeout-prerequisite';Assert-True (@('PASS','BLOCKED')-ccontains$Closeout.cutoverPrerequisiteVerdict) 'closeout-prerequisite-value';Assert-String $Closeout.handoffPath 'closeout-handoffPath';Assert-True ($Closeout.handoffPath-ceq'docs/handoffs/2026-09-08-vm105-profile-cutover-requirements.md') 'closeout-handoff-path';Assert-Digest $Closeout.handoffSha256 'closeout-handoffSha256';Assert-True ($Closeout.selectorDigest-ceq$Evidence.selectorDiscovery.selectorDigest -and $Closeout.candidateDigest-ceq$Evidence.candidatePreparation.candidateDigest -and $Closeout.cutoverPrerequisiteVerdict-ceq$Evidence.cutoverPrerequisites.verdict) 'closeout-digest-link'
    $ready=$Evidence.selectorDiscovery.verdict-ceq'PASS'-and$Evidence.selectorDiscovery.review.status-ceq'ACCEPTED'-and$Evidence.candidatePreparation.verdict-ceq'PASS'-and$Evidence.candidatePreparation.review.status-ceq'ACCEPTED';Assert-True (($Closeout.verdict-ceq'PREPARATION_READY')-eq$ready) 'closeout-readiness';$digest=Get-CanonicalStageDigest $Closeout @('review');Assert-Review $Closeout.review $digest @('PENDING','ACCEPTED','REJECTED')
    Assert-True (Test-Path -LiteralPath $Closeout.handoffPath -PathType Leaf) 'Missing closeout handoff';$bytes=[IO.File]::ReadAllBytes((Resolve-Path -LiteralPath $Closeout.handoffPath));Assert-True ((Get-UpperSha256 $bytes)-ceq$Closeout.handoffSha256) 'handoff-digest';Test-NonExecutableHandoff ([Text.Encoding]::UTF8.GetString($bytes))
}

function Test-NoSecretShapedData {
    param([object]$Value)
    $json=$Value|ConvertTo-Json -Depth 100 -Compress
    Assert-True ($json -notmatch '(?i)(sk-(?:or-)?[A-Za-z0-9_-]{8,}|sess-[A-Za-z0-9_-]{8,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|(?:api[_-]?key|token|secret|password|client[_-]?secret|authorization|access[_-]?token|refresh[_-]?token|id[_-]?token|oauth[_-]?(?:code|state))\s*[:=]\s*[^\s,}\]]{4,})') 'secret-shaped-value'
}

function Test-PreparationEvidence {
    param([object]$Evidence,[ValidateSet('Selector','Candidate','Closeout')][string]$Stage)
    Assert-ExactKeys $Evidence @('schemaVersion','workflowId','target','overallVerdict','selectorDiscovery','cutoverPrerequisites','candidatePreparation','closeout','operationLedger') 'root';Assert-Int $Evidence.schemaVersion 'schemaVersion' 1 1;Assert-True ($Evidence.workflowId-ceq'vm105-profile-preparation') 'workflow-id';Assert-Target $Evidence.target;Assert-SelectorDiscovery $Evidence.selectorDiscovery $Evidence.target.candidateRoot;Assert-CutoverPrerequisites $Evidence.cutoverPrerequisites $Evidence.target.futureDropInFile;Assert-OperationLedger $Evidence.operationLedger $Evidence
    switch($Stage){
        'Selector'{Assert-True ($null-eq$Evidence.candidatePreparation -and $null-eq$Evidence.closeout) 'selector-stage-artifacts';$expected=if($Evidence.selectorDiscovery.verdict-ceq'PASS'){'SELECTOR_PASS'}else{'BLOCKED'};Assert-True ($Evidence.overallVerdict-ceq$expected) 'selector-overall-verdict'}
        'Candidate'{Assert-True ($Evidence.selectorDiscovery.verdict-ceq'PASS') 'candidate-stage-selector';Assert-True ($null-ne$Evidence.candidatePreparation -and $null-eq$Evidence.closeout) 'candidate-stage-artifacts';Assert-CandidatePreparation $Evidence.candidatePreparation $Evidence @('PENDING','ACCEPTED','REJECTED');$expected=if($Evidence.candidatePreparation.verdict-ceq'PASS'){'CANDIDATE_STATIC_PASS'}else{'BLOCKED'};Assert-True ($Evidence.overallVerdict-ceq$expected) 'candidate-overall-verdict'}
        'Closeout'{Assert-True ($Evidence.selectorDiscovery.verdict-ceq'PASS' -and $null-ne$Evidence.candidatePreparation -and $null-ne$Evidence.closeout) 'closeout-stage-artifacts';Assert-CandidatePreparation $Evidence.candidatePreparation $Evidence @('ACCEPTED');Assert-Closeout $Evidence.closeout $Evidence;$expected=if($Evidence.closeout.verdict-ceq'PREPARATION_READY'){'PREPARATION_READY'}else{'BLOCKED'};Assert-True ($Evidence.overallVerdict-ceq$expected) 'closeout-overall-verdict'}
    }
    Test-NoSecretShapedData $Evidence
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
    $time = '2026-09-08T00:00:00.0000000Z'
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
    $futureFile='/etc/systemd/system/deepseek-harness.service.d/90-vm105-provider-profile.conf'
    $privilegeSpecs=@(
        @('future-install','/usr/bin/install','-o','root','-g','root','-m','0644','/dev/stdin',$futureFile),
        @('future-remove','/usr/bin/rm','-f','--',$futureFile),
        @('future-stop','/usr/bin/systemctl','stop','deepseek-harness.service'),
        @('future-start','/usr/bin/systemctl','start','deepseek-harness.service'),
        @('future-reload','/usr/bin/systemctl','daemon-reload'),
        @('future-status','/usr/bin/systemctl','show','deepseek-harness.service')
    )
    $privileges=@($privilegeSpecs | ForEach-Object {[pscustomobject]@{
        sourceClass='privilege-receipt';operationId=$_[0];capturedAt=$time;queryUser='dsh';sudoPath='/usr/bin/sudo';targetExecutable=$_[1]
        targetArgv=@($_[2..($_.Count-1)]);noninteractive=$true;result='DENIED';exitCode=1;rawOutputStored=$false;claim='synthetic denied privilege'
    }})
    $contentLines = @('server:','  host: 127.0.0.1','  port: 3080','providers: []','automaticFallback: false')
    $contentBytes = [Text.Encoding]::UTF8.GetBytes(($contentLines -join "`n") + "`n")
    $record=[pscustomobject]@{
        schemaVersion = 1; workflowId = 'vm105-profile-preparation'
        target = [pscustomobject]@{
            hostname='deepseek-harness-01';address='192.168.1.139';sshHostKeyIdentity='SHA256:synthetic-host-key'
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
                address='192.168.1.139';sshHostKeyIdentity='SHA256:synthetic-host-key';installedVersion='0.1.1-rc.2'
                service=$unit;listeners=@([pscustomobject]@{address='127.0.0.1';port=3080;protocol='tcp'})
                localHttp=[pscustomobject]@{url='http://127.0.0.1:3080/';statusCode=200;exitCode=0}
                ufw=[pscustomobject]@{active=$true;defaults='deny-in-allow-out';ruleIds=@('synthetic-ssh');tcp3080Allowed=$false}
                directLanDenied=[pscustomobject]@{source='controller-lan';destination='192.168.1.139';port=3080;denied=$true;timeoutMs=1000}
            }
            selector=[pscustomobject]@{
                name='SYNTHETIC_PROFILE_ROOT';precedence='synthetic installed proof';absoluteCandidateValue='/home/dsh/.dsh-profiles/vm105-provider-v1'
                futureUnitSelectorLines=@('synthetic selector line');effectiveProfileProbe=[pscustomobject]@{executable='/opt/deepseek-harness/package/index.js';argv=@('synthetic-safe-paths','/home/dsh/.dsh-profiles/vm105-provider-v1')}
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
            selectorDigest=$null;review=[pscustomobject]@{status='ACCEPTED';reviewedAt=$time;reviewer='synthetic-reviewer';reviewedDigest=$null;findings=@()}
        }
        cutoverPrerequisites=[pscustomobject]@{
            observedAt=$time;verdict='BLOCKED';privilegeSeam=[pscustomobject]@{verdict='BLOCKED';receipts=$privileges}
            dropInDirectory=[pscustomobject]@{path='/etc/systemd/system/deepseek-harness.service.d';exists=$false;realDirectory=$false;owner=$null;group=$null;mode=$null;linkStatus='absent';broadAcl=$null;unexpectedMount=$null;verdict='BLOCKED'}
            blockers=@('Synthetic privilege seam denied')
        }
        candidatePreparation=$null;closeout=$null;operationLedger=@()
    }
    $record.selectorDiscovery.selectorDigest=Get-CanonicalStageDigest $record.selectorDiscovery @('selectorDigest','review')
    $record.selectorDiscovery.review.reviewedDigest=$record.selectorDiscovery.selectorDigest
    return $record
}

function New-SyntheticCandidateResult {
    param([object]$Evidence,[string]$FailAt,[switch]$ContinueAfterFailure)
    $ids = @('selector-gate','target-preflight','create-parent','create-root','write-blueprint','metadata','static-validation','secret-scan','service-unchanged','network-unchanged')
    $root=$Evidence.target.candidateRoot;$file=$Evidence.selectorDiscovery.candidateBlueprint.files[0];$time='2026-09-08T00:00:00.0000000Z'
    $dir={param($path)[pscustomobject]@{path=$path;objectType='directory';symlink=$false;owner='dsh';group='dsh';mode='0700';aclBroad=$false;unexpectedMount=$false}}
    $observations=@(
        [pscustomobject]@{parser='SelectorGateV1';value=[pscustomobject]@{selectorDigest=$Evidence.selectorDiscovery.selectorDigest;selectorVerdict='PASS';reviewStatus='ACCEPTED';reviewedDigest=$Evidence.selectorDiscovery.selectorDigest}},
        [pscustomobject]@{parser='TargetPreflightV1';value=[pscustomobject]@{parentAbsent=$true;rootAbsent=$true;ancestorsSafe=$true}},
        [pscustomobject]@{parser='CandidateDirectoryMutationV1';value=[pscustomobject]@{path='/home/dsh/.dsh-profiles';attempted=$true;completed=$true;metadata=(& $dir '/home/dsh/.dsh-profiles')}},
        [pscustomobject]@{parser='CandidateDirectoryMutationV1';value=[pscustomobject]@{path=$root;attempted=$true;completed=$true;metadata=(& $dir $root)}},
        [pscustomobject]@{parser='BlueprintWriteV1';value=[pscustomobject]@{plannedWrites=2;completedWrites=2;lastOperationOrder=4}},
        [pscustomobject]@{parser='CandidateMetadataSetV1';value=[pscustomobject]@{available=$true;directories=@((& $dir '/home/dsh/.dsh-profiles'),(& $dir $root),(& $dir "$root/state"));files=@([pscustomobject]@{path="$root/settings.yaml";objectType='regular file';symlink=$false;owner='dsh';group='dsh';mode='0600';linkCount=1;aclBroad=$false;unexpectedMount=$false;contentSha256=$file.contentSha256});allSafe=$true;allDigestsMatch=$true}},
        [pscustomobject]@{parser='StaticValidationV1';value=[pscustomobject]@{supported=$false;exitCode=$null;parsedResult='NOT PROVEN'}},
        [pscustomobject]@{parser='SecretScanV1';value=[pscustomobject]@{available=$true;filesScanned=1;findingCount=0;categories=@()}},
        [pscustomobject]@{parser='ServiceBaselineV1';value=[pscustomobject]@{available=$true;activeState='active';subState='running';user='dsh';group='dsh';execStart='/usr/local/bin/dsh';workingDirectory='/opt/deepseek-harness';umask='0077';result='success';nRestarts=0;matchesBaseline=$true}},
        [pscustomobject]@{parser='NetworkBaselineV1';value=[pscustomobject]@{available=$true;listeners=@([pscustomobject]@{address='127.0.0.1';port=3080;protocol='tcp'});localHttpStatus=200;ufwActive=$true;tcp3080Allowed=$false;directLanDenied=$true;matchesBaseline=$true}}
    )
    $checks = [Collections.Generic.List[object]]::new()
    $blocked = $false
    for ($i = 0; $i -lt $ids.Count; $i++) {
        if ($blocked -and -not $ContinueAfterFailure) { break }
        $result = if ($ids[$i] -ceq $FailAt) { 'BLOCKED' } elseif($ids[$i]-ceq'static-validation'){'NOT PROVEN'} else { 'PASS' }
        $checks.Add([pscustomobject]@{order=$i+1;id=$ids[$i];result=$result;observedAt=$time;parser=$observations[$i].parser;safeObservation=$observations[$i].value;failureState='BLOCKED'})
        if ($result -ceq 'BLOCKED') { $blocked = $true }
    }
    $verdict = if ($blocked) { 'BLOCKED' } else { 'PASS' }
    $ledger=if($blocked){@()}else{@(
        [pscustomobject]@{order=1;operation='CREATE_DIRECTORY';path='/home/dsh/.dsh-profiles';contentSha256=$null;result='PASS';at=$time;secretObserved=$false},
        [pscustomobject]@{order=2;operation='CREATE_DIRECTORY';path=$root;contentSha256=$null;result='PASS';at=$time;secretObserved=$false},
        [pscustomobject]@{order=3;operation='CREATE_DIRECTORY';path="$root/state";contentSha256=$null;result='PASS';at=$time;secretObserved=$false},
        [pscustomobject]@{order=4;operation='WRITE_FILE';path="$root/settings.yaml";contentSha256=$file.contentSha256;result='PASS';at=$time;secretObserved=$false}
    )}
    $candidate=[pscustomobject]@{selectorDigest=$Evidence.selectorDiscovery.selectorDigest;candidateDigest=$null;startedAt=$time;finishedAt='2026-09-08T00:00:01.0000000Z';verdict=$verdict;checks=@($checks);mutationLedger=$ledger;runtimeVerdict='NOT PROVEN';blockers=$(if($blocked){@("synthetic failure at $FailAt")}else{@()});review=[pscustomobject]@{status='PENDING';reviewedAt=$null;reviewer=$null;reviewedDigest=$null;findings=@()}}
    $candidate.candidateDigest=Get-CanonicalStageDigest $candidate @('candidateDigest','review')
    return $candidate
}

function New-SyntheticBlockedSelectorRecord {
    $record=New-SyntheticPreparationRecord;$record.overallVerdict='BLOCKED';$record.selectorDiscovery.verdict='BLOCKED';$record.selectorDiscovery.blockers=@('Synthetic selector proof unavailable');$record.selectorDiscovery.installedEntrypoint=$null;$record.selectorDiscovery.selector=$null;$record.selectorDiscovery.candidateBlueprint=$null;$record.selectorDiscovery.selectorDigest=Get-CanonicalStageDigest $record.selectorDiscovery @('selectorDigest','review');$record.selectorDiscovery.review.reviewedDigest=$record.selectorDiscovery.selectorDigest;return $record
}
```

The self-test body uses only synthetic values and must include concrete cross-class and continuation assertions:

```powershell
$script:NegativeTestCount=0;$positiveCount=0;$good=New-SyntheticPreparationRecord
function Sync-SelectorDigest { param([object]$Record) $Record.selectorDiscovery.selectorDigest=Get-CanonicalStageDigest $Record.selectorDiscovery @('selectorDigest','review');$Record.selectorDiscovery.review.reviewedDigest=$Record.selectorDiscovery.selectorDigest }
function Attach-Candidate { param([object]$Record,[string]$FailAt='',[switch]$Continue) $Record.candidatePreparation=New-SyntheticCandidateResult $Record $FailAt -ContinueAfterFailure:$Continue;$Record.overallVerdict=if($Record.candidatePreparation.verdict-ceq'PASS'){'CANDIDATE_STATIC_PASS'}else{'BLOCKED'} }

Test-PreparationEvidence $good 'Selector';$positiveCount++
$blocked=New-SyntheticBlockedSelectorRecord;Test-PreparationEvidence $blocked 'Selector';$positiveCount++
$candidate=Copy-SyntheticRecord $good;Attach-Candidate $candidate;Test-PreparationEvidence $candidate 'Candidate';$positiveCount++
$candidateBlocked=Copy-SyntheticRecord $good;Attach-Candidate $candidateBlocked 'metadata';Test-PreparationEvidence $candidateBlocked 'Candidate';$positiveCount++

$negativeCases=[Collections.Generic.List[object]]::new()
function Add-NegativeCase { param([string]$Name,[scriptblock]$Action,[string]$Pattern) $negativeCases.Add([pscustomobject]@{name=$Name;action=$Action;pattern=$Pattern}) }
Add-NegativeCase 'root allowlist' { $r=Copy-SyntheticRecord $good;$r|Add-Member extra 1;Test-PreparationEvidence $r Selector } 'root keys differ'
Add-NegativeCase 'target allowlist' { $r=Copy-SyntheticRecord $good;$r.target|Add-Member extra 1;Test-PreparationEvidence $r Selector } 'target keys differ'
Add-NegativeCase 'target value' { $r=Copy-SyntheticRecord $good;$r.target.address='192.0.2.105';Test-PreparationEvidence $r Selector } 'target-values'
Add-NegativeCase 'selectorDiscovery allowlist' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery|Add-Member extra 1;Test-PreparationEvidence $r Selector } 'selectorDiscovery keys differ'
Add-NegativeCase 'blocked selector artifacts' { $r=New-SyntheticBlockedSelectorRecord;$r.selectorDiscovery.selector=$good.selectorDiscovery.selector;Test-PreparationEvidence $r Selector } 'blocked-selector-artifacts'
Add-NegativeCase 'pass selector null installed' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.installedEntrypoint=$null;Test-PreparationEvidence $r Selector } 'pass-selector-artifacts'
Add-NegativeCase 'installed allowlist' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.installedEntrypoint|Add-Member extra 1;Test-PreparationEvidence $r Selector } 'installedEntrypoint keys differ'
Add-NegativeCase 'installed symlink' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.installedEntrypoint.wrapperSymlink=$true;Test-PreparationEvidence $r Selector } 'installed-entrypoint-fields'
Add-NegativeCase 'installed ownership' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.installedEntrypoint.entrypointOwner='dsh';Test-PreparationEvidence $r Selector } 'installed-entrypoint-fields'
Add-NegativeCase 'installedSource allowlist' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.installedEntrypoint.proofRefs[0]|Add-Member extra 1;Test-PreparationEvidence $r Selector } 'installedSourceRef keys differ'
Add-NegativeCase 'installedSource class' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.selector.proof.nonMerge[0].sourceClass='unknown';Test-PreparationEvidence $r Selector } 'proof-source-class'
Add-NegativeCase 'installedSource path' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.selector.proof.absolutePath[0].path='/tmp/x';Test-PreparationEvidence $r Selector } 'posix-path-root|installed-source-root'
Add-NegativeCase 'installedSource lines' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.selector.proof.precedence[0].lineStart=0;Test-PreparationEvidence $r Selector } 'installed-source-lineStart'
Add-NegativeCase 'sanitizedUnit allowlist' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.baseline.service|Add-Member extra 1;Test-PreparationEvidence $r Selector } 'sanitizedUnitRef keys differ'
Add-NegativeCase 'sanitizedUnit property' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.baseline.service.propertyAllowlist[0]='Environment';Test-PreparationEvidence $r Selector } 'unit-property-allowlist'
Add-NegativeCase 'sanitizedUnit duplicate' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.baseline.service.observations[1].name='User';Test-PreparationEvidence $r Selector } 'unit-property-duplicate'
Add-NegativeCase 'baseline allowlist' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.baseline|Add-Member extra 1;Test-PreparationEvidence $r Selector } 'selectorBaseline keys differ'
Add-NegativeCase 'listener allowlist' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.baseline.listeners[0]|Add-Member extra 1;Test-PreparationEvidence $r Selector } 'baselineListener keys differ'
Add-NegativeCase 'http value' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.baseline.localHttp.statusCode=503;Test-PreparationEvidence $r Selector } 'http-status'
Add-NegativeCase 'ufw value' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.baseline.ufw.tcp3080Allowed=$true;Test-PreparationEvidence $r Selector } 'baseline-ufw'
Add-NegativeCase 'direct denial' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.baseline.directLanDenied.denied=$false;Test-PreparationEvidence $r Selector } 'baseline-direct-denial'
Add-NegativeCase 'selector allowlist' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.selector|Add-Member extra 1;Test-PreparationEvidence $r Selector } 'selector keys differ'
Add-NegativeCase 'selector proof allowlist' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.selector.proof|Add-Member extra 1;Test-PreparationEvidence $r Selector } 'selectorProof keys differ'
Add-NegativeCase 'missing absolute path' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.selector.proof.absolutePath=@();Test-PreparationEvidence $r Selector } 'missing-absolutePath'
Add-NegativeCase 'missing precedence' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.selector.proof.precedence=@();Test-PreparationEvidence $r Selector } 'missing-precedence'
Add-NegativeCase 'missing nonMerge' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.selector.proof.nonMerge=@();Test-PreparationEvidence $r Selector } 'missing-nonMerge'
Add-NegativeCase 'fullProfileScope allowlist' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.selector.proof.fullProfileScope|Add-Member extra 1;Test-PreparationEvidence $r Selector } 'fullProfileScope keys differ'
Add-NegativeCase 'missing credentials scope' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.selector.proof.fullProfileScope.credentials=@();Test-PreparationEvidence $r Selector } 'missing-credentials'
Add-NegativeCase 'missing settings scope' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.selector.proof.fullProfileScope.settings=@();Test-PreparationEvidence $r Selector } 'missing-settings'
Add-NegativeCase 'missing plugins scope' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.selector.proof.fullProfileScope.plugins=@();Test-PreparationEvidence $r Selector } 'missing-plugins'
Add-NegativeCase 'missing sessions scope' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.selector.proof.fullProfileScope.sessionsState=@();Test-PreparationEvidence $r Selector } 'missing-sessionsState'
Add-NegativeCase 'missing other scope' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.selector.proof.fullProfileScope.otherMutableStores=@();Test-PreparationEvidence $r Selector } 'missing-otherMutableStores'
Add-NegativeCase 'serviceCompatibility allowlist' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.selector.proof.serviceCompatibility|Add-Member extra 1;Test-PreparationEvidence $r Selector } 'serviceCompatibility keys differ'
Add-NegativeCase 'blueprint allowlist' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.candidateBlueprint|Add-Member extra 1;Test-PreparationEvidence $r Selector } 'candidateBlueprint keys differ'
Add-NegativeCase 'directory allowlist' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.candidateBlueprint.directories[0]|Add-Member extra 1;Test-PreparationEvidence $r Selector } 'candidateDirectory keys differ'
Add-NegativeCase 'directory mode' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.candidateBlueprint.directories[0].mode='0755';Test-PreparationEvidence $r Selector } 'candidate-directory'
Add-NegativeCase 'file allowlist' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.candidateBlueprint.files[0]|Add-Member extra 1;Test-PreparationEvidence $r Selector } 'candidateFile keys differ'
Add-NegativeCase 'file mode' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.candidateBlueprint.files[0].mode='0644';Test-PreparationEvidence $r Selector } 'candidate-file'
Add-NegativeCase 'file digest' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.candidateBlueprint.files[0].contentSha256='B'*64;Test-PreparationEvidence $r Selector } 'candidate-content-digest'
Add-NegativeCase 'static allowlist' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.candidateBlueprint.staticValidation|Add-Member extra 1;Test-PreparationEvidence $r Selector } 'staticValidation keys differ'
Add-NegativeCase 'policy allowlist' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.candidateBlueprint.policyAssertions|Add-Member extra 1;Test-PreparationEvidence $r Selector } 'policyAssertions keys differ'
Add-NegativeCase 'policy isolation' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.candidateBlueprint.policyAssertions.automaticFallback=$true;Test-PreparationEvidence $r Selector } 'candidate-policy'
Add-NegativeCase 'prerequisite allowlist' { $r=Copy-SyntheticRecord $good;$r.cutoverPrerequisites|Add-Member extra 1;Test-PreparationEvidence $r Selector } 'cutoverPrerequisites keys differ'
Add-NegativeCase 'privilegeSeam allowlist' { $r=Copy-SyntheticRecord $good;$r.cutoverPrerequisites.privilegeSeam|Add-Member extra 1;Test-PreparationEvidence $r Selector } 'privilegeSeam keys differ'
Add-NegativeCase 'privilege receipt allowlist' { $r=Copy-SyntheticRecord $good;$r.cutoverPrerequisites.privilegeSeam.receipts[0]|Add-Member extra 1;Test-PreparationEvidence $r Selector } 'privilegeReceiptRef keys differ'
Add-NegativeCase 'privilege argv' { $r=Copy-SyntheticRecord $good;$r.cutoverPrerequisites.privilegeSeam.receipts[0].targetArgv[1]='dsh';Test-PreparationEvidence $r Selector } 'privilege-receipt-argv'
Add-NegativeCase 'dropIn allowlist' { $r=Copy-SyntheticRecord $good;$r.cutoverPrerequisites.dropInDirectory|Add-Member extra 1;Test-PreparationEvidence $r Selector } 'dropInDirectory keys differ'
Add-NegativeCase 'dropIn consistency' { $r=Copy-SyntheticRecord $good;$r.cutoverPrerequisites.dropInDirectory.verdict='PASS';Test-PreparationEvidence $r Selector } 'dropin-consistency'
Add-NegativeCase 'selector digest' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.selectorDigest='B'*64;Test-PreparationEvidence $r Selector } 'selector-stage-digest'
Add-NegativeCase 'review allowlist' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.review|Add-Member extra 1;Test-PreparationEvidence $r Selector } 'review keys differ'
Add-NegativeCase 'candidate allowlist' { $r=Copy-SyntheticRecord $candidate;$r.candidatePreparation|Add-Member extra 1;Test-PreparationEvidence $r Candidate } 'candidatePreparation keys differ'
Add-NegativeCase 'check allowlist' { $r=Copy-SyntheticRecord $candidate;$r.candidatePreparation.checks[0]|Add-Member extra 1;Test-PreparationEvidence $r Candidate } 'candidateCheck keys differ'
Add-NegativeCase 'opaque observation' { $r=Copy-SyntheticRecord $candidate;$r.candidatePreparation.checks[1].safeObservation|Add-Member extra 1;$r.candidatePreparation.candidateDigest=Get-CanonicalStageDigest $r.candidatePreparation @('candidateDigest','review');Test-PreparationEvidence $r Candidate } 'TargetPreflightV1 keys differ'
Add-NegativeCase 'wrong parser' { $r=Copy-SyntheticRecord $candidate;$r.candidatePreparation.checks[0].parser='OpaqueV1';$r.candidatePreparation.candidateDigest=Get-CanonicalStageDigest $r.candidatePreparation @('candidateDigest','review');Test-PreparationEvidence $r Candidate } 'check-parser'
Add-NegativeCase 'illegal not proven' { $r=Copy-SyntheticRecord $candidate;$r.candidatePreparation.checks[7].result='NOT PROVEN';$r.candidatePreparation.candidateDigest=Get-CanonicalStageDigest $r.candidatePreparation @('candidateDigest','review');Test-PreparationEvidence $r Candidate } 'not-proven-check'
Add-NegativeCase 'runtime verdict' { $r=Copy-SyntheticRecord $candidate;$r.candidatePreparation.runtimeVerdict='PASS';$r.candidatePreparation.candidateDigest=Get-CanonicalStageDigest $r.candidatePreparation @('candidateDigest','review');Test-PreparationEvidence $r Candidate } 'runtime-verdict'
Add-NegativeCase 'mutation allowlist' { $r=Copy-SyntheticRecord $candidate;$r.candidatePreparation.mutationLedger[0]|Add-Member extra 1;Test-PreparationEvidence $r Candidate } 'mutationLedgerEntry keys differ'
Add-NegativeCase 'mutation operation' { $r=Copy-SyntheticRecord $candidate;$r.candidatePreparation.mutationLedger[0].operation='SYSTEMCTL';Test-PreparationEvidence $r Candidate } 'mutation-ledger-fields'
Add-NegativeCase 'continued after block' { $r=Copy-SyntheticRecord $good;Attach-Candidate $r 'write-blueprint' -Continue;Test-PreparationEvidence $r Candidate } 'continued-after-block'
Add-NegativeCase 'operationLedger allowlist' { $r=Copy-SyntheticRecord $good;$r.operationLedger=@([pscustomobject]@{at='2026-09-08T00:00:00.0000000Z';actor='controller';operation='READ_BASELINE';target='deepseek-harness.service';result='PASS';secretObserved=$false;extra=1});Test-PreparationEvidence $r Selector } 'operationLedgerEntry keys differ'
Add-NegativeCase 'operationLedger forbidden' { $r=Copy-SyntheticRecord $good;$r.operationLedger=@([pscustomobject]@{at='2026-09-08T00:00:00.0000000Z';actor='controller';operation='SYSTEMCTL';target='deepseek-harness.service';result='PASS';secretObserved=$false});Test-PreparationEvidence $r Selector } 'operation-ledger-values'
Add-NegativeCase 'secret shaped value' { $r=Copy-SyntheticRecord $good;$r.selectorDiscovery.selector.precedence='api_key=synthetic_nonempty_value';Sync-SelectorDigest $r;Test-PreparationEvidence $r Selector } 'secret-shaped-value'
Add-NegativeCase 'closeout allowlist' { $r=Copy-SyntheticRecord $candidate;$r.candidatePreparation.review.status='ACCEPTED';$r.candidatePreparation.review.reviewedAt='2026-09-08T00:00:00.0000000Z';$r.candidatePreparation.review.reviewer='synthetic-reviewer';$r.candidatePreparation.review.reviewedDigest=$r.candidatePreparation.candidateDigest;$r.closeout=[pscustomobject]@{closedAt='2026-09-08T00:00:00.0000000Z';verdict='PREPARATION_READY';selectorDigest=$r.selectorDiscovery.selectorDigest;candidateDigest=$r.candidatePreparation.candidateDigest;cutoverPrerequisiteVerdict='BLOCKED';handoffPath='docs/handoffs/2026-09-08-vm105-profile-cutover-requirements.md';handoffSha256=('A'*64);review=[pscustomobject]@{status='PENDING';reviewedAt=$null;reviewer=$null;reviewedDigest=$null;findings=@()};extra=1};$r.overallVerdict='PREPARATION_READY';Test-PreparationEvidence $r Closeout } 'closeout keys differ'

foreach($case in $negativeCases){Assert-Throws $case.action $case.pattern}
$captured=&{Test-SyntheticSecretScanner 'api_key: synthetic_nonempty_value'}2>&1|Out-String;Assert-True ($captured-notmatch'synthetic_nonempty_value') 'secret-output-suppression'
Assert-True ($positiveCount-eq4 -and $negativeCases.Count-eq63 -and $script:NegativeTestCount-eq$negativeCases.Count) 'self-test-count-drift'
"SELF_TEST_PASS positive=$positiveCount negative=$script:NegativeTestCount"
```

`New-SyntheticPreparationRecord`, `New-SyntheticBlockedSelectorRecord`, `New-SyntheticCandidateResult`, and `Test-SyntheticSecretScanner` are private functions in the same script. The record factory populates every Shared Preparation Contract field with the fixed hostname/address `deepseek-harness-01`/`192.168.1.139`, a synthetic host-key identity, `/opt/deepseek-harness/package/index.js`, all five installed-source store proofs, zero routes, fallback false, six denied privilege receipts, and no secret-shaped data. The candidate-result factory emits the ten ordered parser-specific check records and a complete success ledger, or stops at the requested failed check.

Implement canonical JSON, uppercase SHA-256, exact schema checks, and a value-suppressing scanner. The scanner reports only relative filename, one-based line, and category; it never emits matching text. Reject nonempty assignments for `key`, `api_key`, `token`, `secret`, `password`, `client_secret`, authorization headers, PEM private keys, `sk-`, `sk-or-`, `sess-`, and raw or encoded OAuth `code`, `state`, `access_token`, `refresh_token`, and `id_token` values. Empty values and prose naming a field are allowed.

`-SelfTest` must cover four positive records (selector `PASS`, selector `BLOCKED`, candidate `PASS` with the one allowed static `NOT PROVEN`, and candidate `BLOCKED`) and these rejection classes:

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

Run `./scripts/Test-VM105ProfilePreparation.ps1 -SelfTest` before completing validator logic. Expected RED: nonzero exit with `Expected rejection was not raised`. After implementing the private factories plus all assertions, expected GREEN: exit 0 with `SELF_TEST_PASS positive=4 negative=63`, matching the 63 explicit named negative cases above, and no synthetic secret-shaped value in output.

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

function ConvertFrom-ListenerLines {
    param([string[]]$Lines)
    $items=foreach($line in $Lines){
        if($line -notmatch '^LISTEN\s+\d+\s+\d+\s+(\S+):3080\s+'){throw 'Malformed listener observation'}
        $address=$Matches[1].Trim('[',']')
        if(@('127.0.0.1','::1') -cnotcontains $address){throw 'Non-loopback listener'}
        [pscustomobject]@{address=$address;port=3080;protocol='tcp'}
    }
    if(@($items).Count -eq 0){throw 'Missing listener'}
    return @($items)
}

function Get-LocalHttpObservation {
    param([scriptblock]$Reader)
    $token=((& $Reader @('/usr/bin/curl','--silent','--show-error','--output','/dev/null','--max-time','5','--write-out','HTTP%{http_code}','http://127.0.0.1:3080/'))-join '')
    if($token -notmatch '^HTTP([0-9]{3})$'){throw 'Malformed local HTTP observation'}
    return [pscustomobject]@{url='http://127.0.0.1:3080/';statusCode=[int]$Matches[1];exitCode=0}
}

function ConvertFrom-UfwLines {
    param([string[]]$Lines)
    $active=$false;$defaults=$null;$ids=[Collections.Generic.List[string]]::new();$tcp3080=$false
    foreach($line in $Lines){
        if($line -match '^Status:\s+(active|inactive)$'){$active=$Matches[1]-ceq'active';continue}
        if($line -match '^Default:\s+(.+)$'){$defaults=($Matches[1]-replace '\s+','-').ToLowerInvariant();continue}
        if($line -match '^\[\s*(\d+)\]\s+(.+)$'){$ids.Add("rule-$($Matches[1])");if($Matches[2]-match '(^|\s)3080(/tcp)?\s+.*ALLOW'){$tcp3080=$true}}
    }
    if($null -eq $defaults){throw 'Malformed UFW observation'}
    return [pscustomobject]@{active=$active;defaults=$defaults;ruleIds=@($ids);tcp3080Allowed=$tcp3080}
}

function Get-DirectLanObservation {
    param([string]$Source,[string]$Destination,[int]$Port=3080,[int]$TimeoutMs=1500)
    $client=[Net.Sockets.TcpClient]::new();$cts=[Threading.CancellationTokenSource]::new($TimeoutMs)
    try{$client.ConnectAsync($Destination,$Port,$cts.Token).GetAwaiter().GetResult();$denied=$false}catch{$denied=$true}finally{$client.Dispose();$cts.Dispose()}
    return [pscustomobject]@{source=$Source;destination=$Destination;port=$Port;denied=$denied;timeoutMs=$TimeoutMs}
}

$listeners=ConvertFrom-ListenerLines $listenerLines
$localHttp=Get-LocalHttpObservation {param($argv) Invoke-StrictSsh $argv}
$ufw=ConvertFrom-UfwLines (Invoke-StrictSsh @('/usr/bin/sudo','-n','/usr/sbin/ufw','status','numbered'))
$directLan=Get-DirectLanObservation 'controller-lan' '192.168.1.139'
$baseline=[pscustomobject]@{
    repositoryOrigin=$expectedOrigin;branch='codex/vm105-authoritative-roadmap';capturedAt=(Get-Date).ToUniversalTime().ToString('o')
    hostname=$hostname;address='192.168.1.139';sshHostKeyIdentity='accepted-known-host';installedVersion=$version
    service=$unitRef;listeners=$listeners;localHttp=$localHttp;ufw=$ufw;directLanDenied=$directLan
}
if($localHttp.statusCode -ne 200 -or -not $ufw.active -or $ufw.tcp3080Allowed -or -not $directLan.denied){throw 'Network baseline mismatch'}
```

Expected typed result: eleven unique allowlisted service observations; one or more loopback-only TCP/3080 listeners; local HTTP `{ statusCode: 200, exitCode: 0 }`; active UFW with `tcp3080Allowed: false`; and bounded direct-LAN `{ denied: true, timeoutMs: 1500 }`. No raw UFW, curl, listener, or socket error text enters evidence.

- [ ] **Step 3: Verify the wrapper and discover only from its fixed installed entrypoint**

After capturing owner/mode/SHA-256, read exactly `/usr/local/bin/dsh` as data. Require one fixed absolute entrypoint below `/opt/deepseek-harness`; reject command substitution, environment-derived/relative/fallback paths, eval, extra executable branches, writable owner/mode, or a target outside that root. Verify the extracted entrypoint is a regular installed/package-owned safe file. Walk upward only inside `/opt/deepseek-harness` to its owning `package.json`, verify package name/version, and record digests before reading package help/docs/schema/state-location sources. Do not follow links outside the package root, run network package commands, or install anything.

Build selector semantic proof exclusively from `installedSourceRef` records. Prove exact selector name/precedence, absolute-path support, non-merge/non-inherit/non-migrate behavior, and full-profile coverage for credentials, settings, plugins, sessions/state, and every other mutable store. Service compatibility requires installed-source proof; a `sanitizedUnitRef` may additionally establish that the unchanged installed command/user can consume the selector. Query only the proven selector key from effective unit metadata and suppress all other environment values.

Use this fail-closed parser and package-root walk; it returns `BLOCKED` instead of guessing:

```powershell
function ConvertFrom-InstalledFileMetadata {
    param([string]$Line,[string]$ExpectedPath,[string]$RequiredOwner,[string]$RequiredGroup)
    $parts=$Line -split '\|',6
    if($parts.Count-ne 6 -or $parts[0]-cne $ExpectedPath -or $parts[1]-cne 'regular file' -or $parts[2]-cne $RequiredOwner -or $parts[3]-cne $RequiredGroup -or [int]$parts[5]-ne 1){throw 'BLOCKED installed file metadata'}
    if(([Convert]::ToInt32($parts[4],8)-band 18)-ne 0){throw 'BLOCKED writable installed file'}
    return [pscustomobject]@{path=$parts[0];type=$parts[1];symlink=$false;owner=$parts[2];group=$parts[3];mode=('0'+$parts[4]);linkCount=[int]$parts[5]}
}

function Get-VerifiedInstalledEntrypoint {
    $statLine = (Invoke-StrictSsh @('/usr/bin/stat','-c','%n|%F|%U|%G|%a|%h','--','/usr/local/bin/dsh')) -join ''
    $wrapper=ConvertFrom-InstalledFileMetadata $statLine '/usr/local/bin/dsh' 'root' 'root'
    $wrapperLines = Invoke-StrictSsh @('/usr/bin/cat','--','/usr/local/bin/dsh')
    $meaningful = @($wrapperLines | Where-Object { $_ -and $_ -notmatch '^#!' -and $_ -notmatch '^set -e(?:u)?$' })
    if ($meaningful.Count -ne 1) { throw 'BLOCKED wrapper shape' }
    $match = [regex]::Match($meaningful[0], '^exec\s+(?:(/[A-Za-z0-9._/-]+)\s+)?(/opt/deepseek-harness/[A-Za-z0-9._/-]+)(?:\s+"\$@")?\s*$')
    if (-not $match.Success -or $meaningful[0] -match '\$\(|`|\$\{') { throw 'BLOCKED wrapper entrypoint' }
    $entrypoint = $match.Groups[2].Value
    Assert-StrictPosixPath $entrypoint '/opt/deepseek-harness'
    $entryStat = (Invoke-StrictSsh @('/usr/bin/stat','-c','%n|%F|%U|%G|%a|%h','--',$entrypoint)) -join ''
    $entry=ConvertFrom-InstalledFileMetadata $entryStat $entrypoint 'root' 'root'
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
        wrapperPath=$wrapper.path;wrapperType=$wrapper.type;wrapperSymlink=$wrapper.symlink;wrapperOwner=$wrapper.owner;wrapperGroup=$wrapper.group;wrapperMode=$wrapper.mode;wrapperLinkCount=$wrapper.linkCount;wrapperSha256=$wrapperSha
        entrypointPath=$entry.path;entrypointType=$entry.type;entrypointSymlink=$entry.symlink;entrypointOwner=$entry.owner;entrypointGroup=$entry.group;entrypointMode=$entry.mode;entrypointLinkCount=$entry.linkCount;entrypointSha256=$entrySha
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
    try { $stat=(Invoke-StrictSsh @('/usr/bin/stat','-c','%n|%F|%U|%G|%a','--',$path)) -join '' }
    catch { return [pscustomobject]@{path=$path;exists=$false;realDirectory=$false;owner=$null;group=$null;mode=$null;linkStatus='absent';broadAcl=$null;unexpectedMount=$null;verdict='BLOCKED'} }
    $parts=$stat -split '\|',5
    if ($parts.Count -ne 5) { throw 'Malformed drop-in directory metadata' }
    $acl=Invoke-StrictSsh @('/usr/bin/getfacl','-cp','--',$path)
    $mount=(Invoke-StrictSsh @('/usr/bin/findmnt','-n','-o','TARGET','--target',$path)) -join ''
    $broadAcl=@($acl | Where-Object { $_ -match '^(group|other|mask)::.*w' }).Count -gt 0
    $safe=($parts[1] -ceq 'directory' -and $parts[2] -ceq 'root' -and $parts[3] -ceq 'root' -and $parts[4] -ceq '755' -and -not $broadAcl -and $mount -ceq '/')
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

function New-SyntheticInitializerRecord {
    [pscustomobject]@{target=[pscustomobject]@{candidateRoot='/home/dsh/.dsh-profiles/vm105-provider-v1'};candidatePreparation=[pscustomobject]@{verdict='RUNNING';checks=@();mutationLedger=@();blockers=@();finishedAt=$null};operationLedger=@();overallVerdict='RUNNING'}
}

function New-SyntheticStepObservation {
    param([string]$Id,[switch]$Blocked)
    [pscustomobject]@{id=$Id;available=(-not$Blocked)}
}

function Invoke-PreparationStep {
    param(
        [object]$Record,
        [ValidateSet('selector-gate','target-preflight','create-parent','create-root','write-blueprint','metadata','static-validation','secret-scan','service-unchanged','network-unchanged')][string]$Id,
        [string]$Parser,
        [object[]]$WriteOperations,
        [scriptblock]$Action,
        [scriptblock]$Persist,
        [scriptblock]$Adapter
    )
    if($Record.candidatePreparation.verdict-ceq'BLOCKED'){return $false}
    $expectedIds=@('selector-gate','target-preflight','create-parent','create-root','write-blueprint','metadata','static-validation','secret-scan','service-unchanged','network-unchanged')
    $order=@($Record.candidatePreparation.checks).Count+1
    Assert-Initializer ($Id-ceq$expectedIds[$order-1]) 'step order mismatch'
    try {
        foreach($operation in @($WriteOperations)){
            Assert-Initializer (@('CREATE_DIRECTORY','WRITE_FILE')-ccontains$operation.operation) 'write operation forbidden'
            Assert-Initializer ($operation.path-ceq'/home/dsh/.dsh-profiles' -or $operation.path-ceq$Record.target.candidateRoot -or $operation.path.StartsWith("$($Record.target.candidateRoot)/",[StringComparison]::Ordinal)) 'write target forbidden'
            $receipt=[pscustomobject]@{order=@($Record.candidatePreparation.mutationLedger).Count+1;operation=$operation.operation;path=$operation.path;contentSha256=$operation.contentSha256;result='BLOCKED';at=(Get-Date).ToUniversalTime().ToString('o');secretObserved=$false}
            $Record.candidatePreparation.mutationLedger=@($Record.candidatePreparation.mutationLedger)+$receipt
            $opReceipt=[pscustomobject]@{at=$receipt.at;actor='dsh';operation=$operation.operation;target=$operation.path;result='BLOCKED';secretObserved=$false}
            $Record.operationLedger=@($Record.operationLedger)+$opReceipt
            & $Persist $Record
            & $Adapter $operation.argv $operation.stdin
            $receipt.result='PASS';$opReceipt.result='PASS'; & $Persist $Record
        }
        $parsed=& $Action
        Assert-Initializer ($null-ne$parsed -and @('PASS','NOT PROVEN')-ccontains$parsed.result) 'step parser result'
        Assert-Initializer ($parsed.result-cne'NOT PROVEN' -or $Id-ceq'static-validation') 'NOT PROVEN outside static validation'
        $Record.candidatePreparation.checks=@($Record.candidatePreparation.checks)+[pscustomobject]@{order=$order;id=$Id;result=$parsed.result;observedAt=(Get-Date).ToUniversalTime().ToString('o');parser=$Parser;safeObservation=$parsed.safeObservation;failureState='BLOCKED'}
        & $Persist $Record
        return $true
    } catch {
        $Record.candidatePreparation.verdict='BLOCKED';$Record.candidatePreparation.finishedAt=(Get-Date).ToUniversalTime().ToString('o');$Record.overallVerdict='BLOCKED';$Record.candidatePreparation.blockers=@("$Id failed; inspect nonsecret receipt metadata")
        $Record.candidatePreparation.checks=@($Record.candidatePreparation.checks)+[pscustomobject]@{order=$order;id=$Id;result='BLOCKED';observedAt=(Get-Date).ToUniversalTime().ToString('o');parser=$Parser;safeObservation=(& $Action -Blocked);failureState='BLOCKED'}
        & $Persist $Record
        return $false
    }
}

function Invoke-InitializerSelfTest {
    $ids=@('selector-gate','target-preflight','create-parent','create-root','write-blueprint','metadata','static-validation','secret-scan','service-unchanged','network-unchanged')
    foreach($failAt in $ids){
        $record=New-SyntheticInitializerRecord;$persisted=[Collections.Generic.List[object]]::new();$calls=[Collections.Generic.List[string]]::new()
        foreach($id in $ids){
            $writes=if($id-ceq$failAt){@([pscustomobject]@{operation='WRITE_FILE';path='/home/dsh/.dsh-profiles/vm105-provider-v1/settings.yaml';contentSha256=('A'*64);argv=@('synthetic-write');stdin=[byte[]]@(1)})}else{@()}
            $adapter={param($argv,$stdin)$calls.Add($id);if($id-ceq$failAt){throw 'synthetic failure'}}
            $action={param([switch]$Blocked)[pscustomobject]@{result=$(if($Blocked){'BLOCKED'}else{'PASS'});safeObservation=(New-SyntheticStepObservation $id -Blocked:$Blocked)}}
            if(-not(Invoke-PreparationStep $record $id 'SyntheticV1' $writes $action {$persisted.Add(($args[0]|ConvertTo-Json -Depth 100|ConvertFrom-Json))} $adapter)){break}
        }
        Assert-Initializer ($record.candidatePreparation.verdict-ceq'BLOCKED' -and $record.candidatePreparation.mutationLedger[-1].result-ceq'BLOCKED') 'failed receipt not persisted'
        Assert-Initializer (@($persisted[-1].candidatePreparation.checks)[-1].id-ceq$failAt -and $calls.Count-eq1) 'continued after failure'
        Assert-Initializer (@($calls|Where-Object{$_-match'cleanup|repair|service|systemd'}).Count-eq0) 'forbidden recovery call'
    }
    $record=New-SyntheticInitializerRecord;foreach($id in $ids){if(-not(Invoke-PreparationStep $record $id 'SyntheticV1' @() { [pscustomobject]@{result='PASS';safeObservation=(New-SyntheticStepObservation $id)} } {} {})){throw 'positive sequence stopped'}}
    Assert-Initializer (@($record.candidatePreparation.checks).Count-eq10) 'positive sequence incomplete'
    'SELF_TEST_PASS failures=10 positive=1'
}
```

Require exactly one mode. Before constructing SSH, reject a non-`PASS`/unaccepted selector, digest drift, unsafe or existing target/parent, blueprint/hash/path/mode/reference failure, provider/OAuth/secret content, and every destination outside `/home/dsh/.dsh-profiles/vm105-provider-v1`. Inject a fake SSH adapter only in self-test.

Fail each post-create operation in turn: parent creation, candidate-root creation, each directory/file write, metadata verification, static validation, secret scan, and unchanged-service/network check. After the first failure, assert `candidatePreparation.verdict: BLOCKED`, no later write, no cleanup/remove/repair, no service lifecycle or privileged mutation, and no old-profile operation. Preserve candidate paths already created before failure for review. The positive synthetic run executes every planned candidate write once and only the two exact read-only baseline queries.

Expected RED from `./scripts/Initialize-VM105ProviderProfile.ps1 -AcceptedSelectorDigest ('A'*64) -SelfTest`: nonzero exit with `continued after failure` until stop-on-first-failure is implemented. Expected GREEN: exit 0 with `SELF_TEST_PASS failures=10 positive=1` and zero SSH calls.

- [ ] **Step 2: Implement the fixed-path preparation lane**

The `-Prepare` path first reruns the Task 1 selector validator and revalidates VM/SSH identity, service active baseline, listener, selector digest, candidate ancestor metadata, and exact parent/target absence. It then uses one sequential `dsh` writer lane with `umask 077` to:

1. Create exactly `/home/dsh/.dsh-profiles` and `/home/dsh/.dsh-profiles/vm105-provider-v1` as real `dsh:dsh` mode `0700` directories.
2. Create only blueprint directories/files below the candidate; transfer reviewed secret-free file bytes through standard input without shell evaluation.
3. Verify local and VM-side nonsecret file SHA-256, `dsh:dsh` ownership, 0700 directories, 0600-or-narrower regular files, link count one, no symbolic links, no broad ACL, and no unexpected mount.
4. Run only the installed static-validation argv proved in the blueprint. If no safe static syntax validator exists, record syntax `NOT PROVEN`; if the uncertainty weakens loopback/zero-route/fallback isolation, set `BLOCKED`.
5. Read only newly created candidate files through the value-suppressing scanner.
6. Revalidate the existing service is active and unchanged, loopback-only, locally healthy, UFW unchanged with no TCP 3080 allowance, and direct LAN TCP 3080 denied.

The initializer rejects every service lifecycle or privilege-changing command. Its only systemd/sudo argv are the exact read-only `systemctl show` and `sudo -n ufw status numbered` baselines. It never starts Harness against the candidate. Any post-create failure records `BLOCKED`, stops remaining writes, and leaves the candidate untouched for review; it does not delete, repair, or normalize it.

Implement path confinement and atomic SSH/stdin transfer with these concrete functions:

```powershell
$candidateRoot='/home/dsh/.dsh-profiles/vm105-provider-v1'
$sshBaseArgs=@('-i',$SshKey,'-o','BatchMode=yes','-o','IdentitiesOnly=yes','-o','StrictHostKeyChecking=yes',$SshTarget)

function Resolve-CandidatePath {
    param([string]$RelativePath)
    Assert-StrictPosixRelativePath $RelativePath
    $absolute="$candidateRoot/$RelativePath"
    Assert-StrictPosixPath $absolute $candidateRoot
    return $absolute
}

function ConvertFrom-CandidateMetadata {
    param([string]$StatLine,[string[]]$AclLines,[string]$MountTarget,[string]$ExpectedPath,[ValidateSet('directory','file')][string]$Kind,[string]$ContentSha256)
    $parts=$StatLine -split '\|',6
    if($parts.Count-ne 6 -or $parts[0]-cne $ExpectedPath -or $parts[2]-cne 'dsh' -or $parts[3]-cne 'dsh'){throw 'candidate metadata mismatch'}
    $isDirectory=$parts[1]-ceq'directory';$isFile=$parts[1]-ceq'regular file'
    if(($Kind-eq'directory'-and(-not $isDirectory-or $parts[4]-cne'700'))-or($Kind-eq'file'-and(-not $isFile-or([Convert]::ToInt32($parts[4],8)-band 63)-ne 0-or[int]$parts[5]-ne 1))){throw 'candidate object mismatch'}
    $broadAcl=@($AclLines|Where-Object{$_-match'^(group|other|mask)::.*w'}).Count-gt 0
    $unexpectedMount=($MountTarget-cne'/')
    if($broadAcl-or$unexpectedMount){throw 'candidate metadata unsafe'}
    if($Kind-eq'directory'){
        return [pscustomobject]@{path=$ExpectedPath;objectType='directory';symlink=$false;owner='dsh';group='dsh';mode='0700';aclBroad=$false;unexpectedMount=$false}
    }
    if($ContentSha256-notmatch'^[A-F0-9]{64}$'){throw 'candidate file digest missing'}
    return [pscustomobject]@{path=$ExpectedPath;objectType='regular file';symlink=$false;owner='dsh';group='dsh';mode=('0'+$parts[4]);linkCount=1;aclBroad=$false;unexpectedMount=$false;contentSha256=$ContentSha256}
}

function Invoke-SshProcess {
    param([string[]]$RemoteArgv,[byte[]]$StandardInput,[int]$TimeoutSeconds=30)
    $joined=@($RemoteArgv)-join "`0"
    $readOnlySystemctl=@('/usr/bin/systemctl','show','deepseek-harness.service','--property=User,Group,ExecStart,WorkingDirectory,UMask,FragmentPath,DropInPaths,ActiveState,SubState,Result,NRestarts','--no-pager')-join "`0"
    $readOnlyUfw=@('/usr/bin/sudo','-n','/usr/sbin/ufw','status','numbered')-join "`0"
    if($RemoteArgv[0]-in @('/usr/bin/systemctl','/usr/bin/sudo') -and $joined-cne$readOnlySystemctl -and $joined-cne$readOnlyUfw){throw 'lifecycle or privileged command forbidden'}
    if($RemoteArgv[0]-in @('/usr/sbin/service','/sbin/initctl','/sbin/shutdown','/sbin/reboot')){throw 'lifecycle command forbidden'}
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

$now=(Get-Date).ToUniversalTime().ToString('o')
$record.candidatePreparation=[pscustomobject]@{selectorDigest=$record.selectorDiscovery.selectorDigest;candidateDigest=$null;startedAt=$now;finishedAt=$null;verdict='RUNNING';checks=@();mutationLedger=@();runtimeVerdict='NOT PROVEN';blockers=@();review=[pscustomobject]@{status='PENDING';reviewedAt=$null;reviewer=$null;reviewedDigest=$null;findings=@()}}
$persist={param($state)$state.candidatePreparation.candidateDigest=Get-CanonicalStageDigest $state.candidatePreparation @('candidateDigest','review');$json=$state|ConvertTo-Json -Depth 100;[IO.File]::WriteAllText((Resolve-Path $EvidencePath),$json+"`n",[Text.UTF8Encoding]::new($false))}
$adapter={param($argv,$stdin)[void](Invoke-SshProcess $argv $stdin)}
$run={param($id,$parser,$writes,$action)if(-not(Invoke-PreparationStep $record $id $parser $writes $action $persist $adapter)){return $false};return $true}

if(-not(& $run 'selector-gate' 'SelectorGateV1' @() {param([switch]$Blocked)[pscustomobject]@{result=$(if($Blocked){'BLOCKED'}else{'PASS'});safeObservation=[pscustomobject]@{selectorDigest=$record.selectorDiscovery.selectorDigest;selectorVerdict=$record.selectorDiscovery.verdict;reviewStatus=$record.selectorDiscovery.review.status;reviewedDigest=$record.selectorDiscovery.review.reviewedDigest}}})){return}
if(-not(& $run 'target-preflight' 'TargetPreflightV1' @() {param([switch]$Blocked)$parentAbsent=$false;$rootAbsent=$false;$ancestorsSafe=$false;if(-not$Blocked){try{[void](Invoke-SshProcess @('/usr/bin/test','!','-e','/home/dsh/.dsh-profiles') $null);$parentAbsent=$true}catch{};try{[void](Invoke-SshProcess @('/usr/bin/test','!','-e',$candidateRoot) $null);$rootAbsent=$true}catch{};$ancestorsSafe=$true;foreach($ancestor in @('/home','/home/dsh')){$parts=((Invoke-SshProcess @('/usr/bin/stat','-c','%n|%F|%U|%G|%a','--',$ancestor) $null)-join'')-split'\|',5;$acl=Invoke-SshProcess @('/usr/bin/getfacl','-cp','--',$ancestor) $null;$mount=(Invoke-SshProcess @('/usr/bin/findmnt','-n','-o','TARGET','--target',$ancestor) $null)-join'';if($parts.Count-ne5-or$parts[0]-cne$ancestor-or$parts[1]-cne'directory'-or([Convert]::ToInt32($parts[4],8)-band18)-ne0-or@($acl|Where-Object{$_-match'^(group|other|mask)::.*w'}).Count-gt0-or$mount-cne'/'){$ancestorsSafe=$false}}};$pass=$parentAbsent-and$rootAbsent-and$ancestorsSafe;[pscustomobject]@{result=$(if($pass){'PASS'}else{'BLOCKED'});safeObservation=[pscustomobject]@{parentAbsent=$parentAbsent;rootAbsent=$rootAbsent;ancestorsSafe=$ancestorsSafe}}})){return}
$parentWrite=[pscustomobject]@{operation='CREATE_DIRECTORY';path='/home/dsh/.dsh-profiles';contentSha256=$null;argv=@('/usr/bin/install','-d','-m','0700','--','/home/dsh/.dsh-profiles');stdin=$null}
if(-not(& $run 'create-parent' 'CandidateDirectoryMutationV1' @($parentWrite) {param([switch]$Blocked)$metadata=if($Blocked){$null}else{ConvertFrom-CandidateMetadata ((Invoke-SshProcess @('/usr/bin/stat','-c','%n|%F|%U|%G|%a|%h','--','/home/dsh/.dsh-profiles') $null)-join'') (Invoke-SshProcess @('/usr/bin/getfacl','-cp','--','/home/dsh/.dsh-profiles') $null) ((Invoke-SshProcess @('/usr/bin/findmnt','-n','-o','TARGET','--target','/home/dsh/.dsh-profiles') $null)-join'') '/home/dsh/.dsh-profiles' directory $null};[pscustomobject]@{result=$(if($Blocked){'BLOCKED'}else{'PASS'});safeObservation=[pscustomobject]@{path='/home/dsh/.dsh-profiles';attempted=$true;completed=(-not$Blocked);metadata=$metadata}}})){return}
$rootWrite=[pscustomobject]@{operation='CREATE_DIRECTORY';path=$candidateRoot;contentSha256=$null;argv=@('/usr/bin/install','-d','-m','0700','--',$candidateRoot);stdin=$null}
if(-not(& $run 'create-root' 'CandidateDirectoryMutationV1' @($rootWrite) {param([switch]$Blocked)$metadata=if($Blocked){$null}else{ConvertFrom-CandidateMetadata ((Invoke-SshProcess @('/usr/bin/stat','-c','%n|%F|%U|%G|%a|%h','--',$candidateRoot) $null)-join'') (Invoke-SshProcess @('/usr/bin/getfacl','-cp','--',$candidateRoot) $null) ((Invoke-SshProcess @('/usr/bin/findmnt','-n','-o','TARGET','--target',$candidateRoot) $null)-join'') $candidateRoot directory $null};[pscustomobject]@{result=$(if($Blocked){'BLOCKED'}else{'PASS'});safeObservation=[pscustomobject]@{path=$candidateRoot;attempted=$true;completed=(-not$Blocked);metadata=$metadata}}})){return}
$blueprintWrites=@();foreach($directory in @($record.selectorDiscovery.candidateBlueprint.directories)){$path=Resolve-CandidatePath $directory.relativePath;$blueprintWrites+=,[pscustomobject]@{operation='CREATE_DIRECTORY';path=$path;contentSha256=$null;argv=@('/usr/bin/install','-d','-m','0700','--',$path);stdin=$null}};foreach($file in @($record.selectorDiscovery.candidateBlueprint.files)){$path=Resolve-CandidatePath $file.relativePath;$bytes=[Text.Encoding]::UTF8.GetBytes((@($file.contentLines)-join"`n")+"`n");$blueprintWrites+=,[pscustomobject]@{operation='WRITE_FILE';path=$path;contentSha256=$file.contentSha256;argv=@('/usr/bin/install','-m',$file.mode,'/dev/stdin',$path);stdin=$bytes}}
if(-not(& $run 'write-blueprint' 'BlueprintWriteV1' $blueprintWrites {param([switch]$Blocked)[pscustomobject]@{result=$(if($Blocked){'BLOCKED'}else{'PASS'});safeObservation=[pscustomobject]@{plannedWrites=$blueprintWrites.Count;completedWrites=$(if($Blocked){@($record.candidatePreparation.mutationLedger|Where-Object result -eq PASS).Count-2}else{$blueprintWrites.Count});lastOperationOrder=@($record.candidatePreparation.mutationLedger).Count}}})){return}
if(-not(& $run 'metadata' 'CandidateMetadataSetV1' @() {param([switch]$Blocked)$directories=@();$files=@();if(-not$Blocked){foreach($operation in @($record.candidatePreparation.mutationLedger|Where-Object operation -eq CREATE_DIRECTORY)){$directories+=ConvertFrom-CandidateMetadata ((Invoke-SshProcess @('/usr/bin/stat','-c','%n|%F|%U|%G|%a|%h','--',$operation.path) $null)-join'') (Invoke-SshProcess @('/usr/bin/getfacl','-cp','--',$operation.path) $null) ((Invoke-SshProcess @('/usr/bin/findmnt','-n','-o','TARGET','--target',$operation.path) $null)-join'') $operation.path directory $null};foreach($operation in @($record.candidatePreparation.mutationLedger|Where-Object operation -eq WRITE_FILE)){$digest=((Invoke-SshProcess @('/usr/bin/sha256sum','--',$operation.path) $null)-join'').Split(' ')[0].ToUpperInvariant();$files+=ConvertFrom-CandidateMetadata ((Invoke-SshProcess @('/usr/bin/stat','-c','%n|%F|%U|%G|%a|%h','--',$operation.path) $null)-join'') (Invoke-SshProcess @('/usr/bin/getfacl','-cp','--',$operation.path) $null) ((Invoke-SshProcess @('/usr/bin/findmnt','-n','-o','TARGET','--target',$operation.path) $null)-join'') $operation.path file $digest}};[pscustomobject]@{result=$(if($Blocked){'BLOCKED'}else{'PASS'});safeObservation=[pscustomobject]@{available=(-not$Blocked);directories=$directories;files=$files;allSafe=(-not$Blocked);allDigestsMatch=(-not$Blocked)}}})){return}
$static=$record.selectorDiscovery.candidateBlueprint.staticValidation
if(-not(& $run 'static-validation' 'StaticValidationV1' @() {param([switch]$Blocked)if($Blocked){return [pscustomobject]@{result='BLOCKED';safeObservation=[pscustomobject]@{supported=$static.supported;exitCode=$null;parsedResult='BLOCKED'}}};if(-not$static.supported){return [pscustomobject]@{result='NOT PROVEN';safeObservation=[pscustomobject]@{supported=$false;exitCode=$null;parsedResult='NOT PROVEN'}}};$parsed=(Invoke-SshProcess (@($static.executable)+@($static.argv)) $null $static.timeoutSeconds)-join"`n";if(@($static.acceptedResults)-cnotcontains$parsed){throw 'static validation result rejected'};[pscustomobject]@{result='PASS';safeObservation=[pscustomobject]@{supported=$true;exitCode=0;parsedResult=$parsed}}})){return}
if(-not(& $run 'secret-scan' 'SecretScanV1' @() {param([switch]$Blocked)$filesScanned=0;$findingCount=0;$categories=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal);if(-not$Blocked){foreach($file in @($record.selectorDiscovery.candidateBlueprint.files)){$lines=Invoke-SshProcess @('/usr/bin/cat','--',(Resolve-CandidatePath $file.relativePath)) $null;$filesScanned++;foreach($line in $lines){if($line-match'(?i)(api[_-]?key|token|secret|password|client[_-]?secret|authorization|access[_-]?token|refresh[_-]?token|id[_-]?token|oauth[_-]?(code|state))\s*[:=]\s*\S+' -or $line-match'(sk-(or-)?[A-Za-z0-9_-]{8,}|sess-[A-Za-z0-9_-]{8,}|-----BEGIN [A-Z ]*PRIVATE KEY-----)'){$findingCount++;[void]$categories.Add('secret-shaped-assignment')}}}};[pscustomobject]@{result=$(if($Blocked-or$findingCount-gt0){'BLOCKED'}else{'PASS'});safeObservation=[pscustomobject]@{available=(-not$Blocked);filesScanned=$filesScanned;findingCount=$findingCount;categories=@($categories)}}})){return}

$currentUnit=ConvertFrom-SanitizedUnitLines (Invoke-SshProcess @('/usr/bin/systemctl','show','deepseek-harness.service','--property=User,Group,ExecStart,WorkingDirectory,UMask,FragmentPath,DropInPaths,ActiveState,SubState,Result,NRestarts','--no-pager') $null);$currentListeners=ConvertFrom-ListenerLines (Invoke-SshProcess @('/usr/bin/ss','-lntH','sport = :3080') $null);$currentHttp=Get-LocalHttpObservation {param($argv)Invoke-SshProcess $argv $null};$currentUfw=ConvertFrom-UfwLines (Invoke-SshProcess @('/usr/bin/sudo','-n','/usr/sbin/ufw','status','numbered') $null);$currentDirect=Get-DirectLanObservation 'controller-lan' '192.168.1.139'
$before=ConvertTo-CanonicalNode ([pscustomobject]@{repositoryOrigin=$record.selectorDiscovery.baseline.repositoryOrigin;branch=$record.selectorDiscovery.baseline.branch;hostname=$record.selectorDiscovery.baseline.hostname;address=$record.selectorDiscovery.baseline.address;sshHostKeyIdentity=$record.selectorDiscovery.baseline.sshHostKeyIdentity;installedVersion=$record.selectorDiscovery.baseline.installedVersion;service=[pscustomobject]@{sourceClass=$record.selectorDiscovery.baseline.service.sourceClass;observationId=$record.selectorDiscovery.baseline.service.observationId;propertyAllowlist=$record.selectorDiscovery.baseline.service.propertyAllowlist;observations=$record.selectorDiscovery.baseline.service.observations;claim=$record.selectorDiscovery.baseline.service.claim};listeners=$record.selectorDiscovery.baseline.listeners;localHttp=$record.selectorDiscovery.baseline.localHttp;ufw=$record.selectorDiscovery.baseline.ufw;directLanDenied=$record.selectorDiscovery.baseline.directLanDenied})
$after=ConvertTo-CanonicalNode ([pscustomobject]@{repositoryOrigin=$record.selectorDiscovery.baseline.repositoryOrigin;branch=$record.selectorDiscovery.baseline.branch;hostname=$record.target.hostname;address=$record.target.address;sshHostKeyIdentity=$record.target.sshHostKeyIdentity;installedVersion=$record.selectorDiscovery.installedVersion;service=[pscustomobject]@{sourceClass=$currentUnit.sourceClass;observationId=$currentUnit.observationId;propertyAllowlist=$currentUnit.propertyAllowlist;observations=$currentUnit.observations;claim=$currentUnit.claim};listeners=$currentListeners;localHttp=$currentHttp;ufw=$currentUfw;directLanDenied=$currentDirect})
$baselineMatches=(($before|ConvertTo-Json -Depth 100 -Compress)-ceq($after|ConvertTo-Json -Depth 100 -Compress))
$unitMap=@{};foreach($item in $currentUnit.observations){$unitMap[$item.name]=$item.value}
if(-not(& $run 'service-unchanged' 'ServiceBaselineV1' @() {param([switch]$Blocked)[pscustomobject]@{result=$(if($Blocked-or-not$baselineMatches){'BLOCKED'}else{'PASS'});safeObservation=[pscustomobject]@{available=(-not$Blocked);activeState=$unitMap.ActiveState;subState=$unitMap.SubState;user=$unitMap.User;group=$unitMap.Group;execStart=$unitMap.ExecStart;workingDirectory=$unitMap.WorkingDirectory;umask=$unitMap.UMask;result=$unitMap.Result;nRestarts=[int]$unitMap.NRestarts;matchesBaseline=$baselineMatches}}})){return}
if(-not(& $run 'network-unchanged' 'NetworkBaselineV1' @() {param([switch]$Blocked)[pscustomobject]@{result=$(if($Blocked-or-not$baselineMatches){'BLOCKED'}else{'PASS'});safeObservation=[pscustomobject]@{available=(-not$Blocked);listeners=$currentListeners;localHttpStatus=$currentHttp.statusCode;ufwActive=$currentUfw.active;tcp3080Allowed=$currentUfw.tcp3080Allowed;directLanDenied=$currentDirect.denied;matchesBaseline=$baselineMatches}}})){return}
$record.candidatePreparation.verdict='PASS';$record.candidatePreparation.finishedAt=(Get-Date).ToUniversalTime().ToString('o');$record.overallVerdict='CANDIDATE_STATIC_PASS';& $persist $record
```

The single production step runner above owns all ten ordered checks. It persists a `BLOCKED` mutation and operation receipt before every remote write, flips both receipts to `PASS` only after that write returns successfully, and persists the final check state. Its catch path records only the failed check ID, leaves partial candidate state untouched, and stops the remaining steps; it never cleans up, repairs, retries, or invokes a service lifecycle action. The baseline comparison removes exactly the two capture timestamps (`selectorDiscovery.baseline.capturedAt` and `service.capturedAt`) and compares every other repository, identity, version, unit, listener, HTTP, UFW, and direct-LAN field canonically and exactly.

Expected typed success: checks 1-6 and 8-10 are `PASS`; check 7 is `PASS` when the installed static validator is supported, or the sole permitted `NOT PROVEN` when it is unsupported and the separately parsed loopback/zero-route/fallback assertions remain exact. `runtimeVerdict` is always `NOT PROVEN`; the ledgers contain only fixed-path `CREATE_DIRECTORY`/`WRITE_FILE` entries. Any isolation-affecting uncertainty is `BLOCKED` and stops the lane.

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

A fresh independent reviewer checks exact-path confinement, selector digest, blueprint equivalence, ownership/modes/links/ACL/mounts, value suppression, zero service lifecycle or privileged mutations, only the two allowlisted read-only baseline queries, no old-profile data flow, zero routes, fallback disabled, and runtime `NOT PROVEN`. Record acceptance against `candidateDigest`, rerun checks, and commit only:

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
