# VM105 Phase 13 R4 reconstruction successor contract — 2026-09-15

## Status and authority

**CAPTURE ONLY.** `scripts/Invoke-VM105ReconstructionSuccessor.py` authorizes one prerequisite capture for generation `phase13-r4-20260915`. The accepted capture binding is:

`d9d14c8ebebb4b91dd775b32ad45ec2297273706ee85454c44d74ec6e5537e4d`

The source raw SHA-256 is `35084d5e879d5ef0c207d0c17d546a5d3be1645129ea361961d66516856e6517`; the focused regression raw SHA-256 is `d007fd363d9094d1ac3495d037779745c80c65ef1ef478a4dc114a8d617af504`.

`ACCEPTED_BUNDLE_DELIVERY_BINDING_SHA256` is closed. The dispatch binding, all four receipt pins, and `ACCEPTED_LIVE_BINDINGS` remain `None`. `ACCEPTED_SUDO_VERSION` is exactly `1.9.15p5`.

## Fixed provenance

The capture binding includes the six fresh evidence paths and both immutable provenance records below. Each record is read through stable descriptor validation and then checked for canonical JSON, raw SHA-256, self SHA-256, and the stated terminal fields before either capture transport can run.

| Provenance | Raw SHA-256 | Self SHA-256 | Required terminal fields |
|---|---|---|---|
| `docs/evidence/vm105-dsh-reconstruction-bundle-delivery-phase13-r2-20260915.json` | `d3739ef37d16c76f3aa29eefc461b6660e091620b37d3dbc6e9b68179f9e831c` | `d1990c9414ca647c36639fd703d0aef200ff7dd11d7678e779bcc6531fa68340` | `status=PASS`, `reason=NONE`, `remoteState=PROVEN_PASS`, `retryAuthorized=false` |
| `docs/evidence/vm105-dsh-reconstruction-sudo-discovery-phase13-20260915.json` | `d88e629c18ef86249e27bfc02d944b35a0ae128faea43f0f74437dd5bf9c8f24` | `64e1028797590c4349c5ce1b03f35bcf106e4699ee7f355bdd3f888bf52986fd` | `status=PASS`, `reason=NONE`, `sudoVersion=1.9.15p5`, `exactCommandAllowed=true`, `policyState=UNSUPPORTED`, `targetExecuted=false`, `rawOutputStored=false`, `retryAuthorized=false` |

Exact `-text` rules in `.gitattributes` preserve both provenance files byte-for-byte in Windows checkouts, temporary-index materialization, and Git archives. The provenance content and Git blobs are unchanged.

## Fixed capture

- Bundle root: `/var/tmp/omniroute-dsh-reconstruction-input-20260914`
- Expected files: the same five fixed basename/SHA-256 pairs from the proven R2 delivery
- Bundle capture command: the exact ASCII result of `_capture_remote_command()`, 4,615 bytes, SHA-256 `be90e4246133923788b844698b42f38df831c44bee4d6ecfb7370313cdb61633`
- Full sudo query command: the exact final argv element from `_sudo_full_query_command()`, 943 bytes, SHA-256 `2b2ace5f77034b1a13bf9447eb014b61d07b391c962bd4857e0ca84dad941766`
- SSH prefix: the preserved strict `ssh.exe` argv for `dsh@192.168.1.139`

The bundle receipt requires a stable root-owned `0550` directory containing exactly the five root-owned `0440` regular files at their fixed hashes. The sudo capture performs the exact non-executing `sudo -n -l -- <argv>` query and the bounded `sudo -V` plus `sudo -n -ll` query. The parser accepts the established source forms plus sudo 1.9.15's `Sudoers entry: /etc/sudoers...:line:column` form. It still requires exactly one entry, safe defaults, `RunAsUsers: root`, `Options: !authenticate`, and the exact reconstruction command. `ALL`, wildcard, shell, Python, extra-entry, unsafe-default, version, stderr, transport, or grammar ambiguity remains blocked or unsupported.

Only canonical bundle and sudo receipts are exclusively published, each at most once. Raw policy output and stderr are hashed or discarded and are never stored.

Fresh evidence leaves:

- `docs/evidence/vm105-dsh-reconstruction-bundle-delivery-phase13-r4-attempt-20260915.json`
- `docs/evidence/vm105-dsh-reconstruction-bundle-delivery-phase13-r4-20260915.json`
- `docs/evidence/vm105-dsh-reconstruction-bundle-phase13-r4-20260915.json`
- `docs/evidence/vm105-dsh-reconstruction-sudo-policy-phase13-r4-20260915.json`
- `docs/evidence/vm105-dsh-reconstruction-phase13-r4-attempt-20260915.json`
- `docs/evidence/vm105-dsh-reconstruction-phase13-r4-20260915.json`

## Explicitly unavailable

This revision does not authorize delivery, dispatch, sudoers mutation, reconstruction, cleanup or retry, ordinary client proof, or any OmniRoute, Hermes, or gateway action. Source verification performs no SSH, sudo, or live command.
