# VM105 final-client transport review — 2026-09-13

Scope: fixture-only implementation in `scripts/Invoke-VM105FinalClient.py`; no final client, provider, service, key, proxy, profile, default, or live endpoint action.

## Bindings and limits

The native documented endpoint remains `http://192.168.1.68:20128/v1`. No TLS identity was invented. The fresh proxy matcher for public `https://ai.mysw.me/v1` lacks `/v1/agent-routes/events`; this public route is unusable for durable ACK unless a separate route addition and live proof are authorized and completed. This binding was supplied by the coordinator's current source inspection; this fixture did not contact either endpoint.

Strict Bell-PC2 OpenSSH control access to VM105 is an established read-only control path. Existing strict SSH to VM1205 `belladmin@192.168.1.68` and the previously observed loopback-only management forwarding are candidate ingredients for a separately reviewed secure transport. VM105-to-gateway credentials and an active durable provider-data tunnel remain NOT PROVEN. Direct private-LAN HTTP is the minimum documented native data path. No encrypted provider traffic is claimed.

## Implementation and evidence

`TwoRequestRelay` permits only literal loopback fixture HTTP with `fixture-key-not-secret`; it is intentionally unavailable for production origins. A lock classifies one chat and one matching `output_started` event. A timed event gates chat bytes on HTTP 202 and exactly `{accepted:true}`. Requests have bounded bodies and timeouts, a fixed upstream origin, fresh controlled headers, no redirects/retries, and owned connection/listener cleanup. Receipts contain no incoming headers, credentials, payloads, or provider attribution.

Strict RED: `python -m unittest -v scripts.test_vm105_final_client_transport` exited 1 with `FileNotFoundError` for the absent launcher. The first implementation run caught missing third-request denial output; that per-request state error was corrected before GREEN.

GREEN: the same focused command passed two tests. `python scripts/Invoke-VM105FinalClient.py --fixture-regression` exited 0 with status PASS, requestCount 2, tupleEquality/ackBeforeOutput/progressCommitted/thirdRequestDenied/cleanupComplete true, resumeRequired false, and retries/redirects/discovery/catalog/directProvider/tools zero. The real threaded fixture holds its ACK response while the client observes no first byte, then verifies literal `data: first\n\n`, identical literal tuple fields, exactly two gateway arrivals, denied third POST, and closed listener/threads.

Production preflight requires the exact documented endpoint, a nonblank opaque external key reference, and a PASS closure manifest with a syntactically valid canonical hash. It emits only binding presence and documented origin, then stops. It does not resolve keys, verify/stage runtime files, launch a client, create a namespace, or transfer sockets. A PASS input receipt is necessary, not final authorization or fresh artifact verification. The accepted systemd namespace/socket handoff and production integration remain separate release work; this local fixture is not proof of that integration or live durable ACK.
