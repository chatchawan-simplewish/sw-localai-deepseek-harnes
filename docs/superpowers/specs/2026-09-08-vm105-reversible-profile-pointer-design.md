# VM105 reversible profile-pointer design

Date: 2026-09-08
Repository: `chatchawan-simplewish/sw-localai-deepseek-harnes`
Target: Prox-01 VM105, `deepseek-harness-01`
Status: approved design; secret-free preparation authorized; cutover remains separately gated

## Goal

Prepare a fresh, owner-only DeepSeek Harness profile at
`/home/dsh/.dsh-profiles/vm105-provider-v1` and later replace the current
service profile through a reversible pointer change. This workflow never writes,
moves, or deletes the provenance-uncertain profile and fails closed unless the
installed Harness version exposes a supported profile-selection mechanism that
isolates the entire Harness profile.

## Non-goals

This work does not:

- read, copy, move, overwrite, quarantine, back up, restore, or delete the
  existing profile or any secret-bearing file beneath it;
- create a shadow Harness instance or run both profiles at once;
- create provider credentials, API access, OAuth grants, login sessions,
  consent records, or native Codex authentication;
- enter, display, log, hash, measure, transmit, or otherwise inspect a secret;
- run inference, provider connectivity, invalid-credential, fallback, or
  attribution tests;
- add firewall rules, expose TCP 3080 beyond loopback, install packages, change
  VM power state, restart services, enable routes, or perform cutover during
  preparation;
- inspect, change, or rely on Hermes/VM104 credential stores; or
- retire the old profile after a successful future switch.

The profile switch does not resolve the native Codex login blocker or any
provider-route blocker. Those remain independent prerequisites.

## Current evidence and problem

VM105 currently runs `deepseek-harness.service` as `dsh:dsh`, serving HTTP on
loopback port 3080. Historical planning expected `DSH_HOME=/home/dsh/.dsh` and
`UMask=0077`, but neither effective unit fact is tracked proof. Both are
`NOT PROVEN` until fresh sanitized selector discovery records them without
opening profile contents. The existing path contains provenance-unverified
state, so its ownership and restrictive modes do not prove that it is fresh or
VM105-specific.

The Phase 3 owner-entry packet also records:

- the exact effective credential store is not proven without inspecting
  provenance-uncertain state;
- the installed Models draft does not expose a supported native Codex login
  control or safe configured-state indicator;
- six of nine requested provider routes remain blocked;
- OpenRouter Auto, OpenRouter Pareto Code, and Typhoon text need no inbound
  firewall change, but their credential and runtime behavior remain unproven;
- no firewall rule was released, no credential/OAuth gate was presented, and
  all provider responses and inference remain `NOT PROVEN`; and
- `/home/dsh/.dsh/phase-03-provider-backup-20260908T110706` is an empty
  owner-only directory, not a backup of credential state.

The problem is not file permission alone. It is missing provenance and an
unproven profile-selection interface. A fresh profile provides a clean
provenance boundary only if the installed Harness version officially supports
selecting it without altering or interpreting the current profile.

## Design principles

1. **Preserve uncertain state.** Treat the current profile as an opaque object.
2. **Use one supported seam.** The only allowed pointer is the minimum
   profile-selection mechanism supported by the installed Harness version. It
   must isolate every mutable Harness store, not a credential-only or
   settings-only subset.
3. **Separate preparation from cutover.** Preparation is secret-free and
   static. Runtime proof requires a separately approved maintenance restart.
4. **Fail closed.** Missing, ambiguous, deprecated, or content-dependent
   selector behavior blocks work; no wrapper, symlink, package change, copied
   config, or guessed environment variable substitutes for proof.
5. **Keep network posture unchanged.** The candidate remains loopback-only,
   exposes zero active provider routes, and disables automatic fallback.
6. **Retain rollback.** The prior service pointer and old profile root remain
   available after success. Destruction is never part of this design.

## Architecture and boundaries

### Existing profile boundary

The provenance-uncertain profile under `/home/dsh/.dsh` is opaque; whether it is
the effective service profile is `NOT PROVEN` until selector discovery. No
content read, child traversal, or copy is permitted. Inspection of that tree is
limited to `lstat`-equivalent metadata on the root path itself: path, object
type, owner, group, mode, and link status. Preservation evidence is limited to
that permitted root metadata, proof that the service selector is detached after
cutover, and an operation ledger showing this workflow issued no write, move, or
delete against the old tree. It does not claim byte identity or full-tree proof.

### Selector-discovery boundary

