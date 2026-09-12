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

class ReviewRegressionTest(unittest.TestCase):
    def test_chat_waits_for_downstream_ack_write_and_failure_releases_nothing(self):
        import http.server
        import threading
        from unittest.mock import patch
        original = http.server.BaseHTTPRequestHandler.end_headers
        for fail_write in (False, True):
            entered, release, chat_output = threading.Event(), threading.Event(), threading.Event()
            def delayed(handler):
                if handler.path == transport.ACK and handler.server.server_address == address[0]:
                    entered.set()
                    release.wait(2)
                    if fail_write:
                        raise OSError('fixture failed downstream ACK write')
                return original(handler)
            # The gateway is real; only the downstream socket-write boundary is held/fails.
            class Gateway(http.server.BaseHTTPRequestHandler):
                def log_message(self, *args): pass
                def do_POST(self):
                    self.rfile.read(int(self.headers['Content-Length']))
                    self.send_response(202 if self.path == transport.ACK else 200)
                    self.end_headers()
                    self.wfile.write(b'{"accepted":true}' if self.path == transport.ACK else b'data: first\n\n')
            gateway = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Gateway)
            gateway.daemon_threads = False
            gt = threading.Thread(target=gateway.serve_forever, kwargs={'poll_interval': .01}); gt.start()
            address, clients, workers = [], [], []
            identity = dict(taskId='t', runId='r', turnId='u', idempotencyKey='i')
            def request(path, payload):
                import http.client, json
                c = http.client.HTTPConnection(*address[0], timeout=3); clients.append(c)
                try:
                    c.request('POST', path, json.dumps(payload))
                    r = c.getresponse()
                    if path == transport.CHAT and r.status == 200 and r.read(1): chat_output.set()
                    r.read()
                except (OSError, http.client.HTTPException): pass
                finally: c.close()
            try:
                with transport.TwoRequestRelay('http://127.0.0.1:%s/v1' % gateway.server_port) as relay:
                    address.append(relay.address)
                    with patch.object(http.server.BaseHTTPRequestHandler, 'end_headers', delayed):
                        chat = threading.Thread(target=request, args=(transport.CHAT, dict(identity, model='agent/normal', stream=True, tools=[], tool_choice='none'))); workers.append(chat); chat.start()
                        import time
                        deadline = time.monotonic()+2
                        while relay.state['count'] < 1 and time.monotonic() < deadline: time.sleep(.01)
                        ack = threading.Thread(target=request, args=(transport.ACK, dict(identity, event='output_started'))); workers.append(ack); ack.start()
                        try:
                            self.assertTrue(entered.wait(2))
                            self.assertFalse(chat_output.wait(.15), 'chat escaped before downstream ACK write')
                        finally: release.set()
                        for w in workers: w.join(3)
                        self.assertEqual(chat_output.is_set(), not fail_write)
                self.assertFalse(relay.thread.is_alive())
                self.assertTrue(all(not w.is_alive() for w in workers))
                self.assertTrue(all(c.sock is None for c in relay.connections + clients))
                self.assertEqual(list(relay.server._threads), [])
                self.assertEqual(relay.server.socket.fileno(), -1)
            finally:
                release.set()
                for w in workers: w.join(3)
                gateway.shutdown(); gateway.server_close(); gt.join()

    def test_preflight_validates_complete_manifest_and_expected_hash(self):
        import json, copy
        manifest = json.loads((Path(__file__).parents[1] / 'docs/evidence/vm105-final-client-runtime-manifest-20260913.json').read_text())
        expected = manifest['canonicalManifestSha256']
        result = transport.production_preflight(transport.GATEWAY, 'opaque-ref', manifest, expected)
        self.assertEqual(result['status'], 'PREFLIGHT_ONLY')
        self.assertFalse(result['clientInvoked'])
        for broken in ({'status':'PASS','canonicalManifestSha256':expected}, dict(manifest, modules=[]), dict(manifest, modules=list(reversed(manifest['modules'])))):
            self.assertEqual(transport.production_preflight(transport.GATEWAY, 'opaque-ref', broken, expected)['status'], 'BLOCKED')
        changed = copy.deepcopy(manifest); changed['runtime']['node']['sha256']='0'*64
        self.assertEqual(transport.production_preflight(transport.GATEWAY, 'opaque-ref', changed, expected)['status'], 'BLOCKED')
        self.assertEqual(transport.production_preflight(transport.GATEWAY, 'opaque-ref', manifest, '0'*64)['status'], 'BLOCKED')


if __name__ == '__main__':
    unittest.main()
