# VM105 OmniRoute final-client review packet

Prepared 2026-09-13. This packet is non-executing and does not transfer the final-client root, gateway, credential, service, profile, provider, model, firewall, or default-routing authority.

## Accepted anchors

- The one-shot systemd containment smoke passed with five assertions and unchanged `deepseek-harness.service`; receipt `docs/evidence/vm105-omniroute-containment-smoke-20260913.json` SHA256 `a5bdc12c4f2833671ba1c869578523b37e034d0826c06acd87620e9c42985920` at commit `4317d60b164517e267e35eb4648012ece7133c86`.
- Compatibility evidence `auto-switch-vm105-final-client-compatibility-20260913.md` SHA256 `9ad832f89e579504a806698614b78701162115b5bbf5929caad91a5e03093995` binds the native credential-pipe shape and two-request lifecycle.
- The accepted compiled-package pipe fixture SHA256 is `7d484038930e3f20ad8bbf337f32a05f8748bfc0fecff7f8a51c9fa2bc0ae22d`.
- Installed identity anchors remain `@deepseek-ai/dsh@0.1.1-rc.2` and `@deepseek-ai/dsh-client-ui-settings-models/lib/client.js` SHA256 `c3b9a2d2d074c600c10553a4b15e294082f5851dd4a834d06ddb268b310d18de`.

## Installed copied-module closure

The final 2026-09-13 strict read-only capture is **PASS**: 447 reachable packages, 10,026 modules, two accepted entrypoints, three selected config bundles, and seven Node runtime libraries. The current receipt is `docs/evidence/vm105-final-client-runtime-manifest-20260913.json`; its independently recomputed canonical manifest SHA-256 is `4331e0e5fd9ac6f5e881a0dae941f9f07dea7b69969ee8b610071ce14cb03f8b`, and its file SHA-256 is `54d117c638335edeefe43aaef0f181ea5317f7938a6861a145871a0d9e45e8dd`. This supersedes the historical 28-package/56-file source anchor and the earlier BLOCKED capture receipts.

The inspector binds accepted CLI/client entrypoint and config-bundle hashes, resolves reachable package roots within `/opt/deepseek-harness/node_modules`, and inventories regular `.js`, `.cjs`, `.mjs`, `.json`, `.node`, and `.wasm` files across those roots. Every hash compares pre/post path and held-descriptor identity; a second complete inventory must match before PASS. It rejects unresolved required artifacts, link escapes, accepted-pin mismatches, and observed hash/inventory drift. The fresh post-fix capture returned the same canonical hash; no JavaScript, client, provider, or model ran and no VM state was changed.

The manifest is UTF-8 JSON with alphabetically sorted object keys and module rows sorted by `stagedRelativePath`; its canonical digest excludes `canonicalManifestSha256` itself. The Node pin is `/opt/node-v24.19.0-linux-x64/bin/node`, SHA-256 `bc17c508ffeed0ec622934f9b7fa72f8e78da65350e63c3eceb56fa688aa5e12`; canonical paths and loader/shared-library hashes are present in the receipt. The install-path version is not a JavaScript-executed version probe. This captures installed sources; production copying, descriptor custody, and before/after staging verification remain external release work.

## Exact two-request transport

The final contained client performs one native generation step with tools disabled and `maxRetries: 0`. A coordinator-owned anonymous pipe contains one version-1 credential document. Its write end closes before child start; only the read FD is inherited; a non-secret patch points `credentials-local` to `/proc/self/fd/<fd>` with `watch: false`; core dumps are disabled; both descriptors close after the initial read; no credential bytes persist in environment, argv, ordinary files, logs, receipts, stores, or the retained root.

Only these requests are accepted:

1. `POST <BOUND_RELAY_ORIGIN>/v1/chat/completions` with `model: "agent/normal"`, streaming enabled, `tools: []`, `tool_choice: "none"`, and the bound task/run/turn/idempotency tuple. Virtual-route data is a separately bound chat-request field and is not claimed as part of the shared tuple.
2. Before any output is released, `POST <BOUND_RELAY_ORIGIN>/v1/agent-routes/events` with event `output_started`, the identical task/run/turn/idempotency tuple, HTTP 202, and `{accepted:true}`.

The receipt must show exactly two classified HTTP requests, tuple equality, ACK-before-output, `progressCommitted:true`, `resumeRequired:false`, and zero redirects, retries, discovery, catalog, direct-provider, tool, or second-generation requests. It omits credential, prompt, response, endpoint secret, environment values, and provider attribution.