Discovery examines only installed-version help, package-shipped documentation,
package metadata, and the effective systemd unit definition. It must establish
all of the following without opening profile contents:

- the exact supported selector and its precedence;
- that it isolates the entire Harness profile, explicitly including
  credentials, settings, plugins, sessions/state, and every other mutable store,
  rather than selecting only credentials/settings, a working directory, or a
  cache;
- that an absolute path is accepted;
- that selection does not merge with, inherit from, migrate, or rewrite the
  current profile;
- that the selector is usable by `deepseek-harness.service` as user `dsh`; and
- that the chosen unit override is the minimum supported systemd drop-in or
  equivalent supported selector.

The specification intentionally gives no selector syntax. Syntax becomes
eligible for an implementation plan only after direct proof against the
installed Harness version. If any condition is unproven, the outcome is
`BLOCKED` and no profile directory or service change follows. A selector that
covers credentials and settings but not plugins, sessions/state, or any other
mutable store is insufficient and `BLOCKED`.

### Fresh profile boundary

After selector proof, preparation may create exactly
`/home/dsh/.dsh-profiles/vm105-provider-v1` and its required parent. Content is
derived only from installed Harness defaults and settings explicitly approved
for this project. Nothing is seeded from the old profile.

The static configuration must encode or preserve:

- bind host `127.0.0.1` and port `3080` through the existing service command;
- zero active provider routes and automatic fallback disabled;
- no provider/model selection, provider credentials, native OAuth state, or
  account identities; provider/model selection is deferred to the separate
  later credential/route gate;
- no Hermes/VM104 references or inherited paths; and
- no setting that broadens network, filesystem, process, or identity access.

The preparation lane cannot start Harness against the new profile. Without a
shadow instance, static checks establish only configuration eligibility; runtime
readiness remains `NOT PROVEN`.

### Service-pointer boundary

The future switch changes only the proven profile selector in the systemd
service configuration. Fresh sanitized discovery must first prove the effective
unit facts; only the verified service identity, command, loopback endpoint,
working directory, restart policy, hardening, and network policy may be held
unchanged. Any additional change is a material departure and requires a revised
design and approval.

## Components

| Component | Responsibility | Permitted dependency | Forbidden dependency |
| --- | --- | --- | --- |
| Installed Harness evidence | Prove selector syntax, precedence, and isolation of the entire mutable profile | Installed help/docs/package metadata | Current profile contents or online package changes |
| Fresh profile root | Hold all fresh VM105-specific mutable Harness stores; it begins secret-free and receives credentials only through a later gate | Installed defaults and approved explicit settings | Existing profile, Hermes, copied credentials, inferred values |
| Static validator | Check path, ownership, modes, syntax, loopback, zero-route and fallback-disabled policy | Newly created secret-free candidate files and metadata | Running Harness, provider calls, old-profile content, secret output |
| Service-pointer drop-in | Select the fresh profile during approved cutover | Proven supported selector and existing unit | Wrapper scripts, symlinks, guessed selectors, broad unit rewrite |
| Cutover controller | Stop, switch, start, verify, and roll back on failure | Separately approved exact change packet | Credential entry, provider enablement, unrelated repair |
| New reviewed evidence record | Store this workflow's commands, safe metadata, verdicts, mutation ledger, and rollback result while pre-existing baseline artifacts stay unchanged | Redacted nonsecret outputs | Changes to existing evidence artifacts; secret values, hashes, lengths, fragments, OAuth URLs/codes |

## Exact state and data flow

### Preparation flow

1. Revalidate VM105 identity and the existing service baseline without mutation.
2. Inspect installed-version sources and effective unit metadata within the
   selector-discovery boundary.
3. Record the selector contract or record `BLOCKED` with the exact missing
   proof. Do not guess or install an alternative.
4. Only after selector proof, create the dedicated parent/profile paths with the
   required owner and modes.
5. Materialize the minimum secret-free profile from installed defaults and
   explicitly approved settings.
6. Run static validation and record `PASS`, `WARN`, `BLOCKED`, and
   `NOT PROVEN` findings.
7. Stop. Do not point the service at the candidate and do not restart it.

No data flows from the current profile to the candidate. The only allowed
inputs are installed-version evidence, freshly captured sanitized unit/selector
metadata, approved settings, and the fixed profile path.

### Future cutover flow

Cutover begins only after separate action-time approval of an exact packet and
a bounded maintenance interruption:

1. Revalidate VM identity, service baseline, local tunnel assumptions, UFW, and
   direct-LAN denial.
