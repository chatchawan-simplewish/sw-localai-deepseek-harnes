import hashlib
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).with_name("Capture-VM105ReconstructionSudoVersion.py")
SPEC = importlib.util.spec_from_file_location("vm105_sudo_discovery", SCRIPT)
discovery = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(discovery)


class SudoDiscoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.namespace, cls.details = discovery._reviewed_context()

    def run_capture(self, transport, *, lstat=lambda _path: (_ for _ in ()).throw(FileNotFoundError())):
        published = {}
        publish = self.namespace["_publish_exclusive"]
        self.namespace["_publish_exclusive"] = lambda path, raw: published.setdefault(path, raw)
        try:
            with patch.object(discovery, "_reviewed_context", return_value=(self.namespace, self.details)):
                terminal = discovery.capture_sudo_discovery(
                    discovery.ACCEPTED_DISCOVERY_BINDING_SHA256,
                    transport=transport,
                    lstat=lstat,
                )
        finally:
            self.namespace["_publish_exclusive"] = publish
        return terminal, published

    def test_only_two_read_only_queries_run_and_raw_output_is_not_stored(self):
        calls = []
        exact_raw = b"EXACT-RAW-SECRET\n"
        full_raw = self.namespace["canonical_line"]({
            "sudoVersion": "1.9.13p3", "policy": "POLICY-RAW-SECRET\n",
        })

        def transport(command, payload):
            calls.append((command, payload))
            if command == self.details["sudoExactQueryCommand"]:
                return 0, exact_raw, b""
            if command == self.details["sudoFullQueryCommand"]:
                return 0, full_raw, b""
            self.fail("target command executed")

        terminal, published = self.run_capture(transport)
        self.assertEqual(
            [row[0] for row in calls],
            [self.details["sudoExactQueryCommand"], self.details["sudoFullQueryCommand"]],
        )
        self.assertTrue(all(row[1] == b"" for row in calls))
        self.assertNotIn(self.details["dispatchCommand"], [row[0] for row in calls])
        self.assertEqual(terminal["status"], "PASS")
        self.assertEqual(terminal["policyState"], "UNSUPPORTED")
        self.assertTrue(terminal["exactCommandAllowed"])
        persisted = b"".join(published.values())
        self.assertNotIn(b"EXACT-RAW-SECRET", persisted)
        self.assertNotIn(b"POLICY-RAW-SECRET", persisted)

    def test_occupied_leaf_stops_before_transport(self):
        for occupied in (discovery.ATTEMPT_PATH, discovery.TERMINAL_PATH):
            with self.subTest(occupied=occupied):
                calls = []

                def lstat(path):
                    if path == occupied:
                        return object()
                    raise FileNotFoundError()

                with self.assertRaisesRegex(discovery.DiscoveryBlocked, "EVIDENCE_ALREADY_EXISTS"):
                    self.run_capture(lambda *args: calls.append(args), lstat=lstat)
                self.assertEqual(calls, [])

    def test_attempt_and_terminal_are_canonical_and_self_hashed(self):
        policy = (
            "User dsh may run the following commands on vm105:\n\n"
            "Sudoers entry: /etc/sudoers.d/vm105\n"
            "    RunAsUsers: root\n"
            "    Options: !authenticate\n"
            "    Commands:\n"
            "        " + self.details["sudoPolicyCommand"] + "\n"
        )
        full_raw = self.namespace["canonical_line"]({
            "sudoVersion": "1.9.13p3", "policy": policy,
        })

        def transport(command, _payload):
            return ((0, b"", b"") if command == self.details["sudoExactQueryCommand"]
                    else (0, full_raw, b""))

        terminal, published = self.run_capture(transport)
        self.assertEqual(terminal["policyState"], "EXACT")
        for path in (discovery.ATTEMPT_PATH, discovery.TERMINAL_PATH):
            raw = published[path]
            value = json.loads(raw)
            self.assertEqual(raw, self.namespace["canonical_line"](value))
            unsigned = dict(value)
            receipt = unsigned.pop("receiptSha256")
            self.assertEqual(receipt, hashlib.sha256(
                self.namespace["canonical_bytes"](unsigned)).hexdigest())

    def test_transport_or_schema_uncertainty_is_sanitized(self):
        cases = (
            [(0, b"SECRET", b"stderr-secret"), (0, b"{}\n", b"")],
            [(0, b"SECRET", b""), (0, b"not-json SECRET", b"")],
        )
        for responses in cases:
            with self.subTest(responses=responses):
                iterator = iter(responses)
                terminal, published = self.run_capture(lambda *_args: next(iterator))
                self.assertEqual(terminal["status"], "UNKNOWN")
                self.assertEqual(terminal["policyState"], "UNKNOWN")
                self.assertFalse(terminal["retryAuthorized"])
                persisted = b"".join(published.values())
                self.assertNotIn(b"SECRET", persisted)
                self.assertNotIn(b"stderr-secret", persisted)


if __name__ == "__main__":
    unittest.main()