The proven no-network smoke cannot carry HTTP. The final client must keep `PrivateNetwork=yes` and have no direct route outside its fresh namespace. Its sole reachable listener remains a fixed loopback relay. The native documented gateway is `http://192.168.1.68:20128/v1`; the earlier invented gateway TLS binding is withdrawn. Public `https://ai.mysw.me/v1` currently lacks `/v1/agent-routes/events` in its fresh proxy matcher and is unusable for durable ACK without a separately authorized route addition and live proof.

Strict Bell-PC2 SSH control access to VM105 and existing strict SSH to VM1205 `belladmin@192.168.1.68` are control/review facts. Previously observed loopback management forwarding is not an active provider-data tunnel. SSH forwarding remains only a candidate separately reviewed secure transport; VM105-to-gateway SSH credentials, durable data forwarding, and encrypted provider traffic remain NOT PROVEN. Retain the native private-LAN HTTP origin without inventing TLS or changing any gateway.

The fixture-only `scripts/Invoke-VM105FinalClient.py` proves two-request ordering on literal loopback HTTP, ACK-before-first-byte, tuple equality, third-request denial, and cleanup. All unsupported methods, including unknown verbs, share the failure/denial path and wake waiters; a denied GET between chat and ACK releases no chat output. ACK waits until successful upstream chat response headers prove chat arrival, then rechecks failure before sending. The adversarial regression starts ACK while chat is held before its upstream send and observes the gateway arrival order chat then events. The combined focused suites pass 18 tests and the fixture CLI returns PASS. Its production preflight requires external endpoint/key-reference bindings and a complete PASS closure manifest whose canonical hash is recomputed and matched to an independently supplied expected hash, emits sanitized presence only, and never invokes the final client. It does not implement or prove production namespace/socket transfer. Before live acceptance, a separate reviewed containment integration must connect only the two fixed upstream sockets and transfer them to the namespace relay without introducing a host-network listener or direct client route. No general proxy, destination/provider/model selection, or live execution is authorized by fixture PASS.

On any failure, release no output, record explicit resume state, terminate and reap the exact unit cgroup, close only owned descriptors, retain the final root and sanitized receipt, and stop without retry or recursive cleanup.

## Active real-service selectors

A 2026-09-13 sanitized read-only classifier inspected only allowlisted selector names and known-path equality. Receipt `docs/evidence/vm105-real-service-selector-classification-20260913.json` has SHA256 `5b1ffd4006834961d3810ce204b5e40cff9274971e013403c377fbad90779721`; it emitted no environment value or config content. The active `deepseek-harness.service` process has both `DSH_HOME` and `HOME`; `DSH_HOME` matches the existing pilot root `/home/dsh/.dsh`, and `HOME` matches `/home/dsh`. This binds the current service configuration root for a later rollback receipt. It does not authorize reading or changing the opaque pilot.

Source precedence is configured `dshHomePath`, then nonblank `DSH_HOME`, then OS home plus `.dsh`. The relevant default selector is `/settings.json#/agentDefaultModel`, with profile composition under `/profiles/web/cordis.yml` and its patch input. The exact active default-model value and profile composition remain **UNBOUND**: the fixed settings probe returned no readable result, and the two `dshHomePath` key-presence probes were false. No value was emitted.

A later default activation transfer must therefore name only: the existing service unit `/etc/systemd/system/deepseek-harness.service`; the current rollback selector `DSH_HOME -> /home/dsh/.dsh`; the exact new profile root; the exact non-secret selector/drop-in permitted to change; one restart; one rollback; and post-change real-client acceptance. It remains separate from isolated final-client acceptance.

## Remaining release bindings

1. Fresh production staging and verification against the now-bound installed manifest, entrypoint/config-bundle pins, Node hash, and native/runtime dependency hashes. Installed capture PASS does not establish a copied final root.
2. Bound private loopback relay origin, the documented native HTTP LAN origin, and any separately reviewed secure-transport binding.
3. Credential key identity/reference and exact version-1 document schema, without the key value.
4. A fixed launcher/relay and receipt schema implementing the two-request contract under the proven systemd controls.
5. Independent Sol High acceptance, coordinator acceptance of the exact final root and contract, and fresh VM105 service/pilot state immediately before release.

Until all five are bound, absence of `/var/tmp/omniroute-dsh-client-final-20260913` must be freshly verified and this packet grants no execution or default-routing authority.
