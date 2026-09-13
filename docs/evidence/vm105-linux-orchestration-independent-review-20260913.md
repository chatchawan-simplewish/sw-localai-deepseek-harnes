# VM105 Linux orchestration independent review — 2026-09-13

## Verdict

**PASS FOR SOURCE-ONLY PUBLICATION**

- Ready to publish/merge: **Yes**
- Ready to execute or activate: **No — NOT EXECUTABLE**
- Critical findings: **0 open**
- Important findings: **0 open**

The reviewed source remains deliberately fail closed. `ACCEPTED_LIVE_BINDINGS` and `ACCEPTED_STAGING_TOPOLOGY_SHA256` are both `None`, so shape-valid input cannot read a credential descriptor, inspect or create the staging root, start `systemd-run`, create a namespace, open a gateway socket, or run DSH. This verdict accepts the concrete local source, contracts, and failure evidence at the exact revision below. It grants no capture retry, topology acceptance, staging, gateway, credential, VM, service, profile, selector, default, provider, or live-execution authority.

## Review identity and revision

- Repository: `https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git`
- Working repository: `C:\Users\chatc\Projects\sw-localai-deepseek-harnes\.worktrees\vm105-authoritative-roadmap`
- Branch: `codex/vm105-authoritative-roadmap`
- Base: `b6b0d6524b1fc040a37448e331589d41a45c4b1b`
- Reviewed head: `4b03089dae047868ee53007fb24d41d154186e29`
- Local HEAD and local origin-tracking ref: both `4b03089dae047868ee53007fb24d41d154186e29`
- Reviewer: independent Sol High task `linux_launcher_review`

The committed base-to-head diff and the complete final launcher, relay, topology helper, focused tests, production and topology contracts, packet, plan, prior-review transcription, three attempt records, BLOCKED receipt, and referenced external review artifacts were reviewed. No source, live resource, receipt, or existing evidence file was modified by the reviewer. The pre-existing untracked `scripts/__pycache__/` directory was not touched.

## Exact reviewed hashes

| Artifact | SHA-256 |
|---|---|
| `scripts/Invoke-VM105ProductionLauncher.py` | `8b2ba45a186bec854787376d34d63f6ff8bc8aac390f6cb83fc063c8ff355a7e` |
| `scripts/test_vm105_production_launcher.py` | `ff7769fccd6767038cc8287f29abe1b42e461ecfce2ff93c8269c84ede291778` |
| `scripts/Invoke-VM105FinalClient.py` | `1381e0717a89667641ce64598911e99de91a994994401a3f76078074823c9f34` |
| `scripts/test_vm105_final_client_transport.py` | `46b60f6a9b915af60cef4a1f3d12470979003ad86384d3f012c42a2999fcd97b` |
| `scripts/Capture-VM105DshTopology.py` | `aa2ca52f0460279d4fd76314be96610bfd87b1bf3e6b2c92e5446983468b6190` |
| `scripts/test_vm105_dsh_topology_capture.py` | `3d1a5941eea05a9516b893480be610539ade4d1d57c4e9549ed8c61fc1977d34` |
| `docs/contracts/vm105-dsh-topology-capture-contract-20260913.md` | `a841f94c1ef97ee884a4179b211190a72ae742e52be9e0ad6610506cc1c337e8` |
| `docs/contracts/vm105-production-staging-and-socket-handoff-contract-20260913.md` | `66d6ebbe7879228288fe638d4239b1bc7f7071cb579455c354de6bb3b699459b` |
| `docs/handoffs/vm105-omniroute-final-client-packet-20260913.md` | `aef69c78033204b4acf1ba44977ec3e15033e5bdf697bc7f2a80b4513068d9b0` |
| `docs/superpowers/plans/2026-09-13-vm105-linux-orchestration-source.md` | `44c16cb11abddd449a6756f745a58723abc431711995d28f0578f1e0f17448be` |
| `docs/evidence/vm105-source-preparation-independent-review-transcription-20260913.md` | `e61418091c00aaaa8d295f6729a6f374a3d3c0a7ee3d8ce32cc078366aa354b3` |

The launcher source pins the exact final-client hash `1381e071...c9f34`, topology-helper hash `aa2ca52f...8b6190`, manifest-builder hash `371481fe...0c885f`, and accepted manifest canonical hash `4331e0e5...03f8b`. Those pins match the reviewed operational files and evidence.

## Validation performed

The following focused command was rerun against the exact final files with Python bytecode disabled:

