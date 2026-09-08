# VM105 Scoped Package Path Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Recover the accepted VM105 Task 1 parser blocker by permitting a conservative npm scope only as a complete installed-path segment below `/opt/deepseek-harness`, then rerun fixed-wrapper installed-source discovery and record an independently accepted selector `PASS` or accepted `BLOCKED` result.

**Architecture:** Tighten the existing absolute-path validator with an installed-root-only segment grammar; the same grammar remains closed to every other `@`, traversal, shell metacharacter, and interpolation form. Reuse the existing evidence schema and Task 1 discovery boundary: the fixed wrapper selects the only entrypoint, every consumed installed file is a root-owned non-link regular file, and uncertainty produces reviewed `BLOCKED` evidence rather than discovery expansion.

**Tech Stack:** PowerShell 7, .NET standard library, Windows OpenSSH client, POSIX `stat`/`cat`/`find`/`sha256sum` already installed on VM105, JSON, Git.

## Global Constraints

- Project: DeepSeek Harness; repository: `C:\Users\chatc\Projects\sw-localai-deepseek-harnes`; verified origin: `https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git`; implementation worktree: `C:\Users\chatc\Projects\sw-localai-deepseek-harnes\.worktrees\vm105-authoritative-roadmap`; branch: `codex/vm105-authoritative-roadmap`.
- Modify only `scripts/Test-VM105ProfilePreparation.ps1` and `docs/evidence/vm105-profile-pointer-preparation.json`. Preserve all other tracked, ignored, and untracked work; stage exact paths only.
- The accepted starting evidence is selector digest `8CC8BA324B8FBC4560542A048DD51C4617BDA0C95F4BB73FFE298201D5E2FCA4`, review `ACCEPTED`, selector verdict `BLOCKED`, with `installedEntrypoint`, `selector`, and `candidateBlueprint` all `null`.
- The only new accepted `@` form is a complete path segment matching `^@[a-z0-9][a-z0-9._-]*$`, and only when the validation root is `/opt/deepseek-harness` or a descendant of it. Ordinary segments remain `^[A-Za-z0-9._-]+$`.
- Reject a lone `@`, uppercase or punctuation-leading scope, `@` inside an ordinary segment, scopes outside `/opt/deepseek-harness`, empty/doubled/trailing segments, `.`/`..`, backslashes, control characters, whitespace, quotes, shell metacharacters, command substitution, variable interpolation, or extra wrapper commands/arguments.
- Start installed-source discovery only at the root-owned, non-link, link-count-one, non-group/world-writable regular wrapper `/usr/local/bin/dsh`. Accept exactly one fixed absolute handoff and walk upward only from that entrypoint inside `/opt/deepseek-harness` to the nearest package-owned `package.json`.
- Require the entrypoint, package manifest, and every file used by an `installedSourceRef` to be a root-owned, non-link, link-count-one, non-group/world-writable regular file. Require package name/path agreement and installed version `0.1.1-rc.2`.
- Treat the current profile as opaque. Do not read, list, copy, move, write, infer, or delete its root or children. Store only sanitized installed-source references, digests, line ranges, claims, and the already approved typed evidence fields.
- All VM operations in this recovery are read-only. Do not create a candidate, stop/start/restart/reload a service, write a drop-in, install/update a package, read or create credentials, start API/OAuth/login/consent work, perform cutover, change a provider route, or mutate firewall/network state.
- Keep raw stderr, source text, unit environment, logs, credentials, tokens, and secret-shaped values out of chat, Git, evidence, screenshots, and reports. Source text may exist only in process memory while deriving a sanitized claim; any secret-shaped or ambiguous content blocks that reference.
- Keep the fixed candidate root, fixed-wrapper handoff, installed identity/version checks, selector proof-source separation, full-profile/non-merge requirements, zero-route/fallback policy, digest rules, read-only prerequisite status, and every other constraint from `docs/superpowers/plans/2026-09-08-vm105-reversible-profile-pointer.md` unchanged.
- The recovery ends with independent review tied to the recomputed `selectorDigest`. `ACCEPTED` means the recorded outcome is accurate; it does not convert `BLOCKED` to `PASS`.
- Original-plan Task 2 may resume only when this recovery records `selectorDiscovery.verdict: "PASS"`, `review.status: "ACCEPTED"`, `reviewedDigest` equal to the recomputed `selectorDigest`, and the Selector validator passes. Every other outcome remains stopped before candidate creation.

---

## Planned File Map

| Path | Responsibility |
| --- | --- |
| `scripts/Test-VM105ProfilePreparation.ps1` | Existing schema/digest/safety validator and synthetic self-test; add only the scoped installed-path contract and its RED/GREEN cases. |
| `docs/evidence/vm105-profile-pointer-preparation.json` | Existing typed Task 1 record; replace only selector-discovery results and review metadata derived from the bounded rerun, while retaining unrelated accepted fields unless a read-only observation proves drift. |

### Task 1: Admit only valid installed npm scope segments and rerun selector discovery

**Files:**
- Modify: `scripts/Test-VM105ProfilePreparation.ps1:49-57,457-552`
- Modify: `docs/evidence/vm105-profile-pointer-preparation.json:18-100`
- Test: `scripts/Test-VM105ProfilePreparation.ps1 -SelfTest`

