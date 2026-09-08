# Bounded Linux native-bridge verification

Routine verification design, not an execution release. Repository: https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git. Preserve the usable VM105 pilot, both Harness homes and every spent gate.

## Purpose and fixed scope

The new bridge passed Windows fake-service checks but its real Linux Unix-socket bind,0600 mode, descriptor alias and owned cleanup are unproven. Run a single independently reviewed synthetic test of the final frozen bridge with fake authorization and credentials services. Never load a provider adapter or invoke real authentication. This is a concrete changed-implementation reason for a new test, not a repeat of a consumed smoke/preflight gate.

Use the existing strict SSH identity and verified root Python3.12 only as a bounded test launcher. The test child runs as dsh, with a new isolated network namespace, sanitized environment and pinned Node executable. No systemd units, service controls, firewall changes, package installs, browser, inference, GPU, host/VM power or current/candidate-profile access. The exact isolation/child-cleanup implementation must be reviewed before execution; unsupported primitives fail closed, never fall back to host networking.

Create only a fresh exact owner-private test root under a verified root-owned non-writable ancestor such as `/run`. Choose/freeze the one-attempt name before execution, refuse existing objects, and retain the test root as evidence afterward. Never use `/tmp` with the bridge's current ancestor policy and never weaken that policy. Only new test-owned public source files and synthetic socket fixtures exist there; no credential or `.env` file is created. Record safe modes/inodes/hashes for owned artifacts. No recursive cleanup; retaining harmless private fixtures avoids deleting unknown state.

Deliver exact reviewed bridge, terminal and one small Linux fixture as a bounded hash-checked bundle. The fixture uses Node stdlib only and a fake context; output only fixed check names, booleans/counts and fixed failure codes. Raw protocol frames, inputs and errors are never emitted. Give the child30 seconds, the remote wrapper a bounded cleanup reserve, and the SSH parent a bounded whole-attempt timeout. Retain and terminate only the exact owned child on failure, with no broad PID controls or retries.

## Native checks

1. Passive apply binds a real0600 Unix socket beneath0700 parent; connection alone calls no fake begin.
2. Explicit synthetic begin, notice, native device-only choice and synthetic result traverse the real socket. This result is labelled fake authorization and proves no real native credential commitment.
3. A fresh fixture's disconnect aborts pending fake input. Disposal removes its owned socket and releases handles within the deadline.
4. Pre-existing fixture paths are refused and preserved. A deliberate owned-fixture replacement is preserved by bridge disposal and still exists after child exit, checking Node automatic-cleanup behavior. Every replacement belongs to this new synthetic test root; no foreign file is changed.

Existing parser/unit checks are not duplicated. This test establishes Linux transport only. Cordis core lifecycle is separately being source-inspected; a later actual Context fixture may reuse the same synthetic services only after its exact provide/activation/disposal API is verified and independently reviewed. No actual credential service, application profile or provider needs to load for either fixture.

## Acceptance and limits

Freeze exact implementation and fixture hashes; obtain independent pre-execution review, then one parent-owned execution and independent receipt review. Failure spends the attempt and leaves exact safe evidence; diagnose without replaying it. Linux PASS never advances a provider requirement, establishes private owner consent, releases the pilot cutover, or clears the Bell-PC2 resource conflict. Complete effective-store and owner-readiness prerequisites separately.
