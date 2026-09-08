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

ROOT = '/run/dsh-native-bridge-check-20260909-a2'
RELEASED = False  # Replacement preservation is unresolved; this a2 draft cannot execute.
NODE = '/opt/node-v24.19.0-linux-x64/bin/node'
NODE_SHA = 'bc17c508ffeed0ec622934f9b7fa72f8e78da65350e63c3eceb56fa688aa5e12'
INSPECTOR_SHA = 'fcddc77c890b289e28c609fa30b3b41f6c060a73c5c4ea3ab69b468a130df424'
PINS = {
    'native-codex-owner.mjs': '52e8c18d1b10c9c02eec27cbe8bce8ea60b7de1e5c78e29b137c1e13a4cd6fcb',
    'native-codex-terminal.mjs': '9e9bf70f8c6e4088f66ac573ce2bf89a60971d30b4f9ea3000aface4af33b458',
    'test-native-codex-owner-linux.mjs': '8a001554022b7d7eb20711ae12b5c6ec770c380c146d9d2247699ecb9e769405',
}
CHECKS = ('passiveSocket0600', 'fakeDeviceFlowOnce', 'ownedSocketRemoved',
          'disconnectAbortAndDispose', 'preexistingPreserved', 'replacementPreservedAfterExit')
MAX_BUNDLE = 262144
FIXTURE_STAGES = ('arguments', 'root_policy', 'empty_root', 'owned_bind', 'owned_connect',
                  'owned_flow', 'owned_dispose', 'disconnect_bind', 'disconnect_flow',
                  'disconnect_dispose', 'preexisting', 'replacement_spawn', 'replacement_bind',
                  'replacement_rename', 'replacement_dispose', 'replacement_preserve', 'complete')
REMOTE_STAGES = ('prerequisites', 'bundle', 'executable', 'root_create', 'source_write',
                 'child_fork', 'child_session', 'child_group', 'child_wait', 'fixture_parse', 'complete')


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


def valid_fixture(value):
    return (valid_result(value) or
            (isinstance(value, dict) and set(value) == {'status', 'stage'}
             and value['status'] == 'LINUX_BRIDGE_FAIL' and type(value['stage']) is str
             and value['stage'] in FIXTURE_STAGES))


def original_exit(reason, value):
    # Linux waitid CLD_EXITED/KILLED/DUMPED; never expose arbitrary exception data.
    require(type(reason) is int and reason in (1, 2, 3) and type(value) is int
            and (0 <= value <= 255 if reason == 1 else 1 <= value <= 64), 'EXIT_FIELDS')
    return {'kind': {1: 'exited', 2: 'killed', 3: 'dumped'}[reason], 'value': value}


