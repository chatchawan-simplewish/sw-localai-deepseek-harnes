# VM105 cutover independent spec and quality review

20260909 040623 Asia/Bangkok. Reviewer: `/root/cutover_code_review`.

Review - 02/02: spec review complete; quality review complete. These are review activities, not roadmap acceptance counts.

Project: DeepSeek Harness. Authoritative worktree: `C:/Users/chatc/Projects/sw-localai-deepseek-harnes/.worktrees/vm105-authoritative-roadmap`. Repository URL freshly read from origin: `https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git`.

## Verdicts

- **Spec verdict: CHANGES REQUIRED.** Final-stage EOF/extra-message handling does not meet the amendment's fail-closed protocol and post-stop parent-loss requirements. Known dependency failures also lose their exact safe discrepancy codes.
- **Quality verdict: CHANGES REQUIRED.** One P1 and one P2 finding below. The frozen implementation must not be released on this review.
- **Native runtime verdict: NOT PROVEN.** This was an offline source review, not Linux/systemd, service, SSH, authentication, or cutover acceptance.

## Reviewed scope and exact bytes

Read root `AGENTS.md`, the Task 1 brief in `docs/evidence/vm105-continuation-implementation-2026-09-09.md`, the September 9 post-smoke amendment, the September 8 packet's unamended restrictions, and `.superpowers/sdd/cutover-execution/review-package.md`. Traced the execution entry, shared state machine, native controls, bootstrap, parent protocol, test callers, and reused smoke verifier source/property/process/inventory helpers. Reviewed the retained base-contract receipt.

Freshly checked working-file SHA256 values match the requested frozen review:

| File | SHA256 |
| --- | --- |
| `scripts/Invoke-VM105CandidateCutover.py` | `16d75bdc52ad9cf9b7b6386a29c8bfde82a95e55f86f7c2cc24a661f4a0b1391` |
| `scripts/test_vm105_candidate_cutover.py` | `fc02089df9c139443d23e5558255c507283af6f50d4afb7a4d8b015024afeed1` |

No reported tests were rerun. The implementer's 18 passing fixtures and self-test are reported evidence, not independent execution evidence from this reviewer. No implementation changes, commits, live SSH, VM controls, authentication, or browser actions were performed. This report is the only owned write.

## Findings

### P1 — Check final-stage channel state before accepting the switch

Location: `scripts/Invoke-VM105CandidateCutover.py:101-105`; related `581-585`, `705-710`.

The remote reads exactly one response line at the CANDIDATE gate, then performs `verify_candidate()` and emits `SWITCH_ACCEPTED`. Its only pending-input/EOF check runs before sending a gate. No later gate occurs on success. Therefore a valid CANDIDATE response followed by another queued frame is accepted, and stdin EOF occurring during the final verification is never examined. A concrete normal parent-loss path is KeyboardInterrupt during that verification: the parent's exception handler closes stdin but deliberately retains SSH/stdout to allow restoration; the remote can still write its accepted receipt successfully and leave the provider-less candidate running while the parent returns BLOCKED / RESTORATION_NOT_PROVEN. This occurs before the documented accepted-receipt boundary and is not the acknowledged post-acceptance host-loss limitation.

Required correction: verify the expected protocol channel state at the final acceptance boundary, rejecting already-queued extra input and EOF through the existing single rollback path. Apply the corresponding final check before claiming ROLLED_BACK so fresh parent proof is not accepted after detectable parent loss. Keep VM restoration independent of stdout delivery. Add bounded offline regressions for a valid final reply followed by an extra frame and for stdin EOF during final verification, including the parent's close-stdin/keep-stdout behavior. Existing tests cover gate-time EOF and malformed lines, but not these late states.

### P2 — Preserve allowlisted failure codes from the frozen verifier

Location: `scripts/Invoke-VM105CandidateCutover.py:53-56`; related `293`, `471-487`, `764-765`.