**Interfaces:**
- Consumes: the existing `Assert-StrictPosixPath -Path [string] -Root [string] [-AllowRoot]` interface, accepted Task 1 evidence digest, fixed wrapper `/usr/local/bin/dsh`, installed package manifest/version, and package-owned source files reached from that handoff.
- Produces: the unchanged validator CLI `Test-VM105ProfilePreparation.ps1 -EvidencePath [string] -Stage Selector|Candidate|Closeout [-SelfTest]`, with installed-root-only npm-scope support and no broader path allowance.
- Produces: a recomputed selector digest whose review is independently `ACCEPTED` for either a fully proven selector `PASS` or a precise fail-closed `BLOCKED` result.

- [ ] **Step 1: Verify the exact starting boundary without changing it**

Run from the implementation worktree:

```powershell
$expectedOrigin='https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git'
$expectedBranch='codex/vm105-authoritative-roadmap'
if((git remote get-url origin).Trim() -cne $expectedOrigin){throw 'Unexpected repository origin'}
if((git branch --show-current).Trim() -cne $expectedBranch){throw 'Unexpected branch'}
$before=git status --short
$record=Get-Content -Raw -LiteralPath 'docs/evidence/vm105-profile-pointer-preparation.json' | ConvertFrom-Json -DateKind String
if($record.selectorDiscovery.selectorDigest -cne '8CC8BA324B8FBC4560542A048DD51C4617BDA0C95F4BB73FFE298201D5E2FCA4' -or
   $record.selectorDiscovery.review.status -cne 'ACCEPTED' -or
   $record.selectorDiscovery.verdict -cne 'BLOCKED' -or
   $null -ne $record.selectorDiscovery.installedEntrypoint -or
   $null -ne $record.selectorDiscovery.selector -or
   $null -ne $record.selectorDiscovery.candidateBlueprint){throw 'Accepted blocker baseline drifted'}
$before
```

Expected: origin and branch match; the evidence has the accepted blocker digest and null discovery artifacts. Record the status output and preserve every listed path not owned by this task.

- [ ] **Step 2: Add the RED installed-path behavior test before production logic**

Insert this test helper immediately before `if ($SelfTest)`, then call `Test-InstalledPathContract` as the first statement inside that block, before `New-SyntheticPreparationRecord`:

```powershell
function Test-InstalledPathContract {
    $failures=[Collections.Generic.List[string]]::new()
    $valid=@(
        [pscustomobject]@{name='ordinary installed path';path='/opt/deepseek-harness/package/dist/index.js';root='/opt/deepseek-harness/package'},
        [pscustomobject]@{name='scoped npm path';path='/opt/deepseek-harness/node_modules/@deepseek-ai/harness/dist/index.js';root='/opt/deepseek-harness/node_modules/@deepseek-ai/harness'}
    )
    foreach($case in $valid){
        try{Assert-StrictPosixPath $case.path $case.root}
        catch{$failures.Add("valid $($case.name) rejected: $($_.Exception.Message)")}
    }
    $invalid=@(
        [pscustomobject]@{name='arbitrary at';path='/opt/deepseek-harness/pkg@scope/index.js';root='/opt/deepseek-harness'},
        [pscustomobject]@{name='empty scope';path='/opt/deepseek-harness/@/index.js';root='/opt/deepseek-harness'},
        [pscustomobject]@{name='uppercase scope';path='/opt/deepseek-harness/@DeepSeek/index.js';root='/opt/deepseek-harness'},
        [pscustomobject]@{name='leading punctuation scope';path='/opt/deepseek-harness/@-deepseek/index.js';root='/opt/deepseek-harness'},
        [pscustomobject]@{name='scope outside installed root';path='/usr/local/bin/@deepseek-ai/dsh';root='/usr/local/bin'},
        [pscustomobject]@{name='traversal';path='/opt/deepseek-harness/@deepseek-ai/../index.js';root='/opt/deepseek-harness'},
        [pscustomobject]@{name='shell metacharacter';path='/opt/deepseek-harness/@deepseek-ai/pkg;id/index.js';root='/opt/deepseek-harness'},
        [pscustomobject]@{name='interpolation';path='/opt/deepseek-harness/@deepseek-ai/$(id)/index.js';root='/opt/deepseek-harness'}
    )
    foreach($case in $invalid){
        try{Assert-StrictPosixPath $case.path $case.root;$failures.Add("accepted $($case.name)")}
        catch{}
    }
    Assert-True ($failures.Count-eq0) "scoped-package-path contract failures: $($failures-join', ')"
}
```

The production mutations caught are: restoring the old root regex rejects the valid scoped case; treating `@` as a generic character accepts the arbitrary/empty/uppercase/punctuation/outside-root cases; weakening path safety accepts traversal, shell syntax, or interpolation. Expectations are literal paths and do not reuse production regexes.

- [ ] **Step 3: Run RED and confirm the exact missing behavior**

Run:

```powershell
./scripts/Test-VM105ProfilePreparation.ps1 -SelfTest
if($LASTEXITCODE -eq 0){throw 'RED unexpectedly passed'}
```

Expected: nonzero exit containing exactly this assertion payload (PowerShell may add location text):

```text
scoped-package-path contract failures: valid scoped npm path rejected: posix-root-shape, accepted arbitrary at, accepted empty scope, accepted uppercase scope, accepted leading punctuation scope, accepted scope outside installed root, accepted shell metacharacter, accepted interpolation
```

Do not edit the test after observing this expected failure.

- [ ] **Step 4: Replace only the absolute-path grammar with the minimal GREEN logic**

