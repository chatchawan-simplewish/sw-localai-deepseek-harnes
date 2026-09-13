# VM105 reconstruction final independent review — 2026-09-14

## Final verdict

**PASS. Ready source-only: Yes.**

Critical findings: **0**. Important findings: **0**.

The frozen reconstruction source closes C1, C2, I1, and I2 from the prior independent review. This verdict covers dormant source correctness only. Bundle delivery, SSH, `sudo`, reconstruction, staging, cleanup, retry, credentials, sockets, systemd, DSH process launch, provider access, profile/default changes, and all other live actions remain unauthorized and unproven.

## Immutable review boundary

- Repository: `https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git`
- Reviewed commit: `638907f77bb73727f4a54addb23b46ee02cb11fc`
- Reviewed parent and final-diff base: `981914cd9f8e21821fea306db640924b82dddff0`
- Inspection method: committed Git blobs and a temporary `git archive`; mutable source, test, and contract files were not read.
- `scripts/Invoke-VM105ProductionLauncher.py`: Git blob `56157a4f04b4061332958cd7bee6815f99d173fb`; 70,429 bytes; raw SHA-256 `f2011f4d81831e4fb102f2f9e9755690418387e2f697e5ca3044417de5767c6d`.
- `scripts/test_vm105_production_launcher.py`: Git blob `3330392fbe4976ebfe684f1424a40285bbb16858`; 75,878 bytes; raw SHA-256 `50438748a38d79495e293050b05afc447e20ff11bbef964749a324035f9974af`.
- `docs/contracts/vm105-reconstruction-only-successor-contract-20260914.md`: Git blob `d811761f7d961cf59329985917018fe7708539e8`; 10,649 bytes; raw SHA-256 `549b7c911f95376bb5cdca893e0876f43634c7cb66ba65c76c58ef2e3b79d0db`.
- `git diff --check 981914cd9f8e21821fea306db640924b82dddff0..638907f77bb73727f4a54addb23b46ee02cb11fc`: PASS.

The expected blob fingerprints supplied for this review all match the immutable bytes.

## Final drain-error disposition

The local bounded SSH reader now uses a `threading.Event` shared by the stdout and stderr drain workers. Either worker sets the event if `read()` raises `OSError` (`scripts/Invoke-VM105ProductionLauncher.py`, immutable lines 1453-1464). After the SSH process has been waited and both workers have been joined, the caller checks that event before returning any captured bytes and raises the fixed sanitized reason `LOCAL_SSH_DRAIN_FAILED` (`lines 1485-1500`). The `finally` block closes both pipes and performs bounded final joins (`lines 1501-1508`).

Because `_run_bounded_reconstruction_ssh` raises before returning its tuple, `_coordinate_reconstruction_attempt` cannot pass incomplete bytes to `_classify_reconstruction_terminal`. It catches the fixed `ReconstructionUnknown` reason and publishes the existing canonical, self-hashed UNKNOWN terminal record with `remoteState=UNPROVEN` and `retryAuthorized=false` (`lines 1403-1437`). No exception text or stderr content enters the evidence.

The regression covers four cases: immediate stdout failure, stdout failure after a valid PASS frame, stdout failure after a valid BLOCKED frame, and stderr failure after a valid PASS frame. Every case produces signed `UNKNOWN` with reason `LOCAL_SSH_DRAIN_FAILED` and remote state `UNPROVEN`. Thus valid-looking bytes cannot override a local evidence-channel failure.

The local process lifecycle remains bounded. Timeout and output-limit paths kill and wait for the SSH process; inability to reap becomes `LOCAL_SSH_REAP_UNPROVEN`. Drain workers are joined, both streams are closed, and final joins are bounded. For a drain failure after normal process exit, the preceding successful `wait()` has already reaped SSH before UNKNOWN is raised.

## Prior finding dispositions

- **C1 — privileged launcher execution before authentication: closed.** The remote bootstrap opens the exact launcher path with `O_NOFOLLOW`, enforces a 128 KiB limit, verifies stable path/descriptor identity, regular type, root:root ownership, exact `0440` mode, and the exact launcher SHA-256 before compiling the held bytes.
- **C2 — remote process could outlive local SSH timeout indefinitely: closed.** The SIGHUP-independent bootstrap creates a new session, forks the authenticated launcher into its own process group, flushes child stdout/stderr before `_exit`, and independently supervises 575 seconds followed by TERM, five seconds, KILL, and a bounded reap.
- **I1 — stderr or drain failure could be accepted: closed.** Nonempty stderr is rejected. Either stdout or stderr read failure now produces signed sanitized UNKNOWN, including failure after complete-looking PASS/BLOCKED bytes.
- **I2 — uncertain pre-receipt failures lacked durable no-retry evidence: closed.** The exact attempt marker is reserved with `O_CREAT|O_EXCL` before transport. It is canonical, self-hashed, `remoteState=UNPROVEN`, and `retryAuthorized=false`. Transport uncertainty produces an equally bounded signed UNKNOWN terminal record; failed terminal publication leaves the spent marker durable.

