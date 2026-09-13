# VM105 reconstruction source independent review — 2026-09-14

## Verdict

**BLOCKED**

- Ready for source-only publication: **No**
- Critical findings: **2**
- Important findings: **2**
- Live authority: **None**

The reconstruction source is dormant and its remote staging logic is narrowly scoped, but the exact wrapper is not safe to authorize. It executes the remote launcher as root before independently authenticating those bytes, and its local timeout/output-limit handling does not prove that the remote root process stopped. Transport failures can also consume the one-shot action without durable sanitized UNKNOWN evidence. No SSH, sudo, VM, reconstruction, staging, credential, socket, systemd, DSH, provider, profile, or default action is authorized by this review.

## Frozen review identity

- Repository: `https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git`
- Working repository: `C:\Users\chatc\Projects\sw-localai-deepseek-harnes\.worktrees\vm105-authoritative-roadmap`
- Reviewed commit: `0fbef6bab42d100f8f8d221c4ffae80adaecfb5e`
- Parent: `4cdd08809d1d68098f7d23b7f62832c800197f1f`
- Review method: immutable Git object data obtained with `git show`, `git diff`, `git cat-file`, and `git archive`; mutable worktree source/test/contract files were not read as review inputs

| Frozen blob | Git blob | Raw SHA-256 | Bytes |
|---|---|---|---:|
| `scripts/Invoke-VM105ProductionLauncher.py` | `b04c24c419d702269fae4171d86a34c4c0c4b494` | `9cd4fb3c4364a3471e37971345cc00ccf65bff70db930f890e101bbf48795e4d` | 58,069 |
| `scripts/test_vm105_production_launcher.py` | `34692f92fc82efe1dacbdf48117e84ba11fdd515` | `95f563b0a8d1b3d920d43e7c0836ebe5a1785ac3a9c53b49f064f31517f8bbc2` | 61,273 |
| `docs/contracts/vm105-reconstruction-only-successor-contract-20260914.md` | `7a7d1becf229d2247c817afc0ae94f8491b2144b` | `46fe4c40a3e198736ff646f6d8788c746de61b8ce5b6d14269e9dcc1284bd201` | 9,550 |

The contract's launcher pin matches the frozen launcher blob. Its fixed bundle also pins builder `371481fe62d6611913f82f65b6e26b12512fda8a853a2f4591b6314f580c885f`, topology helper `aa2ca52f0460279d4fd76314be96610bfd87b1bf3e6b2c92e5446983468b6190`, manifest raw bytes `54d117c638335edeefe43aaef0f181ea5317f7938a6861a145871a0d9e45e8dd`, manifest canonical content `4331e0e5fd9ac6f5e881a0dae941f9f07dea7b69969ee8b610071ce14cb03f8b`, topology raw bytes `86882398a06921bd351c84dbfc1eecc9abeb963912df41499ee21462b50cb47f`, and topology self-hash `cc7ca73f74bd1e515416cbff65809531fff2c052d0f7e406b9cc2efdb4c1ab20`.

## Critical findings

### C1 — Remote launcher is trusted only after privileged execution begins

The exact wrapper invokes `/usr/bin/sudo -n /usr/bin/python3.12 -I /var/tmp/omniroute-dsh-reconstruction-input-20260914/Invoke-VM105ProductionLauncher.py ...` directly (`docs/contracts/vm105-reconstruction-only-successor-contract-20260914.md`, lines 50–55). Python must open, parse, and execute that remote file as root before its `reconstruction_entry` can verify the supplied launcher hash (`scripts/Invoke-VM105ProductionLauncher.py`, lines 1298–1310). The later bundle verification cannot protect this initial trust boundary. A remote launcher changed after preflight can execute arbitrary root code before rejecting its own hash.

Minimum remediation: make the remote command execute a small independently reviewed bootstrap supplied in the fixed command, not the remote launcher path. Under `sudo`, the bootstrap must open the exact launcher with `O_NOFOLLOW`, hold the descriptor, require a stable lstat/fstat/path identity, regular-file type, UID/GID `0:0`, no group/world-write bit, an explicit size bound, and the exact launcher SHA-256 before compiling the held bytes. It must set the exact `__file__` value and invoke only the reconstruction entry from those authenticated bytes. Add a regression in which a tampered launcher tries to create a marker at module import; the marker must remain absent.

### C2 — Local timeout or output-limit kill does not bound the remote root process

On output overflow and timeout the wrapper calls `process.kill()` only on local `ssh.exe` (`docs/contracts/vm105-reconstruction-only-successor-contract-20260914.md`, lines 70–94). Closing or killing the SSH client does not independently prove that the remote sudo/Python process and any in-progress reconstruction stopped. The remote process may continue copying or sealing the exact staging root after the local command reports timeout/limit and exits without a receipt. That breaks the claimed 600-second action bound and creates an unsafe state for a one-shot, no-retry operation.

Minimum remediation: enforce an absolute lifetime on VM105 around the exact authenticated reconstruction process, with a reviewed remote watchdog/process-group boundary that sends termination and then a bounded forced kill independent of the client connection. The coordinator must also kill and wait for local SSH, drain/close both pipes, and classify remote termination as unproven unless the authenticated remote terminal state is received. Add a regression that simulates a remote child surviving local SSH termination and prove the remote deadline/process-group mechanism ends it.

## Important findings

### I1 — Nonempty stderr is silently accepted

