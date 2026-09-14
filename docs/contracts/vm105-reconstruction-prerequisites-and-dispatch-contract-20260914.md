# VM105 reconstruction prerequisites and dispatch contract — 2026-09-14

## Status and authority

**DORMANT — NOT AUTHORIZED.** `scripts/Invoke-VM105ReconstructionPrerequisites.py` is a source-only package. Its three mutually exclusive modes are bundle delivery, read-only prerequisite capture, and reconstruction dispatch. Each callable mode requires its module accepted binding constant to be non-`None` and requires `provided == accepted == computed binding`; knowing the public computed hash grants no authority. All three accepted binding constants are `None`; the accepted sudo-version pin, four accepted bundle/sudo receipt raw/self-hash constants, and `ACCEPTED_LIVE_BINDINGS` are also `None`. Therefore every CLI mode is **NOT EXECUTABLE**. This source does not authorize SSH, bundle delivery, `sudo`, reconstruction, staging, cleanup/retry, VM or service changes, OmniRoute, Hermes, credentials, gateway/provider traffic, a canary, or a default change.

The immutable launcher is `scripts/Invoke-VM105ProductionLauncher.py`, raw SHA-256 `f2011f4d81831e4fb102f2f9e9755690418387e2f697e5ca3044417de5767c6d`. The prerequisite package must load it through a stable held descriptor and reuse only its `RECONSTRUCTION_BINDING`, `RECONSTRUCTION_REMOTE_BOOTSTRAP`, `_run_bounded_reconstruction_ssh`, and `_coordinate_reconstruction_attempt` reconstruction seams. It must never use the topology `_run_bounded` seam. The authenticated reconstruction bootstrap is exactly 2,072 ASCII bytes with SHA-256 `cb0281b3a3816d355a6e114f11f55776ed1f3ca6a95be3e4874d4b4b613dd171`; the complete remote command is exactly 2,949 ASCII bytes with SHA-256 `b2f1c14ee67933c33bea9dde2736e384389c926d84837be0820ef73d57ca8d48`.

## Frozen bundle and evidence leaves

The final bundle root is `/var/tmp/omniroute-dsh-reconstruction-input-20260914`; its absent sibling temporary root is `/var/tmp/.omniroute-dsh-reconstruction-input-20260914.tmp`. The reconstruction staging root is `/var/tmp/omniroute-dsh-client-final-20260913`. The bundle contains only these basename-sorted rows:

| Repository source | Destination basename | Raw SHA-256 |
|---|---|---|
| `scripts/Build-VM105FinalClientManifest.py` | `Build-VM105FinalClientManifest.py` | `371481fe62d6611913f82f65b6e26b12512fda8a853a2f4591b6314f580c885f` |
| `scripts/Capture-VM105DshTopology.py` | `Capture-VM105DshTopology.py` | `aa2ca52f0460279d4fd76314be96610bfd87b1bf3e6b2c92e5446983468b6190` |
| `scripts/Invoke-VM105ProductionLauncher.py` | `Invoke-VM105ProductionLauncher.py` | `f2011f4d81831e4fb102f2f9e9755690418387e2f697e5ca3044417de5767c6d` |
| `docs/evidence/vm105-dsh-topology-capture-successor-20260913.json` | `vm105-dsh-topology-capture-successor-20260913.json` | `86882398a06921bd351c84dbfc1eecc9abeb963912df41499ee21462b50cb47f` |
| `docs/evidence/vm105-final-client-runtime-manifest-20260913.json` | `vm105-final-client-runtime-manifest-20260913.json` | `54d117c638335edeefe43aaef0f181ea5317f7938a6861a145871a0d9e45e8dd` |

The fixed local evidence leaves are:

- delivery attempt: `docs/evidence/vm105-dsh-reconstruction-bundle-delivery-successor-attempt-20260914.json`
- delivery terminal: `docs/evidence/vm105-dsh-reconstruction-bundle-delivery-successor-20260914.json`
- bundle receipt: `docs/evidence/vm105-dsh-reconstruction-bundle-successor-20260914.json`
- sudo receipt: `docs/evidence/vm105-dsh-reconstruction-sudo-policy-successor-20260914.json`
- dispatch attempt: `docs/evidence/vm105-dsh-reconstruction-successor-attempt-20260914.json`
- dispatch terminal: `docs/evidence/vm105-dsh-reconstruction-successor-20260914.json`

Every local evidence leaf uses canonical JSON, a canonical self-hash, and `O_CREAT|O_EXCL`. An occupied applicable evidence leaf blocks before transport. The local SSH helper concurrently streams a bounded stdin frame and bounded stdout/stderr, kills and waits/reaps on timeout, overflow, or stream error, drains and closes every pipe, and exposes only sanitized `UNKNOWN` evidence on failure. Stderr content is never stored. A consumed attempt never authorizes cleanup or retry.

## Bundle delivery mode

Local source reads must open each fixed path read-only with available `O_NOFOLLOW`/close-on-exec flags, compare path and descriptor identity before and after the raw bounded read, and verify the table SHA-256. The strict SSH argv fixes the executable, identity, target `dsh@192.168.1.139`, host-key and authentication options, disables forwarding, and includes `--` immediately before the target. The canonical stdin frame contains only the final root, temporary root, and the exact five basenames, raw hashes, and base64-encoded bytes.

