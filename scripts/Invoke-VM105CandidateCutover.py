#!/usr/bin/env python3
"""VM105 bounded cutover. Default is read-only; execution requires separate release/readiness."""
import argparse
import base64
import contextlib
import hashlib
import json
import os
import pathlib
import re
import shlex
import socket
import signal
import stat
import subprocess
import sys
import time

SMOKE_SHA = 'bcbfe2c6ee27f7895dc8feef26ae134ef574ab7d337902c11098cbee753ddc77'
GRAPH_SHA = 'f41ff7a8ed958f0baf262f043d9cee6e19fd56a97d2513a6770cc8d505b2d73b'
BASE_SHA = '286e05565c12cdaae886a3907500932b07e239277afe60da2f251777967761d3'
PREFLIGHT_CODES = frozenset({
    'BOOTSTRAP_TIMEOUT', 'BOOTSTRAP_EOF', 'BOOTSTRAP_SIZE', 'BOOTSTRAP_PIN', 'BOOTSTRAP_SCHEMA', 'INPUT_PIN',
    'GRAPH_RECEIPT', 'BASE_RECEIPT', 'FRESH_GRAPH_VERIFICATION', 'GRAPH_DRIFT', 'INVENTORY_DRIFT', 'CANDIDATE_PIN_DRIFT',
    'BASE_SOURCE_DRIFT', 'BASE_EFFECTIVE_DRIFT', 'ACTIVATION_SOURCE', 'SOCKET_EXISTS', 'DROPIN_DESTINATION',
    'BASE_EXECSTART', 'PILOT_ENVIRONMENT', 'PILOT_MEMORY_PRESSURE', 'FIREWALL_POLICY', 'PILOT_LISTENER', 'PILOT_CHANGED',
    'FD_CLOSE_FAILED', 'VERIFICATION_INCOMPLETE',
})
DROP = (b'[Service]\nEnvironment=DSH_HOME=/home/dsh/.dsh-profiles/vm105-provider-v1\nExecStart=\n'
        b'ExecStart=/opt/node-v24.19.0-linux-x64/bin/node --no-global-search-paths '
        b'/opt/deepseek-harness/node_modules/@deepseek-ai/dsh/lib/bin.js '
        b'web --host 127.0.0.1 --port 3080 --no-open\n')


class Blocked(Exception):
    pass


def require(ok, code):
    if not ok:
        raise Blocked(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class Interrupted(BaseException):
    pass


def safe_error(error, smoke=None):
    if isinstance(error, (TimeoutError, subprocess.TimeoutExpired)):
        return 'TIMEOUT'
    if isinstance(error, EOFError):
        return 'PARENT_EOF'
    if isinstance(error, BrokenPipeError):
        return 'OUTPUT_FAILURE'
    # Never echo arbitrary exception arguments or dependency output.
    value = error.args[0] if len(error.args) == 1 else None
    if smoke is not None and type(error) is smoke.Blocked and type(value) is str and value in smoke.DIAGNOSTIC_CODES:
        return value
    if isinstance(error, (Blocked, Interrupted)) and isinstance(value, str) and re.fullmatch('[A-Z0-9_]{1,64}', value):
        return value
    return 'VERIFICATION_INCOMPLETE'


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'PROTOCOL_DUPLICATE')
            result[key] = value
        return result
    require(0 < len(raw) <= 4096, 'PROTOCOL_SIZE')
    try:
        return json.loads(raw, object_pairs_hook=pairs)
    except (ValueError, UnicodeError):
        raise Blocked('PROTOCOL_JSON') from None


class GateProtocol:
    def __init__(self, nonce):
        require(type(nonce) is str and re.fullmatch('[0-9a-f]{64}', nonce), 'PROTOCOL_NONCE')
        self.nonce, self.used = nonce, set()

    def accept(self, raw, stage):
        require(stage in {'PREFLIGHT', 'CANDIDATE', 'ROLLBACK'} and stage not in self.used, 'PROTOCOL_REPLAY')
        self.used.add(stage)  # Malformed or negative messages also consume their gate.
        message = strict_json(raw)
        require(type(message) is dict and set(message) == {'nonce', 'stage', 'ok'}
                and message['nonce'] == self.nonce and message['stage'] == stage
                and type(message['ok']) is bool, 'PROTOCOL_SCHEMA')
        require(message['ok'], 'PARENT_GATE_FAILED')


def run_cutover(runtime, gate, emit):
    """One attempt; receipt delivery is part of acceptance, independent rollback output."""
    stopped = False
    try:
        runtime.preflight()
        gate('PREFLIGHT')
        stopped = True  # A failed or interrupted stop command may already have taken effect.
        runtime.stop_pilot()
        runtime.old_baseline()
        runtime.create()
        runtime.reload()
        runtime.start_candidate()
        runtime.accept()
        gate('CANDIDATE')
        runtime.verify_candidate()
        runtime.channel_check()
        result = {'status': 'SWITCH_ACCEPTED', 'gate': 'CREDENTIAL_GATE',
                  'primary_error': None, 'rollback_error': None}
        emit(result)
        return result
    except (Exception, Interrupted, KeyboardInterrupt) as error:
        stopped = getattr(runtime, 'stop_attempted', stopped)
        result = {'status': 'BLOCKED', 'gate': 'CREDENTIAL_GATE',
                  'primary_error': safe_error(error, getattr(runtime, 'smoke', None)), 'rollback_error': None}
    if stopped:
        try:
            runtime.rollback()
            gate('ROLLBACK')
            runtime.verify_restored()
            runtime.channel_check()
            result['status'] = 'ROLLED_BACK'
        except (Exception, Interrupted, KeyboardInterrupt) as error:
            result['rollback_error'] = safe_error(error, getattr(runtime, 'smoke', None))
    try:
        emit(result)
    except (Exception, Interrupted, KeyboardInterrupt):
        result.update(status='BLOCKED', rollback_error=result['rollback_error'] or 'OUTPUT_FAILURE')
    return result


FRAGMENT = '/etc/systemd/system/deepseek-harness.service'
DIRECTORY = FRAGMENT + '.d'
DROP_NAME = '90-vm105-provider-profile.conf'
DROP_PATH = DIRECTORY + '/' + DROP_NAME
NODE = '/opt/node-v24.19.0-linux-x64/bin/node'
CLI = '/opt/deepseek-harness/node_modules/@deepseek-ai/dsh/lib/bin.js'
CANDIDATE_ARGV = [NODE, '--no-global-search-paths', CLI, 'web', '--host', '127.0.0.1', '--port', '3080', '--no-open']
PILOT_ARGV = [NODE, CLI, 'web', '--host', '127.0.0.1', '--port', '3080']


def identity(s):
    return (s.st_dev, s.st_ino, s.st_mode, s.st_uid, s.st_gid, s.st_nlink)


def owned_matches(original, current, content, written):
    return original == current and content == written and DROP.startswith(written)


@contextlib.contextmanager
def file_boundary():
    # Defer asynchronous interruption until exclusive-inode/write bookkeeping is complete.
    previous = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGHUP, signal.SIGTERM, signal.SIGINT, signal.SIGALRM})
    try:
        yield
    finally:
        signal.pthread_sigmask(signal.SIG_SETMASK, previous)


def wait_job(show):
    end = time.monotonic() + 95  # The base start/stop jobs each have a 90-second timeout.
    while True:
        require(time.monotonic() < end, 'SYSTEMD_JOB_TIMEOUT')
        job = show()['Job']
        require(type(job) is str and re.fullmatch('0|[1-9][0-9]*', job), 'SYSTEMD_JOB_SCHEMA')
        if job == '0':
            return
        time.sleep(min(0.2, max(0, end - time.monotonic())))


