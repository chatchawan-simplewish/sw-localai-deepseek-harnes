"""Fail-closed Linux supervisor for the accepted VM105 staging and relay."""

import argparse
import array
import ctypes
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import selectors
import signal
import socket
import struct
import stat
import subprocess
import sys
import time
import types
import urllib.parse
import uuid

try:
    import fcntl
    import pwd
except ModuleNotFoundError:  # Windows imports only to prove the gate.
    fcntl = pwd = None


ACCEPTED_MANIFEST_SHA256 = "4331e0e5fd9ac6f5e881a0dae941f9f07dea7b69969ee8b610071ce14cb03f8b"
ACCEPTED_LIVE_BINDINGS = None
ACCEPTED_STAGING_TOPOLOGY_SHA256 = None
SOURCE_ROOT = "/"
STAGING_ROOT = "/var/tmp/omniroute-dsh-client-final-20260913"
STAGED_NODE = STAGING_ROOT + "/runtime/opt/node-v24.19.0-linux-x64/bin/node"
STAGED_CLI = STAGING_ROOT + "/node_modules/@deepseek-ai/dsh/lib/bin.js"
STAGED_LOADER = STAGING_ROOT + "/runtime/lib64/ld-linux-x86-64.so.2"
STAGED_LIBRARY_PATH = ":".join((
    STAGING_ROOT + "/runtime/lib/x86_64-linux-gnu",
    STAGING_ROOT + "/runtime/usr/lib/x86_64-linux-gnu"))
DSH_DUMMY_REFERENCE = "DSH_LOCAL_DUMMY"
DSH_DUMMY_DOCUMENT = b'{"refs":{"DSH_LOCAL_DUMMY":"fixture-dummy-v1-only"},"version":1}\n'
GATEWAY_FD_MESSAGE = b"VM105_GATEWAY_FDS_V1 chat ack"
MAX_CREDENTIAL_BYTES = 4096
DSH_TIMEOUT_SECONDS = 120
UNIT_RUNTIME_SECONDS = 600
UNIT_STOP_SECONDS = 10
OUTER_WAIT_SECONDS = 625
CLONE_NEWNET = 0x40000000
CLONE_NEWNS = 0x00020000
CLONE_NEWPID = 0x20000000
MS_RDONLY = 1
MS_NOSUID = 2
MS_NODEV = 4
MS_NOEXEC = 8
MS_REMOUNT = 32
MS_BIND = 4096
MS_REC = 16384
MS_PRIVATE = 1 << 18
SIOCGIFFLAGS = 0x8913
SIOCSIFFLAGS = 0x8914
IFF_UP = 0x1
IFF_RUNNING = 0x40
O_CLOEXEC = getattr(os, "O_CLOEXEC", 0)
O_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)
O_NONBLOCK = getattr(os, "O_NONBLOCK", 0)
O_DIRECTORY = getattr(os, "O_DIRECTORY", 0)
SCM_RIGHTS = getattr(socket, "SCM_RIGHTS", 1)
UNIT_RE = re.compile(r"vm105-dsh-[0-9a-f]{32}\.service\Z")
FINAL_CLIENT_SOURCE_SHA256 = "64652DE310EE6104365E0655C9D8897F8093ED1BFB5C4CE12C1B3313D4897D69"
MANIFEST_SOURCE_SHA256 = "371481FE62D6611913F82F65B6E26B12512FDA8A853A2F4591B6314F580C885F"
TOPOLOGY_SOURCE_SHA256 = "17E43721293D3BFFE5C33F63AD2491CD79905BC961993BF40AC0072E48A2BB73"


class LaunchBlocked(RuntimeError):
    pass


_BINDING_KEYS = {
    "gatewayIp", "gatewayPort", "credentialReference", "credentialSchema",
    "relayOrigin", "currentSelector", "sourceRoot", "stagingRoot",
    "manifestPath", "manifestSha256", "topologyPath", "topologySha256", "task",
}
_INSIDE_RECEIPT_KEYS = {
    "status", "invocationId", "controlGroup", "runtimeDirectory", "stagedFiles",
    "connections", "handoffs", "retries", "requestAttempts", "deniedRequests",
    "acceptedRequests", "commitState", "outputState", "resumeRequired",
    "credentialExposed", "networkIsolation", "afUnixPathnameSockets",
    "networkNamespace", "pidNamespace", "namespacePid",
}


def _shape_bindings(value):
    try:
        if not isinstance(value, dict) or set(value) != _BINDING_KEYS:
            raise ValueError()
        ip = str(ipaddress.ip_address(value["gatewayIp"]))
        port = value["gatewayPort"]
        if ip != value["gatewayIp"] or type(port) is not int or not 0 < port < 65536:
            raise ValueError()
        origin = urllib.parse.urlsplit(value["relayOrigin"])
        if (origin.scheme != "http" or origin.hostname != "127.0.0.1" or
                not origin.port or origin.path not in ("", "/") or origin.query or
                origin.fragment or origin.username or origin.password):
            raise ValueError()
        for key in ("credentialReference", "credentialSchema", "currentSelector",
                    "manifestPath", "topologyPath", "task"):
            if not isinstance(value[key], str) or not value[key].strip() or "\0" in value[key]:
                raise ValueError()
        if value["manifestSha256"] != ACCEPTED_MANIFEST_SHA256:
            raise ValueError()
        if not re.fullmatch(r"[0-9a-f]{64}", value["topologySha256"]):
            raise ValueError()
        if (value["credentialSchema"] != "v1-refs" or
                not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*",
                                 value["credentialReference"])):
            raise ValueError()
        if value["sourceRoot"] != SOURCE_ROOT or value["stagingRoot"] != STAGING_ROOT:
            raise LaunchBlocked("BINDING_PATH_REJECTED")
        if (not value["manifestPath"].startswith("/") or
                not value["topologyPath"].startswith("/")):
            raise ValueError()
    except LaunchBlocked:
        raise
    except (KeyError, TypeError, ValueError):
        raise LaunchBlocked("BINDINGS_UNBOUND") from None
    return dict(value)


