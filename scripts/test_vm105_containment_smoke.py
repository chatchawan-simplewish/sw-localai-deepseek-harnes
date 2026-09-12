"""Offline contract checks for the unexecuted VM105 containment launcher."""
import importlib.util
import json
import pathlib
import subprocess
import sys
import unittest


SCRIPT = pathlib.Path(__file__).with_name('Invoke-VM105ContainmentSmoke.py')


class ContainmentSmokeContractTest(unittest.TestCase):
    def load(self):
        spec = importlib.util.spec_from_file_location('containment_smoke', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_default_is_contract_only(self):
        result = subprocess.run([sys.executable, '-B', str(SCRIPT)], capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)['status'], 'CONTRACT_ONLY')

    def test_fixed_contract_has_every_required_assertion(self):
        module = self.load()
        for marker in ('NETWORK_DENIED', 'OUTSIDE_WRITE_DENIED', 'HOME_HIDDEN', 'INSIDE_WRITE_ALLOWED',
                       'DESCENDANT_REAPED', 'PrivateNetwork=yes', 'RestrictAddressFamilies=AF_UNIX',
                       'ProtectSystem=strict', 'ProtectHome=yes', 'PrivateDevices=yes',
                       'RestrictNamespaces=yes', 'KillMode=control-group', 'RuntimeMaxSec=30s', 'Environment='):
            self.assertIn(marker, module.REMOTE_SCRIPT)

    def test_cleanup_stays_armed_until_descendant_is_proven_reaped(self):
        script = self.load().REMOTE_SCRIPT
        self.assertGreater(script.index('owned=0', script.index('wait "$runner"')), script.index("printf 'DESCENDANT_REAPED"))

    def test_launcher_pins_transport_and_rejects_bad_receipts(self):
        module = self.load()
        self.assertEqual(module.SSH, 'C:/Windows/System32/OpenSSH/ssh.exe')
        self.assertIn('-T', module.ssh_argv())
        self.assertTrue(module.valid_receipt(b'{"status":"CONTAINMENT_SMOKE_PASS","root":"/var/tmp/omniroute-dsh-containment-smoke-20260913","unit":"omniroute-dsh-containment-smoke-20260913.service","service_pin_sha256":"' + b'a' * 64 + b'"}'))
        self.assertFalse(module.valid_receipt(b''))
        self.assertFalse(module.valid_receipt(b'{}'))

    def test_remote_refuses_preexisting_outside_path_and_proves_effective_unit_state(self):
        script = self.load().REMOTE_SCRIPT
        self.assertIn('[ ! -e "$OUTSIDE" ] && [ ! -L "$OUTSIDE" ] || fail OUTSIDE_ALREADY_EXISTS', script)
        for marker in ('--quiet', '--wait', '--property=Type=exec', 'UNIT_PROPERTY_', 'CGROUP_NOT_EMPTY',
                       'touch "$ROOT/release"', 'wait "$runner"'):
            self.assertIn(marker, script)
        self.assertIn('if : 2>/dev/null >"$OUTSIDE"; then', script)


if __name__ == '__main__':
    unittest.main()
