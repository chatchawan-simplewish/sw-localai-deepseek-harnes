# VM105 native owner bridge — offline implementation

2026-09-09 04:01:13 Asia/Bangkok. Repository: https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git; verified using `git remote get-url origin`. Worktree: `C:/Users/chatc/Projects/sw-localai-deepseek-harnes/.worktrees/vm105-authoritative-roadmap`.

Implementation checks after repair round 1 - 16/16 passing. The latest frozen hashes are in the appended repair section below; the initial hashes and evidence remain as history. Independent re-review and parent acceptance are pending. This is an offline artifact, not an installation or authentication success.

## Scope and source verification

This lane owns only the three files below and this report. Other agents' Python cutover work, existing dirty files and untracked evidence were preserved. No Git commit, SSH, live VM access, package installation, browser, OAuth interaction, profile composition, candidate edit, credential read/write or inference occurred.

The implementation uses Node stdlib exclusively. It exports a passive Cordis `name`, `inject: ['authorization', 'credentials']`, and `apply`; a separately launched terminal provides the owner interaction. There is no separate grant store, custom OAuth, HTTP surface, settings mutation or browser launcher.

Full retained public source strings were reconstructed as UTF-8 and SHA256-checked against their capture records:

| Capture / source | Reconstructed SHA256 | Source contract used |
| --- | --- | --- |
| `C:/Users/chatc/.codex/tmp-typhoon-ocr-adapter.json` / dsh-llm-pi-ai `lib/index.js` | `e183a9cdde703b47485410bd68d247c8becdb277c390f0f91c6dd28718d350e2` | 2156–2168 native OAuth method; 2179–2206 notice message/url/code; 2219–2240 select/text/secret and optional signal; 2267–2281 native registration/run |
| `C:/Users/chatc/.codex/tmp-native-oauth-entries.json` / dsh-authorization `lib/index.js` | `d86547a2f450ff7f58f421f5e2a91eab6abc5ac3dc2ae90cd3785d15547002a3` | 98–109 descriptor; 137–160 begin request/outcome; 198–244 cancellation race and attempt-specific committed-record authorization |
| `C:/Users/chatc/.codex/tmp-native-surface-headless.json` / dsh-app-boot `lib/index.js` | `9d4b7f214cd35b3e8ce4e027b12cca34a416d355577aeacbf08a5b324f0cabb6` | Plan's retained module-loading provenance; no runtime load claimed |

## Frozen implementation hashes

| File | SHA256 |
| --- | --- |
| `scripts/native-codex-owner.mjs` | `90bb452d25d5b6c7c7593e2cfc7c01650069d1d63f4770728bff5ef32935b14b` |
| `scripts/native-codex-terminal.mjs` | `005acd012ca69fd543de902893014965431fd9d4dbb64ada6134b2dc9b92845d` |
| `scripts/native-codex-owner.test.mjs` | `d1ab61da2a7bc93f57ade7017cb23045601017eaba57e33188d35ff962c0f5b9` |

The report hash is supplied separately to the parent after writing, avoiding a self-referential hash.

## Verification evidence

Runtime: local Windows Node `v24.19.0`; no Linux subsystem was used. Initial TDD run failed 00/09 with explicit missing-implementation assertions. First implementation passed 09/09. A subsequent socket-cleanup check failed 13/14 before extracting the lifecycle operation for direct testing, and a terminal-conversation check failed 14/15 before exposing the shared terminal driver. Final checks passed 15/15. Deadline, fragmented UTF-8, malformed-callback and additional hidden-input checks passed when added to the existing implementation; these are supplemental branch coverage, not falsely claimed prior RED failures.

Exact final test command, executed from the worktree above:

```text
node --test --test-reporter=dot scripts/native-codex-owner.test.mjs
...............
```

Exit code: 0. The preceding default-reporter run confirmed tests 15, pass 15, fail 0, cancelled 0, skipped 0, todo 0. All three `.mjs` files also passed `node --check <exact-file>` with no output and exit 0.

Exact captured-terminal refusal check:

```text
node scripts/native-codex-terminal.mjs /not-a-real-socket
OWNER_TERMINAL_UNAVAILABLE
```

Exit code: 1. This ran in captured, noninteractive execution and refused before Linux path/socket access or authentication.

## Spec mapping

