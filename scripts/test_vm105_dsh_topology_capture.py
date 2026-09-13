import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import posixpath
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest import mock


SCRIPT = Path(__file__).with_name("Capture-VM105DshTopology.py")
SPEC = importlib.util.spec_from_file_location("vm105_topology_capture", SCRIPT)
capture = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(capture)


class TopologyFixture:
    def __init__(self):
        self.temp = Path(tempfile.mkdtemp())
        self.root = self.temp / "opt" / "deepseek-harness"
        self.modules = self.root / "node_modules"
        self.packages = {
            "@deepseek-ai/dsh": self.modules / ".pnpm/dsh@1/node_modules/@deepseek-ai/dsh",
            "@deepseek-ai/dsh-headless": self.modules / ".pnpm/headless@1/node_modules/@deepseek-ai/dsh-headless",
            "fixture-util": self.modules / ".pnpm/fixture-util@1/node_modules/fixture-util",
        }
        self.links = {}
        for path in self.packages.values():
            path.mkdir(parents=True)
        self._write_package("@deepseek-ai/dsh", {"@deepseek-ai/dsh-headless": "1", "fixture-util": "1"})
        self._write_package("@deepseek-ai/dsh-headless", {"fixture-util": "1"})
        self._write_package("fixture-util", {})
        (self.packages["@deepseek-ai/dsh-headless"] / "cordis.patch.yml").write_bytes(b"fixture: true\n")
        self.start = self.modules / "@deepseek-ai/dsh"
        self.start.parent.mkdir(parents=True)
        self._link(self.start, self.packages["@deepseek-ai/dsh"])
        self._dependency("@deepseek-ai/dsh", "@deepseek-ai/dsh-headless")
        self._dependency("@deepseek-ai/dsh", "fixture-util")
        self._dependency("@deepseek-ai/dsh-headless", "fixture-util")
        self._seal()
        self.manifest = self._manifest()

    def _write_package(self, name, dependencies):
        value = {"name": name, "version": "1.0.0", "dependencies": dependencies}
        (self.packages[name] / "package.json").write_text(json.dumps(value, sort_keys=True))

    @staticmethod
    def _link_path(link, target):
        link.parent.mkdir(parents=True, exist_ok=True)
        raw = os.path.relpath(target, link.parent)
        link.write_text(raw)
        return raw

    def _link(self, link, target):
        self.links[link] = (self._link_path(link, target), target)

    def _dependency(self, owner, dependency):
        package = self.packages[owner]
        virtual = package.parent.parent if package.parent.name.startswith("@") else package.parent
        self._link(virtual / Path(*dependency.split("/")), self.packages[dependency])

    def _seal(self):
        for path in sorted(self.root.rglob("*"), key=lambda item: len(item.parts), reverse=True):
            if not path.is_symlink():
                path.chmod(0o555 if path.is_dir() else 0o444)
        self.root.chmod(0o555)

    def _manifest(self):
        rows = []
        for name, path in self.packages.items():
            rows.append({"name": name, "version": "1.0.0", "logicalPath": str(path),
                         "canonicalPath": str(path)})
        value = {"status": "PASS", "packages": sorted(rows, key=lambda row: row["name"]),
                 "modules": [], "edges": [], "entrypoints": [], "configBundles": [], "runtime": {}}
        value["canonicalManifestSha256"] = hashlib.sha256(capture.canonical_bytes(value)).hexdigest()
        return value

    def run(self):
        with mock.patch.object(capture, "_link_snapshot", side_effect=self._snapshot):
            return capture.capture_topology(self.root, self.manifest,
                                            self.manifest["canonicalManifestSha256"], len(self.packages))

    def _snapshot(self, path, root):
        raw, target = self.links[path]
        if os.path.isabs(raw):
            raise capture.CaptureBlocked("ABSOLUTE_LINK")
        if not capture._within(target, root):
            raise capture.CaptureBlocked("LINK_ESCAPE")
        disk = path.lstat()
        info = SimpleNamespace(st_dev=disk.st_dev, st_ino=disk.st_ino,
                               st_mode=stat.S_IFLNK | 0o777, st_size=disk.st_size,
                               st_mtime_ns=disk.st_mtime_ns, st_ctime_ns=disk.st_ctime_ns,
                               st_uid=0, st_gid=0)
        return capture._link_identity(info), raw, target, info

    def unseal(self):
        for path in [self.root, *self.root.rglob("*")]:
            if not path.is_symlink():
                try:
                    path.chmod(0o755 if path.is_dir() else 0o644)
                except OSError:
                    pass

    def close(self):
        self.unseal()
        shutil.rmtree(self.temp)


