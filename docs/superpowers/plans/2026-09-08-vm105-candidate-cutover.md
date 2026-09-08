# VM105 candidate profile cutover: owner-review packet

Status: **Static candidate ACCEPTED — corrected five-row candidate separately verified and independently reviewed at 2026-09-08 23:23:25 Asia/Bangkok. Runtime NOT PROVEN; no cutover performed. Awaiting owner readiness for fresh credential entry.**

Repository: `https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git`.

This packet implements the reversible switch and verification sequence in [the profile design](../specs/2026-09-08-vm105-reversible-profile-pointer-design.md). Its authority interpretation is corrected below: the authored design does not itself override the owner's instruction to continue and standing routine preapproval. Installed-source findings and their limits are recorded in [the selector/store trace](../../evidence/vm105-selector-store-trace.md).

## Overview

Switch `deepseek-harness.service` on VM105 (`deepseek-harness-01`, `192.168.1.139`) from `/home/dsh/.dsh` to the fresh, secret-free home `/home/dsh/.dsh-profiles/vm105-provider-v1`. The only service configuration change is one `DSH_HOME` drop-in. Access stays SSH-only through the established tunnel to loopback port 3080.

The service will briefly stop. The new profile retains the native default selection `deepseek-official/deepseek-v4-flash`, with zero active adapters and no usable inference route. Saved pilot providers, credentials and history stay in the old profile and are not copied. The owner must configure fresh credentials and a usable model route later; native Codex OAuth through the Web UI remains **NOT PROVEN**. No provider inference or provider charges are part of this cutover.

One switch attempt and, if needed, one automatic rollback attempt are permitted. Neither profile is deleted. Runtime readiness remains **NOT PROVEN** until all acceptance checks pass.

## Release conditions before the owner readiness decision

- Parent records the final preparation artifact paths, SHA-256 pins, static verification receipt and independent review verdict below. The candidate must be established by those receipts, not inferred from this packet.
- The final candidate contains the fresh web-profile manifest/composition inputs and empty settings described in the reviewed preparation, with exactly the five overrides below. Remove only the previous `agent-default-model` disable row through the separately verified candidate amendment. Revalidation reads only these newly prepared secret-free files; it never reads current-profile content.
- Parent has verified the amended candidate receipt and reviewed the bounded runtime probe below. Actual runtime readback (effective selector, zero active adapters and expected native dormant default) runs only after the switch. Static source intent cannot mark runtime acceptance PASS.
- Confirm the exact drop-in destination is absent and its ancestors satisfy the expected trust checks. An existing destination or conflicting drop-in is a blocker, never an overwrite.

| Release artifact | Final reference |
| --- | --- |
| Candidate preparation helper and SHA-256 | `scripts/prepare-vm105-provider-candidate.py`: `1E24CDC5215087E84C2A8F1D1CF78B04CC84B7D7CCC9C7EC50F02A5576F5DE73`; Linux self-test PASS, exclusive creation verified |
| Five-row amendment helper | `scripts/repair-vm105-candidate-default.py`: `A9DE5FDD6EC6D30296EA13C01EBAE9783A2B131C79E880D0C3E4EC9E72135115`; self-test PASS, one apply, separate parent verification PASS |
| Static receipt and file SHA-256 inventory | `docs/evidence/vm105-provider-candidate.json`: `B527D0C7230BCF5F2A19CCD3713C0B8777BC995F3F3239FAF03AA2571A1049F9` |
| Independent review | `/root/runtime_recovery_review`, ACCEPTED at 2026-09-08 23:23:25 Asia/Bangkok; corrected static candidate and cutover probe reviewed; runtime NOT PROVEN |

Preflight at 2026-09-08 23:24:39 Asia/Bangkok: `/etc/systemd/system` is a nonlinked root-owned 0755 directory; both the exact drop-in directory and destination are absent. UFW is active without an explicit TCP 3080 allowance; direct Bell-PC2 LAN connection to VM105:3080 failed within the three-second bound. The existing pilot remained PID 829 with unchanged start time and HTTP 200 through loopback and the tunnel. Revalidate these mutable facts immediately before execution. This packet is pinned by its publishing Git commit, avoiding a self-referential file hash.

```yaml
- id: spill-local
  config:
    root: /home/dsh/.dsh-profiles/vm105-provider-v1/spills
- id: session-telemetry-otel
  config:
    mode: DISABLED
- id: llm-deepseek
  disabled: true
- id: web-search-deepseek
  disabled: true
- id: llm-pi-ai
  config:
    providers: {}
```

