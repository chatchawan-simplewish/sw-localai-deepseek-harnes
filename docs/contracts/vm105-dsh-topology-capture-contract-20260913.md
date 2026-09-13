# VM105 DSH topology capture contract — 2026-09-13

## Status and purpose

`LOCAL SUCCESSOR FIXED / THREE CAPTURE AUTHORITIES SPENT / SIGNED REMOTE RECEIPT BLOCKED`

This is the smallest new read-only capture needed to prove whether the accepted VM105 DSH installation can be reconstructed as an executable pnpm closure. It does not reuse a spent gate and does not authorize staging, package execution, provider traffic, credential access, a launch, or default activation.

## Exact target and inputs

- SSH target: `dsh@192.168.1.139`
- Installed root: `/opt/deepseek-harness`
- Traversal start: `/opt/deepseek-harness/node_modules/@deepseek-ai/dsh`
- Pinned Node runtime: `/opt/node-v24.19.0-linux-x64/bin/node`
- Target interpreter: `/usr/bin/python3.12 -I`
- Local capture source: `scripts/Capture-VM105DshTopology.py`
- Independently pinned local successor SHA-256: `aa2ca52f0460279d4fd76314be96610bfd87b1bf3e6b2c92e5446983468b6190`
- Accepted manifest: `docs/evidence/vm105-final-client-runtime-manifest-20260913.json`
- Accepted manifest canonical SHA-256: `4331e0e5fd9ac6f5e881a0dae941f9f07dea7b69969ee8b610071ce14cb03f8b`
- Accepted manifest file SHA-256: `54d117c638335edeefe43aaef0f181ea5317f7938a6861a145871a0d9e45e8dd`
- Pinned builder: `scripts/Build-VM105FinalClientManifest.py`
- Pinned builder SHA-256: `371481fe62d6611913f82f65b6e26b12512fda8a853a2f4591b6314f580c885f`
- Expected accepted closure: 447 package identities and 10,026 module rows
- Preserved third-attempt BLOCKED evidence: `docs/evidence/vm105-dsh-topology-capture-20260913.json`

## Preconditions and authority

There is no current capture authority. The first two one-shot authorities stopped locally before SSH. The third reached the authenticated remote source entry and published the canonical signed BLOCKED receipt above with sole reason `CAPTURE_TARGET_MISMATCH`; it stopped before accepted-manifest validation, builder execution, `ldd`, or topology traversal. All three authorities are spent. A future attempt requires a newly frozen source/contract/test set, independent review, a newly named absent evidence leaf, and a fresh explicit dispatch. Before that future SSH starts, the local capture source must be a regular non-link file matching its independently supplied hash, and the manifest and builder must likewise be stable regular non-link files matching their hashes. Strict host-key verification and the pinned identity must succeed, and no other owner may be changing `/opt/deepseek-harness`.

The remote process receives the capture source, its independently supplied expected hash, accepted manifest, and pinned builder source over stdin. The fixed bootstrap hashes the exact UTF-8 source bytes and fails before `compile`/`exec` unless they match. It performs no writes, provider requests, credential reads, Node/DSH package execution, runtime launch, service change, namespace change, cgroup change, or profile/default mutation. The pinned builder invokes `ldd` only to revalidate the accepted Node shared-library closure; the dispatch gives it a fixed `/usr/bin:/bin` PATH. SSH is only the transport used by the coordinator outside the capture process.

## Fail-closed checks and receipt

The source validates the pinned builder hash, executes that exact source under a non-main isolated namespace, and calls its `build_manifest` against `/opt/deepseek-harness/node_modules` and the pinned Node path. That fresh builder run captures the complete inventory twice, including all package identities, 10,026 module bytes, entrypoints, configuration bundles, the Node binary, and its runtime libraries. The capture requires the fresh unsigned canonical JSON to equal the supplied accepted unsigned manifest byte for byte and to hash to `4331e0e5fd9ac6f5e881a0dae941f9f07dea7b69969ee8b610071ce14cb03f8b` before topology traversal begins. Any builder or inventory failure becomes the secret-free `FRESH_MANIFEST_RESCAN_FAILED` or `FRESH_MANIFEST_MISMATCH` reason.

After full-manifest revalidation, the source traverses every present dependency, optional-dependency, and peer-dependency link reachable from `@deepseek-ai/dsh`.

Every recorded link contains its install-root-relative logical path, raw relative target, resolved install-root-relative canonical package path, stable `lstat` identity, root:root ownership, package name/version, and stable `package.json` SHA-256. Absolute or escaping links, changing identities, missing required dependencies, links or real paths whose UID or GID is nonzero, group/world-writable real paths, and any missing or extra canonical package identity block the receipt. Nominal symlink mode bits are recorded but are not treated as writable-file permissions.

