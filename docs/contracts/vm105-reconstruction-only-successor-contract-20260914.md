# VM105 reconstruction-only successor contract — 2026-09-14

## Status and authority

**DORMANT — NOT AUTHORIZED.** This contract defines one source-only reconstruction invocation. It does not authorize bundle delivery, SSH, `sudo`, staging, DSH, systemd, credential access, gateway traffic, provider traffic, service changes, or default changes.

The fixed remote bundle is `/var/tmp/omniroute-dsh-reconstruction-input-20260914`. It must already be a stable root-owned, root-group directory with no group/world write bit and contain these exact root-owned, root-group, regular non-symlink files with no group/world write bit:

| File | Raw SHA-256 |
|---|---|
| `Invoke-VM105ProductionLauncher.py` | `f2011f4d81831e4fb102f2f9e9755690418387e2f697e5ca3044417de5767c6d` |
| `Build-VM105FinalClientManifest.py` | `371481fe62d6611913f82f65b6e26b12512fda8a853a2f4591b6314f580c885f` |
| `Capture-VM105DshTopology.py` | `aa2ca52f0460279d4fd76314be96610bfd87b1bf3e6b2c92e5446983468b6190` |
| `vm105-final-client-runtime-manifest-20260913.json` | `54d117c638335edeefe43aaef0f181ea5317f7938a6861a145871a0d9e45e8dd` |
| `vm105-dsh-topology-capture-successor-20260913.json` | `86882398a06921bd351c84dbfc1eecc9abeb963912df41499ee21462b50cb47f` |

The manifest canonical SHA-256 is `4331e0e5fd9ac6f5e881a0dae941f9f07dea7b69969ee8b610071ce14cb03f8b`; the topology canonical self-hash is `cc7ca73f74bd1e515416cbff65809531fff2c052d0f7e406b9cc2efdb4c1ab20`. Source root is exactly `/`, staging root is exactly `/var/tmp/omniroute-dsh-client-final-20260913`, the durable local attempt marker is exactly `docs/evidence/vm105-dsh-reconstruction-successor-attempt-20260914.json`, and the local terminal record is exactly `docs/evidence/vm105-dsh-reconstruction-successor-20260914.json`.

Bundle delivery, fresh root-ownership/mode/hash evidence for the bundle and all five files, and review of the exact passwordless `sudo` argv remain prerequisites. They are not supplied or claimed here. The local terminal record and attempt marker must both be absent. Any occupied terminal leaf blocks before marker creation and SSH; an occupied marker blocks before SSH. On VM105, any existing object at the staging root blocks before `mkdir` or staging. A mid-stage failure retains that exact partial root for diagnosis; no retry or cleanup is permitted.

## Frozen prerequisite plan — still not authorized

One separately reviewed bundle-delivery action must copy only the five table entries from their repository paths (`scripts/Invoke-VM105ProductionLauncher.py`, `scripts/Build-VM105FinalClientManifest.py`, `scripts/Capture-VM105DshTopology.py`, and the two named files under `docs/evidence/`) to the matching basenames under the fixed bundle root. It must refuse an occupied final root, use a fixed absent sibling temporary root, create files with no-overwrite semantics, preserve the exact raw bytes, set every file to root:root with mode `0440`, set the final directory to root:root with mode `0550`, fsync the files and parent, and publish by one same-filesystem rename. Failure retains the temporary root and authorizes neither cleanup nor retry.

The required fresh read-only bundle receipt is `docs/evidence/vm105-dsh-reconstruction-bundle-successor-20260914.json`. It must bind the VM identity, exact final root, directory UID/GID/mode and stable identity, and for each of the five files its fixed basename, regular/non-symlink type, UID/GID, mode, size, stable held-descriptor/path identity, and table SHA-256. The receipt must be canonical, self-hashed, scalar-only apart from the fixed five-row table, and independently accepted before reconstruction authorization. Its file and any private temporary leaf must be absent before that capture.

The sole privileged reconstruction argv is `/usr/bin/sudo`, `-n`, `/usr/bin/python3.12`, `-I`, `-c`, the exact decoded bootstrap expression constructed below, and the exact launcher hash. The authenticated remote bootstrap is 2,072 ASCII bytes with SHA-256 `cb0281b3a3816d355a6e114f11f55776ed1f3ca6a95be3e4874d4b4b613dd171`; the complete remote shell command constructed below is 2,949 ASCII bytes with SHA-256 `b2f1c14ee67933c33bea9dde2736e384389c926d84837be0820ef73d57ca8d48`. A separate read-only sudo-policy check must prove that exact argv is allowed passwordlessly; broader Python, shell, wildcard, alternate-argument, or alternate-path authority is not accepted. These delivery, receipt, independent acceptance, and sudo-policy artifacts do not yet exist, so reconstruction dispatch remains blocked.

## Dormant exact invocation

The following command is concrete but **must not be run until separately authorized after all prerequisites above pass**. It sends a frozen authenticated bootstrap through remote `python -c`; it never asks privileged Python to import the launcher path. The remote bootstrap opens the exact launcher with `O_NOFOLLOW`, caps it at 128 KiB, verifies stable path/descriptor identity, regular type, root ownership, mode, and exact SHA-256 before compile or execution, then supplies the exact `__file__` and reconstruct-only argv.

The bootstrap becomes a SIGHUP-independent session watchdog before it forks the authenticated reconstruction into its own process group. It allows 575 seconds, sends TERM, allows five seconds, then sends KILL and performs a bounded reap. The local SSH boundary is 600 seconds with 8 MiB stdout and 64 KiB stderr caps; every local stop kills and waits for SSH, drains and closes both pipes, and treats the remote state as unproven unless one authenticated terminal receipt is received.