Replace the existing `Assert-StrictPosixPath` function with this complete implementation:

```powershell
function Assert-StrictPosixPath {
    param([string]$Path,[string]$Root,[switch]$AllowRoot)
    Assert-True (-not [string]::IsNullOrWhiteSpace($Path)) 'posix-path-empty'
    Assert-True ($Path[0] -ceq '/') 'posix-path-relative'
    Assert-True ($Path -notmatch '\\|//|(^|/)\.\.?(/|$)|[\x00-\x1f]') 'posix-path-shape'
    $installedRoot='/opt/deepseek-harness'
    $ordinaryPattern='^/(?:[A-Za-z0-9._-]+/)*[A-Za-z0-9._-]+$'
    $installedPattern='^/opt/deepseek-harness(?:/(?:[A-Za-z0-9._-]+|@[a-z0-9][a-z0-9._-]*))*$'
    $allowNpmScope=$Root -ceq $installedRoot -or $Root.StartsWith("$installedRoot/",[StringComparison]::Ordinal)
    Assert-True ($(if($allowNpmScope){$Root -cmatch $installedPattern}else{$Root -cmatch $ordinaryPattern})) 'posix-root-shape'
    Assert-True ($(if($allowNpmScope){$Path -cmatch $installedPattern}else{$Path -cmatch $ordinaryPattern})) 'posix-path-segment'
    $inside=$Path.StartsWith("$Root/",[StringComparison]::Ordinal)
    Assert-True ($inside -or ($AllowRoot -and $Path -ceq $Root)) 'posix-path-root'
}
```

This is the only production logic change. Do not add a general path library, configuration knob, new schema field, or second parser.

- [ ] **Step 5: Run GREEN locally before any VM read**

Run:

```powershell
./scripts/Test-VM105ProfilePreparation.ps1 -SelfTest
if($LASTEXITCODE -ne 0){throw 'Validator self-test failed'}
./scripts/Test-VM105ProfilePreparation.ps1 -EvidencePath 'docs/evidence/vm105-profile-pointer-preparation.json' -Stage Selector
if($LASTEXITCODE -ne 0){throw 'Accepted starting evidence no longer validates'}
```

Expected:

```text
SELF_TEST_PASS positive=6 negative=68
EVIDENCE_PASS stage=Selector
```

- [ ] **Step 6: Rerun only fixed-wrapper installed-source discovery with the corrected grammar**

Run one in-memory PowerShell block containing the GREEN `Assert-StrictPosixPath` from Step 4 and the complete code below. It uses the already approved identity, never writes remotely, and never prints returned source text or stderr:

