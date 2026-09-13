"""Two-request loopback relay, socket handoff, and binding preflight."""
import argparse
import array
import hashlib
import http.client
import http.server
import ipaddress
import json
import socket
import threading
import urllib.parse

GATEWAY = 'http://192.168.1.68:20128/v1'
TUPLE = ('taskId', 'runId', 'turnId', 'idempotencyKey')
CHAT = '/v1/chat/completions'
ACK = '/v1/agent-routes/events'
GATEWAY_FD_MESSAGE = b'VM105_GATEWAY_FDS_V1 chat ack'


def receive_gateway_sockets(control, expected_ip, expected_port):
    """Receive the fixed chat/ACK TCP pair from one Unix control socket."""
    if (not getattr(socket, 'SCM_RIGHTS', None) or not getattr(socket, 'AF_UNIX', None) or
            not getattr(socket, 'CMSG_SPACE', None) or not getattr(socket, 'MSG_CMSG_CLOEXEC', None)):
        raise RuntimeError('SCM_RIGHTS close-on-exec Unix descriptor passing is unavailable')
    if (getattr(control, 'family', None) != socket.AF_UNIX or
            getattr(control, 'type', 0) & socket.SOCK_STREAM != socket.SOCK_STREAM or
            not callable(getattr(control, 'recvmsg', None))):
        raise ValueError('gateway socket handoff rejected')
    try:
        expected = (str(ipaddress.ip_address(expected_ip)), int(expected_port))
        if not 0 < expected[1] < 65536:
            raise ValueError()
    except (TypeError, ValueError):
        raise ValueError('gateway socket handoff rejected') from None

    itemsize = array.array('i').itemsize
    wrapped = []
    try:
        payload, ancillary, flags, _ = control.recvmsg(
            len(GATEWAY_FD_MESSAGE) + 1, socket.CMSG_SPACE(itemsize * 3),
            socket.MSG_CMSG_CLOEXEC)
        values = []
        valid_ancillary = bool(ancillary)
        for level, kind, data in ancillary:
            if level != socket.SOL_SOCKET or kind != socket.SCM_RIGHTS:
                valid_ancillary = False
                continue
            rights = array.array('i')
            complete = len(data) - len(data) % itemsize
            rights.frombytes(data[:complete])
            values.extend(rights)
            if complete != len(data):
                valid_ancillary = False
        for index, descriptor in enumerate(values):
            try:
                wrapped.append(socket.socket(fileno=descriptor))
            except OSError:
                for unopened in values[index:]:
                    try:
                        socket.close(unopened)
                    except OSError:
                        pass
                raise
        if payload != GATEWAY_FD_MESSAGE or flags or not valid_ancillary or len(wrapped) != 2:
            raise ValueError()
        for stream in wrapped:
            peer = stream.getpeername()
            actual = (str(ipaddress.ip_address(peer[0])), int(peer[1]))
            if (stream.family not in (socket.AF_INET, socket.AF_INET6) or
                    stream.proto != socket.IPPROTO_TCP or stream.get_inheritable() or
                    stream.getsockopt(socket.SOL_SOCKET, socket.SO_TYPE) != socket.SOCK_STREAM or
                    actual != expected):
                raise ValueError()
        return tuple(wrapped)
    except (AttributeError, IndexError, OSError, TypeError, ValueError):
        for stream in wrapped:
            stream.close()
        raise ValueError('gateway socket handoff rejected') from None