`safe_error` recognizes only this helper's `Blocked` class. The smoke verifier is executed into its own module and has a distinct `Blocked` class. Consequently, known safe failures raised by reused operations, such as `COMMAND_TIMEOUT`, `CANDIDATE_PIN`, or `TRUST_METADATA_DRIFT`, become the generic `VERIFICATION_INCOMPLETE` in primary or rollback receipts. The preflight integration similarly replaces the retained result's existing sanitized error code with `FRESH_PREFLIGHT_FAILED`. The packet requires the exact sanitized discrepancy and separate primary/rollback errors; these paths prevent the parent from distinguishing a timeout from source or private-input drift.

Required correction: explicitly translate the frozen verifier's known exception type and an enumerated safe-code set at the integration boundary, preserving primary and rollback provenance. Carry through already-sanitized preflight failure codes where available. Do not broaden this into echoing arbitrary dependency exception strings. Add an offline check using the actual distinct verifier exception class and verify that arbitrary strings remain suppressed.

## Other reviewed boundaries

- The default path is nonmutating. Explicit execution checks owner readiness, the helper hash, Bell-PC2 identity, and frozen inputs before launching one strict SSH child. These assertions do not establish actual owner authority or release evidence.
- The owned-file algorithm records the exclusive inode and written prefix, uses held nofollow parents, rejects replacement/content/ownership/attribute/mount drift, and leaves the directory and both profiles intact. Fixtures simulate these boundaries; native filesystem and signal-mask behavior remain unproven.
- Controls submit once without blocking in systemctl and poll Job with a 95-second bound for the base's 90-second jobs. Rollback waits for outstanding jobs before further control. Main and rollback timers are distinct, and the parent retains a combined transport budget. These bounds are visible in source; real systemd property output and job behavior are not accepted here.
- Acceptance requires unchanged candidate invocation/restart identity. Rollback permits a later candidate only through full source/process/cgroup proof, applicable restart/start lineage, and an immediate second capture; the start-error-before-first-capture path is explicitly restricted to proven candidate composition.
- Base-plus-owned-drop-in checks preserve the pinned base settings. Missing EnvironmentFiles and Sockets receive separate source-proof markers, emitted values must be empty, TriggeredBy is empty, and the same-stem socket must remain not-found.
- Candidate API probing reuses the frozen two-request probe with only port 3081 changed to 3080. Root HTTP, listener ownership, UFW equality, tunnel identity and LAN denial are checked. Graph/source/root/input/private-inventory verification retains the reused verifier's bounds and restores descriptor limits. These are implementation observations, not live acceptance claims.
- Primary and rollback fields are separate, and post-stop exceptions, receipt write failures and supported signals enter one guarded rollback in the reviewed state machine. Finding P1 limits the completeness of the parent-loss and protocol claims.

## Next acceptance step and limits

Parent should obtain the two bounded corrections, freeze replacement hashes, run the new regressions and appropriate existing checks, and request fresh independent review of the changed boundaries. Keep the pilot preserved pending actual owner readiness and completed release evidence. Native runtime, credential entry, OAuth, provider routes, inference, and full-v1 acceptance remain NOT PROVEN. Available choices remain the read-only default, explicit read-only preflight, and a later separately released execution; this report authorizes none of the live actions.

## Scoped correction review — round 1

20260909 041628 Asia/Bangkok. Reviewed only `.superpowers/sdd/cutover-execution/fix-round-1.md`, its two corrected boundaries and possible breakage introduced by them, plus the appended implementation evidence. Fresh file hashes match helper `2f0aaf554235fb5880247dc0a4df72a387c37b6ceff270537b567fee7a4816a6` and test `d6ddbe1bfb23a8a64032cd8f050fcdaa2fdf4e8cac17294b01bfc0e84cd6822b`. Parent reports independent 21/21 tests and self-test PASS. This reviewer did not rerun checks or perform live actions.

