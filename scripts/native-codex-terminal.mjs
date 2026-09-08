import net from 'node:net';
import fs from 'node:fs';
import { pathToFileURL } from 'node:url';
import { fields, boundedString, frames, send, limits, privateDirectory, checkMetadata } from './native-codex-owner.mjs';

export function requirePrivateTTY(input, output) {
  if (!input.isTTY || !output.isTTY || typeof input.setRawMode !== 'function') throw Error('PRIVATE_TTY_REQUIRED');
}
export const safeText = value => value.replace(/[\x00-\x1f\x7f-\x9f\u2028\u2029\u202a-\u202e\u2066-\u2069]/g, char => `\\u${char.charCodeAt(0).toString(16).padStart(4, '0')}`);
export function hiddenInput(input, output, signal) {
  return new Promise((resolve, reject) => {
    let value = ''; const raw = input.isRaw; const decoder = new TextDecoder('utf-8', { fatal: true });
    const finish = (error, answer) => {
      input.off('data', data); input.off('error', abort); input.off('end', abort); signal?.removeEventListener('abort', abort);
      try { input.setRawMode(raw); input.pause(); } catch { error = Error('TERMINAL_FAILED'); }
      value = ''; if (error) reject(error); else resolve(answer);
    };
    const abort = () => finish(Error('CANCELLED'));
    const data = chunk => {
      try {
        for (const char of decoder.decode(chunk, { stream: true })) {
          if (char === '\x03' || char === '\x04' || char === '\x1b') { abort(); return; }
          if (char === '\r' || char === '\n') { finish(undefined, value); return; }
          if (char === '\x7f' || char === '\b') value = [...value].slice(0, -1).join('');
          else if (!/[\x00-\x1f]/.test(char)) value += char;
          if (Buffer.byteLength(value) > limits.answer) { abort(); return; }
        }
      } catch { abort(); }
    };
    try {
      requirePrivateTTY(input, output); if (signal?.aborted) throw Error('CANCELLED');
      input.setRawMode(true); input.on('data', data); input.on('error', abort); input.on('end', abort);
      signal?.addEventListener('abort', abort, { once: true }); input.resume();
    } catch { finish(Error('PRIVATE_TTY_REQUIRED')); }
  });
}

// Launch only in the owner's unrecorded SSH terminal. A TTY cannot prove no recorder exists.
export async function runTerminal(socketPath, input = process.stdin, output = process.stdout) {
  requirePrivateTTY(input, output);
  const held = privateDirectory(socketPath);
  try {
    checkMetadata(fs.lstatSync(held.anchored), held.uid, 'socket');
    return await ownerTerminal(net.createConnection(held.anchored), input, output);
  } finally { fs.closeSync(held.fd); }
}
export async function ownerTerminal(socket, input, output) {
  requirePrivateTTY(input, output);
  let pending; let finished = false; let lastId = 0; let removeFrames; let timer;
  const release = () => {
    pending?.abort(); pending = undefined; clearTimeout(timer); removeFrames?.();
    input.off('error', cancel); output.off('error', cancel);
    process.off('SIGINT', cancel); process.off('SIGTERM', cancel); process.off('SIGHUP', cancel);
    socket.destroy();
  };
  let settle;
  const done = new Promise(resolve => { settle = resolve; });
  const finish = code => { if (finished) return; finished = true; release(); settle(code); };
  const cancel = () => { try { send(socket, { type: 'cancel' }); } catch {} finish(1); };
  const display = value => {
    if (output.writableLength + Buffer.byteLength(value) > limits.queue || !output.write(value)) throw Error('TERMINAL_FAILED');
  };
  try {
    input.on('error', cancel); output.on('error', cancel);
    process.on('SIGINT', cancel); process.on('SIGTERM', cancel); process.on('SIGHUP', cancel);
    timer = setTimeout(cancel, limits.sessionMs);
    socket.on('error', () => finish(1)); socket.on('close', () => finish(1)); socket.on('end', () => finish(1));
    removeFrames = frames(socket, message => {
      if (fields(message, ['type', 'message'], ['url', 'code']) && message.type === 'notice'
        && ['message', 'url', 'code'].every(key => message[key] === undefined || boundedString(message[key]))) {
        display(['message', 'url', 'code'].filter(key => message[key] !== undefined).map(key => safeText(message[key])).join('\n') + '\n'); return;
      }
      if (fields(message, ['type', 'id']) && message.type === 'withdraw' && pending?.id === message.id) { pending.abort(); pending = undefined; return; }
      if (fields(message, ['type', 'status']) && message.type === 'result' && ['authorized', 'cancelled'].includes(message.status)) {
        display(message.status + '\n'); finish(message.status === 'authorized' ? 0 : 1); return;
      }
      if (fields(message, ['type', 'code']) && message.type === 'error' && ['UNAVAILABLE', 'AUTH_FAILED'].includes(message.code)) {
        display(message.code + '\n'); finish(1); return;
      }
      if (!fields(message, ['type', 'id', 'kind', 'message'], ['options', 'placeholder']) || message.type !== 'prompt'
        || pending || !Number.isSafeInteger(message.id) || message.id <= lastId || !boundedString(message.message)
        || !['select', 'text', 'secret'].includes(message.kind)) throw Error('PROTOCOL');
      if (message.kind === 'select') {
        if (message.placeholder !== undefined || !Array.isArray(message.options) || !message.options.length || message.options.length > 64
          || !message.options.every(option => fields(option, ['id', 'label']) && boundedString(option.id, limits.answer) && option.id.length && option.id !== 'browser' && boundedString(option.label))
          || new Set(message.options.map(option => option.id)).size !== message.options.length) throw Error('PROTOCOL');
      } else if (message.options !== undefined || (message.placeholder !== undefined && !boundedString(message.placeholder))) throw Error('PROTOCOL');
      lastId = message.id; const prompt = new AbortController(); prompt.id = message.id; pending = prompt;
      display(safeText(message.message) + '\n');
      if (message.options) display(message.options.map((option, index) => `${index + 1}. ${safeText(option.label)}`).join('\n') + '\n');
      const deadline = setTimeout(cancel, limits.promptMs);
      hiddenInput(input, output, prompt.signal).then(value => {
        if (pending !== prompt || finished) return;
        pending = undefined;
        if (message.kind === 'select') {
          if (!/^[1-9][0-9]*$/.test(value) || !message.options[Number(value) - 1]) { cancel(); return; }
          value = message.options[Number(value) - 1].id;
        }
        try { send(socket, { type: 'answer', id: message.id, value }); } catch { finish(1); }
      }, () => { if (pending === prompt && !finished) cancel(); }).finally(() => clearTimeout(deadline));
    }, () => finish(1));
    socket.on('connect', () => { try { send(socket, { type: 'begin' }); } catch { finish(1); } });
  } catch { finish(1); }
  return done;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  if (process.argv.length !== 3) { process.stderr.write('OWNER_TERMINAL_UNAVAILABLE\n'); process.exitCode = 1; }
  else {
    try { process.exitCode = await runTerminal(process.argv[2]); }
    catch { process.stderr.write('OWNER_TERMINAL_UNAVAILABLE\n'); process.exitCode = 1; }
  }
}
