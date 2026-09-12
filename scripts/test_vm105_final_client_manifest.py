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

    def fixture(self):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        packages = root / "node_modules" / ".pnpm"
        alpha = packages / "alpha"
        beta = packages / "beta"
        self.write(alpha / "package.json", json.dumps({
            "name": "@fixture/alpha", "version": "1.0.0",
            "dependencies": {"@fixture/beta": "1.0.0"},
        }))
        self.write(beta / "package.json", json.dumps({
            "name": "@fixture/beta", "version": "1.0.0",
            "peerDependencies": {"@fixture/alpha": "1.0.0"},
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
        self.link_dir(beta, alpha / "node_modules" / "@fixture" / "beta")
        return temp, root, root / "node"

    def test_build_manifest_freezes_sorted_closure_and_runtime(self):
        """Fails if reachable files, pins, or their stable order are omitted."""
        module = importlib.import_module("Build-VM105FinalClientManifest")
        temp, root, node = self.fixture()
        self.addCleanup(temp.cleanup)
        logical = root / "node_modules" / "@fixture" / "alpha"
        pins = {
            "entrypoints": {"@fixture/alpha/lib/cli.js": hashlib.sha256((logical / "lib" / "cli.js").read_bytes()).hexdigest(),
                            "@fixture/alpha/lib/client.mjs": hashlib.sha256((logical / "lib" / "client.mjs").read_bytes()).hexdigest()},
            "config_bundles": {"@fixture/alpha/config/agent.cordis.yml": hashlib.sha256((logical / "config" / "agent.cordis.yml").read_bytes()).hexdigest()},
        }
        with patch.object(module, "ACCEPTED_PINS", pins), patch.object(module, "runtime_dependencies", return_value=[]):
            manifest = module.build_manifest(root / "node_modules", node)

        self.assertEqual("PASS", manifest["status"])
        self.assertEqual(["@fixture/alpha", "@fixture/beta"], [row["name"] for row in manifest["packages"]])
        self.assertEqual(["@fixture/alpha->@fixture/beta"], manifest["edges"])
        self.assertEqual(sorted(manifest["entrypoints"], key=lambda row: row["logicalPath"]), manifest["entrypoints"])
        self.assertEqual(sorted(manifest["configBundles"], key=lambda row: row["logicalPath"]), manifest["configBundles"])
        self.assertEqual(pins["entrypoints"], {row["logicalPath"]: row["sha256"] for row in manifest["entrypoints"]})
        captured_bundles = {row["logicalPath"]: row["sha256"] for row in manifest["configBundles"]}
        self.assertEqual(pins["config_bundles"], {key: captured_bundles[key] for key in pins["config_bundles"]})
        self.assertIn(".pnpm/alpha/node_modules/@fixture/beta/config/cordis.patch.yml", captured_bundles)
        self.assertEqual(sorted(row["stagedRelativePath"] for row in manifest["modules"]),
                         [row["stagedRelativePath"] for row in manifest["modules"]])
        self.assertIn("node", manifest["runtime"])
        self.assertEqual(hashlib.sha256(node.read_bytes()).hexdigest(), manifest["runtime"]["node"]["sha256"])
        self.assertEqual(module.canonical_bytes(manifest), module.canonical_bytes(json.loads(module.canonical_bytes(manifest))))

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


if __name__ == "__main__":
    unittest.main()
