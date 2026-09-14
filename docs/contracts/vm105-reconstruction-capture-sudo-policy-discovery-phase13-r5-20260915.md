# VM105 Phase 13 R5 capture sudo-policy discovery contract — 2026-09-15

## Status and authority

**DISCOVERY ONLY.** `scripts/Capture-VM105ReconstructionCaptureSudoPolicy.py` is a source-only, one-shot package for generation `phase13-r5-20260915`. Preparation and tests perform no SSH, sudo, capture, construction, reconstruction, or dispatch. The sole accepted discovery binding is:

`0998b798aa925b2fcb1182f46655187ec7b6410851e6d90e8d10967fcc425540`

The caller, accepted constant, and freshly computed binding must match. Both fresh evidence leaves must be absent. An occupied or uncertain leaf blocks before transport. Every attempt and terminal record fixes `targetExecuted=false`, `rawOutputStored=false`, and `retryAuthorized=false`.

## Immutable inputs and provenance

| Input | Raw SHA-256 | Self SHA-256 / meaning |
|---|---|---|
| Current reviewed successor `scripts/Invoke-VM105ReconstructionSuccessor.py` | `35084d5e879d5ef0c207d0c17d546a5d3be1645129ea361961d66516856e6517` | Phase 13 R4 source |
| R2 delivery `docs/evidence/vm105-dsh-reconstruction-bundle-delivery-phase13-r2-20260915.json` | `d3739ef37d16c76f3aa29eefc461b6660e091620b37d3dbc6e9b68179f9e831c` | `d1990c9414ca647c36639fd703d0aef200ff7dd11d7678e779bcc6531fa68340`; `PASS`, `PROVEN_PASS`, retry false |
| Spent R4 capture `docs/evidence/vm105-dsh-reconstruction-bundle-phase13-r4-20260915.json` | `a588740fcdb447b0ab1cf425ca53062a0577c7d8f439dd6467964efa082f2745` | `e2239a359200d814e23de1c19214f5c28eda2c591ac1b528c2779af5d6c14b96`; `UNKNOWN`, `BUNDLE_CAPTURE_TRANSPORT_UNKNOWN`; R5 grants no retry |

All three inputs are stable-loaded without following symlinks. Both evidence records must remain canonical, self-hashed, raw-hash exact, and semantically exact before transport. The current successor must retain only the already-spent R4 capture gate; delivery, reconstruction dispatch, all receipt pins, and live bindings remain closed.

## Bound targets and commands

The corrected capture policy target is exactly `/usr/bin/python3.12`, `-I`, `-c`, and the base64 expression synthesized from the unchanged `BUNDLE_CAPTURE_REMOTE_BOOTSTRAP`. `/usr/bin/sudo` is the outer policy-query command and is not part of that target argv. The existing reconstruction target is derived unchanged from the reviewed successor.

| Binding | Capture | Reconstruction |
|---|---:|---:|
| Target argc | `4` | `5` |
| Canonical target argv SHA-256 | `43f1c72370553c1fb422428be1d3ad87e8129d4f405947315eaa380dd79276b5` | `ed1b946ae10ea6399822335a39514134b06360b828ced7309126a6ed6fba4f4f` |
| Bootstrap bytes | `3384` | `2072` |
| Bootstrap SHA-256 | `caa49700e0294164fdaa942a860da92a11a5068d120174ab9ad49e6d7d5d534a` | `cb0281b3a3816d355a6e114f11f55776ed1f3ca6a95be3e4874d4b4b613dd171` |
| Canonical exact-query argv SHA-256 | `191780afb4b4cdad22cb2d6981b6a09772cacf0bba9001295262c94ac9f48663` | `741ccce580096340f49ebc5b277f05f2824e1fd7afad09cede1603559845b4b7` |

The binding contains the complete argv arrays for the capture exact query, reconstruction exact query, and full query. Their final remote-command bytes/SHA-256 are respectively `4603`/`7d5357b5a1a44650d8c909f9b7420fac874c74b7b91ba127ddc26a70077caff2`, `2920`/`39bf82f2977d72d7a53a2c2e473087bebd3b0deee3ae67a481c7812545637c57`, and `943`/`2b2ace5f77034b1a13bf9447eb014b61d07b391c962bd4857e0ca84dad941766`. The full-query canonical argv SHA-256 is `8c70410d721e0e8d89850475c01f52e3702a6eefdebc6c1738cefea0708adc2a`.

## One-shot evidence

The only transport sequence is:

1. exact `/usr/bin/sudo -n -l -- <capture target argv>`;
2. exact `/usr/bin/sudo -n -l -- <reconstruction target argv>`;
3. the reviewed bounded bootstrap that invokes `/usr/bin/sudo -V` and `/usr/bin/sudo -n -ll`.

All three calls use the reviewed strict SSH prefix and empty stdin. Neither target command, bundle capture, construction path, nor reconstruction dispatch is called.

Fresh exclusive leaves:

- `docs/evidence/vm105-dsh-reconstruction-capture-sudo-policy-discovery-phase13-r5-attempt-20260915.json`
- `docs/evidence/vm105-dsh-reconstruction-capture-sudo-policy-discovery-phase13-r5-20260915.json`

The terminal evidence records exact-query allowance booleans and `captureCommandState`, `reconstructionCommandState`, and `fullPolicyState`, each restricted to `EXACT`, `BROAD`, or `UNSUPPORTED`. Policy parsing accepts only sudo `1.9.15p5`, safe Defaults, root run-as, `!authenticate`, inline `Sudoers entry: /etc/sudoers` or `Sudoers entry: /etc/sudoers.d/<safe-name>` source rows, and tab-prefixed command rows. The three-query design cannot obtain userspec line or column coordinates, so it retains only unique safe absolute source paths. Those paths are sufficient input for a separately reviewed exact policy mutation. It retains no policy line, stdout, stderr, secret, or executable payload.

Malformed or extra framing, version drift, an unexpected source, stderr, output overflow, unexpected return code, transport uncertainty, or parser ambiguity produces one sanitized canonical `UNKNOWN` terminal. `BROAD` and `UNSUPPORTED` are successful discovery classifications and grant no mutation or retry.

## Source verification

| File | Raw SHA-256 |
|---|---|
| `scripts/Capture-VM105ReconstructionCaptureSudoPolicy.py` | `06482b2ab89b463edafca044c1bca905385b52bb54ca74e9fb7a92f3ccfbf876` |
| `scripts/tests/test_vm105_reconstruction_capture_sudo_policy.py` | `f340013eff0482b5b9ef4162c199c2a52ee6c8f00763ddee587c3f22dc340b06` |

The focused suite has seven source-only tests covering the R4 permission mismatch, exact target synthesis, three-query exclusivity, no target or dispatch execution, canonical self-hashed leaves, raw-output exclusion, `EXACT` and `BROAD` policy classification, real sudo `1.9.15p5` inline-source and tab-command grammar, matching Defaults/User hosts, rejection of separate source coordinates and unsafe paths, provenance binding, and spent-leaf blocking.

Exact `text eol=lf` attributes cover the source, test, and contract paths so their reviewed bytes survive a fresh checkout.

## Explicit exclusions

This contract grants no sudoers mutation, bundle delivery, bundle capture, construction, reconstruction, dispatch, cleanup, retry, ordinary-client proof, credential access, OmniRoute, Hermes, gateway, provider, or production action.
