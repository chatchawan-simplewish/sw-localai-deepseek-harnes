# VM105 isolated OmniRoute DSH consumer lane transfer

20260912 232947 Asia/Bangkok. Repository: https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git. This durable handoff transfers one uncreated future lane to OmniRoute coordinator task `01a09361-8143-73d3-adb7-15043355276b`.

## Transfer verdict

**TRANSFERRED — `/var/tmp/omniroute-dsh-client-20260912` only, conditional on fresh absence and reviewed execution scope.** The directory does not exist according to this transfer; no live check or creation occurred. Before any later use, the executor must verify the exact path is absent and create it atomically as the sole named child, refusing existing objects, symlinks, alternate paths, retries or cleanup. `/var/tmp` is only a shared parent; the reviewed launcher must hold and recheck its own new private directory with nofollow ownership/mode checks. Absence observation alone is not the creation guarantee.

The coordinator owns only future creation, staging, execution, inspection, retention and exact-child cleanup for this directory, a dedicated synthetic endpoint, and their correlated secret-free receipts. The coordinator may prepare the packet now, but may not execute it until independent review accepts the frozen implementation, pins and output contract.

## Accepted package staging boundary

The retained source-only receipt `docs/evidence/vm105-v1-source-revalidation-2026-09-09.json` accepts installed package identity for `@deepseek-ai/dsh` and `@deepseek-ai/dsh-client-ui-settings-models` version `0.1.1-rc.2`; `lib/client.js` pin is `c3b9a2d2d074c600c10553a4b15e294082f5851dd4a834d06ddb268b310d18de`.

Later package staging may read only the exact frozen package bytes from `/opt/deepseek-harness/node_modules` through held nofollow descriptors, rehash them, and write only verified copies under the transferred directory. It must not install, modify, delete, relink or broadly enumerate `/opt`. The receipt proves source identity only, so the packet must state exactly which executable/module graph is staged and must not claim compiled-runtime or routing parity before its own synthetic receipt.

## Explicit exclusions

This is not a transfer of the pilot, opaque `/home/dsh/.dsh`, stopped candidate `/home/dsh/.dsh-profiles/vm105-provider-v1`, any other profile, `/opt` runtime ownership, systemd, tunnel/reconnect task, firewall, native bridge, credentials/OAuth, providers, GPU, inference, Bell-PC2, host/VM power or any spent gate. It does not authorize native bridge a2, which remains disabled, or any candidate/pilot start.

## Minimum future acceptance packet

The packet must freeze: the exact exclusive directory and mode/owner; all package/executable hashes; a no-secret consumer profile; synthetic endpoint identity and loopback binding; sanitized environment; bounded process/PID/PGID/deadline cleanup; output schema; no-pilot-change readback; and one retained receipt correlation with the coordinator's V6/V7 decision/attribution fields. The synthetic consumer can prove only client-protocol handling. Provider qualification, normal-service composition, authentication and final route acceptance remain separate `NOT PROVEN` gates.

This DeepSeek task retains sole ownership of all excluded resources and remains stopped and unarchived. No deployment, provider call, key delivery or bridge action occurred during this transfer.