2. Record the effective current selector metadata and the exact rollback
   operation without reading profile content.
3. Revalidate the candidate profile's owner, modes, static policy, and absence
   of credential material.
4. Stop `deepseek-harness.service` once.
5. Confirm the service is stopped. Only then capture the old profile root's
   `lstat` baseline: path, object type, owner, group, mode, and link status. Do
   not traverse children or read content. This post-stop, pre-pointer record is
   the only old-root comparison baseline used for cutover acceptance.
6. Apply the minimal pre-reviewed pointer drop-in and reload systemd.
7. Start `deepseek-harness.service` once.
8. Verify every cutover check before accepting the switch.
9. If any check fails or is ambiguous, restore the prior pointer, reload,
   restart once, and verify the original baseline.
10. If all checks pass, retain the old profile root, confirm the operation ledger
   contains no old-tree mutation, and stop before any credential/API access
   creation, OAuth/login/consent, or sensitive entry.

No old-root metadata captured while the service is running may substitute for
the post-stop, pre-pointer baseline. This ordering prevents a shutdown-time
comparison race while keeping inspection within the root-only `lstat` boundary.

## Permission and mode expectations

| Path or object | Owner | Required mode or control |
| --- | --- | --- |
| `/home/dsh/.dsh-profiles` | `dsh:dsh` | `0700`; real directory; not a symlink |
| `/home/dsh/.dsh-profiles/vm105-provider-v1` | `dsh:dsh` | `0700`; real directory; not a symlink |
| Secret-free configuration files | `dsh:dsh` | `0600` or narrower; regular files; no hard/symbolic links |
| Future credential files, if separately authorized | `dsh:dsh` | `0600` or narrower under protected parents; never created by this preparation |
| Systemd drop-in directory/file | `root:root` | directory `0755`, file `0644`; file contains selector metadata only, no secret |
| Harness service process | `dsh:dsh` | live process identity is tracked; effective `UMask` and unit hardening are `NOT PROVEN` until fresh sanitized discovery, then verified facts remain unchanged |

Every ancestor used by the candidate must prevent unintended write access.
Unexpected owners, group/world write, symlinks, hard links, mounts, ACLs that
broaden access, or an already-populated target produce `BLOCKED`. Preparation
must not repair an unexpected condition automatically if doing so could alter
pre-existing state; it records the discrepancy and stops.

## Cutover and rollback state machine

| State | Entry condition | Allowed action | Success transition | Failure transition |
| --- | --- | --- | --- | --- |
| `CURRENT_ACTIVE` | Existing service baseline verified | Read-only discovery; after selector proof, bounded writes only to the new candidate path and new reviewed evidence record | `CANDIDATE_STATIC_PASS` | `BLOCKED`, with the original service still active |
| `BLOCKED` | Selector, path, permission, scope, or baseline proof fails | Record exact nonsecret blocker | `CURRENT_ACTIVE` only after a reviewed replan or corrected prerequisite | Remain `BLOCKED` |
| `CANDIDATE_STATIC_PASS` | Selector proven; candidate secret-free; static checks pass | Await separate cutover approval | `CUTOVER_APPROVED` | `BLOCKED` if state drifts, with the original service still active |
| `CUTOVER_APPROVED` | Owner approves exact action-time cutover packet | Revalidate all inputs without stopping the service | `CUTOVER_REVALIDATED` | `BLOCKED`, with the original service still active |
| `CUTOVER_REVALIDATED` | Every pre-stop check passes and the original service is still active | Stop the service once | `SERVICE_STOPPED` | `ROLLBACK_REQUIRED` |
| `SERVICE_STOPPED` | Service stop is confirmed and prior pointer metadata is recorded | Capture only the old-root `lstat` fields | `OLD_ROOT_BASELINED` | `ROLLBACK_REQUIRED` |
| `OLD_ROOT_BASELINED` | Root-only `lstat` baseline is captured after stop and before pointer application | Apply the reviewed pointer | `POINTER_APPLIED` | `ROLLBACK_REQUIRED` |
| `POINTER_APPLIED` | Exact pointer is installed and systemd reload succeeds | Start service | `CANDIDATE_RUNNING` | `ROLLBACK_REQUIRED` |
| `CANDIDATE_RUNNING` | Service starts against candidate | Run full cutover verification | `SWITCH_ACCEPTED` | `ROLLBACK_REQUIRED` |
| `ROLLBACK_REQUIRED` | Any command, check, timeout, identity, or ambiguity fails | Restore prior pointer, reload, restart, verify baseline | `ROLLED_BACK` | `ROLLBACK_FAILED` |
| `ROLLED_BACK` | Original baseline is restored | Record failure and stop | Terminal safe state | `ROLLBACK_FAILED` |
| `ROLLBACK_FAILED` | Original baseline cannot be restored | Stop mutations, preserve evidence, escalate immediately | Terminal incident state | Terminal incident state |
| `SWITCH_ACCEPTED` | All checks pass | Record selector detachment and the empty old-tree mutation ledger | `CREDENTIAL_GATE` | `ROLLBACK_REQUIRED` if acceptance evidence is invalidated before handoff |
| `CREDENTIAL_GATE` | Candidate is active and this workflow recorded no old-tree mutation | Stop and request the existing Phase 3 credential gate | Terminal for this design | No credential action |

