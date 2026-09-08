import net from 'node:net';
import fs from 'node:fs';
import path from 'node:path';

export const name = 'native-codex-owner';
export const inject = ['authorization', 'credentials'];
const KEY = 'llm-pi-ai/openai-codex';
export const limits = Object.freeze({ frame: 16384, queue: 65536, answer: 4096, promptMs: 180000, sessionMs: 1200000 });
const fail = code => new Error(code);
export function fields(value, required, optional = []) {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
    && required.every(key => Object.hasOwn(value, key))
    && Object.keys(value).every(key => required.includes(key) || optional.includes(key));
}
export const boundedString = (value, max = limits.frame) => typeof value === 'string' && Buffer.byteLength(value) <= max;
export function send(socket, message) {
  const frame = JSON.stringify(message);
  if (Buffer.byteLength(frame) > limits.frame || socket.destroyed
    || socket.writableLength + Buffer.byteLength(frame) + 1 > limits.queue
    || !socket.write(frame + '\n')) throw fail('TRANSPORT');
}
export function frames(socket, receive, invalid) {
  let buffer = Buffer.alloc(0);
  const data = chunk => {
    try {
      if (!Buffer.isBuffer(chunk)) throw fail('PROTOCOL');
      let start = 0;
      while (start < chunk.length && !socket.destroyed) {
        const newline = chunk.indexOf(10, start);
        const end = newline < 0 ? chunk.length : newline;
        if (buffer.length + end - start > limits.frame) throw fail('PROTOCOL');
        buffer = Buffer.concat([buffer, chunk.subarray(start, end)]);
        if (newline < 0) break;
        const line = new TextDecoder('utf-8', { fatal: true }).decode(buffer);
        buffer = Buffer.alloc(0); receive(JSON.parse(line)); start = end + 1;
      }
    } catch { invalid(); }
  };
  socket.on('data', data);
  return () => { buffer = Buffer.alloc(0); socket.off('data', data); };
}

function noticeData(notice) {
  if (!fields(notice, ['message'], ['url', 'code']) || !Object.values(notice).every(value => boundedString(value))) throw fail('INTERACTION');
  return { type: 'notice', ...notice };
}
function promptData(prompt, id) {
  if (!fields(prompt, ['kind', 'message'], ['options', 'placeholder', 'signal']) || !boundedString(prompt.message)) throw fail('INTERACTION');
  const result = { type: 'prompt', id, kind: prompt.kind, message: prompt.message };
  if (prompt.kind === 'select') {
    if (prompt.placeholder !== undefined || !Array.isArray(prompt.options) || !prompt.options.length || prompt.options.length > 64
      || !prompt.options.every(option => fields(option, ['id', 'label']) && boundedString(option.id, limits.answer) && option.id.length && boundedString(option.label))
      || new Set(prompt.options.map(option => option.id)).size !== prompt.options.length) throw fail('INTERACTION');
    // The browser/callback path has no release approval. The server enforces the choice.
    const deviceChoice = prompt.options.some(option => ['browser', 'device_code'].includes(option.id));
    result.options = deviceChoice ? prompt.options.filter(option => option.id === 'device_code') : prompt.options;
    if (!result.options.length) throw fail('DEVICE_REQUIRED');
  } else {
    if (!['text', 'secret'].includes(prompt.kind) || prompt.options !== undefined) throw fail('INTERACTION');
    if (prompt.placeholder !== undefined) {
      if (!boundedString(prompt.placeholder)) throw fail('INTERACTION');
      result.placeholder = prompt.placeholder;
    }
  }
  return result;
}

