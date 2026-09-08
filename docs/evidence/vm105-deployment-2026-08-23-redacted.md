# VM105 deployment record — expressly redacted

> **Expressly redacted:** This record contains no credential values and no OAuth
> state. It preserves safe operational facts only. Source:
> `C:\Users\chatc\Projects\SW-LocalAI\worktrees\deepseek-harness-vm105\DeepSeek-Harness\deployment-2026-08-23.md`
> at commit `a3fcfc3f141fe54719598335d28358b6a681ebb7`; source SHA-256:
> `127DD18DFD6978E504ED1DE54951533CFF1F15DA23FD5EE4FA7D322C538A89BF`.

## Historical deployment evidence — 2026-08-23

VM105 (`deepseek-harness-01`) runs the official DeepSeek Harness Web profile
as unprivileged user `dsh`, is reboot-persistent, and leaves VM104/Hermes
unchanged. The Web UI is loopback-only at `127.0.0.1:3080` and is accessed from
Bell-PC2 through an SSH local forward.

| Item | Historical value |
| --- | --- |
| VM | `105`, `deepseek-harness-01` |
| Compute | 8 host CPU cores; 16 GiB fixed RAM; ballooning disabled |
| Disk | 160 GiB thin-provisioned `local-lvm`; discard and IO thread enabled |
| OS | Ubuntu 24.04 Noble cloud image |
| Network | DHCP `192.168.1.139/24`; MAC `BC:24:11:5C:49:52` |
| Boot | `onboot=1`; `order=50,up=60,down=120`; QEMU agent responsive |
| Node.js | `v24.19.0`; tarball SHA-256 `14b342e71204f811bde6153be8e04b62aef63c236fef92b55f9c83154b409647` |
| Package tools | npm `11.17.0`; Corepack `0.35.0`; pnpm `11.7.0` |
| Harness | `@deepseek-ai/dsh@0.1.1-rc.2` |

### Security and service

- SSH is key-only for `dsh`; root and password attempts were rejected.
- UFW is active, defaults to deny incoming, and historically allowed only
  Bell-PC2 (`192.168.1.161`) to TCP 22.
- `deepseek-harness.service` was enabled and active with `Result=success` and
  `NRestarts=0` after the acceptance reboot.
- The listener was limited to `127.0.0.1:3080`; direct LAN TCP 3080 was
  unreachable. Cloud-init completed with zero errors.
- `/home/dsh/.dsh` was mode `0700`; `/srv/dsh/workspaces` was mode `0750`.

| File | Historical SHA-256 |
| --- | --- |
| `/etc/systemd/system/deepseek-harness.service` | `5019702fa48ea6067de59b5071297f80450b90bd759a813236b71db7e4bf6ec0` |
| `/etc/ssh/sshd_config.d/60-dsh-hardening.conf` | `88e7833403ca45e59065c13959cb2858dced4bf924ddc6543a07025c8f6e8b96` |
| `/usr/local/bin/dsh` | `553ca65c989274e30583bfa56b08a3bca1a9b613e6647680f57558b19406dd14` |
| `/opt/deepseek-harness/pnpm-lock.yaml` | `df7a474e07c6120e1533679816a260ea4b998549118c1a21cc47ba015a8af6da` |

### Historical acceptance matrix

| Check | Result | Evidence |
| --- | --- | --- |
| VM105 configuration and QEMU agent | **PASS** | Resources, disk, MAC, boot policy, running state, and agent ping verified |
| Key-only SSH and UFW | **PASS** | `dsh` key worked; root/password rejects; Bell-PC2 TCP 22 allowed |
| Pinned Harness runtime | **PASS** | DSH `0.1.1-rc.2`; Node `v24.19.0`; integrity recorded |
| Loopback Web UI | **PASS** | `127.0.0.1:3080`; local HTTP 200 |
| Bell-PC2 SSH tunnel | **PASS** | Temporary `localhost:13080` forward returned UI HTTP 200 |
| Direct LAN Web denial | **PASS** | `192.168.1.139:3080` unreachable before and after reboot |
| Reboot recovery | **PASS** | Service enabled/active; success; zero restarts; HTTP 200 |
| Existing VM configuration preservation | **PASS** | VM104/1201/1202/1203/1204 hashes unchanged |
| OpenRouter routes | **NOT PROVEN** | No fresh VM105 credential entered |
| VM1201 worker | **NOT PROVEN** | No VM105 credential or route-specific TCP 8000 rule installed |
| Bell-PC2 local worker | **NOT PROVEN** | No VM105-specific credential entered |
| Typhoon text / OCR | **NOT PROVEN** | Provider setup not demonstrated |
| Codex routes | **NOT PROVEN** | Fresh DSH OAuth login not completed |
| Automatic dispatch and invalid-key failure | **NOT PROVEN** | No real provider route was available to exercise it |

