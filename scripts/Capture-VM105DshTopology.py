#!/usr/bin/env python3
"""Read-only, fail-closed capture of the accepted VM105 DSH pnpm topology."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import posixpath
import stat
import subprocess
import sys
import tempfile
import threading
import time


INSTALL_ROOT_TEXT = "/opt/deepseek-harness"
INSTALL_ROOT = Path(INSTALL_ROOT_TEXT)
START_PACKAGE = Path("node_modules/@deepseek-ai/dsh")
HEADLESS_NAME = "@deepseek-ai/dsh-headless"
HEADLESS_PATCH = "cordis.patch.yml"
ACCEPTED_MANIFEST_SHA256 = "4331e0e5fd9ac6f5e881a0dae941f9f07dea7b69969ee8b610071ce14cb03f8b"
ACCEPTED_MANIFEST_FILE_SHA256 = "54d117c638335edeefe43aaef0f181ea5317f7938a6861a145871a0d9e45e8dd"
ACCEPTED_BUILDER_SHA256 = "371481fe62d6611913f82f65b6e26b12512fda8a853a2f4591b6314f580c885f"
ACCEPTED_PACKAGE_COUNT = 447
ACCEPTED_MODULE_COUNT = 10_026
ACCEPTED_NODE = Path("/opt/node-v24.19.0-linux-x64/bin/node")
CAPTURE_TIMEOUT_SECONDS = 600
MAX_CAPTURE_STDOUT_BYTES = 8 * 1024 * 1024
MAX_CAPTURE_STDERR_BYTES = 64 * 1024
REMOTE_TARGET = "dsh@192.168.1.139"


class CaptureBlocked(RuntimeError):
    def __init__(self, reason: str, details: dict | None = None):
        super().__init__(reason)
        self.details = details or {}


def canonical_bytes(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _identity(info) -> tuple:
    return (info.st_dev, info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns,
            info.st_uid, info.st_gid)


def _link_identity(info) -> tuple:
    return (*_identity(info), info.st_ctime_ns)


def _identity_row(info) -> dict:
    return {"device": info.st_dev, "inode": info.st_ino, "mode": stat.S_IMODE(info.st_mode),
            "size": info.st_size, "mtimeNs": info.st_mtime_ns, "ctimeNs": info.st_ctime_ns,
            "uid": info.st_uid, "gid": info.st_gid,
            "rootOwned": info.st_uid == 0 and info.st_gid == 0}


def _within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError as error:
        raise CaptureBlocked("PATH_ESCAPE") from error


def _require_secure_real_path(path: Path, root: Path, kind: str) -> os.stat_result:
    current = root
    try:
        parts = path.relative_to(root).parts
        checks = [root]
        for part in parts:
            current /= part
            checks.append(current)
        for item in checks:
            info = item.lstat()
            if (stat.S_ISLNK(info.st_mode) or info.st_uid != 0 or info.st_gid != 0
                    or stat.S_IMODE(info.st_mode) & 0o022):
                raise CaptureBlocked("INSECURE_PATH")
        final = checks[-1].lstat()
    except OSError as error:
        raise CaptureBlocked("PATH_UNRESOLVED") from error
    if kind == "directory" and not stat.S_ISDIR(final.st_mode):
        raise CaptureBlocked("PATH_NOT_DIRECTORY")
    if kind == "file" and not stat.S_ISREG(final.st_mode):
        raise CaptureBlocked("PATH_NOT_REGULAR")
    return final


def _stable_file(path: Path, root: Path) -> tuple[bytes, os.stat_result]:
    before = _require_secure_real_path(path, root, "file")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, "rb") as handle:
            opened = os.fstat(handle.fileno())
            if _identity(before) != _identity(opened):
                raise CaptureBlocked("FILE_IDENTITY_DRIFT")
            value = handle.read()
            after_fd = os.fstat(handle.fileno())
        after_path = path.lstat()
    except OSError as error:
        raise CaptureBlocked("FILE_UNRESOLVED") from error
    if (_identity(before) != _identity(after_fd) or _identity(before) != _identity(after_path)
            or opened.st_ctime_ns != after_fd.st_ctime_ns or before.st_ctime_ns != after_path.st_ctime_ns):
        raise CaptureBlocked("FILE_IDENTITY_DRIFT")
    return value, before


def _package(path: Path, root: Path) -> tuple[dict, str, os.stat_result]:
    _require_secure_real_path(path, root, "directory")
    raw, info = _stable_file(path / "package.json", root)
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as error:
        raise CaptureBlocked("PACKAGE_MANIFEST_INVALID") from error
    if not isinstance(value, dict) or not isinstance(value.get("name"), str) or not isinstance(value.get("version"), str):
        raise CaptureBlocked("PACKAGE_IDENTITY_INVALID")
    return value, hashlib.sha256(raw).hexdigest(), info


def _link_snapshot(path: Path, root: Path) -> tuple[tuple, str, Path, os.stat_result]:
    _require_secure_real_path(path.parent, root, "directory")
    try:
        before = path.lstat()
        if not stat.S_ISLNK(before.st_mode) or before.st_uid != 0 or before.st_gid != 0:
            raise CaptureBlocked("DEPENDENCY_LINK_INSECURE")
        raw = os.readlink(path)
        if os.path.isabs(raw):
            raise CaptureBlocked("ABSOLUTE_LINK")
        resolved = path.resolve(strict=True)
        after = path.lstat()
    except CaptureBlocked:
        raise
    except OSError as error:
        raise CaptureBlocked("DEPENDENCY_LINK_UNRESOLVED") from error
    if _link_identity(before) != _link_identity(after):
        raise CaptureBlocked("LINK_IDENTITY_DRIFT")
    if not _within(resolved, root):
        raise CaptureBlocked("LINK_ESCAPE")
    return _link_identity(before), raw, resolved, before


def _dependency_link(package_root: Path, name: str) -> Path:
    virtual_node_modules = package_root.parent.parent if package_root.parent.name.startswith("@") else package_root.parent
    return virtual_node_modules / Path(*name.split("/"))


def _declared_dependencies(package: dict) -> tuple[dict, set[str]]:
    declared, optional = {}, set()
    for key in ("dependencies", "optionalDependencies", "peerDependencies"):
        value = package.get(key, {})
        if not isinstance(value, dict) or not all(isinstance(name, str) for name in value):
            raise CaptureBlocked("DEPENDENCY_DECLARATION_INVALID")
        declared.update(value)
        if key != "dependencies":
            optional.update(value)
    return declared, optional


def _validate_manifest(manifest: dict, root: Path, expected_sha: str, expected_count: int,
                       expected_modules: int | None = None) -> set[tuple[str, str, str]]:
    if not isinstance(manifest, dict) or manifest.get("status") != "PASS":
        raise CaptureBlocked("ACCEPTED_MANIFEST_INVALID")
    claimed = manifest.get("canonicalManifestSha256")
    unsigned = dict(manifest)
    unsigned.pop("canonicalManifestSha256", None)
    calculated = hashlib.sha256(canonical_bytes(unsigned)).hexdigest()
    if claimed != expected_sha or calculated != expected_sha:
        raise CaptureBlocked("ACCEPTED_MANIFEST_HASH_MISMATCH")
    packages = manifest.get("packages")
    if not isinstance(packages, list) or len(packages) != expected_count:
        raise CaptureBlocked("ACCEPTED_PACKAGE_COUNT_MISMATCH")
    if expected_modules is not None:
        modules = manifest.get("modules")
        if not isinstance(modules, list) or len(modules) != expected_modules:
            raise CaptureBlocked("ACCEPTED_MODULE_COUNT_MISMATCH")
    identities = set()
    for row in packages:
        try:
            name, version = row["name"], row["version"]
            canonical = Path(row["canonicalPath"])
        except (KeyError, TypeError) as error:
            raise CaptureBlocked("ACCEPTED_PACKAGE_IDENTITY_INVALID") from error
        if not isinstance(name, str) or not isinstance(version, str) or not canonical.is_absolute():
            raise CaptureBlocked("ACCEPTED_PACKAGE_IDENTITY_INVALID")
        identities.add((name, version, _relative(canonical, root)))
    if len(identities) != expected_count:
        raise CaptureBlocked("ACCEPTED_PACKAGE_IDENTITY_DUPLICATE")
    return identities


def _revalidate_fresh_manifest(builder_source: str, manifest: dict, expected_sha: str,
                               scan=None) -> None:
    if hashlib.sha256(builder_source.encode("utf-8")).hexdigest() != ACCEPTED_BUILDER_SHA256:
        raise CaptureBlocked("ACCEPTED_BUILDER_HASH_MISMATCH")
    namespace = {"__name__": "vm105_pinned_manifest_builder"}
    try:
        exec(compile(builder_source, "<pinned-vm105-manifest-builder>", "exec"), namespace)
        builder = namespace["build_manifest"]
        fresh = (scan or builder)(Path(INSTALL_ROOT / "node_modules"), ACCEPTED_NODE)
    except Exception:
        raise CaptureBlocked("FRESH_MANIFEST_RESCAN_FAILED") from None
    accepted = dict(manifest)
    accepted.pop("canonicalManifestSha256", None)
    if (not isinstance(fresh, dict)
            or hashlib.sha256(canonical_bytes(fresh)).hexdigest() != expected_sha
            or canonical_bytes(fresh) != canonical_bytes(accepted)):
        raise CaptureBlocked("FRESH_MANIFEST_MISMATCH")


def capture_topology(root: Path, manifest: dict, expected_sha: str,
                     expected_count: int, expected_modules: int | None = None) -> dict:
    root = Path(root)
    if not root.is_absolute():
        raise CaptureBlocked("CAPTURE_ROOT_ALIAS")
    try:
        resolved_root = root.resolve(strict=True)
    except OSError as error:
        raise CaptureBlocked("CAPTURE_ROOT_UNRESOLVED") from error
    if resolved_root != root:
        raise CaptureBlocked("CAPTURE_ROOT_ALIAS")
    _require_secure_real_path(root, root, "directory")
    expected = _validate_manifest(manifest, root, expected_sha, expected_count, expected_modules)
    queue = [(root / START_PACKAGE, "@deepseek-ai/dsh")]
    seen_packages, link_rows, link_checks, package_checks, packages = set(), [], {}, {}, {}
    while queue:
        logical, requested_name = queue.pop(0)
        logical_key = _relative(logical, root)
        identity, raw_target, canonical, link_info = _link_snapshot(logical, root)
        package, package_sha, package_json_info = _package(canonical, root)
        if package["name"] != requested_name:
            raise CaptureBlocked("DEPENDENCY_NAME_MISMATCH")
        row = {"logicalRelativePath": logical_key, "rawRelativeTarget": raw_target,
               "resolvedCanonicalPackagePath": _relative(canonical, root),
               "lstatIdentity": _identity_row(link_info), "packageName": package["name"],
               "packageVersion": package["version"], "packageJsonSha256": package_sha}
        previous = link_checks.get(logical_key)
        if previous is not None and previous[0] != identity:
            raise CaptureBlocked("LINK_IDENTITY_DRIFT")
        if previous is None:
            link_rows.append(row)
            link_checks[logical_key] = (identity, raw_target, canonical)
        package_key = (package["name"], package["version"], _relative(canonical, root))
        check = (_identity(package_json_info), package_sha)
        if canonical in package_checks and package_checks[canonical] != check:
            raise CaptureBlocked("PACKAGE_IDENTITY_DRIFT")
        package_checks[canonical] = check
        packages.setdefault(package_key, {"name": package["name"], "version": package["version"],
                                           "canonicalPackagePath": package_key[2],
                                           "packageJsonSha256": package_sha,
                                           "packageJsonIdentity": _identity_row(package_json_info),
                                           "firstLogicalPath": logical_key})
        if canonical in seen_packages:
            continue
        seen_packages.add(canonical)
        declared, optional = _declared_dependencies(package)
        for dependency in sorted(declared):
            link = _dependency_link(canonical, dependency)
            if not os.path.lexists(link):
                if dependency in optional:
                    continue
                raise CaptureBlocked("DEPENDENCY_MISSING")
            queue.append((link, dependency))
    actual = set(packages)
    if actual != expected:
        def rows(values):
            return [{"name": name, "version": version, "canonicalPackagePath": path}
                    for name, version, path in sorted(values)]
        raise CaptureBlocked("PACKAGE_CLOSURE_MISMATCH",
                             {"missingPackageIdentities": rows(expected - actual),
                              "extraPackageIdentities": rows(actual - expected)})
    for logical_key, original in link_checks.items():
        current = _link_snapshot(root / logical_key, root)
        if current[:3] != original:
            raise CaptureBlocked("LINK_IDENTITY_DRIFT")
    for canonical, original in package_checks.items():
        raw, info = _stable_file(canonical / "package.json", root)
        if (_identity(info), hashlib.sha256(raw).hexdigest()) != original:
            raise CaptureBlocked("PACKAGE_IDENTITY_DRIFT")
    headless = [row for key, row in packages.items() if key[0] == HEADLESS_NAME]
    if len(headless) != 1:
        raise CaptureBlocked("HEADLESS_PACKAGE_UNRESOLVED")
    canonical_headless = root / headless[0]["canonicalPackagePath"]
    patch_raw, patch_info = _stable_file(canonical_headless / HEADLESS_PATCH, root)
    logical_headless = root / headless[0]["firstLogicalPath"] / HEADLESS_PATCH
    patch = {"logicalRelativePath": _relative(logical_headless, root),
             "canonicalRelativePath": _relative(canonical_headless / HEADLESS_PATCH, root),
             "sha256": hashlib.sha256(patch_raw).hexdigest(), "lstatIdentity": _identity_row(patch_info)}
    link_rows.sort(key=lambda row: row["logicalRelativePath"])
    package_rows = sorted(packages.values(), key=lambda row: (row["name"], row["version"], row["canonicalPackagePath"]))
    return {"status": "PASS", "acceptedManifestCanonicalSha256": expected_sha,
            "acceptedPackageCount": expected_count, "startPackage": START_PACKAGE.as_posix(),
            "reachablePackageCount": len(package_rows), "dependencyLinkCount": len(link_rows),
            "packages": package_rows, "links": link_rows, "headlessPatch": patch}


def _signed_receipt(value: dict) -> dict:
    value = dict(value)
    value.pop("receiptSha256", None)
    value["receiptSha256"] = hashlib.sha256(canonical_bytes(value)).hexdigest()
    return value


def _exact_keys(value, keys, reason):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise CaptureBlocked(reason)


def _hex_digest(value, reason):
    if not isinstance(value, str) or len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise CaptureBlocked(reason)
    return value


def _relative_parts(value, reason):
    if not isinstance(value, str) or value.startswith("/") or "\\" in value or "\0" in value:
        raise CaptureBlocked(reason)
    parts = value.split("/")
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise CaptureBlocked(reason)
    return parts


def _absolute_parts(value, reason):
    if not isinstance(value, str) or not value.startswith("/") or "\\" in value or "\0" in value:
        raise CaptureBlocked(reason)
    parts = value.split("/")[1:]
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise CaptureBlocked(reason)
    return parts


def _resolved_relative_link(logical, raw):
    _relative_parts(logical, "TOPOLOGY_LINK_PATH_INVALID")
    if not isinstance(raw, str) or raw.startswith("/") or "\\" in raw or "\0" in raw:
        raise CaptureBlocked("TOPOLOGY_LINK_TARGET_INVALID")
    raw_parts = raw.split("/")
    if not raw_parts or any(part in {"", "."} for part in raw_parts):
        raise CaptureBlocked("TOPOLOGY_LINK_TARGET_INVALID")
    resolved = posixpath.normpath(posixpath.join(posixpath.dirname(logical), raw))
    if resolved == ".." or resolved.startswith("../") or resolved.startswith("/"):
        raise CaptureBlocked("TOPOLOGY_LINK_ESCAPE")
    _relative_parts(resolved, "TOPOLOGY_LINK_TARGET_INVALID")
    return resolved


def _valid_identity(value, reason, link=False):
    keys = {"device", "inode", "mode", "size", "mtimeNs", "ctimeNs", "uid", "gid", "rootOwned"}
    _exact_keys(value, keys, reason)
    if any(type(value[key]) is not int for key in keys - {"rootOwned"}) or type(value["rootOwned"]) is not bool:
        raise CaptureBlocked(reason)
    if value["uid"] != 0 or value["gid"] != 0 or value["rootOwned"] is not True:
        raise CaptureBlocked(reason)
    if not link and value["mode"] & 0o022:
        raise CaptureBlocked(reason)


def _validated_topology_receipt(manifest, receipt, accepted_receipt_sha):
    _hex_digest(accepted_receipt_sha, "TOPOLOGY_RECEIPT_PIN_INVALID")
    top_keys = {"status", "acceptedManifestCanonicalSha256", "acceptedPackageCount", "startPackage",
                "reachablePackageCount", "dependencyLinkCount", "packages", "links", "headlessPatch",
                "receiptSha256"}
    _exact_keys(receipt, top_keys, "TOPOLOGY_RECEIPT_SCHEMA_INVALID")
    unsigned = dict(receipt)
    claimed = unsigned.pop("receiptSha256")
    if (claimed != accepted_receipt_sha
            or hashlib.sha256(canonical_bytes(unsigned)).hexdigest() != accepted_receipt_sha):
        raise CaptureBlocked("TOPOLOGY_RECEIPT_HASH_MISMATCH")
    expected_identities = _validate_manifest(manifest, INSTALL_ROOT, ACCEPTED_MANIFEST_SHA256,
                                             ACCEPTED_PACKAGE_COUNT, ACCEPTED_MODULE_COUNT)
    if (receipt["status"] != "PASS" or receipt["acceptedManifestCanonicalSha256"] != ACCEPTED_MANIFEST_SHA256
            or receipt["acceptedPackageCount"] != ACCEPTED_PACKAGE_COUNT
            or receipt["reachablePackageCount"] != ACCEPTED_PACKAGE_COUNT
            or receipt["startPackage"] != START_PACKAGE.as_posix()
            or type(receipt["dependencyLinkCount"]) is not int
            or receipt["dependencyLinkCount"] != len(receipt["links"])
            or not isinstance(receipt["packages"], list) or len(receipt["packages"]) != ACCEPTED_PACKAGE_COUNT):
        raise CaptureBlocked("TOPOLOGY_RECEIPT_CONTRACT_MISMATCH")

    packages = {}
    for row in receipt["packages"]:
        _exact_keys(row, {"name", "version", "canonicalPackagePath", "packageJsonSha256",
                          "packageJsonIdentity", "firstLogicalPath"}, "TOPOLOGY_PACKAGE_SCHEMA_INVALID")
        if not isinstance(row["name"], str) or not isinstance(row["version"], str):
            raise CaptureBlocked("TOPOLOGY_PACKAGE_SCHEMA_INVALID")
        canonical = row["canonicalPackagePath"]
        logical = row["firstLogicalPath"]
        _relative_parts(canonical, "TOPOLOGY_PACKAGE_PATH_INVALID")
        _relative_parts(logical, "TOPOLOGY_PACKAGE_PATH_INVALID")
        if not canonical.startswith("node_modules/") or not logical.startswith("node_modules/"):
            raise CaptureBlocked("TOPOLOGY_PACKAGE_PATH_INVALID")
        _hex_digest(row["packageJsonSha256"], "TOPOLOGY_PACKAGE_HASH_INVALID")
        _valid_identity(row["packageJsonIdentity"], "TOPOLOGY_PACKAGE_IDENTITY_INVALID")
        key = (row["name"], row["version"], canonical)
        if key in packages:
            raise CaptureBlocked("TOPOLOGY_PACKAGE_DUPLICATE")
        packages[key] = row
    if set(packages) != expected_identities:
        raise CaptureBlocked("TOPOLOGY_PACKAGE_SET_MISMATCH")

    links = {}
    for row in receipt["links"]:
        _exact_keys(row, {"logicalRelativePath", "rawRelativeTarget", "resolvedCanonicalPackagePath",
                          "lstatIdentity", "packageName", "packageVersion", "packageJsonSha256"},
                    "TOPOLOGY_LINK_SCHEMA_INVALID")
        logical, raw, resolved = row["logicalRelativePath"], row["rawRelativeTarget"], row["resolvedCanonicalPackagePath"]
        if _resolved_relative_link(logical, raw) != resolved or not resolved.startswith("node_modules/"):
            raise CaptureBlocked("TOPOLOGY_LINK_RESOLUTION_MISMATCH")
        _valid_identity(row["lstatIdentity"], "TOPOLOGY_LINK_IDENTITY_INVALID", link=True)
        _hex_digest(row["packageJsonSha256"], "TOPOLOGY_LINK_PACKAGE_HASH_INVALID")
        package_key = (row["packageName"], row["packageVersion"], resolved)
        if package_key not in packages or packages[package_key]["packageJsonSha256"] != row["packageJsonSha256"]:
            raise CaptureBlocked("TOPOLOGY_LINK_PACKAGE_MISMATCH")
        if logical in links:
            raise CaptureBlocked("TOPOLOGY_LINK_DUPLICATE")
        links[logical] = (raw, resolved)
    if START_PACKAGE.as_posix() not in links:
        raise CaptureBlocked("TOPOLOGY_START_LINK_MISSING")
    if set(row["firstLogicalPath"] for row in packages.values()) - set(links):
        raise CaptureBlocked("TOPOLOGY_PACKAGE_LINK_MISSING")

    patch = receipt["headlessPatch"]
    _exact_keys(patch, {"logicalRelativePath", "canonicalRelativePath", "sha256", "lstatIdentity"},
                "TOPOLOGY_HEADLESS_PATCH_SCHEMA_INVALID")
    headless = [row for row in packages.values() if row["name"] == HEADLESS_NAME]
    if len(headless) != 1:
        raise CaptureBlocked("TOPOLOGY_HEADLESS_PACKAGE_INVALID")
    if (patch["logicalRelativePath"] != headless[0]["firstLogicalPath"] + "/" + HEADLESS_PATCH
            or patch["canonicalRelativePath"] != headless[0]["canonicalPackagePath"] + "/" + HEADLESS_PATCH):
        raise CaptureBlocked("TOPOLOGY_HEADLESS_PATCH_PATH_INVALID")
    _hex_digest(patch["sha256"], "TOPOLOGY_HEADLESS_PATCH_HASH_INVALID")
    _valid_identity(patch["lstatIdentity"], "TOPOLOGY_HEADLESS_PATCH_IDENTITY_INVALID")
    return links, patch


def _builder_helper(builder, name):
    value = builder.get(name) if isinstance(builder, dict) else getattr(builder, name, None)
    if not callable(value):
        raise CaptureBlocked("TOPOLOGY_BUILDER_INVALID")
    return value


def _physical_destination(source):
    parts = _absolute_parts(source, "TOPOLOGY_SOURCE_PATH_INVALID")
    prefix = ["opt", "deepseek-harness", "node_modules"]
    if parts[:len(prefix)] != prefix or len(parts) == len(prefix):
        raise CaptureBlocked("TOPOLOGY_SOURCE_PATH_INVALID")
    return "/".join(["node_modules", *parts[len(prefix):]])


def _topology_file_rows(manifest, patch):
    rows = []
    for row in manifest.get("modules", []):
        _exact_keys(row, {"sourceLogicalPath", "sourceCanonicalPath", "stagedRelativePath", "sha256"},
                    "TOPOLOGY_MODULE_SCHEMA_INVALID")
        rows.append((row["sourceCanonicalPath"], _physical_destination(row["sourceCanonicalPath"]),
                     _hex_digest(row["sha256"], "TOPOLOGY_FILE_HASH_INVALID"), 0o600))
    for row in manifest.get("configBundles", []):
        _exact_keys(row, {"logicalPath", "canonicalPath", "sha256"}, "TOPOLOGY_CONFIG_SCHEMA_INVALID")
        rows.append((row["canonicalPath"], _physical_destination(row["canonicalPath"]),
                     _hex_digest(row["sha256"], "TOPOLOGY_FILE_HASH_INVALID"), 0o600))
    patch_source = INSTALL_ROOT_TEXT + "/" + patch["canonicalRelativePath"]
    rows.append((patch_source, patch["canonicalRelativePath"], patch["sha256"], 0o600))
    runtime = manifest.get("runtime")
    if not isinstance(runtime, dict) or set(runtime) != {"node", "dependencies"} or not isinstance(runtime["dependencies"], list):
        raise CaptureBlocked("TOPOLOGY_RUNTIME_SCHEMA_INVALID")
    for index, row in enumerate([runtime["node"], *runtime["dependencies"]]):
        _exact_keys(row, {"logicalPath", "canonicalPath", "sha256"}, "TOPOLOGY_RUNTIME_SCHEMA_INVALID")
        logical = "/".join(_absolute_parts(row["logicalPath"], "TOPOLOGY_RUNTIME_PATH_INVALID"))
        _absolute_parts(row["canonicalPath"], "TOPOLOGY_RUNTIME_PATH_INVALID")
        rows.append((row["canonicalPath"], "runtime/" + logical,
                     _hex_digest(row["sha256"], "TOPOLOGY_FILE_HASH_INVALID"), 0o500 if index == 0 else 0o600))
    destinations = set()
    for source, destination, _digest, _mode in rows:
        _absolute_parts(source, "TOPOLOGY_SOURCE_PATH_INVALID")
        _relative_parts(destination, "TOPOLOGY_DESTINATION_PATH_INVALID")
        if destination in destinations:
            raise CaptureBlocked("TOPOLOGY_PATH_COLLISION")
        destinations.add(destination)
    return rows


def _create_link_at(builder, staging_root_fd, logical, raw):
    parts = _relative_parts(logical, "TOPOLOGY_LINK_PATH_INVALID")
    parent = _builder_helper(builder, "_directory_at")(staging_root_fd, parts[:-1], create=True)
    try:
        os.symlink(raw, parts[-1], dir_fd=parent)
    except OSError as error:
        raise CaptureBlocked("TOPOLOGY_LINK_CREATE_FAILED") from error
    finally:
        os.close(parent)


def _copy_topology_file(builder, source_root_fd, staging_root_fd, row):
    source, destination, expected_hash, mode = row
    source_fd = destination_fd = None
    try:
        source_fd = _builder_helper(builder, "_open_source_at")(source_root_fd, source)
        before = os.fstat(source_fd)
        identity = (before.st_dev, before.st_ino, before.st_mode, before.st_size,
                    before.st_mtime_ns, before.st_ctime_ns)
        if _builder_helper(builder, "_hash_fd")(source_fd) != expected_hash:
            raise CaptureBlocked("TOPOLOGY_SOURCE_HASH_MISMATCH")
        destination_fd = _builder_helper(builder, "_create_destination_at")(staging_root_fd, destination)
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
            raise CaptureBlocked("TOPOLOGY_SOURCE_IDENTITY_DRIFT")
        if _builder_helper(builder, "_hash_fd")(destination_fd) != expected_hash:
            raise CaptureBlocked("TOPOLOGY_STAGED_HASH_MISMATCH")
    except CaptureBlocked:
        raise
    except OSError as error:
        raise CaptureBlocked("TOPOLOGY_COPY_FAILED") from error
    finally:
        if destination_fd is not None:
            os.close(destination_fd)
        if source_fd is not None:
            os.close(source_fd)


def _inventory_topology(builder, staging_root_fd):
    files, links, directories = {}, {}, {}

    def visit(directory_fd, prefix):
        for name in os.listdir(directory_fd):
            relative = "/".join((*prefix, name))
            before = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
            if stat.S_ISDIR(before.st_mode):
                child = _builder_helper(builder, "_directory_at")(directory_fd, [name])
                try:
                    opened = os.fstat(child)
                    if _link_identity(before) != _link_identity(opened) or before.st_uid != 0 or before.st_gid != 0:
                        raise CaptureBlocked("TOPOLOGY_STAGED_DIRECTORY_INVALID")
                    visit(child, (*prefix, name))
                finally:
                    os.close(child)
                after = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
                if _link_identity(before) != _link_identity(after):
                    raise CaptureBlocked("TOPOLOGY_STAGED_IDENTITY_DRIFT")
                directories[relative] = {"path": relative, "mode": stat.S_IMODE(before.st_mode),
                                         "uid": before.st_uid, "gid": before.st_gid,
                                         "identity": _identity_row(before)}
            elif stat.S_ISREG(before.st_mode):
                descriptor = _builder_helper(builder, "_open_staged_at")(staging_root_fd, relative)
                try:
                    opened = os.fstat(descriptor)
                    digest = _builder_helper(builder, "_hash_fd")(descriptor)
                    after_fd = os.fstat(descriptor)
                finally:
                    os.close(descriptor)
                after_path = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
                if (_identity(before) != _identity(opened) or _identity(opened) != _identity(after_fd)
                        or _identity(before) != _identity(after_path)
                        or opened.st_ctime_ns != after_fd.st_ctime_ns or before.st_ctime_ns != after_path.st_ctime_ns):
                    raise CaptureBlocked("TOPOLOGY_STAGED_IDENTITY_DRIFT")
                if before.st_uid != 0 or before.st_gid != 0:
                    raise CaptureBlocked("TOPOLOGY_STAGED_FILE_INVALID")
                files[relative] = {"path": relative, "sha256": digest, "mode": stat.S_IMODE(before.st_mode),
                                   "uid": before.st_uid, "gid": before.st_gid,
                                   "identity": _identity_row(before)}
            elif stat.S_ISLNK(before.st_mode):
                raw = os.readlink(name, dir_fd=directory_fd)
                after = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
                if _link_identity(before) != _link_identity(after) or before.st_uid != 0 or before.st_gid != 0:
                    raise CaptureBlocked("TOPOLOGY_STAGED_LINK_INVALID")
                resolved = _resolved_relative_link(relative, raw)
                target = _builder_helper(builder, "_directory_at")(staging_root_fd, resolved.split("/"))
                os.close(target)
                links[relative] = {"path": relative, "rawRelativeTarget": raw,
                                   "resolvedCanonicalPackagePath": resolved,
                                   "uid": before.st_uid, "gid": before.st_gid,
                                   "identity": _identity_row(before)}
            else:
                raise CaptureBlocked("TOPOLOGY_STAGED_ARTIFACT_INVALID")

    visit(staging_root_fd, ())
    return {"files": [files[path] for path in sorted(files)],
            "links": [links[path] for path in sorted(links)],
            "directories": [directories[path] for path in sorted(directories)]}


def stage_verified_topology(manifest, topology_receipt, accepted_receipt_sha,
                            source_root_fd, staging_root_fd, builder):
    """Rebuild the accepted physical pnpm tree using held Linux directory descriptors."""
    try:
        _builder_helper(builder, "_require_descriptor_platform")()
        _builder_helper(builder, "_require_empty_staging")(staging_root_fd)
        links, patch = _validated_topology_receipt(manifest, topology_receipt, accepted_receipt_sha)
        rows = _topology_file_rows(manifest, patch)
        files = {row[1]: (row[2], row[3]) for row in rows}
        if set(files) & set(links):
            raise CaptureBlocked("TOPOLOGY_PATH_COLLISION")
        all_paths = set(files) | set(links)
        for path in all_paths:
            parts = path.split("/")
            if any("/".join(parts[:index]) in all_paths for index in range(1, len(parts))):
                raise CaptureBlocked("TOPOLOGY_PATH_COLLISION")
        expected_dirs = {"/".join(parts[:index]) for path in all_paths
                         for parts in [path.split("/")] for index in range(1, len(parts))}
        for _raw, resolved in links.values():
            if resolved not in expected_dirs:
                raise CaptureBlocked("TOPOLOGY_LINK_TARGET_MISSING")
        for row in rows:
            _copy_topology_file(builder, source_root_fd, staging_root_fd, row)
        for logical, (raw, _resolved) in sorted(links.items()):
            _create_link_at(builder, staging_root_fd, logical, raw)
        first = _inventory_topology(builder, staging_root_fd)
        second = _inventory_topology(builder, staging_root_fd)
        if first != second:
            raise CaptureBlocked("TOPOLOGY_STAGED_INVENTORY_DRIFT")
        actual_files = {row["path"]: (row["sha256"], row["mode"]) for row in first["files"]}
        actual_links = {row["path"]: (row["rawRelativeTarget"], row["resolvedCanonicalPackagePath"])
                        for row in first["links"]}
        actual_dirs = {row["path"]: (row["mode"], row["uid"], row["gid"])
                       for row in first["directories"]}
        if (actual_files != files or actual_links != links or set(actual_dirs) != expected_dirs
                or any(value != (0o700, 0, 0) for value in actual_dirs.values())
                or any(row["uid"] != 0 or row["gid"] != 0 for row in first["files"] + first["links"])):
            raise CaptureBlocked("TOPOLOGY_STAGED_TREE_MISMATCH")
        return {"status": "PASS", "canonicalManifestSha256": ACCEPTED_MANIFEST_SHA256,
                "topologyReceiptSha256": accepted_receipt_sha, "fileCount": len(files),
                "linkCount": len(links), "directoryCount": len(expected_dirs),
                "files": first["files"], "links": first["links"], "directories": first["directories"]}
    except CaptureBlocked:
        raise
    except Exception:
        raise CaptureBlocked("TOPOLOGY_STAGING_FAILED") from None


def capture_payload(payload: dict) -> dict:
    try:
        if not isinstance(payload, dict) or payload.get("installRoot") != str(INSTALL_ROOT):
            raise CaptureBlocked("CAPTURE_TARGET_MISMATCH")
        builder = payload.get("builderSource")
        if not isinstance(builder, str):
            raise CaptureBlocked("ACCEPTED_BUILDER_HASH_MISMATCH")
        _validate_manifest(payload.get("acceptedManifest"), INSTALL_ROOT, ACCEPTED_MANIFEST_SHA256,
                           ACCEPTED_PACKAGE_COUNT, ACCEPTED_MODULE_COUNT)
        _revalidate_fresh_manifest(builder, payload["acceptedManifest"], ACCEPTED_MANIFEST_SHA256)
        value = capture_topology(INSTALL_ROOT, payload.get("acceptedManifest"), ACCEPTED_MANIFEST_SHA256,
                                 ACCEPTED_PACKAGE_COUNT, ACCEPTED_MODULE_COUNT)
    except (CaptureBlocked, OSError) as error:
        value = {"status": "BLOCKED", "reasons": [str(error) if isinstance(error, CaptureBlocked)
                                                     else "CAPTURE_IO_FAILURE"]}
        if isinstance(error, CaptureBlocked) and error.details:
            value["details"] = error.details
    return _signed_receipt(value)


def remote_entry(payload: dict) -> None:
    sys.stdout.write(canonical_bytes(capture_payload(payload)).decode("utf-8") + "\n")


def _read_pinned_file(path: Path, expected_sha256: str, reason: str) -> bytes:
    _hex_digest(expected_sha256, reason)
    descriptor = None
    try:
        before = path.lstat()
        if not stat.S_ISREG(before.st_mode):
            raise CaptureBlocked(reason)
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0))
        opened = os.fstat(descriptor)
        chunks = []
        while True:
            chunk = os.read(descriptor, 65536)
            if not chunk:
                break
            chunks.append(chunk)
        after_fd = os.fstat(descriptor)
        after_path = path.lstat()
    except CaptureBlocked:
        raise
    except OSError:
        raise CaptureBlocked(reason) from None
    finally:
        if descriptor is not None:
            os.close(descriptor)
    value = b"".join(chunks)
    if (_identity(before) != _identity(opened) or _identity(opened) != _identity(after_fd)
            or _identity(before) != _identity(after_path)
            or hashlib.sha256(value).hexdigest() != expected_sha256):
        raise CaptureBlocked(reason)
    return value


def _transport_payload(source: bytes, expected_source_sha256: str,
                       manifest: dict, builder: bytes) -> bytes:
    if hashlib.sha256(source).hexdigest() != _hex_digest(
            expected_source_sha256, "CAPTURE_SOURCE_HASH_MISMATCH"):
        raise CaptureBlocked("CAPTURE_SOURCE_HASH_MISMATCH")
    try:
        value = {"source": source.decode("utf-8"),
                 "captureSourceSha256": expected_source_sha256,
                 "installRoot": str(INSTALL_ROOT),
                 "acceptedManifest": manifest,
                 "builderSource": builder.decode("utf-8")}
    except UnicodeDecodeError:
        raise CaptureBlocked("CAPTURE_INPUT_INVALID") from None
    return canonical_bytes(value) + b"\n"


def _remote_command() -> str:
    bootstrap = (
        'import hashlib,json,sys;p=json.load(sys.stdin);s=p.pop("source");'
        'h=p.pop("captureSourceSha256");b=s.encode("utf-8");'
        'hashlib.sha256(b).hexdigest()==h or (_ for _ in ()).throw(SystemExit(74));'
        'n={"__name__":"vm105_topology_capture"};'
        'exec(compile(s,"<vm105-topology-capture>","exec"),n);n["remote_entry"](p)'
    )
    encoded = base64.b64encode(bootstrap.encode("utf-8")).decode("ascii")
    return ("/usr/bin/env -i PATH=/usr/bin:/bin /usr/bin/python3.12 -I -c "
            f"'import base64;exec(base64.b64decode(\"{encoded}\"))'")


def _run_bounded(command: list[str], payload: bytes, timeout_seconds: float,
                 max_stdout: int, max_stderr: int) -> bytes:
    deadline = time.monotonic() + timeout_seconds
    try:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, bufsize=0)
    except OSError:
        raise CaptureBlocked("CAPTURE_TRANSPORT_FAILED") from None
    output = {"stdout": bytearray(), "stderr": bytearray()}
    overflow = []
    write_failed = []

    def drain(name, stream, limit):
        try:
            for chunk in iter(lambda: stream.read(65536), b""):
                if len(output[name]) + len(chunk) > limit:
                    overflow.append(f"CAPTURE_{name.upper()}_LIMIT_EXCEEDED")
                    process.kill()
                    return
                output[name].extend(chunk)
        except OSError:
            pass

    def feed():
        try:
            remaining = memoryview(payload)
            while remaining:
                written = process.stdin.write(remaining)
                if not written:
                    raise BrokenPipeError
                remaining = remaining[written:]
            process.stdin.flush()
        except OSError:
            write_failed.append(True)
        finally:
            try:
                process.stdin.close()
            except OSError:
                pass

    threads = [threading.Thread(target=feed, daemon=True),
               threading.Thread(target=drain, args=("stdout", process.stdout, max_stdout), daemon=True),
               threading.Thread(target=drain, args=("stderr", process.stderr, max_stderr), daemon=True)]
    for thread in threads:
        thread.start()
    timed_out = False
    try:
        return_code = process.wait(timeout=max(0.001, deadline - time.monotonic()))
    except subprocess.TimeoutExpired:
        timed_out = True
        process.kill()
        return_code = None
    for thread in threads:
        thread.join(max(0, deadline - time.monotonic()))
    for stream in (process.stdin, process.stdout, process.stderr):
        try:
            stream.close()
        except OSError:
            pass
    if timed_out or any(thread.is_alive() for thread in threads):
        process.kill()
        raise CaptureBlocked("CAPTURE_TIMEOUT")
    if overflow:
        raise CaptureBlocked(overflow[0])
    if write_failed or return_code != 0:
        raise CaptureBlocked("CAPTURE_TRANSPORT_FAILED")
    return bytes(output["stdout"])


def _validated_capture_stdout(raw: bytes, manifest: dict) -> bytes:
    if not raw.endswith(b"\n") or b"\n" in raw[:-1]:
        raise CaptureBlocked("CAPTURE_RECEIPT_FRAMING_INVALID")
    try:
        receipt = json.loads(raw[:-1].decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise CaptureBlocked("CAPTURE_RECEIPT_JSON_INVALID") from None
    if not isinstance(receipt, dict) or canonical_bytes(receipt) + b"\n" != raw:
        raise CaptureBlocked("CAPTURE_RECEIPT_CANONICAL_INVALID")
    claimed = receipt.get("receiptSha256")
    _hex_digest(claimed, "CAPTURE_RECEIPT_HASH_INVALID")
    unsigned = dict(receipt)
    unsigned.pop("receiptSha256")
    if hashlib.sha256(canonical_bytes(unsigned)).hexdigest() != claimed:
        raise CaptureBlocked("CAPTURE_RECEIPT_HASH_INVALID")
    if receipt.get("status") == "PASS":
        _validated_topology_receipt(manifest, receipt, claimed)
    elif receipt.get("status") == "BLOCKED":
        keys = {"status", "reasons", "receiptSha256"}
        if "details" in receipt:
            keys.add("details")
        _exact_keys(receipt, keys, "CAPTURE_RECEIPT_SCHEMA_INVALID")
        if (not isinstance(receipt["reasons"], list) or not receipt["reasons"]
                or not all(isinstance(reason, str) and reason for reason in receipt["reasons"])
                or ("details" in receipt and not isinstance(receipt["details"], dict))):
            raise CaptureBlocked("CAPTURE_RECEIPT_SCHEMA_INVALID")
    else:
        raise CaptureBlocked("CAPTURE_RECEIPT_SCHEMA_INVALID")
    return canonical_bytes(receipt) + b"\n"


def _publish_fresh(path: Path, value: bytes) -> None:
    temporary = None
    descriptor = None
    try:
        descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
        if hasattr(os, "fchmod"):
            os.fchmod(descriptor, 0o600)
        else:
            os.chmod(temporary, 0o600)
        with os.fdopen(descriptor, "wb", closefd=True) as handle:
            descriptor = None
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path, follow_symlinks=False)
    except FileExistsError:
        raise CaptureBlocked("CAPTURE_EVIDENCE_EXISTS") from None
    except OSError:
        raise CaptureBlocked("CAPTURE_EVIDENCE_PUBLISH_FAILED") from None
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temporary is not None:
            try:
                os.unlink(temporary)
            except OSError:
                pass


def capture_via_ssh(source: bytes, expected_source_sha256: str, manifest_path: Path,
                    builder_path: Path, evidence_path: Path, ssh_exe: Path,
                    identity_path: Path) -> dict:
    if hashlib.sha256(source).hexdigest() != _hex_digest(
            expected_source_sha256, "CAPTURE_SOURCE_HASH_MISMATCH"):
        raise CaptureBlocked("CAPTURE_SOURCE_HASH_MISMATCH")
    manifest_raw = _read_pinned_file(manifest_path, ACCEPTED_MANIFEST_FILE_SHA256,
                                     "ACCEPTED_MANIFEST_FILE_HASH_MISMATCH")
    builder = _read_pinned_file(builder_path, ACCEPTED_BUILDER_SHA256,
                                "ACCEPTED_BUILDER_HASH_MISMATCH")
    try:
        manifest = json.loads(manifest_raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise CaptureBlocked("ACCEPTED_MANIFEST_INVALID") from None
    _validate_manifest(manifest, INSTALL_ROOT, ACCEPTED_MANIFEST_SHA256,
                       ACCEPTED_PACKAGE_COUNT, ACCEPTED_MODULE_COUNT)
    payload = _transport_payload(source, expected_source_sha256, manifest, builder)
    command = [str(ssh_exe), "-T", "-i", str(identity_path), "-o", "BatchMode=yes",
               "-o", "IdentitiesOnly=yes", "-o", "StrictHostKeyChecking=yes",
               "-o", "ConnectTimeout=10", REMOTE_TARGET, _remote_command()]
    raw = _run_bounded(command, payload, CAPTURE_TIMEOUT_SECONDS,
                       MAX_CAPTURE_STDOUT_BYTES, MAX_CAPTURE_STDERR_BYTES)
    validated = _validated_capture_stdout(raw, manifest)
    _publish_fresh(evidence_path, validated)
    return json.loads(validated)


def coordinator_entry(payload: dict, source: bytes) -> int:
    try:
        _exact_keys(payload, {"expectedCaptureSourceSha256", "acceptedManifestPath", "builderPath",
                              "evidencePath", "sshExe", "identityPath"}, "CAPTURE_ARGUMENT_INVALID")
        value = capture_via_ssh(source, payload["expectedCaptureSourceSha256"],
                                Path(payload["acceptedManifestPath"]), Path(payload["builderPath"]),
                                Path(payload["evidencePath"]), Path(payload["sshExe"]),
                                Path(payload["identityPath"]))
    except (CaptureBlocked, TypeError):
        sys.stderr.write("CAPTURE_COORDINATOR_BLOCKED\n")
        return 1
    sys.stdout.write(canonical_bytes(value).decode("utf-8") + "\n")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--accepted-manifest", type=Path, required=True)
    parser.add_argument("--builder", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        payload = {"installRoot": str(INSTALL_ROOT),
                   "acceptedManifest": json.loads(args.accepted_manifest.read_text(encoding="utf-8")),
                   "builderSource": args.builder.read_text(encoding="utf-8")}
        value = capture_payload(payload)
    except (OSError, ValueError):
        value = _signed_receipt({"status": "BLOCKED", "reasons": ["CAPTURE_INPUT_INVALID"]})
    sys.stdout.write(canonical_bytes(value).decode("utf-8") + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
