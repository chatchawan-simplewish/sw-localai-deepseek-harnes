"""Inert R12 bootstrap diagnostic; production uses only its pinned successor transport."""

import base64
import hashlib
import json
import os
from pathlib import Path
import stat


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
GENERATION = "phase13-r12-bootstrap-diagnostic-20260915"
ATTEMPT_PATH = REPOSITORY_ROOT / "docs/evidence/vm105-r12-bootstrap-diagnostic-phase13-attempt-20260915.json"
TERMINAL_PATH = REPOSITORY_ROOT / "docs/evidence/vm105-r12-bootstrap-diagnostic-phase13-20260915.json"
CONTRACT_PATH = REPOSITORY_ROOT / "docs/contracts/vm105-r12-bootstrap-diagnostic-contract-20260915.md"
TEST_PATH = REPOSITORY_ROOT / "scripts/tests/test_vm105_r12_bootstrap_diagnostic.py"
R11_SOURCE_PATH = REPOSITORY_ROOT / "scripts/Classify-VM105R10BootstrapTerminal.py"
R11_BOUNDARY_PATH = REPOSITORY_ROOT / "docs/handoffs/2026-09-15-vm105-r11-source-only-terminal-boundary.md"
SUCCESSOR_PATH = REPOSITORY_ROOT / "scripts/Invoke-VM105ReconstructionSuccessor.py"
SOURCE_REVIEW_PATH = REPOSITORY_ROOT / "docs/evidence/vm105-r12-bootstrap-diagnostic-source-review-20260915.json"
SEALED_ACTION_REVIEW_PATH = REPOSITORY_ROOT / "docs/evidence/vm105-r12-bootstrap-diagnostic-sealed-action-review-20260915.json"
SOURCE_PATHS = (CONTRACT_PATH, Path(__file__).resolve(), TEST_PATH, R11_SOURCE_PATH, R11_BOUNDARY_PATH, SUCCESSOR_PATH)
REVIEW_PATHS = (SOURCE_REVIEW_PATH, SEALED_ACTION_REVIEW_PATH)
BINDING_PATHS = SOURCE_PATHS + REVIEW_PATHS


def canonical_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def canonical_line(value):
    return canonical_bytes(value) + b"\n"


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


ROOT_LAUNCHER = r'''import hashlib,json,os,sys
def c(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('ascii')
def out(reason,confirmed):
 d=json.loads(sys.stdin.buffer.read(512));assert set(d)=={'bindingSha256','generation'}
 v={'bindingSha256':d['bindingSha256'],'generation':d['generation'],'rawOutputStored':False,'reason':reason,'rootExecutionConfirmed':confirmed}
 v['receiptSha256']=hashlib.sha256(c(v)).hexdigest();sys.stdout.buffer.write(c(v)+b'\n')
out('ROOT_EXECUTION_CONFIRMED' if os.geteuid()==0 else 'ROOT_LAUNCHER_MISMATCH',os.geteuid()==0)
'''
ROOT_LAUNCHER_SHA256 = _sha(ROOT_LAUNCHER.encode("ascii"))
ROOT_LAUNCHER_B64 = base64.b64encode(ROOT_LAUNCHER.encode("ascii")).decode("ascii")
ROOT_EXPRESSION = "import base64;exec(base64.b64decode('" + ROOT_LAUNCHER_B64 + "'))"
REMOTE_WRAPPER = r'''import hashlib,json,subprocess,sys
def c(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('ascii')
def out(reason,confirmed=False):
 v={'bindingSha256':d['bindingSha256'],'generation':d['generation'],'rawOutputStored':False,'reason':reason,'rootExecutionConfirmed':confirmed}
 v['receiptSha256']=hashlib.sha256(c(v)).hexdigest();sys.stdout.buffer.write(c(v)+b'\n')
try:
 raw=sys.stdin.buffer.read(512);d=json.loads(raw);assert c(d)+b'\n'==raw and set(d)=={'bindingSha256','generation'} and len(d['bindingSha256'])==64
 p=subprocess.run(['/usr/bin/sudo','-n','/usr/bin/python3.12','-I','-c',"''' + ROOT_EXPRESSION + r'''"],input=raw,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=15)
 if p.returncode!=0 or len(p.stdout)>512:out('ROOT_LAUNCHER_UNATTRIBUTED')
 else:sys.stdout.buffer.write(p.stdout)
except Exception:out('ROOT_LAUNCHER_UNATTRIBUTED')
'''
REMOTE_WRAPPER_SHA256 = _sha(REMOTE_WRAPPER.encode("ascii"))
REMOTE_COMMAND = "/usr/bin/env -i PATH=/usr/bin:/bin /usr/bin/python3.12 -I -c 'import base64;exec(base64.b64decode(\"" + base64.b64encode(REMOTE_WRAPPER.encode("ascii")).decode("ascii") + "\"))'"


