# Linux bridge a1: offline diagnosis

Repository: https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git. Method: systematic-debugging Phase1, source/retained-receipt analysis. No live read, replay, cleanup, implementation edit or authentication action. The a1 gate remains consumed.

## Conclusion

The exact failing runtime boundary is NOT PROVEN. The receipt is insufficient to distinguish child setup failure, Node startup failure, fixture assertion failure, or parent output validation failure. No transport or namespace success is established. Do not select a functional fix from elapsed time alone.

## What the receipt establishes

`vm105-native-bridge-linux-attempt-a1-2026-09-09.json` binds launcher `3fa388c3fbdb0ed48b368c63114a16940c87312ad661147aed062ca384ff688a`, SSH exit0 and LINUX_CHECK_FAIL to the exact a1 root. Following the frozen source control flow, its three artifact entries/root inode/Node digest are recorded only after bundle validation, root Python/primitives checks, trusted executable double hashing, dsh lookup, exclusive root/source creation, file writes/chmod/fsync, source-directory chmod and root chown complete. The artifact digests describe supplied bytes, not independent readback hashes. Artifact mode strings are fixed receipt values after successful fchmod, not fresh post-child metadata.

`owned_child_reaped:true` establishes fork returned an owned child and cleanup observed its direct waitpid completion. It does not show the original exit status, prove a new network namespace was entered, prove Node exec succeeded, or enumerate descendants. SSH0 means wrapper completion, not successful fixture execution. The reported1.94s elapsed is consistent with an early failure, but no phase timing was retained; it is not a root-cause proof.

## Confirmed diagnostic defect and concrete failure branches

The wrapper catches every remote exception and overwrites it with LINUX_CHECK_FAIL. In particular CHILD_SESSION, CHILD_GROUP, CHILD_EXIT, CHILD_OUTPUT_LIMIT and FIXTURE_RESULT disappear. The child setup handler exits121 without recording which step failed. The parent checks waitid's exit fields but emits neither. It captures fixture stdout/stderr privately, then discards it on any exception. The fixture emits only LINUX_BRIDGE_FAIL for all assertions/rejections. Consequently even the otherwise safe fixed121 exit distinction is lost. This is a source-confirmed observability defect; it is not proof that any specific setup step failed.

The child has concrete unproven operations after the established artifact boundary: setsid and handshake, `unshare(CLONE_NEWNET)`, chdir, supplementary-group/gid/uid changes, resource limits, stdin/output remapping, executable-FD inheritance and execve(fd). Presence of unshare constants proves API availability only, not kernel permission for this invocation. If Node starts, the fixture still has concrete failure points at root policy validation, real bind/chmod, synthetic protocol assertions, disconnect cancellation/disposal, preservation assertions and replacement subprocess startup/natural exit. The retained receipt cannot rank these responsibly.

Full launcher, fixture, implementation report and owner module were read. Their explicit path, filename, JSON status/check names and source pins agree. Source root0700/dsh and source directory0555/root are intentionally distinct and do not by themselves violate the bridge's parent policy, which validates socket root and its ancestors. No definite syntax/schema/path mismatch was identified offline. The previous setuid/setgid correction is present; do not relax it. No speculative functional patch is recommended.

## Minimal next evidence: a separate read-only retained-path diagnostic

Prepare/freeze and independently review one exact bounded metadata reader before any execution. This is not permission in this report to run it or reuse a1. Use the already approved strict SSH identity and root Python; no Node/process execution, namespace action, service operation, scan, socket connect or file mutation. Root and `/run` ancestors must be held nofollow and checked; a1 root inode must equal4078 with dsh0700, otherwise stop with fixed IDENTITY_DRIFT. Preserve all retained objects.

Read only lstat metadata (absent/present, object kind, uid/gid, mode, dev/inode/nlink/size) of a1 root, `src`, the exact three named public source files and these exact synthetic names: `flow.sock`, `disconnect.sock`, `preexisting.sock`, `replacement.fixture`, `replacement.sock`, `retained.sock`. Verify source inode values4080/4081/4082 against receipt. Do not enumerate directories or read socket/marker contents. Reject symlinks and unexpected types without following them. Bound output to fixed keyed JSON below4KiB and deadline10s; no raw exception text. Recheck held/path identities before returning. A future optional exact public-source hash check is separate from metadata and should be explicitly included in that reviewed reader if needed.

Topology can narrow, not always settle, the boundary: preexisting.sock presence means execution reached the marker after owned/disconnect checks; replacement.fixture presence means replacement setup began; regular replacement.sock plus retained.sock socket means replacement child reached rename/disposal phase. Flow/disconnect sockets indicate bind progress when present, but their absence is ambiguous because successful disposal removes them. No synthetic objects leaves child startup versus initial validation versus cleaned-up early flow unresolved. A metadata-only receipt cannot recover discarded child exit/error codes or prove cancellation behavior.

If topology remains ambiguous, preserve NOT PROVEN. Before any separately reviewed fresh-root test, require fixed safe stage/exit telemetry at the launcher/fixture boundaries. That is diagnostic instrumentation, not authorization to rerun a1 or guess a functional repair. No implementation change was made by this diagnosis.
