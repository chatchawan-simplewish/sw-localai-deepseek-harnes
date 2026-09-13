import hashlib
import importlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest
import subprocess
from unittest.mock import patch


SCRIPTS = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS))


class FinalClientManifestTests(unittest.TestCase):
    def staging_fixture(self):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        source, staging = root / "source", root / "staging"
        files = {
            "/opt/modules/a.js": b"module\n",
            "/opt/config/agent.yml": b"config\n",
            "/opt/node": b"node\n",
            "/lib/libfixture.so": b"library\n",
        }
        for logical, value in files.items():
            path = source / logical.lstrip("/")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(value)
        staging.mkdir()

        def row(logical, staged=None):
            value = {"logicalPath": logical, "canonicalPath": logical,
                     "sha256": hashlib.sha256(files[logical]).hexdigest()}
            if staged:
                value = {"sourceLogicalPath": logical, "sourceCanonicalPath": logical,
                         "stagedRelativePath": staged, "sha256": value["sha256"]}
            return value

        config = row("/opt/config/agent.yml")
        config["logicalPath"] = "opt/config/agent.yml"
        manifest = {
            "status": "PASS", "packages": [], "edges": [], "entrypoints": [],
            "configBundles": [config],
            "modules": [row("/opt/modules/a.js", "modules/a.js")],
            "runtime": {"node": row("/opt/node"), "dependencies": [row("/lib/libfixture.so")]},
        }
        accepted = hashlib.sha256(importlib.import_module("Build-VM105FinalClientManifest").canonical_bytes(manifest)).hexdigest()
        manifest["canonicalManifestSha256"] = accepted
        return temp, source, staging, manifest, accepted

    def staging_patches(self, module, source, staging, before_enumerate=None,
                        file_mode_override=None, directory_mode_override=None):
        opened_staged = {}
        def open_source(_root_fd, canonical):
            path = source / canonical.lstrip("/")
            if path.is_symlink():
                raise module.ManifestBlocked("SOURCE_LINK")
            return os.open(path, os.O_RDONLY | getattr(os, "O_BINARY", 0))

        def create_destination(_root_fd, relative):
            path = staging / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            return os.open(path, os.O_RDWR | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0), 0o600)

        def enumerate_staging(_root_fd):
            if before_enumerate:
                before_enumerate()
            files = {path.relative_to(staging).as_posix() for path in staging.rglob("*") if path.is_file()}
            directories = {path.relative_to(staging).as_posix(): 0o700 for path in staging.rglob("*") if path.is_dir()}
            if directory_mode_override:
                directories[directory_mode_override[0]] = directory_mode_override[1]
            return files, directories

        def open_staged(_root_fd, relative):
            descriptor = os.open(staging / relative, os.O_RDONLY | getattr(os, "O_BINARY", 0))
            opened_staged[descriptor] = relative
            return descriptor

        def file_mode(descriptor):
            relative = opened_staged[descriptor]
            if file_mode_override and relative == file_mode_override[0]:
                return file_mode_override[1]
            return 0o500 if relative == "runtime/opt/node" else 0o600

        return (patch.object(module, "_require_descriptor_platform"),
                patch.object(module, "_require_empty_staging", side_effect=lambda _fd: None if not any(staging.iterdir()) else (_ for _ in ()).throw(module.ManifestBlocked("STAGING_ROOT_NOT_EMPTY"))),
                patch.object(module, "_open_source_at", side_effect=open_source),
                patch.object(module, "_create_destination_at", side_effect=create_destination),
                patch.object(module, "_enumerate_staging", side_effect=enumerate_staging),
                patch.object(module, "_open_staged_at", side_effect=open_staged),
                patch.object(module, "_file_mode", side_effect=file_mode))

    def test_stage_verified_closure_copies_complete_pinned_tree(self):
        """Fails until descriptor-held staging copies modules, config, Node, and libraries."""
        module = importlib.import_module("Build-VM105FinalClientManifest")
        temp, source, staging, manifest, accepted = self.staging_fixture()
        self.addCleanup(temp.cleanup)
        patches = self.staging_patches(module, source, staging)
        with patch.object(module, "ACCEPTED_MANIFEST_SHA256", accepted), patch.object(module, "ACCEPTED_MODULE_COUNT", 1), patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6], patch.object(module.os, "fchmod", create=True) as chmod:
            receipt = module.stage_verified_closure(manifest, 101, 102)
        self.assertEqual({"status": "PASS", "files": 4, "modules": 1,
                          "canonicalManifestSha256": accepted}, receipt)
        self.assertEqual(b"module\n", (staging / "modules/a.js").read_bytes())
        self.assertEqual(b"config\n", (staging / "config/opt/config/agent.yml").read_bytes())
        self.assertEqual(b"node\n", (staging / "runtime/opt/node").read_bytes())
        self.assertEqual(b"library\n", (staging / "runtime/lib/libfixture.so").read_bytes())
        self.assertEqual([0o600, 0o600, 0o500, 0o600], [call.args[1] for call in chmod.call_args_list])

    def test_stage_verified_closure_blocks_changed_duplicate_link_and_extra_inputs(self):
        """Fails until every new staging trust boundary fails closed."""
        module = importlib.import_module("Build-VM105FinalClientManifest")
        for condition in ("changed", "duplicate", "link", "extra", "late_mutation", "empty_dir",
                          "file_mode", "directory_mode"):
            with self.subTest(condition=condition):
                temp, source, staging, manifest, accepted = self.staging_fixture()
                try:
                    if condition == "changed":
                        (source / "opt/modules/a.js").write_bytes(b"changed\n")
                    elif condition == "duplicate":
                        manifest["configBundles"].append(dict(manifest["configBundles"][0]))
                        unsigned = dict(manifest)
                        unsigned.pop("canonicalManifestSha256")
                        accepted = hashlib.sha256(module.canonical_bytes(unsigned)).hexdigest()
                        manifest["canonicalManifestSha256"] = accepted
                    elif condition == "link":
                        target = source / "opt/modules/real.js"
                        target.write_bytes(b"module\n")
                        (source / "opt/modules/a.js").unlink()
                        try:
                            os.symlink(target, source / "opt/modules/a.js")
                        except OSError:
                            continue
                    before_enumerate = None
                    if condition == "extra":
                        before_enumerate = lambda: (staging / "extra").write_bytes(b"extra")
                    elif condition == "late_mutation":
                        before_enumerate = lambda: (staging / "modules/a.js").write_bytes(b"late mutation")
                    elif condition == "empty_dir":
                        before_enumerate = lambda: (staging / "empty").mkdir()
                    file_mode = ("modules/a.js", 0o644) if condition == "file_mode" else None
                    directory_mode = ("modules", 0o755) if condition == "directory_mode" else None
                    patches = self.staging_patches(module, source, staging, before_enumerate,
                                                   file_mode, directory_mode)
                    with patch.object(module, "ACCEPTED_MANIFEST_SHA256", accepted), patch.object(module, "ACCEPTED_MODULE_COUNT", 1), patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6], patch.object(module.os, "fchmod", create=True), self.assertRaises(module.ManifestBlocked):
                        module.stage_verified_closure(manifest, 101, 102)
                finally:
                    temp.cleanup()

    def test_open_source_leaf_is_nonblocking_before_regular_file_check(self):
        """Fails if a FIFO leaf can block the source open before fstat rejects it."""
        module = importlib.import_module("Build-VM105FinalClientManifest")
        regular = os.stat_result((stat.S_IFREG | 0o600, 0, 0, 0, 0, 0, 0, 0, 0, 0))
        with patch.object(module, "_directory_at", return_value=98), patch.object(module.os, "O_NOFOLLOW", 0, create=True), patch.object(module.os, "O_NONBLOCK", 0x4000, create=True), patch.object(module.os, "open", return_value=99) as opened, patch.object(module.os, "fstat", return_value=regular), patch.object(module.os, "close"):
            self.assertEqual(99, module._open_source_at(1, "/source"))
        self.assertTrue(opened.call_args.args[1] & 0x4000)

    @unittest.skipUnless(os.name == "nt", "Windows-specific platform gate")
    def test_descriptor_staging_fails_closed_unpatched_on_windows(self):
        """Fails if Windows reaches descriptor-relative staging primitives."""
        module = importlib.import_module("Build-VM105FinalClientManifest")
        with self.assertRaisesRegex(module.ManifestBlocked, "DESCRIPTOR_STAGING_UNSUPPORTED"):
            module.stage_verified_closure({}, -1, -1)

    def test_digest_blocks_identity_drift_during_hash(self):
        """Fails if changed bytes on the held file descriptor retain a successful digest."""
        module = importlib.import_module("Build-VM105FinalClientManifest")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "module.js"
            path.write_bytes(b"old")
            original_sha256 = hashlib.sha256

            class MutatingHash:
                def __init__(self): self.value = original_sha256()
                def update(self, data):
                    self.value.update(data)
                    path.write_bytes(b"changed length")
                def hexdigest(self): return self.value.hexdigest()

            with patch.object(module.hashlib, "sha256", MutatingHash), self.assertRaises(module.ManifestBlocked):
                module.digest(path)

    def test_build_manifest_blocks_file_changes_between_inventory_passes(self):
        """Fails if a previously captured module changes before final inventory verification."""
        module = importlib.import_module("Build-VM105FinalClientManifest")
        for change in ('rewrite', 'add', 'remove'):
            with self.subTest(change=change):
                temp, root, node = self.fixture()
                try:
                    ldd, _, _ = self.ldd(root)
                    target = root / "node_modules/.pnpm/beta/node_modules/@fixture/beta/lib/worker.cjs"
                    original_runtime = module.runtime_dependencies
                    changed = False

                    def mutate_after_first_inventory(node_path):
                        nonlocal changed
                        result = original_runtime(node_path)
                        if not changed:
                            changed = True
                            if change == 'rewrite': target.write_bytes(b'new module bytes')
                            elif change == 'add': target.with_name('new.js').write_bytes(b'new module')
                            else: target.unlink()
                        return result

                    with patch.object(module, "LDD", ldd), patch.object(module, "ACCEPTED_PINS", {"entrypoints": {}, "config_bundles": {}}), patch.object(module, "runtime_dependencies", mutate_after_first_inventory):
                        with self.assertRaises(module.ManifestBlocked):
                            module.build_manifest(root / "node_modules", node)
                finally:
                    temp.cleanup()

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")

    def link_dir(self, target, link):
        link.parent.mkdir(parents=True, exist_ok=True)
        if os.name == "nt":
            subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)], check=True, capture_output=True)
        else:
            os.symlink(target, link, target_is_directory=True)

    def ldd(self, root, missing=False):
        library = root / "libs" / "libfixture.so"
        alias_dir = root / "alias-libs"
        alias = alias_dir / "libfixture.so"
        self.write(library, "library\n")
        try:
            os.symlink(library.parent, alias_dir, target_is_directory=True)
        except OSError:
            self.link_dir(library.parent, alias_dir)
        script = root / "fake-ldd.py"
        body = "import sys\n"
        body += "print('libfixture.so => " + str(alias).replace("\\", "/") + " (0x1)')\n"
        if missing:
            body += "print('libmissing.so => not found')\n"
        self.write(script, body)
        return (sys.executable, str(script)), library, alias

    def fixture(self):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        packages = root / "node_modules" / ".pnpm"
        alpha = packages / "alpha" / "node_modules" / "@fixture" / "alpha"
        beta = packages / "beta" / "node_modules" / "@fixture" / "beta"
        self.write(alpha / "package.json", json.dumps({
            "name": "@fixture/alpha", "version": "1.0.0",
            "dependencies": {"@fixture/beta": "1.0.0"}, "dsh": {"profile": {"configBundles": ["config/agent.cordis.yml"]}},
        }))
        self.write(beta / "package.json", json.dumps({
            "name": "@fixture/beta", "version": "1.0.0",
            "peerDependencies": {"@fixture/alpha": "1.0.0"}, "dsh": {"profile": {"configBundles": ["config/cordis.patch.yml"]}},
        }))
        self.write(alpha / "lib" / "cli.js", "console.log('cli')\n")
        self.write(alpha / "lib" / "client.mjs", "export default 1\n")
        self.write(alpha / "config" / "agent.cordis.yml", "plugins: []\n")
        self.write(alpha / "native" / "addon.node", "native\n")
        self.write(beta / "lib" / "worker.cjs", "module.exports = 1\n")
        self.write(beta / "config" / "cordis.patch.yml", "patch: true\n")
        self.write(root / "node", "node fixture\n")
        logical = root / "node_modules" / "@fixture"
        logical.mkdir(parents=True)
        self.link_dir(alpha, logical / "alpha")
        self.link_dir(beta, alpha.parent / "beta")
        return temp, root, root / "node"

    def test_build_manifest_freezes_sorted_closure_and_runtime(self):
        """Fails if reachable files, pins, or their stable order are omitted."""
        module = importlib.import_module("Build-VM105FinalClientManifest")
        temp, root, node = self.fixture()
        self.addCleanup(temp.cleanup)
        logical = root / "node_modules" / "@fixture" / "alpha"
        pins = {
            "entrypoints": {("@fixture/alpha", "lib/cli.js"): hashlib.sha256((logical / "lib" / "cli.js").read_bytes()).hexdigest(),
                            ("@fixture/alpha", "lib/client.mjs"): hashlib.sha256((logical / "lib" / "client.mjs").read_bytes()).hexdigest()},
            "config_bundles": {("@fixture/alpha", "config/agent.cordis.yml"): hashlib.sha256((logical / "config" / "agent.cordis.yml").read_bytes()).hexdigest()},
        }
        ldd, library, alias = self.ldd(root)
        with patch.object(module, "ACCEPTED_PINS", pins), patch.object(module, "LDD", ldd):
            manifest = module.build_manifest(root / "node_modules", node)

        self.assertEqual("PASS", manifest["status"])
        self.assertEqual(["@fixture/alpha", "@fixture/beta"], [row["name"] for row in manifest["packages"]])
        self.assertEqual(["@fixture/alpha->@fixture/beta"], manifest["edges"])
        self.assertEqual(sorted(manifest["entrypoints"], key=lambda row: row["logicalPath"]), manifest["entrypoints"])
        self.assertEqual(sorted(manifest["configBundles"], key=lambda row: row["logicalPath"]), manifest["configBundles"])
        self.assertEqual({"/".join(key): value for key, value in pins["entrypoints"].items()}, {row["logicalPath"]: row["sha256"] for row in manifest["entrypoints"]})
        captured_bundles = {row["logicalPath"]: row["sha256"] for row in manifest["configBundles"]}
        self.assertEqual({"/".join(key): value for key, value in pins["config_bundles"].items()}, {"/".join(key): captured_bundles["/".join(key)] for key in pins["config_bundles"]})
        self.assertIn(".pnpm/alpha/node_modules/@fixture/beta/config/cordis.patch.yml", captured_bundles)
        self.assertEqual(sorted(row["stagedRelativePath"] for row in manifest["modules"]),
                         [row["stagedRelativePath"] for row in manifest["modules"]])
        self.assertIn("node", manifest["runtime"])
        self.assertEqual(hashlib.sha256(node.read_bytes()).hexdigest(), manifest["runtime"]["node"]["sha256"])
        self.assertIn("addon.node", [Path(row["sourceLogicalPath"]).name for row in manifest["modules"]])
        self.assertEqual(str(alias).replace("\\", "/"), manifest["runtime"]["dependencies"][0]["logicalPath"])
        self.assertEqual(str(alias.resolve()), manifest["runtime"]["dependencies"][0]["canonicalPath"])
        self.assertEqual(module.canonical_bytes(manifest), module.canonical_bytes(json.loads(module.canonical_bytes(manifest))))

    def test_nested_package_pins_resolve_discovered_roots(self):
        """Fails if accepted pins require an absent top-level package link."""
        module = importlib.import_module("Build-VM105FinalClientManifest")
        temp, root, node = self.fixture()
        self.addCleanup(temp.cleanup)
        pins = {"entrypoints": {("@fixture/beta", "lib/worker.cjs"): hashlib.sha256((root / "node_modules/.pnpm/beta/node_modules/@fixture/beta/lib/worker.cjs").read_bytes()).hexdigest()},
                "config_bundles": {}}
        ldd, _, _ = self.ldd(root)
        with patch.object(module, "ACCEPTED_PINS", pins), patch.object(module, "LDD", ldd):
            manifest = module.build_manifest(root / "node_modules", node)
        row = manifest["entrypoints"][0]
        self.assertEqual(".pnpm/alpha/node_modules/@fixture/beta/lib/worker.cjs", row["logicalPath"])
        self.assertEqual(str(root / "node_modules/.pnpm/beta/node_modules/@fixture/beta/lib/worker.cjs"), row["canonicalPath"])
        staged = [row["stagedRelativePath"] for row in manifest["modules"]]
        self.assertEqual(len(staged), len(set(staged)))

    def test_package_pins_reject_missing_ambiguous_roots_and_mismatch(self):
        """Fails if a pin silently picks an absent or ambiguous package or changed bytes."""
        module = importlib.import_module("Build-VM105FinalClientManifest")
        for condition in ("missing", "ambiguous", "mismatch"):
            with self.subTest(condition=condition):
                temp, root, node = self.fixture()
                try:
                    name = "absent" if condition == "missing" else "@fixture/beta"
                    if condition == "ambiguous":
                        other = root / "node_modules/other"
                        self.write(other / "package.json", '{"name":"@fixture/beta"}')
                    pins = {"entrypoints": {(name, "lib/worker.cjs"): "0" * 64}, "config_bundles": {}}
                    with patch.object(module, "ACCEPTED_PINS", pins), self.assertRaises(module.ManifestBlocked):
                        module.build_manifest(root / "node_modules", node)
                finally:
                    temp.cleanup()

    def test_capture_hash_excludes_existing_remote_hash(self):
        """Fails if local capture hashes the remote hash into its own digest."""
        module = importlib.import_module("Build-VM105FinalClientManifest")
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "manifest.json"
            receipt = {"status": "PASS", "canonicalManifestSha256": "remote-hash"}
            with patch.object(module, "capture_remote", return_value=receipt):
                module.main(["--output", str(output)])
            actual = json.loads(output.read_bytes())
            self.assertEqual(hashlib.sha256(b'{"status":"PASS"}').hexdigest(), actual["canonicalManifestSha256"])

    def test_build_manifest_blocks_dependency_link_escape(self):
        """Fails if an escaped dependency link is accepted into the closure."""
        module = importlib.import_module("Build-VM105FinalClientManifest")
        temp, root, node = self.fixture()
        self.addCleanup(temp.cleanup)
        escaped = root.parent / "escaped-package"
        escaped.mkdir(exist_ok=True)
        self.addCleanup(lambda: escaped.rmdir())
        link = root / "node_modules" / ".pnpm" / "alpha" / "node_modules" / "@fixture" / "beta"
        os.rmdir(link)
        self.link_dir(escaped, link)
        with self.assertRaises(module.ManifestBlocked):
            module.build_manifest(root / "node_modules", node)

    def test_dangling_dependency_links_skip_only_optional_and_peer(self):
        """Fails if absent optional links block closure or absent required links pass."""
        module = importlib.import_module("Build-VM105FinalClientManifest")
        for declaration in ("optionalDependencies", "peerDependencies", "dependencies"):
            with self.subTest(declaration=declaration), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                package = root / "node_modules" / ".pnpm" / "fixture" / "node_modules" / "fixture"
                self.write(package / "package.json", json.dumps({"name": "fixture", declaration: {"absent": "1"}}))
                self.write(root / "node", "node fixture")
                self.link_dir(package, root / "node_modules" / "fixture")
                link = package.parent / "absent"
                try:
                    os.symlink(package.parent / "missing", link, target_is_directory=True)
                except OSError:
                    self.link_dir(package.parent / "missing", link)
                self.assertFalse(link.exists())
                # Windows junctions provide the real dangling directory entry; expose
                # its link classification where file-symlink privilege is unavailable.
                original = Path.is_symlink
                def is_link(path):
                    return original(path) or (path == link and path.is_junction())
                ldd, _, _ = self.ldd(root)
                with patch.object(Path, "is_symlink", is_link), patch.object(module, "LDD", ldd), patch.object(module, "ACCEPTED_PINS", {"entrypoints": {}, "config_bundles": {}}):
                    if declaration == "dependencies":
                        with self.assertRaises(module.ManifestBlocked):
                            module.build_manifest(root / "node_modules", root / "node")
                    else:
                        manifest = module.build_manifest(root / "node_modules", root / "node")
                        self.assertEqual("PASS", manifest["status"])
                        self.assertEqual([], manifest["edges"])
                        self.assertEqual(["fixture"], [row["name"] for row in manifest["packages"]])

    def test_runtime_dependencies_blocks_missing_library(self):
        """Fails if one unresolved ldd library is ignored beside a resolved one."""
        module = importlib.import_module("Build-VM105FinalClientManifest")
        temp, root, node = self.fixture()
        self.addCleanup(temp.cleanup)
        ldd, _, _ = self.ldd(root, missing=True)
        with patch.object(module, "LDD", ldd), self.assertRaises(module.ManifestBlocked):
            module.runtime_dependencies(node)

    def test_dependency_lookup_uses_literal_scoped_and_unscoped_virtual_store_layouts(self):
        """Fails if either pnpm package shape resolves dependencies from the wrong sibling directory."""
        module = importlib.import_module("Build-VM105FinalClientManifest")
        self.assertEqual(Path("/virtual/node_modules/bar"), module.dependency_link(Path("/virtual/node_modules/foo"), "bar"))
        self.assertEqual(Path("/virtual/node_modules/@scope/bar"), module.dependency_link(Path("/virtual/node_modules/@scope/foo"), "@scope/bar"))

    def test_unrelated_manifest_url_is_not_a_cordis_bundle(self):
        """Fails if arbitrary metadata strings are mistaken for selected configuration."""
        module = importlib.import_module("Build-VM105FinalClientManifest")
        self.assertEqual(set(), module.selected_bundles({"homepage": "https://example.invalid/cordis.yml"}))

    def test_selected_bundles_blocks_malformed_dsh_shapes(self):
        """Fails if malformed manifest configuration raises AttributeError instead of blocking."""
        module = importlib.import_module("Build-VM105FinalClientManifest")
        for package in ({"dsh": None}, {"dsh": {"profile": None}}):
            with self.assertRaises(module.ManifestBlocked):
                module.selected_bundles(package)


if __name__ == "__main__":
    unittest.main()
