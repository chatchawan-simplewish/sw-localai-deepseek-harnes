# VM105 bounded cutover implementation — offline review packet

Frozen 2026-09-09 03:59:27 Asia/Bangkok. Status: **OFFLINE IMPLEMENTED; INDEPENDENT REVIEW PENDING; LIVE EXECUTION NOT PROVEN.**

Project: DeepSeek Harness. Repository URL freshly verified with `git remote get-url origin`: `https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git`. Worktree: `C:/Users/chatc/Projects/sw-localai-deepseek-harnes/.worktrees/vm105-authoritative-roadmap`.

Authority is the Task 1 brief in `vm105-continuation-implementation-2026-09-09.md`, the September 9 post-smoke cutover amendment, and the unamended restrictions in the September 8 packet. This packet does not grant owner readiness, release the cutover, or advance full-v1 acceptance. The usable pilot must remain until the parent establishes the release conditions and separate owner readiness.

## Owned files and frozen bytes

| File | SHA256 of exact working-file bytes |
| --- | --- |
| `scripts/Invoke-VM105CandidateCutover.py` | `16d75bdc52ad9cf9b7b6386a29c8bfde82a95e55f86f7c2cc24a661f4a0b1391` |
| `scripts/test_vm105_candidate_cutover.py` | `fc02089df9c139443d23e5558255c507283af6f50d4afb7a4d8b015024afeed1` |

This report is the third owned file; its publishing commit pins it without a self-referential hash. Parent owns publication and any line-ending attributes. No commits were made by this agent. Other agents' files and dirty work were preserved.

The exact drop-in bytes/hash remain `498ffcd058b856e054e8b144292d1831b0a3f4c4004bb0ae6d94a6e21ee0ea0a`. Frozen smoke verifier and graph/base receipt pins were not changed. The helper's default invocation returns `CONTRACT_ONLY`; `--preflight` remains an explicitly requested read-only SSH path. `--apply` remains unsupported. A new `--execute` entry requires `--owner-ready` and `--reviewed-sha256` matching the actual helper bytes before a child can launch. Those arguments are assertions supplied under actual owner authority, not an authentication or approval service; none was supplied or used here.

## Requirement mapping