The wrapper drains and bounds stderr but never requires it to be empty. Receipt validation uses only stdout and the return code (`docs/contracts/vm105-reconstruction-only-successor-contract-20260914.md`, lines 96–136). A PASS or BLOCKED record can therefore be published while sudo, Python, or the remote launcher also emitted unexpected diagnostics. This weakens the single-record evidence boundary and can hide an execution anomaly.

Minimum remediation: require zero stderr bytes for an accepted remote PASS or BLOCKED receipt. Treat any nonempty stderr as a sanitized transport UNKNOWN condition; record only a fixed reason and byte count/hash if needed, never the stderr content. Add PASS-plus-stderr and BLOCKED-plus-stderr regressions.

### I2 — Failure and BLOCKED evidence semantics are incomplete

Timeout, overflow, malformed output, unexpected return code, and local no-overwrite publication failure raise `SystemExit` before any local receipt is created (`docs/contracts/vm105-reconstruction-only-successor-contract-20260914.md`, lines 85–102 and 138–151). The action can be spent after remote mutation while the named evidence leaf remains absent. The local validator also has a PASS-specific proof branch but no corresponding strict BLOCKED branch: it accepts any self-hashed reason, staging-precheck value, and scalar counts so long as the shared fields and broad cleanup-result enum pass (lines 119–136). These paths permit absent or semantically false terminal evidence.

Minimum remediation: reserve a no-overwrite local attempt marker before SSH and always produce a canonical, self-hashed, sanitized terminal record. Transport, timeout, overflow, stderr, and publication failures must be `UNKNOWN`, set `remoteState=UNPROVEN`, set `retryAuthorized=false`, and disclose no raw stderr or inventory. An accepted BLOCKED record must require a fixed uppercase reason, `stagingPrecheck` in the exact allowed enum, integer/nonnegative scalar counts, and count/cleanup combinations consistent with the source state machine. Publication failure must leave the pre-action marker as durable proof that the one-shot authority was consumed. Add regressions for each terminal branch.

## Checks that passed

- **Dormant/fail closed:** the contract says `DORMANT — NOT AUTHORIZED`; `ACCEPTED_LIVE_BINDINGS` remains `None`; `_reconstruction` rejects if it is ever non-`None`; and reconstruct-only CLI dispatch bypasses live bindings, stdin credentials, launch, and service entry.
- **Exact fixed bundle:** the immutable mapping fixes source root `/`, staging root `/var/tmp/omniroute-dsh-client-final-20260913`, bundle root `/var/tmp/omniroute-dsh-reconstruction-input-20260914`, all five filenames and raw hashes, both canonical hashes, 447 packages, and 2,029 links.
- **Bundle validation after the initial trust gap:** bundle directory and all five files are checked through held descriptors for fixed path, regular/nonlink type, root ownership, no group/world-write bit, stable identity, and exact hashes.
- **Absent-root and retention behavior:** any existing file, directory, or symlink at the staging root blocks before `stage`; an absent root is explicitly recorded; failures retain any partial exact root; source contains no cleanup or retry path.
- **Reconstruction scope:** the entry calls only the existing reconstruction, topology verification, and seal path. It looks up the `dsh` UID/GID for the seal and does not read credentials, create sockets, invoke systemd, start DSH/final-client processes, contact providers, or modify service/profile/default state.
- **Remote scalar receipt source:** PASS/BLOCKED source receipts contain only the fixed scalar schema and a canonical SHA-256 self-hash. PASS requires the accepted manifest/topology hashes, positive file/directory counts, exactly 2,029 links, and an exact sealed-entry sum.
- **SSH and publication controls apart from C2/I1/I2:** the wrapper fixes the target, identity path, `-F NUL`, batch/identity-only/password-disabled/keyboard-interactive-disabled/strict-host-key/no-forwarding options, one connection attempt, closed stdin, bounded stdout/stderr buffers, canonical stdout framing, and `O_CREAT|O_EXCL` local publication.
- **Canary wording:** reconstruction is explicitly separate from the exact live two-request chat-then-durable-ACK canary. Additional-request denial remains fixture evidence; ordinary post-default multi-turn, tools, persistence, durable ACKs, profile selection, provider generation, and no-replay remain separate and unproven.

## Immutable validation performed

`git diff --check 4cdd08809d1d68098f7d23b7f62832c800197f1f..0fbef6bab42d100f8f8d221c4ffae80adaecfb5e` returned no errors.

The scoped launcher suite was executed with bytecode disabled from a temporary `git archive` of the exact commit:

`python -B -m unittest scripts/test_vm105_production_launcher.py`

Result: **27 tests run, 27 passed** in 0.048 seconds.

A broader immutable-archive run executed 53 tests and produced 50 passes plus three failures in the unchanged topology-capture suite. Those failures occur because `git archive` exposes the stored LF builder blob while that existing suite deliberately pins the CRLF checkout bytes. They do not exercise this commit's three-file change and do not change the Critical/Important findings above. No test was run from mutable worktree source.

## Limits and authority

No Linux reconstruction, remote bundle, sudo rule, remote watchdog, SSH lifetime, receipt publication, filesystem mutation, root ownership, symlink handling, or staging seal was executed. The Windows unit tests use mocks for those boundaries. Even after the blockers are fixed, a source-only PASS would grant no live action; bundle delivery, fresh remote evidence, exact sudo argv review, independent wrapper review, an absent local receipt, an absent staging root, and a separate one-shot authorization would still be required.

At immutable commit `0fbef6bab42d100f8f8d221c4ffae80adaecfb5e`, source-only readiness is **No**.
