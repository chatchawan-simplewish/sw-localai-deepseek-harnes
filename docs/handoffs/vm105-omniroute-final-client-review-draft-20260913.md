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

Endpoint/key identity and credential delivery are **UNBOUND** pending accepted OmniRoute qualification/rollout. The final design may use only a coordinator-owned ephemeral channel whose values never enter an environment variable, file, command line, logs, receipts or DSH credential store. It must prove observable channel closure and non-persistence: closed descriptors, disabled core dumps, and secret-free retained root/store/logs/environment/command line. If the qualified DSH client contract cannot accept such a channel without persistent credential state, this lane fails closed; no adapter, profile patch or key-copy workaround is authorized.

## Single-call and rollback contract

After qualified endpoint/credential binding and independent review, the consumer may make exactly one outbound request to the accepted OmniRoute agent-routing interface. The containment method must deny all other egress, including DNS discovery, redirects, retries and preflight requests; the receipt must record one attempted connection to the bound endpoint. It may not call a provider directly, start a service, bind port 3080, use the native bridge, or alter the pilot. A deadline and containment that either owns a PID namespace/cgroup or prevents `setsid`/double-fork escape are mandatory. Rollback means terminate and reap every contained descendant, close only its own descriptors, retain the root and receipts, and stop. No recursive cleanup, provider revocation, credential deletion, pilot rollback or service action is in scope.

The receipt must bind graph/executable pins, endpoint public identity, request/result schema, automatic-switch decision and attribution fields, child cleanup, containment verdict and no-pilot-change readback. It must contain no credential, request prompt, provider value or raw endpoint secret. A result proves only the qualified OmniRoute interface accepted that one client call. It does not prove provider health, normal-service composition, CRED-01, native OAuth, bridge correctness, or full VM105 route acceptance.

## Mandatory release prerequisites

1. Provider qualification and OmniRoute rollout are accepted by the coordinator.
2. Independent Sol High review accepts the fully bound graph, containment, endpoint/credential channel, receipt and rollback contract.
3. Coordinator accepts that review and explicitly names this exact root and one-call contract.
4. VM105 parent verifies current pilot/bridge/spent-gate state immediately before any release.

Until all four hold, this draft grants no live authority. Pilot `/home/dsh/.dsh`, stopped candidate/profile paths, `/opt` ownership, systemd, tunnel/reconnect task, firewall, bridge/a2, credentials/OAuth, providers, GPU, inference, Bell-PC2, host/VM power and all earlier gates remain excluded.

## Independent review

Independent Sol High review rejected the first draft for graph-scope ambiguity, unobservable Node-memory zeroization, descendant escape and unenforceable one-call behavior. The revised conditions above were accepted at 20260913 001913 Asia/Bangkok with no remaining concrete issues. This acceptance evaluates the draft's boundaries only; it does not bind any currently unbound value or release execution.
