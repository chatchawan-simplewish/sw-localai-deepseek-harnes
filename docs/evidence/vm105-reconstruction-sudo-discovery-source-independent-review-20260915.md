# VM105 reconstruction sudo-discovery independent source review — 2026-09-15

## Verdict

**PASS — immutable source review.** Findings: **HIGH 0, MEDIUM 0, LOW 0** for the three reviewed Git blobs at commit `ffcd60766e48e18a53abb39e54c7395bd06b6fc4` on branch `codex/vm105-authoritative-roadmap`.

This verdict is limited to the committed source, test, and contract. It confirms the narrow read-only discovery authority encoded by that package; it does not authorize reconstruction or establish live VM state.

## Review identity

- Repository: `https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git`
- Commit: `ffcd60766e48e18a53abb39e54c7395bd06b6fc4`
- Parent: `2883c715f9bcc38510ef9291e3e90739673be6ff`
- Commit subject: `Add one-shot VM105 sudo discovery`
- Review time: `2026-09-15T05:22:28+07:00`
- Discovery binding: `9aabf6718dea7dc914d4cfac70f3651bd626055f8af0247c582d2d09f9dae427`
- Stable-loaded successor raw SHA-256: `b30366f98a22e1a77fbd24451248111adb884280e625d0ac0844d62fb881c960`

| Reviewed Git blob | Git blob object | Raw SHA-256 |
|---|---|---|
| `scripts/Capture-VM105ReconstructionSudoVersion.py` | `784a07095b29579e304ebeecff0143ee800d0f2f` | `115d29a7e4bfb2bb11d2b8d5ad9b43ee3390b120d770d559962f6ad4b0e106d1` |
| `scripts/test_vm105_reconstruction_sudo_version.py` | `b7912d7c73090fd10de7d9e0a77eccbf7bc3d624` | `a83e28e83fce633bf67404ca284b425efba40bc2292ec9666dab2c3a63992e4a` |
| `docs/contracts/vm105-reconstruction-sudo-version-discovery-contract-20260915.md` | `69a32ff5a59da9ac29004246094cb7d19f9e99fa` | `c26a876e7042d46178356f6c571e78cc9cc1cc5b71d22afaa208dafecba225c4` |

## Security and authority checks

- The caller value, accepted constant, and freshly recomputed canonical binding must all equal the discovery binding above. Binding drift or a substituted authority blocks before transport.
- The successor is read through a bounded stable descriptor, must match its raw SHA-256 pin, and must retain `None` for prerequisite capture, reconstruction dispatch, four receipt, sudo-version, and live-binding gates. Its earlier bundle-delivery authority is not read or called.
- The fixed SSH argv uses `C:\Windows\System32\OpenSSH\ssh.exe`, `-F NUL`, batch and identity-only authentication, disabled password and keyboard-interactive authentication, strict host-key checking, disabled forwarding, bounded connection attempts, and `--` before `dsh@192.168.1.139`.
- The authority permits exactly two SSH calls with empty stdin. The first runs only `sudo -n -l -- <exact reconstruction argv>`. The second runs the pinned isolated query bootstrap, which invokes only `sudo -V` and `sudo -n -ll`. `sudo -l`, `sudo -ll`, and `sudo -V` inspect authorization/version; the reconstruction target is never executed.
- The discovery source has no call path to bundle delivery, prerequisite receipt capture, reconstruction dispatch, ordinary-client proof, cleanup, or retry. The successor dispatch argv is derived and bound for comparison only.
- Both fixed evidence leaves must be absent before the attempt. Publication reuses the reviewed `O_CREAT|O_EXCL`, mode `0600`, canonical-line, self-hashed evidence helper. An occupied or uncertain leaf blocks before transport, and every record fixes `retryAuthorized=false`.
- SSH stdin/stdout/stderr handling reuses the reviewed bounded streaming transport. Timeout, output overflow, stdin failure, or drain failure kills the local SSH process and yields sanitized uncertainty.
- Full-query input must be one canonical JSON line with exactly `sudoVersion` and string `policy`; the version grammar is strict. The reviewed parser reports only `EXACT`, `BROAD`, or `UNSUPPORTED`. Malformed framing, unexpected return codes, nonempty stderr, or transport errors yield `UNKNOWN`.
- Terminal evidence stores only fixed schema fields and SHA-256 values for query stdout. Exact-query output, full policy text, and stderr are neither printed nor persisted. Every terminal fixes `targetExecuted=false` and `rawOutputStored=false`.

## Verification

- Read commit `ffcd60766e48e18a53abb39e54c7395bd06b6fc4` directly, recorded its parent and subject, and independently resolved the three Git blob object IDs.
- Hashed each raw blob from `git show <commit>:<path>`; all three matched the required raw SHA-256 values above. The worktree copies matched those immutable bytes before execution.
- Recomputed the canonical discovery binding and both full SSH argv hashes. The binding was `9aabf6718dea7dc914d4cfac70f3651bd626055f8af0247c582d2d09f9dae427`; the exact-query argv hash was `741ccce580096340f49ebc5b277f05f2824e1fd7afad09cede1603559845b4b7`; the full-query argv hash was `8c70410d721e0e8d89850475c01f52e3702a6eefdebc6c1738cefea0708adc2a`.
- Ran `python -B -m unittest scripts.test_vm105_reconstruction_sudo_version`: **4 tests passed**.
- Confirmed the loaded successor `_run_ssh` is byte-identical to the reviewed prerequisite transport and ran its focused streaming/overflow test: **1 test passed**.
- Ran adversarial source checks for wrong authority, command substitution, prohibited routes, occupied/absent evidence leaves, malformed schemas, secret-bearing stdout/stderr sanitization, and broad-policy classification: **PASS**.

## Limits and no-live statement

No SSH connection, `sudo` command, bundle delivery, prerequisite capture, reconstruction, ordinary-client proof, staging, cleanup, retry, VM/service mutation, OmniRoute or Hermes action, gateway/provider request, or credential access was performed. The VM105 sudo version, effective policy, remote bundle/staging state, reconstruction result, runtime behavior, provider generation, defaults, persistence, and ordinary-client behavior remain **NOT PROVEN**.

The review changed only this evidence file. It did not edit the reviewed source, test, or contract; did not touch `scripts/__pycache__`; and did not stage, commit, or push anything.
