"""Offline adversarial checks. Never contacts VM105 or executes service controls."""
import importlib.util
import contextlib
import io
import json
import pathlib
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('cutover', pathlib.Path(__file__).with_name('Invoke-VM105CandidateCutover.py'))
cut = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cut)


class Runtime:
    """Only the external service boundary is simulated; the orchestration is real."""
    def __init__(self, failure=None):
        self.events = []
        self.failure = failure

    def step(self, name):
        self.events.append(name)
        if name == self.failure:
            raise cut.Blocked('FIXTURE_FAILURE')

    def preflight(self): self.step('preflight')
    def stop_pilot(self): self.step('stop')
    def old_baseline(self): self.step('old_baseline')
    def create(self): self.step('create')
    def reload(self): self.step('reload')
    def start_candidate(self): self.step('start')
    def accept(self): self.step('accept')
    def verify_candidate(self): self.step('verify_candidate')
    def rollback(self): self.step('rollback')
    def verify_restored(self): self.step('verify_restored')
    def channel_check(self): self.step('channel_check')


class FileSystem:
    """Linux syscall boundary fixture; does not claim Linux kernel validation."""
    def __init__(self, failure):
        self.failure, self.exists, self.data, self.inode = failure, False, b'', 30
        self.mode, self.writes = 0o100644, 0
        self.directory_exists, self.directory_mode, self.mask = True, 0o40755, 0o077

    def metadata(self, fd):
        from types import SimpleNamespace
        return SimpleNamespace(st_dev=1, st_ino=self.inode if fd == 12 else fd,
            st_mode=self.mode if fd == 12 else self.directory_mode if fd == 11 else 0o40755, st_uid=0, st_gid=0,
            st_nlink=1 if fd == 12 else 2 + int(fd == 10 and self.directory_exists), st_size=len(self.data) if fd == 12 else 0,
            st_mtime_ns=1, st_ctime_ns=1)

    def open(self, name, flags, mode, dir_fd):
        if self.exists: raise FileExistsError()
        assert flags & cut.os.O_EXCL and flags & cut.os.O_CREAT
        self.exists = True
        return 12

    def write(self, fd, data):
        self.writes += 1
        if self.failure == 'write' and self.writes == 2: raise OSError()
        part = data[:5] if self.failure == 'write' else data
        self.data += part
        return len(part)

    def fsync(self, fd):
        if self.failure == 'fsync':
            self.failure = None
            raise OSError()

    def unlink(self, name, dir_fd): self.exists = False

    def umask(self, value):
        old, self.mask = self.mask, value
        return old

    def mkdir(self, name, mode, dir_fd):
        self.directory_exists, self.directory_mode = True, 0o40000 | (mode & ~self.mask)

    @contextlib.contextmanager
    def installed(self):
        from types import SimpleNamespace
        fixture = self
        class Trust:
            def __init__(self): self.held = {}
            def open(self, path):
                if path == cut.DIRECTORY and not fixture.directory_exists: raise FileNotFoundError()
                fd = 11 if path == cut.DIRECTORY else 10
                self.held[path] = (fd, snapshot(fixture.metadata(fd)), False)
                return fd
            def verify(self): pass
            def close(self): pass
        def snapshot(s): return cut.identity(s) + (s.st_size, s.st_mtime_ns, s.st_ctime_ns)
        smoke = SimpleNamespace(Trusted=Trust, snapshot=snapshot, FORBIDDEN=set(), bounded_read=lambda *a: self.data)
        replacements = {'open': self.open, 'fstat': self.metadata, 'lstat': lambda p: self.metadata(11 if p == cut.DIRECTORY else 10),
            'stat': lambda *a, **k: self.metadata(12), 'listxattr': lambda *a: [],
            'listdir': lambda *a: [cut.DROP_NAME] if self.exists else [], 'fchmod': lambda *a: None,
            'write': self.write, 'fsync': self.fsync, 'lseek': lambda *a: None,
            'unlink': self.unlink, 'close': lambda *a: None, 'umask': self.umask, 'mkdir': self.mkdir}
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(cut, 'file_boundary', contextlib.nullcontext))
            stack.enter_context(patch.object(cut.OwnedDrop, 'mount_snapshot', return_value=b'mount'))
            for key, value in replacements.items(): stack.enter_context(patch.object(cut.os, key, value, create=True))
            for key in ('O_NOFOLLOW', 'O_CLOEXEC'): stack.enter_context(patch.object(cut.os, key, 0, create=True))
            yield cut.OwnedDrop(smoke)


