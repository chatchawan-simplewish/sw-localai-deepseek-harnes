import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('transport', Path(__file__).with_name('Invoke-VM105FinalClient.py'))
transport = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transport)


class TransportTest(unittest.TestCase):
    def test_output_waits_for_ack_and_third_request_never_reaches_gateway(self):
        result = transport.run_fixture_regression()
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(result['requestCount'], 2)
        for key in ('tupleEquality', 'ackBeforeOutput', 'progressCommitted', 'thirdRequestDenied', 'cleanupComplete'):
            self.assertIs(result[key], True, key)
        self.assertIs(result['resumeRequired'], False)
        for key in ('retries', 'redirects', 'discovery', 'catalog', 'directProvider', 'tools'):
            self.assertEqual(result[key], 0, key)

    def test_preflight_rejects_missing_external_bindings_and_blocked_closure(self):
        manifest = {'status': 'PASS', 'canonicalManifestSha256': 'a' * 64}
        for endpoint, key, closure in ((None, 'opaque-ref', manifest), (transport.GATEWAY, None, manifest), (transport.GATEWAY, 'opaque-ref', {'status': 'BLOCKED'})):
            self.assertEqual(transport.production_preflight(endpoint, key, closure)['status'], 'BLOCKED')
        self.assertFalse(transport.production_preflight(transport.GATEWAY, 'opaque-ref', manifest)['clientInvoked'])


if __name__ == '__main__':
    unittest.main()
