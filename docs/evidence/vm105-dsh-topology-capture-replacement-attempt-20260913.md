# VM105 DSH topology replacement capture attempt — 2026-09-13

## Authority and frozen inputs

The coordinator issued one new replacement authority for the exact PowerShell block at commit `38a6c4120013c6bdbfc8bac09753dccf01356b94`. The executed contract SHA-256 was `119381f4002cac815471D314C94F52031294572BDDAD7349F73F85EAB5C22537`; capture source SHA-256 was `58f0799b56b3bfc99aacadde965bc367f7da02625787ce6241932865fc6ee02a`; focused test SHA-256 was `e7c9b2914f2ead5c39d9784b816178384f702c7103d32723612aa173726c5c56`; and predecessor-attempt evidence SHA-256 was `72e33bf4132a8688334fcb4018c052f267275d53afeda4124ec006f0f71267c5`. The independent PASS review SHA-256 was `7f04e20a1c0a8a2452e0bf4731f499b87a2d15d2cc17ea1ac1925e301a918fce` at external review commit `f74a3489ecd46a1e43d3465870fc45abb1c15f98`. That artifact is held in the separately named external review repository/worktree at `C:\ChatGPT Projects\SW-Selfhosted-Network\.worktrees\omniroute-live-review-20260913\docs\vm105-dsh-topology-capture-source-review-20260913.md`; the commit is not part of this target repository.

The contract, source, test, predecessor evidence, accepted manifest, and CRLF-sensitive builder matched their reviewed raw hashes and were regular non-reparse files. The intended receipt and private temporary leaf were absent. The pinned SSH identity and executable were regular files, and the strict known-host entry existed. The coordinator stated exclusive installed-root ownership.

## Terminal result

- Replacement coordinator invocation count: `1`
- Cumulative coordinator invocation count across both attempts: `2`
- SSH child invocation count for this replacement: `0`
- Sanitized terminal status: `CAPTURE_COORDINATOR_BLOCKED`
- Exact local category recovered without another remote action: `ACCEPTED_PACKAGE_IDENTITY_INVALID`
- Intended receipt: `docs/evidence/vm105-dsh-topology-capture-20260913.json`
- Receipt state: absent
- Receipt SHA-256: none
- Remote capture status: not started
- Remote PASS/BLOCKED receipt: none existed and none was lost
- Retry, fallback, cleanup, staging, Node/DSH execution, provider traffic, credential access, service/profile/default mutation: none

## Locally proven root cause

After binary-mode builder validation passed, `_validate_manifest()` parsed the accepted manifest's POSIX `canonicalPath` rows with platform-native `pathlib.Path`. On Windows, `/opt/deepseek-harness/...` is rooted but lacks a drive, so `WindowsPath.is_absolute()` is false. The coordinator therefore raised `ACCEPTED_PACKAGE_IDENTITY_INVALID` before `_run_bounded()`.

A local-only diagnostic replaced `_run_bounded` with a marker and called the exact successor coordinator path with the reviewed source, manifest, and builder bytes. Manifest validation raised before the marker. This proves the replacement never reached `_run_bounded`, `subprocess.Popen`, or SSH; receipt absence carries no inference about remote success or failure because remote execution did not start.

## Next gate

The replacement authority is spent. The source must validate manifest path strings with POSIX semantics independent of the coordinator operating system, reject relative/traversal forms, and pass a complete local coordinator regression using the actual accepted manifest and builder with only transport replaced by a no-network stub. Any later capture requires a new explicit coordinator dispatch; this artifact grants none.
