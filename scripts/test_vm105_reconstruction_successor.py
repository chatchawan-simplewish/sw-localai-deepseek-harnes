import errno
import importlib.util
from pathlib import Path
import unittest


SOURCE = Path(__file__).with_name("Invoke-VM105ReconstructionSuccessor.py")


class ReconstructionSuccessorTests(unittest.TestCase):
    def test_delivery_is_only_executable_and_all_fresh_leaves_are_absent_before_transport(self):
        self.assertTrue(SOURCE.is_file(), "successor source must exist")
        spec = importlib.util.spec_from_file_location("vm105_reconstruction_successor", SOURCE)
        successor = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(successor)
        self.assertEqual(successor.GENERATION, "phase13-20260915")
        self.assertEqual(
            successor.ACCEPTED_BUNDLE_DELIVERY_BINDING_SHA256,
            successor.BUNDLE_DELIVERY_BINDING_SHA256,
        )
        for name in (
            "ACCEPTED_PREREQUISITE_CAPTURE_BINDING_SHA256",
            "ACCEPTED_RECONSTRUCTION_DISPATCH_BINDING_SHA256",
            "ACCEPTED_BUNDLE_RECEIPT_RAW_SHA256",
            "ACCEPTED_BUNDLE_RECEIPT_SELF_SHA256",
            "ACCEPTED_SUDO_RECEIPT_RAW_SHA256",
            "ACCEPTED_SUDO_RECEIPT_SELF_SHA256",
            "ACCEPTED_SUDO_VERSION",
            "ACCEPTED_LIVE_BINDINGS",
        ):
            self.assertIsNone(getattr(successor, name), name)
        with self.assertRaisesRegex(
                successor.PrerequisiteBlocked, "PREREQUISITE_CAPTURE_NOT_EXECUTABLE"):
            successor.capture_prerequisites(
                successor.PREREQUISITE_CAPTURE_BINDING_SHA256,
                lambda command: self.fail("capture transport called"),
                lambda command: self.fail("sudo transport called"),
            )
        with self.assertRaisesRegex(
                successor.PrerequisiteBlocked, "RECONSTRUCTION_DISPATCH_NOT_EXECUTABLE"):
            successor.dispatch_reconstruction(
                successor.RECONSTRUCTION_DISPATCH_BINDING_SHA256,
            )

        leaves = {
            successor.DELIVERY_ATTEMPT_PATH,
            successor.DELIVERY_TERMINAL_PATH,
            successor.BUNDLE_RECEIPT_PATH,
            successor.SUDO_RECEIPT_PATH,
            successor.DISPATCH_ATTEMPT_PATH,
            successor.DISPATCH_TERMINAL_PATH,
        }
        checked = []
        published = {}

        def absent(path):
            checked.append(path)
            raise FileNotFoundError(errno.ENOENT, "absent", path)

        def transport(command, payload):
            self.assertEqual(set(checked), leaves)
            self.assertEqual(set(published), {successor.DELIVERY_ATTEMPT_PATH})
            remote = successor.signed({
                "status": "PASS", "reason": "NONE",
                "finalRoot": successor.BUNDLE_ROOT,
                "temporaryRoot": successor.TEMP_BUNDLE_ROOT,
                "fileCount": 5, "renameCompleted": True, "parentFsync": True,
            })
            return 0, successor.canonical_line(remote), b""

        result = successor.deliver_bundle(
            successor.BUNDLE_DELIVERY_BINDING_SHA256,
            transport,
            read_source=lambda path, expected: b"fixture",
            lstat=absent,
            publish=lambda path, raw: published.setdefault(path, raw),
        )
        self.assertEqual(result, 0)
        self.assertEqual(set(published), {
            successor.DELIVERY_ATTEMPT_PATH,
            successor.DELIVERY_TERMINAL_PATH,
        })


if __name__ == "__main__":
    unittest.main()