class TopologyStageFixture:
    def __init__(self):
        self.temp = Path(tempfile.mkdtemp())
        self.source = self.temp / "source"
        self.staging = self.temp / "staging"
        self.staging.mkdir()
        self.dsh = "node_modules/.pnpm/dsh@1/node_modules/@deepseek-ai/dsh"
        self.headless = "node_modules/.pnpm/headless@1/node_modules/@deepseek-ai/dsh-headless"
        self.cli = self.dsh + "/lib/bin.js"
        self.files = {
            "/opt/deepseek-harness/" + self.dsh + "/package.json": b'{"name":"@deepseek-ai/dsh","version":"1.0.0"}\n',
            "/opt/deepseek-harness/" + self.cli: b"console.log('fixture')\n",
            "/opt/deepseek-harness/" + self.headless + "/package.json": b'{"name":"@deepseek-ai/dsh-headless","version":"1.0.0"}\n',
            "/opt/deepseek-harness/" + self.headless + "/cordis.patch.yml": b"fixture: true\n",
            "/opt/node-v24.19.0-linux-x64/bin/node": b"fixture node\n",
            "/lib/libfixture.so": b"fixture library\n",
        }
        for path, value in self.files.items():
            target = self.source / path.lstrip("/")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(value)

        def module(path):
            return {"sourceLogicalPath": path, "sourceCanonicalPath": path,
                    "stagedRelativePath": "unused/" + Path(path).name,
                    "sha256": hashlib.sha256(self.files[path]).hexdigest()}

        dsh_json = "/opt/deepseek-harness/" + self.dsh + "/package.json"
        headless_json = "/opt/deepseek-harness/" + self.headless + "/package.json"
        self.manifest = {
            "status": "PASS", "edges": [], "entrypoints": [], "configBundles": [],
            "packages": [
                {"name": "@deepseek-ai/dsh", "version": "1.0.0", "logicalPath": "/opt/deepseek-harness/node_modules/@deepseek-ai/dsh", "canonicalPath": "/opt/deepseek-harness/" + self.dsh},
                {"name": "@deepseek-ai/dsh-headless", "version": "1.0.0", "logicalPath": "/opt/deepseek-harness/" + self.dsh.rsplit("/", 1)[0] + "/dsh-headless", "canonicalPath": "/opt/deepseek-harness/" + self.headless},
            ],
            "modules": [module(dsh_json), module("/opt/deepseek-harness/" + self.cli), module(headless_json)],
            "runtime": {
                "node": {"logicalPath": "/opt/node-v24.19.0-linux-x64/bin/node", "canonicalPath": "/opt/node-v24.19.0-linux-x64/bin/node", "sha256": hashlib.sha256(self.files["/opt/node-v24.19.0-linux-x64/bin/node"]).hexdigest()},
                "dependencies": [{"logicalPath": "/lib/libfixture.so", "canonicalPath": "/lib/libfixture.so", "sha256": hashlib.sha256(self.files["/lib/libfixture.so"]).hexdigest()}],
            },
        }
        self.manifest_sha = hashlib.sha256(capture.canonical_bytes(self.manifest)).hexdigest()
        self.manifest["canonicalManifestSha256"] = self.manifest_sha
        identity = {"device": 1, "inode": 1, "mode": 0o444, "size": 1, "mtimeNs": 1,
                    "ctimeNs": 1, "uid": 0, "gid": 0, "rootOwned": True}
        link_identity = {**identity, "mode": 0o777}
        dsh_logical = "node_modules/@deepseek-ai/dsh"
        headless_logical = self.dsh.rsplit("/", 1)[0] + "/dsh-headless"

        def link(logical, resolved, name, package_json):
            return {"logicalRelativePath": logical,
                    "rawRelativeTarget": posixpath.relpath(resolved, posixpath.dirname(logical)),
                    "resolvedCanonicalPackagePath": resolved, "lstatIdentity": dict(link_identity),
                    "packageName": name, "packageVersion": "1.0.0",
                    "packageJsonSha256": hashlib.sha256(self.files[package_json]).hexdigest()}

        self.receipt = {
            "status": "PASS", "acceptedManifestCanonicalSha256": self.manifest_sha,
            "acceptedPackageCount": 2, "startPackage": dsh_logical,
            "reachablePackageCount": 2, "dependencyLinkCount": 2,
            "packages": [
                {"name": "@deepseek-ai/dsh", "version": "1.0.0", "canonicalPackagePath": self.dsh,
                 "packageJsonSha256": hashlib.sha256(self.files[dsh_json]).hexdigest(),
                 "packageJsonIdentity": dict(identity), "firstLogicalPath": dsh_logical},
                {"name": "@deepseek-ai/dsh-headless", "version": "1.0.0", "canonicalPackagePath": self.headless,
                 "packageJsonSha256": hashlib.sha256(self.files[headless_json]).hexdigest(),
                 "packageJsonIdentity": dict(identity), "firstLogicalPath": headless_logical},
            ],
            "links": [link(dsh_logical, self.dsh, "@deepseek-ai/dsh", dsh_json),
                      link(headless_logical, self.headless, "@deepseek-ai/dsh-headless", headless_json)],
            "headlessPatch": {"logicalRelativePath": headless_logical + "/cordis.patch.yml",
                              "canonicalRelativePath": self.headless + "/cordis.patch.yml",
                              "sha256": hashlib.sha256(self.files["/opt/deepseek-harness/" + self.headless + "/cordis.patch.yml"]).hexdigest(),
                              "lstatIdentity": dict(identity)},
        }
        self.resign()
        self.expected_packages = {(row["name"], row["version"], row["canonicalPackagePath"])
                                  for row in self.receipt["packages"]}
        self.fd_paths, self.modes, self.links, self.inventory_calls = {}, {}, {}, 0
        self.builder = SimpleNamespace(
            _require_descriptor_platform=lambda: None,
            _require_empty_staging=lambda _fd: None if not any(self.staging.iterdir()) else (_ for _ in ()).throw(capture.CaptureBlocked("STAGING_ROOT_NOT_EMPTY")),
            _open_source_at=self.open_source, _create_destination_at=self.create_destination,
            _hash_fd=self.hash_fd, _directory_at=self.directory_at)

    def resign(self):
        self.receipt.pop("receiptSha256", None)
        self.receipt_sha = hashlib.sha256(capture.canonical_bytes(self.receipt)).hexdigest()
        self.receipt["receiptSha256"] = self.receipt_sha

    def open_source(self, _root_fd, path):
        return os.open(self.source / path.lstrip("/"), os.O_RDONLY | getattr(os, "O_BINARY", 0))

    def create_destination(self, _root_fd, path):
        target = self.staging / path
        target.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(target, os.O_RDWR | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0), 0o600)
        self.fd_paths[descriptor] = path
        return descriptor

    @staticmethod
    def hash_fd(descriptor):
        value = hashlib.sha256()
        os.lseek(descriptor, 0, os.SEEK_SET)
        for part in iter(lambda: os.read(descriptor, 65536), b""):
            value.update(part)
        return value.hexdigest()

    def fchmod(self, descriptor, mode):
        self.modes[self.fd_paths[descriptor]] = mode

    def create_link(self, _builder, _root_fd, logical, raw):
        (self.staging / logical).parent.mkdir(parents=True, exist_ok=True)
        self.links[logical] = raw

    def directory_at(self, _root_fd, parts, create=False):
        path = self.staging.joinpath(*parts)
        if create:
            path.mkdir(parents=True, exist_ok=True)
        if not path.is_dir():
            raise capture.CaptureBlocked("TOPOLOGY_LINK_TARGET_MISSING")
        return os.open(os.devnull, os.O_RDONLY)

    def inventory(self, _builder, _root_fd):
        self.inventory_calls += 1
        identity = {"device": 1, "inode": 1, "mode": 0o700, "size": 1,
                    "mtimeNs": 1, "ctimeNs": 1, "uid": 0, "gid": 0, "rootOwned": True}
        files = []
        for path in self.staging.rglob("*"):
            if path.is_file():
                relative = path.relative_to(self.staging).as_posix()
                files.append({"path": relative, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                              "mode": self.modes[relative], "uid": 0, "gid": 0,
                              "identity": {**identity, "mode": self.modes[relative]}})
        directories = [{"path": path.relative_to(self.staging).as_posix(), "mode": 0o700,
                        "uid": 0, "gid": 0, "identity": dict(identity)}
                       for path in self.staging.rglob("*") if path.is_dir()]
        links = []
        for logical, raw in self.links.items():
            resolved = capture._resolved_relative_link(logical, raw)
            if not (self.staging / resolved).is_dir():
                raise capture.CaptureBlocked("TOPOLOGY_LINK_TARGET_MISSING")
            links.append({"path": logical, "rawRelativeTarget": raw,
                          "resolvedCanonicalPackagePath": resolved, "uid": 0, "gid": 0,
                          "identity": {**identity, "mode": 0o777}})
        return {"files": sorted(files, key=lambda row: row["path"]),
                "links": sorted(links, key=lambda row: row["path"]),
                "directories": sorted(directories, key=lambda row: row["path"])}

    def close(self):
        shutil.rmtree(self.temp)


