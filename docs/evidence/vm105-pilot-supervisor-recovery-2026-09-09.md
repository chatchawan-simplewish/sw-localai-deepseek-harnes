# VM105 pilot supervisor recovery

2026-09-09 00:50 Asia/Bangkok. Scope: restore the previously reviewed automatic SSH reconnect task without disrupting the current tunnel. No VM, firewall, credential, or script changes.

Fresh checks found the task `DeepSeek Harness VM105 SSH Tunnel` Ready, last result `3221225786`, and former supervisor PID55908 absent. The existing SSH child PID33528 still listened on `127.0.0.1:3080` and returned HTTP200. The termination cause was not investigated or inferred.

Before restarting the task, parent verified its exact previously reviewed PowerShell action and both repository and installed script SHA256 `59E1E77B9C9C308E8DF89E2E8E2494B417FFA0BE255DF6CCF228B1EBF4FFF571`. The supervisor's reviewed busy-listener guard preserves existing tunnels. Parent executed only `Start-ScheduledTask -TaskName 'DeepSeek Harness VM105 SSH Tunnel'`, exit0, under the owner's routine unattended development preapproval.

Readback receipt `d1b030`, before clock00:50:49: task Running, result267009 (running), exactly one matching supervisor PID54072; listener PID33528 unchanged at127.0.0.1:3080, HTTP200. Prior VM readback `0cdb6f` showed pilot active, PID829, start2026-09-08 14:41:13UTC, NRestarts0.

This proves the supervisor was restored and preserved the usable tunnel. No child-exit recovery test was repeated; the earlier independently reviewed test remains historical evidence in `vm105-pilot-auto-reconnect.md`. Windows sign-in and host-reboot recovery remain untested. No full-plan progress increment.

Independent review: `candidate_smoke_review` accepted the documented readbacks and source comparison at2026-09-09 00:52:33 Asia/Bangkok, reviewing SHA256 `8DAA53988CFEA66CEAFBDFBF6894F89030BF88F10906E47DC80C5053582A32C4` before this annotation. It independently matched the supervisor source hash and occupied-listener guard; it made no fresh live observation.
