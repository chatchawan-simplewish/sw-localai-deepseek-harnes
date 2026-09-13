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
LDD = ("ldd",)
MODULE_SUFFIXES = {".js", ".cjs", ".mjs", ".json", ".node", ".wasm"}
ACCEPTED_MANIFEST_SHA256 = "4331e0e5fd9ac6f5e881a0dae941f9f07dea7b69969ee8b610071ce14cb03f8b"
ACCEPTED_MODULE_COUNT = 10_026
ACCEPTED_PINS = {
    "entrypoints": {
        ("@deepseek-ai/dsh", "lib/bin.js"): "c0226687bb20f45c603ec6fe50f3de16d1c3510c3a803304ec575ef9bc366c62",
        ("@deepseek-ai/dsh-client-ui-settings-models", "lib/client.js"): "c3b9a2d2d074c600c10553a4b15e294082f5851dd4a834d06ddb268b310d18de",
    },
    "config_bundles": {
        ("@deepseek-ai/dsh", "config/agent-presets/standard/agent.cordis.yml"): "fa14feb98daef20b810fef30bb7239a89a786de3c45c602b37743f7100d9a5af",
        ("@deepseek-ai/dsh-base", "cordis.patch.yml"): "9870a518274194c0e1ebd870cee2737fbc2ffc04ae36887871ffe6fcf74beac1",
        ("@deepseek-ai/dsh-web-app", "cordis.patch.yml"): "7889b655be3809dd21e3c59023f8510e6e8425f6f37616e4ba20389f2e938dda",
    },
}


class ManifestBlocked(RuntimeError):
    pass


def canonical_bytes(manifest: dict) -> bytes:
    return json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _require_descriptor_platform():
    if os.name != "posix" or not all(hasattr(os, name) for name in ("O_DIRECTORY", "O_NOFOLLOW")):
        raise ManifestBlocked("DESCRIPTOR_STAGING_UNSUPPORTED")


def _parts(path, absolute):
    if not isinstance(path, str) or "\\" in path or path.startswith("/") != absolute:
        raise ManifestBlocked("STAGING_PATH_INVALID")
    parts = path.split("/")[1:] if absolute else path.split("/")
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise ManifestBlocked("STAGING_PATH_INVALID")
    return parts


def _directory_at(root_fd, parts, create=False):
    current = os.dup(root_fd)
    try:
        for part in parts:
            if create:
                try:
                    os.mkdir(part, 0o700, dir_fd=current)
                except FileExistsError:
                    pass
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=current)
            if create:
                os.fchmod(child, 0o700)
            os.close(current)
            current = child
        return current
    except OSError as error:
        os.close(current)
        raise ManifestBlocked("STAGING_PATH_UNRESOLVED") from error


def _open_regular_at(root_fd, path, absolute):
    parts = _parts(path, absolute)
    parent = _directory_at(root_fd, parts[:-1])
    try:
        descriptor = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
    finally:
        os.close(parent)
    if not stat.S_ISREG(os.fstat(descriptor).st_mode):
        os.close(descriptor)
        raise ManifestBlocked("SOURCE_NOT_REGULAR")
    return descriptor


def _open_source_at(root_fd, canonical_path):
    return _open_regular_at(root_fd, canonical_path, True)


def _open_staged_at(root_fd, relative_path):
    return _open_regular_at(root_fd, relative_path, False)


def _create_destination_at(root_fd, relative_path):
    parts = _parts(relative_path, False)
    parent = _directory_at(root_fd, parts[:-1], create=True)
    try:
        return os.open(parts[-1], os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                       0o600, dir_fd=parent)
    finally:
        os.close(parent)


def _require_empty_staging(root_fd):
    try:
        if os.listdir(root_fd):
            raise ManifestBlocked("STAGING_ROOT_NOT_EMPTY")
    except OSError as error:
        raise ManifestBlocked("STAGING_ROOT_UNRESOLVED") from error


