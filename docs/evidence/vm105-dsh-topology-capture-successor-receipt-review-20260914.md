# VM105 DSH topology successor receipt review — 2026-09-14

## Verdict

**PASS FOR TOPOLOGY ACCEPTANCE**

- Ready for topology acceptance: **Yes**
- Critical findings: **0**
- Important findings: **0**
- Reconstruction, staging, or execution authority: **None**

This verdict accepts the immutable successor receipt as a valid description of the captured topology under the source package below. It does not authorize reconstruction, staging, DSH execution, another capture, credential use, a service launch, provider traffic, profile/default changes, or any live action. A later acceptance step must explicitly pin the receipt and headless-patch hashes before any separate implementation or action can use them.

## Review identity and inputs

- Repository: `https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git`
- Working repository: `C:\Users\chatc\Projects\sw-localai-deepseek-harnes\.worktrees\vm105-authoritative-roadmap`
- Source package commit: `8f63cd45d07b5b95ba425187338a7fe558e91acf`
- Capture source: `scripts/Capture-VM105DshTopology.py`
- Capture source SHA-256: `aa2ca52f0460279d4fd76314be96610bfd87b1bf3e6b2c92e5446983468b6190`
- Focused test SHA-256: `9d190e2139d3da8ada0794104973841a0526038b125784d1ed3f5a0a22892016`
- Contract SHA-256: `8f765ae0e62be034d8b6e7b0e794fd2c1930fe245ffac4cd4302c3ad32a8d8e8`
- Successor receipt: `docs/evidence/vm105-dsh-topology-capture-successor-20260913.json`
- Successor receipt raw size: `1,825,540` bytes
- Successor receipt raw SHA-256: `86882398a06921bd351c84dbfc1eecc9abeb963912df41499ee21462b50cb47f`
- Claimed and independently recomputed canonical self-hash: `cc7ca73f74bd1e515416cbff65809531fff2c052d0f7e406b9cc2efdb4c1ab20`

The receipt was read locally without modification. No SSH, VM, capture, package, provider, reconstruction, staging, or execution action was performed.

## Validation performed

An independent parser checked the complete 1,825,540-byte file, rather than sampling rows:

1. The file contains exactly one canonical UTF-8 JSON record followed by one LF. Re-encoding with sorted keys, compact separators, and UTF-8 reproduced the raw bytes exactly.
2. The raw SHA-256 and size match the supplied immutable values. Removing only `receiptSha256` and hashing the canonical unsigned object reproduced `cc7ca73f...ab20`.
3. The top-level object contains exactly the ten contract keys. Its status is `PASS`; accepted and reachable package counts are both exactly 447; `dependencyLinkCount` is exactly 2,029 and equals the link-array length; and the start package is exactly `node_modules/@deepseek-ai/dsh`.
4. The accepted manifest raw SHA-256 is `54d117c638335edeefe43aaef0f181ea5317f7938a6861a145871a0d9e45e8dd`. Its independently recomputed unsigned canonical SHA-256 is `4331e0e5fd9ac6f5e881a0dae941f9f07dea7b69969ee8b610071ce14cb03f8b`, matching the receipt.
5. The receipt's 447 unique `(name, version, canonicalPackagePath)` identities equal the accepted manifest's complete 447-package set. There are no missing or extra package identities. Every receipt package has a unique first logical path, and every first logical path is present in the link set.
6. All 447 `packageJsonSha256` values are lowercase 64-digit hashes and equal the corresponding `package.json` byte hashes in the accepted 10,026-module manifest. Every package identity has the exact nine-key schema, UID/GID `0:0`, `rootOwned:true`, and no group/world-write mode. Modes are 446 at `0644` and one at `0755`.
7. All 2,029 link rows have the exact seven-key schema and unique logical paths. Every raw target is relative, uses POSIX separators, contains no empty or `.` component, and normalizes within the install-root-relative tree to the recorded canonical package path. There are no absolute, backslash, NUL, or escaping targets. Every resolved `(name, version, canonical path)` exists in the accepted 447-package set, and every link repeats the matching package.json hash.
8. All 2,029 link identities have the exact nine-key schema, UID/GID `0:0`, and `rootOwned:true`. Their recorded `0777` modes are nominal symlink modes and are not treated as writable-file permissions by the reviewed contract and source.
9. The pinned capture source's own canonical framing, receipt-schema, accepted-manifest, package-set, link-resolution, identity, and headless-patch validators accepted the same raw receipt without normalization or mutation.

## Headless patch

- Logical path: `node_modules/.pnpm/@deepseek-ai+dsh@0.1.1-rc.2_7adf779e9bedfb2e97ced92905792931/node_modules/@deepseek-ai/dsh-headless/cordis.patch.yml`
- Canonical path: `node_modules/.pnpm/@deepseek-ai+dsh-headless@0.1.1-rc.2_6f2d1767c8b04054fa31cea644d40f88/node_modules/@deepseek-ai/dsh-headless/cordis.patch.yml`
- SHA-256: `534dc49c84b0fb9c2d3278dc8990f577d57b7a88442941444b58c96ac1a09ba0`
- Identity: exact nine-key schema, UID/GID `0:0`, `rootOwned:true`, mode `0644`, size `1,300` bytes, and no group/world-write mode

The logical and canonical paths are exactly the unique accepted `@deepseek-ai/dsh-headless` package's first logical and canonical paths plus `cordis.patch.yml`. The hash is well formed, is covered by the receipt self-hash, and is the exact value that a later topology-acceptance change must pin. This review did not independently reread the remote patch bytes.

## Historical receipt preservation

The historical third-attempt receipt remains present at `docs/evidence/vm105-dsh-topology-capture-20260913.json`, size 142 bytes, with unchanged raw SHA-256 `86d878deb002c62cf69013717d38193248b7deed5b19a5a37c40e87de07c001d`. It remains the spent `BLOCKED / CAPTURE_TARGET_MISMATCH` evidence and is not replaced or reclassified by this successor PASS receipt.

## Limits and authority boundary

- This is a source-and-receipt review. It did not repeat the remote capture or observe current VM105 state.
- Stable device, inode, size, mtime, ctime, ownership, and mode values are authenticated by the canonical receipt and were validated for schema and policy. Present-time remote stability is not independently proven by this offline review.
- The headless-patch bytes were not independently retrieved; the receipt records their captured hash and stable root-owned identity.
- Receipt acceptance alone does not prove reconstruction, staging seals, Linux namespace or mount behavior, `systemd-run`, cgroup cleanup, socket handoff, credentials, native DSH boot, canary completion, ordinary-session behavior, or provider generation.
- The successor capture authority is spent by the occupied receipt. No recapture or retry authority is implied.

Within these limits, the successor receipt is internally canonical, hash-valid, schema-valid, closure-complete, identity-consistent, and ready to be pinned by a separate topology-acceptance change. It grants no reconstruction, staging, or execution authority.
