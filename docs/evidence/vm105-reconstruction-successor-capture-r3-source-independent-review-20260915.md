# VM105 reconstruction successor capture R3 — independent source review

## Verdict

**BLOCK.** Exact commit `630763a4ece83bac864bbec54be7a6400c14ce4b` preserves the intended fail-closed authority boundaries, but its prerequisite provenance pins are not stable across a normal Windows checkout.

## Immutable scope

| Path | Git-blob raw SHA-256 |
|---|---|
| `scripts/Invoke-VM105ReconstructionSuccessor.py` | `6c460e8e82d5766df9290d408618f1e26f4dd94a38bb3247407a8740fe5caefb` |
| `scripts/test_vm105_reconstruction_successor.py` | `b420716cdcde50ebe4a7ebd31555dc326229bc9d6b63010c3c8c830c461959e2` |
| `docs/contracts/vm105-reconstruction-successor-contract-20260915.md` | `eb510621168eb054564ba110b060f56ac2a76fc82207d1661da88bd559e73ae1` |

The accepted capture binding equals `ab2fc31d8280ab15437253ca65843b3728d17949eae6b64c34f833383a1a2bf1`. Delivery, dispatch, all four receipt pins, and live bindings remain `None`; the accepted sudo version is `1.9.15p5`.

## Finding

### IMPORTANT — provenance raw hashes depend on unpinned checkout line endings

`scripts/Invoke-VM105ReconstructionSuccessor.py:77` and `:83` pin the LF Git-blob hashes of the R2 delivery and sudo-discovery evidence. `_validate_capture_provenance` then requires those exact filesystem bytes at `:303-319`. The two evidence paths have no `text` or `eol` attribute, while this repository is configured with `core.autocrlf=true`.

A clean local checkout of the exact reviewed commit with that configured Windows policy converts each one-line JSON record to CRLF:

| Provenance path | Required LF SHA-256 | Clean-checkout CRLF SHA-256 |
|---|---|---|
| `docs/evidence/vm105-dsh-reconstruction-bundle-delivery-phase13-r2-20260915.json` | `d3739ef37d16c76f3aa29eefc461b6660e091620b37d3dbc6e9b68179f9e831c` | `289e620db5757ee2e8c878fa4b0ec66a9a4e9e4fad842e384480886741179b36` |
| `docs/evidence/vm105-dsh-reconstruction-sudo-discovery-phase13-20260915.json` | `d88e629c18ef86249e27bfc02d944b35a0ae128faea43f0f74437dd5bf9c8f24` | `04be9d422611f4c2e5a7bb27aa4ba4399f21169cccb9b7c12643a339560ac37b` |

The clean checkout consequently fails 2 of 3 focused tests with `CAPTURE_PROVENANCE_REJECTED` before either transport. The current authoritative worktree passes 3 of 3 only because both tracked evidence files currently remain LF. This contradicts the contract's stable committed-provenance claim at `docs/contracts/vm105-reconstruction-successor-contract-20260915.md:15-20` and makes the published capture source non-reproducible after a fresh Windows checkout.

Required remediation: preserve the exact bytes of both hashed provenance records with explicit `-text` attributes, consistent with the repository's existing immutable hashed-evidence paths, then re-freeze and independently review the resulting commit.

## Confirmed controls

- Both committed provenance records pass raw hash, canonical JSON, self hash, and required-field validation while their LF bytes are preserved, and validation precedes transport.
- The six R3 evidence leaves are fresh and absent.
- The sudo parser accepts `Sudoers entry: source:line:column`, returns `BROAD` for multiple entries or `ALL`, and retains exact-command, root, `!authenticate`, safe-default, version, stderr, and unsupported-grammar blocking.
- Capture publishes only canonical bundle and sudo receipts; raw sudo policy output and stderr are not stored.
- SSH options remain strict and transport output/time are bounded.
- No SSH, sudo, delivery, dispatch, reconstruction, cleanup, retry, OmniRoute, Hermes, or gateway action was run during review.