def _enumerate_staging(root_fd):
    files, directories = set(), {}

    def visit(directory_fd, prefix):
        for name in os.listdir(directory_fd):
            relative = "/".join((*prefix, name))
            info = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
            if stat.S_ISDIR(info.st_mode):
                directories[relative] = stat.S_IMODE(info.st_mode)
                child = _directory_at(directory_fd, [name])
                try:
                    visit(child, (*prefix, name))
                finally:
                    os.close(child)
            elif stat.S_ISREG(info.st_mode):
                files.add(relative)
            else:
                raise ManifestBlocked("STAGING_ARTIFACT_NOT_REGULAR")

    visit(root_fd, ())
    return files, directories


def _manifest_staging_rows(manifest):
    if not isinstance(manifest, dict) or manifest.get("status") != "PASS":
        raise ManifestBlocked("ACCEPTED_MANIFEST_REQUIRED")
    unsigned = dict(manifest)
    claimed = unsigned.pop("canonicalManifestSha256", None)
    actual = hashlib.sha256(canonical_bytes(unsigned)).hexdigest()
    modules = manifest.get("modules")
    if claimed != ACCEPTED_MANIFEST_SHA256 or actual != ACCEPTED_MANIFEST_SHA256:
        raise ManifestBlocked("ACCEPTED_MANIFEST_MISMATCH")
    if not isinstance(modules, list) or len(modules) != ACCEPTED_MODULE_COUNT:
        raise ManifestBlocked("ACCEPTED_MODULE_COUNT_MISMATCH")
    runtime = manifest.get("runtime")
    if not isinstance(runtime, dict) or not isinstance(runtime.get("dependencies"), list):
        raise ManifestBlocked("RUNTIME_UNRESOLVED")

    rows = []
    for row in modules:
        rows.append((row.get("sourceCanonicalPath"), row.get("stagedRelativePath"), row.get("sha256"), 0o600))
    for row in manifest.get("configBundles", []):
        logical = row.get("logicalPath")
        rows.append((row.get("canonicalPath"), "config/" + "/".join(_parts(logical, False)), row.get("sha256"), 0o600))
    for index, row in enumerate([runtime.get("node"), *runtime["dependencies"]]):
        if not isinstance(row, dict):
            raise ManifestBlocked("RUNTIME_UNRESOLVED")
        logical = row.get("logicalPath")
        rows.append((row.get("canonicalPath"), "runtime/" + "/".join(_parts(logical, True)),
                     row.get("sha256"), 0o500 if index == 0 else 0o600))

    destinations = set()
    for source, destination, expected, _mode in rows:
        _parts(source, True)
        _parts(destination, False)
        if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
            raise ManifestBlocked("STAGING_HASH_INVALID")
        if destination in destinations:
            raise ManifestBlocked("STAGING_PATH_COLLISION")
        destinations.add(destination)
    return rows


def _hash_fd(descriptor):
    value = hashlib.sha256()
    os.lseek(descriptor, 0, os.SEEK_SET)
    for part in iter(lambda: os.read(descriptor, 65536), b""):
        value.update(part)
    return value.hexdigest()


def _file_mode(descriptor):
    return stat.S_IMODE(os.fstat(descriptor).st_mode)


