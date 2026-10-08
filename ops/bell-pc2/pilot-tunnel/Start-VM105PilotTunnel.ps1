# Run with Windows PowerShell -NoProfile -WindowStyle Hidden -File <this file>.
# Task Scheduler supplies the current-user logon trigger and IgnoreNew policy.
# An occupied port is left alone; retry later without launching another child.

function Get-VM105PilotTunnelArguments {
    @(
        '-N', '-i', 'C:/Users/chatc/.ssh/codex-prox01-vms-ed25519',
        '-o', 'BatchMode=yes',
        '-o', 'IdentitiesOnly=yes',
        '-o', 'StrictHostKeyChecking=yes',
        '-o', 'ExitOnForwardFailure=yes',
        '-o', 'ConnectTimeout=10',
        '-o', 'ServerAliveInterval=15',
        '-o', 'ServerAliveCountMax=3',
        '-L', '127.0.0.1:3080:127.0.0.1:3080',
        'dsh@192.168.1.139'
    )
}

function Start-VM105PilotTunnel {
    while ($true) {
        $tunnelProcess = $null
        try {
            # Query all listeners: an absent specific port is otherwise a CIM error.
            $listeners = @(Get-NetTCPConnection -State Listen -ErrorAction Stop | Where-Object LocalPort -eq 3080)
            if ($listeners.Count -eq 0) {
                $tunnelProcess = Start-Process -FilePath "$env:SystemRoot/System32/OpenSSH/ssh.exe" `
                    -ArgumentList (Get-VM105PilotTunnelArguments) -WindowStyle Hidden -PassThru -ErrorAction Stop
                $tunnelProcess.WaitForExit()
            }
        }
        catch {
            # Listener-query, startup, authentication, bind, and transport failures retry.
            # Do not log credentials or modify a conflicting listener.
        }
        finally {
            if ($null -ne $tunnelProcess) { $tunnelProcess.Dispose() }
        }
        Start-Sleep -Seconds 5
    }
}

if ($MyInvocation.InvocationName -ne '.') { Start-VM105PilotTunnel }
