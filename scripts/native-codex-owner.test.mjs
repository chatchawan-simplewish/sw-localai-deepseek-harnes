import assert from 'node:assert/strict';
import { EventEmitter } from 'node:events';
import { test } from 'node:test';
import fs from 'node:fs';

const owner = await import('./native-codex-owner.mjs').catch(() => ({}));
const terminal = await import('./native-codex-terminal.mjs').catch(() => ({}));
const tick = () => new Promise(resolve => setImmediate(resolve));
class Socket extends EventEmitter {
  writableLength = 0; destroyed = false; frames = []; blocked = false;
  write(frame) { if (this.throwWrite) throw Error('SYNTHETIC_SECRET'); this.frames.push(JSON.parse(frame)); return !this.blocked; }
  end() { this.ended = true; }
  destroy() { this.destroyed = true; this.emit('close'); }
  send(value) { this.emit('data', Buffer.from(typeof value === 'string' ? value : JSON.stringify(value) + '\n')); }
}
function setup(run = async () => ({ status: 'authorized' }), descriptor) {
  assert.equal(typeof owner.createOwner, 'function', 'offline owner implementation exists');
  const calls = [];
  const ctx = { credentials: {}, authorization: {
    describe: () => descriptor ?? { key: 'llm-pi-ai/openai-codex', methods: [{ id: 'oauth' }], inFlight: false },
    begin: request => { calls.push(request); return run(request); },
  } };
  const bridge = owner.createOwner(ctx); const socket = new Socket(); bridge.connect(socket);
  return { bridge, socket, calls };
}
test('passive connection and one native committed outcome, never a credential read', async () => {
  const { bridge, socket, calls } = setup();
  assert.equal(calls.length, 0); socket.send({ type: 'begin' }); await tick();
  assert.equal(calls.length, 1); assert.deepEqual(Object.keys(calls[0]).sort(), ['interaction', 'key', 'method', 'signal']);
  assert.equal(calls[0].key, 'llm-pi-ai/openai-codex'); assert.equal(calls[0].method, 'oauth');
  assert.ok(calls[0].signal instanceof AbortSignal);
  assert.deepEqual(socket.frames, [{ type: 'result', status: 'authorized' }]);
  const other = new Socket(); bridge.connect(other); other.send({ type: 'begin' });
  assert.equal(calls.length, 1); assert.equal(other.destroyed, true); bridge.dispose();
});
test('descriptor and raw provider errors fail closed with fixed results', async () => {
  for (const descriptor of [{ key: 'wrong', methods: [{ id: 'oauth' }] }, { key: 'llm-pi-ai/openai-codex', methods: [] }, { key: 'llm-pi-ai/openai-codex', methods: [{ id: 'oauth' }], inFlight: true }]) {
    const { bridge, socket, calls } = setup(undefined, descriptor); socket.send({ type: 'begin' }); await tick();
    assert.equal(calls.length, 0); assert.deepEqual(socket.frames, [{ type: 'error', code: 'UNAVAILABLE' }]); bridge.dispose();
  }
  const { bridge, socket } = setup(async () => { throw Error('SYNTHETIC_SECRET'); });
  socket.send({ type: 'begin' }); await tick(); assert.deepEqual(socket.frames, [{ type: 'error', code: 'AUTH_FAILED' }]); bridge.dispose();
});
test('device selection enforced by server; native signals omitted and withdraw prompt', async () => {
  const signal = new AbortController(); let answer;
  const { bridge, socket } = setup(async ({ interaction }) => {
    interaction.notify({ message: 'private', url: 'https://example.invalid', code: 'SYNTHETIC' });
    answer = await interaction.prompt({ kind: 'select', message: 'Choose', options: [{ id: 'browser', label: 'Browser' }, { id: 'device_code', label: 'Device' }], signal: signal.signal });
    await interaction.prompt({ kind: 'text', message: 'Code', signal: signal.signal });
    return { status: 'authorized' };
  });
  socket.send({ type: 'begin' }); await tick();
  assert.deepEqual(socket.frames[1], { type: 'prompt', id: 1, kind: 'select', message: 'Choose', options: [{ id: 'device_code', label: 'Device' }] });
  socket.send({ type: 'answer', id: 1, value: 'device_code' }); await tick(); assert.equal(answer, 'device_code');
  signal.abort(Error('SYNTHETIC_SECRET')); await tick();
  assert.deepEqual(socket.frames[3], { type: 'withdraw', id: 2 });
  assert.ok(!JSON.stringify(socket.frames).includes('SYNTHETIC_SECRET')); bridge.dispose();
});
test('browser, invalid IDs, duplicates, oversized answers and unknown fields abort', async () => {
  for (const bad of [{ type: 'answer', id: 1, value: 'browser' }, { type: 'answer', id: 2, value: 'device_code' }, { type: 'answer', id: 1, value: 'x'.repeat(4097) }, { type: 'answer', id: 1, value: 'device_code', extra: true }, { type: 'begin' }]) {
    const { bridge, socket, calls } = setup(async ({ interaction }) => { await interaction.prompt({ kind: 'select', message: 'Choose', options: [{ id: 'browser', label: 'Browser' }, { id: 'device_code', label: 'Device' }] }); return { status: 'authorized' }; });
    socket.send({ type: 'begin' }); await tick(); socket.send(bad); await tick();
    assert.equal(calls[0].signal.aborted, true); assert.equal(socket.destroyed, true); assert.ok(!socket.frames.some(f => f.status === 'authorized')); bridge.dispose();
  }
  const { bridge, socket } = setup(async ({ interaction }) => { await interaction.prompt({ kind: 'text', message: 'Code' }); return new Promise(() => {}); });
  socket.send({ type: 'begin' }); await tick(); socket.send({ type: 'answer', id: 1, value: 'SYNTHETIC' }); socket.send({ type: 'answer', id: 1, value: 'SYNTHETIC' });
  assert.equal(socket.destroyed, true); bridge.dispose();
});
test('framing rejects malformed UTF-8, unterminated oversized bytes and unsolicited messages', () => {
  for (const frame of ['{\n', 'x'.repeat(16385), JSON.stringify({ type: 'answer', id: 1, value: 'x' }) + '\n']) {
    const { bridge, socket, calls } = setup(); socket.send(frame); assert.equal(socket.destroyed, true); assert.equal(calls.length, 0); bridge.dispose();
  }
  const { bridge, socket } = setup(); socket.emit('data', Buffer.from([0xff, 0x0a])); assert.equal(socket.destroyed, true); bridge.dispose();
});
test('callback errors never escape; write backpressure stops native flow', async () => {
  for (const mode of ['throw', 'blocked', 'queue', 'notice']) {
    let threw = false;
    const { bridge, socket, calls } = setup(async ({ interaction }) => {
      try { interaction.notify(mode === 'notice' ? { message: 'x'.repeat(17000) } : { message: 'SYNTHETIC' }); } catch { threw = true; }
      return { status: 'authorized' };
    });
    socket.throwWrite = mode === 'throw'; socket.blocked = mode === 'blocked'; socket.writableLength = mode === 'queue' ? 65536 : 0;
    socket.send({ type: 'begin' }); await tick();
    assert.equal(threw, false); assert.equal(calls[0].signal.aborted, true); assert.equal(socket.destroyed, true); bridge.dispose();
  }
});
test('cancel, decline, disconnect and disposal reject pending prompt with sanitized reason', async () => {
  for (const action of ['cancel', 'decline', 'disconnect', 'dispose']) {
    let rejection;
    const { bridge, socket, calls } = setup(async ({ interaction }) => {
      try { await interaction.prompt({ kind: 'secret', message: 'Private' }); } catch (error) { rejection = error.message; throw error; }
    });
    socket.send({ type: 'begin' }); await tick();
    if (action === 'disconnect') socket.destroy(); else if (action === 'dispose') bridge.dispose(); else socket.send(action === 'decline' ? { type: action, id: 1 } : { type: action });
    await tick(); assert.equal(calls[0].signal.aborted, true); assert.equal(rejection, 'CANCELLED');
    if (action === 'cancel' || action === 'decline') assert.deepEqual(socket.frames.at(-1), { type: 'result', status: 'cancelled' }); bridge.dispose();
  }
});
test('terminal refuses capture, escapes control characters and hides/restores input', async () => {
  assert.equal(typeof terminal.hiddenInput, 'function', 'private terminal implementation exists');
  assert.throws(() => terminal.requirePrivateTTY({ isTTY: false }, { isTTY: true }), /PRIVATE_TTY_REQUIRED/);
  assert.equal(terminal.safeText('a\x1b[2J\r\n\x07b'), 'a\\u001b[2J\\u000d\\u000a\\u0007b');
  for (const action of ['answer', 'abort']) {
    const input = new EventEmitter(); input.isTTY = true; input.isRaw = false; input.setRawMode = raw => { input.isRaw = raw; }; input.resume = () => {}; input.pause = () => {};
    const output = { isTTY: true, write: () => { throw Error('input must never be echoed'); } };
    const signal = new AbortController(); const pending = terminal.hiddenInput(input, output, signal.signal);
    assert.equal(input.isRaw, true); input.emit('data', Buffer.from('SYNTHETIC'));
    if (action === 'answer') { input.emit('data', Buffer.from('\r')); assert.equal(await pending, 'SYNTHETIC'); }
    else { signal.abort(); await assert.rejects(pending, /CANCELLED/); }
    assert.equal(input.isRaw, false); assert.equal(input.listenerCount('data'), 0);
  }
});
test('Linux metadata rules reject wrong owner, loose modes, links and unexpected socket', () => {
  assert.equal(typeof owner.checkMetadata, 'function');
  const directory = { uid: 1000, mode: 0o40700, isSymbolicLink: () => false, isDirectory: () => true, isSocket: () => false };
  assert.doesNotThrow(() => owner.checkMetadata(directory, 1000, 'private'));
  for (const changed of [{ uid: 5 }, { mode: 0o40750 }, { isSymbolicLink: () => true }]) assert.throws(() => owner.checkMetadata({ ...directory, ...changed }, 1000, 'private'));
  assert.throws(() => owner.checkMetadata({ ...directory, mode: 0o40777 }, 1000, 'ancestor'));
  assert.throws(() => owner.checkMetadata(directory, 1000, 'socket'));
});
test('whole-session and pending-prompt deadlines abort without retry', async t => {
  t.mock.timers.enable({ apis: ['setTimeout'] });
  for (const prompt of [false, true]) {
    const { bridge, socket, calls } = setup(async ({ interaction }) => {
      if (prompt) await interaction.prompt({ kind: 'text', message: 'Code' });
      return new Promise(() => {});
    });
    socket.send({ type: 'begin' }); await tick();
    t.mock.timers.tick(prompt ? 179999 : 1199999); assert.equal(socket.destroyed, false);
    t.mock.timers.tick(1); await tick(); assert.equal(socket.destroyed, true); assert.equal(calls[0].signal.aborted, true); bridge.dispose();
  }
});
test('fragmented UTF-8 frames work and answer limit counts bytes', async () => {
  let answer;
  const { bridge, socket } = setup(async ({ interaction }) => {
    answer = await interaction.prompt({ kind: 'text', message: 'Code' }); return { status: 'authorized' };
  });
  socket.send('{"type":'); socket.send('"begin"}\n'); await tick();
  const frame = Buffer.from(JSON.stringify({ type: 'answer', id: 1, value: 'é' }) + '\n');
  const split = frame.indexOf(0xc3) + 1;
  socket.emit('data', frame.subarray(0, split)); socket.emit('data', frame.subarray(split)); await tick();
  assert.equal(answer, 'é'); assert.equal(socket.frames.at(-1).status, 'authorized'); bridge.dispose();
  const second = setup(async ({ interaction }) => interaction.prompt({ kind: 'text', message: 'Code' }));
  second.socket.send({ type: 'begin' }); await tick(); second.socket.send({ type: 'answer', id: 1, value: 'é'.repeat(2049) });
  assert.equal(second.socket.destroyed, true); second.bridge.dispose();
});
test('malformed native callbacks and duplicate pending prompt reject only safe errors', async () => {
  for (const bad of [{ kind: 'text', message: 'x', unknown: 'SYNTHETIC_SECRET' }, { kind: 'select', message: 'x', options: [{ id: 'browser', label: 'Browser' }] }]) {
    let rejection;
    const { bridge, socket } = setup(async ({ interaction }) => {
      try { await interaction.prompt(bad); } catch (error) { rejection = error.message; }
      return { status: 'authorized' };
    });
    socket.send({ type: 'begin' }); await tick(); assert.equal(rejection, 'CANCELLED'); assert.equal(socket.destroyed, true); bridge.dispose();
  }
  const { bridge, socket } = setup(async ({ interaction }) => {
    const first = interaction.prompt({ kind: 'text', message: 'x' });
    const second = interaction.prompt({ kind: 'secret', message: 'y' });
    const results = await Promise.allSettled([first, second]);
    assert.ok(results.every(result => result.status === 'rejected' && result.reason.message === 'CANCELLED'));
    return { status: 'authorized' };
  });
  socket.send({ type: 'begin' }); await tick(); assert.equal(socket.destroyed, true); bridge.dispose();
});
test('hidden input restores after write-free edit, invalid UTF-8, interrupt and limit', async () => {
  for (const data of [Buffer.from([0xff]), Buffer.from('\x03'), Buffer.from('é'.repeat(2049))]) {
    const input = new EventEmitter(); input.isTTY = true; input.isRaw = false; input.setRawMode = raw => { input.isRaw = raw; }; input.resume = () => {}; input.pause = () => {};
    const pending = terminal.hiddenInput(input, { isTTY: true }); input.emit('data', data);
    await assert.rejects(pending, /CANCELLED/); assert.equal(input.isRaw, false);
  }
});
test('owned socket cleanup preserves identity conflicts before Node automatic unlink', t => {
  assert.equal(typeof owner.releaseSocket, 'function', 'socket ownership cleanup is testable without binding Linux sockets');
  const identity = { uid: 1000, mode: 0o140600, dev: 1, ino: 2, isSymbolicLink: () => false, isSocket: () => true };
  let current = identity; const actions = [];
  t.mock.method(fs, 'lstatSync', () => current);
  t.mock.method(fs, 'unlinkSync', () => actions.push('unlink'));
  t.mock.method(fs, 'closeSync', () => actions.push('fd-close'));
  const server = { close: callback => { actions.push('server-close'); callback(); }, unref: () => actions.push('retained') };
  owner.releaseSocket(server, { uid: 1000, fd: 10, anchored: '/proc/self/fd/10/owner.sock' }, identity);
  assert.deepEqual(actions, ['unlink', 'server-close', 'fd-close']); actions.length = 0;
  current = { ...identity, ino: 3 };
  owner.releaseSocket(server, { uid: 1000, fd: 10, anchored: '/proc/self/fd/10/owner.sock' }, identity);
  assert.deepEqual(actions, ['retained']);
});
test('terminal protocol renders data safely, restores on withdrawal and disconnect, rejects unsafe frames', async () => {
  assert.equal(typeof terminal.ownerTerminal, 'function');
  for (const action of ['withdraw', 'disconnect', 'browser', 'unknown', 'success']) {
    const socket = new Socket(); const input = new EventEmitter();
    input.isTTY = true; input.isRaw = false; input.setRawMode = raw => { input.isRaw = raw; }; input.resume = () => {}; input.pause = () => {};
    const writes = []; const output = Object.assign(new EventEmitter(), { isTTY: true, writableLength: 0, write: value => { writes.push(value); return true; } });
    const done = terminal.ownerTerminal(socket, input, output); socket.emit('connect');
    assert.deepEqual(socket.frames, [{ type: 'begin' }]);
    socket.send({ type: 'notice', message: '\x1b[2JSYNTHETIC' }); assert.equal(writes[0], '\\u001b[2JSYNTHETIC\n');
    if (action === 'browser') socket.send({ type: 'prompt', id: 1, kind: 'select', message: 'x', options: [{ id: 'browser', label: 'Browser' }] });
    else if (action === 'unknown') socket.send({ type: 'notice', message: 'x', secret: 'SYNTHETIC' });
    else {
      socket.send({ type: 'prompt', id: 1, kind: 'text', message: 'Code' }); assert.equal(input.isRaw, true);
      input.emit('data', Buffer.from('SYNTHETIC_INPUT'));
      if (action === 'withdraw') { socket.send({ type: 'withdraw', id: 1 }); assert.equal(input.isRaw, false); socket.send({ type: 'result', status: 'cancelled' }); }
      else if (action === 'disconnect') socket.destroy();
      else { input.emit('data', Buffer.from('\r')); await tick(); assert.deepEqual(socket.frames.at(-1), { type: 'answer', id: 1, value: 'SYNTHETIC_INPUT' }); socket.send({ type: 'result', status: 'authorized' }); }
    }
    assert.equal(await done, action === 'success' ? 0 : 1); assert.equal(input.isRaw, false);
    assert.ok(!writes.join('').includes('SYNTHETIC_INPUT')); assert.equal(input.listenerCount('data'), 0);
  }
});
test('asynchronous terminal stream errors cancel safely and restore hidden input', async () => {
  for (const stream of ['output', 'input']) for (const activePrompt of [true, false]) {
    const socket = new Socket(); const input = new EventEmitter();
    input.isTTY = true; input.isRaw = false; input.setRawMode = raw => { input.isRaw = raw; }; input.resume = () => {}; input.pause = () => {};
    const writes = []; const output = Object.assign(new EventEmitter(), { isTTY: true, writableLength: 0, write: value => { writes.push(value); return true; } });
    const done = terminal.ownerTerminal(socket, input, output); socket.emit('connect');
    if (activePrompt) { socket.send({ type: 'prompt', id: 1, kind: 'secret', message: 'Private' }); assert.equal(input.isRaw, true); }
    await tick();
    try {
      assert.doesNotThrow(() => (stream === 'output' ? output : input).emit('error', Error('SYNTHETIC_SECRET')));
      assert.equal(await done, 1); assert.equal(socket.destroyed, true);
      assert.deepEqual(socket.frames.at(-1), { type: 'cancel' });
      assert.equal(input.isRaw, false); assert.equal(input.listenerCount('data'), 0);
      assert.equal(input.listenerCount('error'), 0); assert.equal(output.listenerCount('error'), 0);
      assert.ok(!writes.join('').includes('SYNTHETIC_SECRET'));
    } finally { socket.destroy(); await done; }
  }
});
