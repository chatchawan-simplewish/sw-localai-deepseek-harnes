# VM105 Phase 13 R7 bounded SSH diagnostic contract — 2026-09-15

R7 is a fresh one-shot, read-only successor to spent R5 and R6 discovery. It retains their canonical `UNKNOWN / SUDO_POLICY_DISCOVERY_UNCERTAIN` provenance and performs the same two exact sudo permission queries plus the bounded full-policy query. It cannot run either target, capture a bundle, mutate sudoers, reconstruct, dispatch, retry R4–R6, or touch OmniRoute, Hermes, or a gateway.

The only change is diagnostic evidence: an existing bounded SSH runner failure is recorded as one of `SSH_START_FAILED`, `SSH_TIMEOUT`, `SSH_OUTPUT_LIMIT_EXCEEDED`, `SSH_DRAIN_FAILED`, or `SSH_STDIN_FAILED`. Unexpected errors remain `SUDO_POLICY_DISCOVERY_UNCERTAIN`. No stdout, stderr, sudo policy, credentials, or payload is retained.

| Path | SHA-256 |
|---|---|
| `scripts/Invoke-VM105ReconstructionSuccessor.py` | `d929842db8f1ddc978d321761a36f07a875e07d3edc63b5301ac87a92f69abb4` |
| `scripts/Capture-VM105ReconstructionCaptureSudoPolicy.py` | `c64f414cfbd21ba58c6fa7077964d58ee88489c1dbe5d0e52fd866212c341c37` |
| `scripts/tests/test_vm105_reconstruction_capture_sudo_policy.py` | `ebf10b149ad6077d00180af869aff34fbedf99be9db43a7e428096c84f66cccd` |

The accepted binding is `a32a7d5b5402ecce2bcb5eb133d97c72cdd06a7ed65d4f780e839209f47d66da`. Fresh exclusive leaves are `docs/evidence/vm105-dsh-reconstruction-capture-sudo-policy-discovery-phase13-r7-attempt-20260915.json` and `docs/evidence/vm105-dsh-reconstruction-capture-sudo-policy-discovery-phase13-r7-20260915.json`.

`python -B -m unittest scripts.test_vm105_reconstruction_successor scripts.tests.test_vm105_reconstruction_capture_sudo_policy` passes 12 tests, including the bounded failure-category regression. A terminal `UNKNOWN` remains a failed discovery and grants no later action.
