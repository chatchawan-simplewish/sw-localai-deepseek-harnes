#!/usr/bin/env python3
"""Remove one inactive candidate patch row; default is read-only. Never retry a failed write."""
import argparse
import hashlib
import json
import os
import stat
import sys

PARTS = ("/", "home", "dsh", ".dsh-profiles", "vm105-provider-v1", "profiles", "web", "cordis.patch.yml")
OLD_SHA = "e50562055d3e82ceef90e49ad8cc2502a69c9415d7b60293c2895d93141ae6cf"
FORBIDDEN = {"system.posix_acl_access", "system.posix_acl_default", "security.capability"}


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def replacement(data):
    require(sha(data) == OLD_SHA, "old patch digest mismatch")
    rows = json.loads(data)
    require(isinstance(rows, list) and len(rows) == 6 and all(isinstance(row, dict) for row in rows),
            "unexpected patch structure")
    matches = [i for i, row in enumerate(rows) if row.get("id") == "agent-default-model"]
    require(len(matches) == 1 and rows[matches[0]] == {"id": "agent-default-model", "disabled": True},
            "unexpected default-model patch")
    return (json.dumps([row for i, row in enumerate(rows) if i != matches[0]], indent=2) + "\n").encode()


def identity(s):
    return s.st_dev, s.st_ino


def run(apply=False):
    require((os.geteuid(), os.getegid()) == (1000, 1000), "requires dsh uid/gid1000")
    held = []
    write_started = False

    def verify():
        for i, (fd, parent, before) in enumerate(held):
            s = os.fstat(fd)
            file = i == len(PARTS) - 1
            require(stat.S_ISREG(s.st_mode) if file else stat.S_ISDIR(s.st_mode), "unexpected object type")
            require((s.st_uid, s.st_gid) == ((0, 0) if i < 2 else (1000, 1000)), "unexpected ownership")
            require(not s.st_mode & 0o022, "untrusted permissions")
            require(i < 3 or stat.S_IMODE(s.st_mode) == (0o600 if file else 0o700), "unexpected candidate mode")
            require(not file or s.st_nlink == 1, "unexpected file hard link")
            require(not FORBIDDEN.intersection(os.listxattr(fd)), "ACL or capability present")
            linked = os.stat(PARTS[i], dir_fd=parent, follow_symlinks=False)
            require(identity(before) == identity(s) == identity(linked) and linked.st_mode == s.st_mode,
                    "path or descriptor identity drift")
            require((s.st_mode, s.st_uid, s.st_gid, s.st_nlink) ==
                    (before.st_mode, before.st_uid, before.st_gid, before.st_nlink), "metadata drift")
            if not (file and write_started):
                require((s.st_size, s.st_mtime_ns, s.st_ctime_ns) ==
                        (before.st_size, before.st_mtime_ns, before.st_ctime_ns), "content metadata drift")

    def read(fd):
        os.lseek(fd, 0, os.SEEK_SET)
        data = b""
        while chunk := os.read(fd, 4096):
            data += chunk
            require(len(data) <= 65536, "patch too large")
        return data

    try:
        parent = None
        for i, part in enumerate(PARTS):
            file = i == len(PARTS) - 1
            flags = (os.O_RDWR if file and apply else os.O_RDONLY) | os.O_NOFOLLOW | os.O_CLOEXEC
            flags |= os.O_NONBLOCK if file else os.O_DIRECTORY
            fd = os.open(part, flags, dir_fd=parent)
            held.append((fd, parent, os.fstat(fd)))
            verify()
            parent = fd
        old = read(fd)
        new = replacement(old)
        verify()
        require(read(fd) == old, "patch drift before write")
        verify()
        if apply:
            write_started = True
            os.lseek(fd, 0, os.SEEK_SET)
            offset = 0
            while offset < len(new):
                written = os.write(fd, new[offset:])
                require(written > 0, "write made no progress")
                offset += written
            os.ftruncate(fd, len(new))
            os.fsync(fd)
            require(read(fd) == new, "written patch mismatch")
            verify()
        return {"status": "APPLIED" if apply else "PREFLIGHT_PASS", "old_sha256": OLD_SHA,
                "new_sha256": sha(new), "retained_rows": 5}
    except Exception as error:
        return {"status": "FAILED_AFTER_WRITE" if write_started else "FAILED_NO_WRITE", "reason": str(error)}
    finally:
        for fd, _, _ in reversed(held):
            os.close(fd)


def self_test():
    rows = [
        {"id": "spill-local", "config": {"root": "/home/dsh/.dsh-profiles/vm105-provider-v1/spills"}},
        {"id": "session-telemetry-otel", "config": {"mode": "DISABLED"}},
        {"id": "llm-deepseek", "disabled": True},
        {"id": "web-search-deepseek", "disabled": True},
        {"id": "llm-pi-ai", "config": {"providers": {}}},
        {"id": "agent-default-model", "disabled": True},
    ]
    data = (json.dumps(rows, indent=2) + "\n").encode()
    new = replacement(data)
    require(json.loads(new) == rows[:-1], "non-target rows changed")
    try:
        replacement(data + b" ")
    except RuntimeError:
        pass
    else:
        raise RuntimeError("unexpected digest accepted")
    return {"status": "SELF_TEST_PASS", "old_sha256": sha(data), "new_sha256": sha(new)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        result = self_test() if args.self_test else run(args.apply)
        print(json.dumps(result))
        sys.exit(1 if result["status"].startswith("FAILED") else 0)
    except Exception as error:
        print(json.dumps({"status": "FAILED_NO_WRITE", "reason": str(error)}))
        sys.exit(1)
