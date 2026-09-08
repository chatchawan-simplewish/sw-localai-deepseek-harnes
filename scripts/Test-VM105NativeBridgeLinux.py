#!/usr/bin/env python3
"""One reviewed synthetic Linux transport attempt; default performs no SSH."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import threading
import time
import zlib

ROOT = '/run/dsh-native-bridge-check-20260909-a1'
NODE = '/opt/node-v24.19.0-linux-x64/bin/node'
NODE_SHA = 'bc17c508ffeed0ec622934f9b7fa72f8e78da65350e63c3eceb56fa688aa5e12'
INSPECTOR_SHA = 'fcddc77c890b289e28c609fa30b3b41f6c060a73c5c4ea3ab69b468a130df424'
PINS = {
    'native-codex-owner.mjs': '90bb452d25d5b6c7c7593e2cfc7c01650069d1d63f4770728bff5ef32935b14b',
    'native-codex-terminal.mjs': '9e9bf70f8c6e4088f66ac573ce2bf89a60971d30b4f9ea3000aface4af33b458',
    'test-native-codex-owner-linux.mjs': '6f82e2f2783123255f9e441cde991da2bdcbddbf92bd9f4dc6cc7e1b12cc1414',
}
CHECKS = ('passiveSocket0600', 'fakeDeviceFlowOnce', 'ownedSocketRemoved',
          'disconnectAbortAndDispose', 'preexistingPreserved', 'replacementPreservedAfterExit')
MAX_BUNDLE = 262144


def require(ok, code):
    if not ok:
        raise RuntimeError(code)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def check_node_mode(mode):
    require(not mode & (stat.S_ISUID | stat.S_ISGID), 'NODE_PRIVILEGED_MODE')


def validate_bundle(bundle):
    require(isinstance(bundle, dict) and set(bundle) == {'inspector', 'files'}, 'BUNDLE_FIELDS')
    inspector = base64.b64decode(bundle['inspector'], validate=True)
    require(sha(inspector) == INSPECTOR_SHA, 'INSPECTOR_HASH')
    require(isinstance(bundle['files'], dict) and set(bundle['files']) == set(PINS), 'FILE_SET')
    files = {}
    for name, digest in PINS.items():
        data = base64.b64decode(bundle['files'][name], validate=True)
        require(len(data) <= 65536 and sha(data) == digest, 'SOURCE_HASH')
        files[name] = data
    return inspector, files


def valid_result(value):
    return (isinstance(value, dict) and set(value) == {'status', 'checks'}
            and value['status'] == 'LINUX_BRIDGE_PASS'
            and isinstance(value['checks'], dict) and set(value['checks']) == set(CHECKS)
            and all(value['checks'][key] is True for key in CHECKS))


def ssh_once(argv, raw):
    """Bound both directions even if SSH stalls or emits unexpected output."""
    captured = []
    failed = []
    proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    def write():
        try:
            proc.stdin.write(raw)
            proc.stdin.close()
        except (OSError, ValueError):
            failed.append(True)

    def read():
        try:
            captured.append(proc.stdout.read(4097))
            proc.stdout.close()
        except (OSError, ValueError):
            failed.append(True)

    writer = threading.Thread(target=write, daemon=True)
    reader = threading.Thread(target=read, daemon=True)
    writer.start()
    reader.start()
    try:
        code = proc.wait(timeout=50)
        writer.join(1)
        reader.join(1)
        require(not writer.is_alive() and not reader.is_alive() and not failed and len(captured) == 1,
                'SSH_IO_INCOMPLETE')
        require(len(captured[0]) <= 4096, 'RECEIPT_SIZE')
        return code, captured[0]
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=2)


def remote():
    # No raw child output or exception text may cross this wrapper.
    import pwd
    import resource
    import selectors
    child = None
    group_ready = False
    check = None
    fds = []
    receipt = {'status': 'LINUX_CHECK_FAIL', 'root': ROOT}

    def expired(*_):
        raise TimeoutError()

    signal.signal(signal.SIGALRM, expired)
    signal.alarm(40)
    try:
        require(os.geteuid() == 0 and sys.version_info[:2] == (3, 12), 'ROOT_PYTHON')
        require(all(hasattr(os, key) for key in ('unshare', 'CLONE_NEWNET', 'waitid', 'WNOWAIT'))
                and os.execve in os.supports_fd, 'ISOLATION_UNSUPPORTED')
        raw = sys.stdin.buffer.read(MAX_BUNDLE + 1)
        require(len(raw) <= MAX_BUNDLE, 'BUNDLE_SIZE')
        inspector, files = validate_bundle(json.loads(raw))
        scope = {'__name__': 'reviewed_inspector'}
        exec(compile(inspector, '<reviewed-inspector>', 'exec'), scope)
        check = scope['Inspection']()
        run = check.open('/run')
        node = check.open(NODE, file=True)
        check_node_mode(os.fstat(node).st_mode)
        require(os.fstat(node).st_size <= 160 * 1024 * 1024, 'NODE_SIZE')

        def digest_node():
            os.lseek(node, 0, os.SEEK_SET)
            digest = hashlib.sha256()
            total = 0
            while chunk := os.read(node, 65536):
                total += len(chunk)
                require(total <= 160 * 1024 * 1024, 'NODE_SIZE')
                digest.update(chunk)
            return digest.hexdigest()

        require(digest_node() == NODE_SHA, 'NODE_HASH')
        check.verify()
        require(digest_node() == NODE_SHA, 'NODE_HASH_DRIFT')
        check.verify()
        account = pwd.getpwnam('dsh')
        require(account.pw_uid > 0 and account.pw_gid > 0, 'DSH_IDENTITY')
        os.umask(0o077)
        name = ROOT.rsplit('/', 1)[1]
        os.mkdir(name, mode=0o700, dir_fd=run)  # Exclusive, spent even on later failure.
        root = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=run)
        fds.append(root)
        os.mkdir('src', 0o700, dir_fd=root)
        src = os.open('src', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=root)
        fds.append(src)
        artifacts = []
        for filename, data in files.items():
            fd = os.open(filename, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o400, dir_fd=src)
            try:
                offset = 0
                while offset < len(data):
                    offset += os.write(fd, data[offset:])
                os.fchmod(fd, 0o444)
                os.fsync(fd)
                item = os.fstat(fd)
                artifacts.append({'name': filename, 'sha256': sha(data), 'inode': item.st_ino, 'mode': '0444'})
            finally:
                os.close(fd)
        os.fchmod(src, 0o555)
        os.fchown(root, account.pw_uid, account.pw_gid)
        receipt.update(artifacts=artifacts, root_inode=os.fstat(root).st_ino, node_sha256=NODE_SHA)
        output_r, output_w = os.pipe()
        ready_r, ready_w = os.pipe()
        gate_r, gate_w = os.pipe()
        fds.extend((output_r, output_w, ready_r, ready_w, gate_r, gate_w))
        child = os.fork()
        if child == 0:
            try:
                os.close(ready_r)
                os.close(gate_w)
                os.setsid()
                os.write(ready_w, b'R')
                require(os.read(gate_r, 1) == b'G', 'PARENT_GATE')
                os.unshare(os.CLONE_NEWNET)
                os.fchdir(root)
                os.setgroups([])
                os.setgid(account.pw_gid)
                os.setuid(account.pw_uid)
                resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
                resource.setrlimit(resource.RLIMIT_CPU, (25, 25))
                with open('/dev/null', 'rb', buffering=0) as null:
                    os.dup2(null.fileno(), 0)
                os.dup2(output_w, 1)
                os.dup2(output_w, 2)
                os.set_inheritable(node, True)
                os.execve(node, [NODE, ROOT + '/src/test-native-codex-owner-linux.mjs', ROOT],
                          {'HOME': ROOT, 'LANG': 'C.UTF-8', 'PATH': '/nonexistent', 'TMPDIR': ROOT})
            except BaseException:
                os._exit(121)
        os.close(output_w)
        fds.remove(output_w)
        os.close(ready_w)
        fds.remove(ready_w)
        require(os.read(ready_r, 1) == b'R', 'CHILD_SESSION')
        group_ready = True
        require(os.getpgid(child) == child, 'CHILD_GROUP')
        os.write(gate_w, b'G')
        deadline = time.monotonic() + 30
        data = bytearray()
        os.set_blocking(output_r, False)
        with selectors.DefaultSelector() as selector:
            selector.register(output_r, selectors.EVENT_READ)
            while True:
                require(time.monotonic() < deadline, 'CHILD_TIMEOUT')
                for _, _ in selector.select(0.05):
                    chunk = os.read(output_r, 4097 - len(data))
                    data.extend(chunk)
                    require(len(data) <= 4096, 'CHILD_OUTPUT_LIMIT')
                    if not chunk:
                        selector.unregister(output_r)
                ended = os.waitid(os.P_PID, child, os.WEXITED | os.WNOHANG | os.WNOWAIT)
                if ended is not None:
                    require(ended.si_code == os.CLD_EXITED and ended.si_status == 0, 'CHILD_EXIT')
                    # Leader remains unreaped, reserving its process group identity.
                    while True:
                        try:
                            chunk = os.read(output_r, 4097 - len(data))
                        except BlockingIOError:
                            break
                        data.extend(chunk)
                        require(len(data) <= 4096, 'CHILD_OUTPUT_LIMIT')
                        if not chunk:
                            break
                    break
        value = json.loads(data)
        require(valid_result(value), 'FIXTURE_RESULT')
        receipt.update(status='LINUX_TRANSPORT_PASS', checks=value['checks'])
    except BaseException:
        receipt['status'] = 'LINUX_CHECK_FAIL'
    finally:
        signal.alarm(5)
        try:
            if child:
                # No wait/reap occurs before this kill; the owned PGID cannot be reused.
                try:
                    if group_ready:
                        os.killpg(child, signal.SIGKILL)
                    else:
                        os.kill(child, signal.SIGKILL)  # Exact still-unreaped direct child.
                except ProcessLookupError:
                    pass
                deadline = time.monotonic() + 4
                while not os.waitpid(child, os.WNOHANG)[0]:
                    require(time.monotonic() < deadline, 'REAP_TIMEOUT')
                    time.sleep(0.02)
                receipt['owned_child_reaped'] = True
            for fd in fds:
                os.close(fd)
            if check:
                check.close()
        except BaseException:
            receipt['status'] = 'LINUX_CLEANUP_NOT_PROVEN'
        signal.alarm(0)
    print(json.dumps(receipt, separators=(',', ':')))


def self_test():
    check_node_mode(stat.S_IFREG | 0o755)
    for privileged in (stat.S_ISUID, stat.S_ISGID):
        try:
            check_node_mode(stat.S_IFREG | 0o755 | privileged)
        except RuntimeError as error:
            require(str(error) == 'NODE_PRIVILEGED_MODE', 'SELF_TEST_MODE_CODE')
        else:
            raise AssertionError('SELF_TEST_PRIVILEGED_MODE')
    good = {'status': 'LINUX_BRIDGE_PASS', 'checks': dict.fromkeys(CHECKS, True)}
    require(valid_result(good), 'SELF_TEST_VALID')
    require(not valid_result(dict(good, secret='unexpected')), 'SELF_TEST_EXTRA')
    require(not valid_result({'status': good['status'], 'checks': dict.fromkeys(CHECKS, 1)}), 'SELF_TEST_BOOL')
    try:
        validate_bundle({'inspector': '', 'files': {}})
    except RuntimeError:
        pass
    else:
        raise AssertionError('SELF_TEST_HASH')
    print('SELF_TEST_PASS')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--execute', action='store_true')
    mode.add_argument('--self-test', action='store_true')
    parser.add_argument('--reviewed-sha256')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.execute:
        print(json.dumps({'status': 'CONTRACT_ONLY', 'root': ROOT, 'pins': PINS}))
        return
    source = Path(__file__).read_bytes()
    require(args.reviewed_sha256 == sha(source), 'REVIEWED_HASH_REQUIRED')
    folder = Path(__file__).resolve().parent
    bundle = {'inspector': base64.b64encode((folder / 'inspect-vm105-pnpm-package.py').read_bytes()).decode(),
              'files': {name: base64.b64encode((folder / name).read_bytes()).decode() for name in PINS}}
    validate_bundle(bundle)
    raw = json.dumps(bundle, separators=(',', ':')).encode()
    require(len(raw) <= MAX_BUNDLE, 'BUNDLE_SIZE')
    encoded = base64.b64encode(zlib.compress(source)).decode()
    bootstrap = "import base64,zlib;exec(compile(zlib.decompress(base64.b64decode('" + encoded + "')),'<reviewed-launcher>','exec'),globals());"
    # Execute the same frozen remote definition, without running the CLI entry point.
    bootstrap = "__name__='reviewed_launcher';" + bootstrap + 'remote()'
    command = "sudo -n /usr/bin/python3.12 -I -c '" + bootstrap.replace("'", "'\"'\"'") + "'"
    argv = ['C:/Windows/System32/OpenSSH/ssh.exe', '-T', '-i', 'C:/Users/chatc/.ssh/codex-prox01-vms-ed25519',
            '-o', 'BatchMode=yes', '-o', 'IdentitiesOnly=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=10',
            'dsh@192.168.1.139', command]
    require(len(subprocess.list2cmdline(argv)) < 30000, 'COMMAND_SIZE')
    code, output = ssh_once(argv, raw)
    value = json.loads(output)
    require(isinstance(value, dict) and value.get('root') == ROOT, 'RECEIPT_INVALID')
    value['ssh_exit'] = code
    print(json.dumps(value, separators=(',', ':')))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        print('{"status":"LOCAL_CHECK_FAIL"}')
        sys.exit(1)
