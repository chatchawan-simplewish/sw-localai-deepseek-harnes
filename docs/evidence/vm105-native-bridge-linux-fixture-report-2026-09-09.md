# Linux synthetic bridge fixture — offline implementation

Prepared 20260909 042844 Asia/Bangkok. Repository: https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git. Implementation owner: bounded `linux_bridge_fixture` sub-agent. Files outside the assigned fixture and this report were not changed.

## Frozen inputs and result

- Fixture: `scripts/test-native-codex-owner-linux.mjs`, SHA256 `6f82e2f2783123255f9e441cde991da2bdcbddbf92bd9f4dc6cc7e1b12cc1414`.
- Reviewed owner module read in full: `scripts/native-codex-owner.mjs`, SHA256 `90bb452d25d5b6c7c7593e2cfc7c01650069d1d63f4770728bff5ef32935b14b`.
- Existing `scripts/native-codex-owner.test.mjs` and `docs/superpowers/plans/2026-09-09-vm105-native-bridge-linux-check.md` read before implementation.
- Windows `node --check scripts/test-native-codex-owner-linux.mjs`: exit0. This is syntax validation only. Linux transport is **NOT PROVEN**; no SSH, Linux fixture execution, installation, provider, credential service, real authorization, service control or Git publication occurred.

## Invocation and containment contract

Invoke the pinned Node executable with the deployed fixture path and exactly one prepared private root argument. Deploy the frozen owner module adjacent to the fixture for its static relative import. The root must already exist as the executing user's0700 directory beneath ancestors permitted by the bridge's actual `privateDirectory` policy. This fixture does not create or relax the root or ancestor modes.

The separately reviewed launcher must provide an isolated network namespace, sanitized environment, unprivileged identity, pinned source and executable bytes, a fresh one-attempt root, and an external30-second child deadline with exact child-tree termination. This script is a test, not a containment mechanism. It does not load Cordis, application profiles, adapters or any real authorization/credential implementation.

The main fixture refuses all six pre-existing synthetic names before testing: `flow.sock`, `disconnect.sock`, `preexisting.sock`, `replacement.fixture`, `replacement.sock`, `retained.sock`. It retains harmless synthetic fixtures after the attempt; it performs no recursive deletion. The only fixture renames move the deliberately created socket to `retained.sock` and the deliberately created marker to `replacement.sock`. The bridge owns its ordinary socket disposal.

## Checks and finite behavior

The main script emits one fixed-schema JSON object plus newline, coordinated with the launcher implementation. Success is exactly `{"status":"LINUX_BRIDGE_PASS","checks":{"passiveSocket0600":true,"fakeDeviceFlowOnce":true,"ownedSocketRemoved":true,"disconnectAbortAndDispose":true,"preexistingPreserved":true,"replacementPreservedAfterExit":true}}`. Failure is `{"status":"LINUX_BRIDGE_FAIL"}` with exit1. No raw frame, answer, dynamic path, assertion message, stack or native error is emitted. Successful acceptance requires both all fixed true checks and clean process exit, not merely the printed object.

Actual socket checks cover passive apply and passive connection;0600 socket metadata; one explicit fake begin, notice, device-only choice and fake authorized result; rejection of a second connection without a second begin; disconnect abort of pending fake input; event-disposer and returned-disposer cleanup; pre-existing marker preservation; and replacement preservation through process exit.

For the last check only, the script starts its own exact fixture via `process.execPath`, with the same root and internal `--replacement-child` argument. The child inherits its launcher's identity and network namespace, receives an empty environment, ignores stdin/stderr, and has a5-second SIGKILL deadline. Its stdout is capped at128 bytes and must equal `REPLACEMENT_CHILD_DONE` plus newline; overflow kills only that child. The parent waits at most7 seconds. Before spawning, the parent creates the replacement marker exclusively and saves its device/inode. After successful natural child exit, the parent verifies the replacement's device/inode, owner,0600 mode and exact synthetic contents, and the retained original socket's presence. This checks automatic Node process-exit behavior without forcing a successful child exit.

All other asynchronous steps have2-second bounds. A25-second watchdog and sanitized uncaught-exception/unhandled-rejection handlers fail the fixture. The launcher's independent deadline and process-tree cleanup remain required if runtime handles prevent normal exit or a subprocess becomes unresponsive. The fixture deliberately reuses the bridge framing functions; existing parser-unit cases are not duplicated.

## Remaining release steps

Independent code and launcher review, exact bundle freeze, one parent-owned isolated Linux execution, and independent receipt review remain required. A Linux PASS proves synthetic transport only. It cannot prove real credential commitment, owner consent, effective credential-store selection, actual Cordis lifecycle, provider readiness, or pilot cutover readiness. No consumed prior gate is replayed by this offline implementation.

The implementation lane is frozen and relinquished to the parent for review.