def require_lineage(original, current, replacement_allowed, composition_proven):
    require(composition_proven, 'CONTROL_SOURCE_AMBIGUOUS')
    if original == current:
        return
    require(replacement_allowed and original is not None
            and int(current['restarts']) > int(original['restarts'])
            and current['invocation'] != original['invocation']
            and int(current['start']) > int(original['start']), 'INVOCATION_CHANGED')


class OwnedDrop:
    """Holds the exclusively created inode, including a partially written prefix."""
    def __init__(self, smoke):
        self.smoke, self.trust = smoke, smoke.Trusted()
        self.fd, self.directory, self.written, self.original = None, None, b'', None
        self.created_directory = False
        self.mounts = self.mount_snapshot()

    @staticmethod
    def mount_snapshot():
        with open('/proc/self/mountinfo', 'rb') as stream:
            raw = stream.read(1048577)
        require(len(raw) <= 1048576, 'MOUNT_BOUND')
        return raw

    def verify(self):
        self.trust.verify()
        require(self.mount_snapshot() == self.mounts, 'MOUNT_DRIFT')
        if self.directory is not None:
            require(os.fstat(self.directory).st_mode & 0o777 == 0o755, 'DROPIN_DIRECTORY_MODE')
            require(sorted(os.listdir(self.directory)) == ([DROP_NAME] if self.fd is not None else []), 'DROPIN_CONFLICT')

    def refresh_directory(self, path):
        fd, old, file = self.trust.held[path]
        now = os.fstat(fd)
        require(identity(now) == old[:6] and identity(os.lstat(path)) == old[:6], 'DIRECTORY_IDENTITY')
        require(not self.smoke.FORBIDDEN.intersection(os.listxattr(fd)), 'DIRECTORY_ATTRIBUTES')
        self.trust.held[path] = (fd, self.smoke.snapshot(now), file)

    def create(self):
        parent = self.trust.open('/etc/systemd/system')
        self.verify()
        try:
            self.directory = self.trust.open(DIRECTORY)
        except FileNotFoundError:
            with file_boundary():
                previous_umask = os.umask(0o022)
                try:
                    os.mkdir('deepseek-harness.service.d', 0o755, dir_fd=parent)
                finally:
                    os.umask(previous_umask)
                self.created_directory = True
                # mkdir changes the parent's link count by exactly one.
                fd, old, file = self.trust.held['/etc/systemd/system']
                now = os.fstat(fd)
                require(identity(now)[:5] == old[:5] and now.st_nlink == old[5] + 1, 'DIRECTORY_IDENTITY')
                self.trust.held['/etc/systemd/system'] = (fd, self.smoke.snapshot(now), file)
                self.directory = self.trust.open(DIRECTORY)
        self.verify()
        with file_boundary():
            self.fd = os.open(DROP_NAME, os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                              0o644, dir_fd=self.directory)
            # Record before any chmod/write/fsync operation that can fail.
            self.original = identity(os.fstat(self.fd))
            self.refresh_directory(DIRECTORY)
        require(self.original[3:] == (0, 0, 1) and stat.S_ISREG(self.original[2]), 'DROPIN_OWNER')
        with file_boundary():
            os.fchmod(self.fd, 0o644)
            self.original = identity(os.fstat(self.fd))
        while len(self.written) < len(DROP):
            with file_boundary():
                count = os.write(self.fd, DROP[len(self.written):])
                require(count > 0, 'DROPIN_SHORT_WRITE')
                self.written += DROP[len(self.written):len(self.written) + count]
        os.fsync(self.fd)
        os.fsync(self.directory)
        self.check_file(complete=True)

    def check_file(self, complete=False):
        self.verify()
        require(self.fd is not None and self.original is not None, 'DROPIN_NOT_OWNED')
        current = os.fstat(self.fd)
        require(identity(os.stat(DROP_NAME, dir_fd=self.directory, follow_symlinks=False)) == identity(current), 'DROPIN_REPLACED')
        require(not self.smoke.FORBIDDEN.intersection(os.listxattr(self.fd)), 'DROPIN_ATTRIBUTES')
        os.lseek(self.fd, 0, os.SEEK_SET)
        content = self.smoke.bounded_read(self.fd, len(DROP))
        require(owned_matches(self.original, identity(current), content, self.written), 'DROPIN_CHANGED')
        require(not complete or content == DROP and stat.S_IMODE(current.st_mode) == 0o644, 'DROPIN_INCOMPLETE')
        require(self.smoke.snapshot(os.fstat(self.fd)) == self.smoke.snapshot(current), 'DROPIN_READ_DRIFT')
        self.verify()

    def remove(self):
        if self.fd is None:
            return
        self.check_file()
        with file_boundary():
            os.unlink(DROP_NAME, dir_fd=self.directory)
            os.close(self.fd)
            self.fd = None
            self.refresh_directory(DIRECTORY)
        os.fsync(self.directory)
        self.verify()

    def close(self):
        try:
            if self.fd is not None:
                os.close(self.fd)
                self.fd = None
        finally:
            self.trust.close()


