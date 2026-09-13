# VM105 DSH topology capture contract — 2026-09-13

## Status and purpose

`SOURCE READY / REMOTE CAPTURE NOT AUTHORIZED OR EXECUTED`

This is the smallest new read-only capture needed to prove whether the accepted VM105 DSH installation can be reconstructed as an executable pnpm closure. It does not reuse a spent gate and does not authorize staging, package execution, provider traffic, credential access, a launch, or default activation.

## Exact target and inputs

- SSH target: `dsh@192.168.1.139`
- Installed root: `/opt/deepseek-harness`
- Traversal start: `/opt/deepseek-harness/node_modules/@deepseek-ai/dsh`
- Pinned Node runtime: `/opt/node-v24.19.0-linux-x64/bin/node`
- Target interpreter: `/usr/bin/python3.12 -I`
- Local capture source: `scripts/Capture-VM105DshTopology.py`
- Accepted manifest: `docs/evidence/vm105-final-client-runtime-manifest-20260913.json`
- Accepted manifest canonical SHA-256: `4331e0e5fd9ac6f5e881a0dae941f9f07dea7b69969ee8b610071ce14cb03f8b`
- Accepted manifest file SHA-256: `54d117c638335edeefe43aaef0f181ea5317f7938a6861a145871a0d9e45e8dd`
- Pinned builder: `scripts/Build-VM105FinalClientManifest.py`
- Pinned builder SHA-256: `371481fe62d6611913f82f65b6e26b12512fda8a853a2f4591b6314f580c885f`
- Expected accepted closure: 447 package identities and 10,026 module rows
- Intended new evidence: `docs/evidence/vm105-dsh-topology-capture-20260913.json`

## Preconditions and authority

The coordinator must issue a fresh, explicit dispatch for this exact read-only capture. Before dispatch, the local manifest and builder hashes above must still match, strict host-key verification and the pinned identity must succeed, and no other owner may be changing `/opt/deepseek-harness`. The capture is invalid if the installed tree changes while it runs.

The remote process receives the capture source, accepted manifest, and pinned builder source over stdin and executes them in memory. It performs no writes, provider requests, credential reads, Node/DSH package execution, runtime launch, service change, namespace change, cgroup change, or profile/default mutation. The pinned builder invokes `ldd` only to revalidate the accepted Node shared-library closure; the dispatch gives it a fixed `/usr/bin:/bin` PATH. SSH is only the transport used by the coordinator outside the capture process.

## Fail-closed checks and receipt

The source validates the pinned builder hash, executes that exact source under a non-main isolated namespace, and calls its `build_manifest` against `/opt/deepseek-harness/node_modules` and the pinned Node path. That fresh builder run captures the complete inventory twice, including all package identities, 10,026 module bytes, entrypoints, configuration bundles, the Node binary, and its runtime libraries. The capture requires the fresh unsigned canonical JSON to equal the supplied accepted unsigned manifest byte for byte and to hash to `4331e0e5fd9ac6f5e881a0dae941f9f07dea7b69969ee8b610071ce14cb03f8b` before topology traversal begins. Any builder or inventory failure becomes the secret-free `FRESH_MANIFEST_RESCAN_FAILED` or `FRESH_MANIFEST_MISMATCH` reason.

After full-manifest revalidation, the source traverses every present dependency, optional-dependency, and peer-dependency link reachable from `@deepseek-ai/dsh`.

Every recorded link contains its install-root-relative logical path, raw relative target, resolved install-root-relative canonical package path, stable `lstat` identity, root owner, package name/version, and stable `package.json` SHA-256. Absolute or escaping links, changing identities, missing required dependencies, non-root-owned links or real paths, group/world-writable real paths, and any missing or extra canonical package identity block the receipt. Nominal symlink mode bits are recorded but are not treated as writable-file permissions.

The receipt also records the exact reachable logical and canonical paths, stable identity, and SHA-256 of `@deepseek-ai/dsh-headless/cordis.patch.yml`. A PASS receipt contains a `receiptSha256` calculated over canonical JSON before that field is inserted. BLOCKED receipts use the same self-hash format and contain no path-dependent traceback.

## Exact coordinator dispatch command

Run only after the fresh capture dispatch is granted. The command keeps the target read-only and persists the single canonical stdout receipt locally as the new evidence file.

```powershell
$worktree = 'C:\Users\chatc\Projects\sw-localai-deepseek-harnes\.worktrees\vm105-authoritative-roadmap'
$sourcePath = Join-Path $worktree 'scripts\Capture-VM105DshTopology.py'
$manifestPath = Join-Path $worktree 'docs\evidence\vm105-final-client-runtime-manifest-20260913.json'
$builderPath = Join-Path $worktree 'scripts\Build-VM105FinalClientManifest.py'
$evidencePath = Join-Path $worktree 'docs\evidence\vm105-dsh-topology-capture-20260913.json'
$payload = [ordered]@{
    source = [IO.File]::ReadAllText($sourcePath)
    installRoot = '/opt/deepseek-harness'
    acceptedManifest = [IO.File]::ReadAllText($manifestPath) | ConvertFrom-Json
    builderSource = [IO.File]::ReadAllText($builderPath)
} | ConvertTo-Json -Depth 100 -Compress
$bootstrap = 'import json,sys;p=json.load(sys.stdin);s=p.pop("source");n={"__name__":"vm105_topology_capture"};exec(compile(s,"<vm105-topology-capture>","exec"),n);n["remote_entry"](p)'
$bootstrap64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($bootstrap))
$remoteCommand = "/usr/bin/env -i PATH=/usr/bin:/bin /usr/bin/python3.12 -I -c 'import base64;exec(base64.b64decode(`"$bootstrap64`"))'"
$previousEncoding = $OutputEncoding
$OutputEncoding = [Text.UTF8Encoding]::new($false)
try {
    $receipt = $payload | & 'C:\Windows\System32\OpenSSH\ssh.exe' -T `
        -i 'C:\Users\chatc\.ssh\codex-prox01-vms-ed25519' `
        -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=10 `
        'dsh@192.168.1.139' $remoteCommand
    if ($LASTEXITCODE -ne 0) { throw 'VM105_TOPOLOGY_CAPTURE_TRANSPORT_FAILED' }
} finally {
    $OutputEncoding = $previousEncoding
}
[IO.File]::WriteAllText($evidencePath, $receipt, [Text.UTF8Encoding]::new($false))
$receipt
```

The coordinator must independently recompute `receiptSha256`, verify `status=PASS`, confirm `reachablePackageCount=447`, review the missing/extra closure result, and pin the headless patch path/hash before any reconstruction or DSH execution source can be accepted.

## Local verification and limits

`python scripts/test_vm105_dsh_topology_capture.py` exercises a three-package synthetic pnpm closure and proves PASS plus absolute-link/escape, identity-drift, closure-mismatch, missing-headless-patch, ownership/writable-path blocking, and fresh pinned-builder inventory equality/failure handling. This Windows host cannot create unprivileged native symlinks, so the fixture emulates only link snapshots; Linux `lstat`, `readlink`, full builder inventory, `ldd`, ownership, and drift behavior remain unexecuted until the newly authorized target capture.