Keep the LLM registry, settings, credentials and provider UI mounted. Empty adapters fail with `NO_ADAPTER`; no invented global fallback setting is used. Intentional read-only project/OS skill inputs remain available. These inputs do not authorize reads or migration of the old Harness profile.

## Exact service change and preserved baseline

Create only `/etc/systemd/system/deepseek-harness.service.d/90-vm105-provider-profile.conf`, a regular nonlinked `root:root` file, mode `0644`, containing:

```ini
[Service]
Environment=DSH_HOME=/home/dsh/.dsh-profiles/vm105-provider-v1
```

The parent directory must be a real `root:root` directory, mode `0755`. If absent, this packet includes creating that exact empty directory with those attributes; do not repair or replace an existing unexpected object. Track its creation separately; rollback leaves an empty directory in place.

Preserve these freshly revalidated facts:

| Service property | Expected value |
| --- | --- |
| Unit | `deepseek-harness.service` |
| ExecStart tokens | `/usr/local/bin/dsh`, `web`, `--host`, `127.0.0.1`, `--port`, `3080` |
| User / Group / UMask | `dsh` / `dsh` / `0077` |
| WorkingDirectory | `/srv/dsh/workspaces` |
| HOME | `/home/dsh` |
| Prior DSH_HOME | `/home/dsh/.dsh` |
| Environment names | `DSH_HOME`, `HOME`, `PATH` |
| EnvironmentFiles / PassEnvironment / existing DropIns | empty / empty / none |

Preserve the verified PATH, restart policy, hardening, tunnel and firewall. Recheck that `/srv/dsh/workspaces/.env` is absent and that process environment names contain no provider credential variables; never emit their values. The prior process-name check describes initial launch environment, not every possible runtime addition. Candidate freshness and the observed dotenv inputs are separate isolation conditions. Changing WorkingDirectory is outside this packet.

## Ordered execution after release checks and the owner readiness decision

1. Revalidate identity, service baseline, candidate pins/permissions/static policy, empty drop-in destination, tunnel assumptions, active UFW and direct-LAN denial. Capture sanitized prior selector metadata and the exact rollback destination. Any failed or ambiguous prerequisite stops with the pilot still active.
2. Stop `deepseek-harness.service` once. Confirm it is stopped before any pointer write. Once a stop is attempted, any failure or ambiguity enters the single rollback sequence below.
3. Capture exactly one root-only `lstat` baseline of `/home/dsh/.dsh`: path, type, owner, group, mode and link status. This post-stop, pre-pointer baseline is authoritative. Do not traverse, read, hash or copy its children.
4. Create the reviewed drop-in exclusively at the exact path, verifying ownership, mode, type and exact secret-free bytes. Do not replace an existing file. Run `systemctl daemon-reload`, then start the service once.
5. Run the acceptance checks below in order, with bounded command/HTTP timeouts fixed in the execution receipt before stopping. Do not treat an empty output, timeout, warning or unrecognized result as success. Any non-PASS immediately enters rollback.
6. If all checks pass, record `SWITCH_ACCEPTED` and stop at `CREDENTIAL_GATE`. No login, consent, key entry, route configuration or inference is included.

## Acceptance checks — all required

1. Hostname/VM identity match VM105 `deepseek-harness-01`.
2. The expected unit is active and its process runs as `dsh:dsh`; preserved service properties match.
3. Effective process selector is exactly the candidate home, with the reviewed composition active for credential/settings/session/state stores and spill root; there is no old-home merge or fallback.
4. The port 3080 listener is only `127.0.0.1:3080`.
5. Local HTTP health and the existing SSH-tunnel Web UI path work; no authentication interaction or secret capture is required.
6. UFW remains active with no new TCP 3080 allowance.
7. Direct LAN access to VM105 TCP 3080 remains denied.
8. Runtime readback confirms zero registered provider routes and the expected dormant native selection `deepseek-official/deepseek-v4-flash`; the reviewed no-alternate-route behavior remains applicable. No inference probe is used.
9. Candidate mutable-data directories/files retain required ownership, private modes and safe ACL/link/mount properties. Classify newly generated metadata without reading potential credential content. Expected boot-generated `profiles/node_modules` code-fallback symlinks are permitted only for source-traced installed package targets under `/opt/deepseek-harness`, with validated target/ancestor ownership and metadata. This is not blanket permission for symlinks: mutable-data redirects, especially to the old profile, remain forbidden.
10. Old-root `lstat` fields match the post-stop baseline, the effective selector is detached, and the operation ledger contains no old-tree write/move/delete. This is root metadata and workflow preservation evidence, not a full-tree byte-equality claim.
11. The ledger contains no credential/OAuth, provider, inference, route, firewall, package, VM-power or unrelated service mutation.

