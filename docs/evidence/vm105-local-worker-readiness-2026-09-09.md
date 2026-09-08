# VM105 local-worker prerequisite audit — 2026-09-09

Repository: https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git (origin verified locally). Audit clock: 2026-09-09 01:01:26 Asia/Bangkok. Local documentation only; no live worker/network/hardware checks.

**Result: VM1201-QWEN and BELL-WORKER remain BLOCKED. Historical endpoint/model mappings were recovered, but no authoritative current worker mapping or VM105 access grant was established.**

- Local-worker prerequisite review: 02/02 documented routes examined; 00/02 routes released.
- The existing Phase 3 packet remains SHA256 `FF91A5E0D0FB29F7CAFEFFF32B8B3A1A7DD2A76CC087A38E4939435532D361A1`, matching its independent review. No packet or route setting changed.

## Historical mapping versus newer project evidence

| Worker | Exact historical documentation | Newer retained project evidence (2026-09-08, not a fresh audit probe) | Current acceptance |
| --- | --- | --- | --- |
| VM1201 | August 17 acceptance names `prox01-local-ai`, `192.168.1.143`, direct bearer-authenticated `http://192.168.1.143:8000/v1`, Qwen3.8-27B Q4_K_M alias `qwen3.8-27b`; `local-ai.service`, `local-ai-default.service`, `local-ai-control.service`. Port 8001 is admin-only, not a Harness inference endpoint. | Provider prerequisite H1 records strict SSH timeout to historical `.143:22` and VM105 `/v1/models` HTTP000 to `.143:8000`; current machine identity cannot be assigned from that failed contact. | Historical candidate only. Current identity, owner, listener, model, auth and effective firewall remain unresolved. |
| Bell-PC2 | August 17 continuation records Ollama 0.32.13 at `127.0.0.1:11434`, Caddy 2.11.4 at `192.168.1.161:11435`, OpenAI-compatible base `http://192.168.1.161:11435/v1`, model IDs `qwen3.5:9b-q4_K_M` and `scb10x/typhoon-ocr1.5-3b:latest`. Coding default was Qwen; OCR quality retained WARN. Startup shortcut recovery was documented, not a Windows service assertion. | H2 records gateway Caddy PID17684 owned by `BELL-PC2\\chatc`, no matching Win32_Service row, owner-host unauthenticated HTTP403 and VM105 HTTP000. Gateway observation does not establish current upstream Ollama, model or authentication configuration. | Gateway identified in the retained September evidence; current upstream/model/auth remains unresolved. Do not treat historical versions or models as live. |

The August 22 Bell-PC2 coordinator handoff explicitly says its earlier idle/listener evidence is historical and not fresh August 22 proof. It preserves separate VM1201/VM1203 ownership and waits for a verified terminal source handoff. That source handoff was not verified in this audit. These are the latest relevant dated coordinator/worker documents located in the bounded named handoff and hardware paths; this is not a claim that no newer evidence exists elsewhere.

## Hardware, load and ownership boundaries

- VM1201's August 17 acceptance concerns the then-current two RTX 5060 Ti 16 GB stage, DTECH PW072A 850 W PSU and separate GPU power cables. Later ADT-Link x8+x8/four-GPU work was explicitly NOT PROVEN there. Its short accepted tests do not establish present topology, cooling, PSU condition or sustained-load readiness.
- The August 17 Qwen benchmark reports a thermal/power-balance WARN and an 80 C abort threshold. The retained monitoring/runbook documentation treats thermal slowdown and attributable Xid/AER/CUDA/fallen-off-GPU faults as stop conditions; sustained 75 C or a sustained 15 C GPU delta requires resolution. These are historical documented criteria, not permission to run their tests or evidence that any later thermal gate cleared.
- Bell-PC2 documentation preserves loopback-only Ollama, exact-client authenticated Caddy, one model at a time, idle VRAM release, and separate approval for sustained load/maximum-context tests. Historical empty `ollama ps` does not establish idle state today.
- The August 22 coordinator forbids taking over VM1201/VM1203 source lanes or consuming their one-shot approvals. Its VM1203 credential/OMP/Hermes dependency is a historical source-lane gate, not proof of a new universal Harness prerequisite. Current ownership and any superseding handoff must be established before work touching those resources.
- This audit does not release model loading, inference, GPU/CUDA tests, service changes, host/VM power actions, firewall changes or credential creation. Routine document preparation remains covered by standing preapproval; hardware and independent source-lane gates are not silently consumed.

## Exact missing facts and next bounded action

For VM1201: an authoritative current VM/host/address mapping; responsible operator; current intended listener/service/model identifier; authentication and credential ownership; present hardware/load gate state; destination-observed VM105 source; effective firewall ownership and a valid unauthorized negative-control source.

For Bell-PC2: current upstream listener/service and intended model identifier; gateway/upstream authentication policy and credential owner; current load/idle boundary and resource owner; destination-observed VM105 source; effective firewall and a valid unauthorized negative control. The retained gateway rule allows `.142/.146/.147`; none is a valid unauthorized control merely because it is not VM105. Local HTTP403 does not attribute a network rejection to a particular firewall rule.

The historical VM1201 onboarding kit requires fixed client-address proof and exact per-client network acceptance before credentials or API calls. It does not authorize copying another client's key or broadening access. VM105 `.139` is not among the historical accepted worker clients. No rule is proposed here; retain both existing BLOCKED decisions until the named facts are supplied through a separately scoped, owner-coordinated read-only verification. Do not substitute another host, model, endpoint or transport after timeout.

## Local source provenance

Independent review: `candidate_smoke_implement` accepted this document's historical/current distinctions and retained gates at2026-09-09 01:09:23 Asia/Bangkok, before this annotation, SHA256 `A4BDF9ED4D9AAEF7A5310D85B96B5A99214D410579924DEFB178D6E4F53202E8`. It checked the cited local records and packet hash; no fresh worker observation or route release.

Authoritative Harness files read:

- `docs/evidence/phase-03-provider-prerequisites.md`, provider table and H1/H2.
- `docs/evidence/phase-03-provider-credentials.md`, local-worker blocked credential mapping (targeted search).
- `docs/evidence/phase-03-firewall-results.json`, both local-worker decisions.
- `docs/evidence/phase-03-firewall-review.md`, immutable packet decision; packet hash independently recomputed above.

Historical SW-LocalAI sources are under `C:/Users/chatc/Projects/SW-LocalAI/worktrees/deepseek-harness-vm105/`:

- `docs/handoffs/bell-pc2-local-ai-coordinator-handoff-20260822.md`.
- `.planning/continuations/bell-pc2-local-ai/.continue-here.md` (August 17 checkpoints).
- `docs/hardware/prox-01/vm1201-multi-gpu-local-ai-acceptance-20260817.md`.
- `docs/hardware/prox-01/vm1201-harness-onboarding-kit.md`.
- `docs/hardware/prox-01/vm1201-qwen3.8-27b-benchmark-20260817.md` (targeted thermal/model search).
- `docs/hardware/prox-01/vm1201-local-ai-monitoring-design.md`, `prox01-adt-link-x8x8-cutover-runbook.md`, and `vm1201-next-model-shortlist.md` (targeted thermal/gate search).

No protected configuration, credentials, live logs, SSH session, browser, provider HTTP or inference was accessed. No historical test command was executed. Only this document was created; other owners' work was preserved. Documentation establishes candidates and missing facts only; effective readiness remains NOT PROVEN.
