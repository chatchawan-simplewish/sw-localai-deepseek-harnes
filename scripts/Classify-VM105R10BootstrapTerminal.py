"""Classify the committed R10 terminal locally without creating an R11 result."""

import hashlib
import json
import os
from pathlib import Path
import stat


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
R10_ATTEMPT_PATH = REPOSITORY_ROOT / "docs/evidence/vm105-dsh-reconstruction-sudoers-narrowing-phase13-r10-attempt-20260915.json"
R10_TERMINAL_PATH = REPOSITORY_ROOT / "docs/evidence/vm105-dsh-reconstruction-sudoers-narrowing-phase13-r10-20260915.json"
R11_RESULT_PATH = REPOSITORY_ROOT / "docs/evidence/vm105-r10-bootstrap-classification-phase13-r11-20260915.json"
R10_ATTEMPT_SHA256 = "8c0d7b153fcde1c508f917a4b434c183c6fc42b625f7ab7ab7b7c93fc0a3a32b"
R10_TERMINAL_SHA256 = "e48e7739e95a358560585d3bd0670b62a8087d63d3dfceb934390125c17c8432"
R10_BINDING_SHA256 = "d5ba2a1514b2359c395332b82be300897c17166b5f066d194ccbee24552e48e5"
CLASSIFICATION = "PRE_REPLACEMENT_BOOTSTRAP_REJECTION_CAUSE_UNATTRIBUTED"

ATTEMPT = {
    "bindingSha256": R10_BINDING_SHA256,
    "generation": "phase13-r10-action-20260915",
    "rawOutputStored": False,
    "reason": "NONE",
    "retryAuthorized": False,
    "status": "ATTEMPTED",
    "targetExecuted": False,
}
TERMINAL = {
    "bindingSha256": R10_BINDING_SHA256,
    "candidateValidationCode": -1,
    "captureExactAllowed": False,
    "fullPolicyState": "UNSUPPORTED",
    "generation": "phase13-r10-action-20260915",
    "rawOutputStored": False,
    "reason": "BOOTSTRAP_REJECTED",
    "reconstructionExactAllowed": False,
    "retryAuthorized": False,
    "rollbackCreated": False,
    "rollbackPath": "",
    "rollbackSha256": "",
    "rollbackSize": 0,
    "rollbackStatus": "NOT_NEEDED",
    "status": "BLOCKED",
    "targetExecuted": False,
    "targetPath": "/etc/sudoers.d/90-cloud-init-users",
}


class ClassificationBlocked(RuntimeError):
    pass


def canonical_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def canonical_line(value):
    return canonical_bytes(value) + b"\n"


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _stable(path, expected, limit=65536):
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
        identity = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
        if len(raw) > limit or _sha(raw) != expected or identity != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
            raise OSError()
        return raw
    except OSError:
        raise ClassificationBlocked("R10_RECORD_PIN_REJECTED") from None


def _absent(path, lstat):
    try:
        lstat(path)
    except FileNotFoundError:
        return
    except OSError:
        raise ClassificationBlocked("R11_RESULT_STATE_UNKNOWN") from None
    raise ClassificationBlocked("R11_RESULT_ALREADY_EXISTS")


def _validate_record(raw, expected_sha256, expected, reason):
    try:
        value = json.loads(raw)
        unsigned = dict(value)
        receipt = unsigned.pop("receiptSha256")
        if (_sha(raw) != expected_sha256 or canonical_line(value) != raw or
                set(value) != set(expected) | {"receiptSha256"} or
                any(type(value[key]) is not type(expected[key]) or value[key] != expected[key]
                    for key in expected) or
                not isinstance(receipt, str) or receipt != _sha(canonical_bytes(unsigned))):
            raise ValueError()
    except (ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError):
        raise ClassificationBlocked(reason) from None


def classify(*, read_file=_stable, lstat=os.lstat):
    """Return the only safe R11 classification frame; this function never writes it."""
    _absent(R11_RESULT_PATH, lstat)
    attempt = read_file(R10_ATTEMPT_PATH, R10_ATTEMPT_SHA256)
    terminal = read_file(R10_TERMINAL_PATH, R10_TERMINAL_SHA256)
    _validate_record(attempt, R10_ATTEMPT_SHA256, ATTEMPT, "R10_ATTEMPT_REJECTED")
    _validate_record(terminal, R10_TERMINAL_SHA256, TERMINAL, "R10_TERMINAL_REJECTED")
    return {
        "classification": CLASSIFICATION,
        "repairAuthorized": False,
        "retryAuthorized": False,
        "r10AttemptSha256": R10_ATTEMPT_SHA256,
        "r10TerminalSha256": R10_TERMINAL_SHA256,
        "targetContacted": False,
    }


if __name__ == "__main__":
    raise SystemExit(2)