def _live(value):
    bound = _shape_bindings(value)
    if (ACCEPTED_LIVE_BINDINGS is None or bound != ACCEPTED_LIVE_BINDINGS or
            not isinstance(ACCEPTED_STAGING_TOPOLOGY_SHA256, str) or
            not re.fullmatch(r"[0-9a-f]{64}",
                             ACCEPTED_STAGING_TOPOLOGY_SHA256) or
            bound["topologySha256"] != ACCEPTED_STAGING_TOPOLOGY_SHA256):
        raise LaunchBlocked("LIVE_BINDINGS_UNBOUND")
    return bound


def _unit(value):
    if not isinstance(value, str) or not UNIT_RE.fullmatch(value):
        raise LaunchBlocked("UNIT_ID_REJECTED")
    return value


def _runtime_root(unit_name):
    return "/run/" + _unit(unit_name)[:-8]


def systemd_command(unit_name, bound):
    bound, unit_name = _live(bound), _unit(unit_name)
    unit_stem = unit_name[:-8]
    encoded = json.dumps(bound, sort_keys=True, separators=(",", ":"))
    properties = [
        "Description=VM105 DSH production launch " + unit_name,
        "CapabilityBoundingSet=CAP_SYS_ADMIN CAP_NET_ADMIN CAP_SETUID CAP_SETGID CAP_CHOWN",
        "NoNewPrivileges=yes", "UMask=0077", "ProtectSystem=strict",
        "ReadOnlyPaths=/run /tmp", "ReadWritePaths=/var/tmp /run/" + unit_stem,
        "ProtectHome=yes", "PrivateDevices=yes",
        "RuntimeDirectory=" + unit_stem, "RuntimeDirectoryMode=0700",
        "RuntimeDirectoryPreserve=no",
        "ProtectControlGroups=yes", "ProtectKernelTunables=yes",
        "ProtectKernelModules=yes", "ProtectKernelLogs=yes", "LockPersonality=yes",
        "RestrictSUIDSGID=yes", "RestrictRealtime=yes",
        "RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6", "TasksMax=32",
        "LimitCORE=0", "KillMode=control-group", "Delegate=no", "Restart=no",
        "TimeoutStartSec=15s", "RuntimeMaxSec=%ss" % UNIT_RUNTIME_SECONDS,
        "TimeoutStopSec=%ss" % UNIT_STOP_SECONDS,
    ]
    return [
        "/usr/bin/systemd-run", "--quiet", "--wait", "--pipe", "--unit=" + unit_name,
        *["--property=" + item for item in properties],
        "--", "/usr/bin/python3", str(Path(__file__).resolve()),
        "--inside-unit", "--bindings-json", encoded,
    ]


def _wipe(value):
    value[:] = b"\0" * len(value)


def _kill_unit(bound, unit_name):
    _live(bound)
    subprocess.run(
        ["/usr/bin/systemctl", "kill", "--kill-whom=all", "--signal=KILL",
         _unit(unit_name)],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        timeout=10, check=False, close_fds=True)


def _run_unit(bound, command, credential_fd, unit_name=None, kill_unit=_kill_unit,
              cgroup_state=None, runtime_state=None):
    bound = _live(bound)
    unit_name = _unit(unit_name or next(
        item.split("=", 1)[1] for item in command if item.startswith("--unit=")))
    if type(credential_fd) is not int or credential_fd < 0:
        raise LaunchBlocked("CREDENTIAL_FD_REJECTED")
    process = subprocess.Popen(
        command, stdin=credential_fd, stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL, close_fds=True)
    try:
        stdout, _ = process.communicate(timeout=OUTER_WAIT_SECONDS)
    except subprocess.TimeoutExpired:
        kill_unit(bound, unit_name)
        try:
            stdout, _ = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, _ = process.communicate(timeout=5)
        _verify_unit_removed(bound, unit_name, cgroup_state, runtime_state)
        raise LaunchBlocked("SYSTEMD_RUN_TIMEOUT") from None
    return {"returncode": process.returncode, "stdout": stdout.decode("utf-8", "strict")}


def _cgroup_state(bound, control_group):
    _live(bound)
    root = Path("/sys/fs/cgroup").resolve()
    candidate = (root / control_group.lstrip("/")).resolve()
    if root not in candidate.parents:
        raise LaunchBlocked("SYSTEMD_PROOF_FAILED")
    procs = candidate / "cgroup.procs"
    try:
        return "empty" if not procs.read_text(encoding="ascii").strip() else "nonempty"
    except FileNotFoundError:
        return "missing"


def _runtime_state(bound, runtime_root):
    _live(bound)
    expected = _runtime_root(Path(runtime_root).name + ".service")
    if runtime_root != expected:
        raise LaunchBlocked("SYSTEMD_PROOF_FAILED")
    try:
        os.lstat(runtime_root)
        return "present"
    except FileNotFoundError:
        return "missing"


def _verify_unit_removed(bound, unit_name, cgroup_state=None, runtime_state=None):
    unit_name = _unit(unit_name)
    group = "/system.slice/" + unit_name
    state = (cgroup_state or _cgroup_state)(bound, group)
    if state not in ("empty", "missing"):
        raise LaunchBlocked("CGROUP_NOT_EMPTY")
    root = _runtime_root(unit_name)
    if (runtime_state or _runtime_state)(bound, root) != "missing":
        raise LaunchBlocked("RUNTIME_DIRECTORY_NOT_REMOVED")
    return state


