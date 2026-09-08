# VM105 native Codex OAuth readiness — 2026-09-09

Captured 2026-09-09 Asia/Bangkok; exact source-read times not retained. Repository: https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git. Assigned worktree baseline: `0416eeab484b9d6f39032906865bd02f98f12837`.

**Result: no native OAuth login entrypoint was established in the examined installed Web Models/API path. Backend capability exists, but its human interaction bridge remains an unresolved prerequisite in this bounded source chain. Native authentication, effective isolated storage, runtime access and CRED-01 remain NOT PROVEN.**

- Additional public source investigation - 08/08 allowed files consumed.
- Existing ledger source hashes matched before excerpts were consumed. No roadmap completion count changes.

## Supported seam and missing surface

`dsh-authorization/lib/index.js:58–65,90–100,137–160` implements the internal authorization service, listing/describing flows and `begin(request)` with a key, optional method, interaction notice/prompt handlers and cancellation signal. This is not an owner CLI command or HTTP endpoint. It requires credentials injection. Lines208–244 require a credential-record update during the attempt and configured record status before returning authorized; an old record alone is insufficient.

`dsh-llm-pi-ai/lib/index.js:2156–2168,2243–2281,2429–2431` registers native flows when the authorization seam is mounted, independently of configured routes. The Codex flow key is `llm-pi-ai/openai-codex`, method `oauth`. The three requested models share this provider-level native grant. Their catalog identifiers remain the previously recorded prerequisite evidence; no account/model-access test was repeated.

The examined `dsh-client-ui-settings-models/lib/client.js` excerpts establish API-key editing and API-key status dots at1701–1711 and2528–2536. They do not establish an authorization/OAuth/login entrypoint. The blank-input placeholder permits environment authentication; it does not establish native-login initiation or native grant status.

`dsh-host-apiproxy/lib/index.js:3427–3455,4438–4452,4761–4772,5419–5424` exposes credential-reference describe/set/unset. These excerpts do not establish OAuth start/list/status transport or authorization-seam binding. The unrelated attachment-authorization error at2796 is not such an endpoint. Its retained manifest dependencies47–81 omit the authorization seam. No authorization registration was established from the examined web manifest and web/base patch captures. The supported conclusion is that this investigation did not establish the required bridge in the examined Models/API path; it is not a whole-installation or whole-file absence proof.

There is no supported owner click sequence established for this Web surface. A usable native integration must first establish the mounted authorization service and an owner interaction transport that invokes its lifecycle and renders its notices and select/text/secret prompts privately. This is a technical prerequisite. Routine in-plan integration work remains covered by the owner's standing preapproval; actual private authentication/consent remains owner-only. This bounded read-only lane did not implement an integration or install a replacement.

## Store binding and isolation

The adapter at1811–1813,1852–1905,2416–2419 maps pi-ai native grants and refresh operations to Harness credential records through `ctx.credentials`. A missing credential service refuses writes. The previously pinned selector/store trace establishes the selected-home local credential default, explicit path/home overrides, and ambient process/cwd authentication exceptions. Active overrides and effective isolation remain independently unproven; no profile, credential or environment was read here.

The installed pi-ai CLI is unsuitable as a Harness-binding substitute: `dist/cli.js:5–21,37–66,85–104` calls provider OAuth directly and reads/writes cwd-relative `auth.json`, bypassing Harness credential records. It prints interaction URLs/codes. It was not executed; no auth.json was inspected or copied.

## Callback and owner prerequisites

`dist/providers/openai-codex.js:6–15` selects native OAuth and the ChatGPT backend base. The explicit lazy-loader chain resolves its Node OAuth module. The exported `dist/oauth.js` is empty. The actual flow states Node-only execution at1–16; it cannot simply execute inside browser UI.

- Device-code: `dist/auth/oauth/openai-codex.js:419–437` prompts for browser/device selection;341–351 emits the owner verification instruction, polls and exchanges. Constants23–31 name auth.openai.com device endpoints and a 15-minute timeout. No localhost callback listener is needed, but the owner must privately authenticate and consent. Server/account eligibility remains NOT PROVEN;153–154 explicitly handles unavailable device login.
- Browser:26,36–38,244–317,353–411 use `http://localhost:1455/auth/callback`, default listener `127.0.0.1:1455`, callback-state validation, PKCE exchange and manual code/redirect input. A VM105 flow with Bell-PC2 Chrome needs a separately verified loopback SSH forward or secure owner manual-input surface; the existing3080 tunnel does not forward1455. Neither was created.
- Both branches need authentication endpoint connectivity and subsequent token refresh. This lane made no provider HTTP requests. Prior backend-base transport evidence does not establish auth endpoint access.
- Error handling at96–104,152–167,193–196,207–223 can include raw response bodies. A future owner surface must sanitize evidence/log output. No private response or provider error was generated here.