The receipt also records the exact reachable logical and canonical paths, stable identity, and SHA-256 of `@deepseek-ai/dsh-headless/cordis.patch.yml`. A PASS receipt contains a `receiptSha256` calculated over canonical JSON before that field is inserted. BLOCKED receipts use the same self-hash format and contain no path-dependent traceback.

## Historical third dispatch command — spent

The following is the exact third dispatch and must not be rerun. It pinned source commit `2c16a3d7d6a953d6d8ad35ab8e37cce46b950c61` and source SHA-256 `17e43721293d3bffe5c33f63ad2491cd79905bc961993bf40ac0072e48a2bb73`. Trusted PowerShell read the source as raw bytes from a regular non-link file and verified the independently pinned hash before any Python from that source could execute. The coordinator then enforced the raw manifest and CRLF-sensitive builder hashes before SSH and bounded total time and output. It accepted one canonical signed BLOCKED line and published it through a fresh no-overwrite hard link. That evidence leaf is now occupied and the one-shot authority is spent.

```powershell
$worktree = 'C:\Users\chatc\Projects\sw-localai-deepseek-harnes\.worktrees\vm105-authoritative-roadmap'
$sourcePath = Join-Path $worktree 'scripts\Capture-VM105DshTopology.py'
$manifestPath = Join-Path $worktree 'docs\evidence\vm105-final-client-runtime-manifest-20260913.json'
$builderPath = Join-Path $worktree 'scripts\Build-VM105FinalClientManifest.py'
$evidencePath = Join-Path $worktree 'docs\evidence\vm105-dsh-topology-capture-20260913.json'
$expectedCaptureSourceSha256 = '17e43721293d3bffe5c33f63ad2491cd79905bc961993bf40ac0072e48a2bb73'
$sourceItem = Get-Item -LiteralPath $sourcePath -Force
if ($sourceItem.PSIsContainer -or ($sourceItem.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
    throw 'CAPTURE_SOURCE_NOT_REGULAR'
}
$sourceBytes = [IO.File]::ReadAllBytes($sourcePath)
$sha256 = [Security.Cryptography.SHA256]::Create()
try {
    $actualCaptureSourceSha256 = [BitConverter]::ToString($sha256.ComputeHash($sourceBytes)).Replace('-', '').ToLowerInvariant()
} finally {
    $sha256.Dispose()
}
if ($actualCaptureSourceSha256 -cne $expectedCaptureSourceSha256) { throw 'CAPTURE_SOURCE_HASH_MISMATCH' }
$sourceText = [Text.UTF8Encoding]::new($false, $true).GetString($sourceBytes)
$payload = [ordered]@{
    source = $sourceText
    expectedCaptureSourceSha256 = $expectedCaptureSourceSha256
    acceptedManifestPath = $manifestPath
    builderPath = $builderPath
    evidencePath = $evidencePath
    sshExe = 'C:\Windows\System32\OpenSSH\ssh.exe'
    identityPath = 'C:\Users\chatc\.ssh\codex-prox01-vms-ed25519'
} | ConvertTo-Json -Compress
$localBootstrap = 'import hashlib,json,sys;p=json.load(sys.stdin);s=p.pop("source");b=s.encode("utf-8");hashlib.sha256(b).hexdigest()==p["expectedCaptureSourceSha256"] or (_ for _ in ()).throw(SystemExit(73));n={"__name__":"vm105_topology_capture"};exec(compile(s,"<vm105-topology-capture>","exec"),n);raise SystemExit(n["coordinator_entry"](p,b))'
$payload | & python -I -c $localBootstrap
if ($LASTEXITCODE -ne 0) { throw 'VM105_TOPOLOGY_CAPTURE_FAILED' }
```

The coordinator must independently recompute `receiptSha256`, verify `status=PASS`, confirm `reachablePackageCount=447`, review the missing/extra closure result, and pin the headless patch path/hash before any reconstruction or DSH execution source can be accepted.

## Local verification and limits

`python scripts/test_vm105_dsh_topology_capture.py` runs 16 focused tests. They exercise a three-package synthetic pnpm closure and prove PASS plus absolute-link/escape, identity-drift, closure-mismatch, missing-headless-patch, UID/GID/writable-path blocking, fresh pinned-builder inventory equality/failure handling, exact CRLF binary-byte hashing, coordinator-independent POSIX manifest paths with relative/traversal rejection, the complete accepted manifest/builder path reaching a no-network transport stub, literal `/opt/deepseek-harness` serialization through both the CLI and actual remote payload, independent source pinning before remote compile, total/stdout/stderr bounds, canonical receipt validation, and fresh no-overwrite publication. This Windows host cannot create unprivileged native symlinks, so the fixture emulates only link snapshots. The third remote entry proved only the target-equality stop. Linux `lstat`, `readlink`, full builder inventory, `ldd`, ownership, and drift behavior remain unexecuted until a future separately authorized target capture.
