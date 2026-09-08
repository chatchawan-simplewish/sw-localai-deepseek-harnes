#!/usr/bin/env python3
"""Print a native candidate blueprint; --apply creates it once, without cleanup/retry."""
import argparse
import hashlib
import json
import os
import stat
import sys

HOME = "/home/dsh/.dsh-profiles/vm105-provider-v1"
FORBIDDEN = {"system.posix_acl_access", "system.posix_acl_default", "security.capability"}
DIRECTORIES = {"": {"profiles", "spills"}, "profiles": {"web"},
               "profiles/web": {"package.json", "pnpm-workspace.yaml", "cordis.yml", "cordis.patch.yml"},
               "spills": set()}


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def content():
    values = {
        "package.json": {"name": "dsh-profile-web", "private": True, "dependencies": {},
                         "dsh": {"profile": {"bundles": ["@deepseek-ai/dsh-base", "@deepseek-ai/dsh-web-app"]}}},
        "pnpm-workspace.yaml": {"packages": ["."], "nodeLinker": "hoisted", "autoInstallPeers": False},
        "cordis.yml": [],
        "cordis.patch.yml": [
            {"id": "spill-local", "config": {"root": HOME + "/spills"}},
            {"id": "session-telemetry-otel", "config": {"mode": "DISABLED"}},
            {"id": "llm-deepseek", "disabled": True},
            {"id": "web-search-deepseek", "disabled": True},
            {"id": "llm-pi-ai", "config": {"providers": {}}},
            {"id": "agent-default-model", "disabled": True},
        ],
    }
    result = {}
    for name, value in values.items():
        data = (json.dumps(value, indent=2) + "\n").encode("utf-8")
        require(json.loads(data) == value, "blueprint serialization failed")
        result["profiles/web/" + name] = data
    return result


def inode(s):
    return s.st_dev, s.st_ino


def check(fd, directory, owner, mode=None):
    s = os.fstat(fd)
    require(stat.S_ISDIR(s.st_mode) if directory else stat.S_ISREG(s.st_mode), "unexpected object type")
    require((s.st_uid, s.st_gid) == owner, "unexpected ownership")
    require(not s.st_mode & 0o022, "writable ancestor")
    require(mode is None or stat.S_IMODE(s.st_mode) == mode, "unexpected permissions")
    require(directory or s.st_nlink == 1, "unexpected file hard link")
    require(not FORBIDDEN.intersection(os.listxattr(fd)), "ACL or capability present")
    return s


def open_dir(name, parent=None):
    return os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent)


