# VM105 final-client transport review — 2026-09-13

Scope: fixture-only implementation in `scripts/Invoke-VM105FinalClient.py`; no final client, provider, service, key, proxy, profile, default, or live endpoint action.

## Bindings and limits

The native documented endpoint remains `http://192.168.1.68:20128/v1`. No TLS identity was invented. The fresh proxy matcher for public `https://ai.mysw.me/v1` lacks `/v1/agent-routes/events`; this public route is unusable for durable ACK unless a separate route addition and live proof are authorized and completed. This binding was supplied by the coordinator's current source inspection; this fixture did not contact either endpoint.

Strict Bell-PC2 OpenSSH control access to VM105 is an established read-only control path. Existing strict SSH to VM1205 `belladmin@192.168.1.68` and the previously observed loopback-only management forwarding are candidate ingredients for a separately reviewed secure transport. VM105-to-gateway credentials and an active durable provider-data tunnel remain NOT PROVEN. Direct private-LAN HTTP is the minimum documented native data path. No encrypted provider traffic is claimed.

## Implementation and evidence

`TwoRequestRelay` permits only literal loopback fixture HTTP with `fixture-key-not-secret`; it is intentionally unavailable for production origins. A lock classifies one chat and one matching `output_started` event. A timed event gates chat bytes on HTTP 202 and exactly `{accepted:true}`. Requests have bounded bodies and timeouts, a fixed upstream origin, fresh controlled headers, no redirects/retries, and owned connection/listener cleanup. Receipts contain no incoming headers, credentials, payloads, or provider attribution.

Strict RED: `python -m unittest -v scripts.test_vm105_final_client_transport` exited 1 with `FileNotFoundError` for the absent launcher. The first implementation run caught missing third-request denial output; that per-request state error was corrected before GREEN.

GREEN: the same focused command passed two tests. `python scripts/Invoke-VM105FinalClient.py --fixture-regression` exited 0 with status PASS, requestCount 2, tupleEquality/ackBeforeOutput/progressCommitted/thirdRequestDenied/cleanupComplete true, resumeRequired false, and retries/redirects/discovery/catalog/directProvider/tools zero. The real threaded fixture holds its ACK response while the client observes no first byte, then verifies literal `data: first\n\n`, identical literal tuple fields, exactly two gateway arrivals, denied third POST, and closed listener/threads.

Production preflight requires the exact documented endpoint, a nonblank opaque external key reference, and a complete PASS closure manifest and an independently supplied expected canonical hash. It emits only binding presence and documented origin, then stops. It validates nonempty package/module/entrypoint/config/runtime structures, ordered unique staged paths, Node/runtime hash shapes, and the recomputed canonical SHA256 (excluding its own field) against that expected hash. It does not resolve keys, verify/stage live runtime files, launch a client, create a namespace, or transfer sockets. A PASS input receipt is necessary, not final authorization or fresh artifact verification. The accepted systemd namespace/socket handoff and production integration remain separate release work; this local fixture is not proof of that integration or live durable ACK.

## Independent review fix round 1

The downstream ACK response is now written and flushed before progress is committed or the chat-release event is set. A deterministic held/failed downstream write regression reproduces the original ordering break and proves failure releases no chat bytes. Non-daemon relay handlers are tracked and joined by server_close before owned connections close, preventing connection-list mutation during teardown. Success and failed-write tests assert closed listener, empty handler tracking, joined workers, and closed owned/client sockets. Four focused tests pass, including the actual Task 1 manifest positive result and incomplete, changed, wrong-hash inputs failing closed. These are local fixture/preflight facts only. Successful flush proves local socket delivery, not remote application consumption.

## Final review fix wave

All unsupported HTTP methods now use one denial path that sets failure and wakes ACK/chat-forwarding waiters. Nine method cases, including TRACE and an unknown verb, prove a rejection between chat and ACK prevents all chat payload bytes. ACK forwarding waits for successful upstream chat response headers and rechecks failure; a regression starts and classifies ACK while the chat upstream send is held, then proves actual gateway arrival order chat followed by events. Existing held/failed downstream ACK-write coverage and cleanup checks still pass.

Strict RED preceded the fix: the new transport regressions reproduced seven leaked-chat cases, two framework 501 bypasses, and the early-ACK ordering break. Final combined focused suites: 18 tests, OK (six transport, 12 manifest). Fixture CLI: PASS with exactly two upstream requests, ACK-before-output, tuple equality, committed progress, third-request denial, and cleanup; all other traffic counters remain zero. Manifest drift checks and a second full inventory are now in place; the fresh strict SSH capture is PASS with canonical SHA-256 `4331e0e5fd9ac6f5e881a0dae941f9f07dea7b69969ee8b610071ce14cb03f8b`.

These remain fixture, preflight, and read-only capture facts. Production namespace/socket handoff, endpoint/key binding, runtime staging verification, and live final-client acceptance are external.
