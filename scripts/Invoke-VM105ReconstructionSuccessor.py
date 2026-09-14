"""Delivery-only Phase 13 successor for the dormant VM105 reconstruction."""

import argparse
import base64
import errno
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import stat
import subprocess
import threading


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
GENERATION = "phase13-20260915"
BUNDLE_ROOT = "/var/tmp/omniroute-dsh-reconstruction-input-20260914"
TEMP_BUNDLE_ROOT = "/var/tmp/.omniroute-dsh-reconstruction-input-20260914.tmp"
STAGING_ROOT = "/var/tmp/omniroute-dsh-client-final-20260913"
LAUNCHER_SHA256 = "f2011f4d81831e4fb102f2f9e9755690418387e2f697e5ca3044417de5767c6d"
RECONSTRUCTION_BOOTSTRAP_BYTES = 2072
RECONSTRUCTION_BOOTSTRAP_SHA256 = "cb0281b3a3816d355a6e114f11f55776ed1f3ca6a95be3e4874d4b4b613dd171"
RECONSTRUCTION_REMOTE_COMMAND_BYTES = 2949
RECONSTRUCTION_REMOTE_COMMAND_SHA256 = "b2f1c14ee67933c33bea9dde2736e384389c926d84837be0820ef73d57ca8d48"
SSH_EXE = r"C:\Windows\System32\OpenSSH\ssh.exe"
SSH_IDENTITY = r"C:\Users\chatc\.ssh\codex-prox01-vms-ed25519"
SSH_TARGET = "dsh@192.168.1.139"
SSH_COMMAND_PREFIX = (
    SSH_EXE, "-F", "NUL", "-T", "-i", SSH_IDENTITY,
    "-o", "BatchMode=yes", "-o", "IdentitiesOnly=yes",
    "-o", "PasswordAuthentication=no", "-o", "KbdInteractiveAuthentication=no",
    "-o", "StrictHostKeyChecking=yes", "-o", "ClearAllForwardings=yes",
    "-o", "ConnectTimeout=10", "-o", "ConnectionAttempts=1", "--", SSH_TARGET)

BUNDLE_FILES = (
    {"source": "scripts/Build-VM105FinalClientManifest.py",
     "basename": "Build-VM105FinalClientManifest.py",
     "sha256": "371481fe62d6611913f82f65b6e26b12512fda8a853a2f4591b6314f580c885f"},
    {"source": "scripts/Capture-VM105DshTopology.py",
     "basename": "Capture-VM105DshTopology.py",
     "sha256": "aa2ca52f0460279d4fd76314be96610bfd87b1bf3e6b2c92e5446983468b6190"},
    {"source": "scripts/Invoke-VM105ProductionLauncher.py",
     "basename": "Invoke-VM105ProductionLauncher.py", "sha256": LAUNCHER_SHA256},
    {"source": "docs/evidence/vm105-dsh-topology-capture-successor-20260913.json",
     "basename": "vm105-dsh-topology-capture-successor-20260913.json",
     "sha256": "86882398a06921bd351c84dbfc1eecc9abeb963912df41499ee21462b50cb47f"},
    {"source": "docs/evidence/vm105-final-client-runtime-manifest-20260913.json",
     "basename": "vm105-final-client-runtime-manifest-20260913.json",
     "sha256": "54d117c638335edeefe43aaef0f181ea5317f7938a6861a145871a0d9e45e8dd"},
)

DELIVERY_ATTEMPT_PATH = REPOSITORY_ROOT / "docs/evidence/vm105-dsh-reconstruction-bundle-delivery-phase13-attempt-20260915.json"
DELIVERY_TERMINAL_PATH = REPOSITORY_ROOT / "docs/evidence/vm105-dsh-reconstruction-bundle-delivery-phase13-20260915.json"
BUNDLE_RECEIPT_PATH = REPOSITORY_ROOT / "docs/evidence/vm105-dsh-reconstruction-bundle-phase13-20260915.json"
SUDO_RECEIPT_PATH = REPOSITORY_ROOT / "docs/evidence/vm105-dsh-reconstruction-sudo-policy-phase13-20260915.json"
DISPATCH_ATTEMPT_PATH = REPOSITORY_ROOT / "docs/evidence/vm105-dsh-reconstruction-phase13-attempt-20260915.json"
DISPATCH_TERMINAL_PATH = REPOSITORY_ROOT / "docs/evidence/vm105-dsh-reconstruction-phase13-20260915.json"
ALL_EVIDENCE_PATHS = (
    DELIVERY_ATTEMPT_PATH, DELIVERY_TERMINAL_PATH, BUNDLE_RECEIPT_PATH,
    SUDO_RECEIPT_PATH, DISPATCH_ATTEMPT_PATH, DISPATCH_TERMINAL_PATH,
)
EVIDENCE_PATH_BINDING = {
    "deliveryAttemptPath": DELIVERY_ATTEMPT_PATH.relative_to(REPOSITORY_ROOT).as_posix(),
    "deliveryTerminalPath": DELIVERY_TERMINAL_PATH.relative_to(REPOSITORY_ROOT).as_posix(),
    "bundleReceiptPath": BUNDLE_RECEIPT_PATH.relative_to(REPOSITORY_ROOT).as_posix(),
    "sudoReceiptPath": SUDO_RECEIPT_PATH.relative_to(REPOSITORY_ROOT).as_posix(),
    "dispatchAttemptPath": DISPATCH_ATTEMPT_PATH.relative_to(REPOSITORY_ROOT).as_posix(),
    "dispatchTerminalPath": DISPATCH_TERMINAL_PATH.relative_to(REPOSITORY_ROOT).as_posix(),
}


def canonical_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def canonical_line(value):
    return canonical_bytes(value) + b"\n"


def signed(value):
    value = dict(value)
    value["receiptSha256"] = hashlib.sha256(canonical_bytes(value)).hexdigest()
    return value


