# VM105 Phase 13 R10 reversible sudoers narrowing contract — 2026-09-15

## Status

**PREPARATION ONLY.** This contract authorizes no SSH, sudo, sudoers write, capture, reconstruction, dispatch, retry, or default/provider action. R4–R9 remain spent. R9 proves both fixed commands are allowed through broad authority; its raw/self receipt hashes are `6f948f4b57199f54da8c9c267140eff37afffa961c3ad59ae694c697fdfb3c6f` / `43858d3d3e993546a5cfc7d4589ac6eebd660b177446810173403d08342aa7b8`.

## Minimum safe transition

The sole candidate target is `/etc/sudoers.d/90-cloud-init-users`. `/etc/sudoers` is never edited. Before any write, one reviewed root-only bootstrap must:

1. Read both R9 safe source paths without emitting their contents.
2. Reject unless every `dsh` authorizing entry has the expected broad-rule shape, the broad `dsh` entry is in `90-cloud-init-users`, and no ambiguous continuation, include, alias, or duplicate authorization exists.
3. Create a root-owned `0600` rollback asset below a fresh fixed `/var/tmp/omniroute-dsh-sudoers-r10-*` path. Evidence retains only its path, size, and SHA-256.
4. Write a temporary replacement that permits only the two R9-bound full argv vectors: the root-owned capture attestation bootstrap and the root-owned reconstruction bootstrap. It must not permit shell, wildcard, `ALL`, another Python argv, or interactive authentication.
5. Validate the complete candidate policy with absolute `visudo -cf` before atomic replacement; leave the old file untouched on any failure.
6. Immediately run bounded nonexecuting exact queries for both argv vectors and a semantic full-policy projection. PASS requires both exact queries allowed and full policy `EXACT`; any other result triggers an automatic rollback from the preserved asset.

## Action-time pins

The mutation source must pin the published R9 terminal receipt and the reviewed successor source. It must bind the capture/reconstruction canonical argv hashes and bootstrap hashes, the target source path, rollback path, `visudo` path, temporary path, and every fresh evidence leaf. It must check that both new leaves are absent before reading or writing VM105 state.

## Evidence and limits

The terminal receipt may contain only status, bounded reason, hashes, source paths, file metadata, validation return codes, exact-query booleans, semantic policy state, and rollback status. It must not contain sudoers text, stderr, credentials, or executable payloads.

This contract deliberately stops before mutation. A source package, focused test, independent review, and action-time revalidation remain required before the single transition gate is consumed.
