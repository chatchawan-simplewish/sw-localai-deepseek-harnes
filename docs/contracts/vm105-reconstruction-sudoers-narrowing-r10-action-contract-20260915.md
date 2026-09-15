# VM105 Phase 13 R10 sealed sudoers action contract — 2026-09-15

## Status and authority

**PREPARATION ONLY.** This is the action-source contract for the one R10 transition; it grants no SSH, sudo, write, capture, reconstruction, dispatch, cleanup, retry, or OmniRoute/Hermes/gateway/default action. R4–R9 remain spent. A future source may enter the remote bootstrap only when its explicit action-time authorization input byte-for-byte equals its computed, reviewed sealed binding SHA-256. Missing, duplicated, malformed, or nonmatching input is `SUDOERS_NARROWING_NOT_AUTHORIZED` before transport.

## Sealed local binding

The canonical binding contains only: generation; fixed R10 attempt and terminal evidence leaves; reviewed R9 source path and SHA-256; R9 receipt path, raw SHA-256, and self SHA-256; the repository-relative path and stable SHA-256 for the reviewed action source, focused action test, independent payload/action review artifact, and this action contract; target `/etc/sudoers.d/90-cloud-init-users`; rollback-root prefix `/var/tmp/omniroute-dsh-sudoers-r10-`; absolute validator `/usr/sbin/visudo`; unique same-directory candidate path rule; the two R9 capture/reconstruction argc, argv-SHA-256, and bootstrap-SHA-256 triples; and the ordered action steps below. The action source must reject if either R10 evidence leaf already exists, any sealed local input changes, or R9 is not its canonical `PASS/NONE`, `BROAD`, nonexecuting, no-raw-output, no-retry record with the two safe source paths.

Each binding file is a regular repository file read without following links and is limited to its reviewed SHA-256. The source computes its own file SHA-256 and the canonical binding at action time, then compares the explicit authorization input to that computed binding SHA-256. Neither the binding nor the source contains a precomputed binding SHA-256 or a self-hash expectation: the source/action-source hash is an input to the computation, never a self-referential requirement.

The source obtains the two complete argv vectors only from the SHA-pinned reviewed R9 source, recomputes each sealed argc/argv/bootstrap triple, and emits neither vector nor bootstrap in a receipt, error, log, or exception. It accepts no caller-provided command, target, policy fragment, path, or payload.

## Machine-checkable pre-transition policy

The root bootstrap reads `/etc/sudoers` and the sole target as bytes, parses them in memory, and never persists or emits their contents. Its grammar accepts exactly one `dsh` authorizing logical entry across both files, located in the target. That entry has exactly these normalized fields: `user=dsh`, `host=ALL`, `run-as=ALL`, `tag=NOPASSWD`, and `command=ALL`. It has no additional users, hosts, run-as values, tags, commands, or options.

The parser rejects an alias declaration or alias reference, continuation, include/include-dir directive, duplicate `dsh` authorization, any `dsh` token outside the one accepted entry, non-ASCII or malformed syntax, or any ambiguity affecting `dsh`. A `dsh` authorization in `/etc/sudoers`, zero accepted entries, or more than one accepted entry fails before rollback creation. Non-`dsh` policy text is not emitted or recorded.

## Reversible root bootstrap

After the grammar passes, the bootstrap creates a fresh root-owned mode-`0600` rollback asset under the sealed rollback-root prefix, copies only the target bytes into it, and retains its path, size, and SHA-256 in memory. It constructs the replacement from the reviewed vectors only: root run-as; noninteractive NOPASSWD; precisely the two complete R9-bound argv vectors; no shell, wildcard, `ALL`, alias, extra Python invocation, option variation, or interactive authorization.

It writes a root-owned mode-`0440` candidate without following links, calls `/usr/sbin/visudo -cf` on that candidate, and atomically replaces only `/etc/sudoers.d/90-cloud-init-users` after validation succeeds. `/etc/sudoers` is never written. Any failure before replacement leaves the target unchanged. Any failure after replacement restores the rollback asset atomically; rollback failure is terminal `UNKNOWN`.

Immediately after replacement, while still inside the bootstrap, root launches the two bounded nonexecuting exact permission queries and the reviewed semantic full-policy projection as unprivileged `dsh`. Root must retain the rollback asset and the capability to restore the target until their canonical, validated result is complete; root is forbidden from attesting its own authority. PASS requires both `dsh` vectors to be exactly allowed and the effective policy state to be `EXACT`. Any other result automatically restores the rollback asset before the bootstrap returns. It never executes either vector, capture, reconstruction, dispatch, cleanup, or a retry.

## Sealed receipt and terminality

The remote result may contain only these fields: `generation`, `bindingSha256`, `status`, bounded uppercase `reason`, `targetPath`, `rollbackCreated`, `rollbackPath`, `rollbackSize`, `rollbackSha256`, `candidateValidationCode`, `captureExactAllowed`, `reconstructionExactAllowed`, `fullPolicyState`, `rollbackStatus`, `targetExecuted`, `rawOutputStored`, and `retryAuthorized`, plus a canonical self-hash. `status` is only `PASS`, `BLOCKED`, or `UNKNOWN`; `targetExecuted`, `rawOutputStored`, and `retryAuthorized` are always `false`. A receipt contains no sudoers text, candidate or rollback bytes, argv, bootstrap, payload, stderr, exception text, credentials, or unallowlisted key.

Exactly one terminal local receipt is written from the allowlisted remote result. Every outcome consumes the R10 action attempt: `PASS` records the narrow authority; `BLOCKED` records either unchanged pre-replacement failure or successful rollback; `UNKNOWN` records uncertainty or rollback failure. No outcome authorizes a second connection, bootstrap, mutation, cleanup, or retry.
