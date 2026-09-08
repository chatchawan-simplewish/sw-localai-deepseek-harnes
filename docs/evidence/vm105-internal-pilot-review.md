# VM105 internal pilot focused result review

Verdict: **ACCEPTED WITH LIMITATIONS** for the disposable internal pilot only. Reviewed 2026-09-08 21:22:52 Asia/Bangkok. No production or strict preparation acceptance.

## Independently verified

- Read the four-check pilot plan and parent result record. Used strict host-key SSH as dsh to VM105; no credentials, profiles, logs, browser state or inference inspected.
- Read `/srv/dsh/workspaces/internal-pilot-20260908/slugify.py`. The implementation rejects non-string input, converts runs outside ASCII letters/digits into a separator before lowercasing, and trims separators. This correctly handles the documented Kelvin-sign regression without Unicode case conversion admitting it as ASCII.
- Executed `python3 /srv/dsh/workspaces/internal-pilot-20260908/slugify.py`: four output assertions and one TypeError check passed; exit 0.
- SHA256: `a3afba54e8d94090fe18b340c5565beb3af345dcae1e010ebe55a61952887021`, matching parent evidence.
- Service readback: active/running, NRestarts 0; port 3080 listener bound only to `127.0.0.1` in the returned socket table.

## Evidence boundaries and limits

- Successful PILOT_OK response, Harness file/tool flow, selected OpenRouter Auto Router, credential permissions and partial Landlock enforcement are parent-observed UI evidence, not independently replayed. No extra paid inference or browser/credential access was needed for this review.
- The successful route is owner-added OpenRouter. Exact served model, backend and cost are not established. The fixed-model objective was achieved only as an explicitly identified router selection, not proof of a particular backend.
- OmniRoute's local Qwen route remains unavailable in the reported attempt. A 503 queue timeout is an observation, not a demonstrated root cause.
- Existing interpreter ownership is accepted only for this trial. Partial Landlock enforcement does not establish a fully enforced sandbox; keep work disposable and internal.
- The prior strict preparation goal remains BLOCKED and the full roadmap remains 09/21. This result does not lift that gate or authorize infrastructure changes.

## Publication correction

Closed: bounded read confirmed the parent replaced the stale pending sentence with "The subsequent OpenRouter coding task passed as recorded above." The historical local-route failure and later successful coding result are now distinguished. No implementation finding blocks this bounded pilot.
