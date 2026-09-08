# Native bridge repair and remaining transport decision

DeepSeek Harness: https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git. Authoritative worktree and ownership are recorded in `vm105-continuation-ownership-2026-09-09.md`.

## Implemented bounded correction

Removed the redundant `ctx.on('dispose', dispose)` registration. Retained Cordis source already proves that it collects the disposer returned by async apply; an inactive context can reject the redundant event registration during pending listen. The new regression drives actual apply through pending listen, makes event registration fail, then verifies returned disposal removes the owned synthetic socket and closes once. Native filesystem/server operations are mocked on Windows; this does not prove Linux transport or actual Cordis activation.

Worker observed a meaningful RED (`OWNER_BRIDGE_UNAVAILABLE`) after correcting two test-harness setup errors, then GREEN. Parent independently ran all 17 Node tests with zero failures. Implementation SHA256: `52e8c18d1b10c9c02eec27cbe8bce8ea60b7de1e5c78e29b137c1e13a4cd6fcb`; test SHA256: `a3931b34cebc4cc6d949687458ffb8cbf6a7ab12b84f8c02e7ae16b0de3e641f`.

Independent reviewer `/root/independent_bridge_review` accepted the bounded diff at 20260909 050607 with no new P1/P2 findings. It verified both hashes, passed all 17 tests on Windows Node v24.19.0, and restored the removed listener in memory: exactly the new regression failed, with 16 other tests passing. It also checked the retained Cordis collection/unload source. Asynchronous close settlement, actual Cordis runtime activation and Linux transport remain unproven.

## Replacement preservation remains blocked

The a1 root and diagnostic are spent and retained. No new VM operation occurred. The lifecycle correction does not repair replacement preservation and does not justify another Linux attempt.

Initial source inspection corroborated why unref is insufficient using related Node releases. Independent review then fetched exact official [libuv pipe.c bundled in Node v24.19.0](https://raw.githubusercontent.com/nodejs/node/v24.19.0/deps/uv/src/unix/pipe.c): initialization clears pipe_fname, pathname bind assigns it, and close unlinks that pathname. This strengthens version-specific source corroboration, but does not identify the precise a1 unlink timing or prove execution by the VM's pinned binary.

Closing the held directory descriptor before calling server.close is rejected: another native thread can reuse its descriptor number, redirecting the proc-fd pathname. No unsafe retirement shortcut or preservation-test relaxation was implemented. The current module must remain unactivated.

## Concrete proposed scope for owner decision

Recommended direction: one Python standard-library supervisor owns the listening Unix socket, passes its descriptor to Node, and retains responsibility for identity-checked cleanup. The bridge accepts the inherited listener through Node's public fd interface. The owner-facing private terminal protocol, device-only flow, account-private permissions and no-authentication-until-owner-ready gate remain required.

[Node pipe_wrap.cc v24.19.0](https://raw.githubusercontent.com/nodejs/node/v24.19.0/src/pipe_wrap.cc) calls uv_pipe_open. The matching libuv implementation opens an inherited descriptor without assigning pipe_fname. Independent review accepted this as a credible architecture candidate to avoid Node's automatic pathname unlink, subject to exact descriptor ownership, supervision, cleanup review and fresh synthetic proof.

This changes process launch, descriptor validation and lifecycle ownership. It requires an explicit architecture decision under AGENTS.md before implementation; it has not been built or released. It adds one small local process and no proposed paid service or dependency. Costs are additional lifecycle tests and integration work. Risks are descriptor misuse, parent/child shutdown behavior and cleanup races; the design must preserve the existing same-account trust boundary and exact owned-child controls.

Alternative: keep native authentication blocked and preserve the pilot. This has no new implementation cost but leaves the three native Codex routes incomplete. Systemd socket activation is another possible mechanism, but introduces unit lifecycle and pathname-removal behavior for a temporary owner flow; it is not the current recommendation. A native addon is unnecessary if inherited descriptors satisfy the reviewed requirements.

Before any future execution: independently review exact supervisor/bridge/fixture scope, freeze executable and source pins, choose a genuinely new exclusive root, enforce existing isolated-network and unprivileged-child rules, then permit only the reviewed attempt. a2 telemetry preparation alone is not a release. All current/candidate homes, pilot service, firewall, GPU and power boundaries remain untouched. Full v1 and CRED-01 remain incomplete; evidence counts stay 09/21.