```powershell
$expectedOrigin='https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git'
if((git remote get-url origin).Trim() -cne $expectedOrigin){throw 'Unexpected repository origin'}
if((git branch --show-current).Trim() -cne 'codex/vm105-authoritative-roadmap'){throw 'Unexpected branch'}
$sshOptionArgs=@(
    '-i','C:\Users\chatc\.ssh\codex-prox01-vms-ed25519',
    '-o','BatchMode=yes',
    '-o','IdentitiesOnly=yes',
    '-o','StrictHostKeyChecking=yes'
)
$sshDestination='dsh@192.168.1.139'

function ConvertTo-PosixShellLiteral {
    param([AllowEmptyString()][string]$Value)
    $singleQuote=[string][char]39
    $doubleQuote=[string][char]34
    return $singleQuote+$Value.Replace($singleQuote,$singleQuote+$doubleQuote+$singleQuote+$doubleQuote+$singleQuote)+$singleQuote
}

function Invoke-StrictSsh {
    param([string[]]$RemoteArgv,[int]$TimeoutSeconds=30,[int[]]$AllowedExitCodes=@(0))
    if(-not $RemoteArgv.Count){throw 'Empty remote argv'}
    $remoteCommand=(@($RemoteArgv | ForEach-Object{ConvertTo-PosixShellLiteral $_}) -join ' ')
    $psi=[Diagnostics.ProcessStartInfo]::new((Get-Command ssh.exe).Source)
    $psi.UseShellExecute=$false
    $psi.RedirectStandardOutput=$true
    $psi.RedirectStandardError=$true
    foreach($arg in @($sshOptionArgs+'--'+$sshDestination+$remoteCommand)){[void]$psi.ArgumentList.Add($arg)}
    $process=[Diagnostics.Process]::Start($psi)
    try{
        $stdoutTask=$process.StandardOutput.ReadToEndAsync()
        $stderrTask=$process.StandardError.ReadToEndAsync()
        $timedOut=-not $process.WaitForExit($TimeoutSeconds*1000)
        if($timedOut){$process.Kill($true)}
        $process.WaitForExit()
        $stdout=$stdoutTask.GetAwaiter().GetResult()
        [void]$stderrTask.GetAwaiter().GetResult()
        if($timedOut){throw 'SSH timeout'}
        $exitCode=$process.ExitCode
        if($exitCode -notin $AllowedExitCodes){throw "SSH exit $exitCode"}
        return [pscustomobject]@{RawStdout=$stdout;ExitCode=$exitCode}
    }finally{$process.Dispose()}
}

function Get-StrictSshScalar {
    param([string[]]$RemoteArgv)
    $value=(Invoke-StrictSsh $RemoteArgv).RawStdout.TrimEnd("`r","`n")
    if($value -match "`r|`n"){throw 'BLOCKED multiline scalar metadata'}
    return $value
}

function ConvertTo-PreservedSourceLines {
    param([string]$RawText)
    return @([regex]::Split($RawText,"`r`n|`n|`r"))
}

function ConvertFrom-InstalledFileMetadata {
    param([string]$Line,[string]$ExpectedPath,[string]$RequiredOwner,[string]$RequiredGroup)
    $parts=$Line -split '\|',6
    if($parts.Count-ne6 -or $parts[0]-cne$ExpectedPath -or $parts[1]-cne'regular file' -or $parts[2]-cne$RequiredOwner -or $parts[3]-cne$RequiredGroup -or [int]$parts[5]-ne1){throw 'BLOCKED installed file metadata'}
    if(([Convert]::ToInt32($parts[4],8)-band18)-ne0){throw 'BLOCKED writable installed file'}
    return [pscustomobject]@{path=$parts[0];type=$parts[1];symlink=$false;owner=$parts[2];group=$parts[3];mode=('0'+$parts[4]);linkCount=[int]$parts[5]}
}

function Assert-CanonicalInstalledPath {
    param([string]$Path,[switch]$AllowRoot)
    Assert-StrictPosixPath $Path '/opt/deepseek-harness' -AllowRoot:$AllowRoot
    $resolved=Get-StrictSshScalar @('/usr/bin/readlink','-f','--',$Path)
    if($resolved-cne$Path){throw 'BLOCKED installed symlink path'}
}

function Assert-RootOwnedInstalledFile {
    param([string]$Path)
    Assert-CanonicalInstalledPath $Path
    $line=Get-StrictSshScalar @('/usr/bin/stat','-c','%n|%F|%U|%G|%a|%h','--',$Path)
    return ConvertFrom-InstalledFileMetadata $line $Path 'root' 'root'
}

function Assert-RootOwnedInstalledDirectory {
    param([string]$Path)
    Assert-CanonicalInstalledPath $Path -AllowRoot
    $parts=(Get-StrictSshScalar @('/usr/bin/stat','-c','%n|%F|%U|%G|%a','--',$Path)) -split '\|',5
    if($parts.Count-ne5 -or $parts[0]-cne$Path -or $parts[1]-cne'directory' -or $parts[2]-cne'root' -or $parts[3]-cne'root' -or ([Convert]::ToInt32($parts[4],8)-band18)-ne0){throw 'BLOCKED installed directory metadata'}
}

function Find-NearestInstalledPackageRoot {
    param(
        [string]$Entrypoint,
        [scriptblock]$AssertDirectory={param($Path) Assert-RootOwnedInstalledDirectory $Path},
        [scriptblock]$AssertFile={param($Path) Assert-RootOwnedInstalledFile $Path},
        [scriptblock]$GetTestExit={param($Test,$Path) (Invoke-StrictSsh @('/usr/bin/test',$Test,$Path) -AllowedExitCodes @(0,1)).ExitCode}
    )
    $current=$Entrypoint.Substring(0,$Entrypoint.LastIndexOf('/',[StringComparison]::Ordinal))
    while($current.StartsWith('/opt/deepseek-harness/',[StringComparison]::Ordinal) -or $current-ceq'/opt/deepseek-harness'){
        & $AssertDirectory $current
        $manifestPath="$current/package.json"
        if((& $GetTestExit '-r' $current)-ne0 -or (& $GetTestExit '-x' $current)-ne0){throw 'BLOCKED unreadable package directory'}
        if((& $GetTestExit '-L' $manifestPath)-eq0){throw 'BLOCKED package manifest symlink'}
        if((& $GetTestExit '-e' $manifestPath)-eq0){
            [void](& $AssertFile $manifestPath)
            return $current
        }
        $slash=$current.LastIndexOf('/',[StringComparison]::Ordinal)
        if($slash-le0){break}
        $current=$current.Substring(0,$slash)
    }
    throw 'BLOCKED package root'
}

function Get-VerifiedInstalledEntrypoint {
    $wrapperPath='/usr/local/bin/dsh'
    $wrapperResolved=Get-StrictSshScalar @('/usr/bin/readlink','-f','--',$wrapperPath)
    if($wrapperResolved-cne$wrapperPath){throw 'BLOCKED wrapper symlink path'}
    $wrapperLine=Get-StrictSshScalar @('/usr/bin/stat','-c','%n|%F|%U|%G|%a|%h','--',$wrapperPath)
    $wrapper=ConvertFrom-InstalledFileMetadata $wrapperLine $wrapperPath 'root' 'root'
    $wrapperRaw=(Invoke-StrictSsh @('/usr/bin/cat','--',$wrapperPath)).RawStdout
    $wrapperLines=ConvertTo-PreservedSourceLines $wrapperRaw
    $meaningful=@($wrapperLines | Where-Object{$_ -and $_ -notmatch '^#!' -and $_ -notmatch '^set -e(?:u)?$'})
    if($meaningful.Count-ne1){throw 'BLOCKED wrapper shape'}
    $match=[regex]::Match($meaningful[0],'^exec\s+(?:(/[A-Za-z0-9._/-]+)\s+)?((?:/opt/deepseek-harness)(?:/\S+)+)(?:\s+"\$@")?\s*$')
    if(-not $match.Success -or $meaningful[0] -match '\$\(|`|\$\{'){throw 'BLOCKED wrapper entrypoint'}
    if($match.Groups[1].Success){
        $interpreterPath=$match.Groups[1].Value
        $interpreterResolved=Get-StrictSshScalar @('/usr/bin/readlink','-f','--',$interpreterPath)
        if($interpreterResolved-cne$interpreterPath){throw 'BLOCKED wrapper interpreter symlink'}
        $interpreterLine=Get-StrictSshScalar @('/usr/bin/stat','-c','%n|%F|%U|%G|%a|%h','--',$interpreterPath)
        [void](ConvertFrom-InstalledFileMetadata $interpreterLine $interpreterPath 'root' 'root')
    }
    $entrypoint=$match.Groups[2].Value
    Assert-StrictPosixPath $entrypoint '/opt/deepseek-harness'
    $entry=Assert-RootOwnedInstalledFile $entrypoint
    $packageRoot=(Find-NearestInstalledPackageRoot -Entrypoint $entrypoint)
    $package=(Invoke-StrictSsh @('/usr/bin/cat','--',"$packageRoot/package.json")).RawStdout | ConvertFrom-Json
    if(-not $package.name -or $package.version-cne'0.1.1-rc.2'){throw 'BLOCKED package identity'}
    $packageName=[string]$package.name
    if($packageName-cmatch'^(@[a-z0-9][a-z0-9._-]*)/([a-z0-9][a-z0-9._-]*)$'){
        $expectedSuffix="/$($Matches[1])/$($Matches[2])"
    }elseif($packageName-cmatch'^[a-z0-9][a-z0-9._-]*$'){
        $expectedSuffix="/$packageName"
    }else{throw 'BLOCKED package identity'}
    if(-not $packageRoot.EndsWith($expectedSuffix,[StringComparison]::Ordinal)){throw 'BLOCKED package path identity'}
    $wrapperSha=(Get-StrictSshScalar @('/usr/bin/sha256sum','--',$wrapperPath)).Split(' ')[0].ToUpperInvariant()
    $entrySha=(Get-StrictSshScalar @('/usr/bin/sha256sum','--',$entrypoint)).Split(' ')[0].ToUpperInvariant()
    return [pscustomobject]@{
        wrapperPath=$wrapper.path;wrapperType=$wrapper.type;wrapperSymlink=$wrapper.symlink;wrapperOwner=$wrapper.owner;wrapperGroup=$wrapper.group;wrapperMode=$wrapper.mode;wrapperLinkCount=$wrapper.linkCount;wrapperSha256=$wrapperSha
        entrypointPath=$entry.path;entrypointType=$entry.type;entrypointSymlink=$entry.symlink;entrypointOwner=$entry.owner;entrypointGroup=$entry.group;entrypointMode=$entry.mode;entrypointLinkCount=$entry.linkCount;entrypointSha256=$entrySha
        packageRoot=$packageRoot;packageName=$packageName;packageVersion=[string]$package.version
    }
}

