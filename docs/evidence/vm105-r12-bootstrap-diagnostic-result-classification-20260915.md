# VM105 R12 bootstrap diagnostic result classification — 2026-09-15

## Verdict

**PASS / `ROOT_EXECUTION_CONFIRMED` — DIAGNOSTIC ONLY; AUTHORITY FALSE.**

The canonical R12 terminal proves that the exact launcher bound by the sealed
R12 manifest executed with effective root through the pinned production SSH
and `/usr/bin/sudo -n` path. It does not reveal sudoers or other policy text,
diagnose the cause of R10 `BOOTSTRAP_REJECTED`, prove that the R10 payload
bootstrap can execute, authorize remediation, or permit an R12 retry. R10
remains spent and its pre-replacement bootstrap rejection cause remains
unattributed.

## Validated binding and receipts

- Committed R12 package head: `0b97766ac2808515260ec2ee0508663f97f19fd8`.
- Recomputed manifest binding: `f6ad098c8b926356d78a74669fda5d187ea1577424f4c65f54a8af9cf2931ba6`.
- Pinned SSH prefix SHA-256: `826a2b2c2f0d367a95fb8a267e48f189d87bceb1cf8d9875700989d0d8cdb083`.
- Source review `docs/evidence/vm105-r12-bootstrap-diagnostic-source-review-20260915.json`: raw SHA-256 `0f605ff1917e2b0495de3bc84b41c6a48844a14a871977249ed15ccb9b2f0e96`, canonical `PASS`.
- Sealed-action review `docs/evidence/vm105-r12-bootstrap-diagnostic-sealed-action-review-20260915.json`: raw SHA-256 `0f605ff1917e2b0495de3bc84b41c6a48844a14a871977249ed15ccb9b2f0e96`, canonical `PASS`.
- Attempt `docs/evidence/vm105-r12-bootstrap-diagnostic-phase13-attempt-20260915.json`: raw SHA-256 `777eca46a302715a4acc7a5131685e7c510b6e7ca2b0df0e452ec45058cf6a4d`; self-hash `d552dd551b773e618f8abfe2bdaf12c65a41909571ccce824ff48c5e340cd46d`; `ATTEMPTED/NONE`.
- Terminal `docs/evidence/vm105-r12-bootstrap-diagnostic-phase13-20260915.json`: raw SHA-256 `d4080f7b74c62c23016e407bbb01d6e758e08622e1094432a2ba811b9054f2f1`; self-hash `916c72423d3e4fe7f6cd6ecf11d22e9cfb382a261a6a9fb8745e68dcdaa39d9b`; `PASS/ROOT_EXECUTION_CONFIRMED`.

Both fresh leaves are regular files, canonical JSON plus one LF, have the exact
secret-free receipt schema, share the recomputed binding, and set
`rawOutputStored=false`, `targetExecuted=false`, and `retryAuthorized=false`.
The attempt predates the terminal. The sealed source uses exclusive publication
and one transport call between those leaves, so this pair records one R12
diagnostic action and now blocks re-entry.

## Complete non-review pins

- `docs/contracts/vm105-r12-bootstrap-diagnostic-contract-20260915.md`: `5b919757a70785f3040097fa48b9542da7ef49472c926a983047b8cf5e75fab2`.
- `docs/handoffs/2026-09-15-vm105-r11-source-only-terminal-boundary.md`: `d43fc487f0d10289f6f1b4f8d39b817609745468fd112f154869c23199c5dda5`.
- `scripts/Classify-VM105R10BootstrapTerminal.py`: `9442580b00166097862279c151db2fe52b66427fdaffe5f5363ab0911f40a8d3`.
- `scripts/Invoke-VM105R12BootstrapDiagnostic.py`: `9467b78e32bc5a0f8571445e93178e8118869edb094125e91b610455431c8ad1`.
- `scripts/Invoke-VM105ReconstructionSuccessor.py`: `d929842db8f1ddc978d321761a36f07a875e07d3edc63b5301ac87a92f69abb4`.
- `scripts/tests/test_vm105_r12_bootstrap_diagnostic.py`: `c122e4ebec5ab225bf0ef872bfced4f17e7d8b88ec81c17bfff31d6cee12cdc6`.

## Smallest next-contract prerequisite

Any further diagnosis requires a new, independently reviewed, read-only
contract with fresh non-R12 evidence leaves that can distinguish the R10
payload-bootstrap rejection from root-launcher availability without retaining
raw policy or other sensitive output. That prerequisite has `authority=false`:
it grants no repair, sudoers mutation, R10/R12 retry, reconstruction, or other
target action. Remediation would still require a later, separately reviewed
reversible-action contract.
