import importlib.util
import base64
import errno
import hashlib
import json
from pathlib import Path
import stat
import threading
import types
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).with_name("Invoke-VM105ReconstructionPrerequisites.py")
SPEC = importlib.util.spec_from_file_location("vm105_reconstruction_prerequisites", SCRIPT)
prereq = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prereq)


class ReconstructionPrerequisiteTests(unittest.TestCase):
    SUDO_VERSION = "1.9.15p5"

    def bundle_receipt(self):
        files = [{
            "basename": row["basename"], "type": "regular", "symlink": False,
            "device": 1, "inode": index + 10, "mode": 0o440, "uid": 0, "gid": 0,
            "size": 100 + index, "mtimeNs": 3, "ctimeNs": 4, "sha256": row["sha256"],
        } for index, row in enumerate(prereq.BUNDLE_FILES)]
        return prereq.signed({
            "status": "PASS", "reason": "NONE", "vmHostname": "deepseek-harness-01",
            "vmMachineIdSha256": "a" * 64, "bundleRoot": prereq.BUNDLE_ROOT,
            "bundleDevice": 1, "bundleInode": 2, "bundleMode": 0o550,
            "bundleUid": 0, "bundleGid": 0, "bundleSize": 4096,
            "bundleMtimeNs": 3, "bundleCtimeNs": 4, "expectedFileCount": 5,
            "fileCount": 5, "files": files,
        })

    def sudo_receipt(self, target_sha="d" * 64):
        return prereq.signed({
            "status": "PASS", "reason": "NONE", "queryUser": "dsh",
            "sudoPath": "/usr/bin/sudo", "noninteractive": True,
            "targetArgc": 5, "targetArgvSha256": target_sha,
            "bootstrapBytes": prereq.RECONSTRUCTION_BOOTSTRAP_BYTES,
            "bootstrapSha256": prereq.RECONSTRUCTION_BOOTSTRAP_SHA256,
            "launcherSha256": prereq.LAUNCHER_SHA256,
            "effectivePolicySha256": "e" * 64, "exactCommandAllowed": True,
            "broaderAuthorityDetected": False, "rawOutputStored": False,
        })

    def command_details(self):
        return {
            "sudoExactQueryCommand": ["ssh", "exact-query"],
            "sudoFullQueryCommand": ["ssh", "full-query"],
            "sudoPolicyCommand": "EXACT_TARGET_ARGV",
            "targetArgc": 5, "targetArgvSha256": "d" * 64,
            "bootstrapBytes": prereq.RECONSTRUCTION_BOOTSTRAP_BYTES,
            "bootstrapSha256": prereq.RECONSTRUCTION_BOOTSTRAP_SHA256,
        }

    def full_policy_frame(self, command="EXACT_TARGET_ARGV", defaults=(),
                          source="", include_defaults_header=True):
        policy = ""
        if include_defaults_header:
            policy += "Matching Defaults entries for dsh on deepseek-harness-01:\n"
            if defaults:
                policy += "    " + ", ".join(defaults) + "\n"
            policy += "\n"
        policy += (
            "User dsh may run the following commands on deepseek-harness-01:\n\n"
            "Sudoers entry:" + ((" " + source) if source else "") + "\n"
            "    RunAsUsers: root\n"
            "    Options: !authenticate\n"
            "    Commands:\n"
            f"        {command}\n")
        return prereq.canonical_line({"sudoVersion": self.SUDO_VERSION,
                                      "policy": policy})

    def test_all_three_live_authorities_default_to_none(self):
        self.assertIsNone(prereq.ACCEPTED_BUNDLE_DELIVERY_BINDING_SHA256)
        self.assertIsNone(prereq.ACCEPTED_PREREQUISITE_CAPTURE_BINDING_SHA256)
        self.assertIsNone(prereq.ACCEPTED_RECONSTRUCTION_DISPATCH_BINDING_SHA256)
        with self.assertRaisesRegex(prereq.PrerequisiteBlocked,
                                    "BUNDLE_DELIVERY_NOT_EXECUTABLE"):
            prereq.deliver_bundle(
                prereq.BUNDLE_DELIVERY_BINDING_SHA256,
                lambda *_: self.fail("public binding hash must not authorize"),
                read_source=lambda *_: self.fail("source must not be read"))

    @patch.object(prereq, "ACCEPTED_BUNDLE_DELIVERY_BINDING_SHA256",
                  prereq.BUNDLE_DELIVERY_BINDING_SHA256)
    def test_delivery_uses_exact_five_pins_and_stops_on_occupied_evidence(self):
        calls = []

        def missing(_path):
            raise FileNotFoundError(errno.ENOENT, "absent")

        def transport(command, payload):
            calls.append((command, json.loads(payload)))
            remote = prereq.signed({
                "status": "PASS", "reason": "NONE",
                "finalRoot": prereq.BUNDLE_ROOT, "temporaryRoot": prereq.TEMP_BUNDLE_ROOT,
                "fileCount": 5, "renameCompleted": True, "parentFsync": True,
            })
            return 0, prereq.canonical_line(remote), b""

        published = {}
        code = prereq.deliver_bundle(
            prereq.BUNDLE_DELIVERY_BINDING_SHA256, transport,
            read_source=lambda _path, digest: bytes.fromhex(digest),
            lstat=missing, publish=lambda path, raw: published.setdefault(str(path), raw))
        self.assertEqual(0, code)
        command, payload = calls[0]
        self.assertEqual("--", command[command.index(prereq.SSH_TARGET) - 1])
        self.assertEqual(prereq.SSH_TARGET, command[command.index(prereq.SSH_TARGET)])
        self.assertEqual(
            [(row["basename"], row["sha256"]) for row in prereq.BUNDLE_FILES],
            [(row["basename"], row["sha256"]) for row in payload["files"]])
        self.assertTrue(all(base64.b64decode(row["content"]) == bytes.fromhex(row["sha256"])
                            for row in payload["files"]))
        terminal = json.loads(published[str(prereq.DELIVERY_TERMINAL_PATH)])
        self.assertEqual(("PASS", "PROVEN_PASS", False),
                         (terminal["status"], terminal["remoteState"], terminal["retryAuthorized"]))

        calls.clear()
        with self.assertRaisesRegex(prereq.PrerequisiteBlocked, "EVIDENCE_LEAF_OCCUPIED"):
            prereq.deliver_bundle(
                prereq.BUNDLE_DELIVERY_BINDING_SHA256, transport,
                read_source=lambda *_: b"", lstat=lambda _path: object(),
                publish=lambda *_: None)
        self.assertEqual([], calls)

    def test_local_source_read_is_nofollow_hash_pinned_and_stable(self):
        raw = b"fixed source"
        digest = hashlib.sha256(raw).hexdigest()

        def info(mode=stat.S_IFREG | 0o644, inode=7):
            return types.SimpleNamespace(st_dev=1, st_ino=inode, st_mode=mode,
                                         st_size=len(raw), st_mtime_ns=3, st_ctime_ns=4)

        accepted = info()
        reads = iter((raw, b""))
        opened = []
        actual = prereq.read_stable_source(
            Path("fixed"), digest, lstat=lambda _path: accepted,
            open_file=lambda _path, flags: opened.append(flags) or 9,
            fstat=lambda _fd: accepted, read=lambda *_: next(reads), close=lambda _fd: None)
        self.assertEqual(raw, actual)
        self.assertEqual(
            prereq.os.O_RDONLY | getattr(prereq.os, "O_BINARY", 0) |
            getattr(prereq.os, "O_CLOEXEC", 0) | getattr(prereq.os, "O_NOFOLLOW", 0),
            opened[0])

        with self.assertRaisesRegex(prereq.PrerequisiteBlocked, "LOCAL_SOURCE_REJECTED"):
            prereq.read_stable_source(
                Path("fixed"), digest, lstat=lambda _path: info(stat.S_IFLNK | 0o777),
                open_file=lambda *_: 9, fstat=lambda _fd: accepted,
                read=lambda *_: b"", close=lambda _fd: None)

    def test_remote_delivery_is_exact_and_atomic_noreplace(self):
        source = prereq.DELIVERY_REMOTE_BOOTSTRAP
        for row in prereq.BUNDLE_FILES:
            self.assertIn(row["basename"], source)
            self.assertIn(row["sha256"], source)
        self.assertIn('renameat2(-100,T.encode(),-100,F.encode(),1)', source)
        self.assertNotIn("os.rename(T,F)", source)
        self.assertIn("sorted(os.listdir(root))!=N", prereq.BUNDLE_CAPTURE_REMOTE_BOOTSTRAP)

    @patch.object(prereq, "ACCEPTED_PREREQUISITE_CAPTURE_BINDING_SHA256",
                  prereq.PREREQUISITE_CAPTURE_BINDING_SHA256)
    @patch.object(prereq, "ACCEPTED_SUDO_VERSION", SUDO_VERSION)
    def test_capture_accepts_only_fixed_bundle_rows_and_blocks_broad_sudo(self):
        published = {}

        def missing(_path):
            raise FileNotFoundError(errno.ENOENT, "absent")

        bundle_raw = prereq.canonical_line(self.bundle_receipt())
        sudo_calls = []

        def sudo_transport(command):
            sudo_calls.append(command)
            if command[-1] == "exact-query":
                return 0, b"(root) NOPASSWD: EXACT_TARGET_ARGV\n", b""
            return 0, self.full_policy_frame("ALL"), b""

        code = prereq.capture_prerequisites(
            prereq.PREREQUISITE_CAPTURE_BINDING_SHA256,
            bundle_transport=lambda command: (0, bundle_raw, b""),
            sudo_transport=sudo_transport, command_details=self.command_details,
            lstat=missing, publish=lambda path, raw: published.setdefault(str(path), raw))
        self.assertEqual(1, code)
        self.assertEqual(bundle_raw, published[str(prereq.BUNDLE_RECEIPT_PATH)])
        sudo = json.loads(published[str(prereq.SUDO_RECEIPT_PATH)])
        self.assertEqual(("BLOCKED", "BLOCKED_BROAD_SUDO_POLICY", True, True, False), (
            sudo["status"], sudo["reason"], sudo["exactCommandAllowed"],
            sudo["broaderAuthorityDetected"], sudo["rawOutputStored"]))
        self.assertNotIn("NOPASSWD", json.dumps(sudo))
        self.assertEqual([["ssh", "exact-query"], ["ssh", "full-query"]], sudo_calls)
        self.assertEqual({
            "status", "reason", "queryUser", "sudoPath", "noninteractive",
            "targetArgc", "targetArgvSha256", "bootstrapBytes", "bootstrapSha256",
            "launcherSha256", "effectivePolicySha256", "exactCommandAllowed",
            "broaderAuthorityDetected", "rawOutputStored", "receiptSha256",
        }, set(sudo))

        extra = self.bundle_receipt()
        unsigned = dict(extra); unsigned.pop("receiptSha256")
        unsigned["files"] = unsigned["files"] + [dict(unsigned["files"][0], basename="extra")]
        unsigned["fileCount"] = 6
        bad_raw = prereq.canonical_line(prereq.signed(unsigned))
        with self.assertRaisesRegex(prereq.PrerequisiteBlocked, "BUNDLE_RECEIPT_REJECTED"):
            prereq.capture_prerequisites(
                prereq.PREREQUISITE_CAPTURE_BINDING_SHA256,
                bundle_transport=lambda command: (0, bad_raw, b""),
                sudo_transport=lambda command: self.fail("sudo query must not run"),
                command_details=lambda: self.fail("command details must not be loaded"),
                lstat=missing, publish=lambda *_: None)

        for key, bad in (("bundleDevice", "1"), ("bundleSize", True),
                         ("files", {})):
            malformed = self.bundle_receipt()
            unsigned = dict(malformed); unsigned.pop("receiptSha256"); unsigned[key] = bad
            with self.subTest(key=key), self.assertRaisesRegex(
                    prereq.PrerequisiteBlocked, "BUNDLE_RECEIPT_REJECTED"):
                prereq.validate_bundle_receipt(
                    prereq.canonical_line(prereq.signed(unsigned)))

    @patch.object(prereq, "ACCEPTED_PREREQUISITE_CAPTURE_BINDING_SHA256",
                  prereq.PREREQUISITE_CAPTURE_BINDING_SHA256)
    @patch.object(prereq, "ACCEPTED_SUDO_VERSION", SUDO_VERSION)
    def test_exact_only_sudo_policy_passes_but_any_sudo_stderr_is_unknown(self):
        details = self.command_details()
        passed = prereq._sudo_receipt(
            0, b"exact command allowed\n", 0, self.full_policy_frame(), details)
        self.assertEqual(("PASS", "NONE", True, False), (
            passed["status"], passed["reason"], passed["exactCommandAllowed"],
            passed["broaderAuthorityDetected"]))

        published = {}

        def missing(_path):
            raise FileNotFoundError(errno.ENOENT, "absent")

        bundle_raw = prereq.canonical_line(self.bundle_receipt())
        responses = iter(((0, b"exact command allowed\n", b"private stderr"),
                          (0, self.full_policy_frame(), b"")))
        code = prereq.capture_prerequisites(
            prereq.PREREQUISITE_CAPTURE_BINDING_SHA256,
            bundle_transport=lambda _command: (0, bundle_raw, b""),
            sudo_transport=lambda _command: next(responses),
            command_details=self.command_details, lstat=missing,
            publish=lambda path, raw: published.setdefault(str(path), raw))
        self.assertEqual(1, code)
        sudo = json.loads(published[str(prereq.SUDO_RECEIPT_PATH)])
        self.assertEqual(("UNKNOWN", "SUDO_POLICY_TRANSPORT_UNKNOWN", False),
                         (sudo["status"], sudo["reason"], sudo["exactCommandAllowed"]))
        self.assertNotIn("private stderr", json.dumps(sudo))

    @patch.object(prereq, "ACCEPTED_SUDO_VERSION", SUDO_VERSION)
    def test_sudo_policy_allows_only_safe_defaults_and_source_metadata(self):
        details = self.command_details()
        safe = self.full_policy_frame(
            defaults=("env_reset", "mail_badpass", "use_pty",
                      "secure_path=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"),
            source="/etc/sudoers.d/vm105-reconstruction:12")
        receipt = prereq._sudo_receipt(0, b"exact\n", 0, safe, details)
        self.assertEqual(("PASS", False),
                         (receipt["status"], receipt["broaderAuthorityDetected"]))

        no_defaults_header = prereq._sudo_receipt(
            0, b"exact\n", 0,
            self.full_policy_frame(source="/etc/sudoers:42",
                                   include_defaults_header=False), details)
        self.assertEqual("PASS", no_defaults_header["status"])

        authorizing = prereq._sudo_receipt(
            0, b"exact\n", 0,
            self.full_policy_frame(defaults=("!authenticate",)), details)
        self.assertEqual(("BLOCKED", True),
                         (authorizing["status"], authorizing["broaderAuthorityDetected"]))

    @patch.object(prereq, "ACCEPTED_RECONSTRUCTION_DISPATCH_BINDING_SHA256",
                  prereq.RECONSTRUCTION_DISPATCH_BINDING_SHA256)
    def test_dispatch_requires_accepted_receipt_pins_then_reuses_launcher_coordinator(self):
        called = []
        with self.assertRaisesRegex(prereq.PrerequisiteBlocked, "RECEIPT_PINS_NOT_ACCEPTED"):
            prereq.dispatch_reconstruction(
                prereq.RECONSTRUCTION_DISPATCH_BINDING_SHA256,
                read_evidence=lambda *_: self.fail("receipt must not be read"),
                command_details=lambda: self.fail("launcher must not be loaded"))

        bundle_receipt = self.bundle_receipt()
        sudo_receipt = self.sudo_receipt()
        bundle_raw = prereq.canonical_line(bundle_receipt)
        sudo_raw = prereq.canonical_line(sudo_receipt)
        accepted = {
            "ACCEPTED_BUNDLE_RECEIPT_RAW_SHA256": hashlib.sha256(bundle_raw).hexdigest(),
            "ACCEPTED_BUNDLE_RECEIPT_SELF_SHA256": bundle_receipt["receiptSha256"],
            "ACCEPTED_SUDO_RECEIPT_RAW_SHA256": hashlib.sha256(sudo_raw).hexdigest(),
            "ACCEPTED_SUDO_RECEIPT_SELF_SHA256": sudo_receipt["receiptSha256"],
        }

        def run(command):
            called.append(("run", command))
            return 0, b"remote", b""

        def coordinate(receipt, marker, transport):
            called.append(("coordinate", Path(receipt), Path(marker), transport()))
            return 0

        command = list(prereq.SSH_COMMAND_PREFIX) + ["fixed-remote-command"]
        details = {
            "dispatchCommand": command, "targetArgc": 5,
            "targetArgvSha256": "d" * 64,
            "bootstrapBytes": prereq.RECONSTRUCTION_BOOTSTRAP_BYTES,
            "bootstrapSha256": prereq.RECONSTRUCTION_BOOTSTRAP_SHA256,
            "launcher": {
                "ACCEPTED_LIVE_BINDINGS": None,
                "_run_bounded_reconstruction_ssh": run,
                "_coordinate_reconstruction_attempt": coordinate,
            },
        }
        evidence = {str(prereq.BUNDLE_RECEIPT_PATH): bundle_raw,
                    str(prereq.SUDO_RECEIPT_PATH): sudo_raw}
        with patch.multiple(prereq, **accepted):
            with self.assertRaisesRegex(prereq.PrerequisiteBlocked,
                                        "RECEIPT_PINS_REJECTED"):
                prereq.dispatch_reconstruction(
                    prereq.RECONSTRUCTION_DISPATCH_BINDING_SHA256,
                    bundle_raw_sha256="0" * 64,
                    bundle_self_sha256=bundle_receipt["receiptSha256"],
                    sudo_raw_sha256=hashlib.sha256(sudo_raw).hexdigest(),
                    sudo_self_sha256=sudo_receipt["receiptSha256"],
                    read_evidence=lambda *_: self.fail("substituted pins must stop before read"),
                    command_details=lambda: self.fail("launcher must not load"))
            code = prereq.dispatch_reconstruction(
                prereq.RECONSTRUCTION_DISPATCH_BINDING_SHA256,
                bundle_raw_sha256=hashlib.sha256(bundle_raw).hexdigest(),
                bundle_self_sha256=bundle_receipt["receiptSha256"],
                sudo_raw_sha256=hashlib.sha256(sudo_raw).hexdigest(),
                sudo_self_sha256=sudo_receipt["receiptSha256"],
                read_evidence=lambda path, digest: evidence[str(path)],
                command_details=lambda: details)
        self.assertEqual(0, code)
        self.assertEqual(("run", command), called[0])
        self.assertEqual((prereq.DISPATCH_TERMINAL_PATH, prereq.DISPATCH_ATTEMPT_PATH),
                         called[1][1:3])

    def test_cli_modes_are_mutually_exclusive_and_dormant_before_transport(self):
        for mode in ("--deliver-bundle", "--capture-prerequisites",
                     "--dispatch-reconstruction"):
            with self.subTest(mode=mode):
                self.assertEqual(2, prereq.main(
                    [mode], ssh_transport=lambda *_args: self.fail("transport must stay dormant")))
        with self.assertRaises(SystemExit):
            prereq.build_parser().parse_args(
                ["--deliver-bundle", "--capture-prerequisites"])

    @patch.object(prereq, "ACCEPTED_PREREQUISITE_CAPTURE_BINDING_SHA256",
                  prereq.PREREQUISITE_CAPTURE_BINDING_SHA256)
    def test_capture_transport_error_publishes_sanitized_unknown(self):
        published = {}

        def missing(_path):
            raise FileNotFoundError(errno.ENOENT, "absent")

        code = prereq.capture_prerequisites(
            prereq.PREREQUISITE_CAPTURE_BINDING_SHA256,
            bundle_transport=lambda _command: (255, b"", b"private diagnostic"),
            sudo_transport=lambda _command: self.fail("sudo must not run"),
            command_details=lambda: self.fail("details must not load"), lstat=missing,
            publish=lambda path, raw: published.setdefault(str(path), raw))
        self.assertEqual(1, code)
        receipt = json.loads(published[str(prereq.BUNDLE_RECEIPT_PATH)])
        self.assertEqual(("UNKNOWN", "BUNDLE_CAPTURE_TRANSPORT_UNKNOWN", 0),
                         (receipt["status"], receipt["reason"], receipt["fileCount"]))
        self.assertNotIn("private diagnostic", json.dumps(receipt))

    def test_ssh_transport_streams_stdin_and_rejects_output_overflow(self):
        written = bytearray()
        input_closed = threading.Event()

        class Input:
            def write(self, chunk):
                written.extend(chunk)
                return len(chunk)

            def flush(self):
                pass

            def close(self):
                input_closed.set()

        class Output:
            def __init__(self, chunks):
                self.chunks = iter(chunks)

            def read(self, _size):
                return next(self.chunks, b"")

            def close(self):
                pass

        class Process:
            def __init__(self, stdout):
                self.stdin, self.stdout, self.stderr = Input(), stdout, Output([b""])
                self.killed = threading.Event()

            def wait(self, timeout):
                input_closed.wait(timeout)
                return 0

            def kill(self):
                self.killed.set()

        good = Process(Output([b"ok", b""]))
        self.assertEqual((0, b"ok", b""), prereq._run_ssh(
            ["ssh"], b"framed input", popen=lambda *_args, **_kwargs: good))
        self.assertEqual(b"framed input", bytes(written))

        overflow = Process(Output([b"too-large", b""]))
        with self.assertRaisesRegex(RuntimeError, "SSH_OUTPUT_LIMIT_EXCEEDED"):
            prereq._run_ssh(["ssh"], b"", popen=lambda *_args, **_kwargs: overflow,
                            max_stdout=3)
        self.assertTrue(overflow.killed.is_set())


if __name__ == "__main__":
    unittest.main()