def _binding_sha256(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


BUNDLE_DELIVERY_BINDING = {
    "generation": GENERATION, **EVIDENCE_PATH_BINDING,
    "bundleRoot": BUNDLE_ROOT, "temporaryRoot": TEMP_BUNDLE_ROOT,
    "files": [{"basename": row["basename"], "sha256": row["sha256"]}
              for row in BUNDLE_FILES],
}
BUNDLE_DELIVERY_BINDING_SHA256 = _binding_sha256(BUNDLE_DELIVERY_BINDING)
PREREQUISITE_CAPTURE_BINDING = {
    "generation": GENERATION, **EVIDENCE_PATH_BINDING,
    "bundleRoot": BUNDLE_ROOT, "expectedFileCount": 5,
    "launcherSha256": LAUNCHER_SHA256,
}
PREREQUISITE_CAPTURE_BINDING_SHA256 = _binding_sha256(PREREQUISITE_CAPTURE_BINDING)
RECONSTRUCTION_DISPATCH_BINDING = {
    "generation": GENERATION, **EVIDENCE_PATH_BINDING,
    "bundleRoot": BUNDLE_ROOT, "stagingRoot": STAGING_ROOT,
    "launcherSha256": LAUNCHER_SHA256,
}
RECONSTRUCTION_DISPATCH_BINDING_SHA256 = _binding_sha256(RECONSTRUCTION_DISPATCH_BINDING)

# Delivery alone is bound. Later reviewed source changes must bind every other gate.
ACCEPTED_BUNDLE_DELIVERY_BINDING_SHA256 = "392eb6e28ef879eee3348f912fb8ff66a8a692ea749f91bc399cc5aa0b6676ee"
ACCEPTED_PREREQUISITE_CAPTURE_BINDING_SHA256 = None
ACCEPTED_RECONSTRUCTION_DISPATCH_BINDING_SHA256 = None
ACCEPTED_BUNDLE_RECEIPT_RAW_SHA256 = None
ACCEPTED_BUNDLE_RECEIPT_SELF_SHA256 = None
ACCEPTED_SUDO_RECEIPT_RAW_SHA256 = None
ACCEPTED_SUDO_RECEIPT_SELF_SHA256 = None
ACCEPTED_SUDO_VERSION = None
ACCEPTED_LIVE_BINDINGS = None


class PrerequisiteBlocked(RuntimeError):
    pass


DELIVERY_REMOTE_BOOTSTRAP = r'''import base64,ctypes,errno,hashlib,json,os,re,stat,sys
F="/var/tmp/omniroute-dsh-reconstruction-input-20260914"
T="/var/tmp/.omniroute-dsh-reconstruction-input-20260914.tmp"
P="/var/tmp"
H={"Build-VM105FinalClientManifest.py":"371481fe62d6611913f82f65b6e26b12512fda8a853a2f4591b6314f580c885f","Capture-VM105DshTopology.py":"aa2ca52f0460279d4fd76314be96610bfd87b1bf3e6b2c92e5446983468b6190","Invoke-VM105ProductionLauncher.py":"f2011f4d81831e4fb102f2f9e9755690418387e2f697e5ca3044417de5767c6d","vm105-dsh-topology-capture-successor-20260913.json":"86882398a06921bd351c84dbfc1eecc9abeb963912df41499ee21462b50cb47f","vm105-final-client-runtime-manifest-20260913.json":"54d117c638335edeefe43aaef0f181ea5317f7938a6861a145871a0d9e45e8dd"}
def canon(v):return json.dumps(v,sort_keys=True,separators=(",",":")).encode()
def out(v):
 v=dict(v);v["receiptSha256"]=hashlib.sha256(canon(v)).hexdigest();sys.stdout.buffer.write(canon(v)+b"\n")
renamed=False
try:
 try:os.lstat(F);raise RuntimeError("FINAL_ROOT_OCCUPIED")
 except FileNotFoundError:pass
 try:os.lstat(T);raise RuntimeError("TEMP_ROOT_OCCUPIED")
 except FileNotFoundError:pass
 p=json.load(sys.stdin)
 if set(p)!={"bundleRoot","files","temporaryRoot"} or p["bundleRoot"]!=F or p["temporaryRoot"]!=T or len(p["files"])!=5:raise RuntimeError("DELIVERY_FRAME_REJECTED")
 pins=[(x.get("basename"),x.get("sha256")) for x in p["files"] if isinstance(x,dict)]
 if pins!=sorted(H.items()):raise RuntimeError("DELIVERY_FRAME_REJECTED")
 os.mkdir(T,0o550)
 for x in p["files"]:
  if set(x)!={"basename","content","sha256"} or "/" in x["basename"] or "\\" in x["basename"]:raise RuntimeError("DELIVERY_FRAME_REJECTED")
  raw=base64.b64decode(x["content"],validate=True)
  if hashlib.sha256(raw).hexdigest()!=x["sha256"]:raise RuntimeError("DELIVERY_HASH_REJECTED")
  path=T+"/"+x["basename"]
  fd=os.open(path,os.O_RDWR|os.O_CREAT|os.O_EXCL|getattr(os,"O_NOFOLLOW",0)|getattr(os,"O_CLOEXEC",0),0o440)
  try:
   view=memoryview(raw)
   while view:
    n=os.write(fd,view)
    if n<=0:raise OSError("short write")
    view=view[n:]
   os.fchown(fd,0,0);os.fchmod(fd,0o440);os.fsync(fd);os.lseek(fd,0,0)
   h=hashlib.sha256();size=0
   while True:
    b=os.read(fd,65536)
    if not b:break
    size+=len(b);h.update(b)
   s=os.fstat(fd)
   if size!=len(raw) or h.hexdigest()!=x["sha256"] or s.st_uid!=0 or s.st_gid!=0 or stat.S_IMODE(s.st_mode)!=0o440:raise RuntimeError("DELIVERY_VERIFY_FAILED")
  finally:os.close(fd)
 d=os.open(T,os.O_RDONLY|getattr(os,"O_DIRECTORY",0)|getattr(os,"O_NOFOLLOW",0)|getattr(os,"O_CLOEXEC",0))
 try:os.fchown(d,0,0);os.fchmod(d,0o550);os.fsync(d)
 finally:os.close(d)
 libc=ctypes.CDLL(None,use_errno=True);renameat2=getattr(libc,"renameat2",None)
 if renameat2 is None:raise RuntimeError("ATOMIC_PUBLISH_UNSUPPORTED")
 if renameat2(-100,T.encode(),-100,F.encode(),1)!=0:
  raise RuntimeError("FINAL_ROOT_OCCUPIED" if ctypes.get_errno()==errno.EEXIST else "ATOMIC_PUBLISH_FAILED")
 renamed=True
 parent=os.open(P,os.O_RDONLY|getattr(os,"O_DIRECTORY",0)|getattr(os,"O_CLOEXEC",0))
 try:os.fsync(parent)
 finally:os.close(parent)
 out({"status":"PASS","reason":"NONE","finalRoot":F,"temporaryRoot":T,"fileCount":5,"renameCompleted":True,"parentFsync":True})
except BaseException as e:
 reason=str(e) if re.fullmatch(r"[A-Z0-9_]+",str(e)) else "DELIVERY_FAILED"
 out({"status":"UNKNOWN" if renamed else "BLOCKED","reason":reason,"finalRoot":F,"temporaryRoot":T,"fileCount":0,"renameCompleted":renamed,"parentFsync":False})
 raise SystemExit(2 if renamed else 1)
'''


def _delivery_remote_command():
    encoded = base64.b64encode(DELIVERY_REMOTE_BOOTSTRAP.encode("ascii")).decode("ascii")
    return ("/usr/bin/env -i PATH=/usr/bin:/bin /usr/bin/sudo -n /usr/bin/python3.12 -I -c "
            "'import base64;exec(base64.b64decode(\"" + encoded + "\"))'")


def _require_authority(provided, accepted, expected, reason):
    if accepted is None or provided != accepted or accepted != expected:
        raise PrerequisiteBlocked(reason)


def _require_absent(paths, lstat):
    for path in paths:
        try:
            lstat(path)
        except OSError as error:
            if error.errno == errno.ENOENT:
                continue
            raise PrerequisiteBlocked("EVIDENCE_LEAF_UNPROVEN") from None
        raise PrerequisiteBlocked("EVIDENCE_LEAF_OCCUPIED")


def _publish_exclusive(path, raw):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                         getattr(os, "O_BINARY", 0), 0o600)
    try:
        view = memoryview(raw)
        while view:
            count = os.write(descriptor, view)
            if count <= 0:
                raise OSError("short evidence write")
            view = view[count:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def read_stable_source(path, expected_sha256, *, lstat=os.lstat,
                       open_file=os.open, fstat=os.fstat, read=os.read,
                       close=os.close, max_bytes=8 * 1024 * 1024):
    descriptor = None
    try:
        before = lstat(path)
        if not stat.S_ISREG(before.st_mode):
            raise PrerequisiteBlocked("LOCAL_SOURCE_REJECTED")
        descriptor = open_file(
            path, os.O_RDONLY | getattr(os, "O_BINARY", 0) |
            getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0))
        opened = fstat(descriptor)
        chunks = []
        digest = hashlib.sha256()
        size = 0
        while True:
            chunk = read(descriptor, min(65536, max_bytes + 1 - size))
            if not chunk:
                break
            size += len(chunk)
            if size > max_bytes:
                raise PrerequisiteBlocked("LOCAL_SOURCE_REJECTED")
            chunks.append(chunk)
            digest.update(chunk)
        after_fd = fstat(descriptor)
        after_path = lstat(path)
        path_identity = lambda value: (
            value.st_dev, value.st_ino, value.st_mode, value.st_size,
            value.st_mtime_ns)
        descriptor_identity = lambda value: path_identity(value) + (value.st_ctime_ns,)
        if (path_identity(before) != path_identity(after_path) or
                path_identity(before) != path_identity(opened) or
                descriptor_identity(opened) != descriptor_identity(after_fd) or
                digest.hexdigest() != expected_sha256):
            raise PrerequisiteBlocked("LOCAL_SOURCE_REJECTED")
        return b"".join(chunks)
    except PrerequisiteBlocked:
        raise
    except (OSError, ValueError):
        raise PrerequisiteBlocked("LOCAL_SOURCE_REJECTED") from None
    finally:
        if descriptor is not None:
            close(descriptor)


