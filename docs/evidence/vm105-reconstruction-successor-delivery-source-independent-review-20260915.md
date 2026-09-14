# VM105 Phase 13 reconstruction-successor delivery source independent review — 2026-09-15

## Verdict

**BLOCK**

| Severity | Count |
|---|---:|
| Critical | 0 |
| High | 0 |
| Medium | 1 |
| Low | 0 |

The delivery successor remains fail-closed, but its fixed build-manifest source pin is not reproducible from the reviewed commit. Do not execute the authorized delivery mode until a fresh source revision binds reproducible committed bytes and receives another independent immutable review.

## Reviewed immutable input

- Commit: `a2372ba6b29b160bac35682001b13cb643ba1937`
- Parent: `63ca98d6a73be5bc07b6c88b97ee8901dd7a3f48`
- Subject: `Add one-shot VM105 bundle delivery successor`
- Phase 12 source raw SHA-256: `756354721f19d156ab336b79755c476a74ee8075cca3a1e11e91f1a418b2b29f`

The commit changes exactly these three paths:

| Path | Git blob | Raw SHA-256 | Bytes |
|---|---|---|---:|
| `scripts/Invoke-VM105ReconstructionSuccessor.py` | `67e8d9b844899d27d0c13b8aaa90692d07598e48` | `15c346f2a14083467ec794335cc0b8d4df8eb3b1d92f3fba564bfd704c5f0eee` | 41,761 |
| `scripts/test_vm105_reconstruction_successor.py` | `14d5677a7e8f017985262fbfd127f94775fb8e62` | `8840dc7c1d203fa78dc04a3558188751d16b6a5b4114fc726a2994cdacf84066` | 3,442 |
| `docs/contracts/vm105-reconstruction-successor-contract-20260915.md` | `a2ccee7980030a45c9d63a48534edde5467e3e9c` | `165c360d6c5f7a449a5bc14db316094c5a25821472d6f3b79e7d808488a25ff9` | 4,010 |

## Finding

### [Medium] Fixed build-manifest pin is not reproducible from the commit

`BUNDLE_FILES` accepts `scripts/Build-VM105FinalClientManifest.py` only at raw SHA-256 `371481fe62d6611913f82f65b6e26b12512fda8a853a2f4591b6314f580c885f`.

The reviewed commit contains that path at raw Git-blob SHA-256 `fad4ef51cdc71dfeb182b9f428c8076e3b6fda1bd34f3129bc80abc7e81ea4ab`. Its `git archive` representation hashes to `d0beec934f53fe0061844efc60905337488efa32225f33885a19dded787ae283`. The current clean worktree happens to match the accepted pin because it contains 288 CRLF line endings among 528 newlines; normalizing those bytes to LF produces the committed Git blob. The committed `.gitattributes` has no rule for this file.

The same missing line-ending policy causes the production-launcher archive representation to hash to `db67ea85ab87acf4aaa2ec841f9d36004395f5e97516f298e39a3e5773f37035`, although its raw Git blob correctly matches the accepted pin `f2011f4d81831e4fb102f2f9e9755690418387e2f697e5ca3044417de5767c6d`.

`read_stable_source()` prevents delivery when raw checkout bytes differ, so this condition fails before SSH and cannot substitute unpinned content. The impact is reproducibility and availability: a fresh checkout or archive cannot reconstruct the exact accepted five-file payload.

Required repair: establish committed deterministic line endings for every pinned source, normalize the affected file, bind the resulting raw hashes in a fresh successor generation, and repeat immutable review. Existing accepted hashes and one-shot evidence leaves must not be reused by implication.

## Preserved controls

- The delivery binding recomputes exactly to accepted SHA-256 `392eb6e28ef879eee3348f912fb8ff66a8a692ea749f91bc399cc5aa0b6676ee`.
- Generation `phase13-20260915` and all six fresh repository-relative evidence paths are included in each binding.
- Delivery is the only accepted mode. Capture, dispatch, all four receipt pins, accepted sudo version, and accepted live bindings remain `None`.
- Every function remains AST-equivalent to Phase 12 except `deliver_bundle`; its only behavioral change checks all six fresh evidence leaves before source reads, reservation, or transport.
- The strict SSH prefix, fixed roots, embedded frame validation, source hashing, descriptor verification, root ownership and modes, fsync, `renameat2` with no-replace flag `1`, UNKNOWN-after-rename handling, bounded transport, and no-retry terminal behavior remain unchanged from Phase 12.
- Direct capture and dispatch calls stop at their authority gates without reaching transport, evidence reads, the launcher, or live bindings.

## Verification

- `git diff-tree` confirmed the exact three-path commit scope.
- The focused test ran from an extracted archive of the exact commit with bytecode writing disabled: 1/1 passed.
- The immutable invariant audit passed 49/51 checks. Its two failures were the archived build-manifest and production-launcher byte hashes described in the finding; all authority, binding, control-flow, evidence-leaf, strict-SSH, atomic-publication, UNKNOWN, and no-retry checks passed.
- Direct `git show` verified all reviewed blob bytes and the Phase 12 baseline hash.

## Authority and limits

This was a source-only independent review. The reviewed source text binds one delivery attempt, but this BLOCK verdict does not authorize running it. No SSH, sudo, bundle delivery, prerequisite capture, reconstruction, cleanup, retry, ordinary-client proof, VM105 mutation, OmniRoute action, Hermes action, or gateway action was performed. Remote state, sudo policy, bundle presence, reconstruction, and ordinary-client behavior remain unproven.
