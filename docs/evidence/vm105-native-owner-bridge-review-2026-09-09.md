# Native owner bridge independent code review

20260909 040719 Asia/Bangkok. Reviewer: `/root/native_bridge_code_review`. Repository URL verified read-only with `git remote get-url origin`: https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git. Worktree: `C:/Users/chatc/Projects/sw-localai-deepseek-harnes/.worktrees/vm105-authoritative-roadmap`.

Review - 03/03 implementation files inspected. Spec verdict: **CHANGES REQUIRED** for terminal error restoration. Quality verdict: **CHANGES REQUIRED**, one substantive P2 defect. Installed Cordis lifecycle compatibility is **NOT PROVEN**, independently of that defect. Parent acceptance remains pending.

## Scope and frozen inputs

Read AGENTS.md, `docs/superpowers/plans/2026-09-09-vm105-native-owner-bridge.md`, `.superpowers/sdd/native-owner-bridge/review-package.md`, all three implementation files, and the implementation report. Read the newer public composition receipt. No implementation changes, tests, runtime commands, SSH, provider requests, credentials, packages, profiles, browser actions, Git staging or commits were performed. This report is the reviewer's sole owned output; other work remains untouched.

Direct SHA256 checks matched all supplied frozen inputs:

| File | SHA256 |
| --- | --- |
| `scripts/native-codex-owner.mjs` | `90bb452d25d5b6c7c7593e2cfc7c01650069d1d63f4770728bff5ef32935b14b` |
| `scripts/native-codex-terminal.mjs` | `005acd012ca69fd543de902893014965431fd9d4dbb64ada6134b2dc9b92845d` |
| `scripts/native-codex-owner.test.mjs` | `d1ab61da2a7bc93f57ade7017cb23045601017eaba57e33188d35ff962c0f5b9` |

The reported 15/15 test result is implementer evidence, not a rerun or new reviewer execution result. The tests were read in full.

## Finding requiring repair

### P2: asynchronous terminal output errors bypass restoration

Location: `scripts/native-codex-terminal.mjs:59-65`, with cleanup at50-57 and raw input at `scripts/native-codex-terminal.mjs:30-34`.

`display()` catches only synchronous write throws and false backpressure returns through the frame handler. `ownerTerminal()` installs error listeners for the socket, and `hiddenInput()` installs them for input, but nothing installs an `error` listener on `output`. A terminal WriteStream can report a failed write as an asynchronous error event. If that arrives while a text/secret prompt is active, it escapes the safe finish path; an unhandled EventEmitter error can terminate the client before `release()` aborts the prompt and `hiddenInput.finish()` restores the saved raw mode. It can also expose the raw error/stack rather than a fixed failure. This contradicts the explicit error-restoration and sanitized-error contract.

Small repair: install a conversation-lifetime output error handler before writing anything; route it to `finish(1)` without echoing the error, and remove the owned listener during cleanup. Review input errors outside a pending prompt under the same conversation ownership. Add a focused synthetic output EventEmitter check that emits an asynchronous error while hidden input is active and verifies safe failure, raw-mode restoration, prompt/listener cleanup and absence of raw error text. Existing terminal doubles at test104-105 and189-191 are plain output objects, so they cannot exercise this failure.

## Native integration and lifecycle assessment

The reconstructed UTF-8 sources were SHA256-checked directly against their retained capture records:

| Retained public source | SHA256 | Findings |
| --- | --- | --- |
| `C:/Users/chatc/.codex/tmp-typhoon-ocr-adapter.json`, dsh-llm-pi-ai | `e183a9cdde703b47485410bd68d247c8becdb277c390f0f91c6dd28718d350e2` |2179-2206 confirms message/url/code notices;2219-2240 confirms select/text/secret and optional signal;2267-2281 confirms native flow;2344-2345,2384,2494 establish named name/inject/apply plugin shape. |
| `C:/Users/chatc/.codex/tmp-native-oauth-entries.json`, dsh-authorization | `d86547a2f450ff7f58f421f5e2a91eab6abc5ac3dc2ae90cd3785d15547002a3` |98-109 descriptor;137-160 begin request/outcome;198-244 cancellation race and attempt-specific committed-record authorization. |
| `C:/Users/chatc/.codex/tmp-native-surface-headless.json`, dsh-app-boot | `9d4b7f214cd35b3e8ce4e027b12cca34a416d355577aeacbf08a5b324f0cabb6` |953-985 proves config-relative loading;1107-1135 audits activation and missing injections;1167-1187 settles the tree and disposes partial contexts on boot failure. |

The exact `describe(KEY)` contract and `begin({key,method,interaction,signal})` match authorization source98-109 and137-160. Source198-244 makes authorized an attempt-observed committed-record outcome; the bridge forwards only that native status, with no credential reads. Native cancellation races provider completion, as the report correctly states. No proof of absent late writes follows from cancelled.

Lifecycle is a separate release prerequisite, not a confirmed compatibility defect: owner197-221 uses async `apply`, adds `ctx.on('dispose', dispose)` only after the listen await, and returns a teardown function. Retained app-boot explicitly permits tree disposal during startup (959-962,1161-1162), but delegates plugin semantics to external Cordis/Loader. It does not establish whether this exact Cordis version accepts returned async-apply disposers, invokes late dispose listeners, or automatically retires a resource acquired while activation is being cancelled. No retained core implementation supporting those details was supplied or located in the reviewed package. Therefore neither normal runtime teardown nor disposal during the listen await can be declared compatible from these captures alone. Before installation, inspect the exact installed lifecycle implementation and verify normal disposal, disposal before listen resolves, and injection withdrawal. Adapt to that supported resource mechanism if needed.

