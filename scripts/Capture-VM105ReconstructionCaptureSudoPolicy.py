"""One-shot discovery of VM105 capture and reconstruction sudo policy."""

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import stat


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
GENERATION = "phase13-r8-20260915"
SUCCESSOR_PATH = REPOSITORY_ROOT / "scripts/Invoke-VM105ReconstructionSuccessor.py"
SUCCESSOR_SHA256 = "d929842db8f1ddc978d321761a36f07a875e07d3edc63b5301ac87a92f69abb4"
ATTEMPT_PATH = REPOSITORY_ROOT / "docs/evidence/vm105-dsh-reconstruction-capture-sudo-policy-discovery-phase13-r8-attempt-20260915.json"
TERMINAL_PATH = REPOSITORY_ROOT / "docs/evidence/vm105-dsh-reconstruction-capture-sudo-policy-discovery-phase13-r8-20260915.json"
DELIVERY_PROVENANCE_PATH = REPOSITORY_ROOT / "docs/evidence/vm105-dsh-reconstruction-bundle-delivery-phase13-r2-20260915.json"
SPENT_R4_CAPTURE_PATH = REPOSITORY_ROOT / "docs/evidence/vm105-dsh-reconstruction-bundle-phase13-r4-20260915.json"
SPENT_R5_POLICY_PATH = REPOSITORY_ROOT / "docs/evidence/vm105-dsh-reconstruction-capture-sudo-policy-discovery-phase13-r5-20260915.json"
SPENT_R6_POLICY_PATH = REPOSITORY_ROOT / "docs/evidence/vm105-dsh-reconstruction-capture-sudo-policy-discovery-phase13-r6-20260915.json"
SPENT_R7_POLICY_PATH = REPOSITORY_ROOT / "docs/evidence/vm105-dsh-reconstruction-capture-sudo-policy-discovery-phase13-r7-20260915.json"
DELIVERY_PROVENANCE = {
    "path": DELIVERY_PROVENANCE_PATH.relative_to(REPOSITORY_ROOT).as_posix(),
    "rawSha256": "d3739ef37d16c76f3aa29eefc461b6660e091620b37d3dbc6e9b68179f9e831c",
    "selfSha256": "d1990c9414ca647c36639fd703d0aef200ff7dd11d7678e779bcc6531fa68340",
    "status": "PASS", "reason": "NONE", "remoteState": "PROVEN_PASS",
    "retryAuthorized": False,
}
SPENT_R4_CAPTURE_PROVENANCE = {
    "path": SPENT_R4_CAPTURE_PATH.relative_to(REPOSITORY_ROOT).as_posix(),
    "rawSha256": "a588740fcdb447b0ab1cf425ca53062a0577c7d8f439dd6467964efa082f2745",
    "selfSha256": "e2239a359200d814e23de1c19214f5c28eda2c591ac1b528c2779af5d6c14b96",
    "status": "UNKNOWN", "reason": "BUNDLE_CAPTURE_TRANSPORT_UNKNOWN",
    "retryAuthorized": False,
}
SPENT_R5_POLICY_PROVENANCE = {
    "path": SPENT_R5_POLICY_PATH.relative_to(REPOSITORY_ROOT).as_posix(),
    "rawSha256": "eb1ed671ca295fe6206864e95a1b33d30d8d10b98e0f11893bfe6304a5d51364",
    "selfSha256": "64387da1bd30ec80cc6d0c1b85788416a6b7d28fe874e7f97f5841ebe020b033",
    "status": "UNKNOWN", "reason": "SUDO_POLICY_DISCOVERY_UNCERTAIN",
    "retryAuthorized": False,
}
SPENT_R6_POLICY_PROVENANCE = {
    "path": SPENT_R6_POLICY_PATH.relative_to(REPOSITORY_ROOT).as_posix(),
    "rawSha256": "615d7a51ad5daa178291ee7ec659316efa067f479e9684afd3877045c5829611",
    "selfSha256": "5d6604f39572c4f184ab7c5cc8ca30963fb059935683bd1338a0a084cd9d059e",
    "status": "UNKNOWN", "reason": "SUDO_POLICY_DISCOVERY_UNCERTAIN",
    "retryAuthorized": False,
}
SPENT_R7_POLICY_PROVENANCE = {
    "path": SPENT_R7_POLICY_PATH.relative_to(REPOSITORY_ROOT).as_posix(),
    "rawSha256": "46504f5109471bc060a6b930e3d177d47832334d4e22cdfde330fb3e44fff9b4",
    "selfSha256": "5d191a1a43599443e892e4a7a50426d2ab7683f22d94d22efed1f35c1c35a484",
    "status": "UNKNOWN", "reason": "SUDO_POLICY_DISCOVERY_UNCERTAIN",
    "retryAuthorized": False,
}


