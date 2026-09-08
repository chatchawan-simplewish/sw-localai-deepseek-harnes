# Bell-PC2 route scope conflict

Recorded 2026-09-09 03:41 Asia/Bangkok by continuation `01a082bd-c2aa-7050-b40c-8508d207cb26`. Repository: https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git.

**PROV-04 remains BLOCKED / NOT PROVEN.** A newer cross-project record changes the premise behind the historical Bell-PC2 worker endpoint. This is source-record evidence, not a fresh live host probe or permission to restore it.

The active task `Continue Bell-PC2 Jellyfin GPU acceptance…` (`01a08159-57cf-7202-97cf-f9941f5811ae`) identifies authorized obsolete local-AI autostart/exposure cleanup in its task preview. Its retained handoff is `C:/ChatGPT Projects/SW-Selfhosted-Network/.worktrees/bell-pc2-jellyfin-transcoding/docs/handoffs/bell-pc2-jellyfin-transcoding-continue-20260908.md`. The latest commit touching that file at inspection was `ad6a205a0590771bbe16b27bfcf2d0a4ac551d7d`, dated 2026-09-09 01:45:50 +07:00; the active task may subsequently update it.

Relevant source lines at inspection:

- Line 124 records removal of the exact `Bell-PC2 Local AI Gateway` scheduled task, stopping its local-AI Caddy listener `192.168.1.161:11435`, and moving `Ollama.lnk` from Startup to a retained disabled-autostart location.
- Line 42 records an independent post-mutation audit, the missing original scheduled-task XML backup, and the later verified absence of Ollama processes/listeners 11434/11435. It also records that an `ollama ps` inspection unexpectedly launched a process; do not use that CLI as a passive probe.
- Line 56 states the owner superseded the old local-AI GPU reservation for the Jellyfin task.

The September 9 01:01 local-worker audit in this Harness repository searched older named worker/coordinator records. Its historical mappings remain historical; it did not establish current availability and does not supersede this newer cross-project evidence. No old receipt or immutable firewall packet is rewritten.

## Consequence and next boundary

Do not restart Ollama/Caddy, recreate autostart, reclaim the GPU, broaden network access or substitute a different worker under routine Harness preapproval. Those steps would reverse a separately owned resource decision. The original Bell-PC2 route remains in the full v1 requirement inventory. It cannot be silently dropped, changed to Jellyfin, or marked accepted.

After the current offline engineering is concrete and reviewed, an owner decision is needed to reconcile the original Bell-PC2 inference requirement with the newer retirement/resource allocation. Until then, retain the existing working VM105 pilot and continue independent cutover/OAuth implementation. No live Bell-PC2, VM1201, VM105 or Jellyfin action was performed for this finding.