The newer `vm105-native-composition-source-2026-09-09.json` establishes base row id `credentials` at source85-86 and zero authorization literal matches in that base patch. It explicitly does not prove the effective mounted services or store configuration. An authorization declaration elsewhere in the frozen fallback graph does not change that limit. The bridge's native begin API has no store-path argument.

## Remaining spec and quality checks

| Area | Offline inspection result |
| --- | --- |
| Passive lifecycle and consumed attempt | Owner69-153 does not begin on load/connect; exact begin consumes the one connection/attempt; reconnect and repeated begin cannot retry. Authentication is owner-client initiated. Runtime lifecycle caveat above remains. |
| Private schemas and limits | Owner10-40,137-146 bounds JSON frames to16KiB UTF-8 bytes, rejects malformed UTF-8/unknown fields, correlates one outstanding integer ID and limits answers to4096 bytes. Output queues are capped at64KiB and false write returns fail closed. Prompt/session deadlines are180/1200 seconds. |
| Native browser/device selection | Owner50-57 restricts a native selection containing browser/device_code to device_code server-side; owner143-144 accepts only remaining options. Client independently rejects browser IDs. Browser-only choices fail closed. Other ordinary selections remain supported. |
| Signal, decline, notify and errors | Owner99-121 keeps native prompt signal local, withdraws/rejects with fixed errors, returns a Promise and catches synchronous notice failures. Cancel/decline abort rather than imitate the native decline class. No throwing settlement listeners or settings writes were introduced. |
| Terminal rendering/input | Terminal9 escapes terminal control and bidi formatting characters. All prompt input uses hidden raw input; success, withdrawal, cancellation, socket failure and handled process signals flow through restoration. TTY refusal cannot prove an unrecorded human-only terminal. Asynchronous output failure is the finding above. |
| Socket ownership and preservation | Owner156-178 verifies Linux parent/ancestor owner/mode/type and holds a directory FD. Owner181-194 checks device/inode before owned unlink; on conflict it retains/unrefs rather than calling Node close against an unknown pathname. No unknown object deletion was found under the stated account trust boundary. Actual Linux bind/connect/close and mode semantics were not executed. |
| Threat boundary and retention | The0700 directory protects against other accounts; same-UID processes and root are outside the claimed exclusion. The report correctly disclaims same-UID TOCTOU protection. Identity-conflict retention leaves resources pending explicit retirement; the bridge has already been disposed so retained connections are rejected. This is an intentional documented limit, not a race-free cleanup claim. |
| Test quality | Covers native request shape, passive start, single attempt, malformed/oversized messages, device restriction, cancellation, signal withdrawal, safe notices, backpressure, simulated socket metadata and terminal conversations. Fake socket close and filesystem tests cannot establish libuv/Linux cleanup or Cordis lifecycle. Async output error coverage is missing as described above. |

## Acceptance boundary

Repair the terminal error path and obtain parent verification of the new frozen files before offline acceptance. Do not infer installation authorization or runtime readiness from an offline verdict. Effective candidate `.credentials.yaml` binding, absence of ambient fallback, complete mounted graph, Cordis lifecycle, Linux socket behavior, private owner terminal use, native device eligibility/connectivity/consent/commit and all three model routes remain NOT PROVEN. Pilot cutover status is unchanged. The available implementation remains device-only; browser mode needs its separate proven callback requirements.

## Repair round 1 independent re-review

20260909 041449 Asia/Bangkok. Scoped repair review - 01/01 finding addressed. This section supersedes the initial CHANGES REQUIRED verdict for the terminal defect; the historical finding remains above. **Offline spec verdict: PASS for the reviewed implementation contract, subject to the unchanged installation/runtime prerequisites. Quality verdict: PASS; no new substantive defect found in this repair.** Cordis lifecycle compatibility remains NOT PROVEN and is a separate source follow-up, not a closed prerequisite.

Read `.superpowers/sdd/native-owner-bridge/fix-round-1.md`, the updated implementation report, the repaired terminal error/cleanup flow and the new regression check. Direct SHA256 checks match the new freeze:

| File | SHA256 |
| --- | --- |
| `scripts/native-codex-owner.mjs`, unchanged | `90bb452d25d5b6c7c7593e2cfc7c01650069d1d63f4770728bff5ef32935b14b` |
| `scripts/native-codex-terminal.mjs` | `9e9bf70f8c6e4088f66ac573ce2bf89a60971d30b4f9ea3000aface4af33b458` |
| `scripts/native-codex-owner.test.mjs` | `973f22c2e782ac2108d627ed2e843f92cc723337b3895762b1a9b47a2c1a9b23` |

Terminal64 now installs input/output error listeners before any write or prompt. Both call existing sanitized cancellation at59, which reaches the guarded finish58 and release50-54. Release aborts active hidden input, allowing its existing raw-mode restoration, and removes the owned stream listeners at52. The handler ignores the original error value; it never renders its message or stack. Errors outside an active prompt also have the conversation listener. Native protocol, socket ownership and authentication behavior are unchanged.

Test208-225 uses EventEmitter output and covers all four input/output and active/no-active-prompt combinations. It checks safe failure, cancel frame, socket destruction, raw-mode restoration, listener cleanup and raw-error redaction. The preexisting conversation test now also supplies an EventEmitter output, matching the real stream interface. These changes directly cover the reported defect without broadening the implementation. The parent reports an independent 16/16 PASS run; this reviewer did not rerun tests and does not label that result as reviewer execution.

No implementation edits, new investigations outside the fix, live actions, credentials, network, browser, SSH, package/profile changes, staging or commits occurred. Parent acceptance and the separate Cordis/Linux/store/authentication release gates remain in force.
