# VM105 OS isolation and later default-routing boundary

Prepared 2026-09-13.  This is a coordination record, not an execution plan or a transfer of any live VM105 resource.

## Read-only isolation metadata result

The only attempted VM105 metadata query used SSH as `dsh@192.168.10.105`, with BatchMode and strict host-key checking.  Its remote payload was limited to `command -v` for `bwrap`, `bubblewrap`, `podman`, `docker`, `nerdctl`, `runc`, `crun`, `unshare`, and `nsenter`; reads of three kernel namespace sysctls; and presence checks for the calling process's user, mount, PID, and network namespace handles.

At 2026-09-13, SSH connection to port 22 timed out before authentication or command execution.  Therefore none of the queried binaries, kernel settings, or namespace facilities is established as present or usable on VM105.

| Facility | Status | What remains required before it may support the final copied-client draft |
| --- | --- | --- |
| Bubblewrap (`bwrap`) | NOT PROVEN | Read-only path/version and unprivileged-user-namespace policy; then a separately authorized containment rehearsal. |
| Rootless container runtime | NOT PROVEN | Read-only runtime and rootless prerequisites; then a separately authorized network-none, bounded-root rehearsal. |
| Native namespaces (`unshare`) | NOT PROVEN | Read-only binary and kernel policy; then a separately authorized test that proves mount, PID, and network containment. |
| OCI runtimes (`runc` or `crun`) | NOT PROVEN | Read-only path and rootless suitability; then a separately authorized rehearsal. |

No container, namespace, process, service, firewall, pilot, credential, or routing action ran.  The SSH timeout is not evidence of VM105 isolation capability or incapability.

## Relationship to the final copied-client draft

The existing final copied-client draft remains unchanged.  A future accepted isolation facility may be selected only if it enforces the draft's bounded writable root, denied egress, and descendant reaping requirements.  Binary presence alone is insufficient, and a successful isolated client acceptance remains synthetic-client evidence only.

## Later real-DSH default-routing activation lane

An isolated acceptance can be followed by a separately reviewed default-routing lane in principle.  It cannot automatically promote the isolated client or inherit its authority.

That later lane needs an explicit transfer that names all of the following before any execution:

1. The exact real-DSH client configuration/profile and its current default-routing baseline, with a narrow owner and immutable pre-change evidence.
2. The exact new default endpoint, credential-reference channel, and trust material; credential values remain owner-only and absent from evidence.
3. The exact process/service and configuration files permitted to change, plus one rollback target that restores the prior default.
4. Current VM105 service, route, and provider-readiness prechecks immediately before activation, followed by acceptance evidence from the real DSH client.
5. Independent review and coordinator acceptance of the activation and rollback transaction, plus the required owner readiness for a production routing/identity mutation.

At present, this activation lane is not transferable: the final copied-client draft excludes the opaque pilot and service/default-profile ownership, and no exact production default target, credential acceptance, or cutover authority is bound.  Any later lane must be a new, narrowly scoped handoff; it must not reinterpret the isolated test as activation.
