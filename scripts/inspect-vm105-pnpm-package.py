#!/usr/bin/env python3
"""Read only named source files in the single verified VM105 pnpm package."""
import argparse
import hashlib
import json
import os
import posixpath
import stat
import sys

PACKAGE = "/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh@0.1.1-rc.2_7adf779e9bedfb2e97ced92905792931/node_modules/@deepseek-ai/dsh"
LOGICAL = "/opt/deepseek-harness/node_modules/@deepseek-ai/dsh"
DEPENDENCIES = {
    "dsh-home-paths": "/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-home-paths@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai+dsh-invar_260f8dde1d5adbe84fd51b779f4f83da/node_modules/@deepseek-ai/dsh-home-paths",
    "dsh-app-boot": "/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-app-boot@0.1.1-rc.2_d7ed335ddbfb7670edc51bd2c8928580/node_modules/@deepseek-ai/dsh-app-boot",
}
FORBIDDEN = {"system.posix_acl_access", "system.posix_acl_default", "security.capability"}
LIMIT = 1024 * 1024


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def relative(value):
    require(value and not value.startswith("/") and "\\" not in value and ":" not in value,
            "invalid relative path")
    require(all(part not in ("", ".", "..") for part in value.split("/")) and "\0" not in value,
            "invalid relative path")
    return value


def snapshot(s):
    return (s.st_dev, s.st_ino, s.st_mode, s.st_uid, s.st_gid, s.st_nlink,
            s.st_size, s.st_mtime_ns, s.st_ctime_ns)


class Inspection:
    def __init__(self):
        self.held = []

    def close(self):
        for fd, _, _, _, _ in reversed(self.held):
            os.close(fd)

    def open(self, path, file=False):
        parent = None
        parts = ["/"] + path.strip("/").split("/")
        for i, part in enumerate(parts):
            final = file and i == len(parts) - 1
            fd = os.open(part, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW |
                         (os.O_NONBLOCK if final else os.O_DIRECTORY), dir_fd=parent)
            s = os.fstat(fd)
            self.held.append((fd, parent, part, snapshot(s), final))
            self.check(self.held[-1])
            parent = fd
        return parent

    def check(self, item):
        fd, parent, name, before, file = item
        s = os.fstat(fd)
        require(snapshot(s) == before, "held object metadata drift")
        require(s.st_uid == 0 and s.st_gid == 0 and not s.st_mode & 0o022, "untrusted owner or mode")
        require(stat.S_ISREG(s.st_mode) if file else stat.S_ISDIR(s.st_mode), "unexpected object type")
        require(not file or s.st_nlink >= 1, "unlinked source file")
        require(not FORBIDDEN.intersection(os.listxattr(fd)), "ACL or capability present")
        require(snapshot(os.stat(name, dir_fd=parent, follow_symlinks=False)) == before, "path identity drift")

    def verify(self):
        for item in self.held:
            self.check(item)

    def read(self, path):
        fd = self.open(path, file=True)
        require(os.fstat(fd).st_size <= LIMIT, "source exceeds 1 MiB")
        chunks, size = [], 0
        while chunk := os.read(fd, min(65536, LIMIT + 1 - size)):
            chunks.append(chunk)
            size += len(chunk)
            require(size <= LIMIT, "source exceeds 1 MiB")
        data = b"".join(chunks)
        first = hashlib.sha256(data).hexdigest()
        self.verify()
        os.lseek(fd, 0, os.SEEK_SET)
        h = hashlib.sha256()
        size = 0
        while chunk := os.read(fd, 65536):
            size += len(chunk)
            require(size <= LIMIT, "source grew beyond 1 MiB")
            h.update(chunk)
        require(h.hexdigest() == first, "source digest drift")
        self.verify()
        s = os.fstat(fd)
        return data.decode("utf-8"), {"path": path, "sha256": first, "links": s.st_nlink,
                                    "device": s.st_dev, "inode": s.st_ino}


def exported_entry(manifest):
    value = manifest.get("exports", manifest.get("main"))
    if isinstance(value, dict) and "." in value:
        value = value["."]
    while isinstance(value, dict):
        value = next((target for key, target in value.items() if key in ("node", "import", "default")), None)
    require(isinstance(value, str), "unsupported dependency entry declaration")
    return relative(value[2:] if value.startswith("./") else value)


def dependency_target(name, path):
    return path == DEPENDENCIES[name]