class TwoRequestRelay:
    """Two-request relay backed by fixture connections or an accepted socket pair."""
    def __init__(self, gateway_base, key='fixture-key-not-secret', timeout=3, upstream_sockets=None):
        target = urllib.parse.urlsplit(gateway_base)
        fixture = upstream_sockets is None
        if target.scheme != 'http' or target.path != '/v1' or target.query or target.fragment or target.username or not target.hostname or not isinstance(key, str) or not key or '\r' in key or '\n' in key or (fixture and (target.hostname != '127.0.0.1' or key != 'fixture-key-not-secret')):
            raise ValueError('fixture binding required')
        if not fixture and len(upstream_sockets) != 2:
            raise ValueError('production socket pair required')
        self.target, self.timeout = target, timeout
        self.key = key
        self.upstream_sockets = [] if fixture else list(upstream_sockets)
        self.claimed_upstreams = [False, False]
        self.lock, self.ack = threading.Lock(), threading.Event()
        self.chat_forwarded = threading.Event()
        self.state = {'count': 0, 'tuple': None, 'failed': False, 'committed': False, 'output': False}
        self.connections = []
        relay = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def deny(self, send=True):
                with relay.lock:
                    if not relay.state['output']:
                        relay.state['failed'] = True
                        relay._close_upstream_sockets()
                relay.ack.set()
                relay.chat_forwarded.set()
                if send:
                    self.send_response(403)
                    self.end_headers()

            def __getattr__(self, name):
                if name.startswith('do_'):
                    return self.deny
                raise AttributeError(name)

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
                        upstream = relay._upstream_connection(n)
                    if self.path == ACK and not relay.chat_forwarded.wait(relay.timeout):
                        raise ValueError()
                    with relay.lock:
                        if relay.state['failed']:
                            raise ValueError()
                    upstream.request('POST', self.path, body, {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + relay.key})
                    response = upstream.getresponse()
                    if self.path == ACK:
                        accepted = response.status == 202 and json.loads(response.read(4097)) == {'accepted': True}
                        if not accepted:
                            raise ValueError()
                        sent = True
                        self.send_response(202)
                        self.send_header('Content-Length', '17')
                        self.end_headers()
                        self.wfile.write(b'{"accepted":true}')
                        self.wfile.flush()
                        with relay.lock:
                            if relay.state['failed']:
                                raise ValueError()
                            relay.state['committed'] = True
                        relay.ack.set()
                    else:
                        if response.status != 200:
                            raise ValueError()
                        # Response headers prove the chat reached the gateway before ACK forwarding.
                        relay.chat_forwarded.set()
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
                    self.deny(send=not sent)
                finally:
                    if 'upstream' in locals():
                        upstream.close()

        self.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.server.daemon_threads = False
        self.address = self.server.server_address
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={'poll_interval': .02})

    @classmethod
    def from_socket_handoff(cls, control, gateway_ip, gateway_port, key, timeout=3):
        if not isinstance(key, str) or not key or '\r' in key or '\n' in key:
            control.close()
            raise ValueError('production key binding required')
        try:
            streams = receive_gateway_sockets(control, gateway_ip, gateway_port)
        finally:
            control.close()
        try:
            ip = ipaddress.ip_address(gateway_ip)
            host = '[%s]' % ip if ip.version == 6 else str(ip)
            return cls('http://%s:%s/v1' % (host, gateway_port), key, timeout, streams)
        except Exception:
            for stream in streams:
                stream.close()
            raise

    def _upstream_connection(self, index):
        if not self.upstream_sockets:
            upstream = http.client.HTTPConnection('127.0.0.1', self.target.port, timeout=self.timeout)
        else:
            if index not in (0, 1) or self.claimed_upstreams[index]:
                raise ValueError('production socket already assigned')
            self.claimed_upstreams[index] = True
            upstream = http.client.HTTPConnection(self.target.hostname, self.target.port, timeout=self.timeout)
            self.upstream_sockets[index].settimeout(self.timeout)
            upstream.sock = self.upstream_sockets[index]
        self.connections.append(upstream)
        return upstream

    def _close_upstream_sockets(self):
        for stream in self.upstream_sockets:
            stream.close()

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *args):
        with self.lock:
            if not self.state['output']:
                self.state['failed'] = True
        self.ack.set()
        self.chat_forwarded.set()
        self.server.shutdown()
        self.thread.join()
        # Non-daemon handlers are joined by server_close before owned connections close.
        self.server.server_close()
        with self.lock:
            for connection in self.connections:
                connection.close()
            self._close_upstream_sockets()


def valid_manifest(manifest, expected_hash):
    def sha(value):
        return isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value)

    def pinned(row):
        return isinstance(row, dict) and all(isinstance(row.get(k), str) and row[k] for k in ('logicalPath', 'canonicalPath')) and sha(row.get('sha256'))

    try:
        if manifest['status'] != 'PASS' or not sha(expected_hash) or manifest['canonicalManifestSha256'] != expected_hash:
            return False
        for key in ('packages', 'modules', 'entrypoints', 'configBundles'):
            if not isinstance(manifest[key], list) or not manifest[key]:
                return False
        if not all(isinstance(p, dict) and all(isinstance(p.get(k), str) and p[k] for k in ('name', 'version', 'logicalPath', 'canonicalPath')) for p in manifest['packages']):
            return False
        paths = []
        for row in manifest['modules']:
            path = row['stagedRelativePath']
            if not isinstance(path, str) or not path.startswith('modules/') or '..' in path.split('/') or '\\' in path or not sha(row['sha256']) or not all(isinstance(row.get(k), str) and row[k] for k in ('sourceLogicalPath', 'sourceCanonicalPath')):
                return False
            paths.append(path)
        if paths != sorted(set(paths)):
            return False
        if not all(pinned(row) for row in manifest['entrypoints'] + manifest['configBundles']):
            return False
        runtime = manifest['runtime']
        if not pinned(runtime['node']) or not isinstance(runtime['dependencies'], list) or not runtime['dependencies'] or not all(pinned(row) for row in runtime['dependencies']):
            return False
        content = {k: v for k, v in manifest.items() if k != 'canonicalManifestSha256'}
        return hashlib.sha256(json.dumps(content, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')).hexdigest() == expected_hash
    except (KeyError, TypeError, ValueError):
        return False


def production_preflight(gateway_base, key_reference, manifest, expected_hash=None):
    closure = valid_manifest(manifest, expected_hash)
    key_present = isinstance(key_reference, str) and bool(key_reference.strip())
    bound = gateway_base == GATEWAY and key_present and closure
    return {'status': 'PREFLIGHT_ONLY' if bound else 'BLOCKED', 'gatewayBase': GATEWAY if gateway_base == GATEWAY else None, 'endpointBound': gateway_base == GATEWAY, 'keyReferencePresent': key_present, 'closurePass': closure, 'clientInvoked': False}


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
        assert not list(relay.server._threads) and relay.server.socket.fileno() == -1
        assert all(connection.sock is None for connection in relay.connections + clients)
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
    parser.add_argument('--expected-manifest-sha256')
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
        result = production_preflight(args.gateway_base, args.key_reference, manifest, args.expected_manifest_sha256)
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(2 if result['status'] == 'BLOCKED' else 0)
