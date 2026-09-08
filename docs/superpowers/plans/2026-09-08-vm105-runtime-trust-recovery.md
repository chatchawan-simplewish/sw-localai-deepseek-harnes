# VM105 runtime ownership recovery

Read-only source-inspection clarification (22:51 Asia/Bangkok): independent review permits positive, stable hard-link counts rather than assuming every pnpm source has exactly two links. Every alias shares the inode's root ownership and non-writable permissions; descriptor/path identity and repeated digest verification remain mandatory. Record actual counts, accept 1/2/3 in the self-check and reject zero. This applies only to source reading and does not authorize modifying shared source inodes. The Node ownership repair retains its original single-link requirement.

Status: bounded repair plan for independent review; this document records no live change.

Project: DeepSeek Harness. Repository: `https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git`. Worktree: `C:\Users\chatc\Projects\sw-localai-deepseek-harnes\.worktrees\vm105-authoritative-roadmap`, branch `codex/vm105-authoritative-roadmap`.

## Scope and authority

The owner's full-plan resumption and project routine-repair preapproval authorize this bounded reviewed repair. The reversible-profile design permits normalization after a reviewed repair packet. The original scoped recovery requires safe root:root regular non-link interpreter metadata; it does not require proving isolation against unrestricted sudo, auditing every ELF dependency, or excluding existing writable descriptors. Do not introduce those as new acceptance gates.

Change ownership of exactly these three existing objects, preserving mode 0755:

| Object | Before uid:gid | After uid:gid |
| --- | --- | --- |
| `/opt/node-v24.19.0-linux-x64` | 1000:1000 | 0:0 |
| `/opt/node-v24.19.0-linux-x64/bin` | 1000:1000 | 0:0 |
| `/opt/node-v24.19.0-linux-x64/bin/node` | 1000:1000 | 0:0 |

No recursive chown, installation/replacement, restart, service/systemd/network change, credentials, inference, profile access/mutation, pointer cutover, or power action. Preserve dirty work and the accepted historical BLOCKED evidence. No new user approval is required for this routine reviewed repair or its bounded read-only discovery follow-up.

## Proof available for the repair packet

Parent verified the official archive over HTTPS from `https://nodejs.org/download/release/v24.19.0/`, checked its release checksum, and inspected the exact archive member in memory without scratch extraction or VM installation:

- `node-v24.19.0-linux-x64.tar.xz` SHA-256: `14b342e71204f811bde6153be8e04b62aef63c236fef92b55f9c83154b409647`.
- Exact `bin/node` member SHA-256: `bc17c508ffeed0ec622934f9b7fa72f8e78da65350e63c3eceb56fa688aa5e12`; matches the live file's descriptor-based digest.
- `/`, `/opt`, and the three target objects are non-links, mode 0755, with no ACL or capability attributes. `/` and `/opt` are 0:0; the three targets are 1000:1000. Node is a regular file with link count one.

Record those observations in the execution evidence and revalidate against held descriptors immediately before mutation. The byte match proves the Node binary matches the release; it makes no claim about the entire installation. dsh retains unrestricted sudo, and ownership changes do not revoke pre-existing writable descriptors. These are disclosed limits, not an assertion of adversarial isolation or extra strict-plan prerequisites.

## Execution and verification