def valid_receipt(value):
    base = {'status', 'root', 'stage', 'original_exit'}
    artifacts = {'artifacts', 'root_inode', 'node_sha256'}
    optional = artifacts | {'fixture_stage', 'owned_child_reaped', 'checks'}
    if not isinstance(value, dict) or not base <= set(value) or set(value) - base - optional:
        return False
    if (value['root'] != ROOT or type(value['stage']) is not str or value['stage'] not in REMOTE_STAGES
            or value['status'] not in ('LINUX_CHECK_FAIL', 'LINUX_CLEANUP_NOT_PROVEN', 'LINUX_TRANSPORT_PASS')):
        return False
    ended = value['original_exit']
    if ended is not None:
        if (not isinstance(ended, dict) or set(ended) != {'kind', 'value'}
                or type(ended['kind']) is not str or ended['kind'] not in ('exited', 'killed', 'dumped')):
            return False
        try:
            original_exit({'exited': 1, 'killed': 2, 'dumped': 3}[ended['kind']], ended['value'])
        except RuntimeError:
            return False
    if 'fixture_stage' in value and (type(value['fixture_stage']) is not str or value['fixture_stage'] not in FIXTURE_STAGES):
        return False
    if 'owned_child_reaped' in value and value['owned_child_reaped'] is not True:
        return False
    if artifacts & set(value):
        if (not artifacts <= set(value) or type(value['root_inode']) is not int or value['root_inode'] <= 0
                or value['node_sha256'] != NODE_SHA or not isinstance(value['artifacts'], list)
                or len(value['artifacts']) != len(PINS)):
            return False
        names = set()
        for item in value['artifacts']:
            if (not isinstance(item, dict) or set(item) != {'name', 'sha256', 'inode', 'mode'}
                    or type(item['name']) is not str or item['name'] not in PINS or item['name'] in names
                    or item['sha256'] != PINS[item['name']] or item['mode'] != '0444'
                    or type(item['inode']) is not int or item['inode'] <= 0):
                return False
            names.add(item['name'])
    if 'checks' in value and not valid_result({'status': 'LINUX_BRIDGE_PASS', 'checks': value['checks']}):
        return False
    return value['status'] != 'LINUX_TRANSPORT_PASS' or (
        value['stage'] == 'complete' and ended == {'kind': 'exited', 'value': 0}
        and artifacts <= set(value) and 'checks' in value and 'fixture_stage' not in value
        and value.get('owned_child_reaped') is True)


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
    receipt = {'status': 'LINUX_CHECK_FAIL', 'root': ROOT, 'stage': 'prerequisites', 'original_exit': None}

    def expired(*_):
        raise TimeoutError()

    signal.signal(signal.SIGALRM, expired)
    signal.alarm(40)
    try:
        require(RELEASED, 'ATTEMPT_NOT_RELEASED')
        require(os.geteuid() == 0 and sys.version_info[:2] == (3, 12), 'ROOT_PYTHON')
        require(all(hasattr(os, key) for key in ('unshare', 'CLONE_NEWNET', 'waitid', 'WNOWAIT'))
                and os.execve in os.supports_fd, 'ISOLATION_UNSUPPORTED')
        receipt['stage'] = 'bundle'
        raw = sys.stdin.buffer.read(MAX_BUNDLE + 1)
        require(len(raw) <= MAX_BUNDLE, 'BUNDLE_SIZE')
        inspector, files = validate_bundle(json.loads(raw))
        scope = {'__name__': 'reviewed_inspector'}
        exec(compile(inspector, '<reviewed-inspector>', 'exec'), scope)
        check = scope['Inspection']()
        receipt['stage'] = 'executable'
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
        receipt['stage'] = 'root_create'
        os.umask(0o077)
        name = ROOT.rsplit('/', 1)[1]
        os.mkdir(name, mode=0o700, dir_fd=run)  # Exclusive, spent even on later failure.
        root = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=run)
        fds.append(root)
        os.mkdir('src', 0o700, dir_fd=root)
        src = os.open('src', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=root)
        fds.append(src)
        receipt['stage'] = 'source_write'
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
        receipt['stage'] = 'child_fork'
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
        receipt['stage'] = 'child_session'
        require(os.read(ready_r, 1) == b'R', 'CHILD_SESSION')
        group_ready = True
        receipt['stage'] = 'child_group'
        require(os.getpgid(child) == child, 'CHILD_GROUP')
        os.write(gate_w, b'G')
        receipt['stage'] = 'child_wait'
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
                    receipt['original_exit'] = original_exit(ended.si_code, ended.si_status)
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
        receipt['stage'] = 'fixture_parse'
        value = json.loads(data)
        require(valid_fixture(value), 'FIXTURE_SCHEMA')
        if value['status'] == 'LINUX_BRIDGE_FAIL':
            receipt['fixture_stage'] = value['stage']
        require(receipt['original_exit'] == {'kind': 'exited', 'value': 0}, 'CHILD_EXIT')
        require(valid_result(value), 'FIXTURE_RESULT')
        receipt.update(status='LINUX_TRANSPORT_PASS', stage='complete', checks=value['checks'])
    except BaseException:
        receipt['status'] = 'LINUX_CHECK_FAIL'
    finally:
        signal.alarm(5)
        try:
            if child:
                # Capture a natural exit before cleanup, never relabel our SIGKILL as original.
                if receipt['original_exit'] is None:
                    ended = os.waitid(os.P_PID, child, os.WEXITED | os.WNOHANG | os.WNOWAIT)
                    if ended is not None:
                        receipt['original_exit'] = original_exit(ended.si_code, ended.si_status)
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
    receipt = {'status': 'LINUX_CHECK_FAIL', 'root': ROOT, 'stage': 'fixture_parse',
               'original_exit': {'kind': 'exited', 'value': 1}, 'fixture_stage': 'replacement_preserve'}
    require(valid_receipt(receipt), 'SELF_TEST_RECEIPT')
    for bad in (dict(receipt, secret='extra'), dict(receipt, stage='secret'),
                dict(receipt, original_exit={'kind': 'exited', 'value': True}),
                dict(receipt, original_exit={'kind': 'exited', 'value': 1, 'secret': 'extra'}),
                dict(receipt, artifacts=[]), dict(receipt, root=ROOT + '-other'),
                dict(receipt, status='LINUX_TRANSPORT_PASS'), dict(receipt, fixture_stage=[]),
                dict(receipt, owned_child_reaped=1), None):
        require(not valid_receipt(bad), 'SELF_TEST_RECEIPT_REJECT')
    failed = {'status': 'LINUX_BRIDGE_FAIL', 'stage': 'replacement_preserve'}
    require(valid_fixture(failed), 'SELF_TEST_FAILURE_STAGE')
    for bad in (dict(failed, stage='raw secret'), dict(failed, detail='secret'),
                dict(failed, stage=[]), [], None):
        require(not valid_fixture(bad), 'SELF_TEST_REJECT_FIXTURE')
    require(original_exit(1, 0) == {'kind': 'exited', 'value': 0}, 'SELF_TEST_EXIT')
    require(original_exit(2, 9) == {'kind': 'killed', 'value': 9}, 'SELF_TEST_SIGNAL')
    require(original_exit(3, 11) == {'kind': 'dumped', 'value': 11}, 'SELF_TEST_CORE')
    for reason, value in ((0, 1), (1, -1), (1, 256), (2, 0), (2, 65), (True, 0), (1, True)):
        try:
            original_exit(reason, value)
        except RuntimeError:
            pass
        else:
            raise AssertionError('SELF_TEST_EXIT_REJECT')
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
        print(json.dumps({'status': 'CONTRACT_ONLY', 'root': ROOT, 'released': RELEASED, 'pins': PINS}))
        return
    require(RELEASED, 'ATTEMPT_NOT_RELEASED')
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
    require(valid_receipt(value), 'RECEIPT_INVALID')
    value['ssh_exit'] = code
    print(json.dumps(value, separators=(',', ':')))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        print('{"status":"LOCAL_CHECK_FAIL"}')
        sys.exit(1)