$identity=Get-StrictSshScalar @('/usr/bin/id','-un')
if($identity-cne'dsh'){throw 'BLOCKED unexpected VM105 identity'}
$installed=Get-VerifiedInstalledEntrypoint
$sourcePaths=@(
    ConvertTo-PreservedSourceLines (Invoke-StrictSsh @('/usr/bin/find',$installed.packageRoot,'-xdev','-type','f','-print')).RawStdout |
        Where-Object{$_ -match '/package\.json$|/README[^/]*$|/(docs|src|dist)/'}
)
foreach($path in $sourcePaths){
    if(-not $path.StartsWith("$($installed.packageRoot)/",[StringComparison]::Ordinal) -and $path-cne"$($installed.packageRoot)/package.json"){throw 'BLOCKED package walk escape'}
    [void](Assert-RootOwnedInstalledFile $path)
}
```

Before the bounded identity read and any other VM call, run these local synthetic checks in the same PowerShell process, against the functions above. The child process is local and only proves that both redirected pipes drain beyond their normal buffer size:

```powershell
function Assert-RunnerCheck { param([bool]$Condition,[string]$Message) if(-not $Condition){throw $Message} }

$quoted=(@('stat','-c','%n|%F|%U|%G|%a|%h','--','/path with space',"quote'value",'$(id);|&') | ForEach-Object{ConvertTo-PosixShellLiteral $_}) -join ' '
Assert-RunnerCheck ($quoted -ceq "'stat' '-c' '%n|%F|%U|%G|%a|%h' '--' '/path with space' 'quote'`"'`"'value' '`$(id);|&'") 'POSIX argv quoting check failed'

$pwshPath=(Microsoft.PowerShell.Core\Get-Command pwsh).Source
$savedGetCommand=${function:Get-Command}
$savedSshOptionArgs=$sshOptionArgs;$savedSshDestination=$sshDestination
try{
    ${function:Get-Command}={param($Name) if($Name-ceq'ssh.exe'){return [pscustomobject]@{Source=$pwshPath}};Microsoft.PowerShell.Core\Get-Command $Name}
    $sshOptionArgs=@('-NoProfile','-Command',"[Console]::Out.Write('o'*131072);[Console]::Error.Write('e'*131072);exit 0 #")
    $sshDestination='ignored'
    $localResult=Invoke-StrictSsh @('ignored') -TimeoutSeconds 10
    Assert-RunnerCheck ($localResult.ExitCode-eq0 -and $localResult.RawStdout.Length-eq131072) 'actual SSH helper async pipe drain failed'
}finally{
    $sshOptionArgs=$savedSshOptionArgs;$sshDestination=$savedSshDestination
    if($null-eq$savedGetCommand){Remove-Item Function:Get-Command}else{${function:Get-Command}=$savedGetCommand}
}

$raw="first`n`nthird`n"
$preserved=ConvertTo-PreservedSourceLines $raw
Assert-RunnerCheck ($preserved.Count-eq4 -and $preserved[1]-ceq'' -and $preserved[3]-ceq'' -and (($preserved -join "`n")-ceq$raw)) 'raw stdout line preservation failed'

$savedScalar=${function:Get-StrictSshScalar};$script:scalarCalls=0
try{
    ${function:Get-StrictSshScalar}={param([string[]]$RemoteArgv) [void]($script:scalarCalls++);if($RemoteArgv[0]-ceq'/usr/bin/readlink'){return $RemoteArgv[-1]};return "$($RemoteArgv[-1])|directory|root|root|755"}
    Assert-RootOwnedInstalledDirectory '/opt/deepseek-harness'
    $rootCalls=$script:scalarCalls
    $siblingBlocked=$false
    try{Assert-RootOwnedInstalledDirectory '/opt/deepseek-harness-other'}catch{$siblingBlocked=$true}
    Assert-RunnerCheck ($rootCalls-eq2 -and $siblingBlocked -and $script:scalarCalls-eq$rootCalls) 'actual directory helper AllowRoot boundary failed'
}finally{${function:Get-StrictSshScalar}=$savedScalar}

$noop={param($Path) [void]$Path}
$script:probe=0
$absentThenPresent={param($Test,$Path) if($Test-in @('-r','-x')){return 0};if($Test-ceq'-L'){return 1};$script:probe++;if($script:probe-eq1){return 1};return 0}
$foundRoot=(Find-NearestInstalledPackageRoot '/opt/deepseek-harness/pkg/dist/index.js' $noop $noop $absentThenPresent)
Assert-RunnerCheck ($foundRoot-ceq'/opt/deepseek-harness/pkg') 'absent manifest did not ascend to the nearest present manifest'
$unsafe={param($Test,$Path) if($Test-in @('-r','-x')){return 0};if($Test-ceq'-L'){return 0};return 1}
$transport={param($Test,$Path) throw 'SSH exit 255'}
foreach($case in @([pscustomobject]@{Name='unsafe';Probe=$unsafe},[pscustomobject]@{Name='transport';Probe=$transport})){
    $blocked=$false
    try{[void](Find-NearestInstalledPackageRoot '/opt/deepseek-harness/pkg/dist/index.js' $noop $noop $case.Probe)}catch{$blocked=$true}
    Assert-RunnerCheck $blocked "$($case.Name) manifest case did not stop"
}

$savedScalar=${function:Get-StrictSshScalar};$savedInvoke=${function:Invoke-StrictSsh};$script:sourceReads=0;$script:scalarReads=0
try{
    ${function:Get-StrictSshScalar}={param([string[]]$RemoteArgv) [void]($script:scalarReads++);return '/redirected/usr/local/bin/dsh'}
    ${function:Invoke-StrictSsh}={param([string[]]$RemoteArgv) [void]($script:sourceReads++);throw 'source read unexpectedly reached'}
    $wrapperBlocked=$false
    try{[void](Get-VerifiedInstalledEntrypoint)}catch{$wrapperBlocked=$true}
    Assert-RunnerCheck ($wrapperBlocked -and $script:scalarReads-eq1 -and $script:sourceReads-eq0) 'actual wrapper helper read after canonical mismatch'
}finally{${function:Get-StrictSshScalar}=$savedScalar;${function:Invoke-StrictSsh}=$savedInvoke}
```

Read only those verified package-owned source files in memory. Preserve each file's raw stdout, split it with `ConvertTo-PreservedSourceLines` only when deriving exact one-based line ranges, and obtain its exact digest separately with the verified `sha256sum -- <path>` call before constructing an `installedSourceRef`. Never trim or rejoin source text. Selector `PASS` still requires direct installed-source proof for absolute path support, precedence, non-merge behavior, service compatibility, and all five mutable-store classes. Query only the proven selector key from effective unit metadata. If any claim, file boundary, ownership, link status, name/version, or selector behavior is missing or ambiguous, stop source inspection and record a precise `BLOCKED` reason; do not search another installation root, home directory, service environment, log, network package source, or current profile.

- [ ] **Step 7: Replace the selector-discovery result and recompute its digest**

Modify only the existing evidence record. Preserve `schemaVersion`, `workflowId`, `target`, the accepted baseline unless a permitted read-only check proves drift, `cutoverPrerequisites`, `candidatePreparation: null`, `closeout: null`, and the operation-ledger schema.

For a directly proven result, set `installedEntrypoint`, `selector`, and `candidateBlueprint` to the exact typed objects required by the approved parent plan; set `selectorDiscovery.verdict` to `PASS`, `blockers` to `[]`, and `overallVerdict` to `SELECTOR_PASS`. For every incomplete result, set `selector` and `candidateBlueprint` to `null`, set `selectorDiscovery.verdict` and `overallVerdict` to `BLOCKED`, and set `blockers` to one or more sanitized exact reasons. Preserve a verified `installedEntrypoint` in the blocked record only when all of its identity/metadata checks completed.

In both branches, set `selectorDiscovery.capturedAt` to current UTC, reset review to exactly:

```json
{
  "status": "PENDING",
  "reviewedAt": null,
  "reviewer": null,
  "reviewedDigest": null,
  "findings": []
}
```

Recompute `selectorDigest` with the validator's existing canonical algorithm, excluding only `selectorDigest` and `review`; run this complete block in the same process that writes the JSON:

```powershell
function Get-UpperSha256 {
    param([byte[]]$Bytes)
    return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($Bytes))
}
function ConvertTo-CanonicalNode {
    param([object]$Value)
    if($null-eq$Value){return $null}
    if($Value-is[string] -or $Value-is[ValueType]){return $Value}
    if($Value-is[Collections.IDictionary]){
        $ordered=[ordered]@{}
        foreach($key in @($Value.Keys | Sort-Object)){$ordered[[string]$key]=ConvertTo-CanonicalNode $Value[$key]}
        return $ordered
    }
    if($Value-is[Collections.IEnumerable]){
        $items=[Collections.Generic.List[object]]::new()
        foreach($item in $Value){$items.Add((ConvertTo-CanonicalNode $item))}
        return ,$items.ToArray()
    }
    $object=[ordered]@{}
    foreach($property in @($Value.psobject.Properties.Name | Sort-Object)){$object[$property]=ConvertTo-CanonicalNode $Value.$property}
    return $object
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
$evidencePath='docs/evidence/vm105-profile-pointer-preparation.json'
$record=Get-Content -Raw -LiteralPath $evidencePath | ConvertFrom-Json -DateKind String
$record.selectorDiscovery.selectorDigest=Get-CanonicalStageDigest $record.selectorDiscovery @('selectorDigest','review')
$json=$record | ConvertTo-Json -Depth 100
[IO.File]::WriteAllText((Resolve-Path -LiteralPath $evidencePath),$json+"`n",[Text.UTF8Encoding]::new($false))
```

The first selector-stage validation must fail with `review-status-value` while review is `PENDING`; this is the required independent-review gate, not a defect.

- [ ] **Step 8: Commit the reviewable recovery using exact paths**

Run all local checks, confirm the diff contains only the two owned implementation paths, then commit:

```powershell
& ./scripts/Test-VM105ProfilePreparation.ps1 -SelfTest
if($LASTEXITCODE-ne0){throw 'Validator self-test failed'}
& ./scripts/Test-Phase03Evidence.ps1 -Stage Network
if($LASTEXITCODE-ne0){throw 'Phase 03 Network validation failed'}
git diff --check -- 'scripts/Test-VM105ProfilePreparation.ps1' 'docs/evidence/vm105-profile-pointer-preparation.json'
if($LASTEXITCODE-ne0){throw 'Implementation diff check failed'}
$changed=@(git diff --name-only)
if($LASTEXITCODE-ne0){throw 'Unable to enumerate implementation changes'}
$unexpected=@($changed | Where-Object{$_ -cnotin @('scripts/Test-VM105ProfilePreparation.ps1','docs/evidence/vm105-profile-pointer-preparation.json')})
if($unexpected.Count){throw "Unexpected changed path: $($unexpected-join', ')"}
$alreadyStaged=@(git diff --cached --name-only)
if($LASTEXITCODE-ne0){throw 'Unable to enumerate staged paths'}
if($alreadyStaged.Count){throw "Pre-staged path blocks exact commit: $($alreadyStaged-join', ')"}
git add -- 'scripts/Test-VM105ProfilePreparation.ps1' 'docs/evidence/vm105-profile-pointer-preparation.json'
if($LASTEXITCODE-ne0){throw 'Exact-path implementation stage failed'}
$staged=@(git diff --cached --name-only)
if($LASTEXITCODE-ne0 -or @($staged | Where-Object{$_ -cnotin @('scripts/Test-VM105ProfilePreparation.ps1','docs/evidence/vm105-profile-pointer-preparation.json')}).Count){throw 'Unexpected staged implementation path'}
git -c user.name='Codex' -c user.email='codex@local' commit -m 'fix: validate VM105 scoped package paths'
if($LASTEXITCODE-ne0){throw 'Implementation commit failed'}
```

Expected: self-test pass, Phase 03 Network check exit `0`, diff check exit `0`, and one exact-path implementation commit. The selector evidence intentionally remains `PENDING` until the next step.

- [ ] **Step 9: Obtain independent selector review and finalize only its typed metadata**

Give a fresh reviewer the approved parent plan, accepted starting evidence/report, this recovery plan, the implementation commit SHA, both changed files, the RED output, GREEN output, and sanitized discovery receipts. The reviewer must independently verify:

1. the scope regex is a full segment, lowercase/conservative, installed-root-only, and cannot admit arbitrary `@`, traversal, shell syntax, interpolation, or scope use in `/usr/local/bin` or candidate paths;
2. the wrapper still has one fixed absolute handoff, with no fallback/extra arguments, and all wrapper/entrypoint/manifest/proof-source files are root-owned safe regular non-links with package name/path/version agreement;
3. every selector semantic claim comes from its exact installed-source digest and line range, with all five mutable stores and non-merge/precedence/absolute-path/service-compatibility claims present for `PASS`;
4. no current-profile, candidate, service lifecycle, drop-in, package, credential/OAuth/login/consent, provider-route, firewall, or network mutation occurred; and
5. the recomputed digest matches the reviewed selector object and the recorded `PASS` or `BLOCKED` verdict is fail-closed.

On findings, set review to `REJECTED`, use the reviewer task name, current UTC, the exact `selectorDigest`, and sanitized findings. Correct only the two owned files; any validator behavior correction starts with a new failing self-test before logic and receives another independent review.

On acceptance, set review to `ACCEPTED`, use the independent reviewer task name, current UTC, the exact `selectorDigest`, and `findings: []`. Do not change any digest-covered selector field after acceptance. Validate and commit the metadata-only finalization:

```powershell
& ./scripts/Test-VM105ProfilePreparation.ps1 -SelfTest
if($LASTEXITCODE-ne0){throw 'Validator self-test failed'}
& ./scripts/Test-VM105ProfilePreparation.ps1 -EvidencePath 'docs/evidence/vm105-profile-pointer-preparation.json' -Stage Selector
if($LASTEXITCODE-ne0){throw 'Selector validation failed'}
& ./scripts/Test-Phase03Evidence.ps1 -Stage Network
if($LASTEXITCODE-ne0){throw 'Phase 03 Network validation failed'}
git diff --check -- 'docs/evidence/vm105-profile-pointer-preparation.json'
if($LASTEXITCODE-ne0){throw 'Review metadata diff check failed'}
$alreadyStaged=@(git diff --cached --name-only)
if($LASTEXITCODE-ne0){throw 'Unable to enumerate staged paths'}
if($alreadyStaged.Count){throw "Pre-staged path blocks metadata commit: $($alreadyStaged-join', ')"}
git add -- 'docs/evidence/vm105-profile-pointer-preparation.json'
if($LASTEXITCODE-ne0){throw 'Exact-path metadata stage failed'}
$staged=@(git diff --cached --name-only)
if($LASTEXITCODE-ne0 -or $staged.Count-ne1 -or $staged[0]-cne'docs/evidence/vm105-profile-pointer-preparation.json'){throw 'Unexpected staged metadata path'}
git -c user.name='Codex' -c user.email='codex@local' commit -m 'docs: finalize VM105 selector recovery review'
if($LASTEXITCODE-ne0){throw 'Review metadata commit failed'}
```

Expected:

```text
SELF_TEST_PASS positive=6 negative=68
EVIDENCE_PASS stage=Selector
```

- [ ] **Step 10: Enforce the stop/resume gate and report the bounded outcome**

Run:

```powershell
if(-not $evidencePath){$evidencePath='docs/evidence/vm105-profile-pointer-preparation.json'}
& (Get-Command pwsh).Source -NoProfile -File './scripts/Test-VM105ProfilePreparation.ps1' -EvidencePath $evidencePath -Stage Selector
if($LASTEXITCODE-ne0){throw 'Selector validation failed; recovery remains stopped'}
$record=Get-Content -Raw -LiteralPath $evidencePath | ConvertFrom-Json -DateKind String
$accepted=$record.selectorDiscovery.review.status -ceq 'ACCEPTED' -and
          $record.selectorDiscovery.review.reviewedDigest -ceq $record.selectorDiscovery.selectorDigest
$resumeTask2=$accepted -and $record.selectorDiscovery.verdict -ceq 'PASS'
[pscustomobject]@{
    selectorVerdict=$record.selectorDiscovery.verdict
    reviewStatus=$record.selectorDiscovery.review.status
    selectorDigest=$record.selectorDiscovery.selectorDigest
    originalPlanTask2=$(if($resumeTask2){'MAY_RESUME'}else{'STOPPED'})
} | Format-List
if(-not $accepted){throw 'Recovery outcome lacks accepted independent review'}
```

Before using the real record, prove locally that a stale reviewed digest cannot reach the resume decision. This fixture copies the accepted evidence to a temporary local file, changes only its reviewed digest, invokes the actual validator through the exact Step 10 block extracted from this plan, and removes the temporary file. It performs no remote writes:

```powershell
$planPath='docs/superpowers/plans/2026-09-08-vm105-scoped-package-path-recovery.md'
$planText=Get-Content -Raw -LiteralPath $planPath
$gateMatch=[regex]::Match($planText,'(?ms)^```powershell\r?\n(?<gate>if\(-not \$evidencePath\).*?Recovery outcome lacks accepted independent review''\}\r?\n)^```\s*$')
if(-not $gateMatch.Success){throw 'Unable to extract exact Step 10 gate'}
$gate=[scriptblock]::Create($gateMatch.Groups['gate'].Value)
$tempEvidence=New-TemporaryFile
try{
    $stale=Get-Content -Raw -LiteralPath 'docs/evidence/vm105-profile-pointer-preparation.json' | ConvertFrom-Json -DateKind String
    $stale.selectorDiscovery.review.reviewedDigest=('0'*64)
    [IO.File]::WriteAllText($tempEvidence.FullName,($stale | ConvertTo-Json -Depth 100)+"`n",[Text.UTF8Encoding]::new($false))
    $evidencePath=$tempEvidence.FullName
    $gateStopped=$false
    try{& $gate}catch{$gateStopped=$_.Exception.Message -ceq 'Selector validation failed; recovery remains stopped'}
    if(-not $gateStopped){throw 'Actual Step 10 gate did not stop stale reviewed digest'}
}finally{Remove-Item -LiteralPath $tempEvidence.FullName -Force}
```

If `originalPlanTask2` is `MAY_RESUME`, hand the exact accepted selector digest back to the original plan and resume at Task 2 only. If it is `STOPPED`, report the accepted blockers and take no further action. Neither branch authorizes candidate creation, cutover, service/systemd work, credentials, or any other prohibited operation during this recovery task.
