# VM105 DSH topology capture attempt — 2026-09-13

## Authority and frozen inputs

The coordinator authorized exactly one read-only capture from commit `704f56bf1cbbfa8c80bbc11685d451e62a68cea9`. The executed PowerShell block came from `docs/contracts/vm105-dsh-topology-capture-contract-20260913.md`, SHA-256 `869c5b50de6911768cb5a62c27937c1c10f8c19ae53636f69fffe91e2d91128f`. The independently reviewed capture source SHA-256 was `3c4b36680d05fd55c9ab3bb33331cc3fc68eee4eee3f26adf7a32f0c47891b66`; the review artifact SHA-256 was `3e3bbe894861b753f789cef474a9631a37d0ef6eaae8059675db935f34dd3d5b` at review commit `40ec5db7f54f7284752bc8194320f5f9aa1eb00a`.

Before dispatch, the contract, capture source, focused test, accepted manifest, and pinned builder matched their reviewed hashes; each local input was a regular non-reparse file. The intended evidence leaf was absent, the pinned SSH identity was a regular non-reparse file, the OpenSSH executable was present, and strict host-key checking was configured.

## Terminal result

- Coordinator invocation count: `1`
- SSH child invocation count: `0`
- Sanitized terminal status: `CAPTURE_COORDINATOR_BLOCKED`
- Exact local category recovered without another remote action: `ACCEPTED_BUILDER_HASH_MISMATCH`
- Intended receipt: `docs/evidence/vm105-dsh-topology-capture-20260913.json`
- Receipt state: absent
- Receipt SHA-256: none
- Remote capture status: not started
- Remote PASS/BLOCKED receipt: none existed and none was lost
- Retry, fallback, cleanup, staging, Node/DSH execution, provider traffic, credential access, service/profile/default mutation: none

## Locally proven root cause

`Capture-VM105DshTopology.py::_read_pinned_file()` opened the builder with `os.O_RDONLY | O_CLOEXEC | O_NOFOLLOW` but omitted Windows `O_BINARY`. Windows text-mode `os.read` translated CRLF to LF before hashing. The reviewed raw builder was 23,327 bytes with SHA-256 `371481fe62d6611913f82f65b6e26b12512fda8a853a2f4591b6314f580c885f`; the translated stream was 23,039 bytes with SHA-256 `fad4ef51cdc71dfeb182b9f428c8076e3b6fda1bd34f3129bc80abc7e81ea4ab`.

A local-only diagnostic replaced `_run_bounded` with a marker and called the frozen coordinator path. The builder check raised before that marker, proving the code never reached `_run_bounded`, `subprocess.Popen`, or SSH. No remote success or failure is inferred from receipt absence; remote execution is proven not to have started.

## Next gate

The one-shot capture authority is spent. A minimal local source fix must add binary-mode pinned-file reads and a CRLF regression, then receive independent review. Any later capture requires a new explicit coordinator dispatch; this artifact grants none.
