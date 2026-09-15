import hashlib
import importlib.util
import inspect
from pathlib import Path
import unittest


SCRIPT = Path(__file__).parents[1] / "Invoke-VM105R12BootstrapDiagnostic.py"
SPEC = importlib.util.spec_from_file_location("vm105_r12", SCRIPT)
r12 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(r12)


class R12BootstrapDiagnosticTests(unittest.TestCase):
    def test_static_payload_taxonomy_and_public_api_are_closed(self):
        self.assertEqual(r12.GENERATION, "phase13-r12-bootstrap-diagnostic-20260915")
        compile(r12.ROOT_LAUNCHER, "<r12-root-launcher>", "exec")
        compile(r12.REMOTE_WRAPPER, "<r12-remote-wrapper>", "exec")
        self.assertEqual(tuple(inspect.signature(r12.prepare_action).parameters), ("manifest",))
        self.assertEqual(tuple(inspect.signature(r12.run_diagnostic).parameters),
                         ("authority_sha256", "manifest"))
        self.assertFalse(hasattr(r12, "_prepare_for_test"))
        self.assertFalse(hasattr(r12, "_run_for_test"))
        self.assertNotIn("R10_ATTEMPT_PATH", r12.__dict__)
        self.assertNotIn("R10_TERMINAL_PATH", r12.__dict__)
        self.assertEqual(set(r12.BINDING_PATHS), set(r12.SOURCE_PATHS) | set(r12.REVIEW_PATHS))
        self.assertEqual(len(r12.REVIEW_PATHS), 2)

        with self.assertRaisesRegex(r12.DiagnosticBlocked, "R12_DIAGNOSTIC_NOT_AUTHORIZED"):
            r12.run_diagnostic("", {})
        with self.assertRaises(TypeError):
            r12.prepare_action({}, read_file=lambda *_: b"")
        with self.assertRaises(TypeError):
            r12.run_diagnostic("", {}, lstat=lambda *_: None)
        with self.assertRaises(TypeError):
            r12.run_diagnostic("", {}, publish=lambda *_: None)
        with self.assertRaises(TypeError):
            r12.run_diagnostic("", {}, transport=lambda *_: None)

        binding = "a" * 64
        frame = {"bindingSha256": binding, "generation": r12.GENERATION, "rawOutputStored": False,
                 "reason": "ROOT_EXECUTION_CONFIRMED", "rootExecutionConfirmed": True}
        frame["receiptSha256"] = hashlib.sha256(r12.canonical_bytes(frame)).hexdigest()
        raw = r12.canonical_line(frame)
        self.assertEqual(r12._validate_remote(raw, binding)["reason"], "ROOT_EXECUTION_CONFIRMED")
        rejected = {"bindingSha256": binding, "generation": r12.GENERATION, "rawOutputStored": False,
                    "reason": "NON_ROOT_SUDO_REJECTED", "rootExecutionConfirmed": False}
        rejected["receiptSha256"] = hashlib.sha256(r12.canonical_bytes(rejected)).hexdigest()
        for invalid in (b"{}\n", r12.canonical_line(rejected)):
            with self.assertRaisesRegex(r12.DiagnosticBlocked, "REMOTE_FRAME_REJECTED"):
                r12._validate_remote(invalid, binding)
        self.assertNotIn(b"sudoers", raw)
        self.assertNotIn(b"SECRET", raw)


if __name__ == "__main__":
    unittest.main()
