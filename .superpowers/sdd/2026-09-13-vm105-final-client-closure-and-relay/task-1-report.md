# Task 1 report — VM105 final client runtime manifest

## Result

- RED recorded: `python -m unittest -v scripts.test_vm105_final_client_manifest` failed with the expected `ModuleNotFoundError` before production code existed.
- GREEN: the focused suite passes two real fixture checks: deterministic full closure/pin capture and fail-closed rejection of a dependency link that escapes the install root.
- Read-only capture: `python scripts/Build-VM105FinalClientManifest.py --output docs/evidence/vm105-final-client-runtime-manifest-20260913.json` returned exit 0 through strict SSH. The sanitized receipt is `BLOCKED` with `DEPENDENCY_UNRESOLVED`, contains no `modules` array, and has SHA-256 `c2333fff94069b3a910f0e29046a45b678ec5ae3a2bbca25231de33a09fa093c`.

## Scope and limits

The inspector does not invoke JavaScript, a client, a model, or a provider. It only transfers a finite Python inspector through strict batch SSH stdin. The blocking receipt is intentionally retained as the current evidence outcome; it does not establish runtime closure or release readiness.

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
`nFix round 4 commit: fae5143acf9003bf444864a9b96fdc3f0d77c4f3. Remaining path is an accepted entrypoint, so it was not skipped or weakened.


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