| Amendment requirement | Implemented boundary |
| --- | --- |
| Fresh exact pinned source, fallback graph, original inputs, source-derived root and post-smoke inventory before mutation | `NativeCutover.preflight` executes the existing read-only `REMOTE` verifier body and retains verified inputs; no consumed smoke apply entry is called. `inputs` checks the three exact frozen artifacts. |
| Exclusive file creation and safe cleanup after partial writes | `OwnedDrop` uses the exact destination, `O_EXCL`, `O_NOFOLLOW`, held descriptors, recorded device/inode/type/owner/mode/link count and exact written prefix. Failed writes/fsync can remove only the owned unchanged inode. Replacements/content/ACL/mount/parent drift block removal. No owned file means no deletion. |
| Exact directory and file modes | Newly created directory is 0755 even under a restrictive inherited umask; the process umask is restored. The exact root-owned file is finalized as 0644. Rollback leaves the directory and both profiles intact. |
| Partial-state bookkeeping survives HUP/TERM/INT/alarm boundaries | `file_boundary` defers those signals through exclusive creation, mkdir bookkeeping, chmod bookkeeping, write-prefix bookkeeping and unlink bookkeeping. Delivery after the critical section enters the guarded failure path. |
| Base plus sole owned drop-in source/activation proof | `sources`, `properties` and `composition` check exact base bytes, hardlink absence, owned payload, held trusted parents, mapping, no conflicting drop-ins, no envfile/socket directives, empty emitted activation properties and distinct source-proof markers for independently missing properties. The same-stem socket must remain not-found. |
| Preserved service settings, selector, argv and process ownership | Exact base receipt properties are compared. Effective ExecStart and process argv, UID/GID, cgroup membership, PID/start/InvocationID/NRestarts, loopback namespace and allowlisted environment are checked without emitting values. |
| One stop, one candidate start, one rollback | `run_cutover` is the shared tested state machine. Native stop-attempt bookkeeping is set only after two fresh pilot captures. Every later failure enters one rollback; no retry loop or repeat switch exists in one invocation. |
| Outstanding 90-second systemd jobs | Controls submit once with `--no-block`; `wait_job` polls the manager's Job property for at most 95 seconds. Rollback first waits for any existing job, submits no competing job, and never cancels a job or kills a PID. A failed reload permits only the exact old or candidate loaded composition, independently recaptured. |
| Bounded parent/remote gates | One strict SSH child receives a bounded, hashed helper/bootstrap bundle. Cryptographic nonce and exact single-use PREFLIGHT/CANDIDATE/ROLLBACK stages reject extra fields, duplicate JSON keys, replay, wrong nonce/stage, queued extra messages, EOF and timeouts. Parent external gate retains its 5/5/5-second probes and 20-second total; remote gate is 30 seconds. |
| Rollback reserve and signal/output failure | Remote main deadline is 480 seconds from runtime construction, with an independent 330-second rollback timer. Parent retains SSH through the 850-second overall budget, including rollback. HUP/TERM/INT/alarm and receipt write failures route through the state machine. VM restoration does not depend on stdout success; unavailable parent proof leaves restoration NOT PROVEN. |
| Restart lineage | Acceptance requires the first candidate identity and restart count to remain unchanged. Rollback may recapture a later candidate invocation only with the exact owned composition, selector/argv and cgroup proof, monotonic restart/start lineage where an initial capture exists, and a second unchanged capture immediately before control. Restart races and unrelated drift prevent control. |
| Candidate API acceptance | The frozen probe is reused with only the literal loopback port changed to 3080. It makes one exact `llm.providers` request and one exact `host.describe` request; retains five-second alarms, 64KiB cap, no proxy/redirect/retry, zero active adapters and dormant native default checks. Raw responses remain in the remote process and only the exact sanitized receipt is accepted. |
| Post-start closure/inventory verification | `evidence` reuses source pins, runtime pin, exact closure traversal, optional-peer rules, absent resolver ancestors, source-derived root and private metadata inventory policies; 512-package/4096-edge/30-second/1MiB verifier bounds remain. Verifier FD limit changes are restored. Generated private files are not read to infer semantics. |
| Old profile opacity and rollback restoration | Only the old-root lstat baseline is captured after stopping; subsequent lstat comparisons stop when rollback resumes pilot use. No old-profile child is opened/copied/migrated/deleted. Restoration rechecks old selector/argv, service composition, listener ownership, HTTP, unchanged firewall and fresh parent tunnel/LAN proof. |

## Exact offline verification

Host Python: `Python 3.12.10` on Windows. All subprocess/network boundaries in the execution tests are fixtures. No SSH, VM controls, browser, authentication, installation or live candidate execution occurred.

```
python -B scripts/test_vm105_candidate_cutover.py
..................
----------------------------------------------------------------------
Ran 18 tests in 0.260s

OK
```

```
python -B scripts/Invoke-VM105CandidateCutover.py --self-test
{"mutation_entry": "READ_ONLY_PREFLIGHT", "status": "SELF_TEST_PASS"}
```

Default invocation is exercised by the new test file as a real subprocess and returns `CONTRACT_ONLY`, exit 0. The explicit entry without readiness was also invoked locally and returned `BLOCKED` / `OWNER_READINESS_REQUIRED` before any SSH child creation. Input-pinning, existing listener/environment/tunnel guards and compiled read-only remote/probe code remain covered by the existing self-test. The new file also compiles the bootstrap.

`git diff --check -- scripts/Invoke-VM105CandidateCutover.py` returned exit 0 with no whitespace findings. Final exact-file hashes above were read using `Get-FileHash -Algorithm SHA256`.

Test-first evidence: the first run failed on the missing execution engine and nonce protocol; the next guarded-native tranche failed on missing outstanding-job, restart-lineage and partial-file guards; the explicit-entry tranche failed until the readiness/hash entry existed. Later regression fixtures exercise the actual orchestration, parent wire parser, native recapture and owned-file algorithm at simulated OS/service boundaries.

