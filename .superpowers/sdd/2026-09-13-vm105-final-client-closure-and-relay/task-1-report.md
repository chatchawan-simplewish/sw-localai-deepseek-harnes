# Task 1 report — VM105 final client runtime manifest

## Result

- Final post-fix strict read-only SSH capture: **PASS**, 447 packages, 10,026 modules, two accepted entrypoints, three config bundles, and seven Node runtime libraries. The completed 2026-09-13 capture uses held-file pre/post identity checks and a second complete inventory comparison before PASS.
- Independently recomputed canonical manifest SHA-256: `4331e0e5fd9ac6f5e881a0dae941f9f07dea7b69969ee8b610071ce14cb03f8b`. Receipt file SHA-256: `54d117c638335edeefe43aaef0f181ea5317f7938a6861a145871a0d9e45e8dd`. Node SHA-256: `bc17c508ffeed0ec622934f9b7fa72f8e78da65350e63c3eceb56fa688aa5e12`.
- Final GREEN: `python -B -m unittest -v scripts.test_vm105_final_client_transport scripts.test_vm105_final_client_manifest` passed 18 tests in 6.019s (12 manifest, six transport). The final regressions recorded strict RED before implementation, including during-hash drift and between-inventory rewrite/add/remove rejection.

## Scope and limits

The inspector does not invoke JavaScript, a client, a model, or a provider. It only transfers a finite Python inspector through strict batch SSH stdin. The current PASS receipt establishes the captured installed closure; production staging/revalidation, namespace/socket handoff, endpoint/key binding, and live final-client acceptance remain external. Earlier BLOCKED results below are historical and have been superseded by the final PASS capture.

## Fix round 1

- Added pnpm virtual-store sibling dependency resolution, boundary-validated package/artifact handling, manifest-selected Cordis bundle tracing, and `ldd` missing-library rejection with resolved shared-library recording.
- Focused tests: `test_runtime_dependencies_blocks_missing_library` passed. The Windows junction fixture command did not return a final suite summary before the command runner deadline after executing its reported checks; this is a local fixture-cleanup limitation, not a passing claim.
- Repeated strict SSH capture returned exit 0 with the same sanitized `BLOCKED` `DEPENDENCY_UNRESOLVED` receipt and no `modules` array; receipt SHA-256 remains `c2333fff94069b3a910f0e29046a45b678ec5ae3a2bbca25231de33a09fa093c`.

## Fixture portability closeout

Diagnosis: the full suite was not hung. It failed in 0.48 seconds because Windows denied file-symlink creation and the fixture correctly fell back to a hard link. A hard link resolves to its alias path, unlike the retained symlink branch on platforms that permit symlinks. The test now expects `alias.resolve()`.

Command and output: `python -m unittest -v scripts.test_vm105_final_client_manifest` completed in `0.410s`: `Ran 3 tests ... OK`.

## Fix round 2

Implemented scoped and unscoped pnpm sibling dependency lookup, strict package-link and symlink-directory rejection, and extraction only from `dsh.profile.configBundles`; unrelated manifest URLs are ignored. The shared-library fixture uses a real file symlink where permitted and a documented Windows hard-link fallback, which is not represented as a symlink.

`python -m unittest -v scripts.test_vm105_final_client_manifest` output: five named tests all `ok`; `Ran 5 tests in 0.443s`; `OK`.

The required repeated strict SSH capture completed with sanitized `BLOCKED` status and no client/provider/model execution.

Exact verbose unittest output retained for review:
```
test_build_manifest_blocks_dependency_link_escape (scripts.test_vm105_final_client_manifest.FinalClientManifestTests.test_build_manifest_blocks_dependency_link_escape)
Fails if an escaped dependency link is accepted into the closure. ... ok
test_build_manifest_freezes_sorted_closure_and_runtime (scripts.test_vm105_final_client_manifest.FinalClientManifestTests.test_build_manifest_freezes_sorted_closure_and_runtime)
Fails if reachable files, pins, or their stable order are omitted. ... ok
test_dependency_lookup_uses_literal_scoped_and_unscoped_virtual_store_layouts (scripts.test_vm105_final_client_manifest.FinalClientManifestTests.test_dependency_lookup_uses_literal_scoped_and_unscoped_virtual_store_layouts)
Fails if either pnpm package shape resolves dependencies from the wrong sibling directory. ... ok
test_runtime_dependencies_blocks_missing_library (scripts.test_vm105_final_client_manifest.FinalClientManifestTests.test_runtime_dependencies_blocks_missing_library)
Fails if one unresolved ldd library is ignored beside a resolved one. ... ok
test_unrelated_manifest_url_is_not_a_cordis_bundle (scripts.test_vm105_final_client_manifest.FinalClientManifestTests.test_unrelated_manifest_url_is_not_a_cordis_bundle)
Fails if arbitrary metadata strings are mistaken for selected configuration. ... ok

----------------------------------------------------------------------
Ran 5 tests in 0.443s

OK
```

