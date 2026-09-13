import array
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import tempfile
import types
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).with_name("Invoke-VM105ProductionLauncher.py")
spec = importlib.util.spec_from_file_location("vm105_production_launcher", SCRIPT)
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)
UNIT = "vm105-dsh-" + "1" * 32 + ".service"
GROUP = "/system.slice/" + UNIT


def bindings():
    return {
        "gatewayIp": "192.0.2.10",
        "gatewayPort": 20128,
        "credentialReference": "DSH_CRED_PIPE",
        "credentialSchema": "v1-refs",
        "relayOrigin": "http://127.0.0.1:39105",
        "currentSelector": "deepseek-harness.service:pid:invocation",
        "sourceRoot": "/",
        "stagingRoot": launcher.STAGING_ROOT,
        "manifestPath": "/run/vm105/final-manifest.json",
        "manifestSha256": launcher.ACCEPTED_MANIFEST_SHA256,
        "topologyPath": "/run/vm105/dsh-topology.json",
        "topologySha256": "e" * 64,
        "task": "fixture-task",
    }


class FakeStream:
    def __init__(self, fd):
        self.fd = fd
        self.closed = False

    def fileno(self):
        return self.fd

    def close(self):
        self.closed = True


class ProductionLauncherTests(unittest.TestCase):
    def live(self):
        return patch.multiple(
            launcher, ACCEPTED_LIVE_BINDINGS=bindings(),
            ACCEPTED_STAGING_TOPOLOGY_SHA256="e" * 64)

    def test_shape_valid_json_and_every_action_remain_hard_gated(self):
        calls = []
        self.assertIsNone(launcher.ACCEPTED_LIVE_BINDINGS)
        self.assertEqual(
            "cc7ca73f74bd1e515416cbff65809531fff2c052d0f7e406b9cc2efdb4c1ab20",
            launcher.ACCEPTED_STAGING_TOPOLOGY_SHA256)
        self.assertEqual(
            "86882398a06921bd351c84dbfc1eecc9abeb963912df41499ee21462b50cb47f",
            launcher.ACCEPTED_STAGING_TOPOLOGY_FILE_SHA256)
        accepted = bindings()
        accepted["topologySha256"] = launcher.ACCEPTED_STAGING_TOPOLOGY_SHA256
        with self.assertRaisesRegex(launcher.LaunchBlocked, "LIVE_BINDINGS_UNBOUND"):
            launcher.launch(accepted, 9, run_unit=lambda *_: calls.append("run"))
        with self.assertRaisesRegex(launcher.LaunchBlocked, "LIVE_BINDINGS_UNBOUND"):
            launcher.copy_credential_to_pipe(
                accepted, bytearray(b"secret"), pipe2=lambda *_: calls.append("pipe"))
        with patch.object(launcher, "ACCEPTED_LIVE_BINDINGS", bindings()), \
                self.assertRaisesRegex(
                    launcher.LaunchBlocked, "LIVE_BINDINGS_UNBOUND"):
            launcher.systemd_command(UNIT, bindings())
        bad = bindings()
        bad["sourceRoot"] = "/opt/deepseek-harness/node_modules"
        with self.live(), self.assertRaisesRegex(launcher.LaunchBlocked, "BINDING_PATH_REJECTED"):
            launcher.systemd_command(UNIT, bad)
        bad = bindings()
        bad["topologyPath"] = "relative.json"
        with self.live(), self.assertRaisesRegex(launcher.LaunchBlocked, "BINDINGS_UNBOUND"):
            launcher.systemd_command(UNIT, bad)
        bad = bindings()
        bad["topologySha256"] = "f" * 64
        with self.live(), self.assertRaisesRegex(launcher.LaunchBlocked, "LIVE_BINDINGS_UNBOUND"):
            launcher.systemd_command(UNIT, bad)
        bad = bindings()
        bad["topologySha256"] = "E" * 64
        with self.live(), self.assertRaisesRegex(launcher.LaunchBlocked, "BINDINGS_UNBOUND"):
            launcher.systemd_command(UNIT, bad)
        with self.live(), patch.object(launcher.sys, "platform", "win32"), self.assertRaisesRegex(
                launcher.LaunchBlocked, "LINUX_REQUIRED"):
            launcher.launch(bindings(), 9, run_unit=lambda *_: calls.append("run"))
        with patch.object(
                launcher.sys.stdin.buffer, "fileno",
                side_effect=lambda: calls.append("fileno")), \
                patch("builtins.print"):
            self.assertEqual(
                1, launcher.main([
                    "--bindings-json",
                    json.dumps(accepted, separators=(",", ":"))]))
        self.assertEqual([], calls)

    def test_systemd_pipe_uses_direct_read_fd_and_exact_hardening(self):
        captured = {}

        def run_unit(bound, command, credential_fd):
            captured.update(bound=bound, command=command, credential_fd=credential_fd)
            return {"returncode": 0, "stdout": json.dumps({
                "status": "PASS", "invocationId": "a" * 32,
                "controlGroup": GROUP,
                "runtimeDirectory": "/run/" + UNIT[:-8],
                "stagedFiles": 10037, "connections": 2, "handoffs": 1,
                "retries": 0,
                "requestAttempts": 2, "deniedRequests": 0,
                "acceptedRequests": 2,
                "commitState": "COMMITTED", "outputState": "RELEASED",
                "resumeRequired": False, "credentialExposed": False,
                "networkIsolation": "IP_TCP_NAMESPACE_ONLY",
                "afUnixPathnameSockets": "RESIDUAL",
                "networkNamespace": "net:[2]", "pidNamespace": "pid:[2]",
                "namespacePid": 1,
            })}

        with self.live(), patch.object(launcher.sys, "platform", "linux"):
            receipt = launcher.launch(
                bindings(), 77, unit_name=UNIT, run_unit=run_unit,
                cgroup_state=lambda bound, group: "missing",
                runtime_state=lambda bound, root: "missing")
        command = captured["command"]
        self.assertEqual(77, captured["credential_fd"])
        self.assertEqual("/usr/bin/systemd-run", command[0])
        for item in ("--wait", "--pipe", "--unit=" + UNIT,
                     "--property=CapabilityBoundingSet=CAP_SYS_ADMIN CAP_NET_ADMIN CAP_SETUID CAP_SETGID CAP_CHOWN",
                     "--property=NoNewPrivileges=yes", "--property=UMask=0077",
                     "--property=ProtectSystem=strict", "--property=ProtectHome=yes",
                     "--property=PrivateDevices=yes", "--property=ProtectControlGroups=yes",
                     "--property=ProtectKernelTunables=yes", "--property=ProtectKernelModules=yes",
                     "--property=ProtectKernelLogs=yes", "--property=LockPersonality=yes",
                     "--property=RestrictSUIDSGID=yes", "--property=RestrictRealtime=yes",
                     "--property=RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6",
                     "--property=TasksMax=32", "--property=KillMode=control-group",
                     "--property=LimitCORE=0",
                     "--property=ReadOnlyPaths=/run /tmp",
                     "--property=ReadWritePaths=/var/tmp /run/" + UNIT[:-8]):
            self.assertIn(item, command)
        self.assertIn("--property=RuntimeDirectory=" + UNIT[:-8], command)
        self.assertIn("--property=RuntimeDirectoryPreserve=no", command)
        self.assertNotIn("PrivateNetwork=yes", " ".join(command))
        self.assertNotIn("secret", " ".join(command) + json.dumps(receipt))
        self.assertLess(launcher.DSH_TIMEOUT_SECONDS,
                        launcher.UNIT_RUNTIME_SECONDS)
        self.assertGreater(
            launcher.OUTER_WAIT_SECONDS,
            launcher.UNIT_RUNTIME_SECONDS + launcher.UNIT_STOP_SECONDS)
        self.assertIn(
            "--property=RuntimeMaxSec=%ss" % launcher.UNIT_RUNTIME_SECONDS,
            command)
        self.assertIn(
            "--property=TimeoutStopSec=%ss" % launcher.UNIT_STOP_SECONDS,
            command)
        self.assertIs(receipt["resumeRequired"], False)
        self.assertEqual("COMMITTED", receipt["commitState"])
        self.assertEqual("RELEASED", receipt["outputState"])
        with self.live(), patch.object(launcher.subprocess, "run") as run:
            launcher._kill_unit(bindings(), UNIT)
        self.assertEqual("/usr/bin/systemctl", run.call_args.args[0][0])
        with self.live(), self.assertRaisesRegex(launcher.LaunchBlocked, "UNIT_ID_REJECTED"):
            launcher.systemd_command("unit.scope", bindings())

    def test_popen_receives_fd_as_stdin_without_input_or_pass_fds(self):
        captured = {}

        class Process:
            returncode = 0

            def communicate(self, **kwargs):
                captured["communicate"] = kwargs
                return b"{}", b""

        def popen(command, **kwargs):
            captured.update(command=command, kwargs=kwargs)
            return Process()

        with self.live(), patch.object(launcher.subprocess, "Popen", popen):
            launcher._run_unit(
                bindings(), ["systemd-run", "--pipe", "--unit=" + UNIT],
                88, UNIT)
        self.assertEqual(88, captured["kwargs"]["stdin"])
        self.assertIs(True, captured["kwargs"]["close_fds"])
        self.assertNotIn("pass_fds", captured["kwargs"])
        self.assertNotIn("input", captured["communicate"])

    def test_outer_timeout_kills_exact_unit_then_checks_its_cgroup(self):
        events = []
        waits = []

        class Process:
            returncode = 1
            calls = 0

            def communicate(self, **_kwargs):
                self.calls += 1
                if self.calls == 1:
                    waits.append(_kwargs["timeout"])
                    raise launcher.subprocess.TimeoutExpired(
                        "systemd-run", launcher.OUTER_WAIT_SECONDS)
                return b"", b""

        with self.live(), patch.object(
                launcher.subprocess, "Popen", lambda *_args, **_kwargs: Process()), \
                self.assertRaisesRegex(launcher.LaunchBlocked, "SYSTEMD_RUN_TIMEOUT"):
            launcher._run_unit(
                bindings(), ["systemd-run", "--pipe", "--unit=" + UNIT],
                88, UNIT,
                kill_unit=lambda bound, unit: events.append(("kill-unit", unit)),
                cgroup_state=lambda bound, group: events.append(
                    ("cgroup", group)) or "missing",
                runtime_state=lambda bound, root: events.append(
                    ("runtime", root)) or "missing")
        self.assertEqual([
            ("kill-unit", UNIT),
            ("cgroup", GROUP),
            ("runtime", "/run/" + UNIT[:-8]),
        ], events)
        self.assertEqual([launcher.OUTER_WAIT_SECONDS], waits)

    def test_nonzero_and_rejected_unit_receipts_kill_then_prove_cleanup(self):
        cases = (
            ({"returncode": 1, "stdout": ""}, "SYSTEMD_RUN_FAILED"),
            ({"returncode": 0, "stdout": "not-json"},
             "SYSTEMD_RECEIPT_REJECTED"),
            ({"returncode": 0, "stdout": json.dumps({
                "status": "BLOCKED", "reason": "SUPERVISOR_FAILED",
                "resumeRequired": True, "commitState": "UNPROVEN",
                "outputState": "UNPROVEN",
            })}, "SUPERVISOR_FAILED"),
        )
        for result, reason in cases:
            with self.subTest(reason=reason):
                events = []
                with self.live(), patch.object(launcher.sys, "platform", "linux"), \
                        self.assertRaisesRegex(launcher.LaunchBlocked, reason):
                    launcher.launch(
                        bindings(), 88, unit_name=UNIT,
                        run_unit=lambda *_: result,
                        cgroup_state=lambda bound, group: events.append(
                            ("cgroup", group)) or "missing",
                        runtime_state=lambda bound, root: events.append(
                            ("runtime", root)) or "missing",
                        kill_unit=lambda bound, unit: events.append(
                            ("kill-unit", unit)))
                self.assertEqual([
                    ("kill-unit", UNIT), ("cgroup", GROUP),
                    ("runtime", "/run/" + UNIT[:-8]),
                ], events)

    def test_inside_read_is_bounded_mutable_and_pipe_wipes_after_close(self):
        def reader(payload):
            pending = bytearray(payload)

            def readv(_fd, buffers):
                if not pending:
                    return 0
                count = min(len(buffers[0]), len(pending))
                buffers[0][:count] = pending[:count]
                del pending[:count]
                return count
            return readv

        with self.live():
            value = launcher.read_bounded_credential(
                bindings(), 5, readv=reader(b"credential"))
        self.assertIsInstance(value, bytearray)
        self.assertEqual(b"credential", value)
        wiped = []

        def wipe(value):
            value[:] = b"\0" * len(value)
            wiped.append(bytes(value))

        with self.live(), self.assertRaisesRegex(
                launcher.LaunchBlocked, "CREDENTIAL_INPUT_REJECTED"):
            launcher.read_bounded_credential(
                bindings(), 5,
                readv=reader(b"x" * (launcher.MAX_CREDENTIAL_BYTES + 1)),
                wipe=wipe)
        self.assertTrue(wiped and set(wiped[-1]) <= {0})

        events = []
        secret = bytearray(b"sensitive")
        with self.live():
            read_fd = launcher.copy_credential_to_pipe(
                bindings(), secret, pipe2=lambda _flags: (10, 11),
                write=lambda fd, data: events.append(("write", fd)) or len(data),
                close=lambda fd: events.append(("close", fd)),
                wipe=lambda value: (
                    events.append("wipe"),
                    value.__setitem__(slice(None), b"\0" * len(value))))
        self.assertEqual(10, read_fd)
        self.assertEqual([("write", 11), ("close", 11), "wipe"], events)
        self.assertEqual({0}, set(secret))

    def test_worker_orders_private_pid_mount_network_drop_then_contained_seam(self):
        events = []
        identity = types.SimpleNamespace(pw_uid=1001, pw_gid=1002)
        with self.live(), patch.object(
                launcher.os, "write",
                side_effect=lambda fd, data: events.append(
                    ("ready", fd, data)) or len(data)), patch.object(
                launcher.os, "getpid", return_value=1):
            launcher.isolated_worker(
                20, 21, 22, "net:[1]", "pid:[1]", bindings(), identity,
                {"root": "/run/test"},
                setsid=lambda bound: events.append("setsid"),
                unshare=lambda bound: events.append("unshare"),
                unshare_mount=lambda bound: events.append("unshare-mount"),
                raise_loopback=lambda bound: events.append("loopback"),
                network_namespace=lambda bound: "net:[2]",
                pid_namespace=lambda bound: "pid:[2]",
                namespace_pid=lambda bound: 1,
                mount_worker=lambda bound, runtime: events.append(
                    ("mount", runtime["root"])),
                close_other_fds=lambda bound, keep: events.append(
                    ("allow", tuple(sorted(keep)))),
                drop_dsh=lambda bound, actual: events.append(
                    ("drop", actual.pw_uid, actual.pw_gid)),
                contained_entry=lambda *args: events.append(
                    ("entry", args[:3])) or {"status": "PASS"},
                fork=lambda: events.append("fork") or 0)
        self.assertEqual([
            "setsid", "unshare", "loopback", "fork", "unshare-mount",
            ("mount", "/run/test"),
            ("allow", (20, 21, 22)), ("drop", 1001, 1002),
            ("ready", 22, b"READY net:[2] pid:[2] nspid=1\n"),
            ("entry", (20, 21, bindings())),
        ], events)

    def test_worker_mounts_runtime_before_readonly_run_and_self_binds_var_tmp(self):
        calls = []
        flags = {"/var/tmp": launcher.MS_RDONLY, "/run/test": 0}
        with self.live():
            launcher._mount_worker_filesystems(
                bindings(), {"root": "/run/test"},
                mount=lambda *args: calls.append(args),
                statvfs=lambda path: types.SimpleNamespace(f_flag=flags[path]))
        self.assertEqual([
            (None, "/", None, launcher.MS_REC | launcher.MS_PRIVATE),
            ("/run/test", "/run/test", None, launcher.MS_BIND),
            (None, "/run", None, launcher.MS_BIND | launcher.MS_REMOUNT |
             launcher.MS_RDONLY | launcher.MS_NOSUID | launcher.MS_NODEV |
             launcher.MS_NOEXEC),
            ("proc", "/proc", "proc", launcher.MS_NOSUID |
             launcher.MS_NODEV | launcher.MS_NOEXEC),
            ("/var/tmp", "/var/tmp", None, launcher.MS_BIND),
            (None, "/var/tmp", None, launcher.MS_BIND | launcher.MS_REMOUNT |
             launcher.MS_RDONLY | launcher.MS_NOSUID | launcher.MS_NODEV |
             launcher.MS_NOEXEC),
        ], calls)

    def test_intermediate_reaps_without_entering_child_mount_namespace(self):
        events = []
        identity = types.SimpleNamespace(pw_uid=1001, pw_gid=1002)
        with self.live():
            result = launcher.isolated_worker(
                20, 21, 22, "net:[1]", "pid:[1]", bindings(), identity,
                {"root": "/run/test"}, setsid=lambda bound: None,
                unshare=lambda bound: None, raise_loopback=lambda bound: None,
                network_namespace=lambda bound: "net:[2]",
                unshare_mount=lambda bound: events.append("unshare-mount"),
                mount_worker=lambda *args: events.append("mount"),
                close_other_fds=lambda bound, keep: events.append(("close", keep)),
                fork=lambda: events.append("fork") or 123,
                waitpid=lambda pid, flags: (events.append(("wait", pid, flags)) or
                                            (pid, 0)))
        self.assertEqual({"status": "PASS"}, result)
        self.assertEqual(["fork", ("close", set()), ("wait", 123, 0)], events)

    def test_strict_credential_decoder_patch_and_dsh_fd_allowlist(self):
        document = bytearray(
            b'{"refs":{"DSH_CRED_PIPE":"real-key"},"version":1}\n')
        with self.live(), patch.object(
                launcher, "read_bounded_credential", return_value=document), \
                patch.object(launcher.json, "loads",
                             side_effect=AssertionError("immutable JSON secret copy")):
            secret = launcher.decode_credential_document(bindings(), 21)
        self.assertEqual(bytearray(b"real-key"), secret)
        self.assertEqual({0}, set(document))
        invalid = (
            b'{"version":1,"refs":{"DSH_CRED_PIPE":"key"}}\n',
            b'{"refs":{"DSH_CRED_PIPE":"key","EXTRA":"x"},"version":1}\n',
            b'{"refs":{"DSH_CRED_PIPE":"key\r"},"version":1}\n',
            b'{"refs":{"WRONG":"key"},"version":1}\n',
        )
        for payload in invalid:
            with self.subTest(payload=payload), self.live(), patch.object(
                    launcher, "read_bounded_credential",
                    return_value=bytearray(payload)), self.assertRaisesRegex(
                        launcher.LaunchBlocked, "CREDENTIAL_DOCUMENT_REJECTED"):
                launcher.decode_credential_document(bindings(), 21)

        made, calls = [], []
        def pipe(bound, value):
            made.append(bytes(value))
            value[:] = b"\0" * len(value)
            return 70 + len(made)
        def run(bound, argv, **kwargs):
            self.assertEqual(bindings(), bound)
            calls.append((argv, kwargs))
            return types.SimpleNamespace(returncode=0)
        runtime = {"root": "/run/" + UNIT[:-8], "home": "/run/" + UNIT[:-8] + "/home",
                   "dshHome": "/run/" + UNIT[:-8] + "/dsh-home",
                   "tmp": "/run/" + UNIT[:-8] + "/tmp",
                   "workspace": "/run/" + UNIT[:-8] + "/workspace"}
        with self.live(), patch.object(
                launcher, "copy_credential_to_pipe", side_effect=pipe), \
                patch.object(launcher.os, "close"):
            launcher.run_dsh_entry(
                bindings(), ("127.0.0.1", 39105), runtime, run=run)
        dummy, patch_document = made
        self.assertEqual(
            b'{"refs":{"DSH_LOCAL_DUMMY":"fixture-dummy-v1-only"},"version":1}\n',
            dummy)
        config = json.loads(patch_document)
        rows = {row["id"]: row for row in config}
        provider = rows["llm-pi-ai"]["config"]["providers"]["omniroute"]
        self.assertEqual("http://127.0.0.1:39105/v1", provider["baseURL"])
        self.assertEqual("DSH_LOCAL_DUMMY", provider["apiKeyEnv"])
        for row in ("tools", "session-title-llm", "compaction", "delegation", "llm-retry"):
            self.assertIs(rows[row]["disabled"], True)
        argv, kwargs = calls[0]
        self.assertEqual((71, 72), kwargs["pass_fds"])
        self.assertNotIn("check", kwargs)
        self.assertNotIn(21, kwargs["pass_fds"])
        self.assertEqual(runtime["workspace"], kwargs["cwd"])
        self.assertEqual({"HOME", "DSH_HOME", "TMPDIR", "LANG", "DSH_TELEMETRY_DISABLED"},
                         set(kwargs["env"]))
        self.assertEqual("fixture-task", argv[-1])
        self.assertNotIn("real-key", repr((argv, kwargs, config)))

        events = []
        class TimedProcess:
            pid = 901
            returncode = -9
            calls = 0
            def communicate(self, **kwargs):
                self.calls += 1
                events.append(("wait", kwargs["timeout"]))
                if self.calls == 1:
                    raise launcher.subprocess.TimeoutExpired("dsh", 120)
        with self.live(), patch.object(
                launcher.subprocess, "Popen",
                side_effect=lambda argv, **kwargs: (
                    events.append(("popen", kwargs["start_new_session"])) or
                    TimedProcess())), patch.object(
                launcher.os, "killpg",
                side_effect=lambda pid, sig: events.append(("killpg", pid, sig)),
                create=True), patch.object(launcher.signal, "SIGKILL", 9,
                                           create=True):
            with self.assertRaisesRegex(launcher.LaunchBlocked, "DSH_ENTRY_TIMEOUT"):
                launcher._run_dsh_process(bindings(), ["dsh"], timeout=120)
        self.assertEqual([("popen", True), ("wait", 120),
                          ("killpg", 901, 9), ("wait", 5)],
                         events)

    def test_pinned_accepted_relay_composes_decoder_and_fixed_port(self):
        events = []

        class Control:
            def close(self):
                events.append("control-close")

        class Relay:
            address = ("127.0.0.1", 39105)

            def __init__(self, complete):
                self.state = {
                    "count": 2 if complete else 0,
                    "committed": complete, "output": complete,
                    "failed": False,
                    "requestAttempts": RelayType.request_attempts,
                    "deniedRequests": RelayType.denied_requests,
                    "tuple": ("task", "run", "turn", "idempotency")
                    if complete else None,
                }
                self.claimed_upstreams = [complete, complete]

            def __enter__(self):
                events.append("relay-enter")
                return self

            def __exit__(self, *_):
                events.append("relay-exit")

        class RelayType:
            complete = True
            request_attempts = 2
            denied_requests = 0

            @classmethod
            def from_socket_handoff(cls, control, ip, port, key, listen_port):
                events.append(("handoff", ip, port, key, listen_port))
                control.close()
                return Relay(cls.complete)

        helper = types.SimpleNamespace(TwoRequestRelay=RelayType)
        with self.live(), patch.object(
                launcher.socket, "AF_UNIX", 1, create=True), patch.object(
                launcher.socket, "socket", return_value=Control()), \
                patch.object(
                    launcher, "_load_accepted", return_value=helper), \
                patch.object(
                    launcher.os, "close",
                    side_effect=lambda fd: events.append(("close-fd", fd))):
            receipt = launcher.contained_composition(
                20, 21, bindings(), {"root": "/run/test"},
                credential_decoder=lambda bound, fd: (
                    events.append(("decode", fd)) or bytearray(b"key")),
                dsh_entry=lambda bound, address, runtime: (
                    events.append(("dsh", address, runtime)) or
                    {"status": "PASS"}))
        self.assertEqual("PASS", receipt["status"])
        self.assertEqual({
            "requestAttempts": 2, "deniedRequests": 0,
            "acceptedRequests": 2, "committed": True, "output": True,
            "failed": False, "tupleFieldCount": 4,
            "upstreamSocketsConsumed": 2,
        }, {key: receipt[key] for key in (
            "requestAttempts", "deniedRequests", "acceptedRequests",
            "committed", "output", "failed", "tupleFieldCount",
            "upstreamSocketsConsumed")})
        self.assertNotIn("task", json.dumps(receipt))
        self.assertIn(("handoff", "192.0.2.10", 20128, "key", 39105), events)
        self.assertIn(("dsh", ("127.0.0.1", 39105), {"root": "/run/test"}), events)
        self.assertEqual(1, events.count("relay-enter"))
        self.assertEqual(1, events.count("relay-exit"))
        self.assertIn(("close-fd", 21), events)

        RelayType.request_attempts = 3
        RelayType.denied_requests = 1
        with self.live(), patch.object(
                launcher.socket, "AF_UNIX", 1, create=True), patch.object(
                launcher.socket, "socket", return_value=Control()), patch.object(
                launcher, "_load_accepted", return_value=helper), patch.object(
                launcher.os, "close"), self.assertRaisesRegex(
                    launcher.LaunchBlocked, "RELAY_COMPLETION_UNPROVEN"):
            launcher.contained_composition(
                20, 21, bindings(), {"root": "/run/test"},
                credential_decoder=lambda *_: bytearray(b"key"),
                dsh_entry=lambda *_: {"status": "PASS"})

        RelayType.request_attempts = 2
        RelayType.denied_requests = 0
        RelayType.complete = False
        with self.live(), patch.object(
                launcher.socket, "AF_UNIX", 1, create=True), patch.object(
                launcher.socket, "socket", return_value=Control()), patch.object(
                launcher, "_load_accepted", return_value=helper), patch.object(
                launcher.os, "close"), self.assertRaisesRegex(
                    launcher.LaunchBlocked, "RELAY_COMPLETION_UNPROVEN"):
            launcher.contained_composition(
                20, 21, bindings(), {"root": "/run/test"},
                credential_decoder=lambda *_: bytearray(b"key"),
                dsh_entry=lambda *_: {"status": "PASS"})

    def test_runtime_directory_is_exact_created_by_descriptor_and_removed_after_unit(self):
        runtime = "/run/" + UNIT[:-8]
        good = {"status": "PASS", "invocationId": "b" * 32,
                "controlGroup": GROUP, "runtimeDirectory": runtime,
                "stagedFiles": 10037, "connections": 2, "handoffs": 1,
                "retries": 0,
                "requestAttempts": 2, "deniedRequests": 0,
                "acceptedRequests": 2,
                "commitState": "COMMITTED", "outputState": "RELEASED",
                "resumeRequired": False, "credentialExposed": False,
                "networkIsolation": "IP_TCP_NAMESPACE_ONLY",
                "afUnixPathnameSockets": "RESIDUAL",
                "networkNamespace": "net:[2]", "pidNamespace": "pid:[2]",
                "namespacePid": 1}
        with self.live():
            receipt = launcher.verify_systemd_lifecycle(
                bindings(), UNIT, good, lambda *_: "missing",
                runtime_state=lambda *_: "missing")
        self.assertEqual(runtime, receipt["runtimeDirectory"])
        with self.live(), self.assertRaisesRegex(
                launcher.LaunchBlocked, "RUNTIME_DIRECTORY_NOT_REMOVED"):
            launcher.verify_systemd_lifecycle(
                bindings(), UNIT, good, lambda *_: "missing",
                runtime_state=lambda *_: "present")

        events = []
        identity = types.SimpleNamespace(pw_uid=1001, pw_gid=1002)
        opened = iter((50, 51, 52, 53, 54))
        with self.live(), patch.dict(
                launcher.os.environ, {"RUNTIME_DIRECTORY": runtime}, clear=True), \
                patch.object(launcher.os, "open",
                             side_effect=lambda *args, **kwargs: next(opened)), \
                patch.object(launcher.os, "fstat", return_value=types.SimpleNamespace(
                    st_mode=stat.S_IFDIR | 0o700, st_uid=0, st_gid=0,
                    st_nlink=2)), \
                patch.object(launcher.os, "fchown",
                             side_effect=lambda fd, uid, gid: events.append(("chown", fd, uid, gid)),
                             create=True), \
                patch.object(launcher.os, "fchmod",
                             side_effect=lambda fd, mode: events.append(("chmod", fd, mode)),
                             create=True), \
                patch.object(launcher.os, "mkdir",
                             side_effect=lambda name, mode, dir_fd: events.append(("mkdir", name, dir_fd))), \
                patch.object(launcher.os, "close"):
            paths = launcher._prepare_runtime(bindings(), GROUP, identity)
        self.assertEqual(runtime, paths["root"])
        self.assertEqual(5, len([event for event in events if event[0] == "chown"]))
        self.assertTrue(all(event[2:] == (1001, 1002)
                            for event in events if event[0] == "chown"))

    def test_helper_source_hash_is_checked_before_execution(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "accepted.py"
            payload = b"VALUE = 7\n"
            source.write_bytes(payload)
            expected = hashlib.sha256(payload).hexdigest()
            with self.live():
                loaded = launcher._load_pinned_source(
                    bindings(), source, "accepted_test", expected)
            self.assertEqual(7, loaded.VALUE)
            with self.live(), self.assertRaisesRegex(
                    launcher.LaunchBlocked, "ACCEPTED_SOURCE_REJECTED"):
                launcher._load_pinned_source(
                    bindings(), source, "rejected_test", "0" * 64)

    def test_topology_receipt_raw_file_hash_is_checked_before_json_use(self):
        receipt = (SCRIPT.parent.parent /
                   "docs/evidence/vm105-dsh-topology-capture-successor-20260913.json")
        descriptor = os.open(receipt, os.O_RDONLY)
        try:
            value = launcher._read_pinned_topology(descriptor)
        finally:
            os.close(descriptor)
        self.assertEqual(
            launcher.ACCEPTED_STAGING_TOPOLOGY_SHA256,
            value["receiptSha256"])
        descriptor = os.open(receipt, os.O_RDONLY)
        try:
            with patch.object(
                    launcher, "ACCEPTED_STAGING_TOPOLOGY_FILE_SHA256",
                    "0" * 64), self.assertRaisesRegex(
                        launcher.LaunchBlocked, "TOPOLOGY_FILE_REJECTED"):
                launcher._read_pinned_topology(descriptor)
        finally:
            os.close(descriptor)

    def test_topology_receipt_is_pinned_reconstructed_then_symlink_aware_sealed(self):
        manifest, topology = {"manifest": True}, {"status": "PASS"}
        staged = {"files": [], "links": [], "directories": []}
        calls = []
        builder = types.SimpleNamespace(_hash_fd=lambda fd: "hash")

        class Helper:
            @staticmethod
            def stage_verified_topology(*args):
                calls.append(("stage", args))
                return dict(staged)

        class Opened:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

        helpers = iter((builder, Helper))
        descriptors = iter((10, 11, 12, 13))
        identity = types.SimpleNamespace(pw_gid=1002)
        bound = bindings()
        with self.live(), patch.object(
                launcher.os, "open", side_effect=lambda *_args, **_kwargs: next(descriptors)), \
                patch.object(launcher.os, "fdopen", return_value=Opened()), \
                patch.object(launcher.os, "dup", side_effect=lambda fd: fd + 100), \
                patch.object(launcher.os, "mkdir"), patch.object(launcher.os, "close"), \
                patch.object(launcher.json, "load", return_value=manifest), \
                patch.object(launcher, "_read_pinned_topology",
                             return_value=topology) as read_topology, \
                patch.object(launcher, "_load_accepted", side_effect=lambda *args: (
                    calls.append(("load", args[1], args[3])) or next(helpers))):
            result = launcher.stage_bound_closure(
                bound, identity,
                seal_tree=lambda live, root, receipt, gid, hash_fd: (
                    calls.append(("seal", live, root, receipt, gid, hash_fd)) or 7))
        self.assertEqual(7, result["sealedEntries"])
        read_topology.assert_called_once_with(11)
        self.assertIn(("load", "Capture-VM105DshTopology.py",
                       launcher.TOPOLOGY_SOURCE_SHA256), calls)
        stage = next(row for row in calls if row[0] == "stage")[1]
        self.assertEqual((manifest, topology, bound["topologySha256"], 12, 13, builder), stage)
        seal = next(row for row in calls if row[0] == "seal")
        self.assertEqual((bound, 13, 1002, builder._hash_fd),
                         (seal[1], seal[2], seal[4], seal[5]))
        self.assertEqual(staged, {key: seal[3][key] for key in staged})

    def test_service_receipt_reduces_full_topology_inventory_to_exact_scalar_keys(self):
        identity = types.SimpleNamespace(pw_uid=1001, pw_gid=1002)
        runtime = {"root": "/run/" + UNIT[:-8]}
        full_stage = {"fileCount": 10037, "files": [{"path": "large"}],
                      "links": [{"path": "link"}], "directories": []}
        handoff = {
            "connections": 2, "handoffs": 1,
            "networkIsolation": "IP_TCP_NAMESPACE_ONLY",
            "afUnixPathnameSockets": "RESIDUAL",
            "namespaces": {"network": "net:[2]", "pid": "pid:[2]",
                           "namespacePid": 1},
        }
        controls = (FakeStream(20), FakeStream(21))
        with self.live(), patch.object(launcher.sys, "platform", "linux"), \
                patch.object(launcher.os, "geteuid", return_value=0, create=True), \
                patch.object(launcher, "_dsh_identity", return_value=identity), \
                patch.object(launcher, "_control_group", return_value=GROUP), \
                patch.object(launcher, "_prepare_runtime", return_value=runtime), \
                patch.object(launcher, "read_bounded_credential",
                             return_value=bytearray(b"credential")), \
                patch.object(launcher, "copy_credential_to_pipe", return_value=30), \
                patch.object(launcher, "stage_bound_closure", return_value=full_stage), \
                patch.object(launcher, "_namespace", return_value="net:[1]"), \
                patch.object(launcher, "_pid_namespace", return_value="pid:[1]"), \
                patch.object(launcher.socket, "AF_UNIX", 1, create=True), \
                patch.object(launcher.socket, "SOCK_CLOEXEC", 0, create=True), \
                patch.object(launcher.socket, "socketpair", return_value=controls), \
                patch.object(launcher.os, "O_CLOEXEC", 0, create=True), \
                patch.object(launcher.os, "pipe2", return_value=(40, 41), create=True), \
                patch.object(launcher.os, "fork", return_value=501, create=True), \
                patch.object(launcher.os, "close"), \
                patch.object(launcher, "handoff_and_wait", return_value=handoff), \
                patch.dict(launcher.os.environ, {"INVOCATION_ID": "a" * 32}):
            receipt = launcher.service_entry(bindings())
        self.assertEqual(launcher._INSIDE_RECEIPT_KEYS, set(receipt))
        self.assertEqual(10037, receipt["stagedFiles"])
        self.assertIs(type(receipt["stagedFiles"]), int)
        self.assertNotIn("files", receipt)

    def test_descriptor_walk_seals_files_and_directories_without_following_links(self):
        state = {
            100: [stat.S_IFDIR | 0o700, 0, 0],
            101: [stat.S_IFDIR | 0o700, 0, 0],
            102: [stat.S_IFREG | 0o600, 0, 0],
            103: [stat.S_IFREG | 0o500, 0, 0],
            104: [stat.S_IFLNK | 0o777, 0, 0],
        }
        hashes = {102: "data-hash", 103: "exec-hash"}
        receipt = {
            "files": [
                {"path": "dir/nested", "sha256": "exec-hash", "mode": 0o500},
                {"path": "file", "sha256": "data-hash", "mode": 0o600},
            ],
            "links": [{"path": "link", "rawRelativeTarget": "dir"}],
            "directories": [{"path": "dir"}],
        }
        children = {100: ["dir", "file", "link"], 101: ["nested"]}
        descriptors = {(100, "dir"): 101, (100, "file"): 102,
                       (101, "nested"): 103, (100, "link"): 104,
                       (100, "escape"): 104}
        ownership, modes, closes, flags = [], [], [], []

        def openat(name, value, dir_fd):
            flags.append(value)
            return descriptors[(dir_fd, name)]

        def info(fd):
            mode, uid, gid = state[fd]
            return types.SimpleNamespace(st_mode=mode, st_uid=uid, st_gid=gid)

        def statat(name, *, dir_fd, follow_symlinks):
            self.assertFalse(follow_symlinks)
            return info(descriptors[(dir_fd, name)])

        def chown(fd, uid, gid):
            ownership.append((fd, uid, gid))
            state[fd][1:] = [uid, gid]

        def chmod(fd, mode):
            modes.append((fd, mode))
            state[fd][0] = stat.S_IFMT(state[fd][0]) | mode

        with self.live(), patch.object(launcher, "O_NOFOLLOW", 0x20000):
            count = launcher._seal_staged_topology(
                bindings(), 100, receipt, 1002,
                listdir=lambda fd: children.get(fd, []), statat=statat,
                readlink=lambda name, dir_fd: "dir", openat=openat,
                fstat=info, fchown=chown, fchmod=chmod,
                close=lambda fd: closes.append(fd),
                hash_fd=lambda fd: hashes[fd])
        self.assertEqual(5, count)
        self.assertEqual({100, 101, 102, 103}, {row[0] for row in ownership})
        self.assertTrue(all(uid == 0 and gid == 1002 for _, uid, gid in ownership))
        self.assertEqual(0o550, stat.S_IMODE(state[100][0]))
        self.assertEqual(0o550, stat.S_IMODE(state[101][0]))
        self.assertEqual(0o440, stat.S_IMODE(state[102][0]))
        self.assertEqual(0o550, stat.S_IMODE(state[103][0]))
        self.assertTrue(all(
            not (stat.S_IMODE(state[fd][0]) & 0o222)
            for fd in (100, 101, 102, 103)))
        self.assertEqual({101, 102, 103}, set(closes))
        self.assertTrue(all(value & 0x20000 for value in flags))

        children[100] = ["escape"]
        ownership.clear()
        with self.live(), patch.object(launcher, "O_NOFOLLOW", 0x20000), \
                self.assertRaisesRegex(
                    launcher.LaunchBlocked, "STAGING_SEAL_REJECTED"):
            launcher._seal_staged_topology(
                bindings(), 100, receipt, 1002,
                listdir=lambda fd: children.get(fd, []), statat=statat,
                readlink=lambda name, dir_fd: "dir", openat=openat,
                fstat=info, fchown=chown, fchmod=chmod,
                close=lambda fd: None, hash_fd=lambda fd: hashes[fd])

    def test_exactly_two_numeric_connects_one_sendmsg_and_no_retry(self):
        events = []
        streams = [FakeStream(30), FakeStream(31)]
        control = FakeStream(19)
        control.sendmsg = lambda chunks, ancillary: events.append(
            ("sendmsg", chunks, ancillary)) or len(launcher.GATEWAY_FD_MESSAGE)

        def connect(bound, peer, timeout):
            events.append(("connect", peer, timeout))
            return streams[len([row for row in events if row[0] == "connect"]) - 1]

        with self.live():
            result = launcher.handoff_and_wait(
                bindings(), 501, control,
                wait_ready=lambda bound, pid, seconds: "net:[2]", connect=connect,
                wait_child=lambda bound, pid, seconds: 0,
                reap_child=lambda bound, pid, seconds: events.append(
                    ("reap", pid)) or 0,
                getpgid=lambda bound, pid: pid,
                kill_group=lambda bound, pid: events.append(("kill-group", pid)),
                kill_child=lambda bound, pid: events.append(("kill-child", pid)))
        self.assertEqual([("192.0.2.10", 20128)] * 2,
                         [row[1] for row in events if row[0] == "connect"])
        sent = [row for row in events if row[0] == "sendmsg"]
        self.assertEqual(1, len(sent))
        rights = array.array("i")
        rights.frombytes(sent[0][2][0][2])
        self.assertEqual([30, 31], list(rights))
        self.assertEqual(0, result["retries"])
        self.assertEqual("IP_TCP_NAMESPACE_ONLY", result["networkIsolation"])
        self.assertEqual("RESIDUAL", result["afUnixPathnameSockets"])
        self.assertTrue(control.closed and all(stream.closed for stream in streams))
        self.assertEqual([("reap", 501)], [row for row in events if row[0] == "reap"])
        self.assertFalse(any(row[0].startswith("kill") for row in events))

    def test_failure_paths_kill_once_without_retry(self):
        for failure in ("ready", "send", "child"):
            with self.subTest(failure=failure), self.live():
                cleanup, connections = [], []
                control = FakeStream(19)
                control.sendmsg = (
                    lambda *_: (_ for _ in ()).throw(OSError())
                    if failure == "send" else len(launcher.GATEWAY_FD_MESSAGE))
                streams = [FakeStream(30), FakeStream(31)]

                def connect(*_):
                    stream = streams[len(connections)]
                    connections.append(stream)
                    return stream

                with self.assertRaisesRegex(launcher.LaunchBlocked, "SUPERVISOR_FAILED"):
                    launcher.handoff_and_wait(
                        bindings(), 501, control,
                        wait_ready=(
                            lambda *_: (_ for _ in ()).throw(TimeoutError()))
                        if failure == "ready" else (lambda *_: "net:[2]"),
                        connect=connect,
                        wait_child=lambda *_: 7 if failure == "child" else 0,
                        reap_child=lambda bound, pid, seconds: cleanup.append(
                            ("reap", pid)) or (7 if failure == "child" else 0),
                        getpgid=lambda bound, pid: pid,
                        kill_group=lambda bound, pid: cleanup.append(("group", pid)),
                        kill_child=lambda bound, pid: cleanup.append(("child", pid)))
                self.assertEqual(
                    [("child", 501), ("reap", 501)] if failure == "ready"
                    else [("group", 501), ("reap", 501)], cleanup)
                self.assertEqual(0 if failure == "ready" else 2, len(connections))

    def test_live_receipt_pins_invocation_and_exact_service_cgroup(self):
        good = {"status": "PASS", "invocationId": "b" * 32,
                "controlGroup": GROUP,
                "runtimeDirectory": "/run/" + UNIT[:-8],
                "stagedFiles": 10037, "connections": 2, "handoffs": 1,
                "retries": 0,
                "requestAttempts": 2, "deniedRequests": 0,
                "acceptedRequests": 2,
                "commitState": "COMMITTED", "outputState": "RELEASED",
                "resumeRequired": False, "credentialExposed": False,
                "networkIsolation": "IP_TCP_NAMESPACE_ONLY",
                "afUnixPathnameSockets": "RESIDUAL",
                "networkNamespace": "net:[2]", "pidNamespace": "pid:[2]",
                "namespacePid": 1}
        with self.live():
            missing = launcher.verify_systemd_lifecycle(
                bindings(), UNIT, good,
                lambda bound, group: "missing", lambda *_: "missing")
            empty = launcher.verify_systemd_lifecycle(
                bindings(), UNIT, good,
                lambda bound, group: "empty", lambda *_: "missing")
        self.assertEqual("missing", missing["cgroupState"])
        self.assertEqual("empty", empty["cgroupState"])
        for bad in ({**good, "invocationId": "bad"},
                    {**good, "controlGroup": "/system.slice/other.service"},
                    {**good, "stagedFiles": []}, {**good, "files": []}):
            with self.live(), self.assertRaisesRegex(
                    launcher.LaunchBlocked, "SYSTEMD_PROOF_FAILED"):
                launcher.verify_systemd_lifecycle(
                    bindings(), UNIT, bad,
                    lambda bound, group: "missing", lambda *_: "missing")
        with self.live(), self.assertRaisesRegex(
                launcher.LaunchBlocked, "CGROUP_NOT_EMPTY"):
            launcher.verify_systemd_lifecycle(
                bindings(), UNIT, good,
                lambda bound, group: "nonempty", lambda *_: "missing")

    def test_main_sanitizes_unexpected_os_failure(self):
        with self.live(), patch.object(
                launcher, "launch", side_effect=OSError("sensitive path")), \
                patch.object(launcher.sys.stdin.buffer, "fileno", return_value=0), \
                patch("builtins.print") as output:
            self.assertEqual(1, launcher.main([
                "--bindings-json", json.dumps(bindings(), separators=(",", ":"))]))
        receipt = json.loads(output.call_args.args[0])
        self.assertEqual({
            "status": "BLOCKED", "reason": "LAUNCH_FAILED",
            "resumeRequired": True, "commitState": "UNPROVEN",
            "outputState": "UNPROVEN",
        }, receipt)
        self.assertNotIn("sensitive", output.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