def _validate_signed_line(raw, expected_keys):
    if not isinstance(raw, bytes) or not raw.endswith(b"\n") or b"\n" in raw[:-1]:
        raise ValueError()
    value = json.loads(raw[:-1].decode("utf-8"))
    if not isinstance(value, dict) or set(value) != set(expected_keys) | {"receiptSha256"} or canonical_line(value) != raw:
        raise ValueError()
    unsigned = dict(value)
    claimed = unsigned.pop("receiptSha256")
    if not isinstance(claimed, str) or not re.fullmatch(r"[0-9a-f]{64}", claimed) or hashlib.sha256(canonical_bytes(unsigned)).hexdigest() != claimed:
        raise ValueError()
    return value


def _delivery_terminal(status, reason, remote_state, remote_sha=""):
    return signed({
        "status": status, "reason": reason, "remoteState": remote_state,
        "retryAuthorized": False, "bindingSha256": BUNDLE_DELIVERY_BINDING_SHA256,
        "remoteReceiptSha256": remote_sha,
    })


def deliver_bundle(authority_sha256, transport, *, read_source, lstat=os.lstat,
                   publish=_publish_exclusive):
    _require_authority(authority_sha256, ACCEPTED_BUNDLE_DELIVERY_BINDING_SHA256,
                       BUNDLE_DELIVERY_BINDING_SHA256,
                       "BUNDLE_DELIVERY_NOT_EXECUTABLE")
    _require_absent(ALL_EVIDENCE_PATHS, lstat)
    files = []
    for row in BUNDLE_FILES:
        raw = read_source(REPOSITORY_ROOT / row["source"], row["sha256"])
        files.append({"basename": row["basename"], "sha256": row["sha256"],
                      "content": base64.b64encode(raw).decode("ascii")})
    frame = canonical_line({"bundleRoot": BUNDLE_ROOT, "temporaryRoot": TEMP_BUNDLE_ROOT,
                            "files": files})
    attempt = signed({"status": "ATTEMPTED", "reason": "DELIVERY_RESERVED",
                      "remoteState": "UNPROVEN", "retryAuthorized": False,
                      "bindingSha256": BUNDLE_DELIVERY_BINDING_SHA256})
    publish(DELIVERY_ATTEMPT_PATH, canonical_line(attempt))
    try:
        return_code, stdout, stderr = transport(
            list(SSH_COMMAND_PREFIX) + [_delivery_remote_command()], frame)
        remote = _validate_signed_line(stdout, {
            "status", "reason", "finalRoot", "temporaryRoot", "fileCount",
            "renameCompleted", "parentFsync"})
        valid = (not stderr and remote["finalRoot"] == BUNDLE_ROOT and
                 remote["temporaryRoot"] == TEMP_BUNDLE_ROOT and
                 remote["status"] == "PASS" and remote["reason"] == "NONE" and
                 remote["fileCount"] == 5 and remote["renameCompleted"] is True and
                 remote["parentFsync"] is True and return_code == 0)
        terminal = (_delivery_terminal("PASS", "NONE", "PROVEN_PASS", remote["receiptSha256"])
                    if valid else _delivery_terminal("UNKNOWN", "REMOTE_DELIVERY_UNPROVEN", "UNPROVEN"))
    except Exception:
        terminal = _delivery_terminal("UNKNOWN", "LOCAL_TRANSPORT_UNKNOWN", "UNPROVEN")
    publish(DELIVERY_TERMINAL_PATH, canonical_line(terminal))
    return 0 if terminal["status"] == "PASS" else 1


