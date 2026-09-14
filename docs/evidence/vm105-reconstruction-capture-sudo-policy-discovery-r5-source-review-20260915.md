# VM105 Phase 13 R5 capture sudo-policy discovery source review — 2026-09-15

## Verdict

PASS for source publication only. This review authorizes neither SSH nor sudo execution; the separate R5 discovery remains a fresh one-shot, read-only gate.

## Reviewed commit and scope

- Commit: `cefb58efc9c3cc69106a9a2dac56879dc4f3dcb1`
- Parent: `879e09cc2a9fab8ebd0608d3ea2d1f6534070e13`
- Reviewed tracked paths: `.gitattributes`, `scripts/Capture-VM105ReconstructionCaptureSudoPolicy.py`, `scripts/tests/test_vm105_reconstruction_capture_sudo_policy.py`, and `docs/contracts/vm105-reconstruction-capture-sudo-policy-discovery-phase13-r5-20260915.md`.
- Preserved unrelated state: `scripts/__pycache__/` remains untracked and untouched.

## Byte and binding verification

`git show HEAD:<path>` SHA-256 values match the worktree and contract:

| Path | SHA-256 |
|---|---|
| `scripts/Capture-VM105ReconstructionCaptureSudoPolicy.py` | `06482b2ab89b463edafca044c1bca905385b52bb54ca74e9fb7a92f3ccfbf876` |
| `scripts/tests/test_vm105_reconstruction_capture_sudo_policy.py` | `f340013eff0482b5b9ef4162c199c2a52ee6c8f00763ddee587c3f22dc340b06` |
| `docs/contracts/vm105-reconstruction-capture-sudo-policy-discovery-phase13-r5-20260915.md` | `0d6728dbf76f367056331a6210b276e1ccc1c4034cffa557627c9835000e551b` |
| `.gitattributes` | `c7db7be32cf1b3cf162a0dc3c027d785b493a59ee1fa8ffb1136c3e6c704afcb` |

The three reviewed source paths have `text eol=lf`; their committed bytes are stable for a fresh checkout. The discovery binding recomputes to the accepted value `0998b798aa925b2fcb1182f46655187ec7b6410851e6d90e8d10967fcc425540`.

## Behavioral verification

`python -B -m unittest scripts.tests.test_vm105_reconstruction_capture_sudo_policy scripts.test_vm105_reconstruction_successor` passed 10/10 tests.

The R5 module stable-loads the reviewed R4 successor (`35084d5e879d5ef0c207d0c17d546a5d3be1645129ea361961d66516856e6517`) and binds the R2 delivery receipt plus the spent R4 `UNKNOWN` receipt. It reserves fresh exclusive leaves and makes exactly two nonexecuting `sudo -n -l -- <argv>` queries plus one bounded `sudo -V`/`sudo -n -ll` query. It cannot run a capture target or dispatch reconstruction.

The parser accepts sudo `1.9.15p5`'s inline `Sudoers entry: <safe-path>` form, tab-prefixed command rows, and equal Defaults/User hosts. It rejects unsafe paths, synthetic `Source:` coordinates, version or grammar drift, extra output, and transport uncertainty. Receipts retain only hashes, scalars, and safe source paths; raw policy, stdout, and stderr are excluded.

## Limits

This is local source evidence only. It does not prove VM105 reachability, current sudo policy, bundle access, sudoers mutation, reconstruction, or ordinary-client behavior. No SSH, sudo, VM105 mutation, OmniRoute, Hermes, or gateway action was performed during review.
