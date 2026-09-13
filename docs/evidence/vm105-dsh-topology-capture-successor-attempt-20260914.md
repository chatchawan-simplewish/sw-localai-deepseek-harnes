# VM105 DSH topology capture successor attempt — 2026-09-14

## Result

`PASS / FOURTH ONE-SHOT AUTHORITY SPENT / TOPOLOGY EVIDENCE ACCEPTED`

The coordinator explicitly authorized the exact successor PowerShell block at source commit `8f63cd45d07b5b95ba425187338a7fe558e91acf`. Action-time preflight matched the reviewed source, test, contract, accepted-manifest, raw CRLF builder, external source-review, and preserved prior-receipt hashes; verified the strict identity as a regular non-link file and the VM105 known-host entry; confirmed sole ownership and installed-root stability; and found the successor leaf absent.

The exact block ran once under terminal handle `339` and returned `rc=0`. The invocation was not retried and is spent. It published `docs/evidence/vm105-dsh-topology-capture-successor-20260913.json` through the fresh no-overwrite boundary.

- Status: `PASS`
- Raw size/framing: 1,825,540 bytes; one canonical UTF-8 JSON line followed by one LF
- Raw file SHA-256: `86882398a06921bd351c84dbfc1eecc9abeb963912df41499ee21462b50cb47f`
- Canonical receipt self-hash: `cc7ca73f74bd1e515416cbff65809531fff2c052d0f7e406b9cc2efdb4c1ab20`
- Accepted manifest canonical SHA-256: `4331e0e5fd9ac6f5e881a0dae941f9f07dea7b69969ee8b610071ce14cb03f8b`
- Accepted/reachable packages: 447/447, zero missing and zero extra identities
- Dependency links: 2,029
- Headless patch SHA-256: `534dc49c84b0fb9c2d3278dc8990f577d57b7a88442941444b58c96ac1a09ba0`

The preserved prior BLOCKED receipt remains 142 bytes with raw SHA-256 `86d878deb002c62cf69013717d38193248b7deed5b19a5a37c40e87de07c001d`.

Independent external receipt review artifact `C:\ChatGPT Projects\SW-Selfhosted-Network\.worktrees\omniroute-live-review-20260913\docs\vm105-dsh-topology-capture-successor-receipt-review-20260913.md`, SHA-256 `0a0a71517e8dc7fe5f9a97439f844913fc69011b25ea8d3b809e6287d7ec73da`, commit `40a7c734bd91c93f1109493b502decca58a5ccdf`, accepted the topology evidence with zero missing/extra identities and granted no reconstruction, staging, credential, DSH, provider, service, profile, or default-routing authority.

The receipt proves the installed topology at capture time. It does not prove a copied final root, reconstruction, sealing, DSH boot, systemd, namespace/cgroup behavior, socket handoff, credential delivery, gateway acceptance, provider behavior, service activation, or ordinary post-default multi-turn/tool/durable-ACK/no-replay behavior.
