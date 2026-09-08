import assert from 'node:assert/strict';
import fs from 'node:fs';
import net from 'node:net';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawn } from 'node:child_process';
import { apply, privateDirectory, frames, send } from './native-codex-owner.mjs';

// Synthetic transport checks only; the reviewed launcher supplies containment.
const KEY = 'llm-pi-ai/openai-codex';
const MARKER = 'SYNTHETIC_REPLACEMENT\n';
const tick = () => new Promise(resolve => setImmediate(resolve));
const code = value => fs.writeSync(1, value + '\n');
const checks = {};
const replacementStages = ['replacement_bind', 'replacement_rename', 'replacement_dispose'];
function replacementFailure(output) {
  try {
    const value = JSON.parse(output);
    return value && Object.keys(value).length === 2 && value.status === 'LINUX_BRIDGE_FAIL'
      && replacementStages.includes(value.stage) ? value.stage : undefined;
  } catch { return undefined; }
}
let stage = 'arguments';
function fatal() { try { code(JSON.stringify({ status: 'LINUX_BRIDGE_FAIL', stage })); } finally { process.exit(1); } }
process.on('uncaughtException', fatal);
process.on('unhandledRejection', fatal);
const deadline = setTimeout(fatal, 25000);
function bounded(promise, ms = 2000) {
  let timer;
  return Promise.race([promise, new Promise((_, reject) => { timer = setTimeout(() => reject(Error('DEADLINE')), ms); })])
    .finally(() => clearTimeout(timer));
}
function context(run) {
  const calls = [];
  return { calls, credentials: Object.freeze({}),
    authorization: {
      describe: key => { assert.equal(key, KEY); return { key: KEY, methods: [{ id: 'oauth' }], inFlight: false }; },
      begin: request => { calls.push(request); return run(request); },
    },
  };
}
function checkFile(file, expected) {
  const actual = fs.lstatSync(file);
  assert.ok(actual.isFile()); assert.equal(actual.uid, process.getuid());
  assert.equal(actual.mode & 0o7777, 0o600);
  assert.equal(actual.dev, expected.dev); assert.equal(actual.ino, expected.ino);
  assert.equal(fs.readFileSync(file, 'utf8'), MARKER);
}
function marker(file) {
  fs.writeFileSync(file, MARKER, { flag: 'wx', mode: 0o600 });
  return fs.lstatSync(file);
}
function absent(file) { assert.throws(() => fs.lstatSync(file), { code: 'ENOENT' }); }
async function connect(socketPath) {
  const socket = net.createConnection(socketPath); const queue = []; let pending; let failed = false;
  const reject = () => { failed = true; pending?.reject(Error('TRANSPORT')); pending = undefined; };
  frames(socket, value => { if (pending) { const waiter = pending; pending = undefined; waiter.resolve(value); } else queue.push(value); }, reject);
  socket.on('error', reject);
  socket.on('close', reject);
  await bounded(new Promise((resolve, rejectConnect) => { socket.once('connect', resolve); socket.once('error', rejectConnect); }));
  return { socket, next() {
    if (queue.length) return Promise.resolve(queue.shift());
    if (failed) return Promise.reject(Error('TRANSPORT'));
    assert.equal(pending, undefined);
    return bounded(new Promise((resolve, rejectNext) => { pending = { resolve, reject: rejectNext }; }));
  } };
}
async function owned(root) {
  stage = 'owned_bind';
  const socketPath = path.join(root, 'flow.sock');
  const ctx = context(async ({ key, method, interaction, signal }) => {
    assert.equal(key, KEY); assert.equal(method, 'oauth'); assert.ok(signal instanceof AbortSignal);
    interaction.notify({ message: 'SYNTHETIC_NOTICE' });
    assert.equal(await interaction.prompt({ kind: 'select', message: 'SYNTHETIC_CHOICE', options: [
      { id: 'browser', label: 'Browser' }, { id: 'device_code', label: 'Device' },
    ] }), 'device_code');
    return { status: 'authorized' };
  });
  const dispose = await bounded(apply(ctx, { socketPath }));
  const stat = fs.lstatSync(socketPath);
  assert.ok(stat.isSocket()); assert.equal(stat.mode & 0o7777, 0o600); assert.equal(stat.uid, process.getuid());
  assert.equal(ctx.calls.length, 0);
  stage = 'owned_connect';
  const client = await connect(socketPath);
  try {
    await tick(); assert.equal(ctx.calls.length, 0); checks.passiveSocket0600 = true;
    stage = 'owned_flow';
    send(client.socket, { type: 'begin' });
    assert.deepEqual(await client.next(), { type: 'notice', message: 'SYNTHETIC_NOTICE' });
    const prompt = await client.next();
    assert.deepEqual(prompt, { type: 'prompt', id: 1, kind: 'select', message: 'SYNTHETIC_CHOICE', options: [{ id: 'device_code', label: 'Device' }] });
    send(client.socket, { type: 'answer', id: prompt.id, value: 'device_code' });
    assert.deepEqual(await client.next(), { type: 'result', status: 'authorized' });
    assert.equal(ctx.calls.length, 1);
    const second = await connect(socketPath);
    try { await bounded(new Promise(resolve => { if (second.socket.destroyed) resolve(); else second.socket.once('close', resolve); })); }
    finally { second.socket.destroy(); }
    assert.equal(ctx.calls.length, 1); checks.fakeDeviceFlowOnce = true;
    stage = 'owned_dispose';
  } finally { client.socket.destroy(); await bounded(Promise.resolve(dispose())); }
  await tick(); absent(socketPath); checks.ownedSocketRemoved = true;
}
async function disconnect(root) {
  stage = 'disconnect_bind';
  const socketPath = path.join(root, 'disconnect.sock'); let cancelled;
  const done = new Promise(resolve => { cancelled = resolve; });
  const ctx = context(async ({ interaction }) => {
    try { await interaction.prompt({ kind: 'text', message: 'SYNTHETIC_PENDING' }); }
    catch (error) { assert.equal(error.message, 'CANCELLED'); cancelled(); throw error; }
  });
  const dispose = await bounded(apply(ctx, { socketPath }));
  const client = await connect(socketPath);
  try {
    stage = 'disconnect_flow';
    send(client.socket, { type: 'begin' }); assert.equal((await client.next()).type, 'prompt');
    client.socket.destroy(); await bounded(done);
    assert.equal(ctx.calls.length, 1); assert.equal(ctx.calls[0].signal.aborted, true);
    stage = 'disconnect_dispose';
    await bounded(Promise.resolve(dispose())); await tick(); absent(socketPath);
    checks.disconnectAbortAndDispose = true;
  } finally { client.socket.destroy(); await bounded(Promise.resolve(dispose())); }
}
async function replacementChild(root) {
  stage = 'replacement_bind';
  const socketPath = path.join(root, 'replacement.sock');
  absent(socketPath); absent(path.join(root, 'retained.sock'));
  const ctx = context(() => { throw Error('UNEXPECTED_BEGIN'); });
  const dispose = await bounded(apply(ctx, { socketPath }));
  stage = 'replacement_rename';
  fs.renameSync(socketPath, path.join(root, 'retained.sock'));
  fs.renameSync(path.join(root, 'replacement.fixture'), socketPath);
  stage = 'replacement_dispose';
  await bounded(Promise.resolve(dispose())); assert.equal(ctx.calls.length, 0);
  code('REPLACEMENT_CHILD_DONE');
  // Natural exit exercises Node's exit cleanup; do not force process.exit here.
}
async function replacement(root) {
  stage = 'replacement_spawn';
  const original = marker(path.join(root, 'replacement.fixture'));
  await bounded(new Promise((resolve, reject) => {
    const child = spawn(process.execPath, [fileURLToPath(import.meta.url), root, '--replacement-child'], {
      env: {}, stdio: ['ignore', 'pipe', 'ignore'], timeout: 5000, killSignal: 'SIGKILL',
    });
    let output = ''; let overflow = false;
    child.stdout.on('data', data => { if (output.length + data.length > 128) { overflow = true; child.kill('SIGKILL'); } else output += data.toString('utf8'); });
    child.on('error', reject);
    child.on('close', (status, signal) => {
      if (status === 0 && signal === null && !overflow && output === 'REPLACEMENT_CHILD_DONE\n') resolve();
      else {
        const failedStage = !overflow && replacementFailure(output);
        if (failedStage) stage = failedStage;
        reject(Error('CHILD_FAILED'));
      }
    });
  }), 7000);
  stage = 'replacement_preserve';
  checkFile(path.join(root, 'replacement.sock'), original);
  assert.ok(fs.lstatSync(path.join(root, 'retained.sock')).isSocket());
  checks.replacementPreservedAfterExit = true;
}
async function main() {
  if (process.argv.length === 3 && process.argv[2] === '--self-test') {
    assert.equal(replacementFailure('{"status":"LINUX_BRIDGE_FAIL","stage":"replacement_dispose"}'), 'replacement_dispose');
    for (const bad of ['null', '[]', '{', '{"status":"LINUX_BRIDGE_FAIL","stage":"secret"}',
      '{"status":"LINUX_BRIDGE_FAIL","stage":"replacement_bind","secret":"extra"}',
      '{"status":"LINUX_BRIDGE_FAIL","stage":[]}']) assert.equal(replacementFailure(bad), undefined);
    code('SELF_TEST_PASS'); return;
  }
  const [root, mode, ...extra] = process.argv.slice(2);
  assert.equal(process.platform, 'linux'); assert.equal(extra.length, 0);
  assert.ok(mode === undefined || mode === '--replacement-child');
  assert.equal(typeof root, 'string'); assert.ok(path.isAbsolute(root)); assert.equal(path.normalize(root), root);
  // Validate the prepared root and all ancestors with the bridge's actual policy.
  stage = 'root_policy';
  const held = privateDirectory(path.join(root, 'validation.sock')); fs.closeSync(held.fd);
  if (mode) { await replacementChild(root); return; }
  stage = 'empty_root';
  for (const name of ['flow.sock', 'disconnect.sock', 'preexisting.sock', 'replacement.fixture', 'replacement.sock', 'retained.sock']) absent(path.join(root, name));
  await owned(root); await disconnect(root);
  stage = 'preexisting';
  const preexisting = path.join(root, 'preexisting.sock'); const identity = marker(preexisting);
  const ctx = context(() => { throw Error('UNEXPECTED_BEGIN'); });
  await assert.rejects(apply(ctx, { socketPath: preexisting }), { message: 'OWNER_BRIDGE_UNAVAILABLE' });
  assert.equal(ctx.calls.length, 0); checkFile(preexisting, identity); checks.preexistingPreserved = true;
  await replacement(root); stage = 'complete'; code(JSON.stringify({ status: 'LINUX_BRIDGE_PASS', checks }));
}
main().then(() => clearTimeout(deadline), fatal);