class DiscoveryBlocked(RuntimeError):
    pass


def _stable_source(path, expected_sha256, *, limit=1024 * 1024):
    descriptor = None
    try:
        before = os.lstat(path)
        if not stat.S_ISREG(before.st_mode):
            raise DiscoveryBlocked("REVIEWED_INPUT_REJECTED")
        descriptor = os.open(
            path, os.O_RDONLY | getattr(os, "O_BINARY", 0) |
            getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
        )
        opened = os.fstat(descriptor)
        digest = hashlib.sha256()
        chunks = []
        size = 0
        while True:
            chunk = os.read(descriptor, min(65536, limit + 1 - size))
            if not chunk:
                break
            size += len(chunk)
            if size > limit:
                raise DiscoveryBlocked("REVIEWED_INPUT_REJECTED")
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
            raise DiscoveryBlocked("REVIEWED_INPUT_REJECTED")
        return b"".join(chunks)
    except DiscoveryBlocked:
        raise
    except (OSError, ValueError):
        raise DiscoveryBlocked("REVIEWED_INPUT_REJECTED") from None
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _capture_expression(namespace):
    encoded = base64.b64encode(namespace["BUNDLE_CAPTURE_REMOTE_BOOTSTRAP"].encode("ascii")).decode("ascii")
    return 'import base64;exec(base64.b64decode("' + encoded + '"))'


def _reviewed_context():
    source = _stable_source(SUCCESSOR_PATH, SUCCESSOR_SHA256)
    namespace = {"__name__": "vm105_reviewed_r4_successor", "__file__": str(SUCCESSOR_PATH)}
    exec(compile(source, str(SUCCESSOR_PATH), "exec"), namespace)
    required = {
        "SSH_COMMAND_PREFIX", "BUNDLE_CAPTURE_REMOTE_BOOTSTRAP", "_capture_remote_command",
        "_reconstruction_command_details", "_sudo_full_query_command", "_run_ssh",
        "canonical_bytes", "canonical_line", "signed", "_publish_exclusive",
        "PREREQUISITE_CAPTURE_BINDING_SHA256",
    }
    if not required.issubset(namespace):
        raise DiscoveryBlocked("REVIEWED_SOURCE_REJECTED")
    if (namespace.get("GENERATION") != "phase13-r4-20260915" or
            namespace.get("ACCEPTED_PREREQUISITE_CAPTURE_BINDING_SHA256") !=
            namespace.get("PREREQUISITE_CAPTURE_BINDING_SHA256") or
            namespace.get("ACCEPTED_SUDO_VERSION") != "1.9.15p5" or
            any(namespace.get(name) is not None for name in (
                "ACCEPTED_BUNDLE_DELIVERY_BINDING_SHA256",
                "ACCEPTED_RECONSTRUCTION_DISPATCH_BINDING_SHA256",
                "ACCEPTED_BUNDLE_RECEIPT_RAW_SHA256", "ACCEPTED_BUNDLE_RECEIPT_SELF_SHA256",
                "ACCEPTED_SUDO_RECEIPT_RAW_SHA256", "ACCEPTED_SUDO_RECEIPT_SELF_SHA256",
                "ACCEPTED_LIVE_BINDINGS",
            ))):
        raise DiscoveryBlocked("REVIEWED_GATES_REJECTED")

    reconstruction = namespace["_reconstruction_command_details"]()
    capture_bootstrap = namespace["BUNDLE_CAPTURE_REMOTE_BOOTSTRAP"].encode("ascii")
    capture_target = ["/usr/bin/python3.12", "-I", "-c", _capture_expression(namespace)]
    capture_policy = " ".join(capture_target)
    capture_query = "/usr/bin/sudo -n -l -- " + " ".join(
        shlex.quote(value) for value in capture_target)
    prefix = list(namespace["SSH_COMMAND_PREFIX"])
    full_query = namespace["_sudo_full_query_command"]()
    if (reconstruction["sudoExactQueryCommand"][:-1] != prefix or
            reconstruction["sudoFullQueryCommand"] != full_query or
            full_query[:-1] != prefix or
            namespace["_capture_remote_command"]().count("/usr/bin/sudo") != 0):
        raise DiscoveryBlocked("REVIEWED_COMMANDS_REJECTED")
    details = {
        "captureTargetArgv": capture_target,
        "capturePolicyCommand": capture_policy,
        "captureTargetArgc": len(capture_target),
        "captureTargetArgvSha256": hashlib.sha256(
            namespace["canonical_bytes"](capture_target)).hexdigest(),
        "captureBootstrapBytes": len(capture_bootstrap),
        "captureBootstrapSha256": hashlib.sha256(capture_bootstrap).hexdigest(),
        "captureCommand": prefix + [namespace["_capture_remote_command"]()],
        "captureExactQueryCommand": prefix + [capture_query],
        "reconstructionTargetArgc": reconstruction["targetArgc"],
        "reconstructionTargetArgvSha256": reconstruction["targetArgvSha256"],
        "reconstructionBootstrapBytes": reconstruction["bootstrapBytes"],
        "reconstructionBootstrapSha256": reconstruction["bootstrapSha256"],
        "reconstructionPolicyCommand": reconstruction["sudoPolicyCommand"],
        "reconstructionExactQueryCommand": reconstruction["sudoExactQueryCommand"],
        "reconstructionDispatchCommand": reconstruction["dispatchCommand"],
        "sudoFullQueryCommand": full_query,
    }
    return namespace, details


