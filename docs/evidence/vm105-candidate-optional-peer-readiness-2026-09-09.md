# VM105 candidate optional-peer diagnosis — 2026-09-09

Repository: https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git. Source-only diagnosis; no candidate startup or guard change. Fresh SDK manifest read: `2026-09-08T18:27:58.243500+00:00` (2026-09-09 01:27:58 Asia/Bangkok), SSH wrapper exit0.

**Result: `@cfworker/json-schema` is explicitly optional in the exact declaring SDK manifest. This does not establish that app-boot skips it, that global resolution is harmless, or that the candidate is safe to start. The existing installed-only guard remains BLOCKED.**

- New public-file budget: 01/02 consumed. Existing complete app-boot capture reused and independently rehashed locally.
- Parent census receipt `vm105-candidate-unresolved-peer-2026-09-09.json`, execution `8870e9`, remains `DIAGNOSTIC_BLOCKED / INSTALLED_ONLY_RESOLUTION`: 246 packages, 1138 edges, descriptor restoration PASS, helper exit1. Those counts are from the parent receipt, not a new census in this lane.

## Optional declaration: proven

SDK manifest lines122–132 declares peer `@cfworker/json-schema: ^4.1.1` and `peerDependenciesMeta["@cfworker/json-schema"].optional: true`. The same block marks zod optional:false. The SDK name is `@modelcontextprotocol/sdk`, version1.30.0. Its SHA256 matches the census's exact declaring-manifest digest:

`0690cbe02511a95d1ff199acf20b5a12ac4dfde1bbe30c82a0de73afa92dffc9`.

This proves the package's declaration, not which SDK runtime paths use that peer or whether those paths are reached during the proposed smoke. No SDK implementation was executed or inspected.

## App-boot behavior: optionality is not its skip condition

The pinned complete app-boot source establishes:

- Lines409–437 build the selected-home fallback map. Line422 traverses dependencies followed by peerDependencies, without consulting peerDependenciesMeta. A previously resolved package name wins (423). Only an undefined lookup result is skipped (424–425); a successful lookup is linked and its manifest queued (426–431).
- Lines499–505 call `createRequire(anchor).resolve.paths(packageName)`, iterate its entire returned list, and return the first candidate whose `package.json` passes `existsSync`. This function contains no installation-root restriction or optional-peer filter. It does not inspect package exports or load package JavaScript to choose the directory.
- If every returned candidate is absent, the function falls through to undefined and the fallback traversal continues. That is a conditional source result; the installed-only census did not establish absence in all resolver paths.
- If a later path contains that manifest, app-boot can select it even for an optional peer. The source does not bound that list to `/opt/deepseek-harness`. Actual Node global/NODE_PATH lookup roots, their contents, permissions and effective launch behavior were not inspected in this lane. Therefore the current verifier's refusal at its installation boundary cannot be reclassified as a proven runtime skip.
- Lines370–387 and433–436 can create or replace fallback links. A safe expected-map proof must match the source's selection behavior; optional metadata does not authorize ignoring a possible selected target.

## Remaining proof before existing-path smoke

The required result is still an exact trusted expected fallback map under the candidate's actual launch contract, with every resolver outcome adjudicated. For this edge, that means proving either no candidate exists anywhere the actual resolver would search, or the exact selected candidate and its trust/identity. The optional flag alone establishes neither. The current no-global-inspection scope and installed-only checker cannot furnish that proof.

Any next step must be a separately bounded, independently reviewed source/resolution contract that addresses this limitation and preserves exact-map comparison, trust checks and fail-closed behavior. This document does not authorize a Node/runtime probe, additional directories, package installation, filtering optional peers, or changing the guard. It also does not infer a supported launch option that suppresses global lookup. Candidate startup remains unattempted by this lane; all other smoke prerequisites and cleanup requirements remain in force.

## Scope and retained evidence

Independent review: `candidate_smoke_implement` accepted source interpretation for document SHA256 `BF8FCF02B7041BAE9DF2E809284B1701194BD7EE8674AE8C0C640E51F24D410C` before this annotation, at2026-09-09 01:30:53 Asia/Bangkok. It recomputed both source hashes and verified optionality, full-path lookup behavior and bounded locator counts. The capture JSON does not independently retain SSH exit status; exit0 remains the author's wrapper-result claim. Safe runtime skipping remains NOT PROVEN.

The initial proposed pi-ai dependency chain was not used: its retained manifest did not declare the SDK, and a pnpm directory suffix is not a dependency declaration. Parent instead authorized one shallow exact-prefix locator in the trusted `.pnpm` directory, bounded at4096 entries and4 matches, with ambiguity stopping before source consumption. It returned449 entries and exactly1 SDK-name match; no recursive crawl or global/profile directory was inspected. This locates matching manifest content, not the runtime dependency-resolution mapping.

- Full new source capture: `C:/Users/chatc/.codex/tmp-candidate-optional-sdk.json`.
- Source: `/opt/deepseek-harness/node_modules/.pnpm/@modelcontextprotocol+sdk@1.30.0_zod@4.4.3/node_modules/@modelcontextprotocol/sdk/package.json`.
- Manifest hash above, link count2. Root ownership/non-writable ancestry, nofollow held descriptors, ACL/capability exclusions, stable metadata/path identity, and double-read hashes used the unchanged `Inspection` definitions from helper SHA256 `fcddc77c890b289e28c609fa30b3b41f6c060a73c5c4ea3ab69b468a130df424`. The locator directory remained held and revalidated.
- Strict SSH used the existing approved VM105 key, BatchMode, IdentitiesOnly, StrictHostKeyChecking, ConnectTimeout10 and `/usr/bin/python3.12 -I -`; local wrapper required exit0 and retained full public source only.
- Reused capture: `C:/Users/chatc/.codex/tmp-native-surface-headless.json`; app-boot `lib/index.js` SHA256 `9d4b7f214cd35b3e8ce4e027b12cca34a416d355577aeacbf08a5b324f0cabb6`. Capture source-receipt UTC was `2026-09-08T17:48:38.589834+00:00`; no fresh remote app-boot read occurred here.
- App-boot canonical source: `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-app-boot@0.1.1-rc.2_d7ed335ddbfb7670edc51bd2c8928580/node_modules/@deepseek-ai/dsh-app-boot/lib/index.js`.

Both retained source strings were independently SHA256-reconstructed locally. No missing-package install, dependency skip, global-directory inspection, profile/credential/environment content read, runtime JavaScript, provider request, inference, service/port change or startup occurred. Only this repository document was created; other owners' files and the current guard were preserved.
