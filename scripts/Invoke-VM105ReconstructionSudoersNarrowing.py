"""Dormant, source-only plan for the reviewed VM105 R10 sudoers transition."""

import hashlib
import json
import os
from pathlib import Path
import stat


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
GENERATION = "phase13-r10-20260915"
R9_SOURCE_PATH = REPOSITORY_ROOT / "scripts/Capture-VM105ReconstructionCaptureSudoPolicy.py"
R9_SOURCE_SHA256 = "62f92a608e3a836e68466f485bb585fb54fe0d09f8c2d2d8174b7dc5bf42248d"
R9_RECEIPT_PATH = REPOSITORY_ROOT / "docs/evidence/vm105-dsh-reconstruction-capture-sudo-policy-discovery-phase13-r9-20260915.json"
R9_RECEIPT_RAW_SHA256 = "6f948f4b57199f54da8c9c267140eff37afffa961c3ad59ae694c697fdfb3c6f"
R9_RECEIPT_SELF_SHA256 = "43858d3d3e993546a5cfc7d4589ac6eebd660b177446810173403d08342aa7b8"
ATTEMPT_PATH = REPOSITORY_ROOT / "docs/evidence/vm105-dsh-reconstruction-sudoers-narrowing-phase13-r10-attempt-20260915.json"
TERMINAL_PATH = REPOSITORY_ROOT / "docs/evidence/vm105-dsh-reconstruction-sudoers-narrowing-phase13-r10-20260915.json"
TARGET_PATH = "/etc/sudoers.d/90-cloud-init-users"
ROLLBACK_ROOT = "/var/tmp/omniroute-dsh-sudoers-r10-"
VISUDO_PATH = "/usr/sbin/visudo"
TEMPORARY_CANDIDATE_PATH = "/var/tmp/omniroute-dsh-sudoers-r10-candidate"
STEPS = [
    "validate-current-policy", "create-root-rollback", "validate-candidate-with-visudo",
    "atomic-replace", "exact-query-attestation", "semantic-attestation-or-rollback",
]


class NarrowingBlocked(RuntimeError):
    pass


def canonical_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def canonical_line(value):
    return canonical_bytes(value) + b"\n"


def signed(value):
    unsigned = dict(value)
    unsigned["receiptSha256"] = hashlib.sha256(canonical_bytes(unsigned)).hexdigest()
    return unsigned


def _stable_source(path, expected_sha256, *, limit=1024 * 1024):
    descriptor = None
    try:
        before = os.lstat(path)
        if not stat.S_ISREG(before.st_mode):
            raise NarrowingBlocked("REVIEWED_INPUT_REJECTED")
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_BINARY", 0) |
                             getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0))
        digest = hashlib.sha256()
        chunks, size = [], 0
        while True:
            chunk = os.read(descriptor, min(65536, limit + 1 - size))
            if not chunk:
                break
            size += len(chunk)
            if size > limit:
                raise NarrowingBlocked("REVIEWED_INPUT_REJECTED")
            chunks.append(chunk)
            digest.update(chunk)
        after = os.lstat(path)
        identity = lambda item: (item.st_dev, item.st_ino, item.st_mode, item.st_size, item.st_mtime_ns)
        if identity(before) != identity(after) or digest.hexdigest() != expected_sha256:
            raise NarrowingBlocked("REVIEWED_INPUT_REJECTED")
        return b"".join(chunks)
    except NarrowingBlocked:
        raise
    except (OSError, ValueError):
        raise NarrowingBlocked("REVIEWED_INPUT_REJECTED") from None
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _r9_context(read_source=_stable_source):
    source = read_source(R9_SOURCE_PATH, R9_SOURCE_SHA256)
    namespace = {"__name__": "vm105_reviewed_r9", "__file__": str(R9_SOURCE_PATH)}
    exec(compile(source, str(R9_SOURCE_PATH), "exec"), namespace)
    required = {"_reviewed_context"}
    if not required.issubset(namespace) or namespace.get("GENERATION") != "phase13-r9-20260915":
        raise NarrowingBlocked("REVIEWED_SOURCE_REJECTED")
    _successor, details = namespace["_reviewed_context"]()
    required_details = {
        "captureTargetArgc", "captureTargetArgvSha256", "captureBootstrapSha256",
        "reconstructionTargetArgc", "reconstructionTargetArgvSha256",
        "reconstructionBootstrapSha256",
    }
    if not required_details.issubset(details):
        raise NarrowingBlocked("REVIEWED_SOURCE_REJECTED")
    return details