## Single automatic rollback

On any failure after the stop attempt, restore the prior selector: remove **only** the drop-in created by this attempt, and only after verifying its recorded identity, root ownership and exact reviewed content. If no drop-in was created, do not delete anything. Reload systemd and restart `deepseek-harness.service` once against `/home/dsh/.dsh`.

Verify the old effective selector, preserved unit/process identity, loopback listener, local/tunnel HTTP reachability, unchanged UFW and LAN denial. Keep both profile trees intact. Old-root comparison for switch acceptance ends when rollback restarts the old profile; normal service use may then update it.

Successful restoration ends `ROLLED_BACK`; record the failed acceptance check and stop. An unexpected drop-in identity/content, failed rollback operation, or failure to restore the baseline ends **ROLLBACK_FAILED**: stop mutations and report the exact sanitized discrepancy. No second switch, retry loop, speculative repair, reboot, firewall change or alternate configuration is permitted.

## What I need from you

After final release checks pass, the owner must choose whether to leave the fresh profile active and be ready for fresh interactive credential entry. This replaces a usable pilot with a profile that cannot run tasks until that entry and subsequent route configuration; waiting for the owner could prolong that loss of use. That material operational consequence and owner-only authentication require the readiness decision. The brief reversible selector validation and automatic rollback are covered by the instruction to continue and standing routine preapproval; an agent-authored design alone does not create a new approval requirement for stopping/restarting the service.

## Choices

- Leave the reviewed candidate active and enter fresh credentials now: completes the isolated-home transition; briefly interrupts the UI and suspends usable provider access until setup finishes. No inference cost is incurred by the switch.
- Keep the pilot active: avoids the interruption and preserves immediate use of saved providers; the isolated-home transition remains pending.

## Recommended choice

Leave the candidate active when the owner is ready for fresh credential entry, after final preparation verification and independent review pass. Keep the working pilot available until that readiness decision; saved pilot configuration remains available by rollback.

## Exact reply

`I am ready to enter fresh credentials. Leave the verified VM105 candidate profile active after the reviewed selector switch, keep SSH-only access, and roll back once if verification fails. Pause for my credential entry before configuring or testing a provider.`

## Reviewed condition amendment and runtime readback

The original condition requiring no provider/model selection is explicitly amended: retain the native dormant default while requiring zero active adapters and no usable inference. The independent review accepted this routine compatibility choice under the owner's standing preapproval; a separate user decision is not required for this condition amendment. This is not an unchanged PASS against the original no-selection condition. The earlier six-row candidate remains ineligible until its bounded five-row amendment and new receipt pass parent verification. The owner readiness decision concerns leaving the provider-less candidate active pending fresh credentials, not the authored design's former stop/restart approval language.

The exact web-bundle dependency `@deepseek-ai/dsh-host-apiproxy` declares `ApiProxyService.static inject` containing `agentDefaultModel` at `lib/index.js:5498–5510`. Its constructor supplies `ctx.agentDefaultModel.currentSelection()` at5532; `host.describe` invokes the supplied function at3108. Retaining this service resolves the mandatory API dependency without enabling the separately disabled DeepSeek adapter. A rendered static page or passing HTTP root is insufficient evidence of a functional API. No live candidate startup or current-profile API request was made in this investigation.

The concrete read-only registered-route query is nevertheless established for a composition in which this API service can mount:

```http
POST /api/llm.providers
Content-Type: application/json

{"type":"client-request","rpcId":"vm105-cutover-route-count","method":"llm.providers","payload":{}}
```

Use only the future candidate's established loopback HTTP carrier, after verifying its process selector. The request is a legacy ApiProxy envelope, not Typert's `{args:{}}` envelope and not a guessed `/api/llm/listProviders` path. `toFetchHandler` routes POST `/api/` methods at4914–4947; `UNARY_ROUTES` binds `llm.providers` at4773–4775. The client constructs the above full envelope and verifies its echoed rpcId at5282–5298. Fix a single-request five-second timeout and a bounded response size before execution; no retries, discovery calls or inference are needed.

The success response has `result.ok === true`, with `result.value.providers` as an array of rows whose `active` member is boolean. At3473–3496, the method obtains `registered = ctx.llm.listProviders()`, marks directory rows active only when present in the registered set, and appends registered routes absent from the directory as active. Therefore count `active === true`, not all directory rows: zero active rows proves zero registered routes, even when dormant provider choices remain visible. Validate the echoed rpcId, server-response type, success flag, array and boolean fields; emit only `registered_route_count` and PASS/BLOCKED. Never output names, descriptions, settings paths, response bodies or errors. No credential-store method is called by this query. The Models UI itself joins settings and credential descriptions at client548–579, so it is broader than this isolated readback and should not substitute for it.

