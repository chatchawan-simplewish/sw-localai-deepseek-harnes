# DRAFT: VM105 final OmniRoute DSH client lane

20260913 000928 Asia/Bangkok. Draft only for OmniRoute coordinator task `01a09361-8143-73d3-adb7-15043355276b`. This is not a transfer, execution release, provider qualification, or authority to create any VM resource.

## Proposed isolated resource

The only proposed future consumer root is `/var/tmp/omniroute-dsh-client-final-20260913`. Its absence has not been checked and it must remain uncreated until the final packet is independently approved. If released, creation must be atomic and exclusive, with nofollow descriptor checks of the exact child; an existing object, link, alternate path, retry, or cleanup attempt fails closed.

The earlier `/var/tmp/omniroute-dsh-client-20260912` transfer remains synthetic-only. It is not broadened by this draft.

## Frozen graph requirement

The final packet must contain a copied-module manifest with one SHA256 over UTF-8 canonical JSON: entries sorted by `stagedRelativePath`, object keys ordered as `{sourceLogicalPath, sourceCanonicalPath, stagedRelativePath, sha256}`, no insignificant whitespace. Every entry must be read only through held nofollow descriptors under `/opt/deepseek-harness/node_modules`, rehashed before and after staging, and written only inside the proposed root. The manifest must include the complete copied JavaScript/module closure, not just the 28-package/56-file source receipt. `COPIED_MODULE_MANIFEST_SHA256` is **UNBOUND** in this draft.

Existing anchors are source-only: `@deepseek-ai/dsh` and `@deepseek-ai/dsh-client-ui-settings-models` version `0.1.1-rc.2`, with `lib/client.js` SHA256 `c3b9a2d2d074c600c10553a4b15e294082f5851dd4a834d06ddb268b310d18de`. No installed JavaScript execution has been evidenced. The final packet must separately bind `NODE_BINARY_SHA256`, executable/loader/runtime dependency pins, and `COPIED_MODULE_MANIFEST_SHA256` before review; it must not claim parity from the source receipt alone.

## No-write and credential boundary

The reviewed launcher must make the consumer unable to write outside its new root. `HOME`, `DSH_HOME`, temporary paths and working directory must point inside the root, but environment redirection alone is insufficient: the packet must name an independently reviewed OS-level containment method that prevents writes to `/home/dsh`, all profiles, `/opt`, `/etc`, systemd state and network/firewall configuration. `CONTAINMENT_METHOD` is **UNBOUND**.

Endpoint/key identity and credential delivery are **UNBOUND** pending accepted OmniRoute qualification/rollout. The accepted compatibility trace `C:/ChatGPT Projects/SW-Selfhosted-Network/.worktrees/omniroute-auto-switch-20260912/docs/auto-switch-vm105-final-client-compatibility-20260913.md` SHA256 `9ad832f89e579504a806698614b78701162115b5bbf5929caad91a5e03093995` establishes a candidate existing path: a coordinator-owned anonymous pipe carries one version-1 credential document, its write end closes before the contained DSH child starts, and only the read descriptor is inherited. A non-secret patch may point the existing credentials row to `/proc/self/fd/<inherited-pipe>` with `watch: false`, and reference the accepted endpoint through the existing credential name.

The final packet must bind the descriptor inheritance, document schema/version and `watch: false` behavior without recording any secret. Values may not enter an environment variable, ordinary file, command line, logs, receipts or DSH credential store. It must prove observable channel closure and non-persistence: closed descriptors after initial read, disabled core dumps, and secret-free retained root/store/logs/environment/command line. An accepted-package Linux descriptor fixture remains mandatory before release. If the qualified DSH client contract cannot use this channel without persistent credential state, this lane fails closed; no adapter, profile patch or key-copy workaround is authorized.

## Single-call and rollback contract

After qualified endpoint/credential binding and independent review, the consumer may make exactly two correlated native requests to the accepted OmniRoute agent-routing interface: one primary `/v1/chat/completions` submission and one mandatory same-tuple `/v1/agent-routes/events` `output_started` acknowledgement. The acknowledgement must return HTTP 202 with `{accepted:true}` before local output release. The receipt must prove identical durable task/run/turn/idempotency tuple fields, `progressCommitted:true` and no `resumeRequired` state.

The containment method must deny all other egress, including DNS discovery, redirects, retries, preflight/catalog requests and direct-provider traffic. Model-facing tool rows must be disabled, so neither tool events nor a second generation step can occur. The adapter must bind `maxRetries: 0`; a failed request transitions to explicit resume state rather than client recovery. The receipt must count and classify both HTTP requests; connection count is insufficient. The consumer may not start a service, bind port 3080, use the native bridge, or alter the pilot. A deadline and containment that either owns a PID namespace/cgroup or prevents `setsid`/double-fork escape are mandatory. Rollback means terminate and reap every contained descendant, close only its own descriptors, retain the root and receipts, and stop. No recursive cleanup, provider revocation, credential deletion, pilot rollback or service action is in scope.

The receipt must bind graph/executable pins, endpoint public identity, request/result schema, automatic-switch decision and attribution fields, child cleanup, containment verdict and no-pilot-change readback. It must contain no credential, request prompt, provider value or raw endpoint secret. A result proves only the qualified OmniRoute interface accepted that one client call. It does not prove provider health, normal-service composition, CRED-01, native OAuth, bridge correctness, or full VM105 route acceptance.

## Mandatory release prerequisites

1. Provider qualification and OmniRoute rollout are accepted by the coordinator.
2. Independent Sol High review accepts the fully bound graph, containment, endpoint/credential channel, receipt and rollback contract.
3. Coordinator accepts that review and explicitly names this exact root and two-request contract.
4. VM105 parent verifies current pilot/bridge/spent-gate state immediately before any release.

Until all four hold, this draft grants no live authority. Pilot `/home/dsh/.dsh`, stopped candidate/profile paths, `/opt` ownership, systemd, tunnel/reconnect task, firewall, bridge/a2, credentials/OAuth, providers, GPU, inference, Bell-PC2, host/VM power and all earlier gates remain excluded.

## Native descriptor fixture evidence

External artifact `C:/ChatGPT Projects/SW-Selfhosted-Network/.worktrees/omniroute-auto-switch-20260912/docs/auto-switch-dsh-container-fixture-result-20260913.md` has SHA256 `7d484038930e3f20ad8bbf337f32a05f8748bfc0fecff7f8a51c9fa2bc0ae22d`, independently hash-checked when this record was updated. It reports a PASS in fresh network-none builder147 container under pinned Node v24.19.0 and a retained compiled V7 package graph: dummy version-1 descriptor credential resolved and disposed through compiled credentials-local with `watch:false`; FD closed, scratch empty, retained entries unchanged, and container removed.

This satisfies the draft's native-interface fixture prerequisite only. It does not bind or prove VM105 copied-graph equality, OS containment, endpoint/key identity, provider qualification, live two-request acceptance, or any execution authority.

## Independent review

Independent Sol High review rejected the first draft for graph-scope ambiguity, unobservable Node-memory zeroization, descendant escape and unenforceable one-call behavior. The revised conditions above were accepted at 20260913 001913 Asia/Bangkok with no remaining concrete issues. This acceptance evaluates the draft's boundaries only; it does not bind any currently unbound value or release execution.

The 20260913 004104 compatibility amendment replaces the incompatible one-request rule with the exact primary chat submission plus same-tuple `output_started` acknowledgement. Independent Sol High review accepted that narrow amendment at 20260913 004314 Asia/Bangkok. It does not bind the endpoint/key, copied graph, containment method or release authority.
