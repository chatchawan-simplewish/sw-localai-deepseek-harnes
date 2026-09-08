# VM105 owner bridge engineering handoff

Prepared 2026-09-09 04:50 Asia/Bangkok. Project: DeepSeek Harness. Verified origin: https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git.

Authoritative worktree: `C:/Users/chatc/Projects/sw-localai-deepseek-harnes/.worktrees/vm105-authoritative-roadmap`; branch `codex/vm105-authoritative-roadmap`. Continue in this exact existing worktree, not the root checkout or a new branch. Current parent task `01a082bd-c2aa-7050-b40c-8508d207cb26` retains control until explicit transfer. Older predecessor `01a081ea-69a3-7d50-b56b-e8fe3614a98a` is already read-only and unarchived.

## Objective and authority

Continue the owner's full v1 plan unattended while the owner sleeps. Routine recommended engineering and bounded verification are preapproved. Preserve the usable pilot. Do not stop with a document-only result while concrete independent implementation remains. Owner-only authentication, readiness to lose pilot provider access during cutover, materially different scope/cost, production identity/data changes and cross-project resource reassignment still need the owner. No readiness or authentication was supplied in this task.

Every user-facing message begins with actual Asia/Bangkok YYYYMMDD HHMMSS. Follow AGENTS.md, bounded implementation plus independent review, exact-path Git staging and command-scoped identity. Do not archive any predecessor. Before85% context, publish a durable handoff, create one authorized continuation and verify transfer. Native command tools are the fallback: context-mode previously resolved an unrelated sandbox; do not reconfigure it. Read/derive large outputs in code and emit compact results; never request raw task histories.

- Total - 09/21
  - Phase 1 - 05/05
  - Phase 2 - 03/03
  - Phase 3 - 01/02
  - Phase 4 - 00/09
  - Phase 5 - 00/02

These count evidence tasks, not accepted requirements. No provider route is accepted. CRED-01 remains BLOCKED / NOT PROVEN.

## Published and reviewed implementation

Cutover checkpoint `1ce6ad25114223307d74a0fba858913d1ce4e323` was pushed and exact remote branch readback matched. Subsequent handoff publication will be a descendant; verify local HEAD and ls-remote before work.

- `scripts/Invoke-VM105CandidateCutover.py`: SHA256 `a1083a64b4c62771ae783075a523a8457de8ca9970754ecc1f524c14ddfead28`. Independent offline spec/quality accepted after two fix rounds; parent22 tests plus self-test passed. See implementation and independent review reports dated2026-09-09. Default is nonmutating, --preflight is read-only, --execute requires reviewed hash and owner-ready assertion. Flags do not create authority. Native systemd execution is NOT PROVEN; do not run it during this continuation without the separate readiness and release prerequisites.
- `scripts/native-codex-owner.mjs`: SHA256 `90bb452d25d5b6c7c7593e2cfc7c01650069d1d63f4770728bff5ef32935b14b`. Terminal SHA256 `9e9bf70f8c6e4088f66ac573ce2bf89a60971d30b4f9ea3000aface4af33b458`; test SHA256 `973f22c2e782ac2108d627ed2e843f92cc723337b3895762b1a9b47a2c1a9b23`. Independent offline review accepted after one terminal-error fix; parent16 tests passed. This is a passive Cordis plugin plus explicitly launched private terminal, Node stdlib only. No installation or real authentication occurred.
- `.gitattributes` pins LF for the seven implementation/test paths so checked source hashes survive checkout. Do not normalize frozen smoke or other evidence inputs.

## Native source proof and pending repair

One public composition read established exact base credential row `id: credentials`, `name: @deepseek-ai/dsh-credentials-local`, no config block. Base patch has no authorization literal. Receipt: `vm105-native-composition-source-2026-09-09.json`. An authorization package in the432-row graph does not prove it is mounted. Effective candidate credential-store binding remains unresolved.

Core capture v1 ran once but parent output limits truncated retention. Its partial artifact and failure remain historical. A separately reviewed V2 compressed capture then ran once at04:40:07 and succeeded. Both readers are spent. Complete receipt `vm105-native-core-source-2026-09-09.json` has SHA256 `f84e506f495c28bca8409d34d9c5e5201258f1839e83819a7bac98371e94930f`; parent reproduced full60378-byte source SHA256 `1729cdbf8ee40b17c8839e06bf96491490548559e11ef7e411271e0754e751c5` and exact saved receipt digest. No further core acquisition is needed.

Read `vm105-native-core-lifecycle-assessment-2026-09-09.md`: Cordis accepts exported apply/inject, awaits the thenable, and collects its resolved disposer. Parent independently verified the key source bodies. Remove the redundant `ctx.on('dispose', dispose)` before activation: core emits no built-in dispose event, and registration can throw when the parent is disposed during pending listen. The returned disposer is the supported mechanism. Make a bounded implementation/test change with independent review; update all affected fixture/launcher hashes only after freeze. Separate limit: current disposal does not await the server-close callback/held-directory FD closure; do not overclaim settlement. Do not add speculative abstractions.

## Linux a1 attempt: failed, retained and spent

Design: `docs/superpowers/plans/2026-09-09-vm105-native-bridge-linux-check.md`.

