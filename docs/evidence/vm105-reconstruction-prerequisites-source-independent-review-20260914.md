# VM105 reconstruction prerequisites independent source review — 2026-09-14

## Verdict

**PASS — immutable source review.** No HIGH or MEDIUM findings remain in the three reviewed Git blobs at commit `d3fed09318effdf7273063647fd36b1bc0007837` on branch `codex/vm105-authoritative-roadmap`.

This verdict is limited to the committed source, tests, and contract. It grants no authority and makes no live-state claim.

## Review identity

- Repository: `https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git`
- Commit: `d3fed09318effdf7273063647fd36b1bc0007837`
- Parent: `cead316c61a9402ad954aeb55a713b78ef7b0d67`
- Commit subject: `Add dormant VM105 reconstruction prerequisite contract`
- Review time: `2026-09-14T16:01:07+07:00`

| Reviewed Git blob | Git blob object | Raw SHA-256 |
|---|---|---|
| `scripts/Invoke-VM105ReconstructionPrerequisites.py` | `b6f37a9a01134b9b7ec3f94aaa80d6f8978159ef` | `756354721f19d156ab336b79755c476a74ee8075cca3a1e11e91f1a418b2b29f` |
| `scripts/test_vm105_reconstruction_prerequisites.py` | `9e0bb8ef0e5360601c3c69eb2244095c93c8e6f9` | `1f5210c84a4c22e55dfe559ff79049d5d5c9197c80daf417ae2340754720c432` |
| `docs/contracts/vm105-reconstruction-prerequisites-and-dispatch-contract-20260914.md` | `cc3646f4cb64ff0989ca4e8228d2fc38f1177cb0` | `e893a51a2b1105f4cd6700c62986d2821ec7c3f35513ce8ac1b990ed58f68ec2` |

## Resolved findings

1. **Direct-call authority and receipt-pin bypass — resolved.** Every callable live mode requires its module accepted binding to be non-`None` and equal both the provided and computed binding. Reconstruction dispatch additionally requires all four module accepted receipt raw/self hashes to be valid and requires every caller value to equal its accepted value before either receipt is read. The regression test proves that a substituted receipt pin stops before evidence or launcher access.
2. **Sudo-policy false assurance and grammar gap — resolved.** Exact-command allowance and a separate complete `sudo -ll` policy capture are both required. PASS requires an accepted exact sudo version, one exact root/NOPASSWD target rule, no extra rule or command, and only the explicitly permitted non-authorizing Defaults/source metadata. `NOPASSWD: ALL`, broader Python or shell authority, wildcards, authorizing or unknown Defaults, ambiguous output, version drift, and nonempty stderr cannot produce PASS. Raw policy and stderr are not stored.

## Security and fail-closed checks

- All three mode authority constants, four receipt acceptance constants, `ACCEPTED_SUDO_VERSION`, and `ACCEPTED_LIVE_BINDINGS` are `None`; all CLI modes return signed `BLOCKED` before transport.
- The bundle has exactly five fixed source paths, destination basenames, and raw SHA-256 pins. The delivery bootstrap embeds and enforces the same five name/hash pairs before creating its temporary root.
- Local source and evidence reads use bounded stable descriptor reads with available `O_NOFOLLOW` and close-on-exec flags, path/descriptor identity checks, and exact raw-hash verification.
- Bundle capture opens a held root descriptor, rejects missing or extra directory members, reads each fixed leaf relative to that descriptor, and rechecks root identity.
- Local evidence records are canonical, self-hashed, and published with `O_CREAT|O_EXCL`; occupied leaves stop before transport.
- Remote delivery uses exclusive file creation, descriptor-held write/reread verification, root ownership, fixed modes, file/directory fsync, and Linux `renameat2(..., RENAME_NOREPLACE)`. Pre-publication failure retains the temporary root; post-publication uncertainty is `UNKNOWN`; neither authorizes cleanup or retry.
- Local SSH I/O is concurrently bounded. Timeout, overflow, stdin failure, or drain failure kills and reaps the local process and produces only sanitized uncertainty evidence.
- Bundle and sudo receipts have exact key sets, canonical self-hashes, strict scalar/container types, exact pins, and PASS-only dispatch validation. No raw stderr is retained.
- The immutable launcher is held-read at raw SHA-256 `f2011f4d81831e4fb102f2f9e9755690418387e2f697e5ca3044417de5767c6d`; only `RECONSTRUCTION_BINDING`, `RECONSTRUCTION_REMOTE_BOOTSTRAP`, `_run_bounded_reconstruction_ssh`, and `_coordinate_reconstruction_attempt` are reused for reconstruction.
- The authenticated reconstruction bootstrap is exactly 2,072 ASCII bytes with SHA-256 `cb0281b3a3816d355a6e114f11f55776ed1f3ca6a95be3e4874d4b4b613dd171`. The complete remote command is exactly 2,949 ASCII bytes with SHA-256 `b2f1c14ee67933c33bea9dde2736e384389c926d84837be0820ef73d57ca8d48`.
- The fixed SSH argv includes `--` immediately before `dsh@192.168.1.139`, pins authentication and host-key behavior, and disables forwarding.
- Dispatch rereads both independently accepted receipts through stable descriptors, checks raw and self hashes, rejects live bindings, and uses the immutable launcher's one-shot reconstruction coordinator.
- Reconstruction and the production canary remain separate proof and authority boundaries. Reconstruction does not authorize or prove the two-request canary or any provider, credential, default, ordinary-session, persistence, or replay claim.

## Verification

- Independently hashed the three Git blobs from the commit object; all matched the required raw SHA-256 values above.
- Confirmed the byte-identical worktree copies of the three reviewed files match the commit before source-only execution.
- Ran `python -B scripts/test_vm105_reconstruction_prerequisites.py` with `PYTHONDONTWRITEBYTECODE=1`: **11 tests passed**.
- Recomputed the launcher bootstrap and full remote-command byte counts and SHA-256 values: both matched the fixed pins.
- Recomputed the five referenced local bundle-source raw SHA-256 values in the current worktree: all matched the contract pins.
- Confirmed all nine accepted authority/version/live values remain `None` and each CLI mode returned `BLOCKED` without invoking transport.

## Limits and no-live statement

No SSH connection, `sudo` command, bundle delivery, prerequisite capture, reconstruction, staging, cleanup, retry, VM/service mutation, OmniRoute or Hermes action, credential access, gateway/provider request, canary, or other live action was performed. The live VM sudo version and policy grammar, remote roots and files, host identity, staging absence, runtime behavior, provider generation, credentials, defaults, persistence, and canary behavior remain **NOT PROVEN**.

The review changed only this evidence file. It did not edit the reviewed source, test, or contract; did not touch `scripts/__pycache__`; and did not stage, commit, or push anything.
