# Linux synthetic bridge fixture independent review

20260909 043227 Asia/Bangkok. Repository: `https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git`. Worktree: `C:/Users/chatc/Projects/sw-localai-deepseek-harnes/.worktrees/vm105-authoritative-roadmap`.

Verdict: **ACCEPT — fixture only; not an execution release**. No blocking fixture finding. The launcher is outside this review and must independently establish containment before a single parent-owned run.

## Frozen scope

The fixture, implementation report, full owner module, and Linux verification plan were read. These SHA256 values were independently verified:

| Artifact | SHA256 |
| --- | --- |
| `scripts/test-native-codex-owner-linux.mjs` | `6f82e2f2783123255f9e441cde991da2bdcbddbf92bd9f4dc6cc7e1b12cc1414` |
| `docs/evidence/vm105-native-bridge-linux-fixture-report-2026-09-09.md` | `2476fca95e55759fb69b5f8a31b7e8212ff0b7a8672062e6117585d54e34b984` |
| `scripts/native-codex-owner.mjs` | `90bb452d25d5b6c7c7593e2cfc7c01650069d1d63f4770728bff5ef32935b14b` |

No tests, SSH, native execution, source edits, authentication, service controls, or fixture mutations were performed by this reviewer. Only this review report was created.

## Assessment

- Imports are Node standard library and the adjacent reviewed owner module. Authorization and credentials are synthetic local objects. Explicit fake `begin` is required and its key/method/signal are asserted. No Cordis, adapter, application profile, or real credential service loads.
- Assertions exercise real socket type/owner/0600 mode, passive application and connection, device-only prompt filtering, notice/answer/result transport, exactly one fake begin across a second connection, disconnect cancellation with an aborted signal, ordinary owned socket removal, pre-existing marker preservation, and replacement preservation after natural child exit.
- The fixture validates the supplied root through the owner module's real private-directory policy and refuses all six synthetic names before work. New markers use exclusive creation. Renames involve only the new test's socket and marker, with before/after marker inode/device checks. No recursive deletion occurs. Fresh root identity and isolation from unrelated same-user work remain launcher obligations.
- Failure paths suppress raw errors and emit a fixed code. Success uses fixed check names and booleans. Child stdout has a 128-byte bound and must equal its fixed success marker; child stderr is ignored. No frame, answer, dynamic path, or assertion text is emitted.
- Individual awaits are bounded, the replacement child has a five-second SIGKILL timeout and seven-second parent wait, and the fixture has a 25-second failure watchdog. These do not substitute for the launcher's 30-second deadline and exact child-tree cleanup. Clean main and child process exit must accompany the complete success object.

## Limits retained for acceptance

The fake `ctx.on()` only stores a callback; this deliberately proves local bridge disposal behavior and cannot establish native Cordis lifecycle semantics. The retained partial Cordis source remains insufficient for that separate conclusion.

Socket absence and clean process exit establish the tested removal and process-liveness behavior. The fixture does not separately count or identify held directory descriptors after ordinary disposal; do not describe a PASS as independent proof that every directory descriptor closes before process exit. If that narrower resource claim is required, add an exact self-process descriptor assertion in a reviewed fixture revision.

The replacement case intentionally retains a harmless synthetic socket and marker. It tests process-exit cleanup of a replaced path, not resistance to malicious concurrent same-UID filesystem changes. The launcher's private fresh root, pinned bundle and executable, unprivileged identity, empty environment, isolated network namespace, bounded supervision, and retained evidence are still mandatory.

A later Linux PASS proves synthetic transport only. Owner consent, actual credential commitment/store selection, native Cordis activation, provider readiness, and pilot cutover remain outside this fixture's verdict.

## Composed launcher pre-execution review

20260909 043645 Asia/Bangkok. Verdict: **BLOCK** for launcher `66f2a4a5718a3a349ceeaa72ef6fb11d1301b0597c56dcfcd8785bc54958bd92`. The earlier fixture-only acceptance stands. No execution release is granted.

The full launcher and launcher report were read along with the complete terminal module. The unchanged imported inspector was previously read in full in this same review lane; its hash was reverified as `fcddc77c890b289e28c609fa30b3b41f6c060a73c5c4ea3ab69b468a130df424`. Launcher and terminal hashes were independently verified; terminal remains `9e9bf70f8c6e4088f66ac573ce2bf89a60971d30b4f9ea3000aface4af33b458`. The accepted owner and fixture remain the pinned inputs listed above. No live action or redundant test was performed.