def _validate_r9(read_evidence):
    raw = read_evidence(R9_RECEIPT_PATH, R9_RECEIPT_RAW_SHA256)
    try:
        value = json.loads(raw)
        if (canonical_line(value) != raw or hashlib.sha256(raw).hexdigest() != R9_RECEIPT_RAW_SHA256 or
                value.get("receiptSha256") != R9_RECEIPT_SELF_SHA256):
            raise ValueError()
        unsigned = dict(value)
        receipt = unsigned.pop("receiptSha256")
        required = {
            "generation": "phase13-r9-20260915", "status": "PASS", "reason": "NONE",
            "captureExactCommandAllowed": True, "reconstructionExactCommandAllowed": True,
            "fullPolicyState": "BROAD", "targetExecuted": False,
            "rawOutputStored": False, "retryAuthorized": False,
            "policySources": ["/etc/sudoers", TARGET_PATH],
        }
        if any(value.get(key) != expected for key, expected in required.items()):
            raise ValueError()
        if hashlib.sha256(canonical_bytes(unsigned)).hexdigest() != receipt:
            raise ValueError()
        return value
    except (TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError):
        raise NarrowingBlocked("R9_PROVENANCE_REJECTED") from None


def _require_absent(path, lstat):
    try:
        lstat(path)
    except FileNotFoundError:
        return
    except OSError:
        raise NarrowingBlocked("EVIDENCE_STATE_UNKNOWN") from None
    raise NarrowingBlocked("EVIDENCE_ALREADY_EXISTS")


def _binding(details):
    return {
        "generation": GENERATION,
        "attemptPath": ATTEMPT_PATH.relative_to(REPOSITORY_ROOT).as_posix(),
        "terminalPath": TERMINAL_PATH.relative_to(REPOSITORY_ROOT).as_posix(),
        "reviewedSourcePath": R9_SOURCE_PATH.relative_to(REPOSITORY_ROOT).as_posix(),
        "reviewedSourceSha256": R9_SOURCE_SHA256,
        "r9ReceiptPath": R9_RECEIPT_PATH.relative_to(REPOSITORY_ROOT).as_posix(),
        "r9ReceiptRawSha256": R9_RECEIPT_RAW_SHA256,
        "r9ReceiptSelfSha256": R9_RECEIPT_SELF_SHA256,
        "targetPath": TARGET_PATH, "rollbackRoot": ROLLBACK_ROOT, "visudoPath": VISUDO_PATH,
        "temporaryCandidatePath": TEMPORARY_CANDIDATE_PATH,
        "captureArgc": details["captureTargetArgc"],
        "captureArgvSha256": details["captureTargetArgvSha256"],
        "captureBootstrapSha256": details["captureBootstrapSha256"],
        "reconstructionArgc": details["reconstructionTargetArgc"],
        "reconstructionArgvSha256": details["reconstructionTargetArgvSha256"],
        "reconstructionBootstrapSha256": details["reconstructionBootstrapSha256"],
        "steps": STEPS,
    }


_INITIAL_DETAILS = _r9_context()
BINDING = _binding(_INITIAL_DETAILS)
BINDING_SHA256 = hashlib.sha256(canonical_bytes(BINDING)).hexdigest()
ACCEPTED_BINDING_SHA256 = "6892d1003043f06160d1d7db3b2fadae918eadc02a0ab09ae2d2d4e373300116"
del _INITIAL_DETAILS


def transition_plan(authority_sha256, *, lstat=os.lstat, read_evidence=_stable_source):
    _require_absent(ATTEMPT_PATH, lstat)
    _require_absent(TERMINAL_PATH, lstat)
    if authority_sha256 != ACCEPTED_BINDING_SHA256 or BINDING_SHA256 != ACCEPTED_BINDING_SHA256:
        raise NarrowingBlocked("SUDOERS_NARROWING_NOT_AUTHORIZED")
    r9 = _validate_r9(read_evidence)
    details = _r9_context()
    plan = dict(_binding(details))
    if plan != BINDING or r9["captureTargetArgvSha256"] != plan["captureArgvSha256"] or \
            r9["reconstructionTargetArgvSha256"] != plan["reconstructionArgvSha256"]:
        raise NarrowingBlocked("R9_PROVENANCE_REJECTED")
    plan["authorized"] = False
    return plan


def dormant_receipt(plan, reason):
    if (not isinstance(plan, dict) or plan.get("authorized") is not False or
            plan.get("steps") != STEPS or reason != "NOT_AUTHORIZED"):
        raise NarrowingBlocked("DORMANT_RECEIPT_REJECTED")
    return signed({
        "status": "DORMANT", "reason": reason, "generation": GENERATION,
        "bindingSha256": BINDING_SHA256, "targetPath": TARGET_PATH,
        "targetExecuted": False, "rollbackCreated": False,
        "rawOutputStored": False, "retryAuthorized": False,
    })