Strict remote receipt classification is unchanged. PASS requires the exact canonical framing, self-hash and pins, empty stderr, matching exit code, `stagingPrecheck=ABSENT`, positive file/directory counts, exactly 2,029 links, the exact sealed-entry sum, and `RETAINED_EXACT_ROOT`. BLOCKED permits only the fixed uppercase source reasons, zero counts, and the exact staging/cleanup combination for that reason. Uncertain transport state cannot be labeled proven BLOCKED.

## Frozen bundle and command fingerprints

The contract and launcher consistently bind `/var/tmp/omniroute-dsh-reconstruction-input-20260914` and exactly five root:root, regular, non-link files:

| Entry | Required raw SHA-256 |
|---|---|
| `Invoke-VM105ProductionLauncher.py` | `f2011f4d81831e4fb102f2f9e9755690418387e2f697e5ca3044417de5767c6d` |
| `Build-VM105FinalClientManifest.py` | `371481fe62d6611913f82f65b6e26b12512fda8a853a2f4591b6314f580c885f` |
| `Capture-VM105DshTopology.py` | `aa2ca52f0460279d4fd76314be96610bfd87b1bf3e6b2c92e5446983468b6190` |
| `vm105-final-client-runtime-manifest-20260913.json` | `54d117c638335edeefe43aaef0f181ea5317f7938a6861a145871a0d9e45e8dd` |
| `vm105-dsh-topology-capture-successor-20260913.json` | `86882398a06921bd351c84dbfc1eecc9abeb963912df41499ee21462b50cb47f` |

The manifest canonical hash remains `4331e0e5fd9ac6f5e881a0dae941f9f07dea7b69969ee8b610071ce14cb03f8b`; the accepted topology canonical self-hash remains `cc7ca73f74bd1e515416cbff65809531fff2c052d0f7e406b9cc2efdb4c1ab20`.

Each bundle file is verified through a held descriptor as root:root with exact mode `0440`; the bundle directory is root:root with exact mode `0550`. Stable identity and no-follow checks remain in place. The delivery plan still requires an absent final root and fixed sibling temporary root, no-overwrite file creation, exact bytes, file and parent fsync, and one same-filesystem rename. Failure retains the temporary root and grants no cleanup or retry.

The authenticated remote bootstrap is exactly 2,072 ASCII bytes and independently hashes to `cb0281b3a3816d355a6e114f11f55776ed1f3ca6a95be3e4874d4b4b613dd171`. The complete remote command is exactly 2,949 ASCII bytes and independently hashes to `b2f1c14ee67933c33bea9dde2736e384389c926d84837be0820ef73d57ca8d48`.

The sole contemplated privileged argv remains:

`/usr/bin/sudo -n /usr/bin/python3.12 -I -c <2,072-byte authenticated bootstrap> f2011f4d81831e4fb102f2f9e9755690418387e2f697e5ca3044417de5767c6d`

A separate read-only sudo-policy proof must bind exactly that argv. Broader Python, shell, wildcard, alternate-path, or alternate-argument authority remains unacceptable.

## Validation performed

The immutable commit was extracted to a temporary directory with `git archive`.

- `python -B -m unittest scripts/test_vm105_production_launcher.py`: **34/34 PASS** in 0.083 seconds.
- The new drain regression passed all four immediate/post-frame stdout/stderr cases.
- The cumulative suite also covers launcher-byte authentication, exact bundle modes, watchdog TERM/KILL/reap, child flush, local timeout/reap/join/close, nonempty stderr rejection, strict BLOCKED mapping, attempt reservation, signed UNKNOWN evidence, occupied-record refusal, and terminal-publication failure.

These are local mocked tests. They do not prove Linux descriptor semantics, remote Python, SSH termination, sudo policy, signal/process-group scheduling, bundle delivery, reconstruction, staging, topology seals, DSH startup, namespace/cgroup behavior, socket handoff, credentials, gateway/provider traffic, production canary results, ordinary sessions, tools, durable ACK behavior, persistence, profile/default selection, or no replay.

## Prerequisites and authority limits

The following required evidence paths are absent from the reviewed commit:

- `docs/evidence/vm105-dsh-reconstruction-bundle-successor-20260914.json`
- `docs/evidence/vm105-dsh-reconstruction-successor-attempt-20260914.json`
- `docs/evidence/vm105-dsh-reconstruction-successor-20260914.json`

Their absence is correct for this dormant source-only packet and keeps reconstruction dispatch blocked. A future action still requires separately reviewed bundle delivery, the independent bundle receipt, exact sudo-policy proof, fresh authorization, the absent attempt and terminal leaves, and the contract's one-shot/no-retry handling.

The production canary remains exactly two accepted requests—chat followed by its durable ACK—with `deniedRequests=0`. Additional-request denial remains fixture evidence only. Reconstruction would prove neither that canary nor ordinary post-default multi-turn, tool lifecycle, durable ordinary-session ACKs, persistence, profile selection, provider generation, or no-automatic-replay behavior.

**Ready to publish or merge as dormant source-only material: Yes. Ready for reconstruction or any live action: No.**