No state permits automatic retries beyond the one explicit rollback sequence.
The controller never proceeds past an ambiguous result.

## Error handling and fail-closed gates

- **Unsupported selector:** `BLOCKED`; no workaround, wrapper, symlink, package
  install, or current-profile inspection.
- **Selector scope unclear:** `BLOCKED`; a home/cache/workspace selector is not
  accepted as a full profile selector without direct proof.
- **Existing target or unexpected content:** `BLOCKED`; do not delete, move,
  rename, inspect, or adopt it.
- **Unsafe ownership, mode, ACL, mount, or link:** `BLOCKED`; do not normalize
  potentially pre-existing state without a reviewed repair packet.
- **Baseline drift:** `BLOCKED`; do not cut over until the exact changed state is
  independently reviewed.
- **Static validation warning affecting isolation or rollback:** treat as
  `BLOCKED`, not merely `WARN`.
- **Service stop/start, pointer, reload, identity, listener, health, UFW,
  routing, ownership, or effective-profile failure:** enter
  `ROLLBACK_REQUIRED` immediately.
- **Rollback verification failure:** enter `ROLLBACK_FAILED`; stop all changes
  and report the incident. Do not attempt speculative repair.
- **Credential/native OAuth prompt encountered:** stop before interaction. Do
  not click, consent, paste, type, capture, or continue.

## Verification plan and verdicts

Verdicts have fixed meanings:

- `PASS`: directly observed evidence satisfies every listed criterion.
- `WARN`: a bounded non-blocking concern exists and does not weaken isolation,
  security, reversibility, or acceptance.
- `BLOCKED`: a required fact or safety condition is absent, ambiguous, or
  failed; dependent work stops.
- `NOT PROVEN`: the behavior cannot be established in the current lane, such as
  runtime behavior before cutover or provider behavior before credentials.

### Preparation checks

1. VM identity is exactly `deepseek-harness-01`; service user/group remain
   `dsh:dsh`; current service stays active and unchanged.
2. Installed-version evidence proves the full selector contract described
   above. Absence of proof is `BLOCKED`.
3. Candidate path and ancestors are new or explicitly proven empty, owned by
   `dsh:dsh`, mode `0700`, and free of links, broad ACLs, or unexpected mounts.
4. Candidate regular files are owned by `dsh:dsh` and mode `0600` or narrower.
5. A value-suppressing scan may read only newly created candidate files already
   generated as secret-free inputs. It confirms no credential field contains a
   value, no OAuth state is present, and no secret-shaped material is recorded,
   while reporting only file paths and rule verdicts. It never reads the old
   profile and never emits matching values.
6. Static configuration proves loopback-only intent, zero active provider routes,
   and automatic fallback disabled. Provider/model selection remains deferred
   to the separate credential/route gate. Unsupported static validation is
   `NOT PROVEN` unless it affects safety, in which case it is `BLOCKED`.
7. The verified current service process, listener, UFW rules, and direct-LAN
   denial remain unchanged after preparation. Fresh sanitized discovery records
   unit facts without treating historical `DSH_HOME` or `UMask` values as proof.
8. Pre-existing tracked baseline and evidence artifacts remain unchanged; this
   workflow may add one new independently reviewed evidence record.
9. No package, firewall, service, VM power, route, provider, credential, OAuth,
   or old-tree mutation appears in the operation ledger.

Preparation may end `PASS` for candidate eligibility while runtime, provider,
credential, and native OAuth behavior remain explicitly `NOT PROVEN`.

### Cutover checks

The future exact packet must verify, in order:

