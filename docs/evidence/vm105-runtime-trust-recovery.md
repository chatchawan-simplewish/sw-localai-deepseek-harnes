# VM105 runtime ownership recovery — 2026-09-08

Repository: https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git

Scope: new recovery following the owner's instruction to continue the full plan. Historical accepted BLOCKED selector evidence is preserved. Current pilot profile stays opaque; this recovery does not earn a provider milestone. Full roadmap remains 09/21.

## Read-only proof

At 22:23–22:25 Asia/Bangkok, strict host-key SSH to `dsh@192.168.1.139` observed:

- `/` and `/opt`: uid/gid 0:0, mode 0755, non-link directories.
- `/opt/node-v24.19.0-linux-x64`, its `bin` directory and `bin/node`: uid/gid 1000:1000, mode 0755, non-links. Node is regular with one hard link.
- All five paths: no POSIX access/default ACL or file capability xattrs. These are metadata observations, not a proof against a malicious administrator.
- Installed Node SHA-256 from an open no-follow file descriptor: `bc17c508ffeed0ec622934f9b7fa72f8e78da65350e63c3eceb56fa688aa5e12`. Device/inode/size/mtime remained stable across hashing.
- Controller fetched `https://nodejs.org/download/release/v24.19.0/SHASUMS256.txt` and the matching `node-v24.19.0-linux-x64.tar.xz` over verified HTTPS. Archive SHA-256 matched `14b342e71204f811bde6153be8e04b62aef63c236fef92b55f9c83154b409647`; exact member `node-v24.19.0-linux-x64/bin/node` matched the installed binary digest. Archive and member were processed in memory, without installation or VM download. This verifies equality with the HTTPS-published release, not a detached signature or the whole installed package.
- `/usr/bin/python3` resolves to root-owned regular `/usr/bin/python3.12`, mode 0755; `/usr` and `/usr/bin` are root-owned 0755 directories. Exact interpreter will be used for the repair.
- Node's containing mount: `/dev/sda1` on `/`, ext4, `rw,relatime,discard,errors=remount-ro,commit=30`.
- Service baseline: `deepseek-harness.service` active/running, MainPID 829, start `2026-09-08 14:41:13 UTC`, NRestarts 0. VM loopback HTTP 200.

Independent review found that the existing contract requires root-owned safe interpreter metadata. It does not establish isolation against `dsh`, which retains unrestricted sudo, or revoke pre-existing writable descriptors. Those limitations remain; no sudo or service change is proposed.

## Other full-plan prerequisites refreshed

From VM105 at `2026-09-08T15:24:23Z`, bounded requests with suppressed bodies found VM1201 `192.168.1.143:8000/health` returned no HTTP response within five seconds, and OmniRoute `192.168.1.68:20128/v1/models` returned HTTP 401. No credentials or inference were used. Backend availability remains unresolved.

