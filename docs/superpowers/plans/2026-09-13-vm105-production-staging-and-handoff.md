# VM105 Production Staging And Socket Handoff Plan

**Goal:** Prepare the source-only production mechanics that copy the accepted VM105 final-client closure into an externally supplied empty staging root and hand exactly two externally connected gateway sockets to the contained loopback relay.

**Baseline:** `40363b9468ebc3ca13334582d03479bb31ad6721`

**Authority boundary:** Local source, fixture tests, review evidence, commit, and branch publication only. Do not create or inspect the final VM105 staging root, connect a gateway, read a credential, enter a namespace, or change any remote staging, provider, firewall, service, profile, selector, or default.

## Task 1: Descriptor-held closure copy

**Owned files:**
- `scripts/Build-VM105FinalClientManifest.py`
- `scripts/test_vm105_final_client_manifest.py`

Add the smallest standard-library copy path that:

- accepts already-open source and exclusive empty staging directory descriptors;
- requires the accepted canonical manifest hash and exactly 10,026 module rows;
- opens every source and destination component relative to held descriptors without following links;
- verifies each regular source identity and hash before copying, then fsyncs and rehashes the staged file;
- stages the manifest-selected config bundles and pinned runtime files under deterministic, collision-free paths;
- enumerates the completed staging tree and fails closed on missing, extra, duplicate, colliding, changed, or non-regular files;
- leaves a partial staging root for investigation on any failure and emits no source contents.

Add focused temporary-directory tests for the success path and the trust-boundary failures introduced by this code. Do not recreate the accepted 18-test closure suite.

## Task 2: Exactly-two-socket namespace handoff

**Owned files:**
- `scripts/Invoke-VM105FinalClient.py`
- `scripts/test_vm105_final_client_transport.py`
- `docs/contracts/vm105-production-staging-and-socket-handoff-contract-20260913.md`
- `docs/handoffs/vm105-omniroute-final-client-packet-20260913.md`

Add the smallest Linux standard-library handoff and relay integration that:

- receives exactly two connected TCP descriptors over one Unix control socket using `SCM_RIGHTS`;
- assigns the descriptors once, in fixed chat then durable-ACK order;
- requires each peer to equal the externally supplied action-time gateway IP and port;
- reuses the accepted two-request protocol and never opens or reconnects an upstream production socket;
- closes all received descriptors on malformed metadata, wrong count, wrong peer, a third descriptor, protocol failure, or shutdown;
- fails closed on platforms without the required Unix descriptor-passing primitives;
- binds the remaining gateway/key/current selector values only when supplied by the coordinator.

Document the host supervisor/contained launcher contract: the supervisor resolves and opens the two sockets before containment; the contained process receives only those sockets and exposes only a fixed namespace-loopback listener. Treat the concrete namespace launcher and live service wiring as external acceptance work.

Add one focused local check. Use a Linux container only if one is already available; otherwise verify all platform-independent parsing and fail-closed paths locally and record the missing Linux end-to-end proof.

## Verification and publication

1. Run only the focused tests covering changed behavior.
2. Obtain a fresh independent Sol High source review.
3. Apply accepted review fixes and rerun the focused checks.
4. Commit only the owned source, tests, contract, plan, and updated packet with command-scoped Git identity.
5. Push the exact branch and send the coordinator a compact packet with commit, paths, results, limits, and remaining live bindings.