Fixture `scripts/test-native-codex-owner-linux.mjs` SHA256 `6f82e2f2783123255f9e441cde991da2bdcbddbf92bd9f4dc6cc7e1b12cc1414` independently accepted offline. Launcher `scripts/Test-VM105NativeBridgeLinux.py` SHA256 `3fa388c3fbdb0ed48b368c63114a16940c87312ad661147aed062ca384ff688a` accepted after rejecting setuid/setgid executable bits; parent self-test passed. Review report records both initial blocker and scoped acceptance.

One approved attempt at04:41 returned LINUX_CHECK_FAIL with SSH0 and owned_child_reaped=true. Receipt `vm105-native-bridge-linux-attempt-a1-2026-09-09.json` binds the frozen source/executable and new root `/run/dsh-native-bridge-check-20260909-a1`, inode4078, source inodes4080/4081/4082. Root/source fixtures are retained. No cleanup or retry. SSH0 is not PASS; native transport remains NOT PROVEN.

Read `vm105-native-bridge-linux-a1-diagnosis-2026-09-09.md`. The launcher discarded fixed stage and original child-exit data; the fixture also reduced failures to one generic code. This confirmed diagnostic defect prevents identifying a runtime cause from the receipt. Do not guess a functional repair from elapsed time. A separate fixed-path metadata-only diagnostic is being completed at this handoff; its final result will be appended below before transfer. If topology cannot establish the cause, add bounded fixed stage/exit instrumentation before any independently reviewed fresh-root attempt. Never reuse a1 or weaken namespace, ownership, executable pinning, privilege drop, deadlines, output sanitation or exact-child cleanup.

## Live boundaries and remaining scope

VM105: dsh@192.168.1.139. Strict SSH BatchMode/IdentitiesOnly/StrictHostKeyChecking, ConnectTimeout10, key `C:/Users/chatc/.ssh/codex-prox01-vms-ed25519`; reviewed root interpreter `/usr/bin/python3.12 -I` via sudo -n. Only parent owns VM controls; bounded agents have none.

Opaque `/home/dsh/.dsh`: no content read/copy/migration/deletion. Candidate `/home/dsh/.dsh-profiles/vm105-provider-v1` contains generated state from isolated v3 and is stopped. All prior --apply/v2/v3, source/preflight/export gates are consumed. Do not replay diagnostics without a concrete changed implementation and independently reviewed new scope. No service/profile/authentication changes occurred in this task; only reviewed public-source reads and the isolated synthetic a1 test. Last pilot runtime proof remains historical03:32; do not describe it as freshly checked.

Keep3080 loopback plus SSH tunnel, unresolved firewall rule unchanged, no broad exposure, no GPU/inference, no host/VM power operations. WSL inventory found it absent; do not install it. Browser work only after verifying exact Chrome profile Codex-Chrome-Bell-PC2; no fallback browser.

PROV-04 Bell-PC2 is now a cross-project scope conflict: separate Jellyfin task `01a08159-57cf-7202-97cf-f9941f5811ae`, title `Continue Bell-PC2 Jellyfin GPU acceptance…`, records owner-approved obsolete local-AI retirement and GPU reassignment. Read `vm105-bell-worker-scope-conflict-2026-09-09.md`. Do not revive Ollama/Caddy, reclaim GPU, change that task or silently remove the original requirement. Owner reconciliation remains pending. Do not use ollama ps as a passive probe; it previously launched a process.

## Exact continuation sequence

1. Verify final published HEAD/remote and clean authoritative worktree; receive sole ownership explicitly. Leave this predecessor unarchived/read-only.
2. Read the final metadata diagnostic appendix and a1 diagnosis. Finish the smallest evidence-driven Linux failure investigation. No spent attempt replay.
3. Remove the source-proven redundant lifecycle listener in a bounded implementation lane, adjust meaningful offline checks and independently review. Coordinate new frozen pins with any new fixture revision.
4. Establish Linux transport and selected credential-store/composed native authorization binding without authenticating or replacing the pilot. Keep source proof distinct from runtime acceptance.
5. Continue remaining safe engineering, then present concrete owner-only authentication/cutover-readiness and Bell scope decisions. Full v1 remains incomplete.

## Final diagnostic and transfer appendix

The corrected metadata reader `31a29a41d4159801bf294b2e0f9945c56399765c69f2e8d6e172d8009f345316` passed parent self-test and independent pre-review at04:50:32, then ran once with SSH0/A1_METADATA_PASS. It is now spent. Receipt `vm105-native-bridge-linux-a1-metadata-2026-09-09.json` retains fixed-path metadata only. Root/source ownership, modes and inodes match. `preexisting.sock` remains regular0600, `retained.sock` remains a0600 socket, while `replacement.fixture` and `replacement.sock` are absent.

Independent receipt assessment at04:54 confirms progress into the replacement case and failed preservation. Node/libuv retirement is the leading explanation, but exact unlink timing/mechanism remains inferred. Do not call the metadata PASS a transport PASS. The current releaseSocket conflict path merely unrefs the server; investigate native process-exit unlink semantics before choosing the smallest repair. Preserve unknown files and the same-account trust boundary; do not weaken the preservation requirement. No further live check is needed to re-establish this retained topology.

All bounded agents have completed and relinquished their lanes. Parent source review and frozen hash checks are complete. The final publication will include all current implementation, failed-attempt evidence and this handoff, with native runtime limits explicit. The parent's successful creation message for one continuation grants that successor sole worktree/VM coordination ownership; this task then becomes read-only and remains unarchived. The successor must verify exact published HEAD/remote and record transfer before further implementation. No worker receives live control implicitly.