def verify_systemd_lifecycle(bound, unit_name, inside, cgroup_state=_cgroup_state,
                             runtime_state=_runtime_state):
    _live(bound)
    unit_name = _unit(unit_name)
    expected_group = "/system.slice/" + unit_name
    expected_runtime = _runtime_root(unit_name)
    try:
        invocation = inside["invocationId"]
        group = inside["controlGroup"]
        runtime = inside["runtimeDirectory"]
        if (not isinstance(inside, dict) or set(inside) != _INSIDE_RECEIPT_KEYS or
                inside.get("status") != "PASS" or
                not isinstance(invocation, str) or
                not re.fullmatch(r"[0-9a-f]{32}", invocation) or
                group != expected_group or runtime != expected_runtime or
                type(inside.get("stagedFiles")) is not int or
                inside["stagedFiles"] <= 0 or inside.get("connections") != 2 or
                inside.get("handoffs") != 1 or inside.get("retries") != 0 or
                inside.get("requestAttempts") != 2 or
                inside.get("deniedRequests") != 0 or
                inside.get("acceptedRequests") != 2 or
                inside.get("commitState") != "COMMITTED" or
                inside.get("outputState") != "RELEASED" or
                inside.get("resumeRequired") is not False or
                inside.get("credentialExposed") is not False or
                inside.get("networkIsolation") != "IP_TCP_NAMESPACE_ONLY" or
                inside.get("afUnixPathnameSockets") != "RESIDUAL" or
                not re.fullmatch(r"net:\[[0-9]+\]", inside.get("networkNamespace", "")) or
                not re.fullmatch(r"pid:\[[0-9]+\]", inside.get("pidNamespace", "")) or
                inside.get("namespacePid") != 1):
            raise ValueError()
    except (KeyError, TypeError, ValueError):
        raise LaunchBlocked("SYSTEMD_PROOF_FAILED") from None
    state = cgroup_state(bound, group)
    if state not in ("empty", "missing"):
        raise LaunchBlocked("CGROUP_NOT_EMPTY")
    if runtime_state(bound, runtime) != "missing":
        raise LaunchBlocked("RUNTIME_DIRECTORY_NOT_REMOVED")
    return {"status": "PASS", "unit": unit_name, "invocationId": invocation,
             "controlGroup": group, "cgroupState": state,
             "runtimeDirectory": runtime, "stagedFiles": inside["stagedFiles"],
             "connections": 2, "handoffs": 1, "retries": 0,
            "requestAttempts": 2, "deniedRequests": 0,
             "acceptedRequests": 2, "commitState": "COMMITTED",
             "outputState": "RELEASED", "resumeRequired": False,
             "credentialExposed": False,
             "networkIsolation": "IP_TCP_NAMESPACE_ONLY",
             "afUnixPathnameSockets": "RESIDUAL",
             "networkNamespace": inside["networkNamespace"],
             "pidNamespace": inside["pidNamespace"], "namespacePid": 1}


def launch(bound, credential_fd, unit_name=None, run_unit=_run_unit,
           cgroup_state=_cgroup_state, runtime_state=_runtime_state,
           kill_unit=_kill_unit):
    bound = _live(bound)
    if sys.platform != "linux":
        raise LaunchBlocked("LINUX_REQUIRED")
    unit_name = _unit(unit_name or "vm105-dsh-" + uuid.uuid4().hex + ".service")
    result = run_unit(bound, systemd_command(unit_name, bound), credential_fd)
    try:
        if not isinstance(result, dict) or result.get("returncode") != 0:
            raise LaunchBlocked("SYSTEMD_RUN_FAILED")
        try:
            inside = json.loads(result["stdout"])
        except (KeyError, TypeError, ValueError):
            raise LaunchBlocked("SYSTEMD_RECEIPT_REJECTED") from None
        if isinstance(inside, dict) and inside.get("status") == "BLOCKED":
            expected = {
                "status", "reason", "resumeRequired", "commitState",
                "outputState",
            }
            reason = inside.get("reason")
            if (set(inside) != expected or
                    not isinstance(reason, str) or
                    not re.fullmatch(r"[A-Z0-9_]+", reason) or
                    inside.get("resumeRequired") is not True or
                    inside.get("commitState") != "UNPROVEN" or
                    inside.get("outputState") != "UNPROVEN"):
                raise LaunchBlocked("SYSTEMD_RECEIPT_REJECTED")
            raise LaunchBlocked(reason)
        return verify_systemd_lifecycle(
            bound, unit_name, inside, cgroup_state, runtime_state)
    except LaunchBlocked:
        kill_unit(bound, unit_name)
        _verify_unit_removed(
            bound, unit_name, cgroup_state, runtime_state)
        raise


def read_bounded_credential(bound, descriptor, readv=None, wipe=_wipe):
    _live(bound)
    if type(descriptor) is not int or descriptor < 0:
        raise LaunchBlocked("CREDENTIAL_FD_REJECTED")
    readv = readv or getattr(os, "readv", None)
    if readv is None:
        raise LaunchBlocked("CREDENTIAL_READ_UNSUPPORTED")
    value = bytearray(MAX_CREDENTIAL_BYTES + 1)
    used = 0
    try:
        while True:
            count = readv(descriptor, [memoryview(value)[used:]])
            if count == 0:
                break
            if count < 0 or count > len(value) - used:
                raise OSError("invalid read count")
            used += count
            if used > MAX_CREDENTIAL_BYTES:
                raise LaunchBlocked("CREDENTIAL_INPUT_REJECTED")
        if used == 0:
            raise LaunchBlocked("CREDENTIAL_INPUT_REJECTED")
        del value[used:]
        return value
    except Exception:
        wipe(value)
        raise


def copy_credential_to_pipe(bound, credential, pipe2=None, write=os.write,
                            close=os.close, wipe=_wipe):
    _live(bound)
    if not isinstance(credential, bytearray) or not 0 < len(credential) <= MAX_CREDENTIAL_BYTES:
        raise LaunchBlocked("CREDENTIAL_INPUT_REJECTED")
    pipe2 = pipe2 or getattr(os, "pipe2", None)
    if pipe2 is None:
        wipe(credential)
        raise LaunchBlocked("CREDENTIAL_PIPE_UNSUPPORTED")
    read_fd = write_fd = None
    try:
        read_fd, write_fd = pipe2(O_CLOEXEC)
        if write(write_fd, credential) != len(credential):
            raise OSError("short credential pipe write")
        close(write_fd)
        write_fd = None
        return read_fd
    except OSError:
        if read_fd is not None:
            close(read_fd)
        raise LaunchBlocked("CREDENTIAL_PIPE_FAILED") from None
    finally:
        if write_fd is not None:
            close(write_fd)
        wipe(credential)


def _unshare_worker_namespaces(bound):
    _live(bound)
    libc = ctypes.CDLL(None, use_errno=True)
    flags = CLONE_NEWNET | CLONE_NEWPID
    if libc.unshare(flags) != 0:
        raise OSError(ctypes.get_errno(), "unshare(worker namespaces)")


def _unshare_mount_namespace(bound):
    _live(bound)
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.unshare(CLONE_NEWNS) != 0:
        raise OSError(ctypes.get_errno(), "unshare(CLONE_NEWNS)")