class DiagnosticBlocked(RuntimeError):
    pass


def _stable(path, expected, limit=131072):
    try:
        before = os.lstat(path)
        if not stat.S_ISREG(before.st_mode):
            raise OSError()
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0))
        try:
            opened = os.fstat(fd)
            if not stat.S_ISREG(opened.st_mode) or (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino):
                raise OSError()
            raw = os.read(fd, limit + 1)
        finally:
            os.close(fd)
        after = os.lstat(path)
        if (len(raw) > limit or _sha(raw) != expected or
                (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) !=
                (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)):
            raise OSError()
        return raw
    except OSError:
        raise DiagnosticBlocked("SEALED_INPUT_REJECTED") from None


def _absent(path):
    try:
        os.lstat(path)
    except FileNotFoundError:
        return
    except OSError:
        raise DiagnosticBlocked("EVIDENCE_STATE_UNKNOWN") from None
    raise DiagnosticBlocked("EVIDENCE_ALREADY_EXISTS")


def action_manifest(files, reviews, ssh_prefix_sha256):
    file_keys = {path.relative_to(REPOSITORY_ROOT).as_posix() for path in SOURCE_PATHS}
    review_keys = {path.relative_to(REPOSITORY_ROOT).as_posix() for path in REVIEW_PATHS}
    if (not isinstance(files, dict) or set(files) != file_keys or not isinstance(reviews, dict) or
            set(reviews) != review_keys or any(not isinstance(value, str) or len(value) != 64 for value in reviews.values()) or
            not isinstance(ssh_prefix_sha256, str) or len(ssh_prefix_sha256) != 64):
        raise DiagnosticBlocked("ACTION_MANIFEST_REJECTED")
    return {"generation": GENERATION, "files": dict(sorted(files.items())), "reviews": dict(sorted(reviews.items())),
            "freshLeaves": [path.relative_to(REPOSITORY_ROOT).as_posix() for path in (ATTEMPT_PATH, TERMINAL_PATH)],
            "rootLauncherSha256": ROOT_LAUNCHER_SHA256, "remoteWrapperSha256": REMOTE_WRAPPER_SHA256,
            "remoteCommandSha256": _sha(REMOTE_COMMAND.encode("ascii")), "sshPrefixSha256": ssh_prefix_sha256,
            "transportSourcePath": SUCCESSOR_PATH.relative_to(REPOSITORY_ROOT).as_posix(),
            "transportSourceSha256": files[SUCCESSOR_PATH.relative_to(REPOSITORY_ROOT).as_posix()]}


def _validate_reviews(manifest):
    for path in REVIEW_PATHS:
        key = path.relative_to(REPOSITORY_ROOT).as_posix()
        raw = _stable(path, manifest["reviews"][key])
        try:
            value = json.loads(raw)
            if (set(value) != {"generation", "status", "pins"} or canonical_line(value) != raw or
                    value["generation"] != GENERATION or value["status"] != "PASS" or
                    value["pins"] != manifest["files"]):
                raise ValueError()
        except (KeyError, ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError):
            raise DiagnosticBlocked("REVIEW_PROVENANCE_REJECTED") from None


def prepare_action(manifest):
    _absent(ATTEMPT_PATH)
    _absent(TERMINAL_PATH)
    if not isinstance(manifest, dict) or set(manifest) != {"generation", "files", "reviews", "freshLeaves", "rootLauncherSha256", "remoteWrapperSha256", "remoteCommandSha256", "sshPrefixSha256", "transportSourcePath", "transportSourceSha256"}:
        raise DiagnosticBlocked("ACTION_MANIFEST_REJECTED")
    expected = action_manifest(manifest.get("files"), manifest.get("reviews"), manifest.get("sshPrefixSha256"))
    if manifest != expected:
        raise DiagnosticBlocked("ACTION_MANIFEST_REJECTED")
    for path in SOURCE_PATHS:
        key = path.relative_to(REPOSITORY_ROOT).as_posix()
        _stable(path, manifest["files"][key])
    _validate_reviews(manifest)
    successor = _stable(SUCCESSOR_PATH, manifest["files"][SUCCESSOR_PATH.relative_to(REPOSITORY_ROOT).as_posix()])
    transport_namespace = {"__name__": "vm105_r12_ssh_pin", "__file__": str(SUCCESSOR_PATH)}
    exec(compile(successor, str(SUCCESSOR_PATH), "exec"), transport_namespace)
    prefix = transport_namespace.get("SSH_COMMAND_PREFIX")
    transport = transport_namespace.get("_run_ssh")
    if (not isinstance(prefix, tuple) or not prefix or not all(isinstance(item, str) and item for item in prefix) or
            _sha(canonical_bytes(list(prefix))) != manifest["sshPrefixSha256"] or not callable(transport)):
        raise DiagnosticBlocked("SSH_PREFIX_REJECTED")
    return {"authorized": False, "bindingSha256": _sha(canonical_bytes(manifest)), "sshPrefix": list(prefix), "transport": transport}


