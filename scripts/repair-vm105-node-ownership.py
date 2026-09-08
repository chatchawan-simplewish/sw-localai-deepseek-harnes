#!/usr/bin/env python3
"""One-shot VM105 metadata repair. Default: read-only; --self-test: temp tree only."""
import argparse
import hashlib
import json
import os
import stat
import sys


PARTS = ("/", "opt", "node-v24.19.0-linux-x64", "bin", "node")
SHA256 = "bc17c508ffeed0ec622934f9b7fa72f8e78da65350e63c3eceb56fa688aa5e12"
FORBIDDEN_XATTRS = {"system.posix_acl_access", "system.posix_acl_default", "security.capability"}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def identity(s):
    return s.st_dev, s.st_ino


def stable(s):
    return identity(s) + (s.st_mode, s.st_nlink, s.st_size, s.st_mtime_ns)


def digest(fd):
    os.lseek(fd, 0, os.SEEK_SET)
    h = hashlib.sha256()
    while chunk := os.read(fd, 1024 * 1024):
        h.update(chunk)
    return h.hexdigest()


def execute(apply=False):
    require(not apply or os.geteuid() == 0, "--apply requires root")
    fds, initial, changed = [], [], []

    def verify(root_owned):
        for i, fd in enumerate(fds):
            s = os.fstat(fd)
            expected = (0, 0) if i < 2 or i in root_owned else (1000, 1000)
            require((s.st_uid, s.st_gid) == expected, "unexpected ownership at index " + str(i))
            require(stat.S_IMODE(s.st_mode) == 0o755, "unexpected permissions")
            require(stat.S_ISREG(s.st_mode) if i == 4 else stat.S_ISDIR(s.st_mode), "unexpected file type")
            require(i != 4 or s.st_nlink == 1, "node must have one hard link")
            require(s.st_dev == initial[0].st_dev, "different filesystem device")
            require(not FORBIDDEN_XATTRS.intersection(os.listxattr(fd)), "ACL or capability present")
            require(stable(s) == stable(initial[i]), "descriptor metadata drift")
            linked = os.stat(PARTS[i], dir_fd=fds[i - 1] if i else None, follow_symlinks=False)
            require(identity(linked) == identity(s) and linked.st_mode == s.st_mode, "path identity drift")

    try:
        for i, part in enumerate(PARTS):
            flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
            flags |= os.O_DIRECTORY if i < 4 else os.O_NONBLOCK
            fd = os.open(part, flags, dir_fd=fds[-1] if fds else None)
            fds.append(fd)
            initial.append(os.fstat(fd))
            # Validate each ancestor before traversing its child.
            verify(set())
        require(digest(fds[-1]) == SHA256, "official node hash mismatch")
        verify(set())
        if apply:
            for i in (2, 3, 4):
                verify(set(changed))
                # Record first so even a partially successful syscall is rolled back.
                changed.append(i)
                os.fchown(fds[i], 0, 0)
                verify(set(changed))
            require(digest(fds[-1]) == SHA256, "post-repair node hash mismatch")
            verify(set(changed))
        return {"status": "APPLIED" if apply else "PREFLIGHT_PASS", "sha256": SHA256,
                "objects": [{"path": "/" if i == 0 else "/" + "/".join(PARTS[1:i + 1]),
                             "device": s.st_dev, "inode": s.st_ino,
                             "uid": os.fstat(fds[i]).st_uid, "gid": os.fstat(fds[i]).st_gid,
                             "mode": "0755"} for i, s in enumerate(initial)]}
    except BaseException as error:
        rollback_errors = []
        for i in reversed(changed):
            try:
                require(identity(os.fstat(fds[i])) == identity(initial[i]), "rollback identity drift")
                os.fchown(fds[i], initial[i].st_uid, initial[i].st_gid)
                s = os.fstat(fds[i])
                require((s.st_uid, s.st_gid, stat.S_IMODE(s.st_mode)) ==
                        (initial[i].st_uid, initial[i].st_gid, 0o755), "rollback verification failed")
            except BaseException:
                rollback_errors.append(i)
        if rollback_errors:
            raise RuntimeError("FAILED; rollback incomplete at indexes " + str(rollback_errors)) from error
        if changed:
            raise RuntimeError("FAILED; ownership rollback verified: " + str(error)) from error
        raise
    finally:
        for fd in reversed(fds):
            os.close(fd)