// One account-private conversation and one consumed attempt per plugin lifetime.
export function createOwner(ctx) {
  let connected = false; let disposed = false; let shutdown;
  return {
    connect(socket) {
      if (connected || disposed) { socket.on('error', () => {}); socket.destroy(); return; }
      connected = true;
      const controller = new AbortController();
      let begun = false; let ended = false; let pending; let nextId = 0;
      const sessionTimer = setTimeout(() => stop('TIMEOUT'), limits.sessionMs);
      const rejectPending = () => {
        if (!pending) return;
        const old = pending; pending = undefined; old.cleanup(); old.reject(fail('CANCELLED'));
      };
      const cleanup = () => { clearTimeout(sessionTimer); removeFrames(); rejectPending(); };
      function stop(code) {
        if (ended) return;
        ended = true; controller.abort(fail('CANCELLED')); cleanup();
        // No native completion claim: native cancellation can race a late credential write.
        if (code === 'CANCELLED') {
          try { send(socket, { type: 'result', status: 'cancelled' }); socket.end(); } catch { socket.destroy(); }
          const closeTimer = setTimeout(() => socket.destroy(), 1000); closeTimer.unref();
        } else socket.destroy();
      }
      function result(message) {
        if (ended) return;
        try { send(socket, message); } catch { stop('TRANSPORT'); return; }
        ended = true; cleanup(); socket.end();
        const closeTimer = setTimeout(() => socket.destroy(), 1000); closeTimer.unref();
      }
      const interaction = {
        notify(notice) {
          if (ended) return;
          try { send(socket, noticeData(notice)); } catch { stop('INTERACTION'); }
        },
        prompt(prompt) {
          return new Promise((resolve, reject) => {
            try {
              if (ended || controller.signal.aborted) throw fail('CANCELLED');
              if (pending) throw fail('INTERACTION');
              const message = promptData(prompt, ++nextId);
              const signal = prompt.signal;
              if (signal !== undefined && !(signal instanceof AbortSignal)) throw fail('INTERACTION');
              if (signal?.aborted) throw fail('CANCELLED');
              const withdraw = () => {
                if (pending?.id !== message.id) return;
                rejectPending();
                try { send(socket, { type: 'withdraw', id: message.id }); } catch { stop('TRANSPORT'); }
              };
              const timer = setTimeout(() => stop('TIMEOUT'), limits.promptMs);
              pending = { id: message.id, message, resolve, reject, cleanup: () => { clearTimeout(timer); signal?.removeEventListener('abort', withdraw); } };
              signal?.addEventListener('abort', withdraw, { once: true });
              send(socket, message);
            } catch { reject(fail('CANCELLED')); stop('INTERACTION'); }
          });
        },
      };
      async function begin() {
        try {
          const descriptor = ctx.authorization?.describe(KEY);
          if (!ctx.credentials || descriptor?.key !== KEY || descriptor.inFlight !== false
            || !Array.isArray(descriptor.methods) || !descriptor.methods.some(method => method.id === 'oauth')) {
            result({ type: 'error', code: 'UNAVAILABLE' }); return;
          }
          const outcome = await ctx.authorization.begin({ key: KEY, method: 'oauth', interaction, signal: controller.signal });
          if (!['authorized', 'cancelled'].includes(outcome?.status)) throw fail('AUTH_FAILED');
          result({ type: 'result', status: outcome.status });
        } catch { result({ type: 'error', code: 'AUTH_FAILED' }); }
      }
      const removeFrames = frames(socket, message => {
        if (ended) return;
        if (fields(message, ['type']) && message.type === 'begin' && !begun) { begun = true; void begin(); return; }
        if (fields(message, ['type']) && message.type === 'cancel') { stop('CANCELLED'); return; }
        if (!begun || !pending || !Number.isSafeInteger(message?.id) || message.id !== pending.id) throw fail('PROTOCOL');
        if (fields(message, ['type', 'id']) && message.type === 'decline') { stop('CANCELLED'); return; }
        if (!fields(message, ['type', 'id', 'value']) || message.type !== 'answer' || !boundedString(message.value, limits.answer)
          || (pending.message.kind === 'select' && !pending.message.options.some(option => option.id === message.value))) throw fail('PROTOCOL');
        const old = pending; pending = undefined; old.cleanup(); old.resolve(message.value);
      }, () => stop('PROTOCOL'));
      socket.on('error', () => stop('TRANSPORT'));
      socket.on('end', () => stop('DISCONNECTED'));
      socket.on('close', () => stop('DISCONNECTED'));
      shutdown = () => stop('DISPOSED');
    },
    dispose() { disposed = true; shutdown?.(); },
  };
}