def stage_verified_closure(manifest, source_root_fd, staging_root_fd):
    """Copy the accepted closure between held Linux directory descriptors."""
    _require_descriptor_platform()
    _require_empty_staging(staging_root_fd)
    rows = _manifest_staging_rows(manifest)
    expected = {destination: (expected_hash, mode) for _, destination, expected_hash, mode in rows}
    expected_dirs = {"/".join(parts[:index]) for path in expected
                     for parts in [path.split("/")] for index in range(1, len(parts))}
    for source_path, destination_path, expected_hash, mode in rows:
        source_fd = destination_fd = None
        try:
            source_fd = _open_source_at(source_root_fd, source_path)
            before = os.fstat(source_fd)
            identity = (before.st_dev, before.st_ino, before.st_mode, before.st_size,
                        before.st_mtime_ns, before.st_ctime_ns)
            if _hash_fd(source_fd) != expected_hash:
                raise ManifestBlocked("SOURCE_HASH_MISMATCH")
            destination_fd = _create_destination_at(staging_root_fd, destination_path)
            os.lseek(source_fd, 0, os.SEEK_SET)
            for part in iter(lambda: os.read(source_fd, 65536), b""):
                view = memoryview(part)
                while view:
                    view = view[os.write(destination_fd, view):]
            os.fchmod(destination_fd, mode)
            os.fsync(destination_fd)
            after = os.fstat(source_fd)
            if identity != (after.st_dev, after.st_ino, after.st_mode, after.st_size,
                            after.st_mtime_ns, after.st_ctime_ns):
                raise ManifestBlocked("SOURCE_IDENTITY_DRIFT")
            if _hash_fd(destination_fd) != expected_hash:
                raise ManifestBlocked("STAGED_HASH_MISMATCH")
        except OSError as error:
            raise ManifestBlocked("STAGING_COPY_FAILED") from error
        finally:
            if destination_fd is not None:
                os.close(destination_fd)
            if source_fd is not None:
                os.close(source_fd)
    files, directories = _enumerate_staging(staging_root_fd)
    if (files != set(expected) or set(directories) != expected_dirs
            or any(mode != 0o700 for mode in directories.values())):
        raise ManifestBlocked("STAGING_TREE_MISMATCH")
    for path, (expected_hash, expected_mode) in expected.items():
        descriptor = _open_staged_at(staging_root_fd, path)
        try:
            if _hash_fd(descriptor) != expected_hash or _file_mode(descriptor) != expected_mode:
                raise ManifestBlocked("STAGED_FILE_MISMATCH")
        finally:
            os.close(descriptor)
    return {"status": "PASS", "files": len(rows), "modules": len(manifest["modules"]),
            "canonicalManifestSha256": ACCEPTED_MANIFEST_SHA256}


def digest(path):
    def identity(info):
        return (info.st_dev, info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns)

    try:
        canonical = path.resolve(strict=True)
        before = canonical.stat()
        if not stat.S_ISREG(before.st_mode):
            raise ManifestBlocked("ARTIFACT_NOT_REGULAR")
        value = hashlib.sha256()
        with os.fdopen(os.open(canonical, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)), "rb") as handle:
            opened = os.fstat(handle.fileno())
            if identity(before) != identity(opened):
                raise ManifestBlocked("FILE_HASH_DRIFT")
            for part in iter(lambda: handle.read(65536), b""):
                value.update(part)
            after_fd, after_path = os.fstat(handle.fileno()), path.stat()
            # Compare ctime within each API; Windows stat/fstat can report different values.
            if (identity(before) != identity(after_fd) or identity(before) != identity(after_path)
                    or opened.st_ctime_ns != after_fd.st_ctime_ns or before.st_ctime_ns != after_path.st_ctime_ns
                    or path.resolve(strict=True) != canonical):
                raise ManifestBlocked("FILE_HASH_DRIFT")
        return value.hexdigest()
    except OSError as error:
        raise ManifestBlocked("FILE_HASH_UNRESOLVED") from error


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


def regular(path, root):
    resolved = resolve_link(path, root)
    if not stat.S_ISREG(resolved.stat().st_mode):
        raise ManifestBlocked("ARTIFACT_NOT_REGULAR")
    return resolved


def package_links(fs_root):
    for item in sorted(fs_root.iterdir()):
        if item.name.startswith("."):
            continue
        if item.name.startswith("@"):
            if not stat.S_ISDIR(resolve_link(item, fs_root).stat().st_mode):
                raise ManifestBlocked("PACKAGE_ROOT_UNRESOLVED")
            for scoped in sorted(item.iterdir()):
                if not stat.S_ISDIR(resolve_link(scoped, fs_root).stat().st_mode):
                    raise ManifestBlocked("PACKAGE_ROOT_UNRESOLVED")
                yield scoped
        else:
            if not stat.S_ISDIR(resolve_link(item, fs_root).stat().st_mode):
                raise ManifestBlocked("PACKAGE_ROOT_UNRESOLVED")
            yield item