`python -B -m unittest scripts/test_vm105_production_launcher.py scripts/test_vm105_final_client_transport.py scripts/test_vm105_dsh_topology_capture.py`

Result: **46 tests run, 46 passed** in 5.868 seconds.

The three Python sources were also compiled in memory without writing bytecode: **PASS**. `git diff --check` for base-to-head returned no errors. The accepted manifest was independently recomputed:

- Raw file SHA-256: `54d117c638335edeefe43aaef0f181ea5317f7938a6861a145871a0d9e45e8dd`
- Canonical unsigned SHA-256: `4331e0e5fd9ac6f5e881a0dae941f9f07dea7b69969ee8b610071ce14cb03f8b`
- Counts: 447 packages, 10,026 modules, two entrypoints, three config bundles, and seven Node runtime dependencies

The focused tests are local Windows tests. They use mocks at the Linux, systemd, namespace, mount, cgroup, credential, descriptor-transfer, and DSH-process boundaries. Their PASS establishes the tested orchestration rules and fail-closed behavior; it does not establish Linux execution.

## Findings and closure

No new Critical or Important defect remains at the reviewed head. The review specifically rechecked the prior findings and their final fixes:

1. **Live gates and paths — addressed.** Both independent source gates remain unbound; the accepted dictionary must match exactly; topology hashes are lowercase-only; source root is exactly `/`; staging root is exactly `/var/tmp/omniroute-dsh-client-final-20260913`; and every launcher operating-system seam is behind the live gate.
2. **Credential handling — addressed.** The outer launcher passes the supplied read descriptor directly as `systemd-run --pipe` standard input with `close_fds=True`, no arbitrary `pass_fds`, and no outer credential copy. The service bounds the mutable document, copies it once to a close-on-exec worker pipe, closes the writer before fork, and wipes its mutable buffers. The relay necessarily retains an immutable key string transiently; the contracts make no complete-memory-erasure claim and limit `credentialExposed:false` to the named persistence surfaces.
3. **Systemd unit and lifecycle — addressed.** Only `.service` unit names matching the exact pattern are accepted. Absolute systemd binaries, exact capabilities and hardening, 120/600/10/625-second bounds, exact `INVOCATION_ID`, exact `/system.slice/<unit>` cgroup identity, scalar compact receipts, runtime-directory removal, and empty-or-missing cgroup checks are enforced. Rejected, malformed, nonzero, and timeout results kill only the exact unit and return sanitized failure state.
4. **Socket handoff and relay completion — addressed.** The supervisor makes exactly two numeric-peer TCP connections in chat/ACK order, performs one fixed `sendmsg`, closes its copies, and never retries. The receiver permits exactly two close-on-exec TCP descriptors and verifies both peers. Production composition requires exactly two request attempts, zero denied requests, two accepted requests, both handed sockets consumed, tuple equality, committed ACK, released output, and no failed state.
5. **Output commit race — addressed.** `scripts/Invoke-VM105FinalClient.py` now holds the relay lock across the first downstream byte write, flush, and `output=True` transition. A concurrent denied request cannot mark the transaction failed after a byte has escaped but before the irreversible state transition. The deterministic regression proves the denial waits and is treated as post-commit.
6. **Process and namespace containment — addressed in source.** The worker creates a session, enters only new network and PID namespaces before fork, raises loopback, and lets namespace PID 1 alone create the mount namespace. PID 1 mounts fresh `/proc`, self-bind/remounts `/var/tmp` read-only, remounts `/run` read-only with only its assigned runtime bind remaining writable, closes descriptors outside the fixed allowlist, and drops supplementary groups/GID/UID before DSH. The supervisor uses `waitid(...WNOWAIT)`, process-group identity, `waitpid`, and bounded exact-child/group termination to prevent PID-reuse ambiguity.
7. **Topology reconstruction and seal — addressed in source.** The accepted manifest builder and topology helper are hash pinned. Capture re-runs the full accepted inventory before link capture. Reconstruction validates receipt schema, self-hash, manifest/count/headless pins, recreates only captured root-owned relative links, copies physical files with descriptors, and performs two full inventory/hash/mode/UID/GID/link-resolution passes. The launcher then applies and rechecks the root:`dsh` read-only seal: directories and executables `0550`, data `0440`, links root:root.
8. **Windows binary and POSIX path handling — addressed.** Pinned files and the CLI use binary reads for CRLF-sensitive hashes. Fixed installed paths use `PurePosixPath` validation on every coordinator OS, rejecting relative, traversal, NUL, and Windows-backslash forms. CLI, transport payload, and remote target comparison now serialize literal `/opt/deepseek-harness`; the actual manifest and raw builder cross a no-network coordinator-to-remote-entry regression.
9. **Documentation authority and provenance — addressed.** The contract says a future capture requires separate fresh authority. The two external review commits resolve in the explicitly named external review repository, and their artifact SHA-256 values match. The third-receipt external review commit `e377656bd91b602535a7f0ca8459500556c1a987` also resolves there and its artifact hash matches `46612f8be54f718e7b7bf41d17829f4b537c4582d395f3c07e2e36dd52839380`.
10. **Canary versus ordinary service — addressed in documentation.** The exact two-request tools-disabled canary does not claim post-default multi-turn, tool-lifecycle, profile-selection, persistence, or normal service proof. Those remain separately unbound.