BUNDLE_CAPTURE_REMOTE_BOOTSTRAP = r'''import hashlib,json,os,stat,sys
R="/var/tmp/omniroute-dsh-reconstruction-input-20260914"
N=["Build-VM105FinalClientManifest.py","Capture-VM105DshTopology.py","Invoke-VM105ProductionLauncher.py","vm105-dsh-topology-capture-successor-20260913.json","vm105-final-client-runtime-manifest-20260913.json"]
H={"Build-VM105FinalClientManifest.py":"371481fe62d6611913f82f65b6e26b12512fda8a853a2f4591b6314f580c885f","Capture-VM105DshTopology.py":"aa2ca52f0460279d4fd76314be96610bfd87b1bf3e6b2c92e5446983468b6190","Invoke-VM105ProductionLauncher.py":"f2011f4d81831e4fb102f2f9e9755690418387e2f697e5ca3044417de5767c6d","vm105-dsh-topology-capture-successor-20260913.json":"86882398a06921bd351c84dbfc1eecc9abeb963912df41499ee21462b50cb47f","vm105-final-client-runtime-manifest-20260913.json":"54d117c638335edeefe43aaef0f181ea5317f7938a6861a145871a0d9e45e8dd"}
def ident(x):return (x.st_dev,x.st_ino,x.st_mode,x.st_size,x.st_mtime_ns,x.st_ctime_ns,x.st_uid,x.st_gid)
def canon(v):return json.dumps(v,sort_keys=True,separators=(",",":")).encode()
def held(path,flags,dir_fd=None,limit=8388608):
 a=os.stat(path,dir_fd=dir_fd,follow_symlinks=False);f=os.open(path,flags|getattr(os,"O_NOFOLLOW",0)|getattr(os,"O_CLOEXEC",0),dir_fd=dir_fd)
 try:
  b=os.fstat(f);h=hashlib.sha256();size=0
  while stat.S_ISREG(b.st_mode):
   q=os.read(f,min(65536,limit+1-size))
   if not q:break
   size+=len(q)
   if size>limit:raise RuntimeError("BUNDLE_FILE_REJECTED")
   h.update(q)
  c=os.fstat(f);z=os.stat(path,dir_fd=dir_fd,follow_symlinks=False)
  if ident(a)!=ident(b) or ident(b)!=ident(c) or ident(c)!=ident(z):raise RuntimeError("BUNDLE_IDENTITY_DRIFT")
  return f,b,h.hexdigest(),size
 except BaseException:
  os.close(f);raise
root,b,_,_=held(R,os.O_RDONLY|getattr(os,"O_DIRECTORY",0))
try:
 if not stat.S_ISDIR(b.st_mode) or b.st_uid!=0 or b.st_gid!=0 or stat.S_IMODE(b.st_mode)!=0o550:raise RuntimeError("BUNDLE_ROOT_REJECTED")
 if sorted(os.listdir(root))!=N:raise RuntimeError("BUNDLE_MEMBERSHIP_REJECTED")
 rows=[]
 for name in N:
  f,s,digest,size=held(name,os.O_RDONLY,root)
  try:
   if not stat.S_ISREG(s.st_mode) or s.st_uid!=0 or s.st_gid!=0 or stat.S_IMODE(s.st_mode)!=0o440 or digest!=H[name] or size!=s.st_size:raise RuntimeError("BUNDLE_FILE_REJECTED")
   rows.append({"basename":name,"type":"regular","symlink":False,"device":s.st_dev,"inode":s.st_ino,"mode":stat.S_IMODE(s.st_mode),"uid":s.st_uid,"gid":s.st_gid,"size":s.st_size,"mtimeNs":s.st_mtime_ns,"ctimeNs":s.st_ctime_ns,"sha256":digest})
  finally:os.close(f)
 end=os.fstat(root);path_end=os.stat(R,follow_symlinks=False)
 if ident(b)!=ident(end) or ident(end)!=ident(path_end):raise RuntimeError("BUNDLE_IDENTITY_DRIFT")
 machine,ms,machine_hash,machine_size=held("/etc/machine-id",os.O_RDONLY,limit=4096)
 try:
  if not stat.S_ISREG(ms.st_mode) or machine_size<1:raise RuntimeError("VM_IDENTITY_REJECTED")
 finally:os.close(machine)
 v={"status":"PASS","reason":"NONE","vmHostname":os.uname().nodename,"vmMachineIdSha256":machine_hash,"bundleRoot":R,"bundleDevice":b.st_dev,"bundleInode":b.st_ino,"bundleMode":stat.S_IMODE(b.st_mode),"bundleUid":b.st_uid,"bundleGid":b.st_gid,"bundleSize":b.st_size,"bundleMtimeNs":b.st_mtime_ns,"bundleCtimeNs":b.st_ctime_ns,"expectedFileCount":5,"fileCount":5,"files":rows}
 v["receiptSha256"]=hashlib.sha256(canon(v)).hexdigest();sys.stdout.buffer.write(canon(v)+b"\n")
finally:os.close(root)
'''