For the second bounded readback, POST `/api/host.describe` with the same envelope, changing `method` to `host.describe` and `rpcId` to `vm105-cutover-default-check`, keeping `payload:{}`. Its implementation returns the current selection at3108–3113. Require successful typed response, echoed rpcId, and exact provider/model equality to `deepseek-official` / `deepseek-v4-flash`; emit only `native_default_matches: true` and PASS/BLOCKED, suppressing all other returned fields. The default's presence demonstrates API compatibility, not routability; the independent active-adapter count must still be zero. Use one five-second request, bounded response size and no retries. Do not call `llm.models` or `llm.discoverModels`: the former builds model catalogs and the latter can contact providers.

The five-row edit's hashes and final review receipt are recorded above. Static release checks are complete; preserve the working pilot pending the owner's readiness for fresh credential entry. Runtime acceptance remains pending. No installed-source patch or provider configuration was required for this resolution.

Future-candidate-only probe body, to run through the verified VM105 Python interpreter **after** independently proving the effective selector. Do not run against the current pilot. It performs two allowlisted reads, suppresses all raw values/errors, rejects redirects, caps each body at64KiB, and applies a five-second wall-clock alarm to each request. Any failed result triggers the packet's rollback; this code does not restart or retry anything.

```python
import json, signal, urllib.request

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None

def expired(*unused):
    raise TimeoutError()

signal.signal(signal.SIGALRM, expired)
opener = urllib.request.build_opener(
    urllib.request.ProxyHandler({}), NoRedirect())

def readback(method, rpc_id):
    assert method in ('llm.providers', 'host.describe')
    body = json.dumps({'type': 'client-request', 'rpcId': rpc_id,
                       'method': method, 'payload': {}}).encode()
    request = urllib.request.Request(
        'http://127.0.0.1:3080/api/' + method, data=body,
        headers={'Content-Type': 'application/json'}, method='POST')
    signal.alarm(5)
    try:
        with opener.open(request, timeout=5) as response:
            assert response.status == 200
            raw = response.read(65537)
            assert len(raw) <= 65536
        envelope = json.loads(raw)
        assert type(envelope) is dict
        assert envelope.get('type') == 'server-response'
        assert envelope.get('rpcId') == rpc_id
        result = envelope.get('result')
        assert type(result) is dict and result.get('ok') is True
        value = result.get('value')
        assert type(value) is dict
        return value
    finally:
        signal.alarm(0)

try:
    value = readback('llm.providers', 'vm105-cutover-route-count')
    rows = value.get('providers')
    assert type(rows) is list
    assert all(type(row) is dict and type(row.get('active')) is bool
               for row in rows)
    count = sum(row['active'] for row in rows)
    assert count == 0
    value = readback('host.describe', 'vm105-cutover-default-check')
    assert value.get('provider') == 'deepseek-official'
    assert value.get('model') == 'deepseek-v4-flash'
    print(json.dumps({'status': 'PASS', 'registered_route_count': count,
                      'native_default_matches': True}))
except Exception:
    print('{"status":"BLOCKED","check":"candidate-runtime-readback"}')
    raise SystemExit(1)
```

Source receipt (installed version0.1.1-rc.2; root-owned nofollow reads, stable metadata and before/after SHA checks; no source execution):

- `dsh-host-apiproxy` canonical root: `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-host-apiproxy@0.1.1-rc.2_7a1c54e2b954eca6f88bad802758761b/node_modules/@deepseek-ai/dsh-host-apiproxy`; declared by the verified web manifest. Manifest SHA256 `156d33df741f8cad7ccce2ade30eb6ca241001a5cb68510423dcd99804b6275d`; `lib/index.js` SHA256 `8e32ffc951f499849c155e30cb30813af5ed7abb11008653125092299b693d9f`.
- `dsh-client-ui-settings-models` canonical root: `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-client-ui-settings-models@0.1.1-rc.2_6ea45dce772d8d764ff9d4e073210778/node_modules/@deepseek-ai/dsh-client-ui-settings-models`; web manifest-declared. Manifest SHA256 `050fcc1cadb0e6bcb8bada85039a636864ebfea16228212d1ffd07def3fe8818`; declared `lib/client.js` SHA256 `c3b9a2d2d074c600c10553a4b15e294082f5851dd4a834d06ddb268b310d18de`.