## Capture-attempt classification

All three topology-capture authorities are spent and no retry is authorized:

| Attempt | Frozen revision | Outcome | Remote boundary |
|---|---|---|---|
| First | `704f56bf1cbbfa8c80bbc11685d451e62a68cea9` | Local `ACCEPTED_BUILDER_HASH_MISMATCH` caused by Windows text-mode CRLF translation | SSH child not started |
| Replacement | `38a6c4120013c6bdbfc8bac09753dccf01356b94` | Local `ACCEPTED_PACKAGE_IDENTITY_INVALID` caused by host-native parsing of absolute POSIX manifest paths | SSH child not started |
| Third | `2c16a3d7d6a953d6d8ad35ab8e37cce46b950c61` | Remote `CAPTURE_TARGET_MISMATCH` caused by Windows serialization of the fixed POSIX target | One SSH child reached the authenticated remote source entry, then stopped at the first target-equality gate |

Attempt evidence hashes:

- `docs/evidence/vm105-dsh-topology-capture-attempt-20260913.md`: `9c4226d2e3d16552a44a2c4fcbe93df190b37fd198af46b7d1b5e926f8b5c0db`
- `docs/evidence/vm105-dsh-topology-capture-replacement-attempt-20260913.md`: `fa21d4bf1a3b9a6acb96253ff61e1d1bb8f8e00306585c7f2bec4dc3c9da50e1`
- `docs/evidence/vm105-dsh-topology-capture-third-attempt-20260913.md`: `2c36f58b4516900fcff31fa39acc93aeb4936597d73e9c85f78d362e96ae0296`
- `docs/evidence/vm105-dsh-topology-capture-20260913.json` (preserved third-attempt raw receipt): `86d878deb002c62cf69013717d38193248b7deed5b19a5a37c40e87de07c001d`
- Receipt status/reason: `BLOCKED` / `CAPTURE_TARGET_MISMATCH`
- Receipt canonical self-hash: `af969cf020e957fc935a825809e4d062ed9cef1879f468c231adc05d3e7e8925`

The third receipt is accepted only as immutable failure evidence. It is not a PASS topology receipt, does not bind `ACCEPTED_STAGING_TOPOLOGY_SHA256`, and cannot authorize reconstruction or DSH execution. Any future capture needs a newly named absent evidence leaf, newly frozen and independently reviewed source/contract/tests, and a fresh explicit dispatch.

## Residual limits

- `ACCEPTED_LIVE_BINDINGS = None` and `ACCEPTED_STAGING_TOPOLOGY_SHA256 = None`; the launcher is **NOT EXECUTABLE**.
- No accepted PASS topology receipt exists. Copied pnpm links, the headless patch, and executable staged topology remain unbound.
- Linux `lstat`/`readlink`, ownership, mount, PID/network namespace, loopback, privilege drop, `SCM_RIGHTS`, `systemd-run --pipe`, cgroup, runtime cleanup, and DSH boot behavior remain **NOT PROVEN**.
- The supported network claim is only `IP_TCP_NAMESPACE_ONLY`. Pathname `AF_UNIX` sockets remain an explicit residual.
- The production key, action-time gateway peer, relay origin, current selector, final profile/config composition, native DSH boot, ordinary persisted multi-turn service, tool lifecycle, durable acknowledgements, and no-automatic-replay behavior remain unbound or **NOT PROVEN**.
- The three capture attempts establish only their bounded failure paths. The third remote entry stopped before manifest validation, builder execution, `ldd`, installed-tree reads, or topology traversal.

Within those explicit limits, the exact head `4b03089dae047868ee53007fb24d41d154186e29` is ready to publish/merge as source-only, fail-closed preparation.
