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
    def test_unsupported_method_between_chat_and_ack_releases_no_output(self):
        """Fails if a rejected method leaves the in-flight chat eligible for release."""
        for method in ('GET', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS', 'CONNECT', 'TRACE', 'CUSTOM'):
            with self.subTest(method=method):
                self.exercise_interleaving(unsupported_method=method)

    def test_early_ack_cannot_overtake_chat_upstream(self):
        """Fails if ACK forwards while the classified chat is held before its socket send."""
        self.exercise_interleaving(hold_chat=True)

    def exercise_interleaving(self, unsupported_method=None, hold_chat=False):
        import http.client
        import http.server
        import json
        import threading
        import time
        from unittest.mock import patch
        seen, results, errors, workers = [], {}, [], []
        held, release, chat_arrived = (threading.Event() for _ in range(3))
        identity = dict(taskId='t', runId='r', turnId='u', idempotencyKey='i')

        class Gateway(http.server.BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def do_POST(self):
                self.rfile.read(int(self.headers['Content-Length']))
                seen.append(self.path)
                if self.path == transport.CHAT:
                    chat_arrived.set()
                self.send_response(200 if self.path == transport.CHAT else 202)
                self.end_headers()
                self.wfile.write(b'data: first\n\n' if self.path == transport.CHAT else b'{"accepted":true}')

        gateway = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Gateway)
        gateway.daemon_threads = False
        gateway_thread = threading.Thread(target=gateway.serve_forever, kwargs={'poll_interval': .01})
        gateway_thread.start()
        original_request = http.client.HTTPConnection.request

        def delayed_send(connection, method, path, *args, **kwargs):
            if hold_chat and connection.port == gateway.server_port and path == transport.CHAT:
                held.set()
                if not release.wait(3):
                    raise OSError('held send timed out')
            return original_request(connection, method, path, *args, **kwargs)

        def request(method, path, payload=None):
            connection = http.client.HTTPConnection(*relay.address, timeout=4)
            try:
                connection.request(method, path, json.dumps(payload) if payload else None)
                response = connection.getresponse()
                results[(method, path)] = (response.status, response.read())
            except (OSError, http.client.HTTPException) as error:
                errors.append(type(error).__name__)
            finally:
                connection.close()

        try:
            with transport.TwoRequestRelay('http://127.0.0.1:%s/v1' % gateway.server_port) as relay:
                with patch.object(http.client.HTTPConnection, 'request', delayed_send):
                    chat = threading.Thread(target=request, args=('POST', transport.CHAT, dict(identity, model='agent/normal', stream=True, tools=[], tool_choice='none')))
                    workers.append(chat); chat.start()
                    try:
                        self.assertTrue((held if hold_chat else chat_arrived).wait(2))
                        if unsupported_method:
                            request(unsupported_method, '/denied')
                        ack = threading.Thread(target=request, args=('POST', transport.ACK, dict(identity, event='output_started')))
                        workers.append(ack); ack.start()
                        if hold_chat:
                            deadline = time.monotonic() + 2
                            while relay.state['count'] < 2 and time.monotonic() < deadline:
                                time.sleep(.01)
                            self.assertEqual(relay.state['count'], 2, 'ACK did not race the held chat')
                            time.sleep(.1)
                            self.assertEqual(seen, [], 'ACK reached upstream before chat was sent')
                    finally:
                        release.set()
                        for worker in workers: worker.join(4)
                    self.assertEqual(errors, [])
                    if unsupported_method:
                        self.assertEqual(results[(unsupported_method, '/denied')], (403, b''))
                        self.assertEqual(results[('POST', transport.CHAT)], (403, b''))
                        self.assertEqual(results[('POST', transport.ACK)], (403, b''))
                        self.assertEqual(seen, [transport.CHAT])
                    else:
                        self.assertEqual(seen, [transport.CHAT, transport.ACK])
                        self.assertEqual(results[('POST', transport.CHAT)], (200, b'data: first\n\n'))
                        self.assertEqual(results[('POST', transport.ACK)], (202, b'{"accepted":true}'))
                self.assertTrue(all(not worker.is_alive() for worker in workers))
            self.assertEqual(list(relay.server._threads), [])
            self.assertTrue(all(connection.sock is None for connection in relay.connections))
        finally:
            release.set()
            for worker in workers: worker.join(4)
            gateway.shutdown(); gateway.server_close(); gateway_thread.join()

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