## Fix round 3

RED checks added before production changes: malformed `dsh: null` and `dsh.profile: null` were required to raise `ManifestBlocked`; the runtime fixture was changed from a hard link to a real directory alias whose returned `ldd` file path differs from its canonical target. The previous implementation did not append validated supported symlink artifacts and would dereference malformed configuration.

Exact GREEN output retained:
```
test_build_manifest_blocks_dependency_link_escape (scripts.test_vm105_final_client_manifest.FinalClientManifestTests.test_build_manifest_blocks_dependency_link_escape)
Fails if an escaped dependency link is accepted into the closure. ... ok
test_build_manifest_freezes_sorted_closure_and_runtime (scripts.test_vm105_final_client_manifest.FinalClientManifestTests.test_build_manifest_freezes_sorted_closure_and_runtime)
Fails if reachable files, pins, or their stable order are omitted. ... ok
test_dependency_lookup_uses_literal_scoped_and_unscoped_virtual_store_layouts (scripts.test_vm105_final_client_manifest.FinalClientManifestTests.test_dependency_lookup_uses_literal_scoped_and_unscoped_virtual_store_layouts)
Fails if either pnpm package shape resolves dependencies from the wrong sibling directory. ... ok
test_runtime_dependencies_blocks_missing_library (scripts.test_vm105_final_client_manifest.FinalClientManifestTests.test_runtime_dependencies_blocks_missing_library)
Fails if one unresolved ldd library is ignored beside a resolved one. ... ok
test_selected_bundles_blocks_malformed_dsh_shapes (scripts.test_vm105_final_client_manifest.FinalClientManifestTests.test_selected_bundles_blocks_malformed_dsh_shapes)
Fails if malformed manifest configuration raises AttributeError instead of blocking. ... ok
test_unrelated_manifest_url_is_not_a_cordis_bundle (scripts.test_vm105_final_client_manifest.FinalClientManifestTests.test_unrelated_manifest_url_is_not_a_cordis_bundle)
Fails if arbitrary metadata strings are mistaken for selected configuration. ... ok

----------------------------------------------------------------------
Ran 6 tests in 0.554s

OK
```

The strict read-only capture completed with `BLOCKED`, reason `DEPENDENCY_UNRESOLVED`, no `modules` array, and receipt SHA-256 `c2333fff94069b3a910f0e29046a45b678ec5ae3a2bbca25231de33a09fa093c`. Commit: `d1d0be52b2aec4c510ed6ba403d282458a9ab76f`.

Windows did not permit a file symlink, so the fixture uses an unprivileged real directory junction to the library directory. Its returned alias file path and resolved canonical target differ; no hard link is claimed to be a symlink.

## Fix round 4

RED: new dangling-link regression failed for optionalDependencies and peerDependencies with UNRESOLVED_LINK; required dependency remained blocked. Ran 7 tests in 0.823s, FAILED (errors=2). Windows uses a real dangling junction with link-classification adaptation because symlink privilege is unavailable; Unix uses an actual symlink.

Minimal fix removes the symlink exclusion from the absent dependency branch. Top-level and artifact validation are unchanged.

