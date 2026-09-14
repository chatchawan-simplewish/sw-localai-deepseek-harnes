# VM105 Phase 13 R2 reconstruction successor contract — 2026-09-15

## Status and authority

**DELIVERY ONLY.** `scripts/Invoke-VM105ReconstructionSuccessor.py` authorizes exactly one bundle-delivery attempt for fresh generation `phase13-r2-20260915`. The accepted delivery binding is:

`442a32392f04b8ee24a44b033db655f8136319e90682f75b0d6ef554566d0935`

The successor is copy-derived from the immutable, independently reviewed Phase 12 source whose raw SHA-256 is `756354721f19d156ab336b79755c476a74ee8075cca3a1e11e91f1a418b2b29f`. The Phase 13 R2 source raw SHA-256 is `b30366f98a22e1a77fbd24451248111adb884280e625d0ac0844d62fb881c960`; the focused regression raw SHA-256 is `3b502b1fd7872feea6f0d850f8b5aea2bacb1468313d7a8669a24205b93caa9d`.

The delivery binding includes the generation, the fixed bundle and temporary roots, all five basename/SHA-256 pins, and all six fresh repository-relative evidence paths. Its canonical JSON SHA-256 is recomputed at import and must equal the accepted value before any source read, evidence reservation, or transport call.

## Fixed delivery operation

- Final bundle root: `/var/tmp/omniroute-dsh-reconstruction-input-20260914`
- Temporary root: `/var/tmp/.omniroute-dsh-reconstruction-input-20260914.tmp`
- Preserved later staging root: `/var/tmp/omniroute-dsh-client-final-20260913`
- Remote command: the exact ASCII result of `_delivery_remote_command()`, 4,828 bytes, SHA-256 `a569cada782d46bfe6aa037045e5acccf2fb307c2d51af773a011e1430974cbe`
- Privileged target: `/usr/bin/env -i PATH=/usr/bin:/bin /usr/bin/sudo -n /usr/bin/python3.12 -I -c <fixed-base64-bootstrap>`
- SSH prefix: the preserved strict Phase 12 `ssh.exe` argv with `BatchMode`, `IdentitiesOnly`, password and keyboard-interactive authentication disabled, strict host-key checking, cleared forwards, bounded connection settings, and target `dsh@192.168.1.139`

The five fixed source pins remain. Exact `-text` rules in `.gitattributes` prevent Git checkout or archive line-ending conversion for each path. `Build-VM105FinalClientManifest.py` is committed as its accepted raw bytes; its LF-normalized semantic content is identical to the prior Git blob. The other four prospective blobs remain byte-identical to their current Git blobs.

| Basename | SHA-256 |
|---|---|
| `Build-VM105FinalClientManifest.py` | `371481fe62d6611913f82f65b6e26b12512fda8a853a2f4591b6314f580c885f` |
| `Capture-VM105DshTopology.py` | `aa2ca52f0460279d4fd76314be96610bfd87b1bf3e6b2c92e5446983468b6190` |
| `Invoke-VM105ProductionLauncher.py` | `f2011f4d81831e4fb102f2f9e9755690418387e2f697e5ca3044417de5767c6d` |
| `vm105-dsh-topology-capture-successor-20260913.json` | `86882398a06921bd351c84dbfc1eecc9abeb963912df41499ee21462b50cb47f` |
| `vm105-final-client-runtime-manifest-20260913.json` | `54d117c638335edeefe43aaef0f181ea5317f7938a6861a145871a0d9e45e8dd` |

Before transport, every fresh evidence leaf must be absent. The attempt leaf is then reserved with exclusive creation. The remote bootstrap preserves the Phase 12 fail-closed frame validation, root-owned `0440` files, root-owned `0550` directory, descriptor-based verification, fsync, and `renameat2(RENAME_NOREPLACE)` publication. Transport remains bounded. Any ambiguity after the reservation is terminal and does not authorize cleanup or retry.

Fresh evidence leaves:

- `docs/evidence/vm105-dsh-reconstruction-bundle-delivery-phase13-r2-attempt-20260915.json`
- `docs/evidence/vm105-dsh-reconstruction-bundle-delivery-phase13-r2-20260915.json`
- `docs/evidence/vm105-dsh-reconstruction-bundle-phase13-r2-20260915.json`
- `docs/evidence/vm105-dsh-reconstruction-sudo-policy-phase13-r2-20260915.json`
- `docs/evidence/vm105-dsh-reconstruction-phase13-r2-attempt-20260915.json`
- `docs/evidence/vm105-dsh-reconstruction-phase13-r2-20260915.json`

## Explicitly unavailable

`ACCEPTED_PREREQUISITE_CAPTURE_BINDING_SHA256`, `ACCEPTED_RECONSTRUCTION_DISPATCH_BINDING_SHA256`, all four receipt pins, `ACCEPTED_SUDO_VERSION`, and `ACCEPTED_LIVE_BINDINGS` remain `None`. This revision does not authorize prerequisite capture, sudo-policy mutation, reconstruction, cleanup or retry, ordinary client proof, or any OmniRoute, Hermes, or gateway action.

The regression verifies that delivery is the only bound mode and that all six fresh leaves are checked absent before transport. No live command is part of source verification.
