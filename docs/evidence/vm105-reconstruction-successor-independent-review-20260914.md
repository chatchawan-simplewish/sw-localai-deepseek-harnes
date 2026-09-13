# VM105 reconstruction successor independent review — 2026-09-14

## Verdict

**BLOCKED. Ready source-only: No.**

The frozen successor closes both prior Critical findings and the durable-attempt/UNKNOWN Important finding. It also rejects ordinary nonempty stderr. One Important fail-closed gap remains: a local stdout or stderr drain thread silently discards `OSError`, so the coordinator can accept a syntactically valid remote PASS/BLOCKED receipt without proving that both streams were drained to EOF. The contract's claim that both pipes are drained is therefore stronger than the implementation.

Current finding count: **Critical 0, Important 1**.

This is a source-only review. It authorizes no bundle delivery, SSH, `sudo`, reconstruction, staging, cleanup, retry, credential access, socket activity, systemd activity, DSH process launch, provider request, profile/default change, or other live action.

## Frozen review boundary

- Repository: `https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git`
- Reviewed commit: `c9863e52c0377d29e2cd1ad769117bc5a7bb112f`
- Reviewed parent: `11d073a3d9a4fe02a0728d577d7c435d1560217b`
- Inspection method: committed Git blobs and an isolated `git archive` only. Mutable launcher, test, and contract files were not read.
- `scripts/Invoke-VM105ProductionLauncher.py`: Git blob `32bcbf34e1f418e6bd941b5bbaba9d8ac08ce65d`; raw SHA-256 `05c78b6a14405cf8a42b1625b905ff0627c9a5429503add6f64ec47fa0bc4bf7`; 70,278 bytes.
- `scripts/test_vm105_production_launcher.py`: Git blob `aff7f2a43677b3aec2cc901ff404705e089a0a35`; raw SHA-256 `5d2c6cbd9b9693b9cae59b880b7a296316c554b2340679e7d6748f042f63d560`; 73,140 bytes.
- `docs/contracts/vm105-reconstruction-only-successor-contract-20260914.md`: Git blob `549f4b2d1274ff7135edefdf57794da589df5ab8`; raw SHA-256 `330088551489850d79811446dab4e646a966ed04eca881c74a293c9432e9844e`; 10,620 bytes.
- `git diff --check 11d073a3d9a4fe02a0728d577d7c435d1560217b..c9863e52c0377d29e2cd1ad769117bc5a7bb112f`: PASS.

The authenticated remote bootstrap is exactly 2,072 ASCII bytes and independently hashes to `cb0281b3a3816d355a6e114f11f55776ed1f3ca6a95be3e4874d4b4b613dd171`. The complete constructed remote shell command is exactly 2,949 ASCII bytes and independently hashes to `a74def12763e5fe5e80086ef9b5759e75aa8af49f5c6bb27cb3f6d8dcd886795`. Both values match the frozen contract.

## Prior finding dispositions

### C1 — privileged execution preceded launcher authentication: addressed

The bootstrap no longer asks privileged Python to execute the launcher pathname directly. It opens the one fixed path with `O_NOFOLLOW`, caps it at 128 KiB, requires a stable path/descriptor identity, requires a regular root-owned, group-owned file with exact mode `0440`, verifies the exact raw SHA-256, and only then compiles and executes the held bytes. The frozen bundle directory is separately required to be root:root with exact mode `0550`. This creates the required trust-before-execution boundary for the immutable launcher bytes.

### C2 — local SSH timeout did not establish a bounded remote process lifetime: addressed

The authenticated bootstrap ignores SIGHUP, creates a new session, forks the reconstructed launcher into its own process group, and supervises it independently of the SSH client. Its bounded sequence is 575 seconds, process-group TERM, five seconds, process-group KILL, then a further bounded reap. The child explicitly flushes stdout and stderr before `_exit` (`scripts/Invoke-VM105ProductionLauncher.py` immutable lines 128-161, including the flush at line 141).

The local boundary separately kills and waits for the SSH process, joins its drain workers, closes stdout and stderr, and performs final bounded joins (`scripts/Invoke-VM105ProductionLauncher.py` immutable lines 1474-1505). A timeout or inability to reap becomes sanitized UNKNOWN; it cannot become PASS/BLOCKED. The remote state remains UNPROVEN unless an authenticated terminal receipt passes validation.

### I1 — stderr evidence was ignored: partially addressed; remains open

Ordinary nonempty stderr is now rejected and converted to sanitized UNKNOWN. However, the drain worker catches `OSError` and silently continues as if EOF had been proven (`scripts/Invoke-VM105ProductionLauncher.py` immutable lines 1454-1463). The caller then returns the captured byte arrays when the process exits and the threads finish (`lines 1490-1497`). A stderr read can therefore fail before EOF while its captured buffer remains empty, allowing a valid stdout receipt and matching exit code to be accepted. A stdout read can similarly return a complete-looking receipt and then fail on the next read.

Minimum remediation:

1. Record every stdout/stderr drain exception in shared state; retain no exception text.
2. After process wait, bounded joins, and stream closure, fail with a fixed sanitized reason such as `LOCAL_SSH_DRAIN_FAILED` whenever either stream read failed.
3. Route that failure through the existing signed UNKNOWN terminal-record path with `remoteState=UNPROVEN` and `retryAuthorized=false`.
4. Add regressions whose fake pipe raises `OSError` immediately and after returning a valid-looking receipt. Neither case may yield accepted PASS/BLOCKED.

The contract says every local stop "drains and closes both pipes" and accepts a terminal receipt only under that boundary (contract line 33). Until the error path above is fail-closed, that statement has source/docs drift.

