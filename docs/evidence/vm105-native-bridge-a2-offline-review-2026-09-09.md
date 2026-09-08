# Linux bridge a2 telemetry preparation

20260909 050756 Asia/Bangkok. DeepSeek Harness: https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git. Offline preparation only; no VM operation or new runtime attempt.

The a1 failure discarded stage and original child-exit information. The revised launcher retains fixed allowlisted stages and bounded waitid exit kind/value before its cleanup kill. It validates the complete receipt schema, fixed source artifacts and success prerequisites. The Linux fixture emits fixed failure stages, forwards only recognized replacement-child failure stages, and uses the returned disposer. Existing replacement identity, contents, mode and post-exit preservation assertions remain intact.

The proposed root is `/run/dsh-native-bridge-check-20260909-a2`, but `RELEASED=False` rejects both CLI execution and the remote body. This root has not been created by this task. Updating the release flag changes the frozen launcher and requires new review; a hash argument never supplies authority. The unresolved preservation defect is a release blocker. a1 and its metadata diagnostic remain spent and untouched.

## Frozen files

| File | SHA256 |
| --- | --- |
| scripts/Test-VM105NativeBridgeLinux.py | f8c3e178355c93a7216980a7323f17fbf55fbde11b03a7d899a4da161dcf5b85 |
| scripts/test-native-codex-owner-linux.mjs | 8a001554022b7d7eb20711ae12b5c6ec770c380c146d9d2247699ecb9e769405 |
| scripts/native-codex-owner.mjs | 52e8c18d1b10c9c02eec27cbe8bce8ea60b7de1e5c78e29b137c1e13a4cd6fcb |
| scripts/native-codex-terminal.mjs | 9e9bf70f8c6e4088f66ac573ce2bf89a60971d30b4f9ea3000aface4af33b458 |

## Verification and independent review

Parent ran `python scripts/Test-VM105NativeBridgeLinux.py --self-test` and `node scripts/test-native-codex-owner-linux.mjs --self-test`; both returned SELF_TEST_PASS. Parent independently compared every source pin with current bytes and asserted RELEASED is false. Scoped whitespace verification passed.

Independent reviewer `/root/independent_telemetry_review` accepted both files at 20260909 050744 with no actionable severity findings. It verified hashes before and after review, both self-tests, fixture syntax, 46 additional receipt/failure cases, source/inspector pins and whitespace. It confirmed isolation and unreaped PID/PGID ownership remain intact through cleanup, and original exit capture occurs before the cleanup SIGKILL. Review was read-only and offline.

These checks establish diagnostic-code behavior and review acceptance only. They do not prove Linux setup, child execution, transport, actual disposer settlement, replacement preservation, effective credential storage, native login or any provider route. Evidence progress remains 09/21. The current owner module is unactivated.
