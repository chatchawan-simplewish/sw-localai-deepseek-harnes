# VM105 R12 bounded bootstrap diagnostic contract — 2026-09-15

## Scope

R12 is one fresh, read-only production diagnostic after the spent R10
\`BLOCKED/BOOTSTRAP_REJECTED\` outcome. It is neither an R10 retry nor a repair
authority. It may contact only VM105 through the previously pinned \`dsh\` SSH
prefix after a separate Sol High source review and a separate Sol High sealed
action review both bind the exact local package.

The source is inert by default. A production run requires the action-time
binding SHA-256 and selects only the pinned successor \`_run_ssh\` transport;
it accepts no caller transport seam. It creates fresh, previously absent R12
attempt and terminal leaves exactly once. Every terminal outcome is final and
has \`retryAuthorized=false\`.

The public \`prepare_action\` and \`run_diagnostic\` APIs accept no read,
filesystem-state, publisher, or transport override. They always use the stable
reader, native \`lstat\`, exclusive publisher, and pinned successor transport.
There is no test action runner or injectable action helper in this package.

## Sealed local inputs

The action-time manifest pins this contract, the R12 source and focused test,
the committed R11 classifier source and R11 terminal boundary, the executed
\`scripts/Invoke-VM105ReconstructionSuccessor.py\` transport source, and both
\`docs/evidence/vm105-r12-bootstrap-diagnostic-source-review-20260915.json\`
and \`docs/evidence/vm105-r12-bootstrap-diagnostic-sealed-action-review-20260915.json\`.
Files are regular, unchanged, size-limited files read without following links.
The R11 files are pinned context only: R12 never
executes the classifier and never reads R10 receipts directly or indirectly.
The successor is the only external source R12 executes, solely to obtain its
sealed \`SSH_COMMAND_PREFIX\` and \`_run_ssh\`; its source path and SHA-256,
plus the prefix hash, are explicit manifest fields. The fixed wrapper and
root-launcher bytes are in the R12 source and are bound by their SHA-256 values.
Both reviews are distinct canonical JSON PASS records.
Each carries a pins map exactly equal to the manifest's complete non-review
TCB file map; the two review hashes are separately bound to avoid a self-pin
cycle. Any missing, changed, malformed, non-PASS, mismatched, or occupied fresh
leaf blocks before transport or evidence publication.

## One bounded remote diagnostic

The reviewed SSH prefix receives one fixed remote command and one canonical
stdin frame containing only R12 generation and binding. There is no caller
provided command, shell, wildcard, default route, gateway, policy query,
credential output, target write, rollback asset, or remediation.

The unprivileged wrapper invokes exactly \`/usr/bin/sudo -n\` with the absolute
Python launcher. The root launcher only verifies effective root and returns a
canonical signed classification; it reads no sudoers file and does not change
the target. The only terminal classifications are:

- \`TRANSPORT_FAILURE\` for a local transport failure or invalid transport tuple.
- \`ROOT_LAUNCHER_MISMATCH\` for a malformed or contradictory remote frame.
- \`ROOT_LAUNCHER_UNATTRIBUTED\` for a non-confirming child return, timeout,
  oversized response, or wrapper failure that does not prove the cause.
- \`ROOT_EXECUTION_CONFIRMED\` when the exact root launcher returns its signed
  confirmation.

No stdout, stderr, exception, policy text, command, credential, or remote path
is stored. The terminal contains only the allowlisted status, reason, binding,
boolean confirmation, permanent nonexecution/no-raw/no-retry flags, and a
canonical self-hash. The attempt and terminal both keep \`targetExecuted=false\`.

## Required review and one-shot boundary

A fresh independent Sol High source review at the source-review path and a
fresh independent Sol High sealed-action review at the sealed-action path are
both mandatory before an owner supplies the binding. The sole production owner
uses only the pinned successor transport and records exactly one R12 attempt and
one terminal receipt. A classification does not authorize a sudoers repair;
any repair needs its own separately reviewed reversible contract.
