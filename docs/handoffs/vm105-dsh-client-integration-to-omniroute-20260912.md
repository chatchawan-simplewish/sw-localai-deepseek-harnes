# VM105 DSH client-integration handoff to OmniRoute

20260912 183017 Asia/Bangkok. DeepSeek Harness repository: https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git. This handoff transfers only the read-only DSH package/client integration assessment lane to OmniRoute automatic-switching coordinator task `01a09361-8143-73d3-adb7-15043355276b`.

## Ownership verdict

**TRANSFERRED — bounded package/client lane only.** The route-client assessment is independent of the blocked VM105 native Unix-socket supervisor. The coordinator may use the retained package/version and source-pin evidence to prepare or review client-side automatic-switching acceptance, provided its own authority covers that work. This transfer grants no VM105 control, deployment, profile mutation, native bridge activation, credential operation, provider routing acceptance, or replay of any VM105 gate.

## Non-secret retained provenance

`docs/evidence/vm105-v1-source-revalidation-2026-09-09.json` records a fresh source-only SSH receipt (`remote_exit_code: 0`) for the installed `@deepseek-ai/dsh` package version `0.1.1-rc.2`:

- logical package path: `/opt/deepseek-harness/node_modules/@deepseek-ai/dsh`
- canonical package path: `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh@0.1.1-rc.2_7adf779e9bedfb2e97ced92905792931/node_modules/@deepseek-ai/dsh`
- package manifest SHA256: `dc930c0b18158f49ae3753ceaf6b1b7ae71dc6c8f45c85a2d679b142024addf7`
- client package: `@deepseek-ai/dsh-client-ui-settings-models` version `0.1.1-rc.2`, logical path beneath `dsh-web-app`, canonical path `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-client-ui-settings-models@0.1.1-rc.2_6ea45dce772d8d764ff9d4e073210778/node_modules/@deepseek-ai/dsh-client-ui-settings-models`, and `lib/client.js` SHA256 `c3b9a2d2d074c600c10553a4b15e294082f5851dd4a834d06ddb268b310d18de`.

The source receipt is public-source inventory only. It proves package identity and pinned bytes at its observation time; it does not prove compiled routing parity, runtime composition, client behavior, or any provider route.

The stopped candidate profile path is `/home/dsh/.dsh-profiles/vm105-provider-v1`. Its generated `profiles/web/package.json` selects `@deepseek-ai/dsh-base` and `@deepseek-ai/dsh-web-app`; its profile patch keeps `llm-pi-ai` provider configuration empty and `agent-default-model` disabled. See `scripts/prepare-vm105-provider-candidate.py`. This is historical candidate construction evidence, not current runtime proof. Opaque `/home/dsh/.dsh` remains unread and out of scope.

## Material limits and spent gates

- Native bridge a1, its metadata diagnostic, source, smoke, preflight and export gates are spent. a2 remains hard-disabled (`RELEASED=False`) and cannot be used as an indirect client test.
- The blocked Python inherited-listener supervisor is a separate, materially changed native-bridge architecture. This transfer does not approve or unblock it.
- No owner authentication or cutover readiness exists. Do not enter, inspect, copy, migrate, export or back up credentials/OAuth material.
- The candidate remains stopped according to retained evidence. Preserve loopback/SSH and firewall boundaries. No GPU, inference, host/VM power, browser login or Bell-PC2 worker action is transferred.
- Native OAuth/UI source evidence did not establish a supported owner login UI or effective credential-store binding. `dsh-client-ui-settings-models` source shows API-key UI/status behavior only; it is not proof of authorization transport.

## Next safe preparation step

For automatic switching, compare the coordinator's expected client request/response and routing attribution contract against the retained `lib/client.js` source pin and package manifest without executing the VM105 package. Record any mismatch as `NOT PROVEN`; do not infer compiled-runtime parity. Any VM105 client execution, profile selection, provider call or normal-service change requires a newly reviewed, separately authorized scope and current live-state verification.

This DeepSeek Harness task remains stopped, unarchived and read-only for the transferred lane. Full VM105 v1 remains incomplete at Total 09/21 evidence tasks; no provider is accepted.