Conditional service sequence once the missing surface and isolated binding are proven: begin the Codex flow using oauth; render its method choice; let the owner complete the private interaction; require the seam's committed-record authorized outcome; separately configure explicit model routes. This is not an executable owner procedure or current readiness claim. Native OAuth remains required; no API-key substitution is proposed.

## Method and limits

The existing Inspection helper was reused unchanged: root-owned/non-writable ancestor trust, held nofollow descriptors, ACL/capability exclusions, stable positive link counts, double-read SHA256 and metadata/path checks. New dependency links followed the verified adapter manifest's declared peer/dependency entries, with root-owned stable symlink checks, canonical installation boundaries and manifest identity/version checks. Remaining files followed exports/bin/files and explicit relative imports. No crawling or rejected dsh-base index read occurred.

All SSH calls used the existing approved key, BatchMode, IdentitiesOnly, StrictHostKeyChecking, ConnectTimeout10 and the isolated Python3.12 interpreter at the assigned VM105 endpoint; wrappers checked SSH exit0. Only inspection Python executed remotely. No installed JavaScript/dsh invocation, login/browser, provider HTTP, profile metadata/content, credentials, environment/logs or VM mutation occurred. The active profile remained opaque. All consumed source files reported stable link count2. Parent independently owns runtime verification and acceptance.

Local retained extraction provenance: `C:/Users/chatc/.codex/tmp-native-oauth-source.json` contains full selected manifests and line-numbered source excerpts selected by Python `re.search('authorization|oauth|OAuth|nativeRecord|openai-codex|onAuth|onPrompt', line)`, with four preceding and seven following lines. `C:/Users/chatc/.codex/tmp-native-oauth-final-source.json` contains the full CLI source and later excerpts; its predicates were `authorization|login` for dsh-base, `recordKeyFor|function createAuth|function relay|function restate|createCredentialStore|credentialStore|function writableStore` for the adapter, `credentials.set|apiKey|apiInput|credential|login` for Models UI, and `credentials:|credentials.set|METHODS|methodHandlers|authorization` for the API proxy, with three preceding and nine following lines. Matching was case-sensitive and the dot in credentials.set was a regex wildcard. Whole source bytes were inspected and hash-checked remotely, but these local captures retain selected excerpts rather than complete UI/API files; standalone whole-file negative-search counts were not retained. Negative conclusions above are therefore explicitly limited to entrypoints not established in this examined path.

## Next action

Independent review: `native_oauth_review` accepted the corrected bounded source findings on2026-09-09 00:54:55 Asia/Bangkok. It recomputed the eight retained full OAuth source hashes and checked declaration/line provenance; runtime, selected storage, native authentication and account access remain NOT PROVEN. The separate CLI/headless follow-up is `vm105-native-oauth-surface-search-2026-09-09.md`.

Retain the OAuth readiness blocker and resolve the interaction-surface prerequisite through bounded independently reviewed routine in-plan work under standing owner preapproval. This technical decision is not an additional permission gate. Do not ask the sleeping owner to authenticate into a surface that is not established. Device-code is the source-supported transport to evaluate first after that surface exists, because it avoids a new callback forward; actual private authentication/consent still requires the owner. No speculative integration or patch was built in this read-only lane.

## Public source ledger

Exactly eight additional files; one-based line references above bind to these public-source hashes.

- `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-authorization@0.1.1-rc.2_e0350187351f9d964689a3e0122aa410/node_modules/@deepseek-ai/dsh-authorization/package.json`
  - SHA256 `32d3147021c95140ba4ded143b4aa9079d04c4c78a10edcd49b573927136a1f7`.
- `/opt/deepseek-harness/node_modules/.pnpm/@earendil-works+pi-ai@0.82.1_@modelcontextprotocol+sdk@1.30.0_zod@4.4.3__ws@8.21.3_zod@4.4.3/node_modules/@earendil-works/pi-ai/package.json`
  - SHA256 `955aa1caab4c875fc7755abe7cacbf9002d9875c471e8d5af245e495ae1d4596`.
- `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-authorization@0.1.1-rc.2_e0350187351f9d964689a3e0122aa410/node_modules/@deepseek-ai/dsh-authorization/lib/index.js`
  - SHA256 `d86547a2f450ff7f58f421f5e2a91eab6abc5ac3dc2ae90cd3785d15547002a3`.
- `/opt/deepseek-harness/node_modules/.pnpm/@earendil-works+pi-ai@0.82.1_@modelcontextprotocol+sdk@1.30.0_zod@4.4.3__ws@8.21.3_zod@4.4.3/node_modules/@earendil-works/pi-ai/dist/oauth.js`
  - SHA256 `bcdee371a91250a4d60f56b272d03959c9f6c401e73c3a1065d0a0dd002eec1a`.
