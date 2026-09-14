"""One-shot, read-only VM105 sudo version and policy discovery."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
GENERATION = "phase13-sudo-discovery-20260915"
SUCCESSOR_PATH = REPOSITORY_ROOT / "scripts/Invoke-VM105ReconstructionSuccessor.py"
SUCCESSOR_SHA256 = "b30366f98a22e1a77fbd24451248111adb884280e625d0ac0844d62fb881c960"
ATTEMPT_PATH = REPOSITORY_ROOT / "docs/evidence/vm105-dsh-reconstruction-sudo-discovery-phase13-attempt-20260915.json"
TERMINAL_PATH = REPOSITORY_ROOT / "docs/evidence/vm105-dsh-reconstruction-sudo-discovery-phase13-20260915.json"


class DiscoveryBlocked(RuntimeError):
    pass


def _stable_source(path, expected_sha256, *, limit=1024 * 1024):
    descriptor = None
    try:
        before = os.lstat(path)
        if not stat.S_ISREG(before.st_mode):
            raise DiscoveryBlocked("REVIEWED_SOURCE_REJECTED")
        descriptor = os.open(
            path,
            os.O_RDONLY | getattr(os, "O_BINARY", 0) |
            getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
        )
        opened = os.fstat(descriptor)
        chunks = []
        digest = hashlib.sha256()
        size = 0
        while True:
            chunk = os.read(descriptor, min(65536, limit + 1 - size))
            if not chunk:
                break
            size += len(chunk)
            if size > limit:
                raise DiscoveryBlocked("REVIEWED_SOURCE_REJECTED")
            chunks.append(chunk)
            digest.update(chunk)
        after_fd = os.fstat(descriptor)
        after_path = os.lstat(path)
        path_identity = lambda value: (
            value.st_dev, value.st_ino, value.st_mode, value.st_size, value.st_mtime_ns,
        )
        descriptor_identity = lambda value: path_identity(value) + (value.st_ctime_ns,)
        if (path_identity(before) != path_identity(opened) or
                descriptor_identity(opened) != descriptor_identity(after_fd) or
                path_identity(before) != path_identity(after_path) or
                digest.hexdigest() != expected_sha256):
            raise DiscoveryBlocked("REVIEWED_SOURCE_REJECTED")
        return b"".join(chunks)
    except DiscoveryBlocked:
        raise
    except (OSError, ValueError):
        raise DiscoveryBlocked("REVIEWED_SOURCE_REJECTED") from None
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _reviewed_context():
    source = _stable_source(SUCCESSOR_PATH, SUCCESSOR_SHA256)
    namespace = {"__name__": "vm105_reviewed_reconstruction_successor", "__file__": str(SUCCESSOR_PATH)}
    exec(compile(source, str(SUCCESSOR_PATH), "exec"), namespace)
    required = {
        "SSH_COMMAND_PREFIX", "SUDO_FULL_QUERY_BOOTSTRAP", "_run_ssh",
        "_reconstruction_command_details", "_parse_full_sudo_policy",
        "canonical_bytes", "canonical_line", "signed", "_publish_exclusive",
    }
    if not required.issubset(namespace):
        raise DiscoveryBlocked("REVIEWED_SOURCE_REJECTED")
    closed = (
        "ACCEPTED_PREREQUISITE_CAPTURE_BINDING_SHA256",
        "ACCEPTED_RECONSTRUCTION_DISPATCH_BINDING_SHA256",
        "ACCEPTED_BUNDLE_RECEIPT_RAW_SHA256",
        "ACCEPTED_BUNDLE_RECEIPT_SELF_SHA256",
        "ACCEPTED_SUDO_RECEIPT_RAW_SHA256",
        "ACCEPTED_SUDO_RECEIPT_SELF_SHA256",
        "ACCEPTED_SUDO_VERSION",
        "ACCEPTED_LIVE_BINDINGS",
    )
    if any(namespace.get(name) is not None for name in closed):
        raise DiscoveryBlocked("REVIEWED_GATES_NOT_CLOSED")
    details = namespace["_reconstruction_command_details"]()
    prefix = list(namespace["SSH_COMMAND_PREFIX"])
    if (details.get("sudoExactQueryCommand", [])[:-1] != prefix or
            details.get("sudoFullQueryCommand", [])[:-1] != prefix or
            details.get("dispatchCommand", [])[:-1] != prefix):
        raise DiscoveryBlocked("REVIEWED_COMMANDS_REJECTED")
    return namespace, details


def _binding(namespace, details):
    bootstrap = namespace["SUDO_FULL_QUERY_BOOTSTRAP"].encode("ascii")
    return {
        "generation": GENERATION,
        "attemptPath": ATTEMPT_PATH.relative_to(REPOSITORY_ROOT).as_posix(),
        "terminalPath": TERMINAL_PATH.relative_to(REPOSITORY_ROOT).as_posix(),
        "loadedSourceSha256": SUCCESSOR_SHA256,
        "targetArgc": details["targetArgc"],
        "targetArgvSha256": details["targetArgvSha256"],
        "reconstructionBootstrapBytes": details["bootstrapBytes"],
        "reconstructionBootstrapSha256": details["bootstrapSha256"],
        "sudoFullQueryBootstrapBytes": len(bootstrap),
        "sudoFullQueryBootstrapSha256": hashlib.sha256(bootstrap).hexdigest(),
        "sudoExactQueryCommand": details["sudoExactQueryCommand"],
        "sudoFullQueryCommand": details["sudoFullQueryCommand"],
    }


_INITIAL_NAMESPACE, _INITIAL_DETAILS = _reviewed_context()
DISCOVERY_BINDING = _binding(_INITIAL_NAMESPACE, _INITIAL_DETAILS)
DISCOVERY_BINDING_SHA256 = hashlib.sha256(
    _INITIAL_NAMESPACE["canonical_bytes"](DISCOVERY_BINDING)).hexdigest()
ACCEPTED_DISCOVERY_BINDING_SHA256 = "9aabf6718dea7dc914d4cfac70f3651bd626055f8af0247c582d2d09f9dae427"
del _INITIAL_NAMESPACE, _INITIAL_DETAILS


def _require_absent(path, lstat):
    try:
        lstat(path)
    except FileNotFoundError:
        return
    except OSError:
        raise DiscoveryBlocked("EVIDENCE_STATE_UNKNOWN") from None
    raise DiscoveryBlocked("EVIDENCE_ALREADY_EXISTS")


def _unknown(namespace, details):
    return namespace["signed"]({
        "status": "UNKNOWN", "reason": "SUDO_DISCOVERY_UNCERTAIN",
        "generation": GENERATION, "bindingSha256": DISCOVERY_BINDING_SHA256,
        "loadedSourceSha256": SUCCESSOR_SHA256,
        "targetArgc": details["targetArgc"], "targetArgvSha256": details["targetArgvSha256"],
        "bootstrapBytes": details["bootstrapBytes"],
        "bootstrapSha256": details["bootstrapSha256"],
        "sudoVersion": "", "exactCommandAllowed": False, "policyState": "UNKNOWN",
        "exactQueryReturnCode": -1, "fullQueryReturnCode": -1,
        "exactQueryOutputSha256": "", "fullQueryOutputSha256": "",
        "targetExecuted": False, "rawOutputStored": False, "retryAuthorized": False,
    })


def _classify(namespace, details, exact_code, exact_raw, full_code, full_raw):
    try:
        frame = json.loads(full_raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise DiscoveryBlocked("SUDO_DISCOVERY_SCHEMA_UNCERTAIN") from None
    version = frame.get("sudoVersion") if isinstance(frame, dict) else None
    if (not isinstance(frame, dict) or set(frame) != {"sudoVersion", "policy"} or
            namespace["canonical_line"](frame) != full_raw or
            not isinstance(version, str) or
            re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:p[0-9]+)?", version) is None or
            not isinstance(frame["policy"], str)):
        raise DiscoveryBlocked("SUDO_DISCOVERY_SCHEMA_UNCERTAIN")
    namespace["ACCEPTED_SUDO_VERSION"] = version
    try:
        policy_state, parsed_version = namespace["_parse_full_sudo_policy"](full_raw, details)
    finally:
        namespace["ACCEPTED_SUDO_VERSION"] = None
    if parsed_version != version or policy_state not in {"EXACT", "BROAD", "UNSUPPORTED"}:
        raise DiscoveryBlocked("SUDO_DISCOVERY_SCHEMA_UNCERTAIN")
    return namespace["signed"]({
        "status": "PASS", "reason": "NONE", "generation": GENERATION,
        "bindingSha256": DISCOVERY_BINDING_SHA256, "loadedSourceSha256": SUCCESSOR_SHA256,
        "targetArgc": details["targetArgc"], "targetArgvSha256": details["targetArgvSha256"],
        "bootstrapBytes": details["bootstrapBytes"],
        "bootstrapSha256": details["bootstrapSha256"],
        "sudoVersion": version, "exactCommandAllowed": exact_code == 0,
        "policyState": policy_state, "exactQueryReturnCode": exact_code,
        "fullQueryReturnCode": full_code,
        "exactQueryOutputSha256": hashlib.sha256(exact_raw).hexdigest(),
        "fullQueryOutputSha256": hashlib.sha256(full_raw).hexdigest(),
        "targetExecuted": False, "rawOutputStored": False, "retryAuthorized": False,
    })


def capture_sudo_discovery(authority_sha256, *, transport=None, lstat=os.lstat):
    namespace, details = _reviewed_context()
    binding = _binding(namespace, details)
    computed = hashlib.sha256(namespace["canonical_bytes"](binding)).hexdigest()
    if (ACCEPTED_DISCOVERY_BINDING_SHA256 != DISCOVERY_BINDING_SHA256 or
            computed != DISCOVERY_BINDING_SHA256 or authority_sha256 != DISCOVERY_BINDING_SHA256):
        raise DiscoveryBlocked("SUDO_DISCOVERY_NOT_AUTHORIZED")
    _require_absent(ATTEMPT_PATH, lstat)
    _require_absent(TERMINAL_PATH, lstat)
    publish = namespace["_publish_exclusive"]
    attempt = namespace["signed"]({
        "status": "ATTEMPTED", "reason": "NONE", "generation": GENERATION,
        "bindingSha256": DISCOVERY_BINDING_SHA256, "loadedSourceSha256": SUCCESSOR_SHA256,
        "targetArgc": details["targetArgc"], "targetArgvSha256": details["targetArgvSha256"],
        "targetExecuted": False, "rawOutputStored": False, "retryAuthorized": False,
    })
    publish(ATTEMPT_PATH, namespace["canonical_line"](attempt))
    run_ssh = transport or namespace["_run_ssh"]
    terminal = None
    try:
        exact_code, exact_raw, exact_stderr = run_ssh(details["sudoExactQueryCommand"], b"")
        full_code, full_raw, full_stderr = run_ssh(details["sudoFullQueryCommand"], b"")
        if exact_code not in (0, 1) or full_code != 0 or exact_stderr or full_stderr:
            terminal = _unknown(namespace, details)
        else:
            terminal = _classify(namespace, details, exact_code, exact_raw, full_code, full_raw)
    except Exception:
        terminal = _unknown(namespace, details)
    publish(TERMINAL_PATH, namespace["canonical_line"](terminal))
    return terminal


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true", required=True)
    parser.parse_args(argv)
    try:
        terminal = capture_sudo_discovery(ACCEPTED_DISCOVERY_BINDING_SHA256)
    except DiscoveryBlocked:
        return 2
    return 0 if terminal["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
