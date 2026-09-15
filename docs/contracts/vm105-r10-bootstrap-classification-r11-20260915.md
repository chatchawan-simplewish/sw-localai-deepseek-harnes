# VM105 R11 local R10 bootstrap classification contract — 2026-09-15

## Scope

**LOCAL CLASSIFICATION ONLY.** This package reads the two committed R10 records and returns one in-memory classification frame. It grants no repair, retry, target contact, transport, SSH, sudo, payload, action manifest, policy parsing, evidence write, or VM105/Prox-01 action authority. R4–R10 remain spent and preserved.

## Pinned inputs and freshness

The classifier stable-reads regular, unchanged files only, limited to 64 KiB, and SHA-256-pins exactly these committed records:

- `docs/evidence/vm105-dsh-reconstruction-sudoers-narrowing-phase13-r10-attempt-20260915.json`: `8c0d7b153fcde1c508f917a4b434c183c6fc42b625f7ab7ab7b7c93fc0a3a32b`.
- `docs/evidence/vm105-dsh-reconstruction-sudoers-narrowing-phase13-r10-20260915.json`: `e48e7739e95a358560585d3bd0670b62a8087d63d3dfceb934390125c17c8432`.

Both records must be canonical JSON lines with no extra keys and a valid `receiptSha256`. They must share R10 binding `d5ba2a1514b2359c395332b82be300897c17166b5f066d194ccbee24552e48e5`. The attempt must be `ATTEMPTED/NONE`, nonexecuting and nonretryable. The terminal must be the exact pre-replacement `BLOCKED/BOOTSTRAP_REJECTED` matrix: target unexecuted; validation `-1`; no rollback asset; exact permissions false; full policy `UNSUPPORTED`; no raw output or retry.

`docs/evidence/vm105-r10-bootstrap-classification-phase13-r11-20260915.json` must be absent. The classifier never creates that leaf; a later, separately reviewed owner may decide whether to publish a local result.

## Only permitted return frame

The classifier returns exactly these keys: `classification` set to `PRE_REPLACEMENT_BOOTSTRAP_REJECTION_CAUSE_UNATTRIBUTED`; `repairAuthorized`, `targetContacted`, and `retryAuthorized` all `false`; and `r10AttemptSha256` and `r10TerminalSha256` carrying the two pinned source-record hashes. It emits no record content, policy text, payload, path from the target, credentials, or repair instruction.

Any read, pin, canonicalization, schema, self-hash, matrix, or freshness failure raises a bounded local rejection. No failure performs fallback, mutation, connection, or retry.