def self_test():
    """Exercise real Linux dirfds with fake ownership; never opens production paths."""
    import tempfile
    from pathlib import Path
    from types import SimpleNamespace
    from unittest.mock import patch

    real_open, real_stat, real_fstat = os.open, os.stat, os.fstat
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        node = root / "opt/node-v24.19.0-linux-x64/bin/node"
        node.parent.mkdir(parents=True)
        node.write_bytes(b"test node")
        paths = [root, root / "opt", node.parent.parent, node.parent, node]
        for path in paths:
            path.chmod(0o755)
        owners = {identity(real_stat(p)): ((0, 0) if i < 2 else (1000, 1000)) for i, p in enumerate(paths)}
        original = owners.copy()
        writes = []

        def remap(path):
            return temp if path == "/" else path

        def reported(s):
            data = {name: getattr(s, name) for name in
                    ("st_dev", "st_ino", "st_mode", "st_nlink", "st_size", "st_mtime_ns")}
            data["st_uid"], data["st_gid"] = owners.get(identity(s), (1000, 1000))
            return SimpleNamespace(**data)

        def chown(fd, uid, gid):
            key = identity(real_fstat(fd))
            writes.append((key, uid, gid))
            owners[key] = (uid, gid)

        with patch.object(os, "open", side_effect=lambda p, *a, **kw: real_open(remap(p), *a, **kw)), \
             patch.object(os, "stat", side_effect=lambda p, *a, **kw: reported(real_stat(remap(p), *a, **kw))), \
             patch.object(os, "fstat", side_effect=lambda fd: reported(real_fstat(fd))), \
             patch.object(os, "fchown", side_effect=chown), patch.object(os, "geteuid", return_value=0), \
             patch.object(sys.modules[__name__], "SHA256", hashlib.sha256(b"test node").hexdigest()):
            require(execute()["status"] == "PREFLIGHT_PASS" and not writes, "preflight test failed")
            with patch.object(os, "listxattr", return_value=["system.posix_acl_access"]):
                try:
                    execute(True)
                except RuntimeError:
                    pass
                else:
                    raise RuntimeError("ACL rejection test failed")
            require(not writes, "rejection mutated ownership")
            with patch.object(sys.modules[__name__], "SHA256", "wrong"):
                try:
                    execute(True)
                except RuntimeError:
                    pass
                else:
                    raise RuntimeError("hash rejection test failed")
            require(not writes, "hash rejection mutated ownership")
            owners[identity(real_stat(root / "opt"))] = (1000, 1000)
            try:
                execute(True)
            except RuntimeError:
                pass
            else:
                raise RuntimeError("ancestor ownership rejection failed")
            owners.update(original)

            def drifted_stat(p, *a, **kw):
                s = reported(real_stat(remap(p), *a, **kw))
                if p == "node":
                    s.st_ino += 1
                return s

            with patch.object(os, "stat", side_effect=drifted_stat):
                try:
                    execute(True)
                except RuntimeError:
                    pass
                else:
                    raise RuntimeError("path identity rejection failed")
            require(not writes, "trust rejection mutated ownership")
            require(execute(True)["status"] == "APPLIED" and len(writes) == 3, "apply test failed")
            require(all(value == (0, 0) for value in owners.values()), "apply ownership failed")
            owners.update(original)
            writes.clear()

            def fail_third(fd, uid, gid):
                chown(fd, uid, gid)
                if len(writes) == 3:
                    raise OSError("injected syscall failure")

            with patch.object(os, "fchown", side_effect=fail_third):
                try:
                    execute(True)
                except RuntimeError as error:
                    require("ownership rollback verified" in str(error), "rollback report missing")
                else:
                    raise RuntimeError("failure injection did not fail")
            require(owners == original and len(writes) == 6, "rollback test failed")
    return {"status": "SELF_TEST_PASS"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(self_test() if args.self_test else execute(args.apply)))
    except Exception as error:
        print(json.dumps({"status": "FAILED", "reason": str(error)}))
        sys.exit(1)
