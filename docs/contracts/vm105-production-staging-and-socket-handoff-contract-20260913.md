# VM105 production staging and socket-handoff contract

Prepared 2026-09-13 against source baseline `40363b9468ebc3ca13334582d03479bb31ad6721`. This is a source-only contract. It grants no staging, gateway, credential, namespace, service, profile, selector, default, or live-execution authority.

## Accepted inputs

- Closure copy is accepted only against the 10,026-module manifest whose canonical SHA-256 is `4331e0e5fd9ac6f5e881a0dae941f9f07dea7b69969ee8b610071ce14cb03f8b`.
- The production gateway remains `http://192.168.1.68:20128/v1`. The coordinator must supply its action-time resolved IP and port; the receiver compares both peers to that exact pair.
- The credential key reference, version-1 credential schema, relay loopback origin, and current service selectors remain unbound. The launcher must stop before receiving sockets or starting the relay until those values are supplied through the separately accepted channels.
- `/var/tmp/omniroute-dsh-client-final-20260913` remains absent. This source must not create or inspect it during preparation or review.

## Host supervisor

The accepted supervisor implementation must:

1. Create one private `AF_UNIX` stream socket pair before containment and pass only the contained endpoint to the launcher.
2. Resolve the accepted gateway once at action time, record only its non-secret IP and port, and open exactly two connected TCP streams in fixed order: chat first, durable ACK second.
3. Send one `sendmsg` payload, exactly `VM105_GATEWAY_FDS_V1 chat ack`, with one or more `SCM_RIGHTS` records containing exactly those two descriptors in that order. It must send no third network descriptor.
4. Close its copies of both TCP descriptors and the control endpoint after a successful handoff. Any send or launcher failure closes all supervisor-owned descriptors and stops without reconnect, retry, discovery, or destination fallback.

No host-network listener is permitted. The concrete supervisor, namespace launcher, systemd wiring, cgroup cleanup, and service unit remain external acceptance work; the earlier `PrivateNetwork=yes` smoke does not prove this handoff.

## Contained launcher and relay

`scripts/Invoke-VM105FinalClient.py` provides `receive_gateway_sockets` and `TwoRequestRelay.from_socket_handoff` for a Linux launcher to use after entering the private network namespace.

The receiver requires Unix `SCM_RIGHTS` with atomic `MSG_CMSG_CLOEXEC`, the exact payload, zero returned receive flags, only `SOL_SOCKET`/`SCM_RIGHTS` ancillary records, and exactly two non-inheritable `AF_INET`/`AF_INET6` TCP stream sockets. It assigns descriptor zero to chat and descriptor one to durable ACK. Both peers must equal the externally supplied action-time gateway IP and port. Platforms without every required primitive fail before reading the control socket. The relay constructor closes the contained control endpoint after the one receive attempt, whether it succeeds or fails.

The existing relay then binds only its namespace-local `127.0.0.1` listener. Its first accepted request uses the chat descriptor and its second accepted request uses the ACK descriptor. Each claimed socket receives the relay timeout before an `HTTPConnection` adopts it; the relay does not call `connect`, resolve another host, or replace either stream. Existing tuple equality, ACK-before-output, third-request denial, zero retry, bounded shutdown, and cleanup rules remain in force.

Before the locked output commit, malformed metadata, truncation, an unexpected ancillary record, a wrong descriptor count, a wrong peer, a duplicate assignment, or protocol failure closes every received descriptor and releases no model output. After that commit, an additional request receives HTTP 403 without changing the successful transaction; normal completion or shutdown still closes the descriptors. No retry is permitted.

The production key must be supplied in memory only after the coordinator binds the opaque key identity/reference and accepted credential schema. It must not arrive in argv, environment, a committed file, logs, or receipts. Current service selectors do not enter this relay and remain a separate activation binding.

## Verification limit

The focused local suite exercises unsupported-platform failure plus mocked ancillary parsing, exact count and ordering, peer validation, cleanup, and no-connect relay wrapping. This Windows host has neither WSL nor Docker, so a real Linux `SCM_RIGHTS` transfer, namespace loopback listener, supervisor lifecycle, and systemd/cgroup cleanup remain **NOT PROVEN** and must pass independent live acceptance before use.