The 18 checks cover successful switching; each main mutation failure; preflight versus post-stop parent loss; primary/rollback failure separation; output failure; HUP/TERM/alarm; exact nonce/schema/stage/replay rejection; reader timeout/EOF/size; 90-second job waiting and timeout; acceptance versus rollback restart lineage; recapture races before pilot stop and rollback stop; owned partial writes/fsync failures/replacements; newly created directory mode and preservation; independent activation-property source markers; no-argument behavior; readiness/hash rejection; and parent receipt/SSH-exit/extra-output sanitization.

## Limits and next acceptance step

- **Linux kernel/systemd behavior is NOT PROVEN.** Windows fixtures cannot prove Linux `openat`/nofollow/ACL/mount/umask/fsync semantics, signal-mask delivery, systemd Job serialization/property spelling, service startup, restart-counter behavior, or real SSH channel-loss timing. The native implementation exists, but offline passing checks are not VM runtime acceptance.
- Independent code review is pending. Parent should review these exact hashes, resolve findings and freeze replacement hashes if changed. Current code must not be released from this report alone.
- Main and rollback controls are bounded per invocation. No persistent attempt-marker file, watchdog, service, or automatic repeated switch was added. Re-execution after a failed/rolled-back attempt requires newly established authority; this report does not authorize it.
- Held trusted parents and repeated source/process captures are the guard against drift. They do not provide an atomic systemd compare-and-control transaction against concurrent privileged administrative changes; unexpected observations fail closed. SIGKILL, host loss, or loss after the accepted receipt boundary cannot guarantee automatic restoration.
- Actual owner readiness is absent. Pilot usability, tunnel candidate access, fresh credentials, native OAuth, usable provider routes, inference and full-v1 acceptance remain separate and NOT PROVEN. The future execution result can at most reach `SWITCH_ACCEPTED` at `CREDENTIAL_GATE`; it does not authorize credential/provider work.

Routine implementation choices were applied unattended within the existing amendment. No architecture, public exposure, live-resource authority or credential scope was expanded. The switchable choices remain read-only default, explicit read-only preflight, or a later separately released execution with fresh owner readiness.

## Independent review corrections — round 1/5

Frozen 2026-09-09 04:13:36 Asia/Bangkok. This revision supersedes the helper/test hashes above; the earlier evidence remains historical. Status: **BOTH FINDINGS CORRECTED OFFLINE; FRESH INDEPENDENT REVIEW PENDING.** Reviewed findings are preserved in the parent-owned `vm105-cutover-independent-review-2026-09-09.md`, which this agent did not edit.

| Current file | SHA256 of exact working-file bytes |
| --- | --- |
| `scripts/Invoke-VM105CandidateCutover.py` | `2f0aaf554235fb5880247dc0a4df72a387c37b6ceff270537b567fee7a4816a6` |
| `scripts/test_vm105_candidate_cutover.py` | `d6ddbe1bfb23a8a64032cd8f050fcdaa2fdf4e8cac17294b01bfc0e84cd6822b` |

- **P1:** The shared state machine now calls `channel_check()` after final candidate/restoration verification and before constructing either successful receipt. Native execution uses the same nonblocking `channel_clear()` predicate used before gates. Queued extra input or detectable EOF after the final valid reply enters the existing single rollback path; loss of parent proof after restoration yields BLOCKED rather than ROLLED_BACK. VM restoration remains independent of stdout delivery.
- **P2:** At the integration boundary, `safe_error` recognizes only the exact distinct `Blocked` class from the frozen verifier and only its enumerated `DIAGNOSTIC_CODES`. Primary and rollback provenance remain separate. The read-only remote preflight also translates that exact class, retains known diagnostic codes from its graph verifier, and passes through only enumerated preflight or frozen diagnostic codes to native execution. Unknown strings, extra exception arguments and unrelated exception classes stay suppressed. Frozen verifier bytes and receipt pins remain unchanged.