class NativeCutover:
    """Linux VM lane. All source, process and private-inventory checks stay local."""
    def __init__(self, bundle_pin):
        self.bundle_pin = bundle_pin
        self.drop = None
        self.candidate = self.restored = None
        self.loaded_candidate = False
        self.started_candidate = False
        self.old = None
        self.stop_attempted = False
        self.deadline = time.monotonic() + 480

    def preflight(self):
        scope = {'BUNDLE_SHA': self.bundle_pin, 'PINS': {'smoke': SMOKE_SHA, 'graph': GRAPH_SHA, 'base': BASE_SHA},
                 'PREFLIGHT_CODES': PREFLIGHT_CODES}
        # Execute the unchanged read-only preflight body, retaining its verified inputs.
        exec(compile(REMOTE[:REMOTE.rindex('print(json.dumps(result,sort_keys=True))')], '<cutover-preflight>', 'exec'), scope)
        self.smoke = scope.get('smoke')
        code = scope['result'].get('error_code')
        allowed = PREFLIGHT_CODES | (self.smoke.DIAGNOSTIC_CODES if self.smoke is not None else set())
        require(scope['result']['status'] == 'CUTOVER_PREFLIGHT_PASS',
                code if type(code) is str and code in allowed else 'FRESH_PREFLIGHT_FAILED')
        self.smoke, self.base, self.graph = scope['smoke'], scope['base'], scope['graph']['result']
        self.path = scope['before'][3]
        self.drop = OwnedDrop(self.smoke)
        self.firewall = self.smoke.command(['/usr/sbin/ufw', 'status', 'numbered'], 5)
        self.pilot = self.capture(False)
        require(self.pilot['invocation'] == scope['initial_identity']['InvocationID']
                and self.pilot['pid'] == scope['initial_identity']['MainPID'], 'PILOT_CHANGED')
        require(self.properties(['Job']) == {'Job': '0'}, 'SYSTEMD_JOB_EXISTS')
        remaining = self.deadline - time.monotonic()
        require(remaining > 0, 'MAIN_DEADLINE')
        signal.setitimer(signal.ITIMER_REAL, remaining)

    def properties(self, keys):
        raw = self.smoke.command(['/usr/bin/systemctl', 'show', self.smoke.PILOT, '--all', '--no-pager',
                                  '--property=' + ','.join(keys)], 5)
        pairs = [line.split('=', 1) for line in raw.splitlines() if '=' in line]
        values = dict(pairs)
        require(len(values) == len(pairs) and not set(values) - set(keys), 'UNIT_PROPERTY_SCHEMA')
        missing = set(keys) - set(values)
        require(missing <= {'EnvironmentFiles', 'Sockets'}, 'UNIT_PROPERTIES_MISSING')
        if missing:
            self.sources(self.loaded_candidate)
        for name, marker in (('EnvironmentFiles', self.smoke.ENV_SOURCE_PROOF), ('Sockets', self.smoke.SOCKET_SOURCE_PROOF)):
            if name in missing:
                values[name] = marker
            elif name in values:
                require(values[name] == '', 'ACTIVATION_SOURCE')
        return values

    def sources(self, candidate, loaded=True):
        trusted = self.smoke.Trusted()
        try:
            require(trusted.read(FRAGMENT) == self.base['source'].encode(), 'BASE_SOURCE_DRIFT')
            require(os.fstat(trusted.open(FRAGMENT, True)).st_nlink == 1, 'BASE_SOURCE_HARDLINK')
            self.smoke.reject_envfile_directives(self.base['source'].encode(), sockets=True)
            if self.drop.fd is not None:
                self.drop.check_file(complete=candidate)
            else:
                require(not os.path.lexists(DROP_PATH), 'DROPIN_UNOWNED')
            try:
                directory = trusted.open(DIRECTORY)
            except FileNotFoundError:
                require(not candidate, 'DROPIN_MISSING')
            else:
                require(os.fstat(directory).st_mode & 0o777 == 0o755
                        and sorted(os.listdir(directory)) == ([DROP_NAME] if self.drop.fd is not None else []), 'DROPIN_CONFLICT')
            if candidate:
                require(trusted.read(DROP_PATH) == DROP, 'DROPIN_SOURCE_DRIFT')
                self.smoke.reject_envfile_directives(DROP, sockets=True)
            if loaded:
                mapping = self.properties(['FragmentPath', 'DropInPaths', 'PassEnvironment', 'TriggeredBy'])
                require(mapping == {'FragmentPath': FRAGMENT, 'DropInPaths': DROP_PATH if candidate else '',
                                    'PassEnvironment': '', 'TriggeredBy': ''}, 'SOURCE_MAPPING_DRIFT')
            require(self.smoke.show('deepseek-harness.socket', ['LoadState']) == {'LoadState': 'not-found'}, 'SOCKET_EXISTS')
            trusted.verify()
            self.drop.verify()
        finally:
            trusted.close()

    def composition(self, candidate):
        self.sources(candidate)
        excluded = {'MainPID', 'NRestarts', 'ExecMainStartTimestamp', 'ActiveState', 'InvocationID', 'DropInPaths'}
        expected = {k: v for k, v in self.base['effective_properties'].items() if k not in excluded}
        p = self.properties(list(expected) + ['EnvironmentFiles', 'Sockets', 'Environment', 'ExecStart'])
        require(all(p[k] == value for k, value in expected.items()), 'BASE_EFFECTIVE_DRIFT')
        pairs = [item.split('=', 1) for item in shlex.split(p['Environment'])]
        require(len(pairs) == 3 and dict(pairs) == {'HOME': '/home/dsh', 'PATH': self.path,
                'DSH_HOME': self.smoke.HOME if candidate else self.smoke.OLD}, 'SELECTOR_OR_ENVIRONMENT')
        args = CANDIDATE_ARGV if candidate else ['/usr/local/bin/dsh', 'web', '--host', '127.0.0.1', '--port', '3080']
        prefix = '{ path=' + args[0] + ' ; argv[]=' + ' '.join(args) + ' ; ignore_errors=no ; '
        require(p['ExecStart'].startswith(prefix) and p['ExecStart'].endswith(' }')
                and p['ExecStart'].count('{') == p['ExecStart'].count('}') == 1, 'EFFECTIVE_EXECSTART')
        require(not os.path.lexists('/srv/dsh/workspaces/.env'), 'WORKSPACE_ENVFILE')

    def capture(self, candidate):
        self.composition(candidate)
        keys = ['InvocationID', 'MainPID', 'ExecMainStartTimestampMonotonic', 'NRestarts', 'ActiveState', 'ControlGroup']
        props = self.properties(keys)
        require(props['ActiveState'] == 'active' and re.fullmatch('[0-9a-f]{32}', props['InvocationID'])
                and props['MainPID'].isdigit() and int(props['MainPID']) > 1
                and props['NRestarts'].isdigit() and props['ExecMainStartTimestampMonotonic'].isdigit()
                and props['ControlGroup'] == '/system.slice/' + self.smoke.PILOT, 'SERVICE_IDENTITY')
        pid = props['MainPID']
        process = self.smoke.process(pid)
        require(process[2] == props['ControlGroup'] and process[3] == os.readlink('/proc/self/ns/net'), 'SERVICE_CGROUP')
        require(self.smoke.argv(pid) == (CANDIDATE_ARGV if candidate else PILOT_ARGV), 'PROCESS_ARGV')
        status = dict(line.split(':', 1) for line in self.smoke.proc_read(pid, 'status').decode().splitlines() if ':' in line)
        require(status['Uid'].split() == status['Gid'].split() == ['1000'] * 4, 'PROCESS_OWNER')
        require(self.group() == {int(pid)}, 'SERVICE_CGROUP_MEMBERS')
        env = self.smoke.environment(pid)
        names = {'HOME', 'DSH_HOME', 'PATH', 'USER', 'LOGNAME', 'SHELL', 'LANG', 'INVOCATION_ID', 'JOURNAL_STREAM',
                 'SYSTEMD_EXEC_PID', 'PWD', 'MEMORY_PRESSURE_WATCH', 'MEMORY_PRESSURE_WRITE'}
        require(set(env) <= names and env.get('HOME') == '/home/dsh' and env.get('PATH') == self.path
                and env.get('DSH_HOME') == (self.smoke.HOME if candidate else self.smoke.OLD)
                and env.get('PWD') == self.base['effective_properties']['WorkingDirectory']
                and env.get('INVOCATION_ID') == props['InvocationID'], 'PROCESS_ENVIRONMENT')
        require(env.get('MEMORY_PRESSURE_WATCH') == '/sys/fs/cgroup/system.slice/deepseek-harness.service/memory.pressure'
                and base64.b64decode(env.get('MEMORY_PRESSURE_WRITE', ''), validate=True) == b'some 200000 2000000\0', 'PROCESS_PRESSURE')
        require(self.properties(['MemoryPressureWatch', 'MemoryPressureThresholdUSec']) ==
                {'MemoryPressureWatch': 'auto', 'MemoryPressureThresholdUSec': '200ms'}, 'PROCESS_PRESSURE')
        require(self.properties(keys) == props and self.smoke.process(pid) == process, 'PROCESS_RACE')
        self.sources(candidate)
        return {'invocation': props['InvocationID'], 'pid': pid, 'start': process[1], 'restarts': props['NRestarts']}

    def group(self):
        try:
            with open('/sys/fs/cgroup/system.slice/deepseek-harness.service/cgroup.procs', 'r', encoding='ascii') as stream:
                raw = stream.read(65537)
            require(len(raw) <= 65536, 'CGROUP_BOUND')
            return {int(x) for x in raw.split()}
        except FileNotFoundError:
            return set()

    def control(self, action):
        # --no-block avoids killing a systemctl waiter while its systemd job continues.
        self.smoke.command(['/usr/bin/systemctl', '--no-block', action, self.smoke.PILOT], 5)
        wait_job(lambda: self.properties(['Job']))

    def stopped(self):
        props = self.properties(['ActiveState', 'MainPID', 'Job'])
        require(props['ActiveState'] in {'inactive', 'failed'} and props['MainPID'] == props['Job'] == '0'
                and not self.group(), 'SERVICE_NOT_STOPPED')

    def stop_pilot(self):
        require(self.capture(False) == self.pilot and self.capture(False) == self.pilot, 'PILOT_CHANGED')
        self.stop_attempted = True
        self.control('stop')
        self.stopped()

    def old_baseline(self):
        self.stopped()
        self.old = self.smoke.snapshot(os.lstat(self.smoke.OLD))  # Root metadata only; never open/traverse.

    def create(self):
        self.stopped()
        self.sources(False)
        self.drop.create()

    def reload(self):
        self.stopped()
        self.sources(True, loaded=False)
        # Set before command: failed/timeout reload may have taken effect.
        self.loaded_candidate = True
        self.smoke.command(['/usr/bin/systemctl', 'daemon-reload'], 10)
        self.composition(True)

    def start_candidate(self):
        self.composition(True)
        self.stopped()
        restarts = self.properties(['NRestarts'])['NRestarts']
        self.started_candidate = True
        self.control('start')
        self.candidate = self.capture(True)
        require(self.candidate['restarts'] == restarts, 'AUTOMATIC_RESTART')

    def verify_candidate(self):
        current = self.capture(True)
        require_lineage(self.candidate, current, False, True)
        require(self.smoke.snapshot(os.lstat(self.smoke.OLD)) == self.old, 'OLD_ROOT_CHANGED')

    def network(self, candidate):
        owner = self.candidate if candidate else self.restored
        require(self.capture(candidate) == owner, 'INVOCATION_CHANGED')
        rows = [row for row in self.smoke.listeners(owner['pid']) if row[0].endswith((':0C08', ':0C09'))]
        require(len(rows) == 1 and rows[0][0] == '0100007F:0C08'
                and rows[0][1] in self.smoke.socket_inodes(owner['pid']), 'LISTENER_OWNERSHIP')
        require(self.smoke.command(['/usr/sbin/ufw', 'status', 'numbered'], 5) == self.firewall, 'FIREWALL_CHANGED')
        self.smoke.command(['/usr/bin/python3.12', '-I', '-c', HTTP], 5)
        require(self.capture(candidate) == owner, 'INVOCATION_CHANGED')

    def evidence(self):
        import resource
        original = resource.getrlimit(resource.RLIMIT_NOFILE)
        trust = self.smoke.Trusted()
        try:
            require(original[1] >= 4096, 'FD_HARD_LIMIT')
            resource.setrlimit(resource.RLIMIT_NOFILE, (4096, original[1]))
            for path, digest in self.smoke.SOURCE_PINS.items():
                require(sha(trust.read(path)) == digest, 'SOURCE_PIN')
            require(sha(trust.read('/usr/local/bin/dsh')) == '553ca65c989274e30583bfa56b08a3bca1a9b613e6647680f57558b19406dd14', 'WRAPPER_PIN')
            require(trust.digest_runtime(NODE) == 'bc17c508ffeed0ec622934f9b7fa72f8e78da65350e63c3eceb56fa688aa5e12', 'NODE_PIN')
            absence = self.smoke.absent_resolver_ancestors(trust)
            def resolver(anchor, dependency, timeout=5):
                end = time.monotonic() + timeout
                absence()
                paths = self.smoke.resolver_query(anchor, dependency, self.path, no_global=True,
                                                 timeout=min(5, end - time.monotonic()))
                absence()
                require(time.monotonic() <= end, 'RESOLVER_TIMEOUT')
                return paths
            rows, stats = [], {}
            links, canonical = self.smoke.closure(trust, stats, resolver, contained=True, export=rows)
            require(rows == self.graph['closure_records'], 'GRAPH_DRIFT')
            self.smoke.candidate_inventory(links, canonical, trust, expected_root=self.smoke.EXPECTED_BOOT_ROOT)
            absence()
            trust.verify()
        finally:
            try:
                trust.close()
            finally:
                resource.setrlimit(resource.RLIMIT_NOFILE, original)
                require(resource.getrlimit(resource.RLIMIT_NOFILE) == original, 'FD_RESTORE_FAILED')

    def accept(self):
        self.verify_candidate()
        self.network(True)
        self.verify_candidate()
        probe = self.smoke.PROBE.replace('127.0.0.1:3081', '127.0.0.1:3080')
        receipt = json.loads(self.smoke.command(['/usr/bin/python3.12', '-I', '-c', probe], 16))
        require(receipt == {'status': 'PASS', 'registered_route_count': 0, 'native_default_matches': True}, 'API_PROBE_FAILED')
        self.verify_candidate()
        self.evidence()
        self.verify_candidate()

    def rollback(self):
        signal.setitimer(signal.ITIMER_REAL, 330)  # Reserve independent restoration time.
        # Resolve the outstanding job first; never submit a competing job or cancel it.
        wait_job(lambda: self.properties(['Job']))
        # A failed daemon-reload can leave either reviewed composition loaded.
        mapping = self.properties(['DropInPaths'])['DropInPaths']
        require(mapping in {'', DROP_PATH}, 'ROLLBACK_SOURCE_AMBIGUOUS')
        self.loaded_candidate = mapping == DROP_PATH
        self.sources(self.loaded_candidate)
        state = self.properties(['ActiveState', 'MainPID'])
        if state['MainPID'] != '0' or state['ActiveState'] not in {'inactive', 'failed'}:
            current = self.capture(self.loaded_candidate)
            original = self.candidate if self.started_candidate else self.pilot
            if original is None:
                # A start error before first capture is controllable only through full candidate proof.
                require(self.started_candidate and self.loaded_candidate, 'ROLLBACK_LINEAGE')
            else:
                require_lineage(original, current, self.started_candidate and self.loaded_candidate, True)
            require(self.capture(self.loaded_candidate) == current, 'ROLLBACK_RESTART_RACE')
            self.control('stop')
        self.stopped()
        self.drop.remove()
        self.loaded_candidate = False
        self.smoke.command(['/usr/bin/systemctl', 'daemon-reload'], 10)
        self.composition(False)
        self.stopped()
        restarts = self.properties(['NRestarts'])['NRestarts']
        self.control('start')
        self.restored = self.capture(False)
        require(self.restored['restarts'] == restarts, 'ROLLBACK_AUTOMATIC_RESTART')
        self.verify_restored()

    def verify_restored(self):
        self.network(False)
        require(self.capture(False) == self.restored, 'ROLLBACK_INVOCATION_CHANGED')

    def channel_check(self):
        channel_clear()


