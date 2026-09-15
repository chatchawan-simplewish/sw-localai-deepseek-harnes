import errno
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest


SCRIPT = Path(__file__).parents[1] / "Classify-VM105R10BootstrapTerminal.py"
SPEC = importlib.util.spec_from_file_location("vm105_r10_bootstrap_terminal", SCRIPT)
classifier = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(classifier)


class R10BootstrapTerminalTests(unittest.TestCase):
    @staticmethod
    def absent(path):
        raise FileNotFoundError(errno.ENOENT, "absent", path)

    @staticmethod
    def signed(value):
        unsigned = dict(value)
        unsigned["receiptSha256"] = hashlib.sha256(classifier.canonical_bytes(unsigned)).hexdigest()
        return classifier.canonical_line(unsigned)

    def reader(self):
        records = {
            classifier.R10_ATTEMPT_PATH: classifier.R10_ATTEMPT_PATH.read_bytes(),
            classifier.R10_TERMINAL_PATH: classifier.R10_TERMINAL_PATH.read_bytes(),
        }
        return records, lambda path, _digest: records[path]

    def test_known_committed_records_return_only_the_safe_local_classification(self):
        result = classifier.classify()
        self.assertEqual({
            "classification": classifier.CLASSIFICATION,
            "repairAuthorized": False,
            "retryAuthorized": False,
            "r10AttemptSha256": classifier.R10_ATTEMPT_SHA256,
            "r10TerminalSha256": classifier.R10_TERMINAL_SHA256,
            "targetContacted": False,
        }, result)
        self.assertFalse(classifier.R11_RESULT_PATH.exists())
        self.assertNotIn(b"SECRET", repr(result).encode("ascii"))

    def test_tampered_committed_record_fails_its_sha_pin(self):
        records, reader = self.reader()
        attempt = json.loads(records[classifier.R10_ATTEMPT_PATH])
        attempt["status"] = "OTHER"
        records[classifier.R10_ATTEMPT_PATH] = self.signed(attempt)
        with self.assertRaisesRegex(classifier.ClassificationBlocked, "R10_ATTEMPT_REJECTED"):
            classifier.classify(read_file=reader, lstat=self.absent)

    def test_canonical_self_hash_and_extra_field_fail_closed(self):
        terminal = json.loads(classifier.R10_TERMINAL_PATH.read_bytes())
        terminal["receiptSha256"] = "0" * 64
        raw = classifier.canonical_line(terminal)
        with self.assertRaisesRegex(classifier.ClassificationBlocked, "R10_TERMINAL_REJECTED"):
            classifier._validate_record(raw, hashlib.sha256(raw).hexdigest(), classifier.TERMINAL,
                                        "R10_TERMINAL_REJECTED")
        terminal = json.loads(classifier.R10_TERMINAL_PATH.read_bytes())
        terminal["extra"] = False
        raw = self.signed(terminal)
        with self.assertRaisesRegex(classifier.ClassificationBlocked, "R10_TERMINAL_REJECTED"):
            classifier._validate_record(raw, hashlib.sha256(raw).hexdigest(), classifier.TERMINAL,
                                        "R10_TERMINAL_REJECTED")
        raw = classifier.R10_TERMINAL_PATH.read_bytes() + b" "
        with self.assertRaisesRegex(classifier.ClassificationBlocked, "R10_TERMINAL_REJECTED"):
            classifier._validate_record(raw, hashlib.sha256(raw).hexdigest(), classifier.TERMINAL,
                                        "R10_TERMINAL_REJECTED")

    def test_wrong_pre_replacement_matrix_or_existing_r11_leaf_is_rejected(self):
        terminal = json.loads(classifier.R10_TERMINAL_PATH.read_bytes())
        terminal["rollbackCreated"] = True
        raw = self.signed(terminal)
        with self.assertRaisesRegex(classifier.ClassificationBlocked, "R10_TERMINAL_REJECTED"):
            classifier._validate_record(raw, hashlib.sha256(raw).hexdigest(), classifier.TERMINAL,
                                        "R10_TERMINAL_REJECTED")
        terminal = json.loads(classifier.R10_TERMINAL_PATH.read_bytes())
        terminal["targetExecuted"] = 0
        raw = self.signed(terminal)
        with self.assertRaisesRegex(classifier.ClassificationBlocked, "R10_TERMINAL_REJECTED"):
            classifier._validate_record(raw, hashlib.sha256(raw).hexdigest(), classifier.TERMINAL,
                                        "R10_TERMINAL_REJECTED")
        with self.assertRaisesRegex(classifier.ClassificationBlocked, "R11_RESULT_ALREADY_EXISTS"):
            classifier.classify(lstat=lambda _path: object())


if __name__ == "__main__":
    unittest.main()
