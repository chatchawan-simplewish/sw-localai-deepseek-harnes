#requires -Version 7.0
# Extracted from reviewed scoped-package-path recovery Step 6.
# Default is local self-test. -Discover executes the newly authorized discovery scope.
# This inventories eligible installed sources; it does not establish selector PASS.
[CmdletBinding(DefaultParameterSetName='SelfTest')]
param(
    [Parameter(ParameterSetName='SelfTest')][switch]$SelfTest,
    [Parameter(Mandatory,ParameterSetName='Discover')][switch]$Discover
)
$ErrorActionPreference='Stop'

function Assert-True {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) { throw $Message }
}

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
    $inside=$Path.StartsWith("$Root/",[StringComparison]::Ordinal)
    Assert-True ($inside -or ($AllowRoot -and $Path -ceq $Root)) 'posix-path-root'
    Assert-True ($(if($allowNpmScope){$Path -cmatch $installedPattern}else{$Path -cmatch $ordinaryPattern})) 'posix-path-segment'
}

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

# Run the reviewed local checks before any live identity/source operation.
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

if(-not $Discover){
    'RUNNER_SELF_TEST_PASS'
    exit 0
}

$installed=$null
$sourcePaths=@()
try{
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
    [pscustomobject]@{
        capturedAt=[DateTimeOffset]::UtcNow.ToString('o')
        verdict='DISCOVERY_READY'
        localRunnerChecks='PASS'
        installed=$installed
        eligibleSourceCount=$sourcePaths.Count
        selectorVerdict='NOT PROVEN'
        rawOutputStored=$false
    } | ConvertTo-Json -Depth 6 -Compress
    exit 0
}catch{
    # Only fixed error labels can leave the process; never emit parser/source errors.
    $message=[string]$_.Exception.Message
    $safeLabels=@(
        'BLOCKED multiline scalar metadata','BLOCKED installed file metadata',
        'BLOCKED writable installed file','BLOCKED installed symlink path',
        'BLOCKED installed directory metadata','BLOCKED unreadable package directory',
        'BLOCKED package manifest symlink','BLOCKED package root',
        'BLOCKED wrapper symlink path','BLOCKED wrapper shape',
        'BLOCKED wrapper entrypoint','BLOCKED wrapper interpreter symlink',
        'BLOCKED package identity','BLOCKED package path identity',
        'BLOCKED unexpected VM105 identity','BLOCKED package walk escape',
        'SSH timeout','posix-path-empty','posix-path-relative','posix-path-shape',
        'posix-root-shape','posix-path-root','posix-path-segment'
    )
    $blocker=if($message -cin $safeLabels -or $message -cmatch '^SSH exit [0-9]+$'){$message}else{'BLOCKED discovery error (details suppressed)'}
    [pscustomobject]@{
        capturedAt=[DateTimeOffset]::UtcNow.ToString('o')
        verdict='BLOCKED'
        localRunnerChecks='PASS'
        blocker=$blocker
        selectorVerdict='NOT PROVEN'
        rawOutputStored=$false
    } | ConvertTo-Json -Compress
    exit 1
}
