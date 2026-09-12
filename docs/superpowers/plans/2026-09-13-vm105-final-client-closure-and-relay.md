# VM105 Final Client Closure and Relay Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Freeze the complete installed VM105 client runtime closure and provide a fixed, locally executable two-request relay/launcher regression without invoking the live client or mutating VM105.

**Architecture:** One read-only inspector connects to VM105 through the established strict SSH path, resolves the accepted DSH entrypoints and config bundles, walks every reachable canonical package root, and emits a canonical manifest or a fail-closed receipt. One stdlib Python relay enforces the two-request protocol against a fixture gateway; its production mode requires explicit endpoint and key-reference bindings and therefore remains non-executing until those external values exist.

**Tech Stack:** Python 3.12 standard library, Windows OpenSSH, POSIX `/proc`, `readlink`, `ldd`, SHA-256, JSON, Markdown, Git.

## Global Constraints

- Repository is `https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git`; work only in `.worktrees/vm105-authoritative-roadmap` on `codex/vm105-authoritative-roadmap`.
- Preserve dirty work and stage exact paths only. Use command-scoped Git identity.
- VM105 access is read-only through `C:/Windows/System32/OpenSSH/ssh.exe`, identity `C:/Users/chatc/.ssh/codex-prox01-vms-ed25519`, target `dsh@192.168.1.139`, with `BatchMode=yes`, `IdentitiesOnly=yes`, and `StrictHostKeyChecking=yes`.
- The installed CLI entrypoint is `/opt/deepseek-harness/node_modules/@deepseek-ai/dsh/lib/bin.js`; the Node binary is `/opt/node-v24.19.0-linux-x64/bin/node`; the accepted client entrypoint is the installed `@deepseek-ai/dsh-client-ui-settings-models/lib/client.js` pinned by SHA-256 `c3b9a2d2d074c600c10553a4b15e294082f5851dd4a834d06ddb268b310d18de`.
- Freeze the root package manifest and `config/agent-presets/standard/agent.cordis.yml`, every reachable package manifest and config-selected `cordis.yml`/`cordis.patch.yml` bundle, every regular `.js`, `.cjs`, `.mjs`, `.json`, `.node`, and `.wasm` file below each resolved package root, the Node binary, its loader, and its `ldd` shared libraries.
- Reject any logical/canonical path outside `/opt/deepseek-harness/node_modules`, any unresolved dependency or peer dependency, symlink escape, non-regular included artifact, hash drift, unresolved Node dependency, or accepted-entrypoint pin mismatch. Emit no partial PASS manifest.
- The gateway stays the documented HTTP LAN service `http://192.168.1.68:20128/v1`. Do not invent a TLS endpoint, certificate identity, DNS name, firewall rule, or gateway change.
- The production relay binds only loopback and permits exactly one `POST /v1/chat/completions` followed by one `POST /v1/agent-routes/events`; the second request must carry event `output_started`, the task/run/turn/idempotency tuple must match, and HTTP 202 with `{\"accepted\":true}` must arrive before the first chat output byte is released.
- Chat uses model `agent/normal`, streaming, `tools: []`, `tool_choice: \"none\"`, and zero retries. A third request, redirect, other method/path, malformed tuple, or failed ACK is denied locally and releases no output.
- Tests use only `http://127.0.0.1:<ephemeral>/v1` and the literal non-secret `fixture-key-not-secret`. Production endpoint and key-reference binding remain deferred and fail closed when absent.
- Do not invoke the VM105 final client, call a provider/model, change the service/default/profile/firewall/gateway, persist a credential, or rerun the spent containment smoke.

---

### Task 1: Complete installed runtime manifest

**Files:**
- Create: `scripts/Build-VM105FinalClientManifest.py`
- Create: `scripts/test_vm105_final_client_manifest.py`
- Create: `docs/evidence/vm105-final-client-runtime-manifest-20260913.json`

**Interfaces:**
- Consumes: the exact VM105 paths, accepted entrypoint pin, and strict SSH values from Global Constraints.
- Produces: `build_manifest(fs_root: pathlib.Path, node_path: pathlib.Path) -> dict`, `canonical_bytes(manifest: dict) -> bytes`, CLI mode `--fixture-root` for local tests, and default read-only SSH capture for VM105.

- [ ] **Step 1: Write the failing behavior test**

Create a temporary pnpm-like tree with a logical root symlink, two package roots, CLI/client/config files, one `.node` artifact, and a synthetic Node executable. Assert that `build_manifest` returns sorted module rows, freezes all three entrypoints/config bundles, records Node/runtime pins, and raises `ManifestBlocked` when a dependency link escapes the install root. Derive all expected relative paths and SHA-256 literals in the test itself.

- [ ] **Step 2: Run the focused test and record RED**

Run: `python -m unittest -v scripts.test_vm105_final_client_manifest`

Expected: import failure because `Build-VM105FinalClientManifest.py` does not exist.

- [ ] **Step 3: Implement the minimum read-only inspector**

