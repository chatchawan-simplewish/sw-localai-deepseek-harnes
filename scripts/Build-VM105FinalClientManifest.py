#!/usr/bin/env python3
"""Capture a read-only, fail-closed VM105 installed client closure."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess


SSH = "C:/Windows/System32/OpenSSH/ssh.exe"
HOST = "dsh@192.168.1.139"
IDENTITY = "C:/Users/chatc/.ssh/codex-prox01-vms-ed25519"
INSTALL_ROOT = "/opt/deepseek-harness/node_modules"
NODE = "/opt/node-v24.19.0-linux-x64/bin/node"
MODULE_SUFFIXES = {".js", ".cjs", ".mjs", ".json", ".node", ".wasm"}
ACCEPTED_PINS = {
    "entrypoints": {
        "@deepseek-ai/dsh/lib/bin.js": "c0226687bb20f45c603ec6fe50f3de16d1c3510c3a803304ec575ef9bc366c62",
        "@deepseek-ai/dsh-client-ui-settings-models/lib/client.js": "c3b9a2d2d074c600c10553a4b15e294082f5851dd4a834d06ddb268b310d18de",
    },
    "config_bundles": {
        "@deepseek-ai/dsh/config/agent-presets/standard/agent.cordis.yml": "fa14feb98daef20b810fef30bb7239a89a786de3c45c602b37743f7100d9a5af",
        "@deepseek-ai/dsh-base/cordis.patch.yml": "9870a518274194c0e1ebd870cee2737fbc2ffc04ae36887871ffe6fcf74beac1",
        "@deepseek-ai/dsh-web-app/cordis.patch.yml": "7889b655be3809dd21e3c59023f8510e6e8425f6f37616e4ba20389f2e938dda",
    },
}


class ManifestBlocked(RuntimeError):
    pass


def canonical_bytes(manifest):
    return json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for part in iter(lambda: handle.read(65536), b""):
            value.update(part)
    return value.hexdigest()


def within(path, root):
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def resolve_link(path, root):
    try:
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise ManifestBlocked("UNRESOLVED_LINK") from error
    if not within(resolved, root):
        raise ManifestBlocked("LINK_ESCAPE")
    return resolved


def package_links(fs_root):
    for item in sorted(fs_root.iterdir()):
        if item.name.startswith(".") or not item.is_dir():
            continue
        if item.name.startswith("@"):
            for scoped in sorted(item.iterdir()):
                if scoped.is_dir() or scoped.is_symlink():
                    yield scoped
        else:
            yield item


def dependency_link(package_root, name):
    return package_root / "node_modules" / Path(*name.split("/"))


def runtime_dependencies(node_path):
    try:
        result = subprocess.run(["ldd", str(node_path)], capture_output=True, text=True, timeout=10, check=False)
    except (OSError, subprocess.SubprocessError):
        raise ManifestBlocked("RUNTIME_DEPENDENCY_UNRESOLVED")
    if result.returncode:
        raise ManifestBlocked("RUNTIME_DEPENDENCY_UNRESOLVED")
    paths = sorted(set(re.findall(r"(?<!\S)(/[^\s(]+)", result.stdout)))
    if not paths:
        raise ManifestBlocked("RUNTIME_DEPENDENCY_UNRESOLVED")
    values = []
    for value in paths:
        path = Path(value)
        if not path.is_file() or path.is_symlink():
            raise ManifestBlocked("RUNTIME_DEPENDENCY_UNRESOLVED")
        values.append({"canonicalPath": str(path.resolve()), "logicalPath": value, "sha256": digest(path)})
    return values


def pin_row(fs_root, logical_path, expected):
    path = fs_root / Path(*logical_path.split("/"))
    canonical = resolve_link(path, fs_root)
    if not stat.S_ISREG(canonical.stat().st_mode) or digest(canonical) != expected:
        raise ManifestBlocked("ACCEPTED_PIN_MISMATCH")
    return {"logicalPath": logical_path, "canonicalPath": str(canonical), "sha256": expected}


def build_manifest(fs_root, node_path):
    fs_root = Path(fs_root).resolve(strict=True)
    node_path = Path(node_path)
    if not fs_root.is_dir() or not node_path.is_file() or node_path.is_symlink():
        raise ManifestBlocked("ROOT_OR_NODE_UNRESOLVED")
    packages, edges, seen, queue = [], set(), set(), []
    for logical in package_links(fs_root):
        queue.append((logical, resolve_link(logical, fs_root)))
    while queue:
        logical, canonical = queue.pop(0)
        manifest_path = canonical / "package.json"
        if canonical in seen or not manifest_path.is_file():
            continue
        seen.add(canonical)
        try:
            package = json.loads(manifest_path.read_text(encoding="utf-8"))
            name = package["name"]
        except (OSError, ValueError, KeyError) as error:
            raise ManifestBlocked("PACKAGE_MANIFEST_UNRESOLVED") from error
        packages.append({"name": name, "logicalPath": str(logical), "canonicalPath": str(canonical),
                         "version": package.get("version")})
        declared = {}
        for key in ("dependencies", "optionalDependencies", "peerDependencies"):
            declared.update(package.get(key, {}))
        for dependency in sorted(declared):
            link = dependency_link(canonical, dependency)
            if not link.exists() and not link.is_symlink():
                if dependency in package.get("optionalDependencies", {}) or dependency in package.get("peerDependencies", {}):
                    continue
                raise ManifestBlocked("DEPENDENCY_UNRESOLVED")
            target = resolve_link(link, fs_root)
            edges.add(name + "->" + dependency)
            queue.append((link, target))
    if not packages:
        raise ManifestBlocked("PACKAGE_ROOT_UNRESOLVED")
    packages.sort(key=lambda row: row["name"])
    modules, discovered_bundles = [], set()
    by_canonical = [(Path(row["canonicalPath"]), Path(row["logicalPath"])) for row in packages]
    for canonical_root, logical_root in by_canonical:
        for path in sorted(canonical_root.rglob("*")):
            if not path.is_file() or path.is_symlink():
                continue
            relative = path.relative_to(canonical_root)
            if path.suffix not in MODULE_SUFFIXES and path.name not in {"cordis.yml", "cordis.patch.yml"}:
                continue
            logical = logical_root / relative
            staged = "modules/" + str(logical.relative_to(fs_root)).replace("\\", "/")
            modules.append({"sourceLogicalPath": str(logical), "sourceCanonicalPath": str(path),
                            "stagedRelativePath": staged, "sha256": digest(path)})
            if path.name in {"cordis.yml", "cordis.patch.yml"}:
                discovered_bundles.add(str(logical.relative_to(fs_root)).replace("\\", "/"))
    modules.sort(key=lambda row: row["stagedRelativePath"])
    entrypoints = [pin_row(fs_root, path, value) for path, value in ACCEPTED_PINS["entrypoints"].items()]
    bundle_paths = set(ACCEPTED_PINS["config_bundles"]) | discovered_bundles
    config_bundles = []
    for path in sorted(bundle_paths):
        expected = ACCEPTED_PINS["config_bundles"].get(path)
        row = pin_row(fs_root, path, expected) if expected else pin_row(fs_root, path, digest(resolve_link(fs_root / Path(*path.split("/")), fs_root)))
        config_bundles.append(row)
    entrypoints.sort(key=lambda row: row["logicalPath"])
    config_bundles.sort(key=lambda row: row["logicalPath"])
    return {"status": "PASS", "packages": packages, "edges": sorted(edges), "entrypoints": entrypoints,
            "configBundles": config_bundles, "modules": modules,
            "runtime": {"node": {"logicalPath": str(node_path), "canonicalPath": str(node_path.resolve()),
                                 "sha256": digest(node_path)}, "dependencies": runtime_dependencies(node_path)}}


def ssh_argv():
    return [SSH, "-T", "-i", IDENTITY, "-o", "BatchMode=yes", "-o", "IdentitiesOnly=yes",
            "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=10", HOST, "/usr/bin/python3.12 -I - --remote"]


def capture_remote():
    result = subprocess.run(ssh_argv(), input=Path(__file__).read_bytes(), capture_output=True, timeout=60)
    if result.returncode or result.stderr or len(result.stdout) > 10_000_000:
        return {"status": "BLOCKED", "reasons": ["SSH_CAPTURE_FAILED"]}
    try:
        value = json.loads(result.stdout)
    except ValueError:
        return {"status": "BLOCKED", "reasons": ["SSH_RECEIPT_INVALID"]}
    if not isinstance(value, dict) or value.get("status") not in {"PASS", "BLOCKED"}:
        return {"status": "BLOCKED", "reasons": ["SSH_RECEIPT_INVALID"]}
    return value


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture-root", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--remote", action="store_true")
    args = parser.parse_args(argv)
    if args.remote:
        try:
            value = build_manifest(Path(INSTALL_ROOT), Path(NODE))
        except ManifestBlocked as error:
            value = {"status": "BLOCKED", "reasons": [str(error)]}
    elif args.fixture_root:
        try:
            value = build_manifest(args.fixture_root / "node_modules", args.fixture_root / "node")
        except ManifestBlocked as error:
            value = {"status": "BLOCKED", "reasons": [str(error)]}
    else:
        value = capture_remote()
    if value["status"] == "PASS":
        value["canonicalManifestSha256"] = hashlib.sha256(canonical_bytes(value)).hexdigest()
    encoded = canonical_bytes(value)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(encoded)
    else:
        print(encoded.decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