- **P1: CLOSED for the reviewed offline implementation.** `run_cutover` now checks channel state after final candidate verification and after final restoration verification, before declaring success (updated helper lines 112 and 126). `channel_clear` rejects pending input or EOF. New socketpair regressions cover queued duplicate replies and parent stdin half-close during both final verifications while stdout remains available. The correction addresses the observable late channel states in the original finding; it does not claim atomic cross-host acceptance or guarantee recovery after the acknowledged host-loss boundary.
- **P2: PARTIALLY CORRECTED; remains open.** Exact frozen verifier exception provenance and code allowlisting are now present, and arbitrary strings/extra exception arguments remain suppressed. However, the newly accepted diagnostic-code set is incompatible with the unchanged receipt code grammar, as detailed below.
- **Current spec verdict: CHANGES REQUIRED. Current quality verdict: CHANGES REQUIRED.** No P1 remains in this scoped review; one P2 correction remains. Native runtime is still NOT PROVEN.

### Remaining P2 — Accept the enumerated diagnostic-code grammar end to end

Locations in updated helper: `scripts/Invoke-VM105CandidateCutover.py:63`, `717`, and `937`. Source evidence: `scripts/Test-VM105CandidateSmoke.py:683` raises `CGROUP_V2_REQUIRED`, which is expressly included in the frozen `DIAGNOSTIC_CODES` at line 1066.

The correction now allows this exact safe code from the actual verifier class, but the local `Blocked` sanitizer and both parent receipt parsers still require `[A-Z_]{1,64}`. The digit in `CGROUP_V2_REQUIRED` therefore fails later validation. On a native post-stop process/cgroup verification failure, the remote can now preserve and emit that exact code, yet the parent rejects its receipt and substitutes `REMOTE_RECEIPT` with `RESTORATION_NOT_PROVEN`, losing the actual primary/rollback evidence. When preflight translates the same known code into the helper's own `Blocked`, `safe_error` instead collapses it to `VERIFICATION_INCOMPLETE`. The explicit read-only preflight parser similarly rejects the otherwise sanitized known code.

Align the finite diagnostic-code acceptance with the sanitizer and both receipt consumers, preserving the provenance/allowlist guards already added. Add one bounded regression taking an actual enumerated code containing a digit through native translation and parent receipt acceptance. This is a gap in the P2 correction, not a request to broaden raw exception output or alter runtime authority.

## Scoped correction review — round 2, final offline verdict

20260909 042129 Asia/Bangkok. Reviewed only `.superpowers/sdd/cutover-execution/fix-round-2.md`, the remaining numeric diagnostic-code transport correction, its regression, and possible new breakage in that correction. Fresh working-file hashes match helper `a1083a64b4c62771ae783075a523a8457de8ca9970754ecc1f524c14ddfead28` and test `5a0eeac0f9d8ba934f4ebaf481bc936b725764441deb5de438d252127761af2a`.

- **P2: CLOSED for the reviewed offline implementation.** The local helper exception sanitizer, execution receipt parser, and read-only preflight receipt parser now consistently accept the bounded `[A-Z0-9_]{1,64}` grammar. The actual frozen verifier exception type and enumerated-code check remain unchanged. The new regression takes the real hash-checked verifier's `CGROUP_V2_REQUIRED` through native preflight translation, execution primary/rollback receipt fields with checked exit, and the read-only preflight receipt. Arbitrary verifier exception strings are still governed by the exact type and enumerated-code restrictions reviewed in round 1.
- **P1 remains CLOSED.** Its channel-state checks were not changed by round 2.
- **Final spec verdict: ACCEPTED for the frozen offline implementation. Final quality verdict: ACCEPTED for the frozen offline implementation.** No actionable finding remains from the original review or the two scoped correction reviews. These final verdicts supersede the earlier CHANGES REQUIRED verdicts only for the exact round-2 hashes above; the historical findings are retained.

Parent reports independent 22/22 tests and self-test PASS. This reviewer inspected the new test and exact hashes but did not rerun tests, contact VM105, execute controls, or change implementation. Only this report was appended. Parent retains final evidence acceptance and publication ownership.

**Native runtime remains NOT PROVEN.** Offline review does not establish Linux filesystem/signal behavior, real systemd jobs and properties, SSH loss timing, live startup/rollback, owner readiness, credentials, OAuth, provider routes, inference, or full-v1 acceptance. No live execution or owner-readiness authority is supplied by this review. The safe default and separately gated future execution choices remain unchanged.