Use only `argparse`, `hashlib`, `json`, `os`, `pathlib`, `re`, `stat`, and `subprocess`. Parse `dependencies`, `optionalDependencies`, and installed `peerDependencies` from each package manifest; resolve package links without following an unvalidated escape; walk the full accepted extension set; hash each regular file; parse absolute paths from `ldd`; and sort packages, edges, entrypoints, config bundles, modules, and runtime dependencies before canonical JSON encoding with `sort_keys=True` and compact separators. Default mode sends a finite Python inspector through SSH stdin and writes only the returned sanitized manifest locally. Status is `PASS` only when every Global Constraint is satisfied; otherwise return `BLOCKED` with reason codes and no `modules` array.

- [ ] **Step 4: Run GREEN and capture the live read-only manifest**

Run: `python -m unittest -v scripts.test_vm105_final_client_manifest`

Expected: all tests pass.

Run: `python scripts/Build-VM105FinalClientManifest.py --output docs/evidence/vm105-final-client-runtime-manifest-20260913.json`

Expected: SSH exit 0 and either a complete `PASS` manifest with canonical manifest hash or a `BLOCKED` receipt naming only non-secret unresolved bindings. No VM file or service state changes.

- [ ] **Step 5: Commit the task**

Stage exactly the three Task 1 paths and commit with command-scoped repository identity using message `feat: freeze VM105 final client runtime closure`.

### Task 2: Fixed exact-two relay and launcher

**Files:**
- Create: `scripts/Invoke-VM105FinalClient.py`
- Create: `scripts/test_vm105_final_client_transport.py`
- Create: `docs/evidence/vm105-final-client-transport-review-20260913.md`
- Modify: `docs/handoffs/vm105-omniroute-final-client-packet-20260913.md`

**Interfaces:**
- Consumes: Task 1 manifest status/hash and the exact transport constraints above.
- Produces: `TwoRequestRelay`, `run_fixture_regression() -> dict`, CLI `--fixture-regression`, and production preflight that accepts `--gateway-base http://192.168.1.68:20128/v1` plus an opaque `--key-reference` and refuses execution when either is absent.

- [ ] **Step 1: Write the failing end-to-end regression**

Start a real loopback `ThreadingHTTPServer` fixture. Run the wished-for relay API against it and assert literal outcomes: streaming chat reaches the fixture once; the relay withholds `data: first` until a concurrent `output_started` ACK returns 202 with `{\"accepted\":true}`; both requests use the same literal tuple; a third POST receives denial without reaching the fixture; cleanup leaves no relay listener/thread; and the receipt contains request count `2`, ACK-before-output true, `progressCommitted` true, `resumeRequired` false, retries/redirects/discovery/catalog/direct-provider/tools all zero. Also assert production preflight refuses an absent endpoint or key reference.

- [ ] **Step 2: Run the focused test and record RED**

Run: `python -m unittest -v scripts.test_vm105_final_client_transport`

Expected: import failure because `Invoke-VM105FinalClient.py` does not exist.

- [ ] **Step 3: Implement the minimum relay/launcher**

Use only `argparse`, `http.client`, `http.server`, `json`, `socket`, `threading`, `time`, and `urllib.parse`. Bind `127.0.0.1` on an ephemeral or explicitly supplied port. Maintain one lock-protected state record for the two allowed requests. Forward only to the fixed parsed gateway origin, set timeouts, disable redirect behavior by using `http.client`, strip hop-by-hop and credential headers from receipts, buffer the first streamed bytes until the ACK succeeds, reject all later traffic, and close the listener plus owned upstream connections in `finally`. The fixture credential remains test-only. Production preflight prints only sanitized binding presence and the selected documented HTTP origin, then stops before any final-client invocation.

- [ ] **Step 4: Run GREEN and write transport review evidence**

Run: `python -m unittest -v scripts.test_vm105_final_client_transport`

Expected: all tests pass without network access beyond loopback.

Run: `python scripts/Invoke-VM105FinalClient.py --fixture-regression`

Expected: exit 0 and a sanitized PASS receipt proving the exact two-request ordering, third-request denial, and cleanup.

Document the source-checked SSH facts: Bell-PC2 already has strict OpenSSH control access to VM105 and a previously observed loopback-only management tunnel to `belladmin@192.168.1.68`; VM105-to-gateway SSH credentials and any durable provider-data tunnel are not proven. Retain direct private-LAN HTTP as the minimum evidenced VM105 data path. Keep SSH as the read-only control/review path and require a separate transport design before claiming encrypted provider traffic.

Update the final packet to replace the invented gateway-TLS requirement with the documented HTTP LAN origin and the reviewed SSH-forwarding option. Preserve the prohibition on live execution and all other gates.

- [ ] **Step 5: Commit the task**

Stage exactly the four Task 2 paths and commit with command-scoped repository identity using message `feat: add exact-two VM105 relay regression`.

## Self-review

- Spec coverage: Task 1 covers accepted entrypoints, config bundles, complete installed closure, Node/runtime pins, and read-only selector policy. Task 2 covers the fixed launcher, streaming and concurrent ACK ordering, third-request denial, cleanup, HTTP gateway correction, and source-checked secure transport option.
- Placeholder scan: production endpoint and key values are intentionally external runtime inputs; tests use fixed fixture values. No implementation step depends on guessed credentials, TLS, or live provider state.
- Type consistency: Task 2 consumes only Task 1's manifest status and canonical hash; the manifest builder and transport regression have independent file ownership.