- [ ] Independently review the exact bounded helper and this packet before execution. Use existing strict-host-key SSH to VM105; do not expose key contents or remote environment/logs.
- [ ] Record repository identity, HEAD, dirty baseline, old accepted evidence digest, VM identity, and sanitized service PID/start-time and loopback health baseline. Preserve the running pilot.
- [ ] Through a trusted privileged helper, traverse from `/` using no-follow descriptors. Pin all five objects; compare lstat/fstat device/inode identities, expected types, uid/gid, mode, ACL/capability absence, and Node link count/digest. Abort without mutation on any drift or unsupported check.
- [ ] Retain the verified descriptors. Apply descriptor-based ownership 0:0 top-down to exactly the three targets, once. Do not use a hash-then-path chown, retry, fallback, or broaden the path set.
- [ ] Verify final owner/group, unchanged mode, descriptor/path identities, ACL/capability absence, Node digest and link count. Recheck service PID/start time and loopback health without restarting it.
- [ ] If a change or helper metadata/hash postcheck fails, restore original 1000:1000 ownership in reverse order only for changed objects through their held descriptors, then verify restoration. Never roll back by reopening a replaced path. Record rollback failure as an incident and stop without speculative repair. Rollback deliberately restores the prior weaker ownership. Descriptors close when the helper returns; a subsequent external service PID/health regression stops as an incident for bounded review, without automatic path-based rollback or restart.
- [ ] Parent checks direct evidence and obtains independent acceptance. Write a new recovery evidence artifact preserving the earlier consumed recovery's accepted BLOCKED result as history. No completion claim before verified outcome.

## Resume the existing plan

After accepted repair PASS, continue the existing fixed-wrapper read-only discovery under the full-plan resumption. Start only at `/usr/local/bin/dsh`; retain the existing exact installed-root grammar, package/version checks, root-owned regular non-link source requirements, opaque-profile boundary, and full-profile/non-merge selector proof. Record new evidence rather than rewriting historical outcome. No new approval is needed merely to perform this bounded read-only follow-up.

Selector discovery still requires independently accepted digest-bound PASS before candidate creation. Candidate preparation and later cutover/credential actions retain their actual existing requirements. Ownership repair does not prove selector semantics or complete roadmap milestones by itself.

Impact: no intended downtime or provider spend; root ownership can prevent future unprivileged updater writes to the two directories. Reversibility is limited to restoring the exact recorded ownership. This planning task ends with the reviewed packet; execution belongs to the parent live-resource lane.

## Bounded pnpm source inspection

The installed logical package `/opt/deepseek-harness/node_modules/@deepseek-ai/dsh` is a pnpm symlink. Permit this explicit layout exception only when its root-owned link resolves exactly to `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh@0.1.1-rc.2_7adf779e9bedfb2e97ced92905792931/node_modules/@deepseek-ai/dsh`. The read-only `scripts/inspect-vm105-pnpm-package.py` traverses logical parents and canonical ancestors with held no-follow directory descriptors; all must be root-owned and not group/world writable, with no ACL/capability attributes. Source files must be regular root-owned non-writable files with the observed link count exactly two. This accepts read-only pnpm hard links; it authorizes no alias or ownership mutation.

Initially read only `package.json` and `lib/bin.js`, each at most 1 MiB. Require package name `@deepseek-ai/dsh` and version `0.1.1-rc.2`, stable descriptor/path metadata, stable repeated file digests and an unchanged logical symlink. Report source excerpts capped at 12,000 characters total. `--start-line` selects a later excerpt; `--relative-path` may follow an exact source import within this same canonical package only, with traversal and symlink directories rejected. No directory inventory, profile access, service changes or network changes are part of this helper. Independent review precedes execution; source inspection does not itself establish whole-profile selector PASS.

The observed profile boot imports additionally permit exactly `--dependency dsh-home-paths` and `--dependency dsh-app-boot`. Each must be declared by the original dsh manifest as `^0.1.1-rc.2`. Inspect its exact sibling symlink under the original canonical package's `node_modules/@deepseek-ai`; accept only these two observed canonical targets (no peer-suffix wildcard):

- `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-home-paths@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai+dsh-invar_260f8dde1d5adbe84fd51b779f4f83da/node_modules/@deepseek-ai/dsh-home-paths`
- `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-app-boot@0.1.1-rc.2_d7ed335ddbfb7670edc51bd2c8928580/node_modules/@deepseek-ai/dsh-app-boot`

Retain all ownership, no-follow ancestor, hard-link-count, metadata and digest checks. Read only its verified manifest and manifest-declared root export (Node/import/default conditions) or an explicitly named relative source imported from that selected package. This extends source evidence to those two packages only; it is not dependency inventory or credential access.
