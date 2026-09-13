# VM105 Linux Production Orchestration Source Plan

**Goal:** Implement the smallest source-only Linux launcher that uses the accepted staging copier and two-socket relay while keeping every live binding and action fail closed.

**Baseline:** `b6b0d6524b1fc040a37448e331589d41a45c4b1b`

**Authority boundary:** Local source, mocked/local tests, review evidence, commits, and branch publication only. Do not connect a gateway, read a real credential, create or inspect the final staging root, start a namespace or systemd unit, touch a cgroup, or change any VM, provider, firewall, service, profile, selector, default, or one-shot gate.

## Task 1: Linux supervisor and contained worker

**Owned files:**
- `scripts/Invoke-VM105ProductionLauncher.py`
- `scripts/test_vm105_production_launcher.py`

Use one Linux-only Python launcher and the standard library. Reuse `receive_gateway_sockets`, `TwoRequestRelay.from_socket_handoff`, and `stage_verified_closure`; do not add another proxy, manifest, or relay.

The concrete transfer mechanism is:

1. The outer launcher invokes one root transient service with `systemd-run --wait --pipe`. Only standard input carries the credential document; do not use or claim arbitrary inherited descriptors.
2. The service validates every non-secret binding, reads the bounded credential document from standard input, writes it once to a fresh anonymous close-on-exec pipe, closes the write end before forking, and wipes its temporary byte buffer.
3. The service creates one close-on-exec Unix socket pair and forks. The worker creates a session, calls `unshare(CLONE_NEWNET)`, raises only `lo` through Linux ioctl, proves its network namespace differs from its parent, closes all descriptors except its control endpoint, credential read descriptor, and bounded receipt channel, then drops groups/GID/UID to `dsh`.
4. After the worker reports namespace readiness, the root supervisor resolves no names and opens exactly two TCP connections to the already bound numeric action-time gateway peer, once, in chat then durable-ACK order. One `sendmsg` transfers the accepted fixed payload and exactly those two descriptors. The supervisor closes its copies immediately and never retries or falls back.
5. The contained entry consumes the existing socket receiver/relay and credential read descriptor. Until gateway, credential schema/reference, relay origin, and current selector bindings are all supplied, the production entry stops before credential read, connection, fork, namespace creation, or service start.
6. The supervisor uses bounded waits, process identity, process-group termination, `waitid(...WNOWAIT)`, and `waitpid`. The outer systemd wrapper binds a unique unit description, `KillMode=control-group`, `Delegate=no`, `Restart=no`, bounded start/run/stop times, and verifies the exact `InvocationID`, `ControlGroup`, result, and empty-or-removed cgroup before returning a sanitized receipt.

Add focused tests for the fail-closed binding gate, exact `systemd-run --pipe` command without `pass_fds`, credential pipe ordering and wiping seam, worker isolation/FD allowlist/privilege-drop order, exactly two numeric-peer connections and one `sendmsg`, send/child/timeout cleanup, systemd identity and empty-cgroup proof, and secret-free receipts. The Windows host must reject real execution before any operating-system action; mock only the Linux boundary needed to test orchestration.

## Task 2: Durable evidence and contract update

**Owned files:**
- `docs/contracts/vm105-production-staging-and-socket-handoff-contract-20260913.md`
- `docs/handoffs/vm105-omniroute-final-client-packet-20260913.md`
- `docs/evidence/vm105-source-preparation-independent-review-transcription-20260913.md`

Update the contract and packet with the selected single-service supervisor/forked-worker design. State that the unit itself keeps host networking for the two fixed connections while only the worker enters `CLONE_NEWNET`; do not retain a literal whole-unit `PrivateNetwork=yes` claim. Record that `systemd-run --pipe` is the selected credential transport and arbitrary descriptor inheritance is not used.

Write an accurately labeled transcription of the prior `b6b0d65` Sol High task output. Name the source task and reviewed revision, and state clearly that this is a durable transcription created afterward rather than an original reviewer-authored file.

## Task 3: Independent review and publication

1. Commit the reviewed launcher, tests, contract, packet, plan, and transcription with exact-path staging and command-scoped Git identity.
2. Run only the focused changed-behavior tests and local dry-plan checks; real Linux systemd, namespace, cgroup, credential, and socket transfer remain NOT PROVEN on this Windows host.
3. Assign a fresh Sol High reviewer exclusive ownership of `docs/evidence/vm105-production-linux-orchestration-independent-review-20260913.md`. The reviewer must record the exact source revision and diff range, evidence paths/hashes, test results, findings, limits, and explicit publish verdict.
4. Commit that reviewer-authored verdict separately, verify its file hash and the remote branch head, publish, and send the coordinator a compact packet with remaining live bindings.
