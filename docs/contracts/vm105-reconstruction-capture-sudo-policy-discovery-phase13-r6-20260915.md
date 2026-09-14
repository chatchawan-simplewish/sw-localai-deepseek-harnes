# VM105 Phase 13 R6 capture sudo-policy discovery contract — 2026-09-15

## Authority

R6 is one fresh, read-only discovery gate. It may make exactly two `sudo -n -l -- <argv>` queries and one bounded `sudo -V`/`sudo -n -ll` query through the reviewed SSH prefix. It cannot capture the bundle, edit sudoers, reconstruct, dispatch, retry R4 or R5, or touch OmniRoute, Hermes, or a gateway.

## Spent evidence and root cause

R4 bundle capture remains spent: `a588740fcdb447b0ab1cf425ca53062a0577c7d8f439dd6467964efa082f2745` / `e2239a359200d814e23de1c19214f5c28eda2c591ac1b528c2779af5d6c14b96`, `UNKNOWN / BUNDLE_CAPTURE_TRANSPORT_UNKNOWN`.

R5 policy discovery remains spent: `eb1ed671ca295fe6206864e95a1b33d30d8d10b98e0f11893bfe6304a5d51364` / `64387da1bd30ec80cc6d0c1b85788416a6b7d28fe874e7f97f5841ebe020b033`, `UNKNOWN / SUDO_POLICY_DISCOVERY_UNCERTAIN`, with no target executed and no retry authority.

The local transport test reproduces the shared SSH wrapper's failure mode: it flushed and treated a broken close on empty stdin as `SSH_STDIN_FAILED` before a query result could be classified. R6 changes only that shared empty-payload behavior: it sends no flush and tolerates a close race when no bytes were supplied. Nonempty payload failures remain fail-closed.

## Immutable source and binding

| Path | SHA-256 |
|---|---|
| `scripts/Invoke-VM105ReconstructionSuccessor.py` | `d929842db8f1ddc978d321761a36f07a875e07d3edc63b5301ac87a92f69abb4` |
| `scripts/test_vm105_reconstruction_successor.py` | `45c2f500a090984e33b6ecb51530aa7f6a506524760cbd3e19b350e0ce11983a` |
| `scripts/Capture-VM105ReconstructionCaptureSudoPolicy.py` | `13100ab08c07d9503aca0820cdac21906149ec50c4a8def44e5a963253962758` |
| `scripts/tests/test_vm105_reconstruction_capture_sudo_policy.py` | `08eb9f754a8de746d1de727e59c36a7e3fa2e4b077c0d9c678059fc8e6c8fb8e` |

The accepted binding is `26099a1a9c4e745bd68d034b3feec2483082ba73357d915ac6cf18eb7fc2f036`. The new exclusive leaves are `docs/evidence/vm105-dsh-reconstruction-capture-sudo-policy-discovery-phase13-r6-attempt-20260915.json` and `docs/evidence/vm105-dsh-reconstruction-capture-sudo-policy-discovery-phase13-r6-20260915.json`.

## Verification and limits

`python -B -m unittest scripts.test_vm105_reconstruction_successor scripts.tests.test_vm105_reconstruction_capture_sudo_policy` passes 11 tests. The added regression makes an empty-input SSH process with a closed stdin return its result rather than fail before classification. All policy-parser checks remain source-only.

R6 records only canonical hashes, scalars, and safe sudoers source paths. It retains no raw stdout, stderr, policy text, credentials, or executable payload. Transport errors remain `UNKNOWN`; broad or unsupported policy grants no mutation or retry.
