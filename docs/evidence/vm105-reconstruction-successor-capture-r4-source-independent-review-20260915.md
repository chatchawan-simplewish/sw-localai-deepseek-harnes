# VM105 reconstruction successor capture R4 — independent source review

## Verdict

**PASS.** No Critical, High, Medium, or Low findings were identified in exact commit `ee4a8a48058afd7834c173eabc9c852948afd13b`.

## Immutable scope

| Path | Git-blob raw SHA-256 |
|---|---|
| `.gitattributes` | `4947c3814136b0f1fee0dc4d39c95ab85afdc2469283b7b58b31dc001ac14dbc` |
| `scripts/Invoke-VM105ReconstructionSuccessor.py` | `35084d5e879d5ef0c207d0c17d546a5d3be1645129ea361961d66516856e6517` |
| `scripts/test_vm105_reconstruction_successor.py` | `d007fd363d9094d1ac3495d037779745c80c65ef1ef478a4dc114a8d617af504` |
| `docs/contracts/vm105-reconstruction-successor-contract-20260915.md` | `1a20cd245dbeeaa0aedf22ec868872e3d76fd3269a30268a47fb3b48eece223e` |

The commit changes exactly these four paths.

## Verification

- The two exact `-text` rules preserve the unchanged R2 delivery and sudo-discovery provenance records byte-for-byte.
- A Git archive retains provenance SHA-256 values `d3739ef37d16c76f3aa29eefc461b6660e091620b37d3dbc6e9b68179f9e831c` and `d88e629c18ef86249e27bfc02d944b35a0ae128faea43f0f74437dd5bf9c8f24` with LF endings.
- A clean checkout of the exact commit with `core.autocrlf=true` retains those same hashes and passes the focused suite: 3 of 3 tests.
- Stable raw-hash, canonical-JSON, self-hash, and required-field validation of both committed provenance records passes before transport.
- Generation and all six fresh evidence leaves are exactly `phase13-r4-20260915`; every leaf is absent in the reviewed commit.
- The computed and accepted capture binding both equal `d9d14c8ebebb4b91dd775b32ad45ec2297273706ee85454c44d74ec6e5537e4d`.
- Delivery, dispatch, all four receipt pins, and live bindings remain `None`. The accepted sudo version is exactly `1.9.15p5`.
- The sudo parser retains exact-one-entry, safe-default, root, `!authenticate`, exact-command, source-line-column, broad-`ALL`, stderr, version, and unsupported-grammar controls. Capture receipts remain canonical and exclude raw policy output and stderr.
- Strict SSH options and bounded transport are unchanged from the reviewed predecessor source.

## Limits

This is source and reproducibility evidence only. No SSH, sudo, bundle delivery, capture, dispatch, reconstruction, cleanup, retry, ordinary-client, OmniRoute, Hermes, or gateway action ran during review.