### Blocking finding

**P1 — Held executable accepts set-ID mode, invalidating the unprivileged-child guarantee.** `remote()` opens Node through `Inspection.open()` and checks size and its byte hash. That inspector checks root ownership, non-writable group/other permissions, regular-file type, and forbidden capabilities/ACLs, but does not reject `S_ISUID` or `S_ISGID`. A root-owned Node inode with mode `04755` and the correct bytes passes all current checks. After the child drops to dsh, `execve(node_fd, ...)` can regain root effective identity from the setuid bit. Holding and hashing the executable inode does not prevent that mode-driven privilege transition.

Required narrow fix: reject setuid and setgid bits on the held Node descriptor before fork, keeping its existing metadata-drift checks (or validate an explicitly approved exact executable mode). Add the smallest offline rejection check that demonstrates a pinned executable with set-ID metadata cannot reach child launch. Freeze the changed launcher and submit the scoped correction for review before execution.

### Other reviewed boundaries

No additional substantive finding was identified in the composed scope. Exact bundle hashes are verified before SSH and remotely; the fixed fresh root is exclusively created and retained; source mutations stay within that root. The child creates its own session, waits for the parent gate, creates the network namespace before identity drop, clears supplementary groups, and supplies a fixed environment. Unsupported namespace/descriptor primitives fail closed.

The acknowledged child remains unreaped through group cleanup: `waitid(...WNOWAIT)` observes exit, then `killpg()` uses the reserved leader identity before `waitpid()`. Before acknowledgement, the unreaped direct child can only wait at the gate, so direct-child termination cannot strand a fixture descendant. The reviewed fixture's spawned child inherits the group and does not detach. The receipt proves direct-child reaping; it does not independently enumerate descendants, as the launcher report states.

Child capture is bounded to 4,096 bytes and must decode to the exact six-true-check schema. Raw child output and exceptions are suppressed on failure. Thirty-second child supervision, the remote 40-second alarm plus five-second cleanup reserve, and the 50-second local SSH wait are finite. The local invocation remains default-nonmutating and requires the exact reviewed launcher hash plus all pinned sources to enter its one-attempt execution path. These controls do not clear the set-ID finding above.

## Scoped correction review and release verdict

20260909 044024 Asia/Bangkok. Verdict: **ACCEPT for one parent-owned composed execution** of launcher `3fa388c3fbdb0ed48b368c63114a16940c87312ad661147aed062ca384ff688a` with its unchanged embedded bundle/inspector/Node pins and exact fresh root `/run/dsh-native-bridge-check-20260909-a1`.

The P1 set-ID finding is **ADDRESSED**. The shared guard rejects either setuid or setgid on the held Node descriptor immediately after its trusted open and before hashing, root creation or fork. The existing complete metadata snapshots and double-hash verification remain in place. The new smallest offline guard check accepts ordinary0755 and rejects04755/02755 with the fixed failure code. Parent reported a fresh SELF_TEST_PASS; this reviewer did not rerun it.

The new launcher hash was independently verified. Removing only the added guard, its single remote call, and its self-test statements reproduced the previously reviewed launcher hash `66f2a4a5718a3a349ceeaa72ef6fb11d1301b0597c56dcfcd8785bc54958bd92`, confirming no other executable change in this correction. The revised launcher report was read. No new substantive finding appears in the scoped correction; earlier fixture and containment limitations still apply.

Frozen invocation: run `scripts/Test-VM105NativeBridgeLinux.py --execute --reviewed-sha256 3fa388c3fbdb0ed48b368c63114a16940c87312ad661147aed062ca384ff688a` from the authoritative worktree using the local Python launcher. This acceptance covers one attempt only. An existing root, failure, timeout or incomplete receipt spends the attempt and requires diagnosis without automatic replay. Runtime PASS still requires parent verification and independent receipt review; it cannot authorize native Cordis/provider/authentication work or pilot cutover.

## Attempt a1 independent receipt assessment

20260909 044237 Asia/Bangkok. Verdict: **FAIL — Linux transport NOT PROVEN; attempt spent**.

