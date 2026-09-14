# VM105 Phase 13 R8 parser-diagnostic contract — 2026-09-15

R8 is one fresh, read-only successor to spent R4–R7 evidence. It executes only the existing two exact sudo permission queries and one bounded full-policy query. It cannot run the capture target, reconstruct, dispatch, mutate sudoers, retry any spent gate, or touch OmniRoute, Hermes, or a gateway.

R5–R7 terminal records were canonical `UNKNOWN / SUDO_POLICY_DISCOVERY_UNCERTAIN` with visible query codes reset to `-1`. R8 changes only failure observability: a rejected full-policy frame retains the three return codes and SHA-256 hashes while emitting one bounded reason: `SUDO_POLICY_FRAME_REJECTED`, `SUDO_POLICY_GRAMMAR_REJECTED`, or `SUDO_POLICY_SOURCE_REJECTED`. It never retains raw stdout, stderr, policy text, credentials, or payload.

| Path | SHA-256 |
|---|---|
| `scripts/Invoke-VM105ReconstructionSuccessor.py` | `d929842db8f1ddc978d321761a36f07a875e07d3edc63b5301ac87a92f69abb4` |
| `scripts/Capture-VM105ReconstructionCaptureSudoPolicy.py` | `a7a292046b0d240ddf88620575f01a8ce61a4541a3dc4b851f8319c0bc082648` |
| `scripts/tests/test_vm105_reconstruction_capture_sudo_policy.py` | `b71f8bc9c983a04dbd6a15b864b0298fdd2a2197da5af3503e513c8226b9a3b6` |

The accepted binding is `220c426ae58e6b6b02100d1093b918a5efc6b603e8682d51efb527a18d2b514b`. Fresh exclusive leaves are `docs/evidence/vm105-dsh-reconstruction-capture-sudo-policy-discovery-phase13-r8-attempt-20260915.json` and `docs/evidence/vm105-dsh-reconstruction-capture-sudo-policy-discovery-phase13-r8-20260915.json`.

`python -B -m unittest scripts.test_vm105_reconstruction_successor scripts.tests.test_vm105_reconstruction_capture_sudo_policy` passes 13 tests, including parser-rejection sanitization. An `UNKNOWN` terminal remains a block on all later action.