def dependency_link(package_root, name):
    virtual_node_modules = package_root.parent.parent if package_root.parent.name.startswith("@") else package_root.parent
    return virtual_node_modules / Path(*name.split("/"))


def runtime_dependencies(node_path):
    try:
        result = subprocess.run([*LDD, str(node_path)], capture_output=True, text=True, timeout=10, check=False)
    except (OSError, subprocess.SubprocessError):
        raise ManifestBlocked("RUNTIME_DEPENDENCY_UNRESOLVED")
    if result.returncode:
        raise ManifestBlocked("RUNTIME_DEPENDENCY_UNRESOLVED")
    if re.search(r"=>\s+not found(?:\s|$)", result.stdout):
        raise ManifestBlocked("RUNTIME_DEPENDENCY_UNRESOLVED")
    paths = set()
    for line in result.stdout.splitlines():
        match = re.search(r"=>\s+((?:/|[A-Za-z]:[\\/])[^\s(]+)", line)
        match = match or re.match(r"\s*((?:/|[A-Za-z]:[\\/])[^\s(]+)\s+\(", line)
        if match:
            paths.add(match.group(1))
    paths = sorted(paths)
    if not paths:
        raise ManifestBlocked("RUNTIME_DEPENDENCY_UNRESOLVED")
    values = []
    for value in paths:
        path = Path(value)
        try:
            canonical = path.resolve(strict=True)
        except OSError as error:
            raise ManifestBlocked("RUNTIME_DEPENDENCY_UNRESOLVED") from error
        if not stat.S_ISREG(canonical.stat().st_mode):
            raise ManifestBlocked("RUNTIME_DEPENDENCY_UNRESOLVED")
        values.append({"canonicalPath": str(canonical), "logicalPath": value, "sha256": digest(canonical)})
    return values


def pin_row(fs_root, logical_path, expected):
    path = fs_root / Path(*logical_path.split("/"))
    canonical = regular(path, fs_root)
    if digest(canonical) != expected:
        raise ManifestBlocked("ACCEPTED_PIN_MISMATCH")
    return {"logicalPath": logical_path, "canonicalPath": str(canonical), "sha256": expected}


def package_pin_row(fs_root, packages, pin, expected):
    name, relative = pin
    roots = [row for row in packages if row["name"] == name]
    if len(roots) != 1:
        raise ManifestBlocked("ACCEPTED_PACKAGE_ROOT_UNRESOLVED")
    logical = Path(roots[0]["logicalPath"]) / relative
    return pin_row(fs_root, logical.relative_to(fs_root).as_posix(), expected)


def selected_bundles(package):
    dsh = package.get("dsh", {})
    if not isinstance(dsh, dict):
        raise ManifestBlocked("CONFIG_BUNDLE_UNRESOLVED")
    profile = dsh.get("profile", {})
    if not isinstance(profile, dict):
        raise ManifestBlocked("CONFIG_BUNDLE_UNRESOLVED")
    bundles = profile.get("configBundles", [])
    if not isinstance(bundles, list) or not all(isinstance(value, str) for value in bundles):
        raise ManifestBlocked("CONFIG_BUNDLE_UNRESOLVED")
    found = set()
    for value in bundles:
        if not value.endswith(("cordis.yml", "cordis.patch.yml")) or value.startswith("/") or ".." in Path(value).parts:
            raise ManifestBlocked("CONFIG_BUNDLE_UNRESOLVED")
        found.add(value[2:] if value.startswith("./") else value)
    return found


