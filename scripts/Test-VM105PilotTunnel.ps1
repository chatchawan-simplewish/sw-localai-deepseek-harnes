$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/Start-VM105PilotTunnel.ps1"

# Exercise busy port, failed listener query, startup failure, and transport exit
# without opening a socket. Every case must delay and retry safely.
$script:launches = 0
$script:unsafeLaunch = $false
$script:queries = 0
$script:delays = 0
$script:waited = $false
$script:disposed = $false
function Get-NetTCPConnection {
    param($State, $ErrorAction)
    if ($State -ne 'Listen' -or $ErrorAction -ne 'Stop') { throw 'TEST: unsafe listener query' }
    $script:queries++
    if ($script:queries -eq 1) { return [pscustomobject]@{ LocalPort = 3080 } }
    if ($script:queries -eq 2) { throw 'Simulated listener query failure' }
    return [pscustomobject]@{ LocalPort = 22 }
}
function Start-Process {
    param($FilePath, $ArgumentList, $WindowStyle, [switch]$PassThru, $ErrorAction)
    if ($script:queries -lt 3) {
        $script:unsafeLaunch = $true
        throw 'TEST: launched while listener state busy or unknown'
    }
    if ($FilePath -ne "$env:SystemRoot/System32/OpenSSH/ssh.exe" -or $WindowStyle -ne 'Hidden' -or -not $PassThru) {
        throw 'TEST: expected hidden Windows OpenSSH child'
    }
    $forwardIndex = [array]::IndexOf($ArgumentList, '-L')
    if ($forwardIndex -lt 0 -or $ArgumentList[$forwardIndex + 1] -ne '127.0.0.1:3080:127.0.0.1:3080' -or
        $ArgumentList[-1] -ne 'dsh@192.168.1.139' -or $ArgumentList -contains '-R' -or $ArgumentList -contains '-g') {
        throw 'TEST: tunnel must target VM105 and bind loopback only'
    }
    foreach ($option in @('BatchMode=yes', 'IdentitiesOnly=yes', 'StrictHostKeyChecking=yes',
        'ExitOnForwardFailure=yes', 'ConnectTimeout=10', 'ServerAliveInterval=15', 'ServerAliveCountMax=3')) {
        $index = [array]::IndexOf($ArgumentList, $option)
        if ($index -lt 1 -or $ArgumentList[$index - 1] -ne '-o') { throw "TEST: missing SSH option $option" }
    }
    $keyIndex = [array]::IndexOf($ArgumentList, '-i')
    if ($keyIndex -lt 0 -or $ArgumentList[$keyIndex + 1] -ne 'C:/Users/chatc/.ssh/codex-prox01-vms-ed25519' -or
        $ArgumentList -notcontains '-N') { throw 'TEST: expected dedicated identity and no remote command' }
    $script:launches++
    if ($script:launches -eq 1) { throw 'Simulated process startup failure' }
    $process = New-Object PSObject
    $process | Add-Member ScriptMethod WaitForExit { $script:waited = $true }
    $process | Add-Member ScriptMethod Dispose { $script:disposed = $true }
    return $process
}
function Start-Sleep {
    param($Seconds)
    if ($Seconds -ne 5) { throw 'Unexpected retry delay' }
    $script:delays++
    if ($script:delays -le 2 -and $script:launches -ne 0) { throw 'Launched while listener state busy or unknown' }
    if ($script:delays -eq 4) { throw 'TestComplete' }
}
try { Start-VM105PilotTunnel }
catch { if ($_.Exception.Message -ne 'TestComplete') { throw } }
if ($script:unsafeLaunch -or $script:queries -ne 4 -or $script:launches -ne 2 -or -not $script:waited -or -not $script:disposed) {
    throw 'Supervisor did not retry startup failure and wait for/dispose the exited child'
}
'PASS: busy/unknown listener blocks launch; hidden strict loopback SSH; startup/transport retries; child disposal'