def verify_tree(root, files):
    """Inventory only the newly created candidate, never an old profile."""
    def visit(fd, relative):
        check(fd, True, (1000, 1000), 0o700)
        require(set(os.listdir(fd)) == DIRECTORIES[relative], "unexpected candidate tree: " + relative)
        for name in sorted(DIRECTORIES[relative]):
            path = relative + "/" + name if relative else name
            directory = path in DIRECTORIES
            flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
            flags |= os.O_DIRECTORY if directory else os.O_NONBLOCK
            child = os.open(name, flags, dir_fd=fd)
            try:
                before = check(child, directory, (1000, 1000), 0o700 if directory else 0o600)
                if directory:
                    visit(child, path)
                else:
                    expected = files[path]
                    data = b""
                    while len(data) <= len(expected):
                        chunk = os.read(child, len(expected) + 1 - len(data))
                        if not chunk:
                            break
                        data += chunk
                    require(data == expected, "candidate content mismatch: " + path)
                    require(json.loads(data) == json.loads(expected), "candidate JSON mismatch")
                after = check(child, directory, (1000, 1000), 0o700 if directory else 0o600)
                linked = os.stat(name, dir_fd=fd, follow_symlinks=False)
                require(inode(before) == inode(after) == inode(linked) and linked.st_mode == after.st_mode,
                        "candidate identity drift: " + path)
                require((before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
                        (after.st_size, after.st_mtime_ns, after.st_ctime_ns), "candidate metadata drift")
            finally:
                os.close(child)
        require(set(os.listdir(fd)) == DIRECTORIES[relative], "candidate tree drift")
    visit(root, "")


def prepare():
    require((os.geteuid(), os.getegid()) == (1000, 1000), "requires dsh uid/gid 1000")
    files, held, created = content(), [], []
    previous_umask = os.umask(0o077)
    try:
        parent = None
        for index, name in enumerate(("/", "home", "dsh")):
            fd = open_dir(name, parent)
            held.append((fd, parent, name, check(fd, True, (0, 0) if index < 2 else (1000, 1000))))
            parent = fd
        # mkdir is exclusive: any existing parent ends this attempt without overwrite.
        for name in (".dsh-profiles", "vm105-provider-v1"):
            os.mkdir(name, 0o700, dir_fd=parent)
            created.append(name)
            fd = open_dir(name, parent)
            held.append((fd, parent, name, check(fd, True, (1000, 1000), 0o700)))
            parent = fd
        root = parent
        dirs = {"": root}
        for path in ("profiles", "profiles/web", "spills"):
            before, _, name = path.rpartition("/")
            os.mkdir(name, 0o700, dir_fd=dirs[before])
            created.append(path)
            fd = open_dir(name, dirs[before])
            held.append((fd, dirs[before], name, check(fd, True, (1000, 1000), 0o700)))
            dirs[path] = fd
        for path, data in files.items():
            before, _, name = path.rpartition("/")
            fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                         0o600, dir_fd=dirs[before])
            created.append(path)
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
        verify_tree(root, files)
        require(set(os.listdir(held[3][0])) == {"vm105-provider-v1"}, "unexpected candidate parent tree")
        for index, (fd, parent, name, before) in enumerate(held):
            after = check(fd, True, (0, 0) if index < 2 else (1000, 1000), 0o700 if index >= 3 else None)
            linked = os.stat(name, dir_fd=parent, follow_symlinks=False)
            require(inode(before) == inode(after) == inode(linked) and linked.st_mode == after.st_mode,
                    "held directory path drift")
        return {"status": "CREATED_VERIFIED", "files": hashes(files)}
    except Exception as error:
        return {"status": "FAILED_RETAINED", "reason": str(error), "retained_created": created}
    finally:
        for fd, _, _, _ in reversed(held):
            os.close(fd)
        os.umask(previous_umask)


def hashes(files):
    return [{"path": path, "sha256": hashlib.sha256(data).hexdigest()} for path, data in files.items()]


def self_test():
    import tempfile
    from pathlib import Path
    from types import SimpleNamespace
    from unittest.mock import patch
    real_open, real_stat, real_fstat = os.open, os.stat, os.fstat
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        (root / "home/dsh").mkdir(parents=True)
        for path in (root / "home", root / "home/dsh"):
            path.chmod(0o755)
        trusted = {inode(real_stat(root)), inode(real_stat(root / "home"))}

        def report(s):
            fields = {key: getattr(s, key) for key in
                      ("st_dev", "st_ino", "st_mode", "st_nlink", "st_size", "st_mtime_ns", "st_ctime_ns")}
            fields["st_uid"] = fields["st_gid"] = 0 if inode(s) in trusted else 1000
            return SimpleNamespace(**fields)

        def remap(path):
            return temp if path == "/" else path

        with patch.object(os, "open", side_effect=lambda p, *a, **kw: real_open(remap(p), *a, **kw)), \
             patch.object(os, "stat", side_effect=lambda p, *a, **kw: report(real_stat(remap(p), *a, **kw))), \
             patch.object(os, "fstat", side_effect=lambda fd: report(real_fstat(fd))), \
             patch.object(os, "geteuid", return_value=1000), patch.object(os, "getegid", return_value=1000):
            first = prepare()
            require(first["status"] == "CREATED_VERIFIED", "creation test failed: " + json.dumps(first))
            require(prepare()["status"] == "FAILED_RETAINED", "existing parent accepted")
            candidate = root / HOME.lstrip("/")
            target = candidate / "profiles/web/cordis.yml"
            require(target.read_bytes() == content()["profiles/web/cordis.yml"], "existing file overwritten")
            target.write_bytes(b"[{}]\n")
            fd = open_dir(str(candidate))
            try:
                try:
                    verify_tree(fd, content())
                except RuntimeError:
                    pass
                else:
                    raise RuntimeError("tampered content accepted")
            finally:
                os.close(fd)
    return {"status": "SELF_TEST_PASS"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        result = self_test() if args.self_test else prepare() if args.apply else {"status": "BLUEPRINT", "files": hashes(content())}
        print(json.dumps(result))
        sys.exit(1 if result["status"] == "FAILED_RETAINED" else 0)
    except Exception as error:
        print(json.dumps({"status": "FAILED", "reason": str(error)}))
        sys.exit(1)