def _mount(source, target, filesystem, flags):
    libc = ctypes.CDLL(None, use_errno=True)
    encode = lambda value: None if value is None else value.encode("ascii")
    if libc.mount(encode(source), encode(target), encode(filesystem), flags, None) != 0:
        raise OSError(ctypes.get_errno(), "mount(%s)" % target)


def _mount_worker_filesystems(bound, runtime, mount=_mount, statvfs=None):
    """Make /run and staged /var/tmp read-only while keeping this runtime writable."""
    _live(bound)
    statvfs = statvfs or getattr(os, "statvfs", None)
    if statvfs is None:
        raise LaunchBlocked("WORKER_MOUNT_ISOLATION_UNSUPPORTED")
    mount(None, "/", None, MS_REC | MS_PRIVATE)
    mount(runtime["root"], runtime["root"], None, MS_BIND)
    mount(None, "/run", None,
          MS_BIND | MS_REMOUNT | MS_RDONLY | MS_NOSUID | MS_NODEV | MS_NOEXEC)
    mount("proc", "/proc", "proc", MS_NOSUID | MS_NODEV | MS_NOEXEC)
    mount("/var/tmp", "/var/tmp", None, MS_BIND)
    mount(None, "/var/tmp", None,
          MS_BIND | MS_REMOUNT | MS_RDONLY | MS_NOSUID | MS_NODEV | MS_NOEXEC)
    readonly = getattr(os, "ST_RDONLY", 1)
    if (not statvfs("/var/tmp").f_flag & readonly or
            statvfs(runtime["root"]).f_flag & readonly):
        raise LaunchBlocked("WORKER_MOUNT_ISOLATION_UNPROVEN")


def _raise_loopback(bound):
    _live(bound)
    interface = struct.pack("16sH14x", b"lo", 0)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM | socket.SOCK_CLOEXEC) as probe:
        current = fcntl.ioctl(probe.fileno(), SIOCGIFFLAGS, interface)
        _, flags = struct.unpack("16sH14x", current)
        fcntl.ioctl(probe.fileno(), SIOCSIFFLAGS,
                    struct.pack("16sH14x", b"lo", flags | IFF_UP | IFF_RUNNING))


def _namespace(bound):
    _live(bound)
    return os.readlink("/proc/self/ns/net")


def _pid_namespace(bound):
    _live(bound)
    return os.readlink("/proc/self/ns/pid")


def _namespace_pid(bound):
    _live(bound)
    rows = Path("/proc/self/status").read_text(encoding="ascii").splitlines()
    matches = [row.split()[1:] for row in rows if row.startswith("NSpid:")]
    if len(matches) != 1 or not matches[0] or not all(value.isdigit() for value in matches[0]):
        raise LaunchBlocked("PID_NAMESPACE_UNPROVEN")
    return int(matches[0][-1])


def _close_other_fds(bound, keep):
    _live(bound)
    allowed = set(keep)
    for value in os.listdir("/proc/self/fd"):
        descriptor = int(value)
        if descriptor not in allowed:
            try:
                os.close(descriptor)
            except OSError:
                pass


def _dsh_identity(bound):
    _live(bound)
    identity = pwd.getpwnam("dsh")
    if identity.pw_uid <= 0 or identity.pw_gid <= 0:
        raise LaunchBlocked("DSH_IDENTITY_REJECTED")
    return identity


def _drop_dsh(bound, identity):
    _live(bound)
    os.setgroups([])
    os.setgid(identity.pw_gid)
    os.setuid(identity.pw_uid)
    if os.getuid() != identity.pw_uid or os.getgid() != identity.pw_gid:
        raise OSError("privilege drop failed")


def _ready_writer(bound, receipt_fd, network_namespace, pid_namespace, namespace_pid):
    _live(bound)
    line = "READY %s %s nspid=%d\n" % (
        network_namespace, pid_namespace, namespace_pid)
    os.write(receipt_fd, line.encode("ascii"))


def _load_pinned_source(bound, path, name, expected_sha256):
    _live(bound)
    descriptor = os.open(path, os.O_RDONLY | O_CLOEXEC | O_NOFOLLOW)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise LaunchBlocked("ACCEPTED_SOURCE_REJECTED")
        chunks = []
        digest = hashlib.sha256()
        while True:
            chunk = os.read(descriptor, 65536)
            if not chunk:
                break
            chunks.append(chunk)
            digest.update(chunk)
        after = os.fstat(descriptor)
        identity = lambda value: (
            value.st_dev, value.st_ino, value.st_mode, value.st_size,
            value.st_mtime_ns, value.st_ctime_ns)
        if (identity(before) != identity(after) or
                digest.hexdigest().upper() != expected_sha256.upper()):
            raise LaunchBlocked("ACCEPTED_SOURCE_REJECTED")
        code = compile(b"".join(chunks), str(path), "exec")
    finally:
        os.close(descriptor)
    module = types.ModuleType(name)
    module.__file__ = str(path)
    exec(code, module.__dict__)
    return module


def _load_accepted(bound, filename, name, expected_sha256):
    return _load_pinned_source(
        bound, Path(__file__).with_name(filename), name, expected_sha256)


_SAFE_SECRET = re.compile(rb"[\x21\x23-\x5b\x5d-\x7e]{1,2048}\Z")
_TOOL_ROWS = (
    "tools", "session-title-llm", "compaction", "delegation",
    "skill", "skill-filesystem", "tool-ask-user", "tool-bash",
    "tool-bash-persistent", "tool-cordis", "tool-fs", "tool-fs-search",
    "tool-goal", "tool-jobs", "tool-pwsh", "tool-pwsh-persistent",
    "tool-ralph", "tool-skill", "tool-str-replace-editor", "tool-subagent",
    "tool-subagent-control", "tool-subagent-report", "tool-todo", "tool-web",
    "tool-workflow",
)


def _parse_credential_document(bound, document):
    bound = _live(bound)
    secret = None
    try:
        reference = bound["credentialReference"].encode("ascii")
        prefix = b'{"refs":{"' + reference + b'":"'
        suffix = b'"},"version":1}\n'
        if (not isinstance(document, bytearray) or b"\r" in document or
                b"\0" in document or document.count(b"\n") != 1 or
                not document.startswith(prefix) or not document.endswith(suffix)):
            raise ValueError()
        secret = document[len(prefix):-len(suffix)]
        if not _SAFE_SECRET.fullmatch(secret):
            raise ValueError()
        return secret
    except (KeyError, TypeError, UnicodeEncodeError, ValueError):
        if secret is not None:
            _wipe(secret)
        raise LaunchBlocked("CREDENTIAL_DOCUMENT_REJECTED") from None
    finally:
        _wipe(document)


