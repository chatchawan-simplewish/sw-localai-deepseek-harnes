"""Loopback fixture relay and non-executing final-client binding preflight."""
import argparse
import http.client
import http.server
import json
import socket
import threading
import urllib.parse

GATEWAY = 'http://192.168.1.68:20128/v1'
TUPLE = ('taskId', 'runId', 'turnId', 'idempotencyKey')
CHAT = '/v1/chat/completions'
ACK = '/v1/agent-routes/events'


class TwoRequestRelay:
    """Fixture only. Production namespace/socket handoff is intentionally unimplemented."""
    def __init__(self, gateway_base, key='fixture-key-not-secret', timeout=3):
        target = urllib.parse.urlsplit(gateway_base)
        if target.scheme != 'http' or target.hostname != '127.0.0.1' or target.path != '/v1' or target.query or target.fragment or target.username or key != 'fixture-key-not-secret':
            raise ValueError('fixture binding required')
        self.target, self.timeout = target, timeout
        self.lock, self.ack = threading.Lock(), threading.Event()
        self.state = {'count': 0, 'tuple': None, 'failed': False, 'committed': False, 'output': False}
        self.connections = []
        relay = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                sent = False
                self.connection.settimeout(relay.timeout)
                try:
                    lengths = self.headers.get_all('Content-Length', [])
                    if len(lengths) != 1 or self.headers.get('Transfer-Encoding') or not 0 < int(lengths[0]) <= 65536:
                        raise ValueError()
                    body = self.rfile.read(int(lengths[0]))
                    data = json.loads(body)
                    identity = tuple(data.get(k) for k in TUPLE)
                    if not all(isinstance(v, str) and v.strip() for v in identity):
                        raise ValueError()
                    with relay.lock:
                        n = relay.state['count']
                        valid = not relay.state['failed'] and ((n == 0 and self.path == CHAT and data.get('model') == 'agent/normal' and data.get('stream') is True and data.get('tools') == [] and data.get('tool_choice') == 'none') or (n == 1 and self.path == ACK and data.get('event') == 'output_started' and identity == relay.state['tuple']))
                        if not valid:
                            raise ValueError()
                        relay.state['count'] += 1
                        relay.state['tuple'] = identity
                        upstream = http.client.HTTPConnection('127.0.0.1', relay.target.port, timeout=relay.timeout)
                        relay.connections.append(upstream)
                    upstream.request('POST', self.path, body, {'Content-Type': 'application/json', 'Authorization': 'Bearer fixture-key-not-secret'})
                    response = upstream.getresponse()
                    if self.path == ACK:
                        accepted = response.status == 202 and json.loads(response.read(4097)) == {'accepted': True}
                        with relay.lock:
                            relay.state['committed'] = accepted and not relay.state['failed']
                        relay.ack.set()
                        if not relay.state['committed']:
                            raise ValueError()
                        self.send_response(202)
                        self.end_headers()
                        self.wfile.write(b'{"accepted":true}')
                    else:
                        if response.status != 200:
                            raise ValueError()
                        first = response.read(1)
                        if not first or not relay.ack.wait(relay.timeout):
                            raise ValueError()
                        with relay.lock:
                            if not relay.state['committed'] or relay.state['failed']:
                                raise ValueError()
                            relay.state['output'] = True
                        sent = True
                        self.send_response(200)
                        self.send_header('Content-Type', 'text/event-stream')
                        self.end_headers()
                        self.wfile.write(first)
                        self.wfile.flush()
                        while chunk := response.read1(4096):
                            self.wfile.write(chunk)
                            self.wfile.flush()
                except (ValueError, TypeError, AttributeError, OSError, http.client.HTTPException):
                    with relay.lock:
                        relay.state['failed'] = True
                    relay.ack.set()
                    if not sent:
                        self.send_response(403)
                        self.end_headers()
                finally:
                    if 'upstream' in locals():
                        upstream.close()

            def do_GET(self):
                self.send_response(403)
                self.end_headers()

            do_PUT = do_DELETE = do_PATCH = do_HEAD = do_OPTIONS = do_CONNECT = do_GET

        self.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.address = self.server.server_address
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={'poll_interval': .02})

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *args):
        with self.lock:
            self.state['failed'] = True
        self.ack.set()
        for connection in self.connections:
            connection.close()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()