def inspect(extra=None, start_line=1, dependency=None):
    if extra is not None:
        relative(extra)
    require(start_line >= 1, "start line must be positive")
    check = Inspection()
    try:
        def pin_link(logical, expected):
            parent = check.open(posixpath.dirname(logical))
            name = posixpath.basename(logical)

            def state():
                s = os.stat(name, dir_fd=parent, follow_symlinks=False)
                require(stat.S_ISLNK(s.st_mode) and (s.st_uid, s.st_gid) == (0, 0), "untrusted package symlink")
                target = os.readlink(name, dir_fd=parent)
                canonical = posixpath.normpath(posixpath.join(posixpath.dirname(logical), target))
                require(expected(canonical), "unexpected canonical package target")
                return snapshot(s), target, canonical

            before = state()
            return state, before

        link_state, link_before = pin_link(LOGICAL, lambda path: path == PACKAGE)
        manifest, metadata = check.read(PACKAGE + "/package.json")
        parsed = json.loads(manifest)
        require(parsed.get("name") == "@deepseek-ai/dsh" and parsed.get("version") == "0.1.1-rc.2",
                "unexpected package identity")
        original_manifest = metadata.copy()
        canonical, logical = PACKAGE, LOGICAL
        dependency_state = None
        entry = "lib/bin.js"
        if dependency is not None:
            require(dependency in ("dsh-home-paths", "dsh-app-boot"), "unsupported dependency")
            name = "@deepseek-ai/" + dependency
            require(parsed.get("dependencies", {}).get(name) == "^0.1.1-rc.2", "unexpected dependency declaration")
            logical = posixpath.dirname(PACKAGE) + "/" + dependency
            dependency_state, dependency_before = pin_link(logical, lambda path: dependency_target(dependency, path))
            canonical = dependency_before[2]
            manifest, metadata = check.read(canonical + "/package.json")
            parsed = json.loads(manifest)
            require(parsed.get("name") == name and parsed.get("version") == "0.1.1-rc.2", "unexpected dependency identity")
            entry = exported_entry(parsed)
        files = [(manifest, metadata)]
        chosen = extra or entry
        if chosen != "package.json":
            files.append(check.read(canonical + "/" + chosen))
        check.verify()
        require(link_state() == link_before, "logical package link drift")
        if dependency_state:
            require(dependency_state() == dependency_before, "dependency package link drift")
        budget, output = 12000, []
        for source, info in files:
            lines = source.splitlines()
            excerpt = "\n".join(f"{i + 1}: {line}" for i, line in enumerate(lines) if i + 1 >= start_line)
            info.update({"source": excerpt[:budget], "truncated": len(excerpt) > budget,
                         "start_line": start_line, "total_lines": len(lines)})
            budget -= len(info["source"])
            output.append(info)
        return {"status": "PASS", "name": parsed["name"], "version": parsed["version"],
                "logical": logical, "canonical": canonical,
                "link_target": dependency_before[1] if dependency_state else link_before[1],
                "original_manifest": original_manifest, "declared_entry": entry, "files": output}
    finally:
        check.close()


def self_test():
    """Small rejection check: path grammar and held-fd trust checks, no filesystem writes."""
    from types import SimpleNamespace
    from unittest.mock import patch
    for value in ("../x", "/x", "lib/../x", "lib//x", "lib\\x", "", "lib/./x", "x\0y"):
        try:
            relative(value)
        except RuntimeError:
            pass
        else:
            raise RuntimeError("invalid path accepted")
    require(relative("lib/bin.js") == "lib/bin.js", "valid path rejected")
    for name, target in DEPENDENCIES.items():
        require(dependency_target(name, target) and not dependency_target(name, target + "-other"),
                "dependency target pin failed")
    require(exported_entry({"exports": {".": {"types": "./lib/index.d.ts", "import": "./lib/index.js"}}}) ==
            "lib/index.js", "export selection failed")
    try:
        exported_entry({"exports": "../outside.js"})
    except RuntimeError:
        pass
    else:
        raise RuntimeError("entry traversal accepted")
    s = SimpleNamespace(st_dev=1, st_ino=2, st_mode=stat.S_IFREG | 0o644, st_uid=0,
                        st_gid=0, st_nlink=2, st_size=8, st_mtime_ns=1, st_ctime_ns=1)
    check = Inspection()
    with patch.object(os, "fstat", return_value=s), patch.object(os, "stat", return_value=s), \
         patch.object(os, "listxattr", return_value=[]):
        for count in (1, 2, 3):
            s.st_nlink = count
            check.check((10, 9, "test.js", snapshot(s), True))
        for field, value in (("st_uid", 1000), ("st_mode", stat.S_IFREG | 0o666), ("st_nlink", 0)):
            old = getattr(s, field)
            setattr(s, field, value)
            try:
                check.check((10, 9, "test.js", snapshot(s), True))
            except RuntimeError:
                pass
            else:
                raise RuntimeError("trust rejection failed: " + field)
            setattr(s, field, old)
        with patch.object(os, "listxattr", return_value=["security.capability"]):
            try:
                check.check((10, 9, "test.js", snapshot(s), True))
            except RuntimeError:
                pass
            else:
                raise RuntimeError("capability rejection failed")
    return {"status": "SELF_TEST_PASS"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--relative-path")
    parser.add_argument("--dependency", choices=("dsh-home-paths", "dsh-app-boot"))
    parser.add_argument("--start-line", type=int, default=1)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(self_test() if args.self_test else inspect(args.relative_path, args.start_line, args.dependency)))
    except Exception as error:
        print(json.dumps({"status": "FAILED", "reason": str(error)}))
        sys.exit(1)