def _signed(binding, status, reason, confirmed):
    value = {"bindingSha256": binding, "generation": GENERATION, "rawOutputStored": False,
             "reason": reason, "retryAuthorized": False, "rootExecutionConfirmed": confirmed,
             "status": status, "targetExecuted": False}
    value["receiptSha256"] = _sha(canonical_bytes(value))
    return value


def _validate_remote(raw, binding):
    try:
        value = json.loads(raw)
        unsigned = dict(value)
        receipt = unsigned.pop("receiptSha256")
        expected = {"bindingSha256", "generation", "rawOutputStored", "reason", "rootExecutionConfirmed", "receiptSha256"}
        if (set(value) != expected or canonical_line(value) != raw or receipt != _sha(canonical_bytes(unsigned)) or
                value.get("generation") != GENERATION or value.get("bindingSha256") != binding or
                value.get("rawOutputStored") is not False or type(value.get("rootExecutionConfirmed")) is not bool or
                value.get("reason") not in {"ROOT_LAUNCHER_MISMATCH", "ROOT_LAUNCHER_UNATTRIBUTED", "ROOT_EXECUTION_CONFIRMED"}):
            raise ValueError()
        if value["reason"] == "ROOT_EXECUTION_CONFIRMED" and value["rootExecutionConfirmed"] is not True:
            raise ValueError()
        if value["reason"] != "ROOT_EXECUTION_CONFIRMED" and value["rootExecutionConfirmed"] is not False:
            raise ValueError()
        return value
    except (KeyError, ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError):
        raise DiagnosticBlocked("REMOTE_FRAME_REJECTED") from None


def _publish_exclusive(path, raw):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0), 0o600)
    try:
        view = memoryview(raw)
        while view:
            written = os.write(fd, view)
            if not written:
                raise OSError("short evidence write")
            view = view[written:]
        os.fsync(fd)
    finally:
        os.close(fd)


def run_diagnostic(authority_sha256, manifest):
    if not isinstance(authority_sha256, str) or len(authority_sha256) != 64:
        raise DiagnosticBlocked("R12_DIAGNOSTIC_NOT_AUTHORIZED")
    prepared = prepare_action(manifest)
    binding = prepared["bindingSha256"]
    if authority_sha256 != binding:
        raise DiagnosticBlocked("R12_DIAGNOSTIC_NOT_AUTHORIZED")
    transport = prepared["transport"]
    _publish_exclusive(ATTEMPT_PATH, canonical_line(_signed(binding, "ATTEMPTED", "NONE", False)))
    try:
        code, raw, stderr = transport(prepared["sshPrefix"] + [REMOTE_COMMAND], canonical_line({"bindingSha256": binding, "generation": GENERATION}))
        if type(code) is not int or not isinstance(raw, bytes) or not isinstance(stderr, bytes) or code != 0 or stderr or len(raw) > 512:
            raise RuntimeError()
    except Exception:
        terminal = _signed(binding, "UNKNOWN", "TRANSPORT_FAILURE", False)
    else:
        try:
            remote = _validate_remote(raw, binding)
            terminal = _signed(binding, "PASS" if remote["reason"] == "ROOT_EXECUTION_CONFIRMED" else "BLOCKED", remote["reason"], remote["rootExecutionConfirmed"])
        except DiagnosticBlocked:
            terminal = _signed(binding, "BLOCKED", "ROOT_LAUNCHER_MISMATCH", False)
    _publish_exclusive(TERMINAL_PATH, canonical_line(terminal))
    return terminal


if __name__ == "__main__":
    raise SystemExit(2)