1. hostname and VM identity;
2. service process identity `dsh:dsh` and expected unit;
3. effective profile selector resolves exactly to
   `/home/dsh/.dsh-profiles/vm105-provider-v1` for credentials, settings,
   plugins, sessions/state, and every other mutable store, without merging or
   fallback;
4. listener is only `127.0.0.1:3080` or the already-approved equivalent
   loopback sockets;
5. local HTTP health succeeds through the established loopback path;
6. UFW remains active with no new TCP 3080 allowance;
7. direct LAN access to TCP 3080 remains denied;
8. zero provider routes are active and automatic fallback remains disabled;
9. candidate path ownership, modes, ACLs, links, and mounts remain compliant;
10. permitted old-root `lstat` metadata matches the pre-cutover record, the
    selector is detached from that root, and the mutation ledger contains no
    write, move, or delete against the old tree; and
11. no credential, OAuth, provider, inference, or route mutation occurred.

Acceptance requires every check to be `PASS`. `WARN`, `BLOCKED`, timeout, empty
output, or an unrecognized result triggers rollback.

## Threat and risk register

| Risk | Failure mode | Impact | Control | Residual verdict before cutover |
| --- | --- | --- | --- | --- |
| Secret disclosure | Old profile contents are opened, copied, logged, hashed, or characterized | Credential exposure and provenance loss | Opaque-profile boundary; permitted root `lstat` only; value-suppressing scan only on new candidate files | `BLOCKED` if boundary cannot be honored |
| Selector spoofing | Guessed syntax points elsewhere or falls back to the old profile | Mixed identity and false isolation | Installed-version proof; exact effective-profile verification | `NOT PROVEN` until selector discovery passes |
| State merging | Harness imports, migrates, or continues using any old mutable store | Inherited credentials/state and false isolation | Prove entire-profile isolation across credentials, settings, plugins, sessions/state, and all other mutable stores; stop on partial selection or migration behavior | `BLOCKED` unless disproved |
| Permission escalation | Broad modes, ACLs, links, mounts, or wrong owner expose the candidate | Unauthorized read/write | 0700 parents, 0600 files, link/ACL/mount checks, `dsh:dsh` runtime | `NOT PROVEN` until static checks pass |
| Network exposure | Pointer change alters bind address or firewall posture | LAN/public access | Preserve command; verify loopback, UFW, direct-LAN denial; immediate rollback | `NOT PROVEN` until cutover |
| Denial of service | Service fails to restart against candidate | Maintenance outage | Bounded window, recorded prior pointer, automatic rollback and baseline check | Brief outage remains possible |
| Rollback failure | Prior pointer cannot be restored | Extended outage | Pre-record exact rollback; verify before stop; fail as incident without improvisation | Low probability, high impact |
| Route ambiguity | Candidate defaults enable a provider route or fallback | Misattribution and unintended spend | Require zero active routes and fallback disabled; defer provider/model selection; no credentials or inference | Provider behavior remains `NOT PROVEN` |
| Native Codex substitution | API key is used where native OAuth is required | Wrong identity and unsupported route | Separate native-login prerequisite; API-key substitution forbidden | `BLOCKED` |
| Evidence leakage | Logs or repository capture secret-derived data | Persistent disclosure | Record only safe metadata and verdicts; existing evidence scanner | `BLOCKED` on any unsafe output |
| Scope creep | Package, firewall, VM, service, or provider changes are bundled | Unreviewed operational risk | Exact-path/action allowlists and separate approval gates | `PASS` only with zero out-of-scope changes |

## Authority matrix

| Action | Preparation authority | Future cutover authority | Credential authority |
| --- | --- | --- | --- |
| Read installed help/docs/package metadata | Allowed, read-only | Allowed for revalidation | Not applicable |
| Read effective nonsecret systemd pointer metadata | Allowed, read-only | Allowed and required | Not applicable |
| Read or copy current profile content | Forbidden | Forbidden | Forbidden by this design |
| Create fresh profile root after selector proof | Allowed within exact path | Already completed or revalidated | Not applicable |
| Write secret-free candidate settings | Allowed after selector proof | Only exact reviewed repair if needed | No secret entry |
| Start a shadow instance | Forbidden | Forbidden | Forbidden |
| Stop/restart service or apply pointer | Forbidden | Requires separate action-time cutover approval | Not implied |
| Install or update packages | Forbidden | Forbidden without a new approved design | Forbidden |
| Change firewall, routes, VM power, service identity, or listener | Forbidden | Forbidden | Forbidden |
| Create API access, initiate OAuth/login/consent, or type secrets | Forbidden | Forbidden; stop after successful switch | Requires the existing separate Phase 3 owner gate |
| Delete or retire old profile | Forbidden | Forbidden after success | Requires separate irreversible-action authorization |
| Automatic rollback after an approved cutover check fails | Not applicable | Required and pre-authorized as part of the exact cutover packet | Not applicable |

