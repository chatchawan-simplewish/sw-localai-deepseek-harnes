# VM105 internal pilot readiness

Observed 2026-09-08 20:40-20:41 Asia/Bangkok. Read-only availability check for the owner-approved current-instance internal pilot; provider/model and coding acceptance remain separate.

Project: DeepSeek Harness. Verified origin: https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git

## Availability checks - 04/04

| Check | Result | Fresh evidence |
| --- | --- | --- |
| VM service | PASS | Strict SSH to `dsh@192.168.1.139`: `deepseek-harness.service` has `ActiveState=active`, `SubState=running`, `NRestarts=0`. |
| VM listener and HTTP | PASS | Port 3080 listener is only `127.0.0.1:3080`; VM loopback HTTP status `200`. The `0.0.0.0:*` peer column from `ss` is not a local bind. |
| Existing Bell-PC2 SSH forward | PASS | `ssh.exe`, PID `42076`, owns listeners `127.0.0.1:3080` and `[::1]:3080`; argv forwards to the approved VM105 target. |
| Tunneled HTTP | PASS | Bell-PC2 `http://127.0.0.1:3080/` returned HTTP status `200`. |

SSH checks used the existing key path, `BatchMode=yes`, `IdentitiesOnly=yes`, `StrictHostKeyChecking=yes`, `ConnectTimeout=10`, and an options terminator before `dsh@192.168.1.139`. Remote inspection was restricted to the three service properties above, loopback HTTP status, and port-3080 listeners. No response body, environment, service logs, profile, or credentials were read.

Existing nonsecret forwarding argv (line wrapping normalized):

```text
"C:\WINDOWS\System32\OpenSSH\ssh.exe" -N -i C:\Users\chatc\.ssh\codex-prox01-vms-ed25519 -o BatchMode=yes -o IdentitiesOnly=yes -o ExitOnForwardFailure=yes -o ServerAliveInterval=15 -L 3080:127.0.0.1:3080 dsh@192.168.1.139
```

Only processes owning the existing local port-3080 listeners were queried; no general process inventory was performed. This historical tunnel argv does not explicitly set `StrictHostKeyChecking`; fresh readiness SSH commands did set it. No tunnel was created or replaced.

## Limits and impact

The existing SSH path is available for the pilot. Browser profile selection, provider writes, model response, and disposable coding task are owned by the parent task and are not proven by these checks. Direct LAN reachability and firewall state were not retested in this bounded lane. Existing interpreter ownership acceptance applies to this trial; no ownership proof or hardening was performed. Earlier blocked preparation evidence and roadmap remain unchanged.

No service, package, systemd, network, profile, credential, or ownership changes were made. Continue using the existing forward; any alternate instance or exposure remains a separate scope choice.

## Authorized disposable workspace setup

At 2026-09-08 20:42 Asia/Bangkok, the parent authorized creation of the pilot workspace only if absent. Strict SSH confirmed the effective user is `dsh`, `/srv/dsh/workspaces` is a writable/searchable directory for that user, and `readlink -e` resolves that parent to the exact same canonical path. The target was absent, including no dangling symlink, so `umask 077` and `mkdir -m 0700` without `-p` created it. A conflicting creation would fail rather than overwrite.

```text
WORKSPACE_ACTION=CREATED
WORKSPACE_PATH=/srv/dsh/workspaces/internal-pilot-20260908 OWNER=dsh GROUP=dsh MODE=700 TYPE=directory
```

No code files were created. This is the sole live mutation in this lane, subsequently authorized separately from the availability check. Provider/model and actual Harness coding-task validation remain with the parent.
