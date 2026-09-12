# VM105 native systemd containment smoke-test contract

Prepared 2026-09-13 from read-only VM105 metadata.  This is a proposed, non-executing contract for an isolated copied-client smoke test.  It does not authorize a unit, directory, process, service, profile, firewall, credential, or routing change.

## Observed feasibility

VM105 has systemd 255, `/usr/bin/systemd-run`, `/usr/bin/systemctl`, and `/usr/bin/systemd-analyze`.  `systemd-run --help` advertises property assignment, `--wait`, and `--collect`.  The `dsh` account's current sudo policy is passwordless unrestricted sudo (`NOPASSWD: ALL`), rather than a narrow command allowlist.

Therefore a transient system unit is the smallest available native containment candidate: it needs no package installation or container runtime.  It is only a candidate.  The broad sudo grant cannot itself prove least privilege, and property behavior, no-network enforcement, writable-root confinement, and descendant cleanup remain unproven until a separately authorized rehearsal.

## Proposed isolated smoke-test contract

If separately reviewed and authorized, create one fresh, uncreated staging root under `/var/tmp/omniroute-dsh-client-final-20260913` and run exactly one transient systemd service under a unique name.  The service must use `User=dsh`, `Group=dsh`, that root as its working directory, and a fixed no-secret smoke command only.

The transient unit must set these minimum properties:

| Requirement | Unit property |
| --- | --- |
| Deny network and DNS | `PrivateNetwork=yes`; `RestrictAddressFamilies=AF_UNIX` |
| Read-only host with one writable staging root | `ProtectSystem=strict`; `ReadWritePaths=/var/tmp/omniroute-dsh-client-final-20260913` |
| Hide real home while retaining the declared staging root | `ProtectHome=yes` |
| Isolate host devices and shared-memory surfaces | `PrivateDevices=yes` |
| Prevent privilege gain | `NoNewPrivileges=yes`; empty `CapabilityBoundingSet`; `RestrictSUIDSGID=yes` |
| Bound process lifetime and descendants | `Type=exec`; `KillMode=control-group`; `Delegate=no`; `TasksMax=64`; finite `RuntimeMaxSec` and `TimeoutStopSec` |

The command must use `systemd-run --wait` without `--collect`, with only these reviewed properties and the fixed smoke command.  While the unit still exists, its evidence must record the unit name, effective property values, cgroup path, exit result, and preserved staging-root manifest.  Only after evidence is retained may the coordinator choose an exact-unit collection action.  On timeout or unexpected output, stop the transient unit, use `systemctl kill --kill-who=all` only on that exact unit, confirm the cgroup is empty, and retain the staging root and evidence.  Never target `deepseek-harness.service`.

This no-network smoke has no HTTP request, including the final draft's two native HTTP requests.  It establishes containment behavior only and cannot be claimed as copied-client or protocol acceptance.  A later, separately reviewed acceptance contract must provide its exact in-namespace receipt sink and narrowly permit only the required transport.  The smoke has no secret-bearing environment, file, argv, or persistent state.  It cannot use port 3080, the running normal service, `/home/dsh/.dsh`, `/home/dsh/.dsh-profiles/vm105-provider-v1`, or any provider route.

## Real DSH default-routing targets: secret-free metadata

Current read-only metadata establishes these process and path targets:

| Item | Observed value | Limit |
| --- | --- | --- |
| Running service | `deepseek-harness.service`, active/running | Current service target only. |
| Unit fragment | `/etc/systemd/system/deepseek-harness.service` | Unit contents were not read. |
| Service account | `dsh:dsh` (UID/GID 1000) | No account data beyond identity metadata was read. |
| Main process | PID 2568, executable `/opt/node-v24.19.0-linux-x64/bin/node`, command name `MainThread` | Arguments and environment were not read. |
| Working directory | `/srv/dsh/workspaces` | Directory metadata only. |
| Account home and known DSH paths | `/home/dsh`, `/home/dsh/.dsh`, `/home/dsh/.dsh-profiles`, `/home/dsh/.dsh-profiles/vm105-provider-v1` | All exist; existence does not prove the running service consumes any one path. |
| Unit environment-file property | empty | This does not establish the absence of direct environment or other configuration input. |

This identifies the future activation surface without exposing configuration contents.  It does **not** establish the current default provider/profile selection.  A later default-routing transfer must bind that selection through a secret-free, reviewed configuration receipt, then explicitly permit only the named unit/drop-in or named new profile pointer, one restart transaction, one rollback target, and real-client acceptance.  Isolated smoke acceptance does not activate or authorize that lane.

## Next reviewed action

Independent review should first check the property set against systemd 255 semantics and confirm that the staging-root, two-request, credential-descriptor, and rollback requirements remain intact.  Only after acceptance may the coordinator request a separately authorized, one-shot rehearsal.  The real DSH activation lane remains a later explicit transfer with owner readiness.