def _binding(namespace, details):
    return {
        "generation": GENERATION,
        "policySourceSchema": "safe-absolute-paths-only",
        "attemptPath": ATTEMPT_PATH.relative_to(REPOSITORY_ROOT).as_posix(),
        "terminalPath": TERMINAL_PATH.relative_to(REPOSITORY_ROOT).as_posix(),
        "loadedSourceSha256": SUCCESSOR_SHA256,
        "deliveryProvenance": DELIVERY_PROVENANCE,
        "spentR4CaptureProvenance": SPENT_R4_CAPTURE_PROVENANCE,
        "spentR5PolicyProvenance": SPENT_R5_POLICY_PROVENANCE,
        "spentR6PolicyProvenance": SPENT_R6_POLICY_PROVENANCE,
        "spentR7PolicyProvenance": SPENT_R7_POLICY_PROVENANCE,
        **{key: details[key] for key in (
            "captureTargetArgc", "captureTargetArgvSha256", "captureBootstrapBytes",
            "captureBootstrapSha256", "captureExactQueryCommand", "reconstructionTargetArgc",
            "reconstructionTargetArgvSha256", "reconstructionBootstrapBytes",
            "reconstructionBootstrapSha256", "reconstructionExactQueryCommand",
            "sudoFullQueryCommand",
        )},
    }


_INITIAL_NAMESPACE, _INITIAL_DETAILS = _reviewed_context()
DISCOVERY_BINDING = _binding(_INITIAL_NAMESPACE, _INITIAL_DETAILS)
DISCOVERY_BINDING_SHA256 = hashlib.sha256(
    _INITIAL_NAMESPACE["canonical_bytes"](DISCOVERY_BINDING)).hexdigest()
ACCEPTED_DISCOVERY_BINDING_SHA256 = "220c426ae58e6b6b02100d1093b918a5efc6b603e8682d51efb527a18d2b514b"
del _INITIAL_NAMESPACE, _INITIAL_DETAILS


