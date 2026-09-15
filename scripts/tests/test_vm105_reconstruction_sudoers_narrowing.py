import errno
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest


SCRIPT = Path(__file__).parents[1] / "Invoke-VM105ReconstructionSudoersNarrowing.py"
SPEC = importlib.util.spec_from_file_location("vm105_sudoers_narrowing", SCRIPT)
narrowing = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(narrowing)


class SudoersNarrowingPlanTests(unittest.TestCase):
    @staticmethod
    def absent(path):
        raise FileNotFoundError(errno.ENOENT, "absent", path)

    def test_plan_is_dormant_and_binds_only_fixed_transition_inputs(self):
        plan = narrowing.transition_plan(narrowing.ACCEPTED_BINDING_SHA256, lstat=self.absent)
        self.assertEqual(plan["targetPath"], "/etc/sudoers.d/90-cloud-init-users")
        self.assertEqual(plan["visudoPath"], "/usr/sbin/visudo")
        self.assertTrue(plan["rollbackRoot"].startswith("/var/tmp/omniroute-dsh-sudoers-r10-"))
        self.assertEqual(plan["temporaryCandidatePath"],
                         "/var/tmp/omniroute-dsh-sudoers-r10-candidate")
        self.assertFalse(plan["authorized"])
        self.assertEqual(plan["steps"], [
            "validate-current-policy", "create-root-rollback", "validate-candidate-with-visudo",
            "atomic-replace", "exact-query-attestation", "semantic-attestation-or-rollback",
        ])
        self.assertTrue(all(len(plan[key]) == 64 for key in (
            "r9ReceiptRawSha256", "r9ReceiptSelfSha256", "reviewedSourceSha256",
            "captureArgvSha256", "reconstructionArgvSha256",
        )))

    def test_invalid_r9_evidence_fails_closed_without_retaining_policy_content(self):
        secret = b"SECRET-SUDOERS-CONTENT"
        with self.assertRaisesRegex(narrowing.NarrowingBlocked, "R9_PROVENANCE_REJECTED"):
            narrowing.transition_plan(
                narrowing.ACCEPTED_BINDING_SHA256, lstat=self.absent,
                read_evidence=lambda _path, _digest: secret,
            )

    def test_spent_evidence_leaf_blocks_before_any_plan_is_returned(self):
        def occupied(path):
            if path == narrowing.ATTEMPT_PATH:
                return object()
            raise FileNotFoundError(errno.ENOENT, "absent", path)

        with self.assertRaisesRegex(narrowing.NarrowingBlocked, "EVIDENCE_ALREADY_EXISTS"):
            narrowing.transition_plan(narrowing.ACCEPTED_BINDING_SHA256, lstat=occupied)

    def test_receipt_is_canonical_and_cannot_retain_raw_policy_or_rollback(self):
        plan = narrowing.transition_plan(narrowing.ACCEPTED_BINDING_SHA256, lstat=self.absent)
        receipt = narrowing.dormant_receipt(plan, "NOT_AUTHORIZED")
        raw = narrowing.canonical_line(receipt)
        self.assertEqual(json.loads(raw), receipt)
        self.assertEqual(receipt["status"], "DORMANT")
        self.assertFalse(receipt["targetExecuted"])
        self.assertFalse(receipt["rawOutputStored"])
        self.assertFalse(receipt["rollbackCreated"])
        self.assertNotIn(b"SECRET-SUDOERS-CONTENT", raw)
        unsigned = dict(receipt)
        self.assertEqual(unsigned.pop("receiptSha256"), hashlib.sha256(
            narrowing.canonical_bytes(unsigned)).hexdigest())


if __name__ == "__main__":
    unittest.main()