def decode_credential_document(bound, credential_fd):
    """Decode the real relay key; credentials-local receives a dummy document."""
    bound = _live(bound)
    document = read_bounded_credential(bound, credential_fd)
    return _parse_credential_document(bound, document)


def build_dsh_patch(bound, credential_fd):
    bound = _live(bound)
    rows = [
        {"id": "credentials", "config": {
            "path": "/proc/self/fd/" + str(credential_fd), "watch": False}},
        {"id": "llm-pi-ai", "config": {"providers": {"omniroute": {
            "api": "openai-completions",
            "baseURL": bound["relayOrigin"].rstrip("/") + "/v1",
            "apiKeyEnv": DSH_DUMMY_REFERENCE,
            "models": [{"id": "agent/normal", "name": "agent/normal",
                        "displayName": "agent/normal", "contextWindow": 32768,
                        "maxTokens": 4096}],
        }}}},
        {"id": "agent-default-model", "config": {
            "provider": "omniroute", "model": "agent/normal"}},
        {"id": "llm-retry", "disabled": True},
        {"id": "llm-deepseek", "disabled": True},
        {"id": "web-search-deepseek", "disabled": True},
        *[{"id": row, "disabled": True} for row in _TOOL_ROWS],
    ]
    return bytearray((json.dumps(
        rows, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8"))


def _run_dsh_process(bound, argv, **kwargs):
    _live(bound)
    timeout = kwargs.pop("timeout")
    process = subprocess.Popen(argv, start_new_session=True, **kwargs)
    try:
        process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.communicate(timeout=5)
        raise LaunchBlocked("DSH_ENTRY_TIMEOUT") from None
    return process


def run_dsh_entry(bound, relay_address, runtime, run=_run_dsh_process):
    bound = _live(bound)
    actual_origin = "http://%s:%s" % relay_address
    if actual_origin != bound["relayOrigin"]:
        raise LaunchBlocked("RELAY_ORIGIN_MISMATCH")
    if (not isinstance(runtime, dict) or
            set(runtime) != {"root", "home", "dshHome", "tmp", "workspace"}):
        raise LaunchBlocked("RUNTIME_DIRECTORY_REJECTED")
    dummy_fd = patch_fd = None
    try:
        dummy_fd = copy_credential_to_pipe(bound, bytearray(DSH_DUMMY_DOCUMENT))
        patch_document = build_dsh_patch(bound, dummy_fd)
        patch_fd = copy_credential_to_pipe(bound, patch_document)
        argv = [
            STAGED_LOADER, "--library-path", STAGED_LIBRARY_PATH, STAGED_NODE,
            "--no-global-search-paths", STAGED_CLI, "--profile", "headless",
            "--patch", "/proc/self/fd/" + str(patch_fd), bound["task"],
        ]
        environment = {
            "HOME": runtime["home"], "DSH_HOME": runtime["dshHome"],
            "TMPDIR": runtime["tmp"], "LANG": "C",
            "DSH_TELEMETRY_DISABLED": "1",
        }
        result = run(
            bound, argv, cwd=runtime["workspace"], env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            close_fds=True, pass_fds=(dummy_fd, patch_fd),
            timeout=DSH_TIMEOUT_SECONDS)
    finally:
        for descriptor in (dummy_fd, patch_fd):
            if descriptor is not None:
                os.close(descriptor)
    if result.returncode != 0:
        raise LaunchBlocked("DSH_ENTRY_FAILED")
    return {"status": "PASS", "credentialExposed": False}


def contained_composition(control_fd, credential_fd, bound, runtime,
                          credential_decoder=decode_credential_document,
                          dsh_entry=run_dsh_entry):
    """Compose the strict decoder and one-shot DSH entry with the accepted relay."""
    bound = _live(bound)
    control = socket.socket(
        socket.AF_UNIX, socket.SOCK_STREAM, fileno=control_fd)
    key = None
    try:
        helper = _load_accepted(
            bound, "Invoke-VM105FinalClient.py", "vm105_final_client",
            FINAL_CLIENT_SOURCE_SHA256)
        key = credential_decoder(bound, credential_fd)
        port = urllib.parse.urlsplit(bound["relayOrigin"]).port
        relay = helper.TwoRequestRelay.from_socket_handoff(
            control, bound["gatewayIp"], bound["gatewayPort"],
            key.decode("ascii"), listen_port=port)
        control = None
        _wipe(key)
        if relay.address != ("127.0.0.1", port):
            relay.server.server_close()
            raise LaunchBlocked("RELAY_ORIGIN_MISMATCH")
        with relay:
            result = dsh_entry(bound, relay.address, runtime)
        if not isinstance(result, dict) or result.get("status") != "PASS":
            raise LaunchBlocked("CONTAINED_CLIENT_FAILED")
        state = getattr(relay, "state", None)
        transaction = state.get("tuple") if isinstance(state, dict) else None
        claimed = getattr(relay, "claimed_upstreams", None)
        if (not isinstance(state, dict) or type(state.get("count")) is not int or
                state["count"] != 2 or state.get("committed") is not True or
                state.get("requestAttempts") != 2 or
                state.get("deniedRequests") != 0 or
                state.get("output") is not True or state.get("failed") is not False or
                not isinstance(transaction, tuple) or len(transaction) != 4 or
                not all(isinstance(value, str) and value.strip()
                        for value in transaction) or claimed != [True, True]):
            raise LaunchBlocked("RELAY_COMPLETION_UNPROVEN")
        return {"status": "PASS", "requestAttempts": 2,
                "deniedRequests": 0, "acceptedRequests": 2,
                "committed": True, "output": True, "failed": False,
                "tupleFieldCount": 4, "upstreamSocketsConsumed": 2,
                "commitState": "COMMITTED", "outputState": "RELEASED",
                "resumeRequired": False, "credentialExposed": False}
    finally:
        if key is not None:
            _wipe(key)
        try:
            os.close(credential_fd)
        except OSError:
            pass
        if control is not None:
            control.close()


def _seal_staged_topology(bound, root_fd, receipt, gid, listdir=os.listdir,
                          statat=os.stat, readlink=os.readlink, openat=os.open,
                          fstat=os.fstat, fchown=None, fchmod=None,
                          close=os.close, hash_fd=None):
    """Grant the dsh group read/execute access without following staged links."""
    _live(bound)
    fchown = fchown or getattr(os, "fchown", None)
    fchmod = fchmod or getattr(os, "fchmod", None)
    if (fchown is None or fchmod is None or hash_fd is None or
            not isinstance(receipt, dict)):
        raise LaunchBlocked("STAGING_OWNERSHIP_UNSUPPORTED")
    expected = {row["path"]: (row["sha256"], 0o550 if row["mode"] & 0o100 else 0o440)
                for row in receipt.get("files", ())}
    expected_links = {row["path"]: row["rawRelativeTarget"]
                      for row in receipt.get("links", ())}
    expected_dirs = {row["path"] for row in receipt.get("directories", ())}
    if (len(expected) != len(receipt.get("files", ())) or
            len(expected_links) != len(receipt.get("links", ())) or
            len(expected_dirs) != len(receipt.get("directories", ()))):
        raise LaunchBlocked("STAGING_SEAL_REJECTED")

    def walk(directory_fd, prefix, apply):
        files, links, directories = set(), set(), {prefix}
        info = fstat(directory_fd)
        if not stat.S_ISDIR(info.st_mode):
            raise LaunchBlocked("STAGING_SEAL_REJECTED")
        for name in sorted(listdir(directory_fd)):
            if not isinstance(name, str) or name in (".", "..") or "/" in name or "\0" in name:
                raise LaunchBlocked("STAGING_SEAL_REJECTED")
            relative = name if not prefix else prefix + "/" + name
            path_info = statat(name, dir_fd=directory_fd, follow_symlinks=False)
            if stat.S_ISLNK(path_info.st_mode):
                if (relative not in expected_links or
                        readlink(name, dir_fd=directory_fd) != expected_links[relative] or
                        path_info.st_uid != 0 or path_info.st_gid != 0):
                    raise LaunchBlocked("STAGING_SEAL_REJECTED")
                links.add(relative)
                continue
            child_fd = openat(
                name, os.O_RDONLY | O_CLOEXEC | O_NOFOLLOW | O_NONBLOCK,
                dir_fd=directory_fd)
            try:
                child = fstat(child_fd)
                if stat.S_ISDIR(child.st_mode):
                    nested_files, nested_links, nested_dirs = walk(child_fd, relative, apply)
                    files.update(nested_files)
                    links.update(nested_links)
                    directories.update(nested_dirs)
                elif stat.S_ISREG(child.st_mode):
                    if relative not in expected:
                        raise LaunchBlocked("STAGING_SEAL_REJECTED")
                    expected_hash, expected_mode = expected[relative]
                    if apply:
                        fchown(child_fd, 0, gid)
                        fchmod(child_fd, expected_mode)
                    current = fstat(child_fd)
                    if (hash_fd(child_fd) != expected_hash or
                            stat.S_IMODE(current.st_mode) != expected_mode or
                            current.st_uid != 0 or current.st_gid != gid):
                        raise LaunchBlocked("STAGING_SEAL_REJECTED")
                    files.add(relative)
                else:
                    raise LaunchBlocked("STAGING_SEAL_REJECTED")
            finally:
                close(child_fd)
        if apply:
            fchown(directory_fd, 0, gid)
            fchmod(directory_fd, 0o550)
        current = fstat(directory_fd)
        if (stat.S_IMODE(current.st_mode) != 0o550 or
                current.st_uid != 0 or current.st_gid != gid):
            raise LaunchBlocked("STAGING_SEAL_REJECTED")
        return files, links, directories

    first_files, first_links, first_dirs = walk(root_fd, "", True)
    files, links, directories = walk(root_fd, "", False)
    if (first_files != set(expected) or files != set(expected) or
            first_links != set(expected_links) or links != set(expected_links) or
            first_dirs != expected_dirs | {""} or directories != expected_dirs | {""}):
        raise LaunchBlocked("STAGING_SEAL_REJECTED")
    return len(files) + len(links) + len(directories)


def isolated_worker(control_fd, credential_fd, receipt_fd,
                    parent_network_namespace, parent_pid_namespace, bound,
                    identity, runtime, setsid=None,
                    unshare=_unshare_worker_namespaces,
                    unshare_mount=_unshare_mount_namespace,
                    raise_loopback=_raise_loopback, network_namespace=_namespace,
                    pid_namespace=_pid_namespace, namespace_pid=_namespace_pid,
                    mount_worker=_mount_worker_filesystems,
                    close_other_fds=_close_other_fds, drop_dsh=_drop_dsh,
                    ready=_ready_writer, contained_entry=contained_composition,
                    fork=None, waitpid=os.waitpid):
    bound = _live(bound)
    setsid = setsid or (lambda live: os.setsid())
    fork = fork or getattr(os, "fork", None)
    if fork is None:
        raise LaunchBlocked("PID_NAMESPACE_UNSUPPORTED")
    setsid(bound)
    unshare(bound)
    raise_loopback(bound)
    child_network_namespace = network_namespace(bound)
    if child_network_namespace == parent_network_namespace:
        raise LaunchBlocked("NETWORK_NAMESPACE_UNCHANGED")
    inner_pid = fork()
    if inner_pid != 0:
        close_other_fds(bound, set())
        waited, status = waitpid(inner_pid, 0)
        if waited != inner_pid or os.waitstatus_to_exitcode(status) != 0:
            raise LaunchBlocked("PID_NAMESPACE_WORKER_FAILED")
        return {"status": "PASS"}
    unshare_mount(bound)
    mount_worker(bound, runtime)
    child_pid_namespace = pid_namespace(bound)
    current_namespace_pid = namespace_pid(bound)
    if (child_pid_namespace == parent_pid_namespace or
            current_namespace_pid != 1 or os.getpid() != 1):
        raise LaunchBlocked("PID_NAMESPACE_UNPROVEN")
    close_other_fds(bound, {control_fd, credential_fd, receipt_fd})
    drop_dsh(bound, identity)
    ready(bound, receipt_fd, child_network_namespace,
          child_pid_namespace, current_namespace_pid)
    return contained_entry(control_fd, credential_fd, bound, runtime)


def _connect_numeric(bound, peer, timeout):
    _live(bound)
    family = socket.AF_INET6 if ipaddress.ip_address(peer[0]).version == 6 else socket.AF_INET
    stream = socket.socket(
        family, socket.SOCK_STREAM | socket.SOCK_CLOEXEC, socket.IPPROTO_TCP)
    try:
        stream.settimeout(timeout)
        stream.connect(peer)
        return stream
    except Exception:
        stream.close()
        raise


def _wait_child(bound, pid, timeout):
    _live(bound)
    deadline = time.monotonic() + timeout
    while True:
        result = os.waitid(os.P_PID, pid, os.WEXITED | os.WNOWAIT | os.WNOHANG)
        if result is not None:
            return result.si_status if result.si_code == os.CLD_EXITED else 128 + result.si_status
        if time.monotonic() >= deadline:
            raise TimeoutError("child timeout")
        time.sleep(0.02)


def _reap_child(bound, pid, timeout):
    _live(bound)
    deadline = time.monotonic() + timeout
    while True:
        waited, status = os.waitpid(pid, os.WNOHANG)
        if waited == pid:
            return os.waitstatus_to_exitcode(status)
        if time.monotonic() >= deadline:
            raise TimeoutError("child reap timeout")
        time.sleep(0.02)


def _kill_group(bound, pid):
    _live(bound)
    os.killpg(pid, signal.SIGKILL)


def _kill_child(bound, pid):
    _live(bound)
    os.kill(pid, signal.SIGKILL)


def _getpgid(bound, pid):
    _live(bound)
    return os.getpgid(pid)


def _wait_ready_fd(bound, descriptor, timeout):
    _live(bound)
    with selectors.DefaultSelector() as poller:
        poller.register(descriptor, selectors.EVENT_READ)
        if not poller.select(timeout):
            raise TimeoutError("namespace readiness timeout")
    line = os.read(descriptor, 256)
    match = re.fullmatch(
        rb"READY (net:\[[0-9]+\]) (pid:\[[0-9]+\]) nspid=(1)\n", line)
    if match is None:
        raise ValueError("namespace readiness rejected")
    return {"network": match.group(1).decode("ascii"),
            "pid": match.group(2).decode("ascii"), "namespacePid": 1}


def handoff_and_wait(bound, child_pid, control, wait_ready,
                     connect=_connect_numeric, wait_child=_wait_child,
                     reap_child=_reap_child, getpgid=_getpgid,
                     kill_group=_kill_group, kill_child=_kill_child):
    bound = _live(bound)
    streams = []
    group_proven = reaped = success = False
    try:
        child_namespaces = wait_ready(bound, child_pid, 15)
        if getpgid(bound, child_pid) != child_pid:
            raise OSError("worker process group not proven")
        group_proven = True
        peer = (bound["gatewayIp"], bound["gatewayPort"])
        streams.append(connect(bound, peer, 5))
        streams.append(connect(bound, peer, 5))
        rights = array.array("i", [stream.fileno() for stream in streams])
        sent = control.sendmsg([GATEWAY_FD_MESSAGE], [
            (socket.SOL_SOCKET, SCM_RIGHTS, rights.tobytes())])
        if sent != len(GATEWAY_FD_MESSAGE):
            raise OSError("short gateway FD payload")
        for stream in streams:
            stream.close()
        streams.clear()
        control.close()
        if wait_child(bound, child_pid, DSH_TIMEOUT_SECONDS) != 0:
            raise OSError("contained worker failed")
        try:
            reaped_status = reap_child(bound, child_pid, 5)
            reaped = True
        except ChildProcessError:
            reaped = True
            raise
        if reaped_status != 0:
            raise OSError("contained worker reap mismatch")
        success = True
        return {"status": "PASS", "connections": 2, "handoffs": 1,
                "retries": 0, "namespaces": child_namespaces,
                "networkIsolation": "IP_TCP_NAMESPACE_ONLY",
                "afUnixPathnameSockets": "RESIDUAL"}
    except Exception:
        raise LaunchBlocked("SUPERVISOR_FAILED") from None
    finally:
        for stream in streams:
            stream.close()
        if not getattr(control, "closed", False):
            control.close()
        if not success and not reaped:
            try:
                (kill_group if group_proven else kill_child)(bound, child_pid)
            except ProcessLookupError:
                pass
            try:
                reap_child(bound, child_pid, 5)
            except (ChildProcessError, ProcessLookupError, TimeoutError):
                pass


def stage_bound_closure(bound, identity=None, seal_tree=_seal_staged_topology):
    bound = _live(bound)
    identity = identity or _dsh_identity(bound)
    manifest_fd = topology_fd = source_fd = staging_fd = None
    try:
        manifest_fd = os.open(
            bound["manifestPath"], os.O_RDONLY | O_CLOEXEC | O_NOFOLLOW)
        with os.fdopen(os.dup(manifest_fd), "r", encoding="utf-8") as source:
            manifest = json.load(source)
        topology_fd = os.open(
            bound["topologyPath"], os.O_RDONLY | O_CLOEXEC | O_NOFOLLOW)
        with os.fdopen(os.dup(topology_fd), "r", encoding="utf-8") as source:
            topology_receipt = json.load(source)
        source_fd = os.open(
            SOURCE_ROOT, os.O_RDONLY | O_DIRECTORY | O_CLOEXEC | O_NOFOLLOW)
        os.mkdir(STAGING_ROOT, 0o700)
        staging_fd = os.open(
            STAGING_ROOT, os.O_RDONLY | O_DIRECTORY | O_CLOEXEC | O_NOFOLLOW)
        builder = _load_accepted(
            bound, "Build-VM105FinalClientManifest.py", "vm105_final_manifest",
            MANIFEST_SOURCE_SHA256)
        helper = _load_accepted(
            bound, "Capture-VM105DshTopology.py", "vm105_dsh_topology",
            TOPOLOGY_SOURCE_SHA256)
        receipt = helper.stage_verified_topology(
            manifest, topology_receipt, bound["topologySha256"],
            source_fd, staging_fd, builder)
        receipt["sealedEntries"] = seal_tree(
            bound, staging_fd, receipt, identity.pw_gid,
            hash_fd=builder._hash_fd)
        return receipt
    except LaunchBlocked:
        raise
    except Exception as error:
        raise LaunchBlocked("STAGING_FAILED") from error
    finally:
        for descriptor in (staging_fd, source_fd, topology_fd, manifest_fd):
            if descriptor is not None:
                os.close(descriptor)


def _control_group(bound):
    _live(bound)
    rows = Path("/proc/self/cgroup").read_text(encoding="ascii").splitlines()
    matches = [row.split(":", 2)[2] for row in rows if row.startswith("0::")]
    if len(matches) != 1 or not matches[0].startswith("/"):
        raise LaunchBlocked("CONTROL_GROUP_UNPROVEN")
    return matches[0]


def _prepare_runtime(bound, control_group, identity):
    bound = _live(bound)
    prefix = "/system.slice/"
    if not control_group.startswith(prefix):
        raise LaunchBlocked("CONTROL_GROUP_UNPROVEN")
    unit_name = _unit(control_group[len(prefix):])
    root = _runtime_root(unit_name)
    if os.environ.get("RUNTIME_DIRECTORY") != root:
        raise LaunchBlocked("RUNTIME_DIRECTORY_UNPROVEN")
    root_fd = os.open(root, os.O_RDONLY | O_DIRECTORY | O_CLOEXEC | O_NOFOLLOW)
    paths = {"root": root}
    try:
        info = os.fstat(root_fd)
        if (not stat.S_ISDIR(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o700 or
                info.st_uid != 0 or info.st_gid != 0 or info.st_nlink != 2):
            raise LaunchBlocked("RUNTIME_DIRECTORY_UNPROVEN")
        os.fchown(root_fd, identity.pw_uid, identity.pw_gid)
        os.fchmod(root_fd, 0o700)
        for key, name in (("home", "home"), ("dshHome", "dsh-home"),
                          ("tmp", "tmp"), ("workspace", "workspace")):
            os.mkdir(name, 0o700, dir_fd=root_fd)
            child_fd = os.open(
                name, os.O_RDONLY | O_DIRECTORY | O_CLOEXEC | O_NOFOLLOW,
                dir_fd=root_fd)
            try:
                os.fchown(child_fd, identity.pw_uid, identity.pw_gid)
                os.fchmod(child_fd, 0o700)
            finally:
                os.close(child_fd)
            paths[key] = root + "/" + name
    finally:
        os.close(root_fd)
    return paths


def service_entry(bound, credential_fd=0, contained_entry=contained_composition):
    bound = _live(bound)
    if sys.platform != "linux" or os.geteuid() != 0:
        raise LaunchBlocked("ROOT_LINUX_SERVICE_REQUIRED")
    identity = _dsh_identity(bound)
    control_group = _control_group(bound)
    runtime = _prepare_runtime(bound, control_group, identity)
    credential = read_bounded_credential(bound, credential_fd)
    os.close(credential_fd)
    credential_pipe = copy_credential_to_pipe(bound, credential)
    parent_control = child_control = None
    ready_read = ready_write = None
    try:
        stage = stage_bound_closure(bound, identity)
        parent_network_namespace = _namespace(bound)
        parent_pid_namespace = _pid_namespace(bound)
        parent_control, child_control = socket.socketpair(
            socket.AF_UNIX, socket.SOCK_STREAM | socket.SOCK_CLOEXEC)
        ready_read, ready_write = os.pipe2(os.O_CLOEXEC)
        pid = os.fork()
    except Exception:
        for endpoint in (parent_control, child_control):
            if endpoint is not None:
                endpoint.close()
        for descriptor in (ready_read, ready_write, credential_pipe):
            if descriptor is not None:
                os.close(descriptor)
        raise
    if pid == 0:
        try:
            parent_control.close()
            os.close(ready_read)
            isolated_worker(
                child_control.detach(), credential_pipe, ready_write,
                parent_network_namespace, parent_pid_namespace,
                bound, identity, runtime,
                contained_entry=contained_entry)
            os._exit(0)
        except BaseException:
            os._exit(1)
    child_control.close()
    os.close(ready_write)
    os.close(credential_pipe)
    try:
        result = handoff_and_wait(
            bound, pid, parent_control,
            wait_ready=lambda live, child, timeout: _wait_ready_fd(
                live, ready_read, timeout))
    finally:
        os.close(ready_read)
    invocation = os.environ.get("INVOCATION_ID", "")
    if not re.fullmatch(r"[0-9a-f]{32}", invocation):
        raise LaunchBlocked("INVOCATION_ID_UNPROVEN")
    if type(stage.get("fileCount")) is not int or stage["fileCount"] <= 0:
        raise LaunchBlocked("STAGING_PROOF_FAILED")
    return {"status": "PASS", "invocationId": invocation,
            "controlGroup": control_group, "runtimeDirectory": runtime["root"],
            "stagedFiles": stage["fileCount"],
            "connections": result["connections"], "handoffs": result["handoffs"],
            "retries": 0, "requestAttempts": 2, "deniedRequests": 0,
             "acceptedRequests": 2, "commitState": "COMMITTED",
             "outputState": "RELEASED", "resumeRequired": False,
             "credentialExposed": False,
             "networkIsolation": result["networkIsolation"],
             "afUnixPathnameSockets": result["afUnixPathnameSockets"],
             "networkNamespace": result["namespaces"]["network"],
             "pidNamespace": result["namespaces"]["pid"],
             "namespacePid": result["namespaces"]["namespacePid"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inside-unit", action="store_true")
    parser.add_argument("--bindings-json")
    args = parser.parse_args(argv)
    try:
        bound = json.loads(args.bindings_json or "{}")
        if args.inside_unit:
            receipt = service_entry(bound)
        else:
            _live(bound)
            receipt = launch(bound, sys.stdin.buffer.fileno())
        print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
        return 0
    except Exception as error:
        reason = str(error) if (
            isinstance(error, LaunchBlocked) and
            re.fullmatch(r"[A-Z0-9_]+", str(error))) else "LAUNCH_FAILED"
        print(json.dumps({
            "status": "BLOCKED", "reason": reason,
            "resumeRequired": True, "commitState": "UNPROVEN",
            "outputState": "UNPROVEN",
        }, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