def _validate_provenance(namespace, read_evidence):
    for path, expected, required in (
        (DELIVERY_PROVENANCE_PATH, DELIVERY_PROVENANCE, {
            "status": "PASS", "reason": "NONE", "remoteState": "PROVEN_PASS",
            "retryAuthorized": False,
        }),
        (SPENT_R4_CAPTURE_PATH, SPENT_R4_CAPTURE_PROVENANCE, {
            "status": "UNKNOWN", "reason": "BUNDLE_CAPTURE_TRANSPORT_UNKNOWN",
        }),
        (SPENT_R5_POLICY_PATH, SPENT_R5_POLICY_PROVENANCE, {
            "status": "UNKNOWN", "reason": "SUDO_POLICY_DISCOVERY_UNCERTAIN",
            "retryAuthorized": False,
        }),
        (SPENT_R6_POLICY_PATH, SPENT_R6_POLICY_PROVENANCE, {
            "status": "UNKNOWN", "reason": "SUDO_POLICY_DISCOVERY_UNCERTAIN",
            "retryAuthorized": False,
        }),
        (SPENT_R7_POLICY_PATH, SPENT_R7_POLICY_PROVENANCE, {
            "status": "UNKNOWN", "reason": "SUDO_POLICY_DISCOVERY_UNCERTAIN",
            "retryAuthorized": False,
        }),
    ):
        raw = read_evidence(path, expected["rawSha256"])
        try:
            value = json.loads(raw)
            if (namespace["canonical_line"](value) != raw or
                    hashlib.sha256(raw).hexdigest() != expected["rawSha256"] or
                    value.get("receiptSha256") != expected["selfSha256"] or
                    any(value.get(key) != wanted for key, wanted in required.items())):
                raise ValueError()
            unsigned = dict(value)
            receipt = unsigned.pop("receiptSha256")
            if hashlib.sha256(namespace["canonical_bytes"](unsigned)).hexdigest() != receipt:
                raise ValueError()
        except (TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError):
            raise DiscoveryBlocked("PROVENANCE_REJECTED") from None


def _require_absent(path, lstat):
    try:
        lstat(path)
    except FileNotFoundError:
        return
    except OSError:
        raise DiscoveryBlocked("EVIDENCE_STATE_UNKNOWN") from None
    raise DiscoveryBlocked("EVIDENCE_ALREADY_EXISTS")


def _safe_source(value):
    match = re.fullmatch(
        r"/etc/sudoers|/etc/sudoers\.d/([A-Za-z0-9](?:[A-Za-z0-9_.-]*[A-Za-z0-9])?)",
        value,
    )
    if match is None or match.group(1) is not None and ".." in match.group(1):
        raise DiscoveryBlocked("SUDO_POLICY_SOURCE_REJECTED")
    return value


