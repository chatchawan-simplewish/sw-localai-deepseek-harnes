# VM105 DSH consumer boundary for OmniRoute client acceptance

20260912 211750 Asia/Bangkok. Read-only clarification for OmniRoute automatic-switching Phase 4 coordinator task `01a09361-8143-73d3-adb7-15043355276b`. Repository: https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git.

## Smallest safe future boundary

**Yes, with a newly reviewed isolated consumer.** A one-attempt DSH consumer can exercise a frozen OmniRoute request/response contract without touching the blocked native supervisor or the usable pilot, but only if it is a new process with a distinct private home, workspace, loopback endpoint, process group and synthetic OmniRoute server. It must not reuse `/home/dsh/.dsh`, `/home/dsh/.dsh-profiles/vm105-provider-v1`, the normal service unit, port 3080, the native owner bridge, or any provider credential/OAuth store.

The test may establish that the exact frozen DSH client communicates correctly with the coordinator's synthetic OmniRoute protocol and that automatic-switch decision/attribution fields survive client consumption. It cannot establish compiled routing parity, final normal-service composition, real provider availability, authentication, or an accepted VM105 provider route. Those remain `NOT PROVEN` until separately evidenced.

## Evidence basis

`docs/evidence/vm105-v1-source-revalidation-2026-09-09.json` source-only receipt binds installed `@deepseek-ai/dsh` and `@deepseek-ai/dsh-client-ui-settings-models`, both version `0.1.1-rc.2`; the latter's `lib/client.js` SHA256 is `c3b9a2d2d074c600c10553a4b15e294082f5851dd4a834d06ddb268b310d18de`. Its explicit scope states no installed JavaScript execution, so the receipt is insufficient for compiled-runtime parity.

The existing stopped candidate at `/home/dsh/.dsh-profiles/vm105-provider-v1` is not a reusable consumer fixture. Its creation/apply gates are consumed. Its generated profile selects only `@deepseek-ai/dsh-base` and `@deepseek-ai/dsh-web-app`, has an empty `llm-pi-ai` provider map, and disables `agent-default-model`; see `scripts/prepare-vm105-provider-candidate.py`. This establishes historical construction, not an integration release.

The native bridge's supervisor issue is disjoint: it concerns Unix-socket replacement preservation. a1, metadata, source, smoke, preflight and export gates remain spent; a2 is `RELEASED=False`. This does not block a separately scoped non-bridge consumer, but it must never be used to justify enabling or exercising the bridge.

## Exact bounded ownership needed for final client acceptance

The coordinator would need a written transfer of these narrow live lanes, with one parent owner for each:

1. **DSH consumer lane:** create, run, inspect and retain one fresh named private consumer home/workspace plus its exact `dsh` child process and loopback listener. The transfer excludes the pilot home, stopped candidate, systemd unit, existing tunnel/reconnect task, firewall, GPU and VM power.
2. **OmniRoute stage lane:** run and inspect one coordinator-owned synthetic or already-authorized staging endpoint that returns only the frozen test contract. It owns its own logs and lifecycle. No provider credential, upstream provider call, or production route is implied.
3. **Acceptance lane:** correlate the two retained receipts: executable/package hashes, consumer request/response and decision/attribution output, endpoint identity, child cleanup and no-pilot-change proof. Independent review must reject any output that exposes credentials or contains an unbound provider claim.

For a final non-synthetic client acceptance, the same lanes must additionally transfer the exact final DSH composition/profile selection and the coordinator's accepted OmniRoute endpoint. That transfer still excludes normal-service cutover; actual provider authentication, credential persistence and pilot replacement remain their own owner-controlled gates.

## Required pre-execution packet

Before any consumer is created, freeze and independently review: the new exclusive root name; package/source and executable pins; a minimal no-secret profile; exact loopback endpoint and protocol fixture; restricted environment; deadline; child-PID/PGID cleanup; nofollow ownership/mode checks; output schema and retained receipt; and a no-pilot-change readback. A failed attempt is retained and diagnosed without retry. No current VM action is authorized by this clarification.