### I2 — pre-receipt failures lacked durable UNKNOWN/no-retry evidence: addressed

Before SSH, the coordinator reserves the exact attempt marker with `O_CREAT|O_EXCL`, canonical JSON, self-hash, `remoteState=UNPROVEN`, and `retryAuthorized=false`. Terminal publication also uses `O_CREAT|O_EXCL`. Transport start failure, timeout, output overflow, unexpected exit, malformed output, and nonempty stderr produce a canonical signed UNKNOWN record containing bounded scalar metadata; stderr content is never retained. If terminal publication itself fails, the attempt marker remains durable and the one-shot is still spent.

The pre-stage remote result mapping is strict. PASS requires `stagingPrecheck=ABSENT`, positive file and directory counts, exactly 2,029 links, the exact sealed-entry sum, and `RETAINED_EXACT_ROOT`. BLOCKED accepts only fixed uppercase source reasons, requires zero returned counts, and requires the exact staging/cleanup combination allowed for that reason. Transport uncertainty does not masquerade as a remote BLOCKED result; it is local UNKNOWN with remote state UNPROVEN.

## New Important finding

### I3 — stream read failure can be mistaken for a clean stream

This is the remaining I1 completeness gap described above and is counted once. Severity is Important because the signed local terminal record may assert PASS/BLOCKED after the evidence channel suffered a local read error. The remote operation remains bounded by the independent watchdog, so this does not reopen C2, but the evidence classification is not fail-closed.

## Frozen bundle-delivery and privilege prerequisites

The contract fixes one bundle root, `/var/tmp/omniroute-dsh-reconstruction-input-20260914`, and exactly five root:root non-link files:

| Bundle entry | Required raw SHA-256 |
|---|---|
| `Invoke-VM105ProductionLauncher.py` | `05c78b6a14405cf8a42b1625b905ff0627c9a5429503add6f64ec47fa0bc4bf7` |
| `Build-VM105FinalClientManifest.py` | `371481bef5595705df486c7a55251241a4c7a57c53ff8adf4a65a5fe8780a6ea` |
| `Capture-VM105DshTopology.py` | `aa2ca52f0460279d4fd76314be96610bfd87b1bf3e6b2c92e5446983468b6190` |
| accepted manifest raw receipt | `54d117ae18a83961012738500dbb27994ed0e7c9d6f176bf6547184d3a54f3f5` |
| accepted topology raw receipt | `86882398a06921bd351c84dbfc1eecc9abeb963912df41499ee21462b50cb47f` |

The delivery plan remains concrete and fail-closed: the final root and a fixed sibling temporary root must start absent; files use no-overwrite creation and exact bytes; each file is sealed root:root `0440`; the final directory is root:root `0550`; files and parent are fsynced; publication is one same-filesystem rename; failure retains the temporary root and grants neither cleanup nor retry.

The required independent bundle receipt is `docs/evidence/vm105-dsh-reconstruction-bundle-successor-20260914.json`. It must bind VM identity, stable root identity/mode/ownership, and the stable held-descriptor/path identity, type, ownership, mode, size, and hash of each of the five entries.

The sole contemplated privileged argv is exactly:

`/usr/bin/sudo -n /usr/bin/python3.12 -I -c <2,072-byte authenticated bootstrap> 05c78b6a14405cf8a42b1625b905ff0627c9a5429503add6f64ec47fa0bc4bf7`

The complete shell command is bound by SHA-256 `a74def12763e5fe5e80086ef9b5759e75aa8af49f5c6bb27cb3f6d8dcd886795`. A separate read-only policy proof must establish passwordless permission for precisely that argv. Broader Python, shell, wildcard, alternate-path, or alternate-argument permission is outside the contract.

At the reviewed commit, the bundle receipt, local attempt marker, and local terminal record are absent from the Git tree. Their absence is required at this source-only stage and means dispatch remains blocked. No delivery, policy check, or live execution was performed during this review.

## Validation performed

The committed tree was extracted to a temporary directory using `git archive`. From that immutable archive:

- `python -B -m unittest scripts/test_vm105_production_launcher.py`: **33/33 PASS** in 0.059 seconds.
- The focused tests exercise launcher-byte authentication before execution, exact file/directory modes, watchdog TERM/KILL/reap, child flushing, local timeout/reap/drain/close, stderr rejection, strict BLOCKED validation, durable attempt reservation, signed UNKNOWN output, occupied-record refusal, and terminal-publication failure.
- No test makes stream `read()` raise `OSError`; the remaining finding is therefore not covered by the passing suite.

These are mocked/local source tests. They do not prove Linux file semantics, remote Python behavior, SSH termination behavior, sudo policy, watchdog scheduling, signal/process-group behavior, bundle delivery, topology reconstruction, staging seals, DSH startup, namespace/cgroup containment, socket handoff, credentials, provider traffic, exact-two-request canary acceptance, ordinary sessions, tools, durable ACK behavior, persistence, profile/default selection, no replay, or production behavior.

## Authority and acceptance limits

The contract remains explicitly DORMANT and NOT AUTHORIZED. Its exact-two-request canary statement remains separate and correctly narrow: chat followed by its durable ACK, with `deniedRequests=0`; an extra-request denial is fixture evidence only. Reconstruction would prove neither that canary nor ordinary post-default multi-turn/tool/persistence/durable-ACK/profile/provider/no-replay acceptance.

The source may be reconsidered after I3 is fixed in a new immutable commit and the focused regressions pass. Even then, source-only readiness would not supply the absent bundle-delivery receipt, exact sudo-policy proof, attempt reservation, reconstruction terminal evidence, or any live acceptance authority.