def channel_clear():
    import select
    require(not select.select([0], [], [], 0)[0], 'PROTOCOL_EXTRA_OR_EOF')


def remote_line(timeout=30):
    import select
    end, raw = time.monotonic() + timeout, bytearray()
    while len(raw) <= 4096:
        remaining = end - time.monotonic()
        require(remaining > 0 and select.select([0], [], [], remaining)[0], 'PROTOCOL_TIMEOUT')
        value = os.read(0, 1)
        if not value:
            raise EOFError()
        if value == b'\n':
            return bytes(raw)
        raw.extend(value)
    raise Blocked('PROTOCOL_SIZE')


def remote_execution(nonce, bundle_pin):
    require(sys.platform == 'linux' and sys.version_info[:2] == (3, 12) and sys.flags.optimize == 0
            and os.geteuid() == os.getegid() == 0 and socket.gethostname() == 'deepseek-harness-01', 'REMOTE_IDENTITY')
    protocol, runtime = GateProtocol(nonce), NativeCutover(bundle_pin)
    def interrupted(number, frame):
        raise Interrupted('SIGNAL_' + {signal.SIGHUP: 'HUP', signal.SIGTERM: 'TERM',
                                      signal.SIGINT: 'INT', signal.SIGALRM: 'TIMEOUT'}[number])
    previous = {number: signal.signal(number, interrupted)
                for number in (signal.SIGHUP, signal.SIGTERM, signal.SIGINT, signal.SIGALRM)}
    def send(message):
        raw = json.dumps(message | {'nonce': nonce}, separators=(',', ':')).encode() + b'\n'
        require(len(raw) <= 4096, 'PROTOCOL_SIZE')
        # The parent drains stdout throughout rollback; any failed write is caught by run_cutover.
        import select
        end = time.monotonic() + 5
        while raw:
            remaining = end - time.monotonic()
            require(remaining > 0 and select.select([], [1], [], remaining)[1], 'OUTPUT_TIMEOUT')
            count = os.write(1, raw)
            require(count > 0, 'OUTPUT_FAILURE')
            raw = raw[count:]
    def gate(stage):
        channel_clear()
        send({'type': 'gate', 'stage': stage})
        protocol.accept(remote_line(), stage)
    result = None
    try:
        result = run_cutover(runtime, gate, lambda receipt: send({'type': 'receipt', 'result': receipt}))
        return 0 if result['status'] == 'SWITCH_ACCEPTED' else 1
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        if runtime.drop is not None:
            runtime.drop.close()
        for number, handler in previous.items():
            signal.signal(number, handler)