def module_rows(canonical_root, logical_root, fs_root):
    rows = []
    def visit(directory):
        for path in sorted(directory.iterdir()):
            try:
                mode = path.lstat().st_mode
            except OSError as error:
                raise ManifestBlocked("ARTIFACT_UNRESOLVED") from error
            if stat.S_ISDIR(mode):
                visit(path)
            elif stat.S_ISLNK(mode):
                resolved = resolve_link(path, fs_root)
                if stat.S_ISDIR(resolved.stat().st_mode):
                    raise ManifestBlocked("ARTIFACT_SYMLINK_DIRECTORY")
                if path.suffix in MODULE_SUFFIXES:
                    canonical = regular(path, fs_root)
                    logical = logical_root / path.relative_to(canonical_root)
                    rows.append({"sourceLogicalPath": str(logical), "sourceCanonicalPath": str(canonical),
                                 "stagedRelativePath": "modules/" + str(logical.relative_to(fs_root)).replace("\\", "/"),
                                 "sha256": digest(canonical)})
            elif path.suffix in MODULE_SUFFIXES:
                canonical = regular(path, fs_root)
                logical = logical_root / path.relative_to(canonical_root)
                rows.append({"sourceLogicalPath": str(logical), "sourceCanonicalPath": str(canonical),
                             "stagedRelativePath": "modules/" + str(logical.relative_to(fs_root)).replace("\\", "/"),
                             "sha256": digest(canonical)})
    visit(canonical_root)
    return rows


def build_manifest(fs_root: Path, node_path: Path) -> dict:
    first = capture_inventory(fs_root, node_path)
    if capture_inventory(fs_root, node_path) != first:
        raise ManifestBlocked("INVENTORY_DRIFT")
    return first


def capture_inventory(fs_root: Path, node_path: Path) -> dict:
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
        if canonical in seen:
            continue
        seen.add(canonical)
        try:
            package = json.loads(regular(manifest_path, fs_root).read_text(encoding="utf-8"))
            name = package["name"]
        except (OSError, ValueError, KeyError) as error:
            raise ManifestBlocked("PACKAGE_MANIFEST_UNRESOLVED") from error
        packages.append({"name": name, "logicalPath": str(logical), "canonicalPath": str(canonical),
                         "version": package.get("version"), "_selectedBundles": sorted(selected_bundles(package))})
        declared = {}
        for key in ("dependencies", "optionalDependencies", "peerDependencies"):
            declared.update(package.get(key, {}))
        for dependency in sorted(declared):
            link = dependency_link(canonical, dependency)
            if not link.exists():
                if dependency in package.get("optionalDependencies", {}) or dependency in package.get("peerDependencies", {}):
                    continue
                raise ManifestBlocked("DEPENDENCY_UNRESOLVED")
            target = resolve_link(link, fs_root)
            edges.add(name + "->" + dependency)
            queue.append((link, target))
    if not packages:
        raise ManifestBlocked("PACKAGE_ROOT_UNRESOLVED")
    packages.sort(key=lambda row: row["name"])
    modules, selected = [], set()
    by_canonical = [(Path(row["canonicalPath"]), Path(row["logicalPath"])) for row in packages]
    for row, (canonical_root, logical_root) in zip(packages, by_canonical):
        modules.extend(module_rows(canonical_root, logical_root, fs_root))
        selected.update(str((logical_root / bundle).relative_to(fs_root)).replace("\\", "/") for bundle in row.pop("_selectedBundles"))
    modules.sort(key=lambda row: row["stagedRelativePath"])
    entrypoints = [package_pin_row(fs_root, packages, pin, value)
                   for pin, value in ACCEPTED_PINS["entrypoints"].items()]
    pinned_bundles = [package_pin_row(fs_root, packages, pin, value)
                      for pin, value in ACCEPTED_PINS["config_bundles"].items()]
    config_bundles = {row["logicalPath"]: row for row in pinned_bundles}
    for path in sorted(selected - config_bundles.keys()):
        config_bundles[path] = pin_row(fs_root, path, digest(regular(fs_root / path, fs_root)))
    config_bundles = list(config_bundles.values())
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
        value.pop("canonicalManifestSha256", None)
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