def _parse_policy(policy, details):
    if not isinstance(policy, str) or "\r" in policy or "\0" in policy or not policy.endswith("\n"):
        raise DiscoveryBlocked("SUDO_POLICY_GRAMMAR_REJECTED")
    lines = policy.splitlines()
    host = r"[A-Za-z0-9](?:[A-Za-z0-9.-]{0,252}[A-Za-z0-9])?"
    index = 0
    defaults_state = "EXACT"
    defaults = re.fullmatch(r"Matching Defaults entries for dsh on (" + host + r"):", lines[0]) if lines else None
    defaults_host = defaults.group(1) if defaults is not None else None
    if defaults is not None:
        index = 1
        values = []
        while index < len(lines) and not lines[index].startswith("User dsh may run "):
            if lines[index]:
                if not lines[index].startswith("    "):
                    raise DiscoveryBlocked("SUDO_POLICY_GRAMMAR_REJECTED")
                values.extend(part.strip().replace(r"\:", ":") for part in lines[index].split(","))
            index += 1
        safe = {
            "env_reset", "mail_badpass", "use_pty",
            "secure_path=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        }
        unexpected = [value for value in values if value and value not in safe]
        if unexpected:
            authorizing = any(re.search(
                r"(?:^|_)(?:!?authenticate|exempt_group|runas_default|targetpw|rootpw|runaspw)(?:=|$)",
                value, re.IGNORECASE) for value in unexpected)
            defaults_state = "BROAD" if authorizing else "UNSUPPORTED"
    user = (re.fullmatch(r"User dsh may run the following commands on (" + host + r"):",
                         lines[index]) if index < len(lines) else None)
    if user is None or defaults_host is not None and user.group(1) != defaults_host:
        raise DiscoveryBlocked("SUDO_POLICY_GRAMMAR_REJECTED")
    index += 1
    while index < len(lines) and not lines[index]:
        index += 1

    entries = []
    while index < len(lines):
        entry = re.fullmatch(r"Sudoers entry: (.+)", lines[index])
        if entry is None:
            raise DiscoveryBlocked("SUDO_POLICY_GRAMMAR_REJECTED")
        source = _safe_source(entry.group(1))
        index += 1
        expected = ["    RunAsUsers: root", "    Options: !authenticate", "    Commands:"]
        if lines[index:index + 3] != expected:
            raise DiscoveryBlocked("SUDO_POLICY_GRAMMAR_REJECTED")
        index += 3
        commands = []
        while index < len(lines) and lines[index].startswith("\t"):
            command = lines[index][1:]
            if not command:
                raise DiscoveryBlocked("SUDO_POLICY_GRAMMAR_REJECTED")
            commands.append(command)
            index += 1
        if not commands:
            raise DiscoveryBlocked("SUDO_POLICY_GRAMMAR_REJECTED")
        while index < len(lines) and not lines[index]:
            index += 1
        entries.append((source, commands))

    targets = {details["capturePolicyCommand"], details["reconstructionPolicyCommand"]}
    commands = [command for _, row in entries for command in row]
    exact_present = {command for command in commands if command in targets}
    broad = any(
        command not in targets or any(token in command for token in ("*", "?", "[", "]")) or
        re.fullmatch(r"(?:NOPASSWD:\s*)?ALL", command, re.IGNORECASE) is not None or
        re.search(r"/(?:bin|usr/bin)/(?:sh|bash|dash|zsh)(?:\s|$)", command, re.IGNORECASE)
        for command in commands
    )
    sources = []
    for source, _ in entries:
        if source not in sources:
            sources.append(source)
    sources.sort()
    if broad or defaults_state == "BROAD":
        return "BROAD", sources, exact_present
    full = ("EXACT" if defaults_state == "EXACT" and set(commands) == targets and
            len(commands) == 2 else "UNSUPPORTED")
    return full, sources, exact_present


def _terminal(namespace, details, *, status, reason, exact_codes=(-1, -1), full_code=-1,
              states=("UNSUPPORTED", "UNSUPPORTED", "UNSUPPORTED"), sources=(), hashes=("", "", "")):
    return namespace["signed"]({
        "status": status, "reason": reason, "generation": GENERATION,
        "bindingSha256": DISCOVERY_BINDING_SHA256, "loadedSourceSha256": SUCCESSOR_SHA256,
        "captureTargetArgc": details["captureTargetArgc"],
        "captureTargetArgvSha256": details["captureTargetArgvSha256"],
        "captureBootstrapBytes": details["captureBootstrapBytes"],
        "captureBootstrapSha256": details["captureBootstrapSha256"],
        "reconstructionTargetArgc": details["reconstructionTargetArgc"],
        "reconstructionTargetArgvSha256": details["reconstructionTargetArgvSha256"],
        "reconstructionBootstrapBytes": details["reconstructionBootstrapBytes"],
        "reconstructionBootstrapSha256": details["reconstructionBootstrapSha256"],
        "sudoVersion": "1.9.15p5" if status == "PASS" else "",
        "captureExactCommandAllowed": exact_codes[0] == 0,
        "reconstructionExactCommandAllowed": exact_codes[1] == 0,
        "captureCommandState": states[0], "reconstructionCommandState": states[1],
        "fullPolicyState": states[2], "policySources": list(sources),
        "captureExactQueryReturnCode": exact_codes[0],
        "reconstructionExactQueryReturnCode": exact_codes[1],
        "fullQueryReturnCode": full_code,
        "captureExactQueryOutputSha256": hashes[0],
        "reconstructionExactQueryOutputSha256": hashes[1],
        "fullQueryOutputSha256": hashes[2],
        "targetExecuted": False, "rawOutputStored": False, "retryAuthorized": False,
    })


def _classify(namespace, details, capture_code, capture_raw, reconstruction_code,
              reconstruction_raw, full_code, full_raw):
    hashes = tuple(hashlib.sha256(raw).hexdigest() for raw in (
        capture_raw, reconstruction_raw, full_raw))
    try:
        frame = json.loads(full_raw)
        if (not isinstance(frame, dict) or set(frame) != {"sudoVersion", "policy"} or
                namespace["canonical_line"](frame) != full_raw or
                frame["sudoVersion"] != "1.9.15p5"):
            raise DiscoveryBlocked("SUDO_POLICY_FRAME_REJECTED")
        full_state, sources, exact_present = _parse_policy(frame["policy"], details)
        codes = (capture_code, reconstruction_code)
        command_states = []
        for code, target in zip(codes, (
                details["capturePolicyCommand"], details["reconstructionPolicyCommand"])):
            command_states.append(
                "UNSUPPORTED" if code != 0 else
                "BROAD" if full_state == "BROAD" else
                "EXACT" if target in exact_present else "UNSUPPORTED")
        if full_state == "EXACT" and command_states != ["EXACT", "EXACT"]:
            full_state = "UNSUPPORTED"
        return _terminal(
            namespace, details, status="PASS", reason="NONE", exact_codes=codes,
            full_code=full_code, states=(*command_states, full_state),
            sources=sources, hashes=hashes,
        )
    except DiscoveryBlocked as error:
        reason = str(error)
        if reason not in {"SUDO_POLICY_FRAME_REJECTED", "SUDO_POLICY_GRAMMAR_REJECTED",
                          "SUDO_POLICY_SOURCE_REJECTED"}:
            reason = "SUDO_POLICY_DISCOVERY_UNCERTAIN"
        return _terminal(namespace, details, status="UNKNOWN", reason=reason,
                         exact_codes=(capture_code, reconstruction_code), full_code=full_code,
                         hashes=hashes)
    except (KeyError, TypeError, UnicodeDecodeError, json.JSONDecodeError):
        return _terminal(namespace, details, status="UNKNOWN", reason="SUDO_POLICY_FRAME_REJECTED",
                         exact_codes=(capture_code, reconstruction_code), full_code=full_code,
                         hashes=hashes)


def capture_policy_discovery(authority_sha256, *, transport=None, lstat=os.lstat,
                             publish=None, read_evidence=_stable_source):
    namespace, details = _reviewed_context()
    computed = hashlib.sha256(namespace["canonical_bytes"](_binding(namespace, details))).hexdigest()
    if (ACCEPTED_DISCOVERY_BINDING_SHA256 != DISCOVERY_BINDING_SHA256 or
            computed != DISCOVERY_BINDING_SHA256 or authority_sha256 != DISCOVERY_BINDING_SHA256):
        raise DiscoveryBlocked("SUDO_POLICY_DISCOVERY_NOT_AUTHORIZED")
    _validate_provenance(namespace, read_evidence)
    _require_absent(ATTEMPT_PATH, lstat)
    _require_absent(TERMINAL_PATH, lstat)
    publish = publish or namespace["_publish_exclusive"]
    publish(ATTEMPT_PATH, namespace["canonical_line"](namespace["signed"]({
        "status": "ATTEMPTED", "reason": "NONE", "generation": GENERATION,
        "bindingSha256": DISCOVERY_BINDING_SHA256, "loadedSourceSha256": SUCCESSOR_SHA256,
        "targetExecuted": False, "rawOutputStored": False, "retryAuthorized": False,
    })))
    run = transport or namespace["_run_ssh"]
    try:
        capture_code, capture_raw, capture_stderr = run(details["captureExactQueryCommand"], b"")
        reconstruction_code, reconstruction_raw, reconstruction_stderr = run(
            details["reconstructionExactQueryCommand"], b"")
        full_code, full_raw, full_stderr = run(details["sudoFullQueryCommand"], b"")
        raws = (capture_raw, reconstruction_raw, full_raw)
        if (capture_code not in (0, 1) or reconstruction_code not in (0, 1) or
                full_code != 0 or capture_stderr or reconstruction_stderr or full_stderr or
                any(not isinstance(raw, bytes) or len(raw) > 262144 for raw in raws)):
            terminal = _terminal(
                namespace, details, status="UNKNOWN", reason="SUDO_POLICY_DISCOVERY_UNCERTAIN")
        else:
            terminal = _classify(
                namespace, details, capture_code, capture_raw, reconstruction_code,
                reconstruction_raw, full_code, full_raw)
    except RuntimeError as error:
        reason = str(error)
        if re.fullmatch(r"SSH_(?:START_FAILED|TIMEOUT|OUTPUT_LIMIT_EXCEEDED|DRAIN_FAILED|STDIN_FAILED)", reason) is None:
            reason = "SUDO_POLICY_DISCOVERY_UNCERTAIN"
        terminal = _terminal(namespace, details, status="UNKNOWN", reason=reason)
    except Exception:
        terminal = _terminal(
            namespace, details, status="UNKNOWN", reason="SUDO_POLICY_DISCOVERY_UNCERTAIN")
    publish(TERMINAL_PATH, namespace["canonical_line"](terminal))
    return terminal


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true", required=True)
    parser.parse_args(argv)
    try:
        terminal = capture_policy_discovery(ACCEPTED_DISCOVERY_BINDING_SHA256)
    except DiscoveryBlocked:
        return 2
    return 0 if terminal["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
