import errno
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest


SCRIPT = Path(__file__).parents[1] / "Capture-VM105ReconstructionCaptureSudoPolicy.py"
SPEC = importlib.util.spec_from_file_location("vm105_capture_sudo_policy", SCRIPT)
discovery = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(discovery)


class CaptureSudoPolicyDiscoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.namespace, cls.details = discovery._reviewed_context()

    @staticmethod
    def absent(path):
        raise FileNotFoundError(errno.ENOENT, "absent", path)

    def policy_frame(self, entries, *, version="1.9.15p5"):
        policy = (
            "Matching Defaults entries for dsh on vm105:\n"
            "    env_reset, mail_badpass, use_pty, secure_path=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin\n"
            "User dsh may run the following commands on vm105:\n\n" +
            "".join(
                f"Sudoers entry: {source}\n"
                "    RunAsUsers: root\n"
                "    Options: !authenticate\n"
                "    Commands:\n" +
                "".join(f"\t{command}\n" for command in commands)
                for source, commands in entries
            )
        )
        return self.namespace["canonical_line"]({"sudoVersion": version, "policy": policy})

    def run_capture(self, responses, *, lstat=None):
        calls = []
        published = {}
        iterator = iter(responses)

        def transport(command, payload):
            calls.append((command, payload))
            return next(iterator)

        terminal = discovery.capture_policy_discovery(
            discovery.ACCEPTED_DISCOVERY_BINDING_SHA256,
            transport=transport,
            lstat=lstat or self.absent,
            publish=lambda path, raw: published.setdefault(path, raw),
        )
        return terminal, calls, published

    def test_r4_unprivileged_capture_mismatch_is_corrected_only_in_policy_target(self):
        successor_capture = self.namespace["_capture_remote_command"]()
        expression = self.details["captureTargetArgv"][3]
        self.assertIn("/usr/bin/env -i PATH=/usr/bin:/bin /usr/bin/python3.12 -I -c", successor_capture)
        self.assertNotIn("/usr/bin/sudo -n", successor_capture)
        self.assertEqual(
            self.details["captureTargetArgv"],
            ["/usr/bin/python3.12", "-I", "-c", expression],
        )
        self.assertEqual(
            expression,
            discovery._capture_expression(self.namespace),
        )
        self.assertIn("/usr/bin/sudo -n -l -- /usr/bin/python3.12 -I -c",
                      self.details["captureExactQueryCommand"][-1])

    def test_only_two_exact_queries_and_full_query_run_without_target_dispatch(self):
        full = self.policy_frame([
            ("/etc/sudoers.d/vm105-reconstruction",
             [self.details["capturePolicyCommand"], self.details["reconstructionPolicyCommand"]]),
        ])
        terminal, calls, published = self.run_capture([
            (0, b"capture exact query output\n", b""),
            (0, b"reconstruction exact query output\n", b""),
            (0, full, b""),
        ])
        self.assertEqual([command for command, _ in calls], [
            self.details["captureExactQueryCommand"],
            self.details["reconstructionExactQueryCommand"],
            self.details["sudoFullQueryCommand"],
        ])
        self.assertTrue(all(payload == b"" for _, payload in calls))
        self.assertNotIn(self.details["captureCommand"], [command for command, _ in calls])
        self.assertNotIn(self.details["reconstructionDispatchCommand"],
                         [command for command, _ in calls])
        self.assertEqual((terminal["captureCommandState"],
                          terminal["reconstructionCommandState"],
                          terminal["fullPolicyState"]), ("EXACT", "EXACT", "EXACT"))
        self.assertEqual(terminal["policySources"],
                         ["/etc/sudoers.d/vm105-reconstruction"])
        self.assertFalse(terminal["targetExecuted"])
        self.assertFalse(terminal["rawOutputStored"])
        self.assertFalse(terminal["retryAuthorized"])
        self.assertEqual(set(published), {discovery.ATTEMPT_PATH, discovery.TERMINAL_PATH})

    def test_canonical_self_hashed_evidence_retains_no_raw_policy_or_stderr(self):
        secret = b"SECRET-POLICY-OR-STDERR"
        terminal, _calls, published = self.run_capture([
            (0, b"exact", b""),
            (0, b"exact", b""),
            (0, b"{}\n", secret),
        ])
        self.assertEqual(terminal["status"], "UNKNOWN")
        persisted = b"".join(published.values())
        self.assertNotIn(secret, persisted)
        self.assertNotIn(b"exact", persisted)
        for raw in published.values():
            value = json.loads(raw)
            self.assertEqual(raw, self.namespace["canonical_line"](value))
            unsigned = dict(value)
            receipt = unsigned.pop("receiptSha256")
            self.assertEqual(receipt, hashlib.sha256(
                self.namespace["canonical_bytes"](unsigned)).hexdigest())
            self.assertFalse(value["targetExecuted"])
            self.assertFalse(value["rawOutputStored"])
            self.assertFalse(value["retryAuthorized"])

    def test_broad_policy_is_classified_without_retaining_policy_text(self):
        full = self.policy_frame([
            ("/etc/sudoers", ["ALL"]),
        ])
        terminal, _calls, published = self.run_capture([
            (0, b"allowed", b""), (0, b"allowed", b""), (0, full, b""),
        ])
        self.assertEqual((terminal["captureCommandState"],
                          terminal["reconstructionCommandState"],
                          terminal["fullPolicyState"]), ("BROAD", "BROAD", "BROAD"))
        self.assertEqual(terminal["policySources"], ["/etc/sudoers"])
        self.assertNotIn(b"ALL", b"".join(published.values()))

    def test_only_1_9_15p5_inline_safe_absolute_sources_are_supported(self):
        command = self.details["reconstructionPolicyCommand"]
        valid = self.policy_frame([
            ("/etc/sudoers.d/vm105-safe_name", [command]),
        ])
        terminal, _calls, _published = self.run_capture([
            (1, b"denied", b""), (0, b"allowed", b""), (0, valid, b""),
        ])
        self.assertEqual(terminal["captureCommandState"], "UNSUPPORTED")
        self.assertEqual(terminal["reconstructionCommandState"], "EXACT")
        self.assertEqual(terminal["fullPolicyState"], "UNSUPPORTED")
        self.assertEqual(terminal["policySources"], ["/etc/sudoers.d/vm105-safe_name"])

        separate_source = json.loads(valid)
        separate_source["policy"] = separate_source["policy"].replace(
            "Sudoers entry: /etc/sudoers.d/vm105-safe_name\n",
            "Sudoers entry:\n    Source: /etc/sudoers.d/vm105-safe_name:9:2\n",
        )
        for bad in (
            self.policy_frame([("/etc/sudoers.d/vm105", [command])],
                              version="1.9.15p4"),
            self.policy_frame([("/tmp/not-sudoers", [command])]),
            self.policy_frame([("/etc/sudoers.d/../unsafe", [command])]),
            self.policy_frame([("/etc/sudoers.d/vm105:9:2", [command])]),
            self.namespace["canonical_line"](separate_source),
            valid.replace(
                b"Matching Defaults entries for dsh on vm105:",
                b"Matching Defaults entries for dsh on vm106:",
                1,
            ),
            valid[:-1] + b"EXTRA\n",
        ):
            with self.subTest(bad=bad[-30:]):
                result, _calls, published = self.run_capture([
                    (1, b"denied", b""), (0, b"allowed", b""), (0, bad, b""),
                ])
                self.assertEqual(result["status"], "UNKNOWN")
                self.assertNotIn(b"vm105-safe_name", b"".join(published.values()))

    def test_spent_or_uncertain_leaf_blocks_before_transport(self):
        for occupied in (discovery.ATTEMPT_PATH, discovery.TERMINAL_PATH):
            with self.subTest(occupied=occupied):
                calls = []

                def lstat(path):
                    if path == occupied:
                        return object()
                    raise FileNotFoundError(errno.ENOENT, "absent", path)

                with self.assertRaisesRegex(discovery.DiscoveryBlocked,
                                            "EVIDENCE_ALREADY_EXISTS"):
                    discovery.capture_policy_discovery(
                        discovery.ACCEPTED_DISCOVERY_BINDING_SHA256,
                        transport=lambda *args: calls.append(args), lstat=lstat,
                        publish=lambda *_: self.fail("published"),
                    )
                self.assertEqual(calls, [])

    def test_binding_includes_current_source_commands_and_spent_provenance(self):
        binding = discovery.DISCOVERY_BINDING
        self.assertEqual(binding["generation"], "phase13-r5-20260915")
        self.assertEqual(binding["loadedSourceSha256"], discovery.SUCCESSOR_SHA256)
        self.assertEqual(binding["deliveryProvenance"]["status"], "PASS")
        self.assertEqual(binding["spentR4CaptureProvenance"]["status"], "UNKNOWN")
        self.assertEqual(binding["spentR4CaptureProvenance"]["retryAuthorized"], False)
        self.assertEqual(binding["captureExactQueryCommand"],
                         self.details["captureExactQueryCommand"])
        self.assertEqual(binding["reconstructionExactQueryCommand"],
                         self.details["reconstructionExactQueryCommand"])
        self.assertEqual(binding["sudoFullQueryCommand"], self.details["sudoFullQueryCommand"])
        self.assertEqual(binding["policySourceSchema"], "safe-absolute-paths-only")
        self.assertEqual(discovery.ACCEPTED_DISCOVERY_BINDING_SHA256,
                         discovery.DISCOVERY_BINDING_SHA256)


if __name__ == "__main__":
    unittest.main()