| Requirement | Implemented behavior and offline evidence |
| --- | --- |
| Passive native integration | No begin on connection. Checks exact key, OAuth method and no existing native in-flight attempt, then calls only `ctx.authorization.begin({ key: 'llm-pi-ai/openai-codex', method: 'oauth', interaction, signal })`. Tests assert request shape and no credential reads. Only returned native `authorized` is reported as authorized. |
| One conversation / attempt | First connection consumes the conversation; first begin consumes the attempt. Reconnects are destroyed, repeated begins rejected, cancellation does not reset state. |
| Bounded finite transport | Strict JSON-line schemas; fatal UTF-8 decode; 16KiB frame, 64KiB queued output, 4096-byte answer, one outstanding prompt, 180-second prompt and 1200-second session deadlines. Oversized partial lines, unknown fields, malformed input, wrong/duplicate IDs and invalid selections close the conversation and abort. False write/backpressure return also closes instead of growing a queue. |
| Device restriction | The server removes browser from browser/device choices and only accepts offered `device_code`; browser-only prompts fail. Client independently rejects browser options. Other ordinary native selection IDs remain possible. No browser callback or tunnelling is implemented. |
| Native callback handling | Notice maps only message/url/code. Prompt retains signal locally and omits it from wire data. Signal abortion withdraws the outstanding prompt and rejects with fixed `CANCELLED`. `notify` catches synchronous validation/serialization/write failure; `prompt` always returns a Promise and exposes only fixed sanitized errors. |
| Cancellation / disposal | Cancel/decline abort this attempt; disconnect/disposal/deadline reject pending input. Native decline class is not invented or emulated. Late native outcomes after local end cannot produce authorized. No settlement listeners or shared credential-write wrappers are installed. |
| Owner terminal | Requires input/output TTY and raw-input capability. Displays escaped control/bidi characters, never opens links and hides all text/secret/selection input. Restores original raw mode on answer, withdrawal, error, input interruption, disconnect and handled process signals. Synthetic terminal driver tests verify private input is absent from display output. |
| Socket ownership | Linux-only. Requires existing 0700 parent owned by current UID; ancestors must be nonsymlink directories owned by root/current UID without group/world writes. Existing socket names are refused. Holds the private directory descriptor, binds through `/proc/self/fd/<fd>/<name>`, sets socket 0600 and checks expected owner/type. Disposal checks saved socket device/inode before unlink. Metadata tests and cleanup tests simulate Linux objects, not native Linux permissions. |
| Unknown-object preservation | Node `net.Server.close` may automatically unlink its bind pathname. Cleanup explicitly unlinks only the verified saved socket before closing; if identity/type/owner/mode checks fail, it does not call close/unlink and retains the parent FD plus unreferenced listener. Fake filesystem/server tests verify the conflict path invokes only `unref`. This intentionally retains resources until a reviewed retirement operation resolves the conflict. |

## Limits and next review

Socket permissions enforce the VM account boundary, not a unique human versus other processes with the same UID or root. The held-directory strategy prevents ancestor pathname changes from redirecting the server's bound cleanup path, but does not claim race-free deletion against malicious same-UID mutation between identity check, unlink and Node automatic cleanup. Identity-conflict retention, `/proc/self/fd` binding/connect/close behavior, Linux owner/mode enforcement and native process retirement remain NOT PROVEN until a bounded native Linux check. Installation must verify the account is an appropriate trust boundary and no unexpected socket objects are present.

TTY detection refuses simple captured execution; it cannot detect terminal recorders or prove that a particular human exclusively owns a TTY. Actual use must occur in the owner's private unrecorded SSH terminal, outside Codex tools/output. The implementation does not launch that terminal or browse a provider page.

The native seam races cancellation with provider unwinding. A cancelled result does not prove the absence of a late native credential write. The one-attempt lock remains spent, with no automatic retry or credential wrapper.

Effective candidate `.credentials.yaml` selection, absence of ambient credential fallbacks, installed flow registration, plugin load/disposal wiring, exact existing profile row identity, device eligibility/connectivity, owner consent, native credential commit and all three model routes remain NOT PROVEN. This bridge does not accept a store-path parameter because the native begin seam has none. Candidate overrides and pilot-cutover readiness are unchanged.

Parent should obtain independent implementation review of these frozen hashes before acceptance. A later exact installation/composition packet must retain whole config objects and proven row IDs. Browser authorization remains an unavailable switch until separately verified callback requirements are met; no option here silently enables it.

## Repair round 1 of 5 — asynchronous terminal stream errors

2026-09-09 04:11:27 Asia/Bangkok. Read the complete independent review `vm105-native-owner-bridge-review-2026-09-09.md`; its confirmed P2 identified asynchronous output error events bypassing terminal restoration. The review report was not edited.

The client now owns one input and one output `error` listener for the conversation lifetime, installed before any terminal write. Both route directly through sanitized cancellation/finish without rendering the underlying error. Cleanup removes only those owned listeners. This also covers input errors between prompts; hiddenInput already covered them while a prompt was pending.

A new EventEmitter-based regression check first failed with 15/16 passing and the expected thrown synthetic output error. After the two-line lifecycle repair it passes for output/input errors both during a hidden prompt and before a prompt. It verifies no escaping exception, exit status 1, a fixed cancel frame, destroyed socket, restored raw mode, no input-data/error or output-error listener leak, and no raw synthetic error in terminal output. No live service, credentials or actual terminal was used.

Exact final repair command and output:

```text
node --test --test-reporter=dot scripts/native-codex-owner.test.mjs
................
```

Exit code: 0. `node --check scripts/native-codex-owner.mjs`, `node --check scripts/native-codex-terminal.mjs` and `node --check scripts/native-codex-owner.test.mjs` each completed with no output and exit 0.

This freeze supersedes the original implementation hash table:

| File | SHA256 |
| --- | --- |
| `scripts/native-codex-owner.mjs` (unchanged) | `90bb452d25d5b6c7c7593e2cfc7c01650069d1d63f4770728bff5ef32935b14b` |
| `scripts/native-codex-terminal.mjs` | `9e9bf70f8c6e4088f66ac573ce2bf89a60971d30b4f9ea3000aface4af33b458` |
| `scripts/native-codex-owner.test.mjs` | `973f22c2e782ac2108d627ed2e843f92cc723337b3895762b1a9b47a2c1a9b23` |

Cordis handling of late dispose-listener registration, async apply returning teardown, injection withdrawal and disposal during listen activation remains **NOT PROVEN**. The retained app-boot evidence delegates these mechanics to external Cordis; no actual-core proof establishes either compatibility or a bug here. This repair makes no lifecycle compatibility claim and no owner-plugin change. Actual Linux sockets/runtime, selected-store binding, owner authentication and routes remain NOT PROVEN. No commit, runtime integration test, SSH, installation or live action was performed; any later actual-runtime/no-auth check requires its separately reviewed packet and is outside this lane.