The authenticated remote bootstrap embeds the exact five basename-to-hash pins and rejects any input-row difference before creating the temporary root. It refuses any object at the final or temporary root. It creates the temporary root and each file with no-overwrite semantics, writes the exact bytes, applies root:root and mode `0440`, fsyncs and rereads each held descriptor, and verifies the exact size/hash/metadata. It applies root:root and `0550` to the directory and fsyncs it. Final publication uses Linux `renameat2(..., RENAME_NOREPLACE)` on the same filesystem, so a final root appearing concurrently is never overwritten; unsupported atomic no-replace or an occupied destination blocks and retains the temporary root. After successful publication it fsyncs `/var/tmp`. Any uncertainty after publication is `UNKNOWN`. No failure authorizes cleanup or retry.

## Read-only prerequisite capture mode

The bundle attestation opens the fixed final root as a stable held directory descriptor, lists that descriptor once, and rejects any missing or extra basename before opening a file. It then reads only the five fixed basenames relative to that descriptor and rechecks the root identity. Its canonical self-hashed schema has exactly `status`, `reason`, `vmHostname`, `vmMachineIdSha256`, `bundleRoot`, `bundleDevice`, `bundleInode`, `bundleMode`, `bundleUid`, `bundleGid`, `bundleSize`, `bundleMtimeNs`, `bundleCtimeNs`, `expectedFileCount`, `fileCount`, `files`, and `receiptSha256`. `files` contains exactly five basename-sorted rows, each with exactly `basename`, `type`, `symlink`, `device`, `inode`, `mode`, `uid`, `gid`, `size`, `mtimeNs`, `ctimeNs`, and `sha256`. PASS requires strictly typed nonnegative numeric identity fields, the final root to be root:root `0550`, and every regular non-symlink file to be root:root `0440` with its exact raw hash.

Two separate noninteractive read-only queries are required. The first asks whether the sole target argv is allowed without executing it: `/usr/bin/python3.12`, `-I`, `-c`, the exact authenticated bootstrap expression, and the launcher hash. The second captures the sudo version and complete `sudo -ll` detailed policy. PASS requires an explicitly accepted exact sudo version and one completely parsed policy entry only: run-as root, the sole `!authenticate`/NOPASSWD option, and the exact target argv. The parser tolerates an omitted `Matching Defaults` section, or only the clearly non-authorizing Defaults `env_reset`, `mail_badpass`, `use_pty`, and the conventional fixed `secure_path`; it also tolerates a syntactically safe `/etc/sudoers` or `/etc/sudoers.d/<leaf>` source location. Authorizing or unrecognized Defaults, extra options or entries, wildcards, other commands, shell authority, broader Python authority, or `ALL` cannot pass. Unsupported or ambiguous output and version drift block; transport uncertainty is `UNKNOWN`. Nonempty stderr from either query is always sanitized `UNKNOWN` and never PASS. No live VM sudo version or output grammar has been captured or accepted, so `ACCEPTED_SUDO_VERSION` remains `None` and this mode remains dormant.

The canonical self-hashed sudo receipt has exactly `status`, `reason`, `queryUser`, `sudoPath`, `noninteractive`, `targetArgc`, `targetArgvSha256`, `bootstrapBytes`, `bootstrapSha256`, `launcherSha256`, `effectivePolicySha256`, `exactCommandAllowed`, `broaderAuthorityDetected`, `rawOutputStored`, and `receiptSha256`. It stores only hashes and scalars; the exact-query output, detailed policy, and stderr are never retained. PASS requires user `dsh`, `/usr/bin/sudo`, noninteractive mode, the exact fixed pins, `exactCommandAllowed=true`, `broaderAuthorityDetected=false`, and `rawOutputStored=false`. A full detailed listing that exposes `NOPASSWD: ALL` produces `BLOCKED_BROAD_SUDO_POLICY` even when the exact-command query succeeds.

A recorded historical `NOPASSWD: ALL` is unverified current state. It remains a blocker/risk that requires this fresh exact attestation; this contract makes no current sudo-policy claim.

## Reconstruction dispatch and remaining gates

Dispatch remains blocked until a later reviewed source change binds its exact authority hash plus independently accepted non-`None` raw and self-hashes for both PASS receipts. The callable itself requires every caller-supplied raw/self hash to equal its corresponding non-`None` module `ACCEPTED_*` constant before any evidence read; an importer cannot substitute a different schema-valid PASS receipt. Dispatch rereads both receipts through stable local descriptors, verifies raw hashes, canonical framing, fixed schemas, self-hashes, exact pins, and PASS state. It then verifies the immutable launcher and `ACCEPTED_LIVE_BINDINGS is None`, builds the exact strict SSH command, and calls the launcher's reconstruction-only bounded transport through its one-shot coordinator. No other runner or live binding is accepted.

Separate authorization is still required for each live mode. After prerequisite PASS, the remaining gates include independent evidence acceptance, exact sudo-policy review, absent dispatch evidence, absent staging root, reconstruction authorization, and acceptance of the immutable reconstruction terminal record. Reconstruction proves only the staged sealed closure described by the immutable launcher contract.

The production canary remains a separate action and proof boundary: exactly two accepted requests, chat followed by its durable ACK, with `deniedRequests=0`. Reconstruction does not authorize or prove that canary, provider generation, credentials, default selection, ordinary multi-turn/tool lifecycle, persistence, durable ordinary-session ACKs, or no-automatic-replay behavior.
