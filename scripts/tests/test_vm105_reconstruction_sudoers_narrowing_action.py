import errno
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).parents[1] / "Invoke-VM105ReconstructionSudoersNarrowingAction.py"
SPEC = importlib.util.spec_from_file_location("vm105_r10_action", SCRIPT)
action = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(action)


class SealedActionTests(unittest.TestCase):
    @staticmethod
    def absent(_path):
        raise FileNotFoundError(errno.ENOENT, "absent")

    def manifest_and_reader(self):
        contents = {}
        for path in action.BINDING_PATHS:
            contents[path] = path.read_bytes() if path.exists() else b"independent review"
        pins={path.relative_to(action.REPOSITORY_ROOT).as_posix(): hashlib.sha256(raw).hexdigest()
              for path, raw in contents.items() if path != action.ACTION_REVIEW_PATH}
        contents[action.ACTION_REVIEW_PATH] = action.canonical_line(
            {"generation":action.GENERATION,"status":"PASS","pins":pins})
        manifest = action.action_manifest({path: hashlib.sha256(raw).hexdigest()
                                           for path, raw in contents.items()})
        return manifest, lambda path, _sha: contents[Path(path)]

    def test_default_is_inert(self):
        self.assertEqual(2, action.main([]))

    def test_absent_leaves_and_authority_block_before_transport(self):
        manifest, reader = self.manifest_and_reader()
        calls = []
        with self.assertRaisesRegex(action.ActionBlocked, "SUDOERS_NARROWING_NOT_AUTHORIZED"):
            action.run_action("", manifest, transport=lambda *_: calls.append(1),
                              read_file=reader, lstat=self.absent)
        self.assertEqual([], calls)

    def test_existing_leaf_and_bad_source_or_review_pin_fail_closed(self):
        manifest, reader = self.manifest_and_reader()
        with self.assertRaisesRegex(action.ActionBlocked, "EVIDENCE_ALREADY_EXISTS"):
            action.run_action("x", manifest, transport=lambda *_: self.fail("transport"),
                              read_file=reader, lstat=lambda _path: object())
        for path in (action.ACTION_SOURCE_PATH, action.ACTION_REVIEW_PATH):
            broken = json.loads(json.dumps(manifest))
            broken["files"][path.relative_to(action.REPOSITORY_ROOT).as_posix()] = "0" * 64
            with self.assertRaisesRegex(action.ActionBlocked, "SEALED_INPUT_REJECTED"):
                action.prepare_action(broken, read_file=reader, lstat=self.absent)

    def test_r9_receipt_is_canonical_safe_provenance_before_transport(self):
        manifest, reader = self.manifest_and_reader()
        value = json.loads(reader(action.R9_RECEIPT_PATH, ""))
        value["status"] = "UNKNOWN"
        unsigned = dict(value)
        unsigned.pop("receiptSha256")
        value["receiptSha256"] = hashlib.sha256(action.canonical_bytes(unsigned)).hexdigest()
        bad = action.canonical_line(value)
        manifest["files"][action.R9_RECEIPT_PATH.relative_to(action.REPOSITORY_ROOT).as_posix()] = hashlib.sha256(bad).hexdigest()
        def corrupt(path, digest):
            return bad if Path(path) == action.R9_RECEIPT_PATH else reader(path, digest)
        with self.assertRaisesRegex(action.ActionBlocked, "R9_PROVENANCE_REJECTED"):
            action.prepare_action(manifest, read_file=corrupt, lstat=self.absent)

    def test_bootstrap_drops_to_dsh_and_requires_canonical_semantic_frame(self):
        bootstrap = action.REMOTE_BOOTSTRAP
        self.assertIn("pwd.getpwnam('dsh')", bootstrap)
        self.assertIn("os.setgid(pw.pw_gid);os.setuid(pw.pw_uid)", bootstrap)
        self.assertIn("preexec_fn=drop", bootstrap)
        self.assertIn("set(frame)=={'sudoVersion','policy'}", bootstrap)
        self.assertIn("frame['sudoVersion']=='1.9.15p5'", bootstrap)

    def test_manifest_binds_durable_payload_review_and_explicit_root_bootstrap(self):
        manifest, _reader = self.manifest_and_reader()
        review = "docs/evidence/vm105-reconstruction-sudoers-narrowing-r10-payload-action-review-20260915.md"
        self.assertIn(review, manifest["files"])
        self.assertTrue(action._remote_command().startswith(
            "/usr/bin/sudo -n /usr/bin/python3.12 -I -c "))

    def test_bad_remote_receipt_never_leaks_raw_output(self):
        manifest, reader = self.manifest_and_reader()
        binding = action.prepare_action(manifest, read_file=reader, lstat=self.absent)["bindingSha256"]
        published = {}
        result = action.run_action(binding, manifest, transport=lambda *_: (0, b"SECRET-SUDOERS", b""),
                                   read_file=reader, lstat=self.absent,
                                   publish=lambda p, raw: published.setdefault(p, raw))
        self.assertEqual("UNKNOWN", result["status"])
        self.assertNotIn(b"SECRET-SUDOERS", b"".join(published.values()))

    def test_wrong_target_is_rejected_and_happy_mock_runs_once(self):
        manifest, reader = self.manifest_and_reader()
        binding = action.prepare_action(manifest, read_file=reader, lstat=self.absent)["bindingSha256"]
        bad = action.result(binding, "PASS", target_path="/etc/sudoers")
        bad_result = action.run_action(binding, manifest, transport=lambda *_: (0, action.canonical_line(bad), b""),
                                       read_file=reader, lstat=self.absent, publish=lambda *_: None)
        self.assertEqual("UNKNOWN", bad_result["status"])
        good = action.result(binding, "PASS")
        calls, published = [], {}
        result = action.run_action(binding, manifest,
            transport=lambda command, payload: (calls.append((command, payload)) or (0, action.canonical_line(good), b"")),
            read_file=reader, lstat=self.absent, publish=lambda p, raw: published.setdefault(p, raw))
        self.assertEqual("PASS", result["status"])
        self.assertEqual(1, len(calls))
        self.assertEqual({action.ATTEMPT_PATH, action.TERMINAL_PATH}, set(published))
        self.assertNotIn(b"SECRET-SUDOERS", published[action.TERMINAL_PATH])

    def test_pass_requires_exact_attestation_and_no_extra_remote_keys(self):
        manifest, reader = self.manifest_and_reader()
        binding = action.prepare_action(manifest, read_file=reader, lstat=self.absent)["bindingSha256"]
        for mutate in (lambda v: v.update(fullPolicyState="BROAD"),
                       lambda v: v.update(captureExactAllowed=False),
                       lambda v: v.update(unexpected="x")):
            value = action.result(binding, "PASS"); mutate(value)
            unsigned = dict(value); unsigned.pop("receiptSha256")
            value["receiptSha256"] = hashlib.sha256(action.canonical_bytes(unsigned)).hexdigest()
            published = {}
            result = action.run_action(binding, manifest, transport=lambda *_: (0, action.canonical_line(value), b""),
                read_file=reader, lstat=self.absent, publish=lambda p, raw: published.setdefault(p, raw))
            self.assertEqual("UNKNOWN", result["status"])
            self.assertEqual({action.ATTEMPT_PATH, action.TERMINAL_PATH}, set(published))

    def test_remote_blocked_receipt_rejects_policy_path_and_invalid_rollback_pair(self):
        manifest, reader = self.manifest_and_reader()
        binding=action.prepare_action(manifest,read_file=reader,lstat=self.absent)["bindingSha256"]
        for mutate in (lambda value: value.update(rollbackPath="/etc/sudoers"),
                       lambda value: value.update(rollbackStatus="RETAINED")):
            value=action.result(binding,"BLOCKED");mutate(value)
            unsigned=dict(value);unsigned.pop("receiptSha256")
            value["receiptSha256"]=hashlib.sha256(action.canonical_bytes(unsigned)).hexdigest()
            result=action.run_action(binding,manifest,transport=lambda *_: (0,action.canonical_line(value),b""),read_file=reader,lstat=self.absent,publish=lambda *_: None)
            self.assertEqual("UNKNOWN",result["status"])

    def test_terminal_outcome_matrix_rejects_signed_invalid_pairs(self):
        manifest, reader = self.manifest_and_reader()
        binding=action.prepare_action(manifest,read_file=reader,lstat=self.absent)["bindingSha256"]
        def invalid(value):
            unsigned=dict(value);unsigned.pop("receiptSha256")
            value["receiptSha256"]=hashlib.sha256(action.canonical_bytes(unsigned)).hexdigest()
            return action.run_action(binding,manifest,transport=lambda *_: (0,action.canonical_line(value),b""),read_file=reader,lstat=self.absent,publish=lambda *_: None)["status"]
        cases=[]
        value=action.result(binding,"PASS");value["candidateValidationCode"]=1;cases.append(value)
        value=action.result(binding,"PASS");value["rollbackSize"]=0;cases.append(value)
        value=action.result(binding,"BLOCKED");value["rollbackCreated"]=True;cases.append(value)
        value=action.result(binding,"BLOCKED");value["rollbackStatus"]="RESTORED";cases.append(value)
        value=action.result(binding,"BLOCKED");value["captureExactAllowed"]=True;cases.append(value)
        value=action.result(binding,"BLOCKED");value["reason"]="NONE";cases.append(value)
        value=action.result(binding,"BLOCKED");value["reason"]="ATTEMPT_PUBLICATION_FAILED";cases.append(value)
        self.assertEqual(["UNKNOWN"]*7,[invalid(value) for value in cases])

    def test_pre_replace_bootstrap_record_uses_empty_rollback_metadata(self):
        bootstrap=action.REMOTE_BOOTSTRAP
        self.assertIn("created=bool(rollback_path) if state!='NOT_NEEDED' else False",bootstrap)
        self.assertIn("'rollbackPath':rollback_path if created else ''",bootstrap)
        self.assertIn("'rollbackSha256':rollback_sha if created else ''",bootstrap)
        value=action.result("0"*64,"BLOCKED")
        self.assertEqual((False,"",0,""),(value["rollbackCreated"],value["rollbackPath"],value["rollbackSize"],value["rollbackSha256"]))

    def test_bootstrap_has_verified_post_replace_rollback_and_exact_entry_match(self):
        self.assertIn("saved=safe(rollback_path)", action.REMOTE_BOOTSTRAP)
        self.assertIn("hashlib.sha256(saved).hexdigest()==rollback_sha", action.REMOTE_BOOTSTRAP)
        self.assertIn("parts=policy.split('Sudoers entry: ')", action.REMOTE_BOOTSTRAP)
        self.assertIn("return len(parts)==2 and parts[1]==entry", action.REMOTE_BOOTSTRAP)

    def test_reason_allowlist_and_attempt_precedes_transport(self):
        manifest, reader = self.manifest_and_reader()
        binding = action.prepare_action(manifest, read_file=reader, lstat=self.absent)["bindingSha256"]
        value = action.result(binding, "BLOCKED"); value["reason"] = "POLICY=SECRET"
        unsigned=dict(value); unsigned.pop("receiptSha256")
        value["receiptSha256"] = hashlib.sha256(action.canonical_bytes(unsigned)).hexdigest()
        events=[]
        result=action.run_action(binding,manifest,transport=lambda *_: (events.append("transport") or (0,action.canonical_line(value),b"")),read_file=reader,lstat=self.absent,publish=lambda path,_raw: events.append(path.name))
        self.assertEqual("UNKNOWN",result["status"])
        self.assertEqual("vm105-dsh-reconstruction-sudoers-narrowing-phase13-r10-attempt-20260915.json",events[0])
        self.assertEqual("transport",events[1])

    def test_failed_attempt_publication_seals_terminal_before_transport(self):
        manifest, reader = self.manifest_and_reader()
        binding=action.prepare_action(manifest,read_file=reader,lstat=self.absent)["bindingSha256"]
        published={};calls=[]
        def publish(path,raw):
            if path==action.ATTEMPT_PATH: raise OSError("interrupted")
            published[path]=raw
        with self.assertRaisesRegex(action.ActionBlocked,"ATTEMPT_PUBLICATION_FAILED"):
            action.run_action(binding,manifest,transport=lambda *_: calls.append(1),read_file=reader,lstat=self.absent,publish=publish)
        self.assertEqual([],calls);self.assertIn(action.TERMINAL_PATH,published)

    def test_attempt_and_fallback_failure_remain_pre_transport(self):
        manifest, reader=self.manifest_and_reader();binding=action.prepare_action(manifest,read_file=reader,lstat=self.absent)["bindingSha256"]
        calls=[]
        with self.assertRaisesRegex(action.ActionBlocked,"TERMINAL_PUBLICATION_FAILED"):
            action.run_action(binding,manifest,transport=lambda *_: calls.append(1),read_file=reader,lstat=self.absent,publish=lambda *_: (_ for _ in ()).throw(OSError()))
        self.assertEqual([],calls)

    def test_authorized_run_requires_explicit_durable_publisher(self):
        manifest, reader=self.manifest_and_reader()
        binding=action.prepare_action(manifest,read_file=reader,lstat=self.absent)["bindingSha256"]
        calls=[]
        with self.assertRaisesRegex(action.ActionBlocked,"SUDOERS_NARROWING_NOT_AUTHORIZED"):
            action.run_action(binding,manifest,transport=lambda *_: calls.append(1),read_file=reader,lstat=self.absent,publish=object())
        self.assertEqual([],calls)

    def test_prepared_r9_context_rejects_replacement_before_transport(self):
        manifest, reader=self.manifest_and_reader()
        prepared=action.prepare_action(manifest,read_file=reader,lstat=self.absent)
        calls=[]
        def swapped(path,digest):
            return b"replaced" if Path(path)==action.R9_SOURCE_PATH else reader(path,digest)
        result=action.run_action(prepared["bindingSha256"],manifest,prepared=prepared,transport=lambda *_: calls.append(1),read_file=swapped,lstat=self.absent,publish=lambda *_: None)
        self.assertEqual("UNKNOWN",result["status"]);self.assertEqual([],calls)

    def test_exclusive_writer_is_canonical_and_refuses_second_disposable_write(self):
        with tempfile.TemporaryDirectory() as directory:
            attempt=Path(directory)/"attempt.json";terminal=Path(directory)/"terminal.json"
            writer=action.EvidenceWriter(attempt,terminal);raw=action.canonical_line({"x":1})
            writer(attempt,raw)
            self.assertEqual(raw,attempt.read_bytes())
            with self.assertRaises(FileExistsError): writer(attempt,raw)

    def test_terminal_publish_failure_retains_attempt_and_never_retries_transport(self):
        manifest, reader=self.manifest_and_reader();prepared=action.prepare_action(manifest,read_file=reader,lstat=self.absent);calls=[];published=[]
        receipt=action.result(prepared["bindingSha256"],"PASS")
        def publish(path,_raw):
            published.append(path)
            if path==action.TERMINAL_PATH: raise OSError("terminal")
        with self.assertRaisesRegex(action.ActionBlocked,"TERMINAL_PUBLICATION_FAILED"):
            action.run_action(prepared["bindingSha256"],manifest,prepared=prepared,transport=lambda *_: (calls.append(1) or (0,action.canonical_line(receipt),b"")),read_file=reader,lstat=self.absent,publish=publish)
        self.assertEqual([1],calls);self.assertEqual(action.ATTEMPT_PATH,published[0])

    def test_bootstrap_uses_nofollow_root_owned_reads_and_failed_rollback_is_not_restored(self):
        self.assertIn("os.O_RDONLY|os.O_NOFOLLOW",action.REMOTE_BOOTSTRAP)
        self.assertIn("stat.S_ISREG(before.st_mode) and before.st_uid==0",action.REMOTE_BOOTSTRAP)
        self.assertIn("stat.S_ISREG(after.st_mode)",action.REMOTE_BOOTSTRAP)
        self.assertIn("fail('BOOTSTRAP_REJECTED',was_replaced,'BLOCKED','RESTORED' if restored else None)",action.REMOTE_BOOTSTRAP)
        self.assertIn("was_replaced=False;restored=False",action.REMOTE_BOOTSTRAP)
        self.assertIn("fail('POST_REPLACEMENT_ATTESTATION_REJECTED',True,'BLOCKED','RESTORED')",action.REMOTE_BOOTSTRAP)
        self.assertIn("fail('ROLLBACK_UNCERTAIN',was_replaced,'UNKNOWN','FAILED')",action.REMOTE_BOOTSTRAP)


if __name__ == "__main__":
    unittest.main()
