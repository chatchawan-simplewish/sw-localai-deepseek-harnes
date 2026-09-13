# VM105 DSH topology capture third attempt — 2026-09-13

## Result

`BLOCKED / THIRD ONE-SHOT AUTHORITY SPENT / NO TOPOLOGY ACCEPTANCE`

The coordinator dispatched frozen commit `2c16a3d7d6a953d6d8ad35ab8e37cce46b950c61` once. Local preflight validated capture source SHA-256 `17e43721293d3bffe5c33f63ad2491cd79905bc961993bf40ac0072e48a2bb73`, contract SHA-256 `7d7348637c198ae717e6ad08df7769edf2bc526618b5287257051aba128dbbbc`, test SHA-256 `215f65c2b737d62fe18ffee3afd3e5c11b5d84a0469a48dc3fc2d32aff8b97a7`, accepted-manifest file SHA-256 `54d117c638335edeefe43aaef0f181ea5317f7938a6861a145871a0d9e45e8dd`, raw CRLF builder SHA-256 `371481fe62d6611913f82f65b6e26b12512fda8a853a2f4591b6314f580c885f`, first-attempt evidence SHA-256 `9c4226d2e3d16552a44a2c4fcbe93df190b37fd198af46b7d1b5e926f8b5c0db`, and second-attempt evidence SHA-256 `fa21d4bf1a3b9a6acb96253ff61e1d1bb8f8e00306585c7f2bec4dc3c9da50e1`.

One SSH child and the fixed remote bootstrap/source entry ran. The bounded transport returned one canonical UTF-8 JSON line, which passed BLOCKED-schema and canonical self-hash validation before fresh no-overwrite publication at `docs/evidence/vm105-dsh-topology-capture-20260913.json`.

- Status: `BLOCKED`
- Sole reason: `CAPTURE_TARGET_MISMATCH`
- Receipt self-hash: `af969cf020e957fc935a825809e4d062ed9cef1879f468c231adc05d3e7e8925`
- Raw receipt SHA-256: `86d878deb002c62cf69013717d38193248b7deed5b19a5a37c40e87de07c001d`
- Raw size and framing: 142 bytes, canonical JSON followed by one LF

## Root cause and boundary

The frozen Windows coordinator used `str(Path('/opt/deepseek-harness'))` in its payload. That serialized as `\opt\deepseek-harness`; the remote source required literal `/opt/deepseek-harness`. Target equality is the first source gate, so the attempt stopped before accepted-manifest validation, builder compilation or execution, `ldd`, installed-tree reads, or topology traversal. It performed no retry, fallback, staging, DSH/Node package execution, provider request, credential access, service change, profile change, or default mutation.

The third authority is spent. The occupied BLOCKED receipt is immutable failure evidence and cannot be used as an accepted topology receipt. A future capture requires a newly named absent evidence leaf, newly frozen source/contract/tests, independent review, and fresh explicit authority.

## Independent review

The external review artifact is `C:\ChatGPT Projects\SW-Selfhosted-Network\.worktrees\omniroute-live-review-20260913\docs\vm105-dsh-topology-capture-third-receipt-review-20260913.md`, SHA-256 `46612f8be54f718e7b7bf41d17829f4b537c4582d395f3c07e2e36dd52839380`, committed there as `e377656bd91b602535a7f0ca8459500556c1a987`. It passed the receipt as failure evidence only and granted no retry or execution authority.

The local successor serializes the fixed POSIX install root at the CLI, coordinator transport, and remote payload checks. Its 16-test suite includes the actual accepted manifest and raw CRLF builder through a no-network coordinator-to-remote-entry fixture. Those local checks do not prove VM105 topology or authorize a new capture.
