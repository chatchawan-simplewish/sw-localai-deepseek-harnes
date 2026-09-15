# VM105 R11 source-only terminal boundary — 2026-09-15

## Terminal conclusion

No distinct, non-consuming, source-only evidence path can identify a VM105 repair contract from the committed R4-R11 evidence graph.

R11 at `f9d7b9b37a33e8aa140b056ed9ebf3fc484517f8` can only validate the fixed R10 pre-replacement terminal state and return `PRE_REPLACEMENT_BOOTSTRAP_REJECTION_CAUSE_UNATTRIBUTED`. Its inputs are the pinned R10 attempt and terminal receipts:

- Attempt raw SHA-256: `8c0d7b153fcde1c508f917a4b434c183c6fc42b625f7ab7ab7b7c93fc0a3a32b`.
- Terminal raw SHA-256: `e48e7739e95a358560585d3bd0670b62a8087d63d3dfceb934390125c17c8432`.

Those canonical records establish only `BLOCKED / BOOTSTRAP_REJECTED` before replacement, with `candidateValidationCode=-1`, `targetExecuted=false`, no rollback asset, no raw output, and `retryAuthorized=false`. They contain no safe discriminating bootstrap fact. Rehashing, canonicalizing, or testing them can only reproduce the same unattributed result.

## Required future boundary

R4-R10 are spent and R10 cannot be replayed, rebound, contacted, or retried. A future repair contract needs a **new external evidence and authority source** that safely distinguishes the bootstrap rejection. It must use fresh non-R10 leaves, an independently reviewed bounded diagnostic taxonomy, and a separate reversible-action design before any target contact.

Until that source exists, no payload, remote command, VM105 or Prox-01 contact, rollback asset, policy inference, repair authorization, or live action is permitted.
