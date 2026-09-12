import hashlib
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
import subprocess
from unittest.mock import patch


SCRIPTS = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS))


class FinalClientManifestTests(unittest.TestCase):
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