Test-first reproduction: before the P1 fix, four real-socketpair regressions incorrectly returned SWITCH_ACCEPTED or ROLLED_BACK for valid-final-reply-plus-extra-frame and parent stdin half-close during final verification. After the fix, all four return BLOCKED, perform exactly one VM rollback, and leave the independent stdout sink open without a success receipt. Before the P2 fix, the actual hash-checked frozen verifier's COMMAND_TIMEOUT became VERIFICATION_INCOMPLETE. The correction preserves COMMAND_TIMEOUT, CANDIDATE_PIN and TRUST_METADATA_DRIFT while rejecting arbitrary strings. An additional test executes the shipped preflight against the real frozen input bundle with a simulated subprocess timeout and proves COMMAND_TIMEOUT survives both preflight integration layers; no command reaches the host or VM.

Fresh exact checks:

```
python -B scripts/test_vm105_candidate_cutover.py
.....................
----------------------------------------------------------------------
Ran 21 tests in 0.419s

OK
```

```
python -B scripts/Invoke-VM105CandidateCutover.py --self-test
{"mutation_entry": "READ_ONLY_PREFLIGHT", "status": "SELF_TEST_PASS"}
```

`git diff --check -- scripts/Invoke-VM105CandidateCutover.py scripts/test_vm105_candidate_cutover.py` returned exit 0 with no findings. Current hashes were read with `Get-FileHash -Algorithm SHA256` after those checks.

Only the same three assigned files changed in this repair. No live SSH, controls, browser, credentials, installation or commit occurred. Native Linux/kernel/systemd semantics, cutover execution and owner readiness remain NOT PROVEN. Detectable late channel loss is now checked immediately before the receipt boundary; this does not claim an atomic transaction spanning two hosts or guarantee restoration after SIGKILL/host loss. Parent must independently review the new hashes before release.

## Independent review corrections — round 2/5

Frozen 2026-09-09 04:19:11 Asia/Bangkok. This revision supersedes the helper/test hashes in round 1. P1 was closed by the scoped reviewer and is unchanged in this round. The remaining P2 grammar correction is implemented; fresh independent acceptance is pending.

| Current file | SHA256 of exact working-file bytes |
| --- | --- |
| `scripts/Invoke-VM105CandidateCutover.py` | `a1083a64b4c62771ae783075a523a8457de8ca9970754ecc1f524c14ddfead28` |
| `scripts/test_vm105_candidate_cutover.py` | `5a0eeac0f9d8ba934f4ebaf481bc936b725764441deb5de438d252127761af2a` |

The change aligns exactly three existing code-format checks: the local sanitizer, the execution receipt parser and the explicit read-only preflight receipt parser now accept `[A-Z0-9_]{1,64}`. The exact frozen dependency exception class and its enumerated allowlist still control dependency-code translation; unknown dependency strings and extra arguments remain suppressed. No protocol stages, authority gates, controls or P1 behavior changed.

One regression uses the actual hash-checked frozen verifier's `CGROUP_V2_REQUIRED` code, translates it through native preflight, and sends it through both real parent parser functions with simulated transport. Execution preserves the code in both primary and rollback fields with checked SSH exit 1; read-only preflight preserves its error code with checked SSH exit 1. Before the fix, its three subcases reproduced VERIFICATION_INCOMPLETE, REMOTE_RECEIPT and REMOTE_RECEIPT respectively.

```
python -B scripts/test_vm105_candidate_cutover.py
......................
----------------------------------------------------------------------
Ran 22 tests in 0.324s

OK
```

```
python -B scripts/Invoke-VM105CandidateCutover.py --self-test
{"mutation_entry": "READ_ONLY_PREFLIGHT", "status": "SELF_TEST_PASS"}
```

`git diff --check -- scripts/Invoke-VM105CandidateCutover.py scripts/test_vm105_candidate_cutover.py` returned exit 0 with no findings. Hashes were captured after these checks. Only the same three assigned files were changed; no live action or commit occurred. Native runtime, cutover readiness and actual owner readiness remain NOT PROVEN. Parent owns the untouched independent review report and the next acceptance decision.