BOOTSTRAP = r'''
import hashlib,os,select,sys,time,types
end=time.monotonic()+30
def take(n):
 out=bytearray()
 while len(out)<n:
  left=end-time.monotonic()
  if left<=0 or not select.select([0],[],[],left)[0]: raise SystemExit(1)
  value=os.read(0,n-len(out))
  if not value: raise SystemExit(1)
  out.extend(value)
 return bytes(out)
count=int.from_bytes(take(4),'big')
if not 0<count<=1048576: raise SystemExit(1)
raw=take(count)
if hashlib.sha256(raw).hexdigest()!=HELPER_PIN: raise SystemExit(1)
module=types.ModuleType('vm105_frozen_cutover')
exec(compile(raw,'<frozen-cutover>','exec'),module.__dict__)
raise SystemExit(module.remote_execution(NONCE,BUNDLE_PIN))
'''


def execute(owner_ready, reviewed_sha256):
    """Explicit future entry; a hash assertion is not a substitute for actual owner authority."""
    require(owner_ready is True, 'OWNER_READINESS_REQUIRED')
    helper = pathlib.Path(__file__).read_bytes()
    require(len(helper) <= 1048576 and reviewed_sha256 == sha(helper), 'FROZEN_HELPER_REQUIRED')
    require(sys.platform == 'win32' and socket.gethostname().lower() == 'bell-pc2', 'LOCAL_IDENTITY')
    raw = inputs(pathlib.Path(__file__).resolve().parent.parent)
    import queue
    import secrets
    import threading
    nonce = secrets.token_hex(32)
    prefix = 'HELPER_PIN=' + repr(sha(helper)) + '\nNONCE=' + repr(nonce) + '\nBUNDLE_PIN=' + repr(sha(raw)) + '\n'
    code = 'import base64;exec(base64.b64decode(' + repr(base64.b64encode((prefix + BOOTSTRAP).encode()).decode()) + '))'
    args = ['C:/Windows/System32/OpenSSH/ssh.exe', '-T', '-i', 'C:/Users/chatc/.ssh/codex-prox01-vms-ed25519',
            '-o', 'BatchMode=yes', '-o', 'IdentitiesOnly=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=10',
            '-o', 'ServerAliveInterval=15', '-o', 'ServerAliveCountMax=3', 'dsh@192.168.1.139',
            '/usr/bin/sudo -n /usr/bin/python3.12 -I -c ' + shlex.quote(code)]
    require(len(subprocess.list2cmdline(args)) < 30000, 'SSH_COMMAND_SIZE')
    proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=0)
    end = time.monotonic() + 850  # 480 main + 330 rollback + startup/transport margin.
    output, writes = queue.Queue(maxsize=16), queue.Queue(maxsize=1)
    def reader():
        try:
            while True:
                line = proc.stdout.readline(4097)
                output.put(line, timeout=1)
                if not line or len(line) > 4096:
                    return
        except Exception:
            try: output.put_nowait(b'')
            except queue.Full: pass
    def writer():
        try:
            for data in (len(helper).to_bytes(4, 'big'), helper, len(raw).to_bytes(4, 'big'), raw):
                view = memoryview(data)
                while view:
                    count = proc.stdin.write(view)
                    require(count and count > 0, 'BOOTSTRAP_WRITE')
                    view = view[count:]
            writes.put(None)
        except Exception as error:
            writes.put(error)
    threading.Thread(target=reader, daemon=True).start()
    threading.Thread(target=writer, daemon=True).start()
    tunnel, stages, receipt, parent_error = None, [], None, None
    try:
        require(writes.get(timeout=30) is None, 'BOOTSTRAP_WRITE')
        while receipt is None:
            left = end - time.monotonic()
            require(left > 0, 'GLOBAL_DEADLINE')
            line = output.get(timeout=left)
            require(line and line.endswith(b'\n') and len(line) <= 4096, 'SSH_OUTPUT')
            message = strict_json(line)
            require(type(message) is dict and message.get('nonce') == nonce, 'PROTOCOL_NONCE')
            if message.get('type') == 'gate':
                require(set(message) == {'type', 'nonce', 'stage'}, 'PROTOCOL_SCHEMA')
                stage = message['stage']
                require((stage == 'PREFLIGHT' and not stages) or
                        (stage == 'CANDIDATE' and stages == ['PREFLIGHT']) or
                        (stage == 'ROLLBACK' and stages in (['PREFLIGHT'], ['PREFLIGHT', 'CANDIDATE'])), 'PROTOCOL_STAGE')
                stages.append(stage)
                ok = True
                try:
                    tunnel = external(tunnel)
                except Exception as error:
                    parent_error, ok = safe_error(error), False
                data = json.dumps({'nonce': nonce, 'stage': stage, 'ok': ok}, separators=(',', ':')).encode() + b'\n'
                require(proc.stdin.write(data) == len(data), 'PROTOCOL_WRITE')
            else:
                require(set(message) == {'type', 'nonce', 'result'} and message['type'] == 'receipt', 'PROTOCOL_SCHEMA')
                receipt = message['result']
                require(type(receipt) is dict and set(receipt) == {'status', 'gate', 'primary_error', 'rollback_error'}
                        and receipt['status'] in {'SWITCH_ACCEPTED', 'ROLLED_BACK', 'BLOCKED'}
                        and receipt['gate'] == 'CREDENTIAL_GATE'
                        and all(value is None or type(value) is str and re.fullmatch('[A-Z0-9_]{1,64}', value)
                                for value in (receipt['primary_error'], receipt['rollback_error'])), 'REMOTE_RECEIPT')
                require(receipt['status'] != 'SWITCH_ACCEPTED' or stages == ['PREFLIGHT', 'CANDIDATE']
                        and parent_error is None and receipt['primary_error'] is receipt['rollback_error'] is None, 'REMOTE_RECEIPT')
                require(receipt['status'] != 'ROLLED_BACK' or stages[-1:] == ['ROLLBACK']
                        and receipt['primary_error'] is not None and receipt['rollback_error'] is None, 'REMOTE_RECEIPT')
        code = proc.wait(timeout=max(1, end - time.monotonic()))
        require(code == (0 if receipt['status'] == 'SWITCH_ACCEPTED' else 1), 'SSH_EXIT')
        require(output.get(timeout=5) == b'', 'SSH_EXTRA_OUTPUT')
        receipt.update(ssh_exit=code, parent_error=parent_error)
        return receipt
    except (Exception, KeyboardInterrupt) as error:
        # EOF asks the remote to roll back; retain the SSH child for its entire reserve.
        try: proc.stdin.close()
        except OSError: pass
        try:
            proc.wait(timeout=max(1, end - time.monotonic()))
        except subprocess.TimeoutExpired:
            proc.terminate()  # Only after the whole main+rollback budget has expired.
            try: proc.wait(timeout=5)
            except subprocess.TimeoutExpired: pass
        return {'status': 'BLOCKED', 'primary_error': safe_error(error), 'rollback_error': 'RESTORATION_NOT_PROVEN',
                'ssh_exit': proc.poll(), 'gate': 'CREDENTIAL_GATE'}
    finally:
        proc.stdout.close()
        if not proc.stdin.closed:
            proc.stdin.close()