Read-only review of `docs/evidence/vm105-native-bridge-linux-attempt-a1-2026-09-09.json`, SHA256 `0293025756a0de1769c62833d6c5c44fed6d4dfadd84f19e809f52c2b391456a`. Parent records the frozen accepted launcher hash and `attempt_consumed: true`. The receipt reports `LINUX_CHECK_FAIL`, `ssh_exit: 0`, `tool_exit: 0`, and `owned_child_reaped: true`. SSH/tool exit 0 means the wrapper returned its receipt; neither overrides the explicit failed test status.

The reported exact root is `/run/dsh-native-bridge-check-20260909-a1`, inode4078. Three expected source artifacts have inodes4080/4081/4082, reported0444 modes, and the accepted bundle hashes. The Node digest matches the accepted executable pin. These metadata fields are consistent with the launcher reaching fresh-root/source preparation before failure. They are retained execution evidence, not a new live filesystem inspection or an independent post-write content rehash.

The child-reaped flag confirms the wrapper completed its direct-child wait. The receipt does not record the failed stage, child's exit status/signal, whether network isolation and identity drop completed, whether group acknowledgement occurred, or which fixture checks ran. No six-true-check result exists. Therefore neither individual socket checks nor native Linux bridge compatibility can be accepted from this attempt. The exact cause cannot be inferred from the generic sanitized failure code.

The fresh root and harmless artifacts stay retained. The single execution gate is consumed; this assessment authorizes no retry, cleanup, readback, or additional live action. Offline diagnosis may establish a concrete implementation defect and a separately reviewed revision, but must preserve this failure verdict and require a new exact gate for any future attempt. Cordis lifecycle, authentication, effective store, provider requirements and pilot cutover remain unproven and unchanged.

This reviewer performed no SSH, test execution, live mutation or cleanup during receipt assessment; only this report was appended.

## Separate a1 metadata receipt assessment

20260909 045400 Asia/Bangkok. Reviewed `docs/evidence/vm105-native-bridge-linux-a1-metadata-2026-09-09.json`, SHA256 `bc8a50e5a825a1d21e0ca8abd2c4f445a4dec51b2042da24674b6933fcfc3298`. The parent reports its fresh self-test passed before the single approved metadata call. The receipt records **A1_METADATA_PASS / SSH0**; this means the bounded metadata inspection succeeded, not that the earlier transport test passed. Both one-attempt gates are now spent.

Directly recorded topology:

- Root inode4078 is dsh1000:1000/0700; src inode4079 is root0:0/0555. Source inodes4080/4081/4082 retain the expected root ownership,0444 modes and single links.
- `flow.sock` and `disconnect.sock` are absent.
- `preexisting.sock` remains a regular0600 dsh-owned file, inode4085, size22. Its contents were not read by this inspection.
- `replacement.fixture` and `replacement.sock` are absent.
- `retained.sock` remains a0600 dsh-owned socket, inode4087.

This narrows the defect substantially. In the frozen fixture's sequential control flow, creation of the pre-existing marker occurs after the owned-flow and disconnect checks. The replacement child is spawned only after the exclusive replacement marker is created, and `retained.sock` is created only by renaming the child's bound `replacement.sock`. Thus the observed topology supports progress through real socket binding and into the replacement case, assuming no out-of-scope concurrent filesystem changes. It is inconsistent with a failure confined to pre-Node namespace setup.

The absence of `replacement.fixture` supports its subsequent rename to `replacement.sock`, because the reviewed fixture has no other operation removing that marker. That latter path is also absent at inspection, so the required preservation outcome was not retained. The owner module's explicit conflict path only unrefs the server and does not itself unlink a regular replacement. These facts make Node/libuv handle retirement removing the original bind pathname the leading explanation.

**Timing and native cause remain inference.** The metadata does not observe either rename as it happens, recover the discarded child exit/marker output, identify the exact assertion that failed, or distinguish natural Node exit, garbage collection, or later wrapper-driven retirement as the unlink trigger. No native cleanup trace was captured. Do not label a specific Node exit-cleanup mechanism as independently proven from this topology alone.

The a1 result remains **FAIL**, with no provider or full Linux transport acceptance. Next implementation work should address and instrument the replacement-retirement boundary rather than broadly relaxing path-identity checks. Any fix and fresh-root verification need their own bounded review/release; preserve this failed root, both receipts and spent gates. No code change, live action, content read or replay was performed by this reviewer.
