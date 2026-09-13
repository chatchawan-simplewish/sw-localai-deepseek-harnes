# VM105 topology-binding independent review — 2026-09-14

## Verdict

**PASS FOR SOURCE-ONLY PUBLICATION**

- Ready source-only: **Yes**
- Ready for reconstruction, staging, or execution: **No**
- Critical findings: **0 open**
- Important findings: **0 open**

The topology receipt is now cryptographically bound in the dormant launcher, while `ACCEPTED_LIVE_BINDINGS` remains `None`. Shape-valid input therefore still stops before credential-descriptor access or any operating-system action. This review grants no reconstruction, staging, service, credential, gateway, provider, profile, default-routing, or live-execution authority.

## Review identity and exact artifacts

- Repository: `https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git`
- Working repository: `C:\Users\chatc\Projects\sw-localai-deepseek-harnes\.worktrees\vm105-authoritative-roadmap`
- Prior reviewed head: `8f63cd45d07b5b95ba425187338a7fe558e91acf`
- Reviewed head: `d2a01134813fd9af06cf0554a456c0124b32afcf`
- Local HEAD and local origin-tracking ref: both `d2a01134813fd9af06cf0554a456c0124b32afcf`

| Artifact | SHA-256 |
|---|---|
| `scripts/Invoke-VM105ProductionLauncher.py` | `5af2e7b542547bbceb4050fa2d0885e92eeda8d62cbe30c5b365aadc7b120c33` |
| `scripts/test_vm105_production_launcher.py` | `2ae1a0ffdd0576637db6bd8c82f20507771a9cebe8febd1bc124519a9ac7c461` |
| `docs/contracts/vm105-dsh-topology-capture-contract-20260913.md` | `4ff3599e119c1ab325e9cbf282420d8af90fa0b85c10a7ae5e7fa7bd3d6a2e1d` |
| `docs/contracts/vm105-production-staging-and-socket-handoff-contract-20260913.md` | `7cb29fcd37e9f9119ce2dbbbdcafca691d243f542bb8e802bffce6c5d42dc23d` |
| `docs/handoffs/vm105-omniroute-final-client-packet-20260913.md` | `978a1e35e1e6e748c8203fedf512a4ccb8c6dcfe733da84cb382d2d2f7552fc5` |
| `docs/evidence/vm105-dsh-topology-capture-successor-20260913.json` | `86882398a06921bd351c84dbfc1eecc9abeb963912df41499ee21462b50cb47f` |
| `docs/evidence/vm105-dsh-topology-capture-successor-attempt-20260914.md` | `d2747c3c0a5c72e24335c7ef9cb1fde54b0406ab8682c5c81a6434b8bfa6015a` |
| `docs/evidence/vm105-dsh-topology-capture-successor-receipt-review-20260914.md` | `db5e640a1539542059a19e431e307a176210a81ea177237cf62f447e5221016d` |

The successor receipt is 1,825,540 bytes. Its accepted canonical self-hash is `cc7ca73f74bd1e515416cbff65809531fff2c052d0f7e406b9cc2efdb4c1ab20`.

## Source behavior

1. **Canonical topology binding is correct.** `ACCEPTED_STAGING_TOPOLOGY_SHA256` equals the receipt's canonical self-hash `cc7ca73f...ab20`. `_live` requires a complete binding dictionary whose lowercase `topologySha256` equals that constant exactly. The value passed to `stage_verified_topology` is the same bound canonical self-hash, so the topology helper recomputes and checks the receipt's canonical semantics rather than confusing the self-hash with its raw-file hash.
2. **Raw receipt binding is independent and precedes JSON use.** `ACCEPTED_STAGING_TOPOLOGY_FILE_SHA256` equals raw receipt SHA-256 `86882398...b47f`. The launcher opens the topology path with `O_NOFOLLOW` and `O_CLOEXEC`, requires a held regular-file descriptor, captures its device/inode/mode/size/mtime/ctime identity, reads and hashes bytes from that descriptor, requires unchanged post-read identity, and checks the exact raw hash before calling `json.loads`.
3. **The receipt read is bounded.** The final source caps topology receipts at 8 MiB, reads at most the remaining budget plus one byte, and rejects before appending once cumulative input exceeds the cap. This closes the Important review finding in the initial `604d484b...` snapshot, where a file that grew after the first `fstat` could have caused unbounded buffering before rejection. The regression uses a four-byte limit and stub reads `abc` then `de` to prove growth is rejected.
4. **The live gate remains pre-OS fail closed.** `ACCEPTED_LIVE_BINDINGS` is still `None`. `_live` compares the entire normalized dictionary before every launcher operating-system seam. The CLI invokes `_live` before reading the credential descriptor, and the focused gate test confirms even a request carrying the accepted topology self-hash cannot reach an injected systemd runner or descriptor operation. The source is **NOT EXECUTABLE**.
5. **Receipt immutability is preserved.** The accepted successor receipt is committed as a single LF-terminated canonical record, `.gitattributes` fixes that path to LF, and its raw hash matches the independently reviewed receipt. The earlier 142-byte third-attempt receipt remains separately preserved at raw SHA-256 `86d878deb002c62cf69013717d38193248b7deed5b19a5a37c40e87de07c001d`.

## Authority and documentation

The topology contract, production contract, attempt record, and handoff packet consistently classify the successor as the fourth and final spent capture authority. The first two attempts stopped locally, the third produced the preserved `BLOCKED / CAPTURE_TARGET_MISMATCH` receipt, and the fourth produced the accepted PASS receipt. None may be retried. The PASS receipt binds installed topology evidence only and grants no reconstruction or action authority.

The documented next reconstruction step remains separate. It must preserve the reviewed reconstruction and seal helpers; bind the exact successor receipt path and self-hash together with the accepted manifest, source root `/`, staging root `/var/tmp/omniroute-dsh-client-final-20260913`, and independently pinned launcher/final-client/builder/topology-helper bytes; freshly prove the staging root absent; and receive separate authorization before any action. Gateway peer, credential reference/schema, relay origin, task, and current selector remain unbound.

The exact two-request canary remains correctly separated from ordinary post-default service acceptance. The canary covers chat then durable ACK, exact two accepted requests, one additional denied request, output ordering, and cleanup. It does not establish profile selection, persisted multi-turn behavior, tool lifecycle, durable ordinary-session acknowledgements, or no-automatic-replay behavior. Those still require their own reviewed profile/config binding and live acceptance.

## Validation performed

The complete prior-to-final diff was reviewed, including the launcher helper, gate tests, contracts, packet, committed PASS receipt, attempt evidence, and receipt review. `git diff --check` returned no errors. The exact focused command was rerun with Python bytecode disabled:

`python -B -m unittest scripts/test_vm105_production_launcher.py scripts/test_vm105_final_client_transport.py scripts/test_vm105_dsh_topology_capture.py`

Result: **47 tests run, 47 passed** in 5.523 seconds.

These are local Windows tests. Linux descriptor semantics, reconstruction, symlink-aware copied-tree sealing, mount and namespace operations, systemd, cgroups, credential transfer, socket handoff, native DSH boot, gateway behavior, and ordinary service behavior remain mocked or unexecuted and therefore **NOT PROVEN**.

Within those limits, exact head `d2a01134813fd9af06cf0554a456c0124b32afcf` is ready to publish/merge as source-only topology binding. It remains pre-operating-system **NOT EXECUTABLE** and grants no reconstruction, staging, or execution authority.