def _capture_remote_command():
    encoded = base64.b64encode(BUNDLE_CAPTURE_REMOTE_BOOTSTRAP.encode("ascii")).decode("ascii")
    return ("/usr/bin/env -i PATH=/usr/bin:/bin /usr/bin/python3.12 -I -c "
            "'import base64;exec(base64.b64decode(\"" + encoded + "\"))'")


SUDO_FULL_QUERY_BOOTSTRAP = r'''import json,re,subprocess,sys
def run(argv):
 p=subprocess.run(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=20,check=False)
 if p.returncode!=0 or p.stderr or len(p.stdout)>262144:raise SystemExit(74)
 return p.stdout.decode("utf-8")
version_output=run(["/usr/bin/sudo","-V"])
match=re.fullmatch(r"Sudo version ([0-9]+\.[0-9]+\.[0-9]+(?:p[0-9]+)?)",version_output.splitlines()[0])
if match is None:raise SystemExit(74)
policy=run(["/usr/bin/sudo","-n","-ll"])
value={"sudoVersion":match.group(1),"policy":policy}
sys.stdout.write(json.dumps(value,sort_keys=True,separators=(",",":"))+"\n")
'''


def _sudo_full_query_command():
    encoded = base64.b64encode(SUDO_FULL_QUERY_BOOTSTRAP.encode("ascii")).decode("ascii")
    remote = ("/usr/bin/env -i PATH=/usr/bin:/bin /usr/bin/python3.12 -I -c "
              "'import base64;exec(base64.b64decode(\"" + encoded + "\"))'")
    return list(SSH_COMMAND_PREFIX) + [remote]


def _load_immutable_launcher(read_source=read_stable_source):
    path = REPOSITORY_ROOT / "scripts/Invoke-VM105ProductionLauncher.py"
    source = read_source(path, LAUNCHER_SHA256)
    namespace = {"__name__": "vm105_immutable_reconstruction_launcher", "__file__": str(path)}
    exec(compile(source, str(path), "exec"), namespace)
    required = {"RECONSTRUCTION_BINDING", "RECONSTRUCTION_REMOTE_BOOTSTRAP",
                "_run_bounded_reconstruction_ssh", "_coordinate_reconstruction_attempt"}
    if not required.issubset(namespace) or namespace.get("ACCEPTED_LIVE_BINDINGS") is not None:
        raise PrerequisiteBlocked("IMMUTABLE_LAUNCHER_REJECTED")
    binding = dict(namespace["RECONSTRUCTION_BINDING"])
    if (binding.get("bundleRoot") != BUNDLE_ROOT or binding.get("stagingRoot") != STAGING_ROOT or
            binding.get("launcherPath") != BUNDLE_ROOT + "/Invoke-VM105ProductionLauncher.py"):
        raise PrerequisiteBlocked("IMMUTABLE_LAUNCHER_REJECTED")
    return namespace


def _reconstruction_command_details(load_launcher=_load_immutable_launcher):
    launcher = load_launcher()
    bootstrap = launcher["RECONSTRUCTION_REMOTE_BOOTSTRAP"].encode("ascii")
    if (len(bootstrap) != RECONSTRUCTION_BOOTSTRAP_BYTES or
            hashlib.sha256(bootstrap).hexdigest() != RECONSTRUCTION_BOOTSTRAP_SHA256):
        raise PrerequisiteBlocked("RECONSTRUCTION_BOOTSTRAP_REJECTED")
    encoded = base64.b64encode(bootstrap).decode("ascii")
    expression = 'import base64;exec(base64.b64decode("' + encoded + '"))'
    target_argv = ["/usr/bin/python3.12", "-I", "-c", expression, LAUNCHER_SHA256]
    remote = ("/usr/bin/env -i PATH=/usr/bin:/bin /usr/bin/sudo -n " +
              " ".join(shlex.quote(value) for value in target_argv))
    if (len(remote.encode("ascii")) != RECONSTRUCTION_REMOTE_COMMAND_BYTES or
            hashlib.sha256(remote.encode("ascii")).hexdigest() != RECONSTRUCTION_REMOTE_COMMAND_SHA256):
        raise PrerequisiteBlocked("RECONSTRUCTION_COMMAND_REJECTED")
    sudo_query = "/usr/bin/sudo -n -l -- " + " ".join(shlex.quote(value) for value in target_argv)
    return {
        "launcher": launcher, "remoteCommand": remote,
        "dispatchCommand": list(SSH_COMMAND_PREFIX) + [remote],
        "sudoExactQueryCommand": list(SSH_COMMAND_PREFIX) + [sudo_query],
        "sudoFullQueryCommand": _sudo_full_query_command(),
        "sudoPolicyCommand": " ".join(target_argv),
        "targetArgc": len(target_argv),
        "targetArgvSha256": hashlib.sha256(canonical_bytes(target_argv)).hexdigest(),
        "bootstrapBytes": len(bootstrap), "bootstrapSha256": hashlib.sha256(bootstrap).hexdigest(),
    }


BUNDLE_RECEIPT_KEYS = {
    "status", "reason", "vmHostname", "vmMachineIdSha256", "bundleRoot",
    "bundleDevice", "bundleInode", "bundleMode", "bundleUid", "bundleGid",
    "bundleSize", "bundleMtimeNs", "bundleCtimeNs", "expectedFileCount",
    "fileCount", "files", "receiptSha256",
}
BUNDLE_FILE_KEYS = {
    "basename", "type", "symlink", "device", "inode", "mode", "uid", "gid",
    "size", "mtimeNs", "ctimeNs", "sha256",
}


