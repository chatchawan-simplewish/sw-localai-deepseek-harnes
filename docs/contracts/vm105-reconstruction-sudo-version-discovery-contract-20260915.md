# VM105 reconstruction sudo-version discovery contract — 2026-09-15

## Scope and authority

This contract grants one read-only discovery of VM105's sudo version and effective policy for the already-reviewed reconstruction command. The package is source-only and has not run SSH or sudo while being prepared.

The sole authority is `ACCEPTED_DISCOVERY_BINDING_SHA256 = 9aabf6718dea7dc914d4cfac70f3651bd626055f8af0247c582d2d09f9dae427`. The caller, accepted constant, and freshly computed binding must all match. Both evidence leaves must be absent before either SSH query. An occupied or uncertain leaf blocks before transport, and every published record has `retryAuthorized=false`.

## Immutable inputs

| Input | Pin |
|---|---|
| Reviewed source | `scripts/Invoke-VM105ReconstructionSuccessor.py` |
| Reviewed source raw SHA-256 | `b30366f98a22e1a77fbd24451248111adb884280e625d0ac0844d62fb881c960` |
| Generation | `phase13-sudo-discovery-20260915` |
| Target argv count | `5` |
| Canonical target argv SHA-256 | `ed1b946ae10ea6399822335a39514134b06360b828ced7309126a6ed6fba4f4f` |
| Reconstruction bootstrap bytes | `2072` |
| Reconstruction bootstrap SHA-256 | `cb0281b3a3816d355a6e114f11f55776ed1f3ca6a95be3e4874d4b4b613dd171` |
| Full-query bootstrap bytes | `629` |
| Full-query bootstrap SHA-256 | `e59ed14279ea52175416b7006e18419823375a1281e7fb8d6ab97bd1620d307f` |

The binding contains the complete argv arrays for both SSH calls. Their canonical-array hashes are:

| Query | Canonical argv SHA-256 |
|---|---|
| Exact `sudo -n -l -- <reconstruction argv>` | `741ccce580096340f49ebc5b277f05f2824e1fd7afad09cede1603559845b4b7` |
| Canonical `sudo -V` plus `sudo -n -ll` bootstrap | `8c70410d721e0e8d89850475c01f52e3702a6eefdebc6c1738cefea0708adc2a` |

The reviewed source must still expose the strict SSH prefix and bounded `_run_ssh`. Its prerequisite-capture, reconstruction-dispatch, four receipt, sudo-version, and live-binding gates must all remain `None`. Any drift blocks discovery. The earlier bundle-delivery authority is neither read nor called.

## One-shot sequence

1. Stable-load and hash the reviewed source without following a symlink, then derive the reviewed reconstruction command details.
2. Verify the exact authority and absence of both evidence leaves.
3. Exclusively publish the canonical, self-hashed attempt leaf.
4. Run exactly the reviewed exact-command policy query, then exactly the reviewed full sudo query. Both send empty stdin. The reconstruction dispatch command is never called.
5. Publish one canonical, self-hashed terminal leaf. Valid framed output is a successful discovery even when `policyState` is `BROAD` or `UNSUPPORTED`.

Evidence paths:

- `docs/evidence/vm105-dsh-reconstruction-sudo-discovery-phase13-attempt-20260915.json`
- `docs/evidence/vm105-dsh-reconstruction-sudo-discovery-phase13-20260915.json`

## Terminal evidence

A valid discovery records only bounded scalar metadata: status/reason, generation and binding, immutable source and target pins, sudo version, exact-command allowed boolean, `policyState` (`EXACT`, `BROAD`, or `UNSUPPORTED`), return codes, SHA-256 values for both query outputs, and the fixed false values for target execution, raw-output storage, and retry authority.

Transport errors, nonempty stderr, unexpected return codes, or invalid full-query framing produce sanitized `UNKNOWN` evidence. Raw policy, exact-query output, and stderr are never printed or stored.

## Explicit exclusions

This authority does not grant bundle delivery, sudoers mutation, prerequisite receipt capture, reconstruction, cleanup, retry, ordinary-client proof, or any OmniRoute, Hermes, or gateway action.
