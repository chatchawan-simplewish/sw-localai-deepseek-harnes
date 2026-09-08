# VM105 pilot automatic SSH reconnect

Completed 2026-09-08 22:12 Asia/Bangkok. Owner explicitly selected automatic pilot reconnection after reboots, not resumption of the full provider roadmap. Repository: https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git. Authoritative branch: codex/vm105-authoritative-roadmap.

## Installed behavior

- Bell-PC2 task: `DeepSeek Harness VM105 SSH Tunnel`.
- Current user `BELL-PC2\chatc`, Interactive logon, Limited privileges, enabled user-logon trigger. No account password stored. Starts now and after that user signs in following a Windows reboot; it does not run before sign-in.
- Action: `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden -File C:\Users\chatc\Projects\DeepSeekHarnessRuntime\Start-VM105PilotTunnel.ps1`.
- Settings: IgnoreNew, no execution time limit, allowed on battery, start when available, restart on task failure up to three times at one-minute intervals.
- Supervisor checks for any existing listener on3080 before launching hidden SSH. Busy or unknown listener state waits without killing another process. After child exit or launch failure, retries after5s. SSH connect timeout10s; keepalive15s with3 unanswered probes. Recovery duration includes transport detection and VM/SSH availability; it is not guaranteed to occur within5s of a host reboot.
- SSH uses the existing project identity path with BatchMode, IdentitiesOnly, StrictHostKeyChecking and ExitOnForwardFailure. Only `127.0.0.1:3080` forwards to `dsh@192.168.1.139` remote `127.0.0.1:3080`. Credentials were not read, copied or logged. No VM/service/firewall changes or host reboot were performed.

## Verification

- [x] Unit behavior: Windows PowerShell5 test passed busy listener, failed listener query, startup failure, transport exit, safe fixed SSH options and child disposal. An in-memory mutation removing the listener guard was rejected. Independent reviewer accepted the final guard and persistent unsafe-launch test flag with no remaining material findings.
- [x] Installation: scheduled task readback confirms trigger, identity, action, settings and Running state. Installed script SHA256 matches repository source: `59E1E77B9C9C308E8DF89E2E8E2494B417FFA0BE255DF6CCF228B1EBF4FFF571`.
- [x] Live recovery: final supervisor55908 preserved the prior listener41388 without creating a duplicate. After parent stopped that exact prior child, supervisor created55232. Parent then stopped its verified own SSH child55232; same supervisor created33528, sole matching SSH process, listener127.0.0.1:3080, localhost HTTP200. This proves process-exit recovery, not an actual Prox-01 reboot or Windows sign-in test.

Initial scheduled launch from AppData failed; the stable Projects runtime location works. The failed AppData script copy and exact temporary test supervisor/SSH children were removed. No execution-policy weakening was used. PID values above are timestamped evidence, not future control targets.

## Use and rollback

Open http://127.0.0.1:3080/ while signed in to Bell-PC2. If Prox-01/VM105 goes away, leave the task running; it retries when SSH is available. Host-key changes and authentication failures remain rejected. Keep the installed runtime file and existing SSH key/known-host entry available.

To disable automatic reconnect, disable and stop the named scheduled task. Windows can leave its SSH child after the supervisor stops: enumerate current ssh.exe command lines, verify the exact loopback forward, target and parent ownership before stopping only that tunnel. Do not kill unrelated SSH sessions. The task may then be unregistered and the exact installed script removed if no longer wanted. No remote rollback is needed.

The internal pilot remains04/04 with its prior limitations; full roadmap09/21 and strict preparation BLOCKED are unchanged. This addition does not make sandbox enforcement or local provider availability proven.