```powershell
$worktree = 'C:\Users\chatc\Projects\sw-localai-deepseek-harnes\.worktrees\vm105-authoritative-roadmap'
$input = [ordered]@{
    receiptPath = Join-Path $worktree 'docs\evidence\vm105-dsh-reconstruction-successor-20260914.json'
    markerPath = Join-Path $worktree 'docs\evidence\vm105-dsh-reconstruction-successor-attempt-20260914.json'
    launcherPath = Join-Path $worktree 'scripts\Invoke-VM105ProductionLauncher.py'
    launcherSha256 = 'f2011f4d81831e4fb102f2f9e9755690418387e2f697e5ca3044417de5767c6d'
    sshExe = 'C:\Windows\System32\OpenSSH\ssh.exe'
    identityPath = 'C:\Users\chatc\.ssh\codex-prox01-vms-ed25519'
} | ConvertTo-Json -Compress
$bootstrap = @'
import base64,errno,hashlib,json,os,stat,sys
p=json.load(sys.stdin)
f=None
try:
    a=os.lstat(p["launcherPath"])
    f=os.open(p["launcherPath"],os.O_RDONLY|getattr(os,"O_BINARY",0)|getattr(os,"O_CLOEXEC",0)|getattr(os,"O_NOFOLLOW",0))
    b=os.fstat(f);chunks=[];digest=hashlib.sha256();size=0
    while True:
        chunk=os.read(f,min(65536,262145-size))
        if not chunk: break
        size+=len(chunk)
        if size>262144: raise SystemExit("LOCAL_LAUNCHER_SIZE_REJECTED")
        chunks.append(chunk);digest.update(chunk)
    c=os.fstat(f);d=os.lstat(p["launcherPath"])
    identity=lambda x:(x.st_dev,x.st_ino,x.st_mode,x.st_size,x.st_mtime_ns,x.st_ctime_ns)
    if (identity(a)!=identity(b) or identity(b)!=identity(c) or identity(c)!=identity(d)
            or not stat.S_ISREG(b.st_mode) or digest.hexdigest()!=p["launcherSha256"]):
        raise SystemExit("LOCAL_LAUNCHER_REJECTED")
    source=b"".join(chunks)
finally:
    if f is not None: os.close(f)
n={"__name__":"vm105_reconstruction_coordinator","__file__":p["launcherPath"]}
exec(compile(source,p["launcherPath"],"exec"),n)
encoded=base64.b64encode(n["RECONSTRUCTION_REMOTE_BOOTSTRAP"].encode("ascii")).decode("ascii")
remote=("/usr/bin/env -i PATH=/usr/bin:/bin /usr/bin/sudo -n /usr/bin/python3.12 -I -c "
        "'import base64;exec(base64.b64decode(\""+encoded+"\"))' "+p["launcherSha256"])
command=[p["sshExe"],"-F","NUL","-T","-i",p["identityPath"],
         "-o","BatchMode=yes","-o","IdentitiesOnly=yes",
         "-o","PasswordAuthentication=no","-o","KbdInteractiveAuthentication=no",
         "-o","StrictHostKeyChecking=yes","-o","ClearAllForwardings=yes",
         "-o","ConnectTimeout=10","-o","ConnectionAttempts=1",
         "dsh@192.168.1.139",remote]
transport=lambda:n["_run_bounded_reconstruction_ssh"](command)
raise SystemExit(n["_coordinate_reconstruction_attempt"](
    p["receiptPath"],p["markerPath"],transport))
'@
$input | & python -I -c $bootstrap
if ($LASTEXITCODE -ne 0) { throw 'VM105_RECONSTRUCTION_BLOCKED_FAILED_OR_UNKNOWN' }
```

The marker is written with `O_CREAT|O_EXCL`, canonical JSON, a self-hash, `remoteState=UNPROVEN`, and `retryAuthorized=false` before SSH. After that reservation, every transport timeout, output overflow, stdout/stderr drain failure, unexpected exit, malformed receipt, and nonempty stderr produces a sanitized canonical self-hashed `UNKNOWN` terminal record with `remoteState=UNPROVEN` and `retryAuthorized=false`; stderr content is never retained. Terminal publication also uses `O_CREAT|O_EXCL`. If terminal publication fails, the durable attempt marker remains as proof that the one-shot action was consumed.

An accepted remote PASS or BLOCKED result requires empty stderr, exact canonical framing and self-hash, the fixed scalar schema and pins, and a matching exit code. PASS requires `stagingPrecheck=ABSENT`, positive file/directory counts, exactly 2,029 links, the exact sealed-entry sum, and `RETAINED_EXACT_ROOT`. BLOCKED requires an allowlisted uppercase source reason, zero returned counts, and the exact staging/cleanup combination allowed for that reason. No remote traceback, stderr content, path inventory, file inventory, link inventory, credential, or provider data is published.

The remote launcher rechecks Linux, effective UID 0, `ACCEPTED_LIVE_BINDINGS is None`, the exact reconstruction binding, the literal bundle path, stable descriptor identity, root ownership, modes, and every raw hash before checking the staging root. It then uses the existing `stage_bound_closure` → `stage_verified_topology` → sealing path. It looks up only the local `dsh` account UID/GID needed to seal staged files; it does not parse live bindings or read stdin, credentials, gateway sockets, systemd state, launch DSH, run the final client, or contact a provider. The receipt contains scalar counts only.

## Canary boundary and remaining proof

The production canary remains exactly two accepted requests—chat followed by its durable ACK—with `deniedRequests=0`. Additional-request denial is fixture evidence only; the live canary does not send a third request. Reconstruction proves neither that canary nor ordinary post-default multi-turn behavior, tool lifecycle, durable ordinary-session ACKs, persistence, profile selection, provider generation, or no-automatic-replay behavior. Those remain separate acceptance work.
