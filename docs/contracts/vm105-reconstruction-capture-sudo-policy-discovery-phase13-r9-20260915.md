# VM105 Phase 13 R9 semantic sudo-policy projection contract — 2026-09-15

R9 is one fresh, read-only successor to spent R4–R8 evidence. It makes two exact `sudo -n -l -- <argv>` queries and a bounded remote semantic projection of `sudo -V` plus `sudo -n -ll`. It cannot execute a target, capture a bundle, mutate sudoers, reconstruct, dispatch, retry any spent gate, or touch OmniRoute, Hermes, or a gateway.

R8 proves both exact queries and the full listing returned `0`, but the raw listing falls outside the local grammar. R9 parses that listing only on VM105 and emits canonical `{sudoVersion, entryCount, hasBroadAll, policySources}`. `hasBroadAll=true` safely classifies `BROAD`; any non-broad semantic result remains `UNSUPPORTED` and never passes as exact. Raw policy, stdout, stderr, credentials, and payload are never returned or stored.

| Path | SHA-256 |
|---|---|
| `scripts/Invoke-VM105ReconstructionSuccessor.py` | `d929842db8f1ddc978d321761a36f07a875e07d3edc63b5301ac87a92f69abb4` |
| `scripts/Capture-VM105ReconstructionCaptureSudoPolicy.py` | `62f92a608e3a836e68466f485bb585fb54fe0d09f8c2d2d8174b7dc5bf42248d` |
| `scripts/tests/test_vm105_reconstruction_capture_sudo_policy.py` | `995c92fdae6b8fe45dd4ca37cd71264607ec8a401a0560765c605b95eb776a6f` |

The accepted binding is `18c42af77fb8a42e309361e46e85ae2028b8d23b1983473374cccb7dff14a87c`. Fresh exclusive leaves are `docs/evidence/vm105-dsh-reconstruction-capture-sudo-policy-discovery-phase13-r9-attempt-20260915.json` and `docs/evidence/vm105-dsh-reconstruction-capture-sudo-policy-discovery-phase13-r9-20260915.json`.

`python -B -m unittest scripts.test_vm105_reconstruction_successor scripts.tests.test_vm105_reconstruction_capture_sudo_policy` passes 14 tests. `BROAD` and `UNSUPPORTED` remain blocks on mutation and reconstruction.