def production_preflight(gateway_base, key_reference, manifest):
    digest = manifest.get('canonicalManifestSha256', '')
    bound = gateway_base == GATEWAY and isinstance(key_reference, str) and bool(key_reference.strip()) and manifest.get('status') == 'PASS' and isinstance(digest, str) and len(digest) == 64 and all(c in '0123456789abcdef' for c in digest)
    return {'status': 'PREFLIGHT_ONLY' if bound else 'BLOCKED', 'gatewayBase': GATEWAY if gateway_base == GATEWAY else None, 'endpointBound': gateway_base == GATEWAY, 'keyReferencePresent': bool(key_reference and key_reference.strip()), 'closurePass': manifest.get('status') == 'PASS', 'clientInvoked': False}


def run_fixture_regression():
    seen, output, errors = [], [], []
    chat_arrived, ack_arrived, release_ack, output_arrived = (threading.Event() for _ in range(4))
    identity = {'taskId': 'fixture-task', 'runId': 'fixture-run', 'turnId': 'fixture-turn', 'idempotencyKey': 'fixture-once'}

    class Gateway(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            data = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            seen.append((self.path, data, self.headers.get('Authorization')))
            if self.path == CHAT:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'data: first\n\n')
                self.wfile.flush()
                chat_arrived.set()
                release_ack.wait(3)
            else:
                ack_arrived.set()
                release_ack.wait(3)
                self.send_response(202)
                self.end_headers()
                self.wfile.write(b'{"accepted":true}')

    gateway = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Gateway)
    gateway_thread = threading.Thread(target=gateway.serve_forever, kwargs={'poll_interval': .02})
    gateway_thread.start()
    clients = []

    def post(address, path, data):
        connection = http.client.HTTPConnection(*address, timeout=4)
        clients.append(connection)
        try:
            connection.request('POST', path, json.dumps(data), {'Content-Type': 'application/json'})
            response = connection.getresponse()
            if path == CHAT:
                first = response.read(1)
                if first:
                    output_arrived.set()
                result = (response.status, first + response.read())
                output.append(result)
            else:
                result = (response.status, response.read())
            return result
        except Exception as exc:
            errors.append(type(exc).__name__)
        finally:
            connection.close()

    workers = []
    try:
        with TwoRequestRelay('http://127.0.0.1:%s/v1' % gateway.server_port) as relay:
            chat = threading.Thread(target=post, args=(relay.address, CHAT, dict(identity, model='agent/normal', stream=True, tools=[], tool_choice='none')))
            workers.append(chat)
            chat.start()
            assert chat_arrived.wait(2), 'chat missing'
            ack = threading.Thread(target=post, args=(relay.address, ACK, dict(identity, event='output_started')))
            workers.append(ack)
            ack.start()
            assert ack_arrived.wait(2), 'ACK missing'
            assert not output_arrived.wait(.15), 'output escaped before ACK'
            release_ack.set()
            for worker in workers:
                worker.join(4)
            assert not errors and output == [(200, b'data: first\n\n')]
            third = post(relay.address, ACK, dict(identity, event='output_started'))
            assert third == (403, b'') and len(seen) == 2
            assert [row[0] for row in seen] == [CHAT, ACK]
            assert all({k: row[1][k] for k in TUPLE} == identity for row in seen)
            assert all(row[2] == 'Bearer fixture-key-not-secret' for row in seen)
            committed = relay.state['committed']
        probe = socket.socket()
        try:
            assert probe.connect_ex(relay.address) != 0
        finally:
            probe.close()
        assert not relay.thread.is_alive() and all(not worker.is_alive() for worker in workers)
        return dict(status='PASS', requestCount=len(seen), tupleEquality=True, ackBeforeOutput=True, progressCommitted=committed, resumeRequired=False, thirdRequestDenied=True, cleanupComplete=True, retries=0, redirects=0, discovery=0, catalog=0, directProvider=0, tools=0)
    finally:
        release_ack.set()
        for connection in clients:
            connection.close()
        gateway.shutdown()
        gateway.server_close()
        gateway_thread.join()
        for worker in workers:
            worker.join(4)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixture-regression', action='store_true')
    parser.add_argument('--gateway-base')
    parser.add_argument('--key-reference')
    parser.add_argument('--manifest')
    args = parser.parse_args()
    if args.fixture_regression:
        result = run_fixture_regression()
    else:
        try:
            with open(args.manifest, encoding='utf-8') as source:
                manifest = json.load(source)
            if not isinstance(manifest, dict):
                manifest = {}
        except (OSError, TypeError, ValueError):
            manifest = {}
        result = production_preflight(args.gateway_base, args.key_reference, manifest)
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(2 if result['status'] == 'BLOCKED' else 0)
