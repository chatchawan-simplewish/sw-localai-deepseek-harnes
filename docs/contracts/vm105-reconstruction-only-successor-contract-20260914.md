# VM105 reconstruction-only successor contract — 2026-09-14

## Status and authority

**DORMANT — NOT AUTHORIZED.** This contract defines one source-only reconstruction invocation. It does not authorize bundle delivery, SSH, `sudo`, staging, DSH, systemd, credential access, gateway traffic, provider traffic, service changes, or default changes.

The fixed remote bundle is `/var/tmp/omniroute-dsh-reconstruction-input-20260914`. It must already contain these exact root-owned, root-group, regular non-symlink files with no group/world write bit:

| File | Raw SHA-256 |
|---|---|
| `Invoke-VM105ProductionLauncher.py` | `9cd4fb3c4364a3471e37971345cc00ccf65bff70db930f890e101bbf48795e4d` |
| `Build-VM105FinalClientManifest.py` | `371481fe62d6611913f82f65b6e26b12512fda8a853a2f4591b6314f580c885f` |
| `Capture-VM105DshTopology.py` | `aa2ca52f0460279d4fd76314be96610bfd87b1bf3e6b2c92e5446983468b6190` |
| `vm105-final-client-runtime-manifest-20260913.json` | `54d117c638335edeefe43aaef0f181ea5317f7938a6861a145871a0d9e45e8dd` |
| `vm105-dsh-topology-capture-successor-20260913.json` | `86882398a06921bd351c84dbfc1eecc9abeb963912df41499ee21462b50cb47f` |

The manifest canonical SHA-256 is `4331e0e5fd9ac6f5e881a0dae941f9f07dea7b69969ee8b610071ce14cb03f8b`; the topology canonical self-hash is `cc7ca73f74bd1e515416cbff65809531fff2c052d0f7e406b9cc2efdb4c1ab20`. Source root is exactly `/`, staging root is exactly `/var/tmp/omniroute-dsh-client-final-20260913`, and the fresh local receipt is exactly `docs/evidence/vm105-dsh-reconstruction-successor-20260914.json`.

Bundle delivery, fresh root-ownership/mode/hash evidence for all five remote files, and review of the exact passwordless `sudo` argv remain prerequisites. They are not supplied or claimed here. The local receipt must be absent; any file, directory, symlink, or other occupied leaf blocks before SSH. On VM105, any existing object at the staging root blocks before `mkdir` or staging. A mid-stage failure retains that exact partial root for diagnosis; no retry or cleanup is permitted.

## Dormant exact invocation

The following command is concrete but **must not be run until separately authorized after all prerequisites above pass**. It uses only `dsh@192.168.1.139`, closes remote stdin, allows no forwarding or interactive authentication, bounds the single attempt to 600 seconds, stdout to 8 MiB, stderr to 64 KiB, validates the canonical receipt and its self-hash locally, and creates the local receipt with no-overwrite semantics.