The upstream master [provider guide](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/user/guide/providers.md#add-a-built-in-provider) states Codex OAuth is not supported on the Models page. Backend authorization code alone is not proof of a usable login surface in installed VM105 release 0.1.1-rc.2. Native OAuth remains NOT PROVEN.

## Execution

The owner's routine preapproval permits this independently reviewed reversible repair. Service/profile cutover remains a separate material action.

At 22:29–22:30 Asia/Bangkok, helper `scripts/repair-vm105-node-ownership.py`, SHA-256 `24A97FC1917F57B93337CFB3A998AE2C0D040A8137DFB20D508B7E9B31836AF7`, passed its unprivileged Linux temporary-tree self-test and read-only live preflight. Independent reviewer `/root/runtime_recovery_review` conditionally accepted it, with the required clarification that automatic rollback covers helper failures; later external health failures require review after descriptors close. That clarification was applied before execution.

A single `sudo -n /usr/bin/python3.12 - --apply` invocation returned `APPLIED`. Exact three target inodes on device 2049 were 262257, 293971, and 293972. Each changed from 1000:1000 to 0:0 with mode 0755 unchanged. The Node digest still matched the official release. No fallback or rollback was needed.

Parent independently checked all three path identities and ownership after execution. Service PID 829, start time, active/running state and NRestarts 0 remained unchanged. Both VM loopback and Bell-PC2 tunneled HTTP returned 200. No service restart, profile access, credential or network mutation occurred.

Result: ownership prerequisite repaired. This does not prove profile-selector semantics, whole-installation integrity, native OAuth or any new provider milestone. Historical selector evidence remains accepted BLOCKED at digest `ADB1FD7758B30059D83D4DD7A3E47FD232AE7551F0E36D63F35DD44AF604076F`.

Independent postexecution review accepted the recovery against the exact helper digest and before/after evidence.

## Discovery follow-up

The extracted reviewed Step 6 runner `scripts/Invoke-VM105SelectorDiscovery.ps1` passed its local checks under PowerShell 7. Windows PowerShell 5.1 is unsupported by the runner's process API. Independent review accepted the bounded read-only discovery.

One discovery at `2026-09-08T15:31:40.8722450+00:00` returned `BLOCKED installed symlink path`, with local checks PASS and selector NOT PROVEN. Metadata-only diagnosis established the root-owned regular wrapper's fixed entrypoint as `/opt/deepseek-harness/node_modules/@deepseek-ai/dsh/lib/bin.js`. The `dsh` package entry is a root-owned symlink; the entrypoint is root-owned mode 0755 with two hard links. Its canonical target is `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh@0.1.1-rc.2_7adf779e9bedfb2e97ced92905792931/node_modules/@deepseek-ai/dsh/lib/bin.js`.

This is a pnpm-layout incompatibility with the existing strict no-link discovery contract, not evidence of a broken pilot. The stopped old-contract run read no source through that symlink and modified no package or wrapper.

Independent review subsequently accepted the explicit pnpm-aware scope and inspector SHA-256 `4C88FB119398014989C09469AD340B7DD749A60459F3BDA6929F14C8231EE8E6`. The parent ran its unprivileged self-test successfully before source reads. Canonical ancestor/file checks, root ownership, explicit link count two, before/after digest checks and logical-link stability all passed. This is a new reviewed scope, not PASS under the unchanged old contract.

Verified installed-source chain (all in the same canonical package):

| File | SHA-256 | Relevant proof |
| --- | --- | --- |
| `package.json` | `dc930c0b18158f49ae3753ceaf6b1b7ae71dc6c8f45c85a2d679b142024addf7` | `@deepseek-ai/dsh` version `0.1.1-rc.2`; declared dependencies |
| `lib/bin.js` | `c0226687bb20f45c603ec6fe50f3de16d1c3510c3a803304ec575ef9bc366c62` | `--profile` selects a name under `$DSH_HOME/profiles`; imports the next file |
| `lib/profile-boot-BnJoK_kl.js` | `778c5b338674d986a49972be920c965d28b2c8cac85364ae77f8587070397663` | Re-exports the next boot implementation |
| `lib/profile-boot-DG5t9aNs.js` | `f83ffea6a4d30cfbe02b41dabcc05104c4ad27bf79c74f601f0ddb6ccdf88969` | Applies home-level patches; imports `resolveDshHome` and profile-loading helpers |

`--profile` alone is insufficient for whole-home isolation. The home-path and boot dependency semantics still need proof; no candidate, cutover or profile read is authorized by these partial findings.

The reviewed inspector was extended to the two exact imported dependencies and their observed canonical targets; final SHA-256 `6327E76549025A347381AF228607A3F157C27B4E8F4E37195AEBB4186F4080B6` passed independent review and its unprivileged self-test. An earlier guessed peer-directory pattern rejected the home-path dependency before reading content; literal targets replaced that pattern, without wildcard discovery.

- `dsh-home-paths/lib/index.js`, SHA-256 `b82aa631aa4bfdd5b02c67d48fce455b2ca73cbf66d2b7096a336b3800914340`, lines 63–84: configured override takes precedence over `DSH_HOME`, then the default; absolute normalization and the shared `dshHomePath` helper are implemented. The comment describes one user-data root; actual store consumers still require tracing.
- `dsh-app-boot/lib/index.js`, SHA-256 `9d4b7f214cd35b3e8ce4e027b12cca34a416d355577aeacbf08a5b324f0cabb6`: fresh profile initialization at lines 353–369, installation code fallback under the selected home at 409 onward, selected-profile loading at 539 onward, and invoking-directory plus selected-home `.env` loading at 726–750.
- Sanitized service metadata: `DSH_HOME=/home/dsh/.dsh`, `HOME=/home/dsh`, working directory `/srv/dsh/workspaces`, user/group `dsh`, no drop-ins. Unit environment names are only `DSH_HOME`, `HOME`, `PATH`; `PassEnvironment` and `EnvironmentFiles` are empty. No other environment values were output. Metadata-only check found no `/srv/dsh/workspaces/.env`.
- At 22:49 Asia/Bangkok, metadata-only checks found both the planned parent `/home/dsh/.dsh-profiles` and candidate `/home/dsh/.dsh-profiles/vm105-provider-v1` absent. Neither was created.

Selector remains NOT PROVEN pending concrete credential/settings/session and other mutable-store consumer checks. No old profile contents, stored credentials or session data were read.

## Backend path clarification

Further read-only checks supersede the inference that the backend itself might be offline. At 15:36:53–15:37:21 UTC, strict SSH identified VM1201 as `prox01-local-ai`; its `local-ai.service` is a successful enabled oneshot with `RemainAfterExit=yes`, no restarts, a listener on `192.168.1.143:8000` and local health HTTP 200. VM105's direct check still timed out. UFW lists VM1205 `.68` among the allowed sources for port 8000, with no VM105 `.139` entry; this supports a direct-path permission gap without proving where packets dropped.

At `2026-09-08T15:38:42Z`, VM1205-to-VM1201 health returned HTTP 200. The intended host-to-host OmniRoute path is available; container routing and inference remain NOT PROVEN. No model start, VM power action, firewall mutation, credential read or inference was performed. No direct VM105 firewall change is justified by this evidence.

## Final preparation outcome

Subsequent bounded store and provider-source tracing is recorded in `vm105-selector-store-trace.md`, SHA-256 `A7AB0F1D371C7283A6B5E8441B05C4312B6FFF86F2B7E2FDDD154CED0A863AE2`. Independent review accepted a new conditional preparation contract, not bare `DSH_HOME` isolation or PASS under the historical no-link record. Intentional read-only project/OS skill inputs are outside mutable-profile migration; an ineffective host skill-provider restriction was not included in the candidate.

At approximately 23:07 Asia/Bangkok, one reviewed exclusive-create attempt prepared `/home/dsh/.dsh-profiles/vm105-provider-v1`. The exact four native files and their hashes, owner-only modes, zero credential/environment files, separate parent verification and accepted independent post-creation review are recorded in `vm105-provider-candidate.json`. The six native overrides relocate spill output, disable telemetry, disable the default model and both DeepSeek request paths, and leave the pi-ai registry with an empty provider map.

The temporary-tree test initially failed because its fixture inherited group-write permission; production checks correctly refused it. Explicit safe fixture modes fixed the test without weakening production checks. Final helper self-test passed before live creation.

Later installed API source revealed a mandatory `agentDefaultModel` dependency. The initial six-row candidate would therefore prevent the Web API from mounting. Independent review explicitly superseded the earlier no-selection recommendation: keep the inactive native selection while requiring zero active adapters and no usable inference route. One separately reviewed descriptor-only correction removed that disabling row from the unused candidate. Self-test, live preflight, application and separate parent four-file verification passed; the current five-row patch hash is `7c4b50b071a07a705b817a689fb02b6e1b616aae159fa47572828bcefece99cb`. All other candidate bytes remained unchanged. The receipt records both original and corrected hashes; the earlier source trace is historical where its six-row recommendation conflicts with this correction.

After creation, service PID 829/start time/NRestarts 0 were unchanged and both VM105 and Bell-PC2 HTTP checks returned 200. Candidate static preparation is accepted; the service still uses the pilot. Runtime candidate readiness, the service cutover, fresh credentials and all full-plan route acceptance remain pending. Full roadmap remains 09/21.