### Bell-PC2 tunnel

Keep this PowerShell command running on Bell-PC2, then open
<http://127.0.0.1:3080>:

```powershell
ssh.exe -N -i 'C:\Users\chatc\.ssh\codex-prox01-vms-ed25519' -o BatchMode=yes -o IdentitiesOnly=yes -o ExitOnForwardFailure=yes -o ServerAliveInterval=15 -L 3080:127.0.0.1:3080 dsh@192.168.1.139
```

Enter any future provider settings only through write-only Harness UI fields.
Use explicit provider/model selection per session until black-box attribution
proves provider, model, and reasoning selection.

### Switchable choices

| Choice | Current selection | Later alternative / trade-off |
| --- | --- | --- |
| VM size | 8 vCPU / 16 GiB / 160 GiB | Resize after measured use |
| Address | DHCP `.139` | Router reservation recommended; guest static adds drift |
| Web access | SSH tunnel | Authenticated Caddy/TLS is easier but permanently exposed |
| Default model | Explicit selection | Automatic selection only after credential and attribution tests |
| Local workers | Disabled pending authorization | Enable each with separate credentials and narrow rules |
| Task routing | Manual per session | Reviewed plugin or fixed upstream release after black-box tests |
| Codex | Fresh DSH OAuth | Leave disabled for subscription isolation |
| VM104/Hermes | Running and unchanged | Stop only after VM105 provider parity is proven |

### Advisories and rollback

- DeepSeek Harness `0.1.1-rc.2` is a developer preview.
- Proxmox reported thin-pool overcommit warnings; actual free pool capacity and
  host RAM passed, but storage policy was not changed.
- DHCP `.139` was not a proven router reservation.
- Reversible rollback is `qm stop 105`. Deleting VM105 or its disks remains
  unauthorized.

## Current revalidation evidence — 2026-09-08

### Repository source baseline — captured 2026-09-08 07:48 Asia/Bangkok

This is the source-checkout baseline captured before the later isolated-branch
commits in `C:\Users\chatc\Projects\sw-localai-deepseek-harnes\.worktrees\vm105-authoritative-roadmap`.
It is not a claim about the later isolated branch.

| Field | Captured value |
| --- | --- |
| Source checkout | `C:\Users\chatc\Projects\sw-localai-deepseek-harnes` |
| Remote | `https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git` |
| Branch | `main` |
| Local `HEAD` | `927ec51ec4c6bdd69f5fd50ecd4a6eb5ec73e7c1` |
| Remote `origin/main` | `927ec51ec4c6bdd69f5fd50ecd4a6eb5ec73e7c1` |
| Dirty result | `0` |

### VM105 current measurements — 2026-09-08

These are current revalidation measurements, distinct from the historical
2026-08-23 deployment evidence above.

| Check | Result | Evidence / boundary |
| --- | --- | --- |
| VM identity and address | **PASS** | Hostname `deepseek-harness-01`; address `192.168.1.139` |
| Harness version | **PASS** | `0.1.1-rc.2` |
| Service | **PASS** | `deepseek-harness.service` is enabled and active; `Result=success`; `NRestarts=0` |
| Listener and local HTTP | **PASS** | Listener exactly `127.0.0.1:3080`; local HTTP `200` |
| Cloud-init | **PASS** | Current status completed without errors |
| pnpm version | **WARN** | Current `11.22.0` differs from historical `11.7.0`; no mutation made |
| UFW SSH rules | **PASS** | Exactly `192.168.1.161 -> TCP 22` (Bell-PC2 SSH) and `192.168.1.141 -> TCP 22` (VM104/Hermes SSH) |
| RX drops | **WARN** | `234093` to `234129`: `+36/45s`; observation only, no network change made |
| VM104-rule provenance | **CONFIRMED** | Hermes VM104 SSH exception origin is documented; current need is **NOT PROVEN** and the rule remains unchanged |
| Bell-PC2 tunnel and UI | **PASS** | Tunnel and UI verified from Bell-PC2 |
| Direct LAN port denial | **PASS** | Direct access to TCP 3080 remains denied |
| Provider credentials and routes | **NOT PROVEN** | No credential values, OAuth state, or route claims are recorded here |

All provider credentials and routes remain **NOT PROVEN** pending separately
authorized configuration and route-specific verification.