class CutoverTests(unittest.TestCase):
    def test_execution_engine_is_present(self):
        self.assertTrue(callable(getattr(cut, 'run_cutover', None)), 'bounded execution engine is missing')

    def test_success_and_every_mutation_failure_have_one_rollback(self):
        if not hasattr(cut, 'run_cutover'): self.skipTest('engine missing')
        for failure in (None, 'preflight', 'stop', 'old_baseline', 'create', 'reload', 'start', 'accept', 'verify_candidate'):
            with self.subTest(failure=failure):
                runtime, messages, stages = Runtime(failure), [], []
                result = cut.run_cutover(runtime, stages.append, messages.append)
                self.assertEqual(result['status'], 'SWITCH_ACCEPTED' if failure is None else
                                 'BLOCKED' if failure == 'preflight' else 'ROLLED_BACK')
                self.assertEqual(runtime.events.count('rollback'), int(failure not in (None, 'preflight')))
                self.assertLessEqual(runtime.events.count('stop'), 1)
                self.assertLessEqual(runtime.events.count('start'), 1)
                if failure is None:
                    self.assertEqual(stages, ['PREFLIGHT', 'CANDIDATE'])
                elif failure != 'preflight':
                    self.assertEqual(stages[-1], 'ROLLBACK')

    def test_parent_failure_signal_and_receipt_pipe_failure_restore(self):
        if not hasattr(cut, 'run_cutover'): self.skipTest('engine missing')
        for boundary in ('PREFLIGHT', 'CANDIDATE', 'emit', 'signal'):
            runtime = Runtime()
            def gate(stage):
                if stage == boundary: raise EOFError()
                if boundary == 'signal' and stage == 'CANDIDATE': raise cut.Interrupted('SIGNAL_TERM')
            def emit(result):
                if boundary == 'emit': raise BrokenPipeError()
            result = cut.run_cutover(runtime, gate, emit)
            self.assertEqual(runtime.events.count('rollback'), int(boundary != 'PREFLIGHT'))
            self.assertNotEqual(result['status'], 'SWITCH_ACCEPTED')
            if boundary == 'emit': self.assertEqual(result['status'], 'BLOCKED')

    def test_rollback_failure_keeps_primary_and_never_retries(self):
        if not hasattr(cut, 'run_cutover'): self.skipTest('engine missing')
        runtime = Runtime('rollback')
        def gate(stage):
            if stage == 'CANDIDATE': raise TimeoutError()
        result = cut.run_cutover(runtime, gate, lambda _: None)
        self.assertEqual(result['status'], 'BLOCKED')
        self.assertEqual(result['primary_error'], 'TIMEOUT')
        self.assertEqual(result['rollback_error'], 'FIXTURE_FAILURE')
        self.assertEqual(runtime.events.count('rollback'), 1)

    def test_protocol_rejects_wrong_stage_nonce_extra_duplicate_replay_and_eof(self):
        self.assertTrue(callable(getattr(cut, 'GateProtocol', None)), 'finite nonce protocol is missing')
        nonce = 'a' * 64
        good = {'nonce': nonce, 'stage': 'PREFLIGHT', 'ok': True}
        for raw in (b'', b'{', json.dumps(good | {'extra': 1}).encode(),
                    json.dumps(good | {'stage': 'CANDIDATE'}).encode(),
                    json.dumps(good | {'nonce': 'b' * 64}).encode(),
                    json.dumps(good | {'ok': 1}).encode(),
                    b'{"nonce":"' + nonce.encode() + b'","stage":"PREFLIGHT","ok":false,"ok":true}'):
            with self.subTest(raw=raw):
                protocol = cut.GateProtocol(nonce)
                with self.assertRaises(cut.Blocked): protocol.accept(raw, 'PREFLIGHT')
        protocol = cut.GateProtocol(nonce)
        protocol.accept(json.dumps(good).encode(), 'PREFLIGHT')
        with self.assertRaises(cut.Blocked): protocol.accept(json.dumps(good).encode(), 'PREFLIGHT')

    def test_no_arguments_remain_nonmutating(self):
        import subprocess, sys
        result = subprocess.run([sys.executable, '-B', str(pathlib.Path(cut.__file__))],
                                capture_output=True, timeout=5)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)['status'], 'CONTRACT_ONLY')

    def test_service_job_waits_for_ninety_second_policy_without_resubmission(self):
        self.assertTrue(callable(getattr(cut, 'wait_job', None)), 'bounded outstanding-job handling is missing')
        clock = [0]
        def pause(seconds): clock[0] += seconds
        def show(): return {'Job': '17' if clock[0] < 90 else '0'}
        with patch.object(cut.time, 'monotonic', side_effect=lambda: clock[0]), patch.object(cut.time, 'sleep', side_effect=pause):
            cut.wait_job(show)
        self.assertGreaterEqual(clock[0], 90)
        clock[0] = 0
        with patch.object(cut.time, 'monotonic', side_effect=lambda: clock[0]), patch.object(cut.time, 'sleep', side_effect=pause):
            with self.assertRaises(cut.Blocked): cut.wait_job(lambda: {'Job': '17'})
        self.assertLessEqual(clock[0], 96)

    def test_restart_is_rejected_for_acceptance_and_replacement_requires_full_lineage(self):
        self.assertTrue(callable(getattr(cut, 'require_lineage', None)), 'invocation-lineage guard is missing')
        original = {'invocation': 'a' * 32, 'pid': '41', 'start': '100', 'restarts': '0'}
        replacement = {'invocation': 'b' * 32, 'pid': '42', 'start': '110', 'restarts': '1'}
        cut.require_lineage(original, original, replacement_allowed=False, composition_proven=True)
        with self.assertRaises(cut.Blocked):
            cut.require_lineage(original, replacement, replacement_allowed=False, composition_proven=True)
        with self.assertRaises(cut.Blocked):
            cut.require_lineage(original, replacement, replacement_allowed=True, composition_proven=False)
        cut.require_lineage(original, replacement, replacement_allowed=True, composition_proven=True)
        with self.assertRaises(cut.Blocked):
            cut.require_lineage(original, replacement | {'restarts': '0'}, replacement_allowed=True, composition_proven=True)

    def test_partial_write_cleanup_rejects_changed_inode_or_unwritten_bytes(self):
        self.assertTrue(callable(getattr(cut, 'owned_matches', None)), 'owned partial-file identity guard is missing')
        identity = (2049, 100, 0o100644, 0, 0, 1)
        self.assertTrue(cut.owned_matches(identity, identity, b'[Service]', b'[Service]'))
        self.assertFalse(cut.owned_matches(identity, (2049, 101, 0o100644, 0, 0, 1), b'[Service]', b'[Service]'))
        self.assertFalse(cut.owned_matches(identity, identity, b'[Service]x', b'[Service]'))

    def test_parent_receipt_schema_and_execution_release_gate(self):
        self.assertTrue(callable(getattr(cut, 'execute', None)), 'gated parent SSH entry is missing')
        with patch.object(cut.subprocess, 'Popen', side_effect=AssertionError('must not contact VM')):
            with self.assertRaises(cut.Blocked): cut.execute(False, '0' * 64)
            with self.assertRaises(cut.Blocked): cut.execute(True, '0' * 64)

    def test_activation_properties_are_separate_and_emitted_markers_are_rejected(self):
        native = cut.NativeCutover('0' * 64)
        from types import SimpleNamespace
        native.loaded_candidate = True
        source_calls = []
        native.sources = source_calls.append
        native.smoke = SimpleNamespace(command=lambda *a: 'TriggeredBy=\n', PILOT='deepseek-harness.service',
            ENV_SOURCE_PROOF='ABSENT_SOURCE_VERIFIED', SOCKET_SOURCE_PROOF='SOCKETS_ABSENT_SOURCE_VERIFIED')
        result = native.properties(['EnvironmentFiles', 'Sockets', 'TriggeredBy'])
        self.assertEqual(result, {'EnvironmentFiles': 'ABSENT_SOURCE_VERIFIED',
                                'Sockets': 'SOCKETS_ABSENT_SOURCE_VERIFIED', 'TriggeredBy': ''})
        self.assertEqual(source_calls, [True])
        native.smoke.command = lambda *a: 'EnvironmentFiles=\nSockets=SOCKETS_ABSENT_SOURCE_VERIFIED\n'
        with self.assertRaises(cut.Blocked): native.properties(['EnvironmentFiles', 'Sockets'])

    def test_real_owned_file_algorithm_cleans_partial_and_fsync_failures_but_preserves_replacements(self):
        for failure in ('write', 'fsync', None):
            fixture = FileSystem(failure)
            with fixture.installed() as owned:
                if failure:
                    with self.assertRaises(OSError): owned.create()
                else:
                    owned.create()
                self.assertTrue(fixture.exists)
                self.assertEqual(fixture.data, b'[Serv' if failure == 'write' else cut.DROP)
                owned.remove()
                self.assertFalse(fixture.exists)
                self.assertIsNone(owned.fd)
        fixture = FileSystem(None)
        with fixture.installed() as owned:
            owned.create()
            fixture.inode += 1
            with self.assertRaises(cut.Blocked): owned.remove()
            self.assertTrue(fixture.exists)

    def test_precontrol_restart_race_causes_no_stop_attempt(self):
        native = cut.NativeCutover('0' * 64)
        native.pilot = {'invocation': 'a'}
        controls = []
        native.control = controls.append
        captures = iter([native.pilot, {'invocation': 'b'}])
        native.capture = lambda _: next(captures)
        with self.assertRaises(cut.Blocked): native.stop_pilot()
        self.assertEqual(controls, [])
        self.assertFalse(native.stop_attempted)

    def test_new_directory_has_exact_mode_and_rollback_leaves_it(self):
        fixture = FileSystem(None)
        fixture.directory_exists = False
        with fixture.installed() as owned:
            owned.create()
            self.assertEqual(fixture.directory_mode, 0o40755)
            self.assertEqual(fixture.mask, 0o077)
            self.assertTrue(owned.created_directory)
            owned.remove()
            self.assertTrue(fixture.directory_exists)

    def test_parent_wire_acceptance_requires_nonce_stages_schema_and_checked_exit(self):
        from types import SimpleNamespace
        import secrets
        nonce = 'f' * 64
        helper_pin = cut.sha(pathlib.Path(cut.__file__).read_bytes())
        for variant in ('pass', 'wrong_nonce', 'exit', 'extra_output', 'extra_field'):
            gate = lambda stage: {'nonce': nonce, 'type': 'gate', 'stage': stage}
            receipt = {'status': 'SWITCH_ACCEPTED', 'gate': 'CREDENTIAL_GATE', 'primary_error': None, 'rollback_error': None}
            last = {'nonce': nonce, 'type': 'receipt', 'result': receipt}
            if variant == 'wrong_nonce': last['nonce'] = 'a' * 64
            if variant == 'extra_field': receipt['secret'] = 'must never be emitted'
            lines = [gate('PREFLIGHT'), gate('CANDIDATE'), last]
            wire = b''.join(json.dumps(line).encode() + b'\n' for line in lines)
            if variant == 'extra_output': wire += b'unexpected\n'
            proc = SimpleNamespace(stdin=io.BytesIO(), stdout=io.BytesIO(wire),
                wait=lambda **k: 2 if variant == 'exit' else 0, poll=lambda: 0, terminate=lambda: None)
            with patch.object(cut.subprocess, 'Popen', return_value=proc), \
                 patch.object(cut, 'inputs', return_value=b'{}'), \
                 patch.object(cut.sys, 'platform', 'win32'), \
                 patch.object(cut.socket, 'gethostname', return_value='bell-pc2'), \
                 patch.object(secrets, 'token_hex', return_value=nonce), \
                 patch.object(cut, 'external', return_value={'pid': 1, 'creation': 'fixture'}):
                result = cut.execute(True, helper_pin)
            self.assertEqual(result['status'], 'SWITCH_ACCEPTED' if variant == 'pass' else 'BLOCKED')
            self.assertNotIn('secret', json.dumps(result))

    def test_remote_reader_is_bounded_for_timeout_eof_and_oversize(self):
        import select
        for variant in ('timeout', 'eof', 'size'):
            with patch.object(select, 'select', return_value=([] if variant == 'timeout' else [0], [], [])), \
                 patch.object(cut.os, 'read', return_value=b'' if variant == 'eof' else b'x'):
                with self.assertRaises((cut.Blocked, EOFError)): cut.remote_line()
        compile(cut.BOOTSTRAP, '<offline-bootstrap>', 'exec')

    def test_post_stop_hup_term_and_timeout_each_take_single_rollback(self):
        for code in ('SIGNAL_HUP', 'SIGNAL_TERM', 'SIGNAL_TIMEOUT'):
            runtime = Runtime()
            def gate(stage):
                if stage == 'CANDIDATE': raise cut.Interrupted(code)
            result = cut.run_cutover(runtime, gate, lambda _: None)
            self.assertEqual(result['status'], 'ROLLED_BACK')
            self.assertEqual(result['primary_error'], code)
            self.assertEqual(runtime.events.count('rollback'), 1)

    def test_rollback_recaptures_replacement_and_refuses_restart_race(self):
        native = cut.NativeCutover('0' * 64)
        native.started_candidate, native.loaded_candidate = True, True
        native.candidate = {'invocation': 'a' * 32, 'pid': '41', 'start': '100', 'restarts': '0'}
        replacement = {'invocation': 'b' * 32, 'pid': '42', 'start': '110', 'restarts': '1'}
        third = {'invocation': 'c' * 32, 'pid': '43', 'start': '120', 'restarts': '2'}
        controls = []
        native.control = controls.append
        native.sources = lambda *a: None
        def props(keys):
            return {key: {'Job': '0', 'DropInPaths': cut.DROP_PATH, 'ActiveState': 'active', 'MainPID': '42'}[key] for key in keys}
        native.properties = props
        captures = iter([replacement, third])
        native.capture = lambda _: next(captures)
        with patch.object(cut.signal, 'setitimer', create=True), patch.object(cut.signal, 'ITIMER_REAL', 0, create=True):
            with self.assertRaises(cut.Blocked): native.rollback()
        self.assertEqual(controls, [])

    def test_final_channel_check_rejects_extra_frame_and_late_parent_stdin_close(self):
        import select, socket
        for boundary in ('candidate_extra', 'candidate_eof', 'rollback_extra', 'rollback_eof'):
            with self.subTest(boundary=boundary):
                parent_input, remote_input = socket.socketpair()
                stdout = io.BytesIO()  # Parent deliberately retains stdout after closing stdin.
                runtime, nonce = Runtime(), 'e' * 64
                protocol = cut.GateProtocol(nonce)
                real_select = select.select
                def poll(read, write, error, timeout):
                    ready, _, _ = real_select([remote_input] if read else [], [], [], timeout)
                    return ([0] if ready else [], [], [])
                def gate(stage):
                    if stage == 'CANDIDATE' and boundary.startswith('rollback'):
                        raise cut.Blocked('FIXTURE_FAILURE')
                    if stage == 'ROLLBACK' and boundary.startswith('candidate'):
                        # The failed final check must still run VM restoration even though the channel is bad.
                        raise EOFError()
                    reply = json.dumps({'nonce': nonce, 'stage': stage, 'ok': True}).encode() + b'\n'
                    if stage == ('CANDIDATE' if boundary.startswith('candidate') else 'ROLLBACK') and boundary.endswith('extra'):
                        reply += reply
                    parent_input.sendall(reply)
                    protocol.accept(cut.remote_line(), stage)
                def close_parent_input():
                    parent_input.shutdown(socket.SHUT_WR)
                if boundary == 'candidate_eof': runtime.verify_candidate = close_parent_input
                if boundary == 'rollback_eof': runtime.verify_restored = close_parent_input
                runtime.channel_check = lambda: cut.channel_clear()
                try:
                    with patch.object(select, 'select', side_effect=poll), \
                         patch.object(cut.os, 'read', side_effect=lambda fd, count: remote_input.recv(count)):
                        result = cut.run_cutover(runtime, gate, lambda value: stdout.write(json.dumps(value).encode()))
                    self.assertEqual(result['status'], 'BLOCKED')
                    self.assertEqual(runtime.events.count('rollback'), 1)
                    self.assertFalse(stdout.closed)
                    self.assertNotIn(b'SWITCH_ACCEPTED', stdout.getvalue())
                    self.assertNotIn(b'ROLLED_BACK', stdout.getvalue())
                finally:
                    parent_input.close()
                    remote_input.close()

    def test_actual_frozen_verifier_errors_preserve_only_enumerated_primary_and_rollback_codes(self):
        import types
        raw = pathlib.Path(cut.__file__).with_name('Test-VM105CandidateSmoke.py').read_bytes()
        self.assertEqual(cut.sha(raw), cut.SMOKE_SHA)
        smoke = types.ModuleType('fixture_frozen_smoke')
        exec(compile(raw, '<actual-frozen-verifier>', 'exec'), smoke.__dict__)
        self.assertIsNot(smoke.Blocked, cut.Blocked)
        cases = [(smoke.Blocked(code), code) for code in ('COMMAND_TIMEOUT', 'CANDIDATE_PIN', 'TRUST_METADATA_DRIFT')]
        cases += [(smoke.Blocked('PRIVATE_VALUE_NOT_ALLOWLISTED'), 'VERIFICATION_INCOMPLETE'),
                  (smoke.Blocked('COMMAND_TIMEOUT', 'private detail'), 'VERIFICATION_INCOMPLETE'),
                  (ValueError('COMMAND_TIMEOUT'), 'VERIFICATION_INCOMPLETE')]
        for error, expected in cases:
            runtime = Runtime()
            runtime.smoke = smoke
            def failed_accept(): raise error
            def failed_rollback(): raise smoke.Blocked('TRUST_METADATA_DRIFT')
            runtime.accept, runtime.rollback = failed_accept, failed_rollback
            result = cut.run_cutover(runtime, lambda _: None, lambda _: None)
            self.assertEqual(result['primary_error'], expected)
            self.assertEqual(result['rollback_error'], 'TRUST_METADATA_DRIFT')
        with patch.dict(cut.sys.modules, {'fixture_frozen_smoke': smoke}):
            for code, expected in [('BASE_SOURCE_DRIFT', 'BASE_SOURCE_DRIFT'), ('CANDIDATE_PIN', 'CANDIDATE_PIN'),
                                   ('PRIVATE_VALUE_NOT_ALLOWLISTED', 'FRESH_PREFLIGHT_FAILED')]:
                source = ('import sys\nsmoke=sys.modules["fixture_frozen_smoke"]\n'
                          + 'result=' + repr({'status': 'CUTOVER_PREFLIGHT_INCOMPLETE', 'error_code': code}) + '\n'
                          + 'print(json.dumps(result,sort_keys=True))')
                with patch.object(cut, 'REMOTE', source):
                    with self.assertRaises(cut.Blocked) as caught:
                        cut.NativeCutover('0' * 64).preflight()
                self.assertEqual(caught.exception.args, (expected,))

    def test_shipped_preflight_translates_actual_frozen_command_timeout_without_live_commands(self):
        import select, subprocess
        bundle = cut.inputs(pathlib.Path(cut.__file__).parent.parent)
        stream = io.BytesIO(len(bundle).to_bytes(4, 'big') + bundle)
        with patch.object(select, 'select', return_value=([0], [], [])), \
             patch.object(cut.os, 'read', side_effect=lambda fd, count: stream.read(count)), \
             patch.object(subprocess, 'run', side_effect=subprocess.TimeoutExpired(['offline-fixture'], 5)):
            with self.assertRaises(cut.Blocked) as caught:
                cut.NativeCutover(cut.sha(bundle)).preflight()
        self.assertEqual(caught.exception.args, ('COMMAND_TIMEOUT',))

    def test_digit_bearing_frozen_code_survives_local_execution_wire_and_preflight_wire(self):
        import secrets, types
        from types import SimpleNamespace
        raw = pathlib.Path(cut.__file__).with_name('Test-VM105CandidateSmoke.py').read_bytes()
        self.assertEqual(cut.sha(raw), cut.SMOKE_SHA)
        smoke = types.ModuleType('fixture_digit_code_smoke')
        exec(compile(raw, '<actual-frozen-verifier>', 'exec'), smoke.__dict__)
        code = cut.safe_error(smoke.Blocked('CGROUP_V2_REQUIRED'), smoke)
        self.assertEqual(code, 'CGROUP_V2_REQUIRED')
        with self.subTest(boundary='local_preflight_translation'):
            source = ('import sys\nsmoke=sys.modules["fixture_digit_code_smoke"]\n'
                      + 'result=' + repr({'status': 'CUTOVER_PREFLIGHT_INCOMPLETE', 'error_code': code}) + '\n'
                      + 'print(json.dumps(result,sort_keys=True))')
            with patch.dict(cut.sys.modules, {'fixture_digit_code_smoke': smoke}), patch.object(cut, 'REMOTE', source):
                with self.assertRaises(cut.Blocked) as caught: cut.NativeCutover('0' * 64).preflight()
            self.assertEqual(cut.safe_error(caught.exception), 'CGROUP_V2_REQUIRED')
        nonce = 'd' * 64
        receipt = {'status': 'BLOCKED', 'gate': 'CREDENTIAL_GATE', 'primary_error': code, 'rollback_error': code}
        wire = b''.join(json.dumps(row).encode() + b'\n' for row in [
            {'nonce': nonce, 'type': 'gate', 'stage': 'PREFLIGHT'},
            {'nonce': nonce, 'type': 'receipt', 'result': receipt}])
        proc = SimpleNamespace(stdin=io.BytesIO(), stdout=io.BytesIO(wire), wait=lambda **k: 1,
                               poll=lambda: 1, terminate=lambda: None)
        with self.subTest(boundary='execution_wire'), \
             patch.object(cut.subprocess, 'Popen', return_value=proc), \
             patch.object(cut, 'inputs', return_value=b'{}'), patch.object(cut.sys, 'platform', 'win32'), \
             patch.object(cut.socket, 'gethostname', return_value='bell-pc2'), \
             patch.object(secrets, 'token_hex', return_value=nonce), \
             patch.object(cut, 'external', return_value={'pid': 1, 'creation': 'fixture'}):
            result = cut.execute(True, cut.sha(pathlib.Path(cut.__file__).read_bytes()))
            self.assertEqual(result['primary_error'], 'CGROUP_V2_REQUIRED')
            self.assertEqual(result['rollback_error'], 'CGROUP_V2_REQUIRED')
            self.assertEqual(result['ssh_exit'], 1)
        preflight_receipt = {'status': 'CUTOVER_PREFLIGHT_INCOMPLETE', 'mutation_entry': 'READ_ONLY_PREFLIGHT', 'error_code': code}
        with self.subTest(boundary='preflight_wire'), \
             patch.object(cut.subprocess, 'run', return_value=SimpleNamespace(returncode=1, stdout=json.dumps(preflight_receipt).encode())), \
             patch.object(cut, 'inputs', return_value=b'{}'), patch.object(cut.sys, 'platform', 'win32'), \
             patch.object(cut.socket, 'gethostname', return_value='bell-pc2'), \
             patch.object(cut, 'external', return_value={'pid': 1, 'creation': 'fixture'}):
            try:
                result = cut.preflight()
            except cut.Blocked as error:
                result = {'error_code': cut.safe_error(error)}
            self.assertEqual(result['error_code'], 'CGROUP_V2_REQUIRED')
            self.assertEqual(result['ssh_exit'], 1)


if __name__ == '__main__':
    unittest.main()