Complete GREEN output:
```
test_build_manifest_blocks_dependency_link_escape (scripts.test_vm105_final_client_manifest.FinalClientManifestTests.test_build_manifest_blocks_dependency_link_escape)
Fails if an escaped dependency link is accepted into the closure. ... ok
test_build_manifest_freezes_sorted_closure_and_runtime (scripts.test_vm105_final_client_manifest.FinalClientManifestTests.test_build_manifest_freezes_sorted_closure_and_runtime)
Fails if reachable files, pins, or their stable order are omitted. ... ok
test_dangling_dependency_links_skip_only_optional_and_peer (scripts.test_vm105_final_client_manifest.FinalClientManifestTests.test_dangling_dependency_links_skip_only_optional_and_peer)
Fails if absent optional links block closure or absent required links pass. ... ok
test_dependency_lookup_uses_literal_scoped_and_unscoped_virtual_store_layouts (scripts.test_vm105_final_client_manifest.FinalClientManifestTests.test_dependency_lookup_uses_literal_scoped_and_unscoped_virtual_store_layouts)
Fails if either pnpm package shape resolves dependencies from the wrong sibling directory. ... ok
test_runtime_dependencies_blocks_missing_library (scripts.test_vm105_final_client_manifest.FinalClientManifestTests.test_runtime_dependencies_blocks_missing_library)
Fails if one unresolved ldd library is ignored beside a resolved one. ... ok
test_selected_bundles_blocks_malformed_dsh_shapes (scripts.test_vm105_final_client_manifest.FinalClientManifestTests.test_selected_bundles_blocks_malformed_dsh_shapes)
Fails if malformed manifest configuration raises AttributeError instead of blocking. ... ok
test_unrelated_manifest_url_is_not_a_cordis_bundle (scripts.test_vm105_final_client_manifest.FinalClientManifestTests.test_unrelated_manifest_url_is_not_a_cordis_bundle)
Fails if arbitrary metadata strings are mistaken for selected configuration. ... ok

----------------------------------------------------------------------
Ran 7 tests in 1.062s

OK
```

Strict read-only capture stdout/stderr: ''
Receipt: {"reasons": ["UNRESOLVED_LINK"], "status": "BLOCKED", "receiptSha256": "24bdb0ef5e99d84f05da0b743eb1cc631e9e087bf3d2ef47010ee65684be09f0", "exit": 0}

Finite strict read-only diagnostic (in-memory payload only) isolated the remaining unresolved install-relative artifact: {"reasons": ["UNRESOLVED_LINK:@deepseek-ai/dsh-client-ui-settings-models/lib/client.js"], "status": "BLOCKED"}
Fix round 4 commit: fae5143acf9003bf444864a9b96fdc3f0d77c4f3. Remaining path is an accepted entrypoint, so it was not skipped or weakened.


## Fix round 5 (final permitted round)

Read task brief, all prior report sections, test-driven-development/SKILL.md and writing-good-tests.md completely. Base HEAD: fae5143acf9003bf444864a9b96fdc3f0d77c4f3. Only the assigned script, test, evidence, and this report were changed; pre-existing scripts/__pycache__/ remains untouched.

RED: Added real pnpm nested-package fixture coverage plus absent/ambiguous package-name root and accepted SHA mismatch rejection. The old implementation rejected package-name/package-relative tuple pins with AttributeError (9 tests, 1.296s, four errors), demonstrating the unsupported contract. The first GREEN attempt exposed fixture CRLF byte expectations on Windows; the expectation now hashes the actual fixture bytes independently. Production pins retain all five exact accepted SHA values.

Implementation: accepted pins use (package name, package-relative path), resolved after graph traversal against exactly one discovered package row. The resulting entrypoint and bundle rows preserve discovered logical paths and canonical file paths. Missing or ambiguous package-name roots block; digest mismatch blocks. Nested module staging paths retain the complete install-relative logical path; the live receipt has 10,026 unique staged paths. No top-level client package link was created or assumed.

Strict read-only capture: python -B scripts/Build-VM105FinalClientManifest.py --output docs/evidence/vm105-final-client-runtime-manifest-20260913.json. Exit 0, PASS, 447 packages, 10,026 modules, seven Node runtime dependencies. No VM mutations, JavaScript execution, client/model/provider calls, or authentication changes.

The bounded local receipt diagnostic found a pre-existing canonical-hash defect: remote main already adds the hash, then local main included that hash in a second digest. A new main-path test recorded RED (1 test, 0.008s, one assertion failure). The one-line fix removes any existing hash before canonical hashing. The already captured receipt was normalized locally using the same canonical encoding; no second live capture was needed and all captured rows remain unchanged.

Final complete verbose suite: python -B -m unittest -v scripts.test_vm105_final_client_manifest

```
test_build_manifest_blocks_dependency_link_escape ... ok
test_build_manifest_freezes_sorted_closure_and_runtime ... ok
test_capture_hash_excludes_existing_remote_hash ... ok
test_dangling_dependency_links_skip_only_optional_and_peer ... ok
test_dependency_lookup_uses_literal_scoped_and_unscoped_virtual_store_layouts ... ok
test_nested_package_pins_resolve_discovered_roots ... ok
test_package_pins_reject_missing_ambiguous_roots_and_mismatch ... ok
test_runtime_dependencies_blocks_missing_library ... ok
test_selected_bundles_blocks_malformed_dsh_shapes ... ok
test_unrelated_manifest_url_is_not_a_cordis_bundle ... ok
Ran 10 tests in 1.683s
OK
```