def validate_bundle_receipt(raw):
    try:
        value = _validate_signed_line(raw, BUNDLE_RECEIPT_KEYS - {"receiptSha256"})
        rows = value["files"]
        top_integers = (
            "bundleDevice", "bundleInode", "bundleMode", "bundleUid", "bundleGid",
            "bundleSize", "bundleMtimeNs", "bundleCtimeNs", "expectedFileCount", "fileCount")
        if (any(type(value[key]) is not int or value[key] < 0 for key in top_integers) or
                not isinstance(rows, list) or len(rows) != 5 or
                not all(isinstance(row, dict) for row in rows)):
            raise ValueError()
        expected = [(row["basename"], row["sha256"]) for row in BUNDLE_FILES]
        actual = [(row.get("basename"), row.get("sha256")) for row in rows]
        integer_keys = ("device", "inode", "mode", "uid", "gid", "size", "mtimeNs", "ctimeNs")
        if (value["status"] != "PASS" or value["reason"] != "NONE" or
                value["bundleRoot"] != BUNDLE_ROOT or value["bundleMode"] != 0o550 or
                value["bundleUid"] != 0 or value["bundleGid"] != 0 or
                value["expectedFileCount"] != 5 or value["fileCount"] != 5 or
                not isinstance(value["vmHostname"], str) or not value["vmHostname"] or
                not re.fullmatch(r"[0-9a-f]{64}", value["vmMachineIdSha256"]) or
                actual != expected):
            raise ValueError()
        for row in rows:
            if (set(row) != BUNDLE_FILE_KEYS or row["type"] != "regular" or
                    row["symlink"] is not False or row["mode"] != 0o440 or
                    row["uid"] != 0 or row["gid"] != 0 or
                    any(type(row[key]) is not int or row[key] < 0 for key in integer_keys)):
                raise ValueError()
        return value
    except (KeyError, TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError):
        raise PrerequisiteBlocked("BUNDLE_RECEIPT_REJECTED") from None


