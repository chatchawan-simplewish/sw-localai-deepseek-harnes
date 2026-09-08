# VM105 authorization contract: offline synthetic characterization

Recorded 2026-09-09 05:10 Asia/Bangkok. This check executes the actual retained authorization service body using synthetic external boundaries. It does not authenticate a provider or accept a provider lane.

## Reproduce

From the authoritative worktree, run:

```powershell
node scripts/test-native-authorization-contract.mjs C:/Users/chatc/.codex/tmp-native-oauth-entries.json
```

The first argument is the retained public-source entries JSON; another location containing the identical pinned source is accepted. The input is required and is not committed or reacquired by the checker. Full authorization source SHA-256: `d86547a2f450ff7f58f421f5e2a91eab6abc5ac3dc2ae90cd3785d15547002a3`. The checker also validates the full Cordis source in `vm105-native-core-source-2026-09-09.json` against `1729cdbf8ee40b17c8839e06bf96491490548559e11ef7e411271e0754e751c5` before any source execution.

## Observed checks

Node v24.19.0, Windows: normal run exited 0, four cases passed:

- An existing configured record without a fresh update is rejected with `NOT_COMMITTED`.
- An update for an unrelated record is rejected with `NOT_COMMITTED`.
- An update event without a configured record is rejected with `NOT_COMMITTED`.
- An initially unconfigured synthetic record configured during the flow, followed by its update event, returns `authorized`.

Each case additionally verifies watcher removal, in-flight release, settlement status, and flow disposal.

Two deliberate in-memory mutations each exited 1 with the expected assertion failure:

```powershell
node scripts/test-native-authorization-contract.mjs C:/Users/chatc/.codex/tmp-native-oauth-entries.json --mutate-missing-write
node scripts/test-native-authorization-contract.mjs C:/Users/chatc/.codex/tmp-native-oauth-entries.json --mutate-missing-configured
```

Removing the observed-write guard produced `Missing expected rejection: existing configured record without fresh write is rejected`. Removing the configured-record guard produced `Missing expected rejection: update without configured record is rejected`. The first mutation was run before the unmodified-source green check. Mutations alter only the in-memory verified source; retained sources remain unchanged.

## Limits and impact

Independent reviewer `/root/independent_auth_review` accepted this bounded contract at 20260909 051303 with no severity findings. It verified script SHA256 `c8952bbeb5ad7947b9543df100789cca059cb65cc88cba0fd8d19ba81224c0b4`, the normal exit-zero run and both specific expected exit-one mutation failures on Node v24.19.0. The script hash remained unchanged. Parent also independently ran the normal four-case check, verified the digest and reviewed the source and evidence. LF checkout policy is pinned for the checker.

The loader replaces only the two imports with synthetic `Service` and `HarnessError`, and the export with a class result; the unmutated authorization class body is retained. The event context and boolean credential description are synthetic. No credential values exist in the fixture. The positive case models a write and notification; it proves no real storage persistence.

Full Cordis source is hash-verified but not executed. Its imported Cosmokit dependency was unavailable in the inspected retained native JSON inputs; no shim graph or new source acquisition was added. Cordis service injection, actual credential storage, real provider adapters, authentication, native bridge operation, Linux execution and cutover readiness remain **NOT PROVEN**. No VM, SSH, sockets, provider network, profiles, GPU, inference, firewall or power operations were performed. No production implementation changed and no live one-shot gate was consumed.