class TopologyCaptureTests(unittest.TestCase):
    def setUp(self):
        self.fixture = TopologyFixture()

    def tearDown(self):
        self.fixture.close()

    def test_pass_records_complete_closure_and_headless_patch(self):
        receipt = self.fixture.run()
        self.assertEqual(receipt["status"], "PASS")
        self.assertEqual(receipt["reachablePackageCount"], 3)
        self.assertEqual(receipt["dependencyLinkCount"], 4)
        self.assertTrue(all(not os.path.isabs(row["rawRelativeTarget"]) for row in receipt["links"]))
        self.assertEqual(receipt["headlessPatch"]["sha256"],
                         hashlib.sha256(b"fixture: true\n").hexdigest())

    def test_absolute_and_escaping_links_are_blocked(self):
        self.fixture.links[self.fixture.start] = (str(self.fixture.temp), self.fixture.temp)
        with self.assertRaisesRegex(capture.CaptureBlocked, "ABSOLUTE_LINK"):
            self.fixture.run()
        self.fixture.links[self.fixture.start] = ("../../../outside", self.fixture.temp)
        with self.assertRaisesRegex(capture.CaptureBlocked, "LINK_ESCAPE"):
            self.fixture.run()

    def test_link_identity_drift_is_blocked(self):
        original = self.fixture._snapshot
        calls = 0

        def drifting(path, root):
            nonlocal calls
            value = original(path, root)
            calls += 1
            if calls > 4 and path == self.fixture.start:
                identity, raw, resolved, info = value
                return ((*identity[:-1], identity[-1] + 1), raw, resolved, info)
            return value

        with mock.patch.object(self.fixture, "_snapshot", side_effect=drifting):
            with self.assertRaisesRegex(capture.CaptureBlocked, "LINK_IDENTITY_DRIFT"):
                self.fixture.run()

    def test_missing_or_extra_package_identity_is_blocked(self):
        self.fixture.manifest["packages"] = self.fixture.manifest["packages"][:-1]
        unsigned = dict(self.fixture.manifest)
        unsigned.pop("canonicalManifestSha256")
        self.fixture.manifest["canonicalManifestSha256"] = hashlib.sha256(capture.canonical_bytes(unsigned)).hexdigest()
        with mock.patch.object(capture, "_link_snapshot", side_effect=self.fixture._snapshot):
            with self.assertRaisesRegex(capture.CaptureBlocked, "PACKAGE_CLOSURE_MISMATCH"):
                capture.capture_topology(self.fixture.root, self.fixture.manifest,
                                         self.fixture.manifest["canonicalManifestSha256"], 2)

    def test_missing_headless_patch_is_blocked(self):
        self.fixture.unseal()
        (self.fixture.packages["@deepseek-ai/dsh-headless"] / "cordis.patch.yml").unlink()
        self.fixture._seal()
        with self.assertRaisesRegex(capture.CaptureBlocked, "PATH_UNRESOLVED"):
            self.fixture.run()

    def test_non_root_or_group_writable_package_path_is_blocked(self):
        info = self.fixture.root.lstat()
        non_root = SimpleNamespace(st_mode=info.st_mode, st_uid=1, st_gid=0)
        with mock.patch.object(Path, "lstat", return_value=non_root):
            with self.assertRaisesRegex(capture.CaptureBlocked, "INSECURE_PATH"):
                capture._require_secure_real_path(self.fixture.root, self.fixture.root, "directory")
        non_root_group = SimpleNamespace(st_mode=info.st_mode, st_uid=0, st_gid=1)
        with mock.patch.object(Path, "lstat", return_value=non_root_group):
            with self.assertRaisesRegex(capture.CaptureBlocked, "INSECURE_PATH"):
                capture._require_secure_real_path(self.fixture.root, self.fixture.root, "directory")
        bad_link_group = SimpleNamespace(st_mode=stat.S_IFLNK | 0o777, st_uid=0, st_gid=1)
        with mock.patch.object(capture, "_require_secure_real_path"), mock.patch.object(
                Path, "lstat", return_value=bad_link_group):
            with self.assertRaisesRegex(capture.CaptureBlocked, "DEPENDENCY_LINK_INSECURE"):
                capture._link_snapshot(self.fixture.start, self.fixture.root)
        self.fixture.unseal()
        self.fixture.packages["fixture-util"].chmod(0o775)
        with self.assertRaisesRegex(capture.CaptureBlocked, "INSECURE_PATH"):
            self.fixture.run()

    def test_pinned_builder_fresh_inventory_must_equal_accepted_manifest(self):
        builder = SCRIPT.with_name("Build-VM105FinalClientManifest.py").read_bytes().decode("utf-8")
        unsigned = dict(self.fixture.manifest)
        unsigned.pop("canonicalManifestSha256")
        called = []

        def matching_scan(root, node):
            called.append((root, node))
            return unsigned

        capture._revalidate_fresh_manifest(builder, self.fixture.manifest,
                                           self.fixture.manifest["canonicalManifestSha256"], matching_scan)
        self.assertEqual(called, [(capture.INSTALL_ROOT / "node_modules", capture.ACCEPTED_NODE)])
        with self.assertRaisesRegex(capture.CaptureBlocked, "FRESH_MANIFEST_MISMATCH"):
            capture._revalidate_fresh_manifest(
                builder, self.fixture.manifest, self.fixture.manifest["canonicalManifestSha256"],
                lambda root, node: {**unsigned, "status": "BLOCKED"})
        with self.assertRaisesRegex(capture.CaptureBlocked, "FRESH_MANIFEST_RESCAN_FAILED"):
            capture._revalidate_fresh_manifest(
                builder, self.fixture.manifest, self.fixture.manifest["canonicalManifestSha256"],
                lambda root, node: (_ for _ in ()).throw(RuntimeError("secret detail")))

    def test_stage_verified_topology_rebuilds_executable_physical_shape(self):
        fixture = TopologyStageFixture()
        self.addCleanup(fixture.close)
        with mock.patch.object(capture, "ACCEPTED_MANIFEST_SHA256", fixture.manifest_sha), \
                mock.patch.object(capture, "ACCEPTED_PACKAGE_COUNT", 2), \
                mock.patch.object(capture, "ACCEPTED_MODULE_COUNT", 3), \
                mock.patch.object(capture, "_validate_manifest", return_value=fixture.expected_packages), \
                mock.patch.object(capture, "_create_link_at", side_effect=fixture.create_link), \
                mock.patch.object(capture, "_inventory_topology", side_effect=fixture.inventory), \
                mock.patch.object(capture.os, "fchmod", side_effect=fixture.fchmod, create=True):
            receipt = capture.stage_verified_topology(
                fixture.manifest, fixture.receipt, fixture.receipt_sha, 101, 102, fixture.builder)
        self.assertEqual(receipt["status"], "PASS")
        self.assertEqual(fixture.inventory_calls, 2)
        self.assertTrue((fixture.staging / fixture.cli).is_file())
        self.assertTrue((fixture.staging / "runtime/opt/node-v24.19.0-linux-x64/bin/node").is_file())
        links = {row["path"]: row["resolvedCanonicalPackagePath"] for row in receipt["links"]}
        self.assertEqual(links["node_modules/@deepseek-ai/dsh"], fixture.dsh)
        self.assertEqual(links[fixture.receipt["packages"][1]["firstLogicalPath"]], fixture.headless)

    def test_stage_verified_topology_blocks_tamper_collision_escape_and_hash_failure(self):
        for condition, reason in (("tampered_receipt", "TOPOLOGY_RECEIPT_HASH_MISMATCH"),
                                  ("link_collision", "TOPOLOGY_PATH_COLLISION"),
                                  ("link_escape", "TOPOLOGY_LINK_ESCAPE"),
                                  ("headless_group", "TOPOLOGY_HEADLESS_PATCH_IDENTITY_INVALID"),
                                  ("source_hash", "TOPOLOGY_SOURCE_HASH_MISMATCH")):
            with self.subTest(condition=condition):
                fixture = TopologyStageFixture()
                try:
                    if condition == "tampered_receipt":
                        fixture.receipt["dependencyLinkCount"] = 99
                    elif condition == "link_collision":
                        extra = copy.deepcopy(fixture.receipt["links"][0])
                        extra["logicalRelativePath"] = fixture.cli
                        extra["rawRelativeTarget"] = posixpath.relpath(
                            fixture.dsh, posixpath.dirname(fixture.cli))
                        fixture.receipt["links"].append(extra)
                        fixture.receipt["dependencyLinkCount"] += 1
                        fixture.resign()
                    elif condition == "link_escape":
                        fixture.receipt["links"][0]["rawRelativeTarget"] = "../../../outside"
                        fixture.receipt["links"][0]["resolvedCanonicalPackagePath"] = "outside"
                        fixture.resign()
                    elif condition == "headless_group":
                        fixture.receipt["headlessPatch"]["lstatIdentity"]["gid"] = 1
                        fixture.receipt["headlessPatch"]["lstatIdentity"]["rootOwned"] = False
                        fixture.resign()
                    else:
                        (fixture.source / fixture.cli.replace("node_modules/", "opt/deepseek-harness/node_modules/", 1)).write_bytes(b"tampered\n")
                    with mock.patch.object(capture, "ACCEPTED_MANIFEST_SHA256", fixture.manifest_sha), \
                            mock.patch.object(capture, "ACCEPTED_PACKAGE_COUNT", 2), \
                            mock.patch.object(capture, "ACCEPTED_MODULE_COUNT", 3), \
                            mock.patch.object(capture, "_validate_manifest", return_value=fixture.expected_packages), \
                            mock.patch.object(capture, "_create_link_at", side_effect=fixture.create_link), \
                            mock.patch.object(capture, "_inventory_topology", side_effect=fixture.inventory), \
                            mock.patch.object(capture.os, "fchmod", side_effect=fixture.fchmod, create=True), \
                            self.assertRaisesRegex(capture.CaptureBlocked, reason):
                        capture.stage_verified_topology(
                            fixture.manifest, fixture.receipt, fixture.receipt_sha, 101, 102, fixture.builder)
                finally:
                    fixture.close()

    def test_capture_transport_source_pin_is_independent_and_rechecked_remotely(self):
        source = b"print('fixture')\n"
        expected = hashlib.sha256(source).hexdigest()
        directory = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, directory)
        pinned = directory / "capture.py"
        pinned.write_bytes(source)
        self.assertEqual(capture._read_pinned_file(pinned, expected, "SOURCE_MISMATCH"), source)
        with self.assertRaisesRegex(capture.CaptureBlocked, "SOURCE_MISMATCH"):
            capture._read_pinned_file(pinned, "0" * 64, "SOURCE_MISMATCH")
        with self.assertRaisesRegex(capture.CaptureBlocked, "SOURCE_MISMATCH"):
            capture._read_pinned_file(directory, expected, "SOURCE_MISMATCH")
        with self.assertRaisesRegex(capture.CaptureBlocked, "CAPTURE_SOURCE_HASH_MISMATCH"):
            capture._transport_payload(source, "0" * 64, {}, b"")
        payload = json.loads(capture._transport_payload(source, expected, {}, b"{}").decode("utf-8"))
        self.assertEqual(payload["captureSourceSha256"], expected)
        encoded = capture._remote_command().split('b64decode("', 1)[1].split('")', 1)[0]
        bootstrap = __import__("base64").b64decode(encoded).decode("utf-8")
        self.assertIn('hashlib.sha256(b).hexdigest()==h', bootstrap)
        self.assertLess(bootstrap.index('hashlib.sha256(b).hexdigest()==h'), bootstrap.index('exec(compile'))

        contract = (SCRIPT.parent.parent / "docs/contracts/vm105-dsh-topology-capture-contract-20260913.md").read_text()
        command = contract.split("```powershell", 1)[1].split("```", 1)[0]
        self.assertLess(command.index("CAPTURE_SOURCE_HASH_MISMATCH"), command.index("| & python"))
        self.assertIn("source = $sourceText", command)

        powershell = shutil.which("powershell.exe") or shutil.which("powershell")
        if powershell:
            altered = directory / "altered.py"
            marker = directory / "executed.txt"
            altered.write_text('import os;open(os.environ["CAPTURE_TEST_MARKER"],"w").write("executed")\n')
            environment = os.environ.copy()
            environment.update(CAPTURE_TEST_SOURCE=str(altered), CAPTURE_TEST_MARKER=str(marker),
                               CAPTURE_TEST_EXPECTED=hashlib.sha256(b"pass\n").hexdigest())
            guard = r'''
$sourceBytes = [IO.File]::ReadAllBytes($env:CAPTURE_TEST_SOURCE)
$sha256 = [Security.Cryptography.SHA256]::Create()
try { $actual = [BitConverter]::ToString($sha256.ComputeHash($sourceBytes)).Replace('-', '').ToLowerInvariant() }
finally { $sha256.Dispose() }
if ($actual -cne $env:CAPTURE_TEST_EXPECTED) { exit 73 }
$sourceText = [Text.UTF8Encoding]::new($false, $true).GetString($sourceBytes)
$sourceText | & python -I -c 'import sys;exec(sys.stdin.read())'
'''
            result = subprocess.run([powershell, "-NoProfile", "-NonInteractive", "-Command", guard],
                                    env=environment, capture_output=True, timeout=5)
            self.assertEqual(result.returncode, 73)
            self.assertFalse(marker.exists())

    def test_capture_transport_has_total_and_output_bounds(self):
        self.assertEqual(capture._run_bounded(
            [sys.executable, "-c", "import sys;sys.stdout.buffer.write(b'ok')"],
            b"", 2, 1024, 1024), b"ok")
        cases = [
            ("timeout", [sys.executable, "-c", "import time;time.sleep(2)"],
             0.05, 1024, 1024, "CAPTURE_TIMEOUT"),
            ("stdout", [sys.executable, "-c", "import sys;sys.stdout.buffer.write(b'x'*2048)"],
             2, 1024, 1024, "CAPTURE_STDOUT_LIMIT_EXCEEDED"),
            ("stderr", [sys.executable, "-c", "import sys;sys.stderr.buffer.write(b'x'*2048)"],
             2, 1024, 1024, "CAPTURE_STDERR_LIMIT_EXCEEDED"),
        ]
        for name, command, timeout, stdout_limit, stderr_limit, reason in cases:
            with self.subTest(name=name):
                started = time.monotonic()
                with self.assertRaisesRegex(capture.CaptureBlocked, reason):
                    capture._run_bounded(command, b"", timeout, stdout_limit, stderr_limit)
                self.assertLess(time.monotonic() - started, 1.5)

    def test_receipt_is_validated_before_fresh_no_overwrite_publish(self):
        directory = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, directory)
        evidence = directory / "receipt.json"
        receipt = capture._signed_receipt({"status": "BLOCKED", "reasons": ["FIXTURE_BLOCKED"]})
        canonical = capture.canonical_bytes(receipt) + b"\n"
        validated = capture._validated_capture_stdout(canonical, {})
        capture._publish_fresh(evidence, validated)
        self.assertEqual(evidence.read_bytes(), canonical)
        with self.assertRaisesRegex(capture.CaptureBlocked, "CAPTURE_EVIDENCE_EXISTS"):
            capture._publish_fresh(evidence, canonical)
        self.assertEqual(evidence.read_bytes(), canonical)
        tampered = canonical.replace(b"FIXTURE_BLOCKED", b"FIXTURE_CHANGED")
        with self.assertRaisesRegex(capture.CaptureBlocked, "CAPTURE_RECEIPT_HASH_INVALID"):
            capture._validated_capture_stdout(tampered, {})
        self.assertEqual(evidence.read_bytes(), canonical)


if __name__ == "__main__":
    unittest.main()