Approval of this specification and implementation start authorizes only
secret-free discovery and preparation. It does not authorize cutover or any
credential-bearing action.

## Test and acceptance criteria

### Specification and implementation-plan acceptance

- The selector is a discovery gate, not invented syntax.
- Every preparation and cutover action has an exact owner, target, precondition,
  verification, failure state, and rollback boundary.
- The current profile is never a data source; verification is limited to its
  permitted root `lstat`, selector detachment, and the mutation ledger.
- No shadow instance or in-place overwrite exists in the design.
- Cutover and credential work are independent explicit gates.
- Native Codex login and all provider-route blockers remain independently
  tracked.
- Repository scans find no unfinished markers, secret material, or ambiguous
  authorization.

### Preparation implementation acceptance

- Selector proof directly covers absolute path, precedence, full-profile scope,
  non-merge behavior, service compatibility, and supported systemd use. Full
  profile scope explicitly covers credentials, settings, plugins,
  sessions/state, and every other mutable store; partial selection is
  `BLOCKED`.
- If selector proof fails, evidence says `BLOCKED` and VM105 has no new profile
  or service change.
- If selector proof passes, only the fixed fresh path and minimum secret-free
  files are created, with verified owner, modes, ACL/link/mount safety.
- Static validators pass and leave one runnable regression check for the
  non-trivial safety rules.
- The existing service remains active on loopback with its pointer unchanged;
  no restart, provider call, inference, credential, OAuth, firewall, package,
  route, or power action occurs.
- Evidence distinguishes preparation `PASS` from runtime/provider
  `NOT PROVEN`.

### Future cutover acceptance

- The owner separately approves the exact cutover packet at action time.
- The maintenance restart is bounded to one switch attempt plus one automatic
  rollback attempt if required.
- After the service stop is confirmed and before the pointer is applied, the
  controller captures exactly one root-only old-profile `lstat` baseline for
  cutover comparison.
- All ordered cutover checks pass, including effective-profile proof and
  unchanged network posture.
- Any non-pass result restores the prior pointer and original baseline or is
  reported as `ROLLBACK_FAILED` without speculative repair.
- Success records no old-tree mutation by this workflow and stops at
  `CREDENTIAL_GATE`; it does not claim a full-tree comparison.

## Impact, cost, and downtime

- **Preparation impact:** one new protected profile tree and secret-free static
  files only after selector proof; no intended service or network impact.
- **Storage cost:** negligible local disk use for one configuration profile.
- **Operational cost:** selector discovery, independent review, static
  validation, and a later controlled cutover/rollback review.
- **Provider cost:** zero during preparation and cutover because no credentials,
  routes, or inference are used.
- **Downtime:** zero during preparation. The later cutover includes a brief
  maintenance interruption for stop, pointer application, start, and checks;
  failure adds one rollback restart. No zero-downtime guarantee is claimed.
- **Rollback impact:** the service returns to the prior pointer; the fresh
  candidate remains for diagnosis, and this workflow issues no old-tree write,
  move, or delete.

## Explicit unresolved facts

The following are deliberately unresolved and must not be inferred from this
design:

1. The installed Harness version's exact supported profile-selector syntax,
   precedence, full-profile scope, and non-merge semantics.
2. The exact systemd drop-in key/value that would implement the proven selector.
3. Runtime startup and health against the fresh profile; no shadow instance is
   allowed, so these remain `NOT PROVEN` until cutover.
4. The fresh profile's final effective credential, settings, plugin,
   session/state, and other mutable-store paths; they depend on full-profile
   selector proof and static initialization behavior.
5. A supported native Codex login surface and safe configured-state indicator.
6. Provider account/project identities, least-scope credential identifiers and
   lifetimes, and owner-only issuance outcomes.
7. The six currently blocked provider-route prerequisites, including the local
   worker and Typhoon OCR paths and native Codex routes.
8. All provider connectivity, responses, invalid-credential behavior,
   inference, fallback resistance, and attribution.
9. The exact maintenance duration; it can be bounded procedurally but measured
   only during an approved cutover.

Each unresolved fact maps to `BLOCKED` or `NOT PROVEN`; none is an implicit gap or
implicit permission to broaden the implementation.
