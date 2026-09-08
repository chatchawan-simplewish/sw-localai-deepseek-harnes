# Native bridge Linux launcher: offline implementation

Repository: https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git. Implementation only; no SSH, namespace, VM file, service or authentication action performed by this worker.

Owned file: `scripts/Test-VM105NativeBridgeLinux.py`.
Frozen SHA256 after scoped privilege-bit correction: `3fa388c3fbdb0ed48b368c63114a16940c87312ad661147aed062ca384ff688a`.

Default prints CONTRACT_ONLY. `--self-test` runs local schema/hash guards. `--execute --reviewed-sha256 <exact launcher digest>` requires matching launcher and all three source/inspector hashes before starting strict SSH. A matching argument is an assertion, not independent approval. Parent must obtain exact composed-bundle review before release.

The root Python3.12 wrapper reuses the pinned existing Inspection class to hold/trust/check `/run` and pinned Node ancestors/inode, rejects ACL/capability metadata, verifies the executable hash twice, and executes the held inode with `execve(fd)`. It refuses unsupported unshare/network namespace/FD execution/wait primitives. Exclusive `/run/dsh-native-bridge-check-20260909-a1` creation spends the path; existing state is refused. Public source files are retained root-owned0444 beneath root-owned0555 `src`; fresh root is dsh-owned0700. No deletion or replay exists.

The child starts a new session, acknowledges it before parent release, enters a new network namespace, drops supplementary groups and root identity, uses a clean environment, and runs only the reviewed synthetic fixture. The fixture's same-Node subprocess remains in this session. The wrapper observes exit using WNOWAIT, kills only the owned group while its leader remains unreaped (reserving PGID), then reaps the direct child. Before acknowledgement it can kill only the still-unreaped direct child. Thirty-second test deadline, forty-second overall remote alarm and five-second cleanup reserve; SSH waits fifty seconds plus bounded local thread/kill reserves. Child output is capped at4096 bytes; stderr stays inside that capture, and neither raw output nor raw exceptions are emitted. Receipt exposes only fixed status/checks and owned artifact metadata/hashes.

Offline checks: SELF_TEST_PASS; BUNDLE_PINS_PASS against actual three fixture/bridge source files and unchanged inspector; default CONTRACT_ONLY; invalid reviewed digest LOCAL_CHECK_FAIL before SSH. No runtime Linux/process-group/namespace claims are made from these checks.

Limits: isolation removes external networking, not filesystem access. Reviewed synthetic code runs as existing dsh; malicious concurrent same-UID mutation is outside this account boundary. Source-only module review remains necessary. Descendants must not detach into another group/session; current fixture uses inherited process group. Cleanup proves the direct child reaped, not independently enumerated descendant reaping. No real Cordis/provider/credential/home is loaded by the fixture. Linux execution, native owner authorization, provider acceptance and service cutover remain NOT PROVEN.

Frozen bundle pins are embedded in the launcher: owner90bb452d25d5b6c7c7593e2cfc7c01650069d1d63f4770728bff5ef32935b14b; terminal9e9bf70f8c6e4088f66ac573ce2bf89a60971d30b4f9ea3000aface4af33b458; fixture6f82e2f2783123255f9e441cde991da2bdcbddbf92bd9f4dc6cc7e1b12cc1414; inspectorfcddc77c890b289e28c609fa30b3b41f6c060a73c5c4ea3ab69b468a130df424; Nodebc17c508ffeed0ec622934f9b7fa72f8e78da65350e63c3eceb56fa688aa5e12.

Scoped review correction: held Node metadata now rejects either setuid or setgid before fork. Existing double digest and complete held-inode/path metadata drift checks remain unchanged. The shared mode guard's offline regression accepts ordinary0755 and rejects04755 and02755 with fixed NODE_PRIVILEGED_MODE. Updated SELF_TEST_PASS observed; no SSH action. Other implementation and bundle pins unchanged.

Ownership relinquished for scoped independent re-review; no live release granted by this report.
