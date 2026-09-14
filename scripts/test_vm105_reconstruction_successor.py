import errno
import importlib.util
import json
from pathlib import Path
import unittest


SOURCE = Path(__file__).with_name("Invoke-VM105ReconstructionSuccessor.py")


class ReconstructionSuccessorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("vm105_reconstruction_successor", SOURCE)
        cls.successor = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.successor)

    def details(self):
        successor = self.successor
        command = "/usr/bin/python3.12 -I -c fixture launcher-sha"
        return {
            "sudoExactQueryCommand": ["exact"],
            "sudoFullQueryCommand": ["full"],
            "sudoPolicyCommand": command,
            "targetArgc": 5,
            "targetArgvSha256": "a" * 64,
            "bootstrapBytes": successor.RECONSTRUCTION_BOOTSTRAP_BYTES,
            "bootstrapSha256": successor.RECONSTRUCTION_BOOTSTRAP_SHA256,
        }

    def bundle_receipt(self):
        successor = self.successor
        rows = [{
            "basename": source["basename"], "type": "regular", "symlink": False,
            "device": 1, "inode": index + 2, "mode": 0o440, "uid": 0, "gid": 0,
            "size": 1, "mtimeNs": 1, "ctimeNs": 1, "sha256": source["sha256"],
        } for index, source in enumerate(successor.BUNDLE_FILES)]
        return successor.canonical_line(successor.signed({
            "status": "PASS", "reason": "NONE", "vmHostname": "vm105",
            "vmMachineIdSha256": "b" * 64, "bundleRoot": successor.BUNDLE_ROOT,
            "bundleDevice": 1, "bundleInode": 1, "bundleMode": 0o550,
            "bundleUid": 0, "bundleGid": 0, "bundleSize": 0,
            "bundleMtimeNs": 1, "bundleCtimeNs": 1,
            "expectedFileCount": 5, "fileCount": 5, "files": rows,
        }))

    def policy(self, command=None):
        successor = self.successor
        command = command or self.details()["sudoPolicyCommand"]
        policy = (
            "Matching Defaults entries for dsh on vm105:\n"
            "    env_reset, mail_badpass, use_pty, secure_path=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin\n"
            "User dsh may run the following commands on vm105:\n"
            "\n"
            "Sudoers entry: /etc/sudoers.d/vm105-reconstruction:12:3\n"
            "    RunAsUsers: root\n"
            "    Options: !authenticate\n"
            "    Commands:\n"
            f"        {command}\n"
        )
        return successor.canonical_line({"sudoVersion": "1.9.15p5", "policy": policy})

    def test_capture_is_the_only_bound_mode_and_provenance_precedes_transport(self):
        successor = self.successor
        self.assertEqual(successor.GENERATION, "phase13-r4-20260915")
        self.assertIsNone(successor.ACCEPTED_BUNDLE_DELIVERY_BINDING_SHA256)
        self.assertEqual(successor.ACCEPTED_PREREQUISITE_CAPTURE_BINDING_SHA256,
                         successor.PREREQUISITE_CAPTURE_BINDING_SHA256)
        self.assertEqual(successor.ACCEPTED_SUDO_VERSION, "1.9.15p5")
        for name in (
            "ACCEPTED_RECONSTRUCTION_DISPATCH_BINDING_SHA256",
            "ACCEPTED_BUNDLE_RECEIPT_RAW_SHA256", "ACCEPTED_BUNDLE_RECEIPT_SELF_SHA256",
            "ACCEPTED_SUDO_RECEIPT_RAW_SHA256", "ACCEPTED_SUDO_RECEIPT_SELF_SHA256",
            "ACCEPTED_LIVE_BINDINGS",
        ):
            self.assertIsNone(getattr(successor, name), name)
        self.assertEqual(successor.DELIVERY_PROVENANCE["rawSha256"],
                         "d3739ef37d16c76f3aa29eefc461b6660e091620b37d3dbc6e9b68179f9e831c")
        self.assertEqual(successor.SUDO_DISCOVERY_PROVENANCE["rawSha256"],
                         "d88e629c18ef86249e27bfc02d944b35a0ae128faea43f0f74437dd5bf9c8f24")
        attributes = (SOURCE.parents[1] / ".gitattributes").read_text(encoding="utf-8").splitlines()
        for provenance in (successor.DELIVERY_PROVENANCE, successor.SUDO_DISCOVERY_PROVENANCE):
            self.assertIn(f'{provenance["path"]} -text', attributes)
        self.assertTrue(all("phase13-r4-" in path.name for path in successor.ALL_EVIDENCE_PATHS))

        with self.assertRaisesRegex(successor.PrerequisiteBlocked,
                                    "BUNDLE_DELIVERY_NOT_EXECUTABLE"):
            successor.deliver_bundle(None, lambda *_: self.fail("delivery transport called"),
                                     read_source=lambda *_: b"")
        with self.assertRaisesRegex(successor.PrerequisiteBlocked,
                                    "RECONSTRUCTION_DISPATCH_NOT_EXECUTABLE"):
            successor.dispatch_reconstruction(None)
        with self.assertRaisesRegex(successor.PrerequisiteBlocked,
                                    "CAPTURE_PROVENANCE_REJECTED"):
            successor.capture_prerequisites(
                successor.PREREQUISITE_CAPTURE_BINDING_SHA256,
                lambda *_: self.fail("bundle transport called"),
                lambda *_: self.fail("sudo transport called"),
                read_evidence=lambda *_: b"wrong\n",
            )

    def test_line_column_policy_captures_each_canonical_receipt_once(self):
        successor = self.successor
        published = []
        bundle_raw = self.bundle_receipt()
        details = self.details()
        full_raw = self.policy()

        def absent(path):
            raise FileNotFoundError(errno.ENOENT, "absent", path)

        def sudo_transport(command):
            return ((0, b"", b"") if command == ["exact"] else
                    (0, full_raw, b""))

        result = successor.capture_prerequisites(
            successor.PREREQUISITE_CAPTURE_BINDING_SHA256,
            lambda command: (0, bundle_raw, b""), sudo_transport,
            command_details=lambda: details,
            lstat=absent,
            publish=lambda path, raw: published.append((path, raw)),
        )
        self.assertEqual(result, 0)
        self.assertEqual([path for path, _ in published],
                         [successor.BUNDLE_RECEIPT_PATH, successor.SUDO_RECEIPT_PATH])
        for _, raw in published:
            self.assertEqual(successor.canonical_line(json.loads(raw)), raw)
        sudo_raw = published[1][1]
        self.assertEqual(json.loads(sudo_raw)["status"], "PASS")
        self.assertNotIn(full_raw, sudo_raw)

    def test_line_column_broad_all_is_blocked_and_stderr_is_never_stored(self):
        successor = self.successor
        details = self.details()
        state, version = successor._parse_full_sudo_policy(self.policy("ALL"), details)
        self.assertEqual((state, version), ("BROAD", "1.9.15p5"))

        published = []
        sensitive = b"sensitive sudo stderr"
        result = successor.capture_prerequisites(
            successor.PREREQUISITE_CAPTURE_BINDING_SHA256,
            lambda command: (0, self.bundle_receipt(), b""),
            lambda command: (0, b"", sensitive),
            command_details=lambda: details,
            lstat=lambda path: (_ for _ in ()).throw(
                FileNotFoundError(errno.ENOENT, "absent", path)),
            publish=lambda path, raw: published.append((path, raw)),
        )
        self.assertEqual(result, 1)
        self.assertEqual(len(published), 2)
        self.assertEqual(json.loads(published[1][1])["status"], "UNKNOWN")
        self.assertNotIn(sensitive, published[1][1])


if __name__ == "__main__":
    unittest.main()