def inputs(root):
    paths = {'smoke': (root / 'scripts/Test-VM105CandidateSmoke.py', SMOKE_SHA),
             'graph': (root / 'docs/evidence/vm105-post-smoke-evidence-2026-09-09.json', GRAPH_SHA),
             'base': (root / 'docs/evidence/vm105-cutover-base-contract-2026-09-09.json', BASE_SHA)}
    bundle = {}
    for key, (path, expected) in paths.items():
        with path.open('rb') as stream:
            raw = stream.read(2097153)
        require(len(raw) <= 2097152 and sha(raw) == expected, 'INPUT_PIN')
        bundle[key] = base64.b64encode(raw).decode('ascii')
    raw = json.dumps(bundle, separators=(',', ':')).encode()
    require(len(raw) <= 4194304, 'BOOTSTRAP_SIZE')
    return raw


# This read-only program is passed in -c. Only the exact bounded bundle uses stdin.
# It imports the frozen verifier under a non-main name and calls verification functions;
# no consumed CLI mode or service action is dispatched.
REMOTE = r'''
import base64,hashlib,json,os,select,signal,sys,time,types
def need(ok,code):
 if not ok: raise ValueError(code)
def digest(raw): return hashlib.sha256(raw).hexdigest()
end=time.monotonic()+30
def take(n):
 out=bytearray()
 while len(out)<n:
  remaining=end-time.monotonic()
  need(remaining>0 and select.select([0],[],[],remaining)[0],'BOOTSTRAP_TIMEOUT')
  part=os.read(0,n-len(out));need(part,'BOOTSTRAP_EOF');out.extend(part)
 return bytes(out)
result={'status':'CUTOVER_PREFLIGHT_INCOMPLETE','mutation_entry':'READ_ONLY_PREFLIGHT'}
trust=None
try:
 count=int.from_bytes(take(4),'big');need(0<count<=4194304,'BOOTSTRAP_SIZE')
 raw=take(count);need(digest(raw)==BUNDLE_SHA,'BOOTSTRAP_PIN')
 bundle=json.loads(raw);need(type(bundle) is dict and set(bundle)=={'smoke','graph','base'},'BOOTSTRAP_SCHEMA')
 decoded={}
 for key,pin in PINS.items():
  data=base64.b64decode(bundle[key],validate=True)
  need(len(data)<=2097152 and digest(data)==pin,'INPUT_PIN');decoded[key]=data
 smoke=types.ModuleType('vm105_cutover_preflight_verifier')
 exec(compile(decoded['smoke'],'<frozen-verifier>','exec'),smoke.__dict__)
 graph=json.loads(decoded['graph']);base=json.loads(decoded['base'])
 need(graph['ssh_exit']==0 and graph['result']['status']=='POST_SMOKE_EVIDENCE_PASS','GRAPH_RECEIPT')
 need(base['ssh_exit']==0 and base['status']=='BASE_CONTRACT_SOURCE_AND_METADATA_PASS','BASE_RECEIPT')
 before=smoke.pilot_baseline()
 identity_keys=['InvocationID','MainPID','ExecMainStartTimestampMonotonic','NRestarts']
 initial_identity=smoke.show(smoke.PILOT,identity_keys)
 # This fresh preparation purpose is explicitly read-only. The verifier retains its
 # original source/manifest/edge/time/private-inventory/FD-restoration bounds.
 evidence=smoke.preflight_diagnostic(post_smoke=True)
 if evidence['status']!='POST_SMOKE_EVIDENCE_PASS':
  code=evidence.get('safe_code')
  if type(code) is str and code in smoke.DIAGNOSTIC_CODES: raise smoke.Blocked(code)
  need(False,'FRESH_GRAPH_VERIFICATION')
 need(evidence['closure_records']==graph['result']['closure_records'],'GRAPH_DRIFT')
 need(evidence['inventory']==graph['result']['inventory'],'INVENTORY_DRIFT')
 need(evidence['root_bytes_equal'] is True and evidence['root_sha256']==graph['result']['root_sha256']
      and evidence['original_input_sha256']==graph['result']['original_input_sha256'],'CANDIDATE_PIN_DRIFT')
 trust=smoke.Trusted()
 unit=smoke.PILOT;fragment='/etc/systemd/system/'+unit
 source=trust.read(fragment)
 need(source==base['source'].encode() and digest(source)=='5019702fa48ea6067de59b5071297f80450b90bd759a813236b71db7e4bf6ec0','BASE_SOURCE_DRIFT')
 smoke.reject_envfile_directives(source,sockets=True)
 excluded={'MainPID','NRestarts','ExecMainStartTimestamp','ActiveState','InvocationID'}
 expected={k:v for k,v in base['effective_properties'].items() if k not in excluded}
 properties=smoke.show(unit,list(expected)+['EnvironmentFiles','Sockets'])
 need(all(properties[k]==v for k,v in expected.items()),'BASE_EFFECTIVE_DRIFT')
 need(properties['EnvironmentFiles'] in {'',smoke.ENV_SOURCE_PROOF}
      and properties['Sockets'] in {'',smoke.SOCKET_SOURCE_PROOF},'ACTIVATION_SOURCE')
 need(smoke.show('deepseek-harness.socket',['LoadState'])=={'LoadState':'not-found'},'SOCKET_EXISTS')
 directory=fragment+'.d'
 try:
  directory_fd=trust.open(directory)
 except FileNotFoundError:
  directory_fd=None
 if directory_fd is not None:
  need(os.fstat(directory_fd).st_mode & 0o777==0o755 and not os.listdir(directory_fd),'DROPIN_DESTINATION')
 need(not os.path.lexists(directory+'/90-vm105-provider-profile.conf'),'DROPIN_DESTINATION')
 # Effective ExecStart must be the single source-pinned base wrapper command.
 exec_value=smoke.show(unit,['ExecStart'])['ExecStart']
 prefix='{ path=/usr/local/bin/dsh ; argv[]=/usr/local/bin/dsh web --host 127.0.0.1 --port 3080 ; ignore_errors=no ; '
 need(exec_value.startswith(prefix) and exec_value.endswith(' }') and exec_value.count('{')==exec_value.count('}')==1,'BASE_EXECSTART')
 pid=before[0]['MainPID'];actual=smoke.environment(pid)
 names={'HOME','DSH_HOME','PATH','USER','LOGNAME','SHELL','LANG','INVOCATION_ID','JOURNAL_STREAM','SYSTEMD_EXEC_PID',
        'PWD','MEMORY_PRESSURE_WATCH','MEMORY_PRESSURE_WRITE'}
 need(set(actual)<=names and actual.get('HOME')=='/home/dsh' and actual.get('DSH_HOME')==smoke.OLD
      and actual.get('PATH')==before[3],'PILOT_ENVIRONMENT')
 pressure=smoke.show(unit,['ControlGroup','MemoryPressureWatch','MemoryPressureThresholdUSec'])
 need(pressure=={'ControlGroup':'/system.slice/deepseek-harness.service','MemoryPressureWatch':'auto',
                 'MemoryPressureThresholdUSec':'200ms'},'PILOT_MEMORY_PRESSURE')
 need(actual.get('PWD')==base['effective_properties']['WorkingDirectory']
      and actual.get('MEMORY_PRESSURE_WATCH')=='/sys/fs/cgroup/system.slice/deepseek-harness.service/memory.pressure'
      and type(actual.get('MEMORY_PRESSURE_WRITE')) is str,'PILOT_MEMORY_PRESSURE')
 need(base64.b64decode(actual['MEMORY_PRESSURE_WRITE'],validate=True)==b'some 200000 2000000\0','PILOT_MEMORY_PRESSURE')
 firewall=smoke.command(['/usr/sbin/ufw','status','numbered'],5)
 need(firewall.startswith('Status: active\n') and not __import__('re').search(r'\b3080\b',firewall),'FIREWALL_POLICY')
 rows=[row for row in smoke.listeners(pid) if row[0].endswith((':0C08',':0C09'))]
 need(len(rows)==1 and rows[0][0]=='0100007F:0C08' and rows[0][1] in smoke.socket_inodes(pid),'PILOT_LISTENER')
 need(smoke.pilot_baseline()==before and smoke.show(unit,identity_keys)==initial_identity,'PILOT_CHANGED')
 need(smoke.show(unit,list(expected)+['EnvironmentFiles','Sockets'])==properties,'BASE_EFFECTIVE_DRIFT')
 trust.verify()
 result.update(status='CUTOVER_PREFLIGHT_PASS',closure_count=len(evidence['closure_records']),
  inventory_count=len(evidence['inventory']),root_bytes_equal=True,fd_restoration=evidence['fd_restoration'],
  base_source_equal=True,base_effective_equal=True,pilot_identity_unchanged=True,
  dropin_destination_absent=True,socket_absent=True,ufw_active=True,
  environment_file_proof=properties['EnvironmentFiles'] or 'EMITTED_EMPTY',
  socket_source_proof=properties['Sockets'] or 'EMITTED_EMPTY')
except Exception as error:
 code=error.args[0] if len(error.args)==1 else None
 if 'smoke' in globals() and type(error) is smoke.Blocked and type(code) is str and code in smoke.DIAGNOSTIC_CODES:
  result['error_code']=code
 else:
  result['error_code']=code if type(code) is str and code in PREFLIGHT_CODES else 'VERIFICATION_INCOMPLETE'
finally:
 if trust is not None:
  try: trust.close()
  except Exception: result.update(status='CUTOVER_PREFLIGHT_INCOMPLETE',error_code='FD_CLOSE_FAILED')
print(json.dumps(result,sort_keys=True))
sys.exit(0 if result['status']=='CUTOVER_PREFLIGHT_PASS' else 1)
'''