Independent canonical hash verification and staged-path uniqueness checks passed. Canonical manifest SHA-256: 4331e0e5fd9ac6f5e881a0dae941f9f07dea7b69969ee8b610071ce14cb03f8b.

Remaining limit: this is installed runtime closure evidence, not client launch, provider generation, relay acceptance, or deployment authorization. No blocker remains for Task 1 capture. The Windows fixture uses real directory junctions when symlink privilege is unavailable.

## Final review fix wave — 2026-09-13

Read the implementation plan, both task reports, full TDD skill, and writing-good-tests reference before edits. Final review findings supplied by the coordinator covered method poisoning, early ACK ordering, manifest drift, and stale completion prose. Sole ownership covers only the coordinator-assigned script/test/evidence/packet/report paths; scripts/__pycache__/ remains untouched.

Strict RED command:
`python -B -m unittest -v scripts.test_vm105_final_client_transport.ReviewRegressionTest.test_unsupported_method_between_chat_and_ack_releases_no_output scripts.test_vm105_final_client_transport.ReviewRegressionTest.test_early_ack_cannot_overtake_chat_upstream scripts.test_vm105_final_client_manifest.FinalClientManifestTests.test_digest_blocks_identity_drift_during_hash scripts.test_vm105_final_client_manifest.FinalClientManifestTests.test_build_manifest_blocks_file_changes_between_inventory_passes`

RED: four tests in 1.246s, 14 expected assertion failures. GET/PUT/DELETE/PATCH/HEAD/OPTIONS/CONNECT left chat eligible and released `data: first`; TRACE/CUSTOM used 501 without poisoning relay state; an early ACK reached upstream while chat was held before send; during-hash mutation and between-inventory rewrite/add/remove did not raise ManifestBlocked.

Fixes: all unsupported methods resolve to the same denial path as invalid POST, setting failure and waking both events. ACK waits for successful upstream chat response headers, proving chat arrival, then rechecks failure before its upstream request. The held-chat test classifies ACK before releasing chat, so it does not hide the original race. Hashing compares pre/post file path and held-descriptor identity, and a full second inventory must equal the first before build_manifest returns PASS.

The first GREEN attempt exposed an overbroad send lock that prevented the regression from exercising concurrent ACK; the lock now protects state and the event enforces forwarding order. It also exposed unequal Windows stat/fstat ctime readings on unchanged files (observed difference 1789258462860758200 versus 1789258462862763300). The final check compares ctime through each API against its own pre-read value and still compares device/inode/mode/size/mtime across APIs. No drift check was disabled.

Final GREEN command: `python -B -m unittest -v scripts.test_vm105_final_client_transport scripts.test_vm105_final_client_manifest`. Result: 18 tests in 6.019s, OK (six transport, 12 manifest). Fixture CLI: `python -B scripts/Invoke-VM105FinalClient.py --fixture-regression`, exit 0:
```json
{"ackBeforeOutput":true,"catalog":0,"cleanupComplete":true,"directProvider":0,"discovery":0,"progressCommitted":true,"redirects":0,"requestCount":2,"resumeRequired":false,"retries":0,"status":"PASS","thirdRequestDenied":true,"tools":0,"tupleEquality":true}
```

Post-change live read-only capture: `python -B scripts/Build-VM105FinalClientManifest.py --output docs/evidence/vm105-final-client-runtime-manifest-20260913.json`, exit 0. Independently verified at 20260913 071816 Asia/Bangkok: PASS; 447 packages; 10,026 modules; two accepted entrypoints; three config bundles; seven runtime libraries. Canonical manifest SHA-256: `4331e0e5fd9ac6f5e881a0dae941f9f07dea7b69969ee8b610071ce14cb03f8b`. Receipt SHA-256: `54d117c638335edeefe43aaef0f181ea5317f7938a6861a145871a0d9e45e8dd`. The recaptured receipt is byte-identical to the existing artifact, so no artifact diff is expected.

Task 1 top-level result and the final packet now describe current PASS evidence; historical BLOCKED outcomes remain explicitly historical. The literal backtick-n formatting defect in Task 1 is corrected. Native gateway remains `http://192.168.1.68:20128/v1`; public ai.mysw.me events remain excluded and SSH forwarding remains candidate-only. Production namespace/socket integration, endpoint/key binding, source staging/revalidation, and live acceptance remain external. No VM mutation or JavaScript/client/provider/model execution occurred.
