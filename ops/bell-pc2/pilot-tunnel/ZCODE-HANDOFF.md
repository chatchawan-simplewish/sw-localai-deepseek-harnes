# DeepSeekHarnessRuntime — ZCode Handoff (2026-09-30)

Written 2026-09-30 ~15:30 Bangkok by a read-only Claude Code audit. No secret values appear in this file.

## 1. What this project is

This is a runtime folder on Bell-PC2 that holds one file, `Start-VM105PilotTunnel.ps1` (2026-09-08). The script keeps an SSH local forward `127.0.0.1:3080 -> VM105 127.0.0.1:3080` alive so the DeepSeek Harness web UI on VM105 can be opened at `http://127.0.0.1:3080` on this PC.

It loops forever:
- If nothing listens on port 3080, it starts `C:\Windows\System32\OpenSSH\ssh.exe -N` and waits for it to exit.
- It retries every 5 s.
- It never touches a port that another process already holds.

There is no git, build or tests.

## 2. Current state snapshot

- It is not a git repo. Last modified 2026-09-08.
- A Windows Scheduled Task **"DeepSeek Harness VM105 SSH Tunnel"** (state `Ready`) runs `powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden -File C:\Users\chatc\Projects\DeepSeekHarnessRuntime\Start-VM105PilotTunnel.ps1`. It has a user-logon trigger and the IgnoreNew policy.
- The target VM105 (192.168.1.139) is **currently stopped by the user's choice** (SW-LocalAI state, 2026-09-30). The script therefore just retries quietly.

## 3. Unfinished tasks

| # | Task | Status | Next step |
|---|---|---|---|
| 1 | None specific to this folder | — | — |
| 2 | Decide whether the tunnel task should stay enabled while VM105 is off | **DECIDED 2026-10-03**: task disabled + stopped (ZCode, user asked what was opening the terminal; no answer to the choice prompt, so the reversible recommendation was applied). Script and task definition kept | To revive when VM105 returns: `Enable-ScheduledTask -TaskName "DeepSeek Harness VM105 SSH Tunnel"` then `Start-ScheduledTask -TaskName "DeepSeek Harness VM105 SSH Tunnel"` |

For the real open work, see the DeepSeek Harness repo handoff: `C:\Users\chatc\Projects\sw-localai-deepseek-harnes\ZCODE-HANDOFF.md`.

## 4. How to run / test

```powershell
# manual run (foreground loop; Ctrl+C to stop)
powershell -NoProfile -File C:\Users\chatc\Projects\DeepSeekHarnessRuntime\Start-VM105PilotTunnel.ps1
# status
Get-ScheduledTask -TaskName "DeepSeek Harness VM105 SSH Tunnel"; Get-NetTCPConnection -State Listen -LocalPort 3080
```
Dot-sourcing the file (`. .\Start-VM105PilotTunnel.ps1`) only defines the functions and does not start the loop.

## 5. Infrastructure and hosts

VM105 DeepSeek Harness is at `dsh@192.168.1.139`, with remote port 3080 (DSH web). It runs on the prox-01 cluster. The script uses no SSH alias, only an explicit key and host.

## 6. Credentials and secrets (locations only)

| What | Where | Env var | Used by |
|---|---|---|---|
| SSH private key | `C:\Users\chatc\.ssh\codex-prox01-vms-ed25519` | — | the tunnel (`-i`, `IdentitiesOnly`, `BatchMode`) |
| VM105 host key | `C:\Users\chatc\.ssh\known_hosts` | — | `StrictHostKeyChecking=yes`: the connection fails if it is missing |
| DSH web login | unknown (the DSH UI's own auth on VM105) | — | browser |

## 7. Things outside this folder that ZCode needs

- `C:\Users\chatc\.ssh\` (key and known_hosts), and Windows OpenSSH.
- The Scheduled Task above.
- Related projects:
  - `C:\Users\chatc\Projects\sw-localai-deepseek-harnes`: DSH ops, the infra-admin MCP, and the blocked VM105 roadmap
  - `C:\Users\chatc\Projects\SW-LocalAI`: prox-01 and VM state, and the main infra handoff (`ZCODE-HANDOFF.md`)

## 8. Gotchas

- Do not log credentials, and do not kill a process that already holds :3080 (by design).
- Windows OpenSSH `ssh.exe` can hang when its output is piped without a console. This script avoids that with `Start-Process -WindowStyle Hidden`.
- Project rules, including the Bangkok timestamp line and the decision format, come from the DSH repo `AGENTS.md`.

## 9. Suggested first prompt for ZCode

```text
Read C:\Users\chatc\Projects\DeepSeekHarnessRuntime\ZCODE-HANDOFF.md. Read-only: confirm the "DeepSeek Harness VM105 SSH Tunnel" scheduled task state and whether 127.0.0.1:3080 is listening. Do not change the task. Then continue with C:\Users\chatc\Projects\sw-localai-deepseek-harnes\ZCODE-HANDOFF.md.
```
