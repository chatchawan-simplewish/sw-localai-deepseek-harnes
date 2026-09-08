// Offline characterization: actual pinned authorization body; synthetic external boundaries.
// Run: node scripts/test-native-authorization-contract.mjs <retained-oauth-entries.json>
// Mutation proof: append --mutate-missing-write or --mutate-missing-configured (must fail).
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { runInNewContext } from 'node:vm';

const [capturePath, mutation] = process.argv.slice(2);
assert.ok(capturePath, 'Supply the retained public-source OAuth entries JSON');
assert.ok([undefined, '--mutate-missing-write', '--mutate-missing-configured'].includes(mutation));
const authHash = 'd86547a2f450ff7f58f421f5e2a91eab6abc5ac3dc2ae90cd3785d15547002a3';
const coreHash = '1729cdbf8ee40b17c8839e06bf96491490548559e11ef7e411271e0754e751c5';
const digest = (source) => createHash('sha256').update(source).digest('hex');
const entries = JSON.parse(readFileSync(capturePath, 'utf8'));
const matches = entries.filter((entry) => entry.sha256 === authHash);
assert.equal(matches.length, 1, 'Exactly one pinned authorization source is required');
let source = matches[0].source;
assert.equal(digest(source), authHash, 'Authorization source hash mismatch');
const core = JSON.parse(readFileSync(new URL('../docs/evidence/vm105-native-core-source-2026-09-09.json', import.meta.url), 'utf8'));
assert.equal(core.source.sha256, coreHash);
assert.equal(digest(core.capture.source), coreHash, 'Cordis source hash mismatch');

// No provider imports, filesystem, network, or real credential store enter this context.
assert.equal((source.match(/^import .+;$/gm) ?? []).length, 2);
source = source.replace('import { Service } from "@deepseek-ai/cordis";', '')
  .replace('import { HarnessError } from "@deepseek-ai/dsh-llm";', '')
  .replace('export { AuthorizationDeclinedError, AuthorizationError, AuthorizationService, AuthorizationService as default };', 'AuthorizationService;');
if (mutation) {
  const guard = mutation === '--mutate-missing-write'
    ? /^\t\tif \(!observed\.committed\) throw .+;$/m
    : /^\t\tif \(!\(await this\.ctx\.credentials\.describeRecord\(flow\.key\)\)\.configured\) throw .+;$/m;
  assert.ok(guard.test(source), 'Mutation target must exist');
  source = source.replace(guard, '');
}
class SyntheticService { constructor(ctx) { this.ctx = ctx; } }
class SyntheticHarnessError extends Error {
  constructor(message, code, options) { super(message, options); this.code = code; }
}
const AuthorizationService = runInNewContext(source, {
  Service: SyntheticService, HarnessError: SyntheticHarnessError, AbortController,
}, { timeout: 1000 });

async function check(name, configured, eventKey, expected, configureDuringRun = false) {
  const listeners = new Set();
  const settlements = [];
  const ctx = {
    credentials: { async describeRecord(key) { assert.equal(key, 'synthetic'); return { configured }; } },
    on(event, listener) {
      assert.equal(event, 'credentials/record-updated');
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    effect(factory) {
      const generator = factory();
      const cleanup = generator.next().value;
      return () => { cleanup(); generator.return(); };
    },
    events: { dispatch(_mode, [event]) {
      assert.equal(event, 'authorization/settled');
      return [(_key, status) => settlements.push(status)];
    } },
    logger: { warn() { assert.fail('Unexpected authorization warning'); } },
  };
  const authorization = new AuthorizationService(ctx);
  const dispose = authorization.registerFlow({
    key: 'synthetic', label: 'Offline synthetic', methods: [{ id: 'synthetic', label: 'Offline' }],
    async run() {
      if (configureDuringRun) configured = true;
      if (eventKey) for (const listener of listeners) listener(eventKey);
    },
  });
  const request = { key: 'synthetic', interaction: {
    notify() { assert.fail('No notices expected'); },
    async prompt() { assert.fail('No prompts permitted'); },
  } };
  if (expected === 'authorized') assert.equal((await authorization.begin(request)).status, expected, name);
  else await assert.rejects(authorization.begin(request), (error) => error.code === 'NOT_COMMITTED', name);
  assert.equal(listeners.size, 0, `${name}: watcher removed`);
  assert.equal(authorization.describe('synthetic').inFlight, false, `${name}: attempt released`);
  assert.deepEqual(settlements, [expected === 'authorized' ? 'authorized' : 'failed']);
  dispose();
  assert.equal(authorization.describe('synthetic'), undefined);
}

await check('existing configured record without fresh write is rejected', true, undefined, 'rejected');
await check('wrong record update is rejected', true, 'unrelated', 'rejected');
await check('update without configured record is rejected', false, 'synthetic', 'rejected');
await check('fresh configured record update is accepted', false, 'synthetic', 'authorized', true);
console.log('PASS: 4 offline authorization contract cases; pinned sources verified. Cordis injection and real credentials NOT PROVEN.');