HTTP = r'''
import urllib.request
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*a,**k): return None
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
with opener.open('http://127.0.0.1:3080/',timeout=4) as response:
 assert response.status==200 and len(response.read(65537))<=65536
'''

TUNNEL = r'''
$ErrorActionPreference='Stop'
$t=Get-ScheduledTask -TaskName 'DeepSeek Harness VM105 SSH Tunnel'
if($t.State -ne 'Running' -or @($t.Actions).Count -ne 1){throw 'task'}
if($t.Actions[0].Execute -ine 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe' -or $t.Actions[0].Arguments -cne '-NoProfile -NonInteractive -WindowStyle Hidden -File C:\Users\chatc\Projects\DeepSeekHarnessRuntime\Start-VM105PilotTunnel.ps1'){throw 'action'}
$hasher=[System.Security.Cryptography.SHA256]::Create()
try{$scriptHash=[BitConverter]::ToString($hasher.ComputeHash([System.IO.File]::ReadAllBytes('C:\Users\chatc\Projects\DeepSeekHarnessRuntime\Start-VM105PilotTunnel.ps1'))).Replace('-','')}finally{$hasher.Dispose()}
if($scriptHash -cne '59E1E77B9C9C308E8DF89E2E8E2494B417FFA0BE255DF6CCF228B1EBF4FFF571'){throw 'script'}
$l=@(Get-NetTCPConnection -State Listen | Where-Object LocalPort -eq 3080)
if($l.Count -ne 1 -or $l[0].LocalAddress -ne '127.0.0.1'){throw 'listener'}
$p=Get-CimInstance Win32_Process -Filter ('ProcessId='+$l[0].OwningProcess)
$tail='-N -i C:/Users/chatc/.ssh/codex-prox01-vms-ed25519 -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o ExitOnForwardFailure=yes -o ConnectTimeout=10 -o ServerAliveInterval=15 -o ServerAliveCountMax=3 -L 127.0.0.1:3080:127.0.0.1:3080 dsh@192.168.1.139'
if($p.ExecutablePath -ine 'C:\Windows\System32\OpenSSH\ssh.exe' -or ($p.CommandLine.TrimEnd([char]' ') -ireplace '^"?C:\\Windows\\System32\\OpenSSH\\ssh.exe"?\s+','') -cne $tail){throw 'process'}
@{pid=[int]$p.ProcessId;creation=$p.CreationDate.ToUniversalTime().ToString('o')}|ConvertTo-Json -Compress
'''