```powershell
$worktree = 'C:\Users\chatc\Projects\sw-localai-deepseek-harnes\.worktrees\vm105-authoritative-roadmap'
$input = [ordered]@{
    receiptPath = Join-Path $worktree 'docs\evidence\vm105-dsh-reconstruction-successor-20260914.json'
    launcherPath = Join-Path $worktree 'scripts\Invoke-VM105ProductionLauncher.py'
    launcherSha256 = '9cd4fb3c4364a3471e37971345cc00ccf65bff70db930f890e101bbf48795e4d'
    sshExe = 'C:\Windows\System32\OpenSSH\ssh.exe'
    identityPath = 'C:\Users\chatc\.ssh\codex-prox01-vms-ed25519'
} | ConvertTo-Json -Compress
$bootstrap = @'
import errno, hashlib, json, os, re, stat, subprocess, sys, threading, time
p = json.load(sys.stdin)
receipt_path = p["receiptPath"]
try:
    os.lstat(receipt_path)
except OSError as error:
    if error.errno != errno.ENOENT:
        raise SystemExit("LOCAL_RECEIPT_PREFLIGHT_FAILED")
else:
    raise SystemExit("LOCAL_RECEIPT_OCCUPIED")

with open(p["launcherPath"], "rb") as source:
    if hashlib.sha256(source.read()).hexdigest() != p["launcherSha256"]:
        raise SystemExit("LOCAL_LAUNCHER_HASH_MISMATCH")

remote = (
    "/usr/bin/env -i PATH=/usr/bin:/bin /usr/bin/sudo -n "
    "/usr/bin/python3.12 -I "
    "/var/tmp/omniroute-dsh-reconstruction-input-20260914/Invoke-VM105ProductionLauncher.py "
    "--reconstruct-only --reconstruction-launcher-sha256 " + p["launcherSha256"]
)
command = [
    p["sshExe"], "-F", "NUL", "-T", "-i", p["identityPath"],
    "-o", "BatchMode=yes", "-o", "IdentitiesOnly=yes",
    "-o", "PasswordAuthentication=no", "-o", "KbdInteractiveAuthentication=no",
    "-o", "StrictHostKeyChecking=yes", "-o", "ClearAllForwardings=yes",
    "-o", "ConnectTimeout=10", "-o", "ConnectionAttempts=1",
    "dsh@192.168.1.139", remote,
]
process = subprocess.Popen(
    command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
    stderr=subprocess.PIPE, bufsize=0)
output = {"stdout": bytearray(), "stderr": bytearray()}
overflow = []

def drain(name, stream, limit):
    for chunk in iter(lambda: stream.read(65536), b""):
        if len(output[name]) + len(chunk) > limit:
            overflow.append(name)
            process.kill()
            return
        output[name].extend(chunk)

threads = [
    threading.Thread(target=drain, args=("stdout", process.stdout, 8 * 1024 * 1024), daemon=True),
    threading.Thread(target=drain, args=("stderr", process.stderr, 64 * 1024), daemon=True),
]
for thread in threads:
    thread.start()
deadline = time.monotonic() + 600
try:
    return_code = process.wait(timeout=max(0.001, deadline - time.monotonic()))
except subprocess.TimeoutExpired:
    process.kill()
    raise SystemExit("RECONSTRUCTION_TRANSPORT_TIMEOUT")
for thread in threads:
    thread.join(max(0, deadline - time.monotonic()))
if overflow or any(thread.is_alive() for thread in threads):
    process.kill()
    raise SystemExit("RECONSTRUCTION_TRANSPORT_LIMIT")

raw = bytes(output["stdout"])
if return_code not in (0, 1) or not raw.endswith(b"\n") or b"\n" in raw[:-1]:
    raise SystemExit("RECONSTRUCTION_TRANSPORT_FAILED")
try:
    receipt = json.loads(raw[:-1].decode("utf-8"))
except (UnicodeDecodeError, ValueError):
    raise SystemExit("RECONSTRUCTION_RECEIPT_INVALID")
keys = {
    "status", "reason", "manifestCanonicalSha256", "manifestFileSha256",
    "topologyReceiptSha256", "topologyFileSha256", "stagingPrecheck",
    "expectedPackageCount", "expectedLinkCount", "fileCount", "linkCount",
    "directoryCount", "sealedEntries", "cleanupAttempted", "cleanupResult",
    "receiptSha256",
}
canonical = lambda value: json.dumps(
    value, sort_keys=True, separators=(",", ":")).encode("utf-8")
if set(receipt) != keys or canonical(receipt) + b"\n" != raw:
    raise SystemExit("RECONSTRUCTION_RECEIPT_INVALID")
unsigned = dict(receipt)
claimed = unsigned.pop("receiptSha256")
if (not isinstance(claimed, str) or not re.fullmatch(r"[0-9a-f]{64}", claimed)
        or hashlib.sha256(canonical(unsigned)).hexdigest() != claimed):
    raise SystemExit("RECONSTRUCTION_RECEIPT_HASH_MISMATCH")
if (receipt["status"] not in ("PASS", "BLOCKED")
        or return_code != (0 if receipt["status"] == "PASS" else 1)
        or receipt["manifestCanonicalSha256"] != "4331e0e5fd9ac6f5e881a0dae941f9f07dea7b69969ee8b610071ce14cb03f8b"
        or receipt["manifestFileSha256"] != "54d117c638335edeefe43aaef0f181ea5317f7938a6861a145871a0d9e45e8dd"
        or receipt["topologyReceiptSha256"] != "cc7ca73f74bd1e515416cbff65809531fff2c052d0f7e406b9cc2efdb4c1ab20"
        or receipt["topologyFileSha256"] != "86882398a06921bd351c84dbfc1eecc9abeb963912df41499ee21462b50cb47f"
        or receipt["expectedPackageCount"] != 447
        or receipt["expectedLinkCount"] != 2029
        or receipt["cleanupAttempted"] is not False
        or receipt["cleanupResult"] not in ("UNPROVEN", "ABSENT", "RETAINED_EXACT_ROOT")):
    raise SystemExit("RECONSTRUCTION_RECEIPT_CONTRACT_MISMATCH")
if receipt["status"] == "PASS" and (
        receipt["reason"] != "NONE" or receipt["stagingPrecheck"] != "ABSENT"
        or receipt["linkCount"] != 2029
        or receipt["sealedEntries"] != receipt["fileCount"] + receipt["linkCount"]
           + receipt["directoryCount"] + 1
        or receipt["cleanupResult"] != "RETAINED_EXACT_ROOT"):
    raise SystemExit("RECONSTRUCTION_PASS_PROOF_MISMATCH")

descriptor = os.open(
    receipt_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
    getattr(os, "O_BINARY", 0), 0o600)
try:
    remaining = memoryview(raw)
    while remaining:
        written = os.write(descriptor, remaining)
        if written <= 0:
            raise OSError("short receipt write")
        remaining = remaining[written:]
    os.fsync(descriptor)
finally:
    os.close(descriptor)
raise SystemExit(return_code)
'@
$input | & python -I -c $bootstrap
if ($LASTEXITCODE -ne 0) { throw 'VM105_RECONSTRUCTION_BLOCKED_OR_FAILED' }
```

The remote launcher itself rechecks Linux, effective UID 0, `ACCEPTED_LIVE_BINDINGS is None`, the exact reconstruction binding, the literal bundle path, stable descriptor identity, root ownership, modes, and every raw hash before checking the staging root. It then uses the existing `stage_bound_closure` → `stage_verified_topology` → sealing path. It looks up only the local `dsh` account UID/GID needed to seal the staged files; it does not parse live bindings or read stdin, credentials, gateway sockets, systemd state, launch a DSH process, run the final client, or contact a provider. The receipt contains scalar counts only. No inventory is emitted.

## Canary boundary and remaining proof

The production canary remains exactly two accepted requests—chat followed by its durable ACK—with `deniedRequests=0`. Additional-request denial is fixture evidence only; the live canary does not send a third request. Reconstruction proves neither that canary nor ordinary post-default multi-turn behavior, tool lifecycle, durable ordinary-session ACKs, persistence, profile selection, provider generation, or no-automatic-replay behavior. Those remain separate acceptance work.