- `/opt/deepseek-harness/node_modules/.pnpm/@earendil-works+pi-ai@0.82.1_@modelcontextprotocol+sdk@1.30.0_zod@4.4.3__ws@8.21.3_zod@4.4.3/node_modules/@earendil-works/pi-ai/dist/providers/openai-codex.js`
  - SHA256 `b458cc964763a2665222f88030aad10c1687905e306cfae957e9771994e24aca`.
- `/opt/deepseek-harness/node_modules/.pnpm/@earendil-works+pi-ai@0.82.1_@modelcontextprotocol+sdk@1.30.0_zod@4.4.3__ws@8.21.3_zod@4.4.3/node_modules/@earendil-works/pi-ai/dist/auth/oauth/load.js`
  - SHA256 `6dcc6e0be9e97722443ff8ac464e11f45b86af2928ee7b21179eb42f6cbf5873`.
- `/opt/deepseek-harness/node_modules/.pnpm/@earendil-works+pi-ai@0.82.1_@modelcontextprotocol+sdk@1.30.0_zod@4.4.3__ws@8.21.3_zod@4.4.3/node_modules/@earendil-works/pi-ai/dist/auth/oauth/openai-codex.js`
  - SHA256 `033266083e72b3b48a3421bdaf19c13d33ad746842516c577d97a698ca3ec5dd`.
- `/opt/deepseek-harness/node_modules/.pnpm/@earendil-works+pi-ai@0.82.1_@modelcontextprotocol+sdk@1.30.0_zod@4.4.3__ws@8.21.3_zod@4.4.3/node_modules/@earendil-works/pi-ai/dist/cli.js`
  - SHA256 `2dc90cb98ed267c808c55476eb68a1fb6090e83ac871c0348a9665a35a831149`.

Existing ledger-named sources consumed:

- `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-web-app@0.1.1-rc.2_ce3874dffedb66ab726b823cc1dadab8/node_modules/@deepseek-ai/dsh-web-app/package.json` — SHA256 `f1ab1f51022e56adae15889764001aed390da0d647db08313d07b571265a27f1`.
- `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-web-app@0.1.1-rc.2_ce3874dffedb66ab726b823cc1dadab8/node_modules/@deepseek-ai/dsh-web-app/cordis.patch.yml` — SHA256 `7889b655be3809dd21e3c59023f8510e6e8425f6f37616e4ba20389f2e938dda`.
- `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-llm-pi-ai@0.1.1-rc.2_236ec8963c16cce3286da2b293de8170/node_modules/@deepseek-ai/dsh-llm-pi-ai/package.json` — SHA256 `b50f77d01dbdffbee612f9969903952c131956e5b28d806c7c82a7f715753f89`.
- `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-llm-pi-ai@0.1.1-rc.2_236ec8963c16cce3286da2b293de8170/node_modules/@deepseek-ai/dsh-llm-pi-ai/lib/index.js` — SHA256 `e183a9cdde703b47485410bd68d247c8becdb277c390f0f91c6dd28718d350e2`.
- `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-host-apiproxy@0.1.1-rc.2_7a1c54e2b954eca6f88bad802758761b/node_modules/@deepseek-ai/dsh-host-apiproxy/package.json` — SHA256 `156d33df741f8cad7ccce2ade30eb6ca241001a5cb68510423dcd99804b6275d`.
- `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-host-apiproxy@0.1.1-rc.2_7a1c54e2b954eca6f88bad802758761b/node_modules/@deepseek-ai/dsh-host-apiproxy/lib/index.js` — SHA256 `8e32ffc951f499849c155e30cb30813af5ed7abb11008653125092299b693d9f`.
- `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-client-ui-settings-models@0.1.1-rc.2_6ea45dce772d8d764ff9d4e073210778/node_modules/@deepseek-ai/dsh-client-ui-settings-models/package.json` — SHA256 `050fcc1cadb0e6bcb8bada85039a636864ebfea16228212d1ffd07def3fe8818`.
- `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-client-ui-settings-models@0.1.1-rc.2_6ea45dce772d8d764ff9d4e073210778/node_modules/@deepseek-ai/dsh-client-ui-settings-models/lib/client.js` — SHA256 `c3b9a2d2d074c600c10553a4b15e294082f5851dd4a834d06ddb268b310d18de`.
- `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-base@0.1.1-rc.2_b6700999316794178df1eb7155dc0a46/node_modules/@deepseek-ai/dsh-base/package.json` — SHA256 `35d203246e9c2a8e623da058cd9b1527252b6c4b4bf2acc56f5233a70db676df`.
- `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-base@0.1.1-rc.2_b6700999316794178df1eb7155dc0a46/node_modules/@deepseek-ai/dsh-base/cordis.patch.yml` — SHA256 `9870a518274194c0e1ebd870cee2737fbc2ffc04ae36887871ffe6fcf74beac1`.