def _parse_full_sudo_policy(raw, details):
    if (ACCEPTED_SUDO_VERSION is None or not isinstance(raw, bytes) or
            not raw.endswith(b"\n") or b"\n" in raw[:-1]):
        return "UNSUPPORTED", ""
    try:
        frame = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return "UNSUPPORTED", ""
    if (not isinstance(frame, dict) or set(frame) != {"sudoVersion", "policy"} or
            canonical_line(frame) != raw or frame["sudoVersion"] != ACCEPTED_SUDO_VERSION or
            not isinstance(frame["policy"], str)):
        return "UNSUPPORTED", ""
    version = frame["sudoVersion"]
    policy = frame["policy"]
    if "\r" in policy or "\0" in policy:
        return "UNSUPPORTED", version
    lines = policy.splitlines()
    while lines and not lines[-1]:
        lines.pop()
    host_pattern = r"[A-Za-z0-9](?:[A-Za-z0-9.-]{0,252}[A-Za-z0-9])?"
    index = 0
    defaults_host = None
    header = (re.fullmatch(r"Matching Defaults entries for dsh on (" + host_pattern + r"):",
                           lines[0]) if lines else None)
    if header is not None:
        defaults_host = header.group(1)
        index = 1
        default_lines = []
        while index < len(lines) and not lines[index].startswith("User dsh may run "):
            if lines[index]:
                if not lines[index].startswith("    "):
                    return "UNSUPPORTED", version
                default_lines.append(lines[index].strip())
            index += 1
        defaults = [part.strip().replace(r"\:", ":")
                    for line in default_lines for part in line.split(",") if part.strip()]
        safe_defaults = {
            "env_reset", "mail_badpass", "use_pty",
            "secure_path=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        }
        if any(value not in safe_defaults for value in defaults):
            authorizing = any(re.search(
                r"(?:^|_)(?:!?authenticate|exempt_group|runas_default|targetpw|rootpw|runaspw)(?:=|$)",
                value, re.IGNORECASE) for value in defaults)
            return ("BROAD" if authorizing else "UNSUPPORTED"), version
    if index >= len(lines):
        return "UNSUPPORTED", version
    user = re.fullmatch(r"User dsh may run the following commands on (" + host_pattern + r"):",
                        lines[index])
    if user is None or defaults_host is not None and user.group(1) != defaults_host:
        return "UNSUPPORTED", version
    index += 1
    while index < len(lines) and not lines[index]:
        index += 1
    source_pattern = r"/etc/sudoers(?:\.d/[A-Za-z0-9_.-]+)?(?::[0-9]+)?"
    if index >= len(lines) or re.fullmatch(
            r"Sudoers entry:(?: " + source_pattern + r")?", lines[index]) is None:
        return "UNSUPPORTED", version
    index += 1
    if index < len(lines) and lines[index].startswith("    Source: "):
        if re.fullmatch(r"    Source: " + source_pattern, lines[index]) is None:
            return "UNSUPPORTED", version
        index += 1
    expected_lines = [
        "    RunAsUsers: root", "    Options: !authenticate", "    Commands:",
        "        " + details["sudoPolicyCommand"],
    ]
    if lines[index:index + len(expected_lines)] == expected_lines:
        index += len(expected_lines)
        if not any(lines[index:]):
            return "EXACT", version
    command_section = policy.split("Commands:", 1)[-1] if "Commands:" in policy else policy
    broad = (re.search(r"(?:^|\n)\s*(?:NOPASSWD:\s*)?ALL\s*(?:\n|$)", command_section,
                       re.IGNORECASE) is not None or
             policy.count("Sudoers entry:") != 1 or
             any(token in command_section for token in ("*", "?", "[", "]")) or
             re.search(r"/(?:bin|usr/bin)/(?:sh|bash|dash|zsh)(?:\s|$)",
                       command_section, re.IGNORECASE) is not None or
             "/usr/bin/python3.12" in command_section)
    return ("BROAD" if broad else "UNSUPPORTED"), version


def _sudo_receipt(exact_code, exact_raw, full_code, full_raw, details):
    policy_state, version = _parse_full_sudo_policy(full_raw, details)
    allowed = exact_code == 0
    passed = allowed and full_code == 0 and policy_state == "EXACT"
    broader = policy_state == "BROAD"
    status = "PASS" if passed else "BLOCKED"
    reason = ("NONE" if passed else "BLOCKED_BROAD_SUDO_POLICY" if broader else
              "EXACT_SUDO_COMMAND_NOT_ALLOWED" if not allowed else
              "SUDO_POLICY_VERSION_UNACCEPTED" if not version else "SUDO_POLICY_UNSUPPORTED")
    policy_hash = hashlib.sha256(canonical_bytes({
        "exactQuerySha256": hashlib.sha256(exact_raw).hexdigest(),
        "fullQuerySha256": hashlib.sha256(full_raw).hexdigest(),
        "sudoVersion": version,
    })).hexdigest()
    return signed({
        "status": status, "reason": reason, "queryUser": "dsh",
        "sudoPath": "/usr/bin/sudo", "noninteractive": True,
        "targetArgc": details["targetArgc"],
        "targetArgvSha256": details["targetArgvSha256"],
        "bootstrapBytes": details["bootstrapBytes"],
        "bootstrapSha256": details["bootstrapSha256"],
        "launcherSha256": LAUNCHER_SHA256,
        "effectivePolicySha256": policy_hash,
        "exactCommandAllowed": allowed, "broaderAuthorityDetected": broader,
        "rawOutputStored": False,
    })


def _unknown_sudo_receipt(details):
    return signed({
        "status": "UNKNOWN", "reason": "SUDO_POLICY_TRANSPORT_UNKNOWN",
        "queryUser": "dsh", "sudoPath": "/usr/bin/sudo", "noninteractive": True,
        "targetArgc": details["targetArgc"], "targetArgvSha256": details["targetArgvSha256"],
        "bootstrapBytes": details["bootstrapBytes"], "bootstrapSha256": details["bootstrapSha256"],
        "launcherSha256": LAUNCHER_SHA256, "effectivePolicySha256": "",
        "exactCommandAllowed": False, "broaderAuthorityDetected": False,
        "rawOutputStored": False,
    })


def _unknown_bundle_receipt():
    return signed({
        "status": "UNKNOWN", "reason": "BUNDLE_CAPTURE_TRANSPORT_UNKNOWN",
        "vmHostname": "", "vmMachineIdSha256": "", "bundleRoot": BUNDLE_ROOT,
        "bundleDevice": -1, "bundleInode": -1, "bundleMode": -1,
        "bundleUid": -1, "bundleGid": -1, "bundleSize": -1,
        "bundleMtimeNs": -1, "bundleCtimeNs": -1,
        "expectedFileCount": 5, "fileCount": 0, "files": [],
    })


def capture_prerequisites(authority_sha256, bundle_transport, sudo_transport, *,
                          command_details=_reconstruction_command_details,
                          lstat=os.lstat, publish=_publish_exclusive):
    _require_authority(authority_sha256, ACCEPTED_PREREQUISITE_CAPTURE_BINDING_SHA256,
                       PREREQUISITE_CAPTURE_BINDING_SHA256,
                       "PREREQUISITE_CAPTURE_NOT_EXECUTABLE")
    _require_absent((BUNDLE_RECEIPT_PATH, SUDO_RECEIPT_PATH), lstat)
    try:
        return_code, stdout, stderr = bundle_transport(
            list(SSH_COMMAND_PREFIX) + [_capture_remote_command()])
    except Exception:
        publish(BUNDLE_RECEIPT_PATH, canonical_line(_unknown_bundle_receipt()))
        return 1
    if return_code != 0 or stderr:
        publish(BUNDLE_RECEIPT_PATH, canonical_line(_unknown_bundle_receipt()))
        return 1
    validate_bundle_receipt(stdout)
    publish(BUNDLE_RECEIPT_PATH, stdout)
    details = command_details()
    try:
        exact_code, exact_stdout, exact_stderr = sudo_transport(
            details["sudoExactQueryCommand"])
        full_code, full_stdout, full_stderr = sudo_transport(
            details["sudoFullQueryCommand"])
        sudo = (_unknown_sudo_receipt(details)
                if exact_stderr or full_stderr or exact_code not in (0, 1) or full_code != 0 else
                _sudo_receipt(exact_code, exact_stdout, full_code, full_stdout, details))
    except Exception:
        sudo = _unknown_sudo_receipt(details)
    publish(SUDO_RECEIPT_PATH, canonical_line(sudo))
    return 0 if sudo["status"] == "PASS" else 1


SUDO_RECEIPT_KEYS = {
    "status", "reason", "queryUser", "sudoPath", "noninteractive",
    "targetArgc", "targetArgvSha256", "bootstrapBytes", "bootstrapSha256",
    "launcherSha256", "effectivePolicySha256", "exactCommandAllowed",
    "broaderAuthorityDetected", "rawOutputStored", "receiptSha256",
}


def validate_sudo_receipt(raw, details):
    try:
        value = _validate_signed_line(raw, SUDO_RECEIPT_KEYS - {"receiptSha256"})
        if (value["status"] != "PASS" or value["reason"] != "NONE" or
                value["queryUser"] != "dsh" or value["sudoPath"] != "/usr/bin/sudo" or
                value["noninteractive"] is not True or value["targetArgc"] != details["targetArgc"] or
                value["targetArgvSha256"] != details["targetArgvSha256"] or
                value["bootstrapBytes"] != RECONSTRUCTION_BOOTSTRAP_BYTES or
                value["bootstrapSha256"] != RECONSTRUCTION_BOOTSTRAP_SHA256 or
                value["launcherSha256"] != LAUNCHER_SHA256 or
                not re.fullmatch(r"[0-9a-f]{64}", value["effectivePolicySha256"]) or
                value["exactCommandAllowed"] is not True or
                value["broaderAuthorityDetected"] is not False or
                value["rawOutputStored"] is not False):
            raise ValueError()
        return value
    except (KeyError, TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError):
        raise PrerequisiteBlocked("SUDO_RECEIPT_REJECTED") from None


def _accepted_hash(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def dispatch_reconstruction(authority_sha256, *, bundle_raw_sha256=None,
                            bundle_self_sha256=None, sudo_raw_sha256=None,
                            sudo_self_sha256=None, read_evidence=read_stable_source,
                            command_details=_reconstruction_command_details):
    _require_authority(authority_sha256, ACCEPTED_RECONSTRUCTION_DISPATCH_BINDING_SHA256,
                       RECONSTRUCTION_DISPATCH_BINDING_SHA256,
                       "RECONSTRUCTION_DISPATCH_NOT_EXECUTABLE")
    pins = (bundle_raw_sha256, bundle_self_sha256, sudo_raw_sha256, sudo_self_sha256)
    accepted_pins = (
        ACCEPTED_BUNDLE_RECEIPT_RAW_SHA256, ACCEPTED_BUNDLE_RECEIPT_SELF_SHA256,
        ACCEPTED_SUDO_RECEIPT_RAW_SHA256, ACCEPTED_SUDO_RECEIPT_SELF_SHA256)
    if not all(_accepted_hash(value) for value in accepted_pins):
        raise PrerequisiteBlocked("RECEIPT_PINS_NOT_ACCEPTED")
    if pins != accepted_pins:
        raise PrerequisiteBlocked("RECEIPT_PINS_REJECTED")
    bundle_raw = read_evidence(BUNDLE_RECEIPT_PATH, bundle_raw_sha256)
    sudo_raw = read_evidence(SUDO_RECEIPT_PATH, sudo_raw_sha256)
    if (hashlib.sha256(bundle_raw).hexdigest() != bundle_raw_sha256 or
            hashlib.sha256(sudo_raw).hexdigest() != sudo_raw_sha256):
        raise PrerequisiteBlocked("RECEIPT_RAW_HASH_REJECTED")
    bundle = validate_bundle_receipt(bundle_raw)
    if bundle["receiptSha256"] != bundle_self_sha256:
        raise PrerequisiteBlocked("BUNDLE_RECEIPT_SELF_HASH_REJECTED")
    details = command_details()
    sudo = validate_sudo_receipt(sudo_raw, details)
    if sudo["receiptSha256"] != sudo_self_sha256:
        raise PrerequisiteBlocked("SUDO_RECEIPT_SELF_HASH_REJECTED")
    launcher = details["launcher"]
    if ACCEPTED_LIVE_BINDINGS is not None or launcher.get("ACCEPTED_LIVE_BINDINGS") is not None:
        raise PrerequisiteBlocked("LIVE_BINDINGS_REJECTED")
    transport = lambda: launcher["_run_bounded_reconstruction_ssh"](
        details["dispatchCommand"])
    return launcher["_coordinate_reconstruction_attempt"](
        DISPATCH_TERMINAL_PATH, DISPATCH_ATTEMPT_PATH, transport)


def _run_ssh(command, payload=b"", *, popen=subprocess.Popen,
             timeout_seconds=120, max_stdout=8 * 1024 * 1024,
             max_stderr=64 * 1024):
    try:
        process = popen(
            command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            bufsize=0,
            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
    except OSError:
        raise RuntimeError("SSH_START_FAILED") from None
    output = {"stdout": bytearray(), "stderr": bytearray()}
    failures = []

    def stop(reason):
        failures.append(reason)
        try:
            process.kill()
        except OSError:
            pass

    def drain(name, stream, limit):
        try:
            for chunk in iter(lambda: stream.read(65536), b""):
                if len(output[name]) + len(chunk) > limit:
                    stop("SSH_OUTPUT_LIMIT_EXCEEDED")
                    return
                output[name].extend(chunk)
        except OSError:
            stop("SSH_DRAIN_FAILED")

    def feed():
        try:
            view = memoryview(payload)
            while view:
                count = process.stdin.write(view[:65536])
                if count is None or count <= 0:
                    raise OSError()
                view = view[count:]
            process.stdin.flush()
        except OSError:
            stop("SSH_STDIN_FAILED")
        finally:
            try:
                process.stdin.close()
            except OSError:
                stop("SSH_STDIN_FAILED")

    threads = [
        threading.Thread(target=drain, args=("stdout", process.stdout, max_stdout), daemon=True),
        threading.Thread(target=drain, args=("stderr", process.stderr, max_stderr), daemon=True),
        threading.Thread(target=feed, daemon=True),
    ]
    for thread in threads:
        thread.start()
    timed_out = False
    try:
        return_code = process.wait(timeout=timeout_seconds)
    except (subprocess.TimeoutExpired, OSError):
        timed_out = True
        stop("SSH_TIMEOUT")
        try:
            process.wait(timeout=5)
        except (subprocess.TimeoutExpired, OSError):
            pass
        return_code = -1
    for thread in threads:
        thread.join(5)
    if any(thread.is_alive() for thread in threads):
        stop("SSH_DRAIN_FAILED")
        try:
            process.stdin.close()
        except OSError:
            pass
        try:
            process.wait(timeout=5)
        except (subprocess.TimeoutExpired, OSError):
            pass
        for thread in threads:
            thread.join(5)
    for stream in (process.stdout, process.stderr):
        try:
            stream.close()
        except OSError:
            failures.append("SSH_DRAIN_FAILED")
    if timed_out or failures:
        priority = ("SSH_TIMEOUT", "SSH_OUTPUT_LIMIT_EXCEEDED", "SSH_DRAIN_FAILED",
                    "SSH_STDIN_FAILED")
        raise RuntimeError(next(reason for reason in priority if reason in failures))
    return return_code, bytes(output["stdout"]), bytes(output["stderr"])


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--deliver-bundle", action="store_true")
    modes.add_argument("--capture-prerequisites", action="store_true")
    modes.add_argument("--dispatch-reconstruction", action="store_true")
    return parser


def main(argv=None, ssh_transport=_run_ssh):
    args = build_parser().parse_args(argv)
    try:
        if args.deliver_bundle:
            return deliver_bundle(
                ACCEPTED_BUNDLE_DELIVERY_BINDING_SHA256, ssh_transport,
                read_source=read_stable_source)
        if args.capture_prerequisites:
            return capture_prerequisites(
                ACCEPTED_PREREQUISITE_CAPTURE_BINDING_SHA256,
                lambda command: ssh_transport(command, b""),
                lambda command: ssh_transport(command, b""))
        return dispatch_reconstruction(
            ACCEPTED_RECONSTRUCTION_DISPATCH_BINDING_SHA256,
            bundle_raw_sha256=ACCEPTED_BUNDLE_RECEIPT_RAW_SHA256,
            bundle_self_sha256=ACCEPTED_BUNDLE_RECEIPT_SELF_SHA256,
            sudo_raw_sha256=ACCEPTED_SUDO_RECEIPT_RAW_SHA256,
            sudo_self_sha256=ACCEPTED_SUDO_RECEIPT_SELF_SHA256)
    except PrerequisiteBlocked as error:
        reason = str(error) if re.fullmatch(r"[A-Z0-9_]+", str(error)) else "PREREQUISITE_BLOCKED"
        print(canonical_line(signed({
            "status": "BLOCKED", "reason": reason, "authorized": False,
        })).decode("utf-8"), end="")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