export function checkMetadata(stat, uid, kind) {
  if (stat.isSymbolicLink() || (stat.uid !== uid && !(kind === 'ancestor' && stat.uid === 0))) throw fail('UNSAFE_SOCKET');
  if (kind === 'socket') {
    if (!stat.isSocket() || (stat.mode & 0o7777) !== 0o600) throw fail('UNSAFE_SOCKET');
  } else if (!stat.isDirectory() || (kind === 'private' ? (stat.mode & 0o7777) !== 0o700 : (stat.mode & 0o022) !== 0)) throw fail('UNSAFE_SOCKET');
}
export function privateDirectory(socketPath) {
  if (process.platform !== 'linux' || typeof socketPath !== 'string' || !path.isAbsolute(socketPath)
    || path.normalize(socketPath) !== socketPath || !/^[a-zA-Z0-9._-]+$/.test(path.basename(socketPath))) throw fail('UNSAFE_SOCKET');
  const uid = process.getuid(); const directory = path.dirname(socketPath);
  let ancestor = directory;
  for (;;) {
    checkMetadata(fs.lstatSync(ancestor), uid, ancestor === directory ? 'private' : 'ancestor');
    if (path.dirname(ancestor) === ancestor) break;
    ancestor = path.dirname(ancestor);
  }
  const fd = fs.openSync(directory, fs.constants.O_RDONLY | fs.constants.O_DIRECTORY | fs.constants.O_NOFOLLOW);
  try {
    checkMetadata(fs.fstatSync(fd), uid, 'private');
    const stat = fs.lstatSync(directory); const held = fs.fstatSync(fd);
    if (stat.dev !== held.dev || stat.ino !== held.ino) throw fail('UNSAFE_SOCKET');
    return { fd, uid, anchored: `/proc/self/fd/${fd}/${path.basename(socketPath)}` };
  } catch { fs.closeSync(fd); throw fail('UNSAFE_SOCKET'); }
}

export function releaseSocket(server, held, identity) {
    // net.Server.close auto-unlinks its bind pathname. Never call it on a replaced path.
    // The held private parent prevents an ancestor rename from redirecting cleanup.
    // Same-UID malicious mutation is outside the account boundary; this is not race-free against it.
    try {
      const current = fs.lstatSync(held.anchored);
      checkMetadata(current, held.uid, 'socket');
      if (current.dev !== identity.dev || current.ino !== identity.ino) throw fail('UNSAFE_SOCKET');
      fs.unlinkSync(held.anchored);
      server.close(() => fs.closeSync(held.fd));
    } catch {
      // ponytail: retain handle on identity conflict; audited process retirement must resolve it.
      server?.unref();
    }
}

export async function apply(ctx, config) {
  let held; let server; let identity; let bridge; let released = false;
  const dispose = () => {
    if (released) return; released = true; bridge?.dispose();
    if (!held) return;
    if (!identity) { if (!server?.listening) fs.closeSync(held.fd); else server.unref(); return; }
    releaseSocket(server, held, identity);
  };
  try {
    if (!fields(config, ['socketPath']) || !ctx.authorization || !ctx.credentials) throw fail('UNAVAILABLE');
    held = privateDirectory(config.socketPath);
    try { fs.lstatSync(held.anchored); throw fail('UNSAFE_SOCKET'); } catch (error) { if (error.code !== 'ENOENT') throw error; }
    bridge = createOwner(ctx);
    server = net.createServer(socket => bridge.connect(socket));
    await new Promise((resolve, reject) => {
      server.once('error', reject);
      server.listen(held.anchored, () => { server.off('error', reject); resolve(); });
    });
    identity = fs.lstatSync(held.anchored);
    if (!identity.isSocket() || identity.uid !== held.uid) throw fail('UNSAFE_SOCKET');
    fs.chmodSync(held.anchored, 0o600);
    checkMetadata(fs.lstatSync(held.anchored), held.uid, 'socket');
    server.on('error', dispose);
    return dispose;
  } catch { dispose(); throw fail('OWNER_BRIDGE_UNAVAILABLE'); }
}