def external(previous=None):
    start = time.monotonic()
    proc = subprocess.run(['C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe', '-NoProfile', '-NonInteractive',
                           '-Command', TUNNEL], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=5)
    require(proc.returncode == 0 and len(proc.stdout) <= 4096, 'TUNNEL_IDENTITY')
    identity = json.loads(proc.stdout)
    require(type(identity) is dict and set(identity) == {'pid', 'creation'} and type(identity['pid']) is int
            and identity['pid'] > 1 and type(identity['creation']) is str
            and re.fullmatch(r'[0-9T:Z.+-]{20,40}', identity['creation']), 'TUNNEL_IDENTITY')
    require(previous is None or identity == previous, 'TUNNEL_CHANGED')
    health = subprocess.run([sys.executable, '-I', '-c', HTTP], stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
    require(health.returncode == 0, 'TUNNEL_HTTP')
    try:
        connected = socket.create_connection(('192.168.1.139', 3080), timeout=5)
    except (ConnectionRefusedError, TimeoutError, socket.timeout):
        pass
    else:
        connected.close()
        raise Blocked('LAN_ACCESSIBLE')
    require(time.monotonic() - start <= 20, 'EXTERNAL_TIMEOUT')
    return identity


def preflight():
    require(sys.platform == 'win32' and socket.gethostname().lower() == 'bell-pc2', 'LOCAL_IDENTITY')
    raw = inputs(pathlib.Path(__file__).resolve().parent.parent)
    prefix = ('BUNDLE_SHA=' + repr(sha(raw)) + '\nPINS=' + repr({'smoke': SMOKE_SHA, 'graph': GRAPH_SHA, 'base': BASE_SHA})
              + '\nPREFLIGHT_CODES=' + repr(sorted(PREFLIGHT_CODES)) + '\n')
    code = 'import base64;exec(base64.b64decode(' + repr(base64.b64encode((prefix + REMOTE).encode()).decode()) + '))'
    command = '/usr/bin/sudo -n /usr/bin/python3.12 -I -c ' + shlex.quote(code)
    args = ['C:/Windows/System32/OpenSSH/ssh.exe', '-T', '-i', 'C:/Users/chatc/.ssh/codex-prox01-vms-ed25519',
            '-o', 'BatchMode=yes', '-o', 'IdentitiesOnly=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=10',
            'dsh@192.168.1.139', command]
    require(len(subprocess.list2cmdline(args)) < 30000, 'SSH_COMMAND_SIZE')
    before = external()
    proc = subprocess.run(args, input=len(raw).to_bytes(4, 'big') + raw, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=150)
    require(len(proc.stdout) <= 16384, 'SSH_OR_REMOTE_FAILURE')
    result = json.loads(proc.stdout)
    if proc.returncode != 0:
        require(type(result) is dict and set(result) == {'status', 'mutation_entry', 'error_code'}
                and result['status'] == 'CUTOVER_PREFLIGHT_INCOMPLETE' and result['mutation_entry'] == 'READ_ONLY_PREFLIGHT'
                and type(result['error_code']) is str and re.fullmatch('[A-Z0-9_]{1,64}', result['error_code']), 'REMOTE_RECEIPT')
        result['ssh_exit'] = proc.returncode
        return result
    require(type(result) is dict and result.get('status') == 'CUTOVER_PREFLIGHT_PASS'
            and result.get('mutation_entry') == 'READ_ONLY_PREFLIGHT', 'REMOTE_RECEIPT')
    external(before)
    result.update(parent_access_before_after=True, candidate_cutover='OWNER_READINESS_REQUIRED',
                  proposed_dropin_sha256=sha(DROP), ssh_exit=proc.returncode)
    return result


def self_test():
    import ast
    from unittest.mock import patch
    # The shipped remote program has no path to consumed apply modes or unit controls.
    tree = ast.parse(REMOTE)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            require(node.func.attr not in {'apply', 'apply_v2', 'unlink', 'mkdir', 'rmdir', 'rename', 'write'}, 'SELF_TEST_MUTATION')
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            require(node.value not in {'start', 'stop', 'restart', 'daemon-reload'}, 'SELF_TEST_MUTATION')
    # Execute the exact shipped listener predicate against host-namespace fixtures.
    listener_lines = REMOTE[REMOTE.index(' rows=[row for row in smoke.listeners(pid)'):REMOTE.index(" need(smoke.pilot_baseline()==before")]
    from types import SimpleNamespace
    for rows, allowed in (([('00000000:0016', 'ssh'), ('0100007F:0C08', 'web')], True),
                          ([('00000000:0016', 'ssh'), ('00000000:0C08', 'web')], False),
                          ([('0100007F:0C08', 'web'), ('0100007F:0C09', 'extra')], False),
                          ([('0100007F:0C08', 'other-owner')], False)):
        fixture = {'pid': '123', 'smoke': SimpleNamespace(listeners=lambda _: rows, socket_inodes=lambda _: {'web'}),
                   'need': require}
        try:
            exec(compile('\n'.join(line[1:] for line in listener_lines.splitlines()), '<listener-fixture>', 'exec'), fixture)
        except Blocked:
            require(not allowed, 'SELF_TEST_NAMESPACE_LISTENER')
        else:
            require(allowed, 'SELF_TEST_NAMESPACE_LISTENER')
    environment_lines = REMOTE[REMOTE.index(' names={'):REMOTE.index(' firewall=')]
    import types
    env_good = {'HOME': '/home/dsh', 'DSH_HOME': '/home/dsh/.dsh', 'PATH': '/usr/bin', 'PWD': '/srv/dsh/workspaces',
                'MEMORY_PRESSURE_WATCH': '/sys/fs/cgroup/system.slice/deepseek-harness.service/memory.pressure',
                'MEMORY_PRESSURE_WRITE': base64.b64encode(b'some 200000 2000000\0').decode()}
    for change in ({}, {'PWD': '/wrong'}, {'MEMORY_PRESSURE_WATCH': '/sys/fs/cgroup/other/memory.pressure'},
                   {'MEMORY_PRESSURE_WRITE': base64.b64encode(b'some 200001 2000000\0').decode()}, {'UNKNOWN': 'x'}):
        pressure = {'ControlGroup': '/system.slice/deepseek-harness.service', 'MemoryPressureWatch': 'auto',
                    'MemoryPressureThresholdUSec': '200ms'}
        fixture = {'actual': env_good | change, 'before': (None, None, None, '/usr/bin'), 'unit': 'deepseek-harness.service',
                   'base': {'effective_properties': {'WorkingDirectory': '/srv/dsh/workspaces'}},
                   'smoke': types.SimpleNamespace(OLD='/home/dsh/.dsh', show=lambda *a: pressure), 'need': require, 'base64': base64}
        try:
            exec(compile('\n'.join(line[1:] for line in environment_lines.splitlines()), '<environment-fixture>', 'exec'), fixture)
        except Blocked:
            require(bool(change), 'SELF_TEST_MEMORY_PRESSURE')
        else:
            require(not change, 'SELF_TEST_MEMORY_PRESSURE')
    with patch.object(subprocess, 'run', side_effect=AssertionError('must not execute')):
        require(sha(DROP) == '498ffcd058b856e054e8b144292d1831b0a3f4c4004bb0ae6d94a6e21ee0ea0a', 'SELF_TEST_DROP_HASH')
    from types import SimpleNamespace
    identity = {'pid': 123, 'creation': '2026-09-08T20:00:00.0000000Z'}
    for variant in ('pass', 'changed', 'lan', 'task'):
        tunnel = SimpleNamespace(returncode=1 if variant == 'task' else 0, stdout=json.dumps(identity).encode())
        health = SimpleNamespace(returncode=0)
        connection = SimpleNamespace(close=lambda: None)
        with patch.object(subprocess, 'run', side_effect=[tunnel, health]), \
             patch.object(socket, 'create_connection', side_effect=None if variant == 'lan' else ConnectionRefusedError(),
                          return_value=connection):
            try:
                observed = external({'pid': 124, 'creation': identity['creation']} if variant == 'changed' else None)
            except Blocked as error:
                require(error.args == ({'changed': 'TUNNEL_CHANGED', 'lan': 'LAN_ACCESSIBLE', 'task': 'TUNNEL_IDENTITY'}[variant],),
                        'SELF_TEST_EXTERNAL_GUARD')
            else:
                require(variant == 'pass' and observed == identity, 'SELF_TEST_EXTERNAL_ACCEPTANCE')
    with patch.object(pathlib.Path, 'open') as opened:
        opened.return_value.__enter__.return_value.read.return_value = b'wrong pinned input'
        try:
            inputs(pathlib.Path('.'))
        except Blocked as error:
            require(error.args == ('INPUT_PIN',), 'SELF_TEST_INPUT_PIN')
        else:
            raise Blocked('SELF_TEST_INPUT_PIN_ACCEPTED')
    require("$p.CommandLine.TrimEnd([char]' ') -ireplace" in TUNNEL, 'SELF_TEST_COMMAND_TRAILING_SPACE')
    require('Get-FileHash' not in TUNNEL and '[System.Security.Cryptography.SHA256]::Create()' in TUNNEL
            and '[System.IO.File]::ReadAllBytes(' in TUNNEL and 'finally{$hasher.Dispose()}' in TUNNEL
            and 'Import-Module' not in TUNNEL and 'PSModulePath' not in TUNNEL, 'SELF_TEST_NATIVE_HASH')
    compile(REMOTE, '<remote>', 'exec')
    compile(HTTP, '<http>', 'exec')
    return {'status': 'SELF_TEST_PASS', 'mutation_entry': 'READ_ONLY_PREFLIGHT'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--self-test', action='store_true')
    modes.add_argument('--preflight', action='store_true')
    modes.add_argument('--execute', action='store_true')
    parser.add_argument('--owner-ready', action='store_true')
    parser.add_argument('--reviewed-sha256')
    args = parser.parse_args()  # --apply is deliberately unsupported.
    try:
        require(args.execute or not args.owner_ready and args.reviewed_sha256 is None, 'EXECUTION_GATE_SCOPE')
        result = execute(args.owner_ready, args.reviewed_sha256) if args.execute else self_test() if args.self_test else preflight() if args.preflight else {
            'status': 'CONTRACT_ONLY', 'mutation_entry': 'EXPLICIT_OWNER_AND_FROZEN_HELPER_GATE',
            'preflight_requires': '--preflight', 'proposed_dropin_sha256': sha(DROP)}
    except Exception as error:
        allowed = {'INPUT_PIN', 'BOOTSTRAP_SIZE', 'TUNNEL_IDENTITY', 'TUNNEL_CHANGED', 'TUNNEL_HTTP', 'LAN_ACCESSIBLE',
                   'EXTERNAL_TIMEOUT', 'LOCAL_IDENTITY', 'SSH_COMMAND_SIZE', 'SSH_OR_REMOTE_FAILURE', 'REMOTE_RECEIPT',
                   'OWNER_READINESS_REQUIRED', 'FROZEN_HELPER_REQUIRED', 'EXECUTION_GATE_SCOPE'}
        code = error.args[0] if len(error.args) == 1 else None
        result = {'status': 'BLOCKED' if args.execute else 'CUTOVER_PREFLIGHT_INCOMPLETE', 'mutation_entry': 'EXPLICIT_OWNER_AND_FROZEN_HELPER_GATE',
                  'error_code': code if isinstance(code, str) and code in allowed else 'VERIFICATION_INCOMPLETE'}
    print(json.dumps(result, sort_keys=True))
    sys.exit(0 if result['status'] in {'CONTRACT_ONLY', 'SELF_TEST_PASS', 'CUTOVER_PREFLIGHT_PASS', 'SWITCH_ACCEPTED'} else 1)
