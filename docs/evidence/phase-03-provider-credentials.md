# Phase 3 provider credentials — owner-entry packet

Captured 2026-09-08 11:07–11:25 Asia/Bangkok. Repository origin:
https://github.com/chatchawan-simplewish/sw-localai-deepseek-harnes.git.
Worktree: `C:\Users\chatc\Projects\sw-localai-deepseek-harnes\.worktrees\vm105-authoritative-roadmap`;
branch `codex/vm105-authoritative-roadmap`.

- Total - 09/21
  - Phase 1 - 05/05
  - Phase 2 - 03/03
  - Phase 3 - 01/02
  - Phase 4 - 00/09
  - Phase 5 - 00/02

FW-01 remains **BLOCKED / NOT PROVEN**. CRED-01 verdict: **BLOCKED / NOT
PROVEN**. This is a finite preparation packet, not credential-entry authority.
No key, native grant, provider route, model, service, firewall rule or credential
backup was created or changed. No secret-bearing file or environment was read.

## Revalidated prerequisite

At 11:07:06 +07:00, the current firewall packet SHA-256 still matched the
independently accepted value
`FF91A5E0D0FB29F7CAFEFFF32B8B3A1A7DD2A76CC087A38E4939435532D361A1`.
The accepted packet still has zero rules, empty approved/releasable rule lists,
and no mutation authority.

Strict SSH re-established the accepted VM105 host identity at
`deepseek-harness-01`, `192.168.1.139/24`, MAC `bc:24:11:5c:49:52`.
`deepseek-harness.service` remained enabled and active/running as `dsh`, result
success, zero restarts, working directory `/srv/dsh/workspaces`. The only 3080
listener was `127.0.0.1:3080`; VM-local HTTP returned 200. UFW retained deny
incoming, allow outgoing, disabled routed, and only the two existing TCP 22
rules for Bell-PC2 `.161` and Hermes VM104 `.141`.

Bell-PC2 retained SSH process 42076 on `127.0.0.1:3080` and `::1:3080`; tunneled
HTTP returned 200. Direct TCP to `192.168.1.139:3080` returned false. No baseline
drift or live network mutation was observed. The six route blockers accepted in
03-01 remain blockers; the three existing HTTPS paths prove transport only.

## Storage baseline

Only names, owner/group, mode, type, timestamps and symlink metadata were
inspected. No file contents, sizes, hashes, environment values, service
environment, credential values or Hermes stores were inspected.

| Path | Metadata at 11:07 +07:00 | Disposition |
| --- | --- | --- |
| `/home/dsh` | directory, `dsh:dsh`, 0750 | Verified parent |
| `/home/dsh/.dsh` | directory, `dsh:dsh`, 0700 | Verified Harness home and protected parent |
| `/home/dsh/.dsh/storages` | directory, `dsh:dsh`, 0700 | Existing non-credential storage |
| `/home/dsh/.dsh/settings.yaml` | regular file, `dsh:dsh`, 0600 | Existing; contents not read |
| `/home/dsh/.dsh/storages/workspace.json` | regular file, `dsh:dsh`, 0600 | Existing; contents not read |
| `/home/dsh/.dsh/.credentials.yaml` | absent | Installed default candidate only; no baseline credential document |
| `/home/dsh/.dsh/.env` | absent | No user fallback at the documented default |
| `/srv/dsh/workspaces/.env` | absent | No invocation-directory fallback at the exact service working directory |
| `/home/dsh/.dsh/cordis.patch.yml` | absent | No home-level patch at the documented name |
| `/home/dsh/.dsh/profiles/web/cordis.yml` | regular file, `dsh:dsh`, 0664, modified 2026-09-04 | Provenance-unverified profile configuration; contents not read |
| `/home/dsh/.dsh/profiles/web/cordis.patch.yml` | regular file, `dsh:dsh`, 0664 | Provenance-unverified profile patch; contents not read |

Installed `@deepseek-ai/dsh-credentials-local@0.1.1-rc.2` resolves an explicit
plugin path first and otherwise uses `<Harness home>/.credentials.yaml`. It
creates the parent as 0700 and the document as 0600, and it can resolve a
launch environment before the managed file. The provenance-unverified web
profile files could change the plugin path or composition, and the launch
environment is intentionally unread. Therefore the actual effective credential
store is **NOT PROVEN**. The absent default candidate must not be promoted to an
effective-path claim.

The one permitted live mutation created exactly this empty host-local destination:

`/home/dsh/.dsh/phase-03-provider-backup-20260908T110706`

It is a directory owned by `dsh:dsh`, mode 0700, beneath the verified 0700 Harness
home, and an immediate bounded `find -mindepth 1` returned no entry. It remains
empty. No credential state was copied merely because a source mode appeared safe.

## Entry packet

### Installed entry and indicator contracts

- **API-BUILTIN** — Settings → Models → Add provider → provider → API key field;
  optional Customized settings exposes Base URL and model rows; Apply writes the
  value through `credentials.set`. The browser receives only a redacted
  descriptor. A successful Apply emits a local accessible status message; a
  configured named reference renders a green solid dot. Empty input on an
  existing row keeps stored credential material.
- **API-CUSTOM** — Settings → Models → Add a custom provider → Provider ID,
  Display name, Base URL, API protocol, model rows and the write-only API key
  field → Create provider. Current protocol choices are `openai-completions`,
  `openai-responses` and `anthropic-messages`.
- **NATIVE-CODEX** — the installed backend and record type support native
  `openai-codex`, but the current Models draft exposes only the API key field,
  Base URL and model rows. It exposes no human native sign-in control and no
  safe native configured indicator. API-key substitution is forbidden.
- **FILE-DEFAULT** — expected candidate `/home/dsh/.dsh/.credentials.yaml`,
  `dsh:dsh`, 0600, parent 0700. This is not released until the effective path is
  proven without opening provenance-unverified state.
- **SETTINGS-DEFAULT** — provider/model/base-URL mutations use the redacted
  settings seam backed by candidate `/home/dsh/.dsh/settings.yaml`, currently
  `dsh:dsh` 0600. Existing profile/settings contents are never a credential
  provenance source.
- **SAFE-API-INDICATOR** — success status plus green provider dot, followed only
  after leaving the entry screen by metadata checks of the proven effective
  file. It proves configured state, not provider access or inference.
- **DISCONNECT-SINK** — edit only the provider row's Customized settings Base URL
  to `https://127.0.0.1:9`, leave the API key field empty, and Apply. Port 9 had
  zero VM105 listeners at preparation time. This settings-only disconnect
  leaves the credential document and native record in place. Never use row
  deletion: installed behavior may delete an identifiable writable credential.

All UI observations used Chrome browser ID 2, profile exactly
`Codex-Chrome-Bell-PC2`, extension identity
`dfd27eec-84b9-446f-81ec-a134992060a6`, existing tab 435371600 at
`http://127.0.0.1:3080/`. Drafts were cancelled; no Apply, Create provider,
login, consent, secret typing, screenshot, clipboard, network-body capture or
configuration-file opening occurred.

### Nine-route packet

Proposed labels below are new safe labels, not claims about existing provider
accounts or projects. Every account/workspace identity marked owner confirmation
must be confirmed at the action-time gate; it must not be inferred from another
machine or an older Hermes setup.

| Route | Smallest supported access and minimum practical lifetime | Safe identity and nonsecret identifier | Consumer, shared access and exact entry/store | Safe indicator, disconnect and status |
| --- | --- | --- | --- | --- |
| OpenRouter Auto | One ordinary OpenRouter inference key scoped to the owner-confirmed VM105 workspace; expiry seven days after issuance; USD 5 total key cap; workspace/model guardrail must admit only the reviewed router use. Exact request model `openrouter/auto`; child allowlist and cost tier remain Phase 4 controls. | Account/workspace **owner confirmation required**. Proposed key label `deepseek-harness-vm105-phase4-20260908`. Credential identifier is `not available` unless the provider safely exposes a distinct non-hash identifier; workspace ID may be recorded separately if shown. Never record the key or its hash. | Harness `llm-pi-ai`, provider `openrouter`; shared with OpenRouter Pareto Code. API-BUILTIN, FILE-DEFAULT and SETTINGS-DEFAULT. | SAFE-API-INDICATOR; DISCONNECT-SINK disconnects both OpenRouter rows while leaving material. **BLOCKED** on exact effective store and owner workspace/guardrail confirmation. |
| OpenRouter Pareto Code | Same seven-day, USD 5-capped key and workspace guardrail; exact request model `openrouter/pareto-code`. Pareto's minimum coding score and selected child attribution belong to Phase 4. | Same owner-confirmed account/workspace and same nonsecret provider identifiers as OpenRouter Auto; no second credential. | Same `openrouter` consumer and one shared `OPENROUTER_API_KEY` reference. API-BUILTIN; no duplicate secret or model-specific key. | Same green-dot/status check and provider-level DISCONNECT-SINK. **BLOCKED** with OpenRouter Auto. |
| VM1201 Qwen | Credential/auth scope and lifetime **not established**. No access may be created until current VM identity, listener, model and worker auth are proven. | No safe account/project identity or provider-issued identifier available. Proposed future Harness provider ID `vm1201qwen` is a label only. | Future `llm-pi-ai` custom route; exact endpoint, model, credential reference and actual store are **BLOCKED**. It must not reuse another worker's identity. | No configured indicator exists. DISCONNECT-SINK would be required before entry is releasable, but original Base URL is unresolved. **BLOCKED**. |
| Bell-PC2 local worker | Credential/auth scope and lifetime **not established**. The confirmed Caddy gateway is not proof of upstream auth or model service. | Host is Bell-PC2; upstream account/service identity and provider-issued identifier unavailable. Proposed future provider ID `bellworker` is a label only. | Future `llm-pi-ai` custom route; gateway candidate `http://192.168.1.161:11435`, but upstream endpoint/model/auth/reference remain **BLOCKED**. | No safe configured indicator. DISCONNECT-SINK requires a proven original route first. **BLOCKED**. |
| Typhoon Thai text | One application-specific OpenTyphoon key for server-side API use, shared only with OCR if OCR compatibility later passes. Official docs recommend minimum permissions and periodic rotation but publish no exact permission selector or expiry control; practical operational lifetime is Task 2 through Phase 4, followed by separately authorized owner revocation. | Account/project **owner confirmation required**. Proposed key label `deepseek-harness-vm105-phase4-20260908`; record a distinct provider-issued non-hash credential ID only if the safe dashboard exposes one, otherwise record `not available`. | Harness `llm-pi-ai`, custom provider ID `opentyphoon`, display name `OpenTyphoon VM105`, Base URL `https://api.opentyphoon.ai/v1`, protocol `openai-completions`, model `typhoon-v2.5-30b-a3b-instruct`; shared `OPENTYPHOON_API_KEY` reference. API-CUSTOM, FILE-DEFAULT and SETTINGS-DEFAULT. | SAFE-API-INDICATOR; DISCONNECT-SINK disconnects Typhoon text and any later OCR row. **BLOCKED** on effective store, owner identity and exact dashboard permission/lifetime controls. |
| Typhoon OCR | No separate credential is justified. Candidate shared OpenTyphoon access only after the installed Harness can support the official `typhoon-ocr` image/PDF message flow without a new helper or adapter. | Same owner-confirmed account/project and any safe nonsecret identifier as Typhoon text; no second key. | Candidate same `opentyphoon` provider/store, but no route entry is allowed. Official docs require the `typhoon-ocr` helper workflow; installed Harness compatibility remains unproven. | No indicator until compatibility is proven. Provider-level DISCONNECT-SINK is concrete but would affect shared Typhoon text. **BLOCKED** on wire/image compatibility. |
| Codex Luna | Native ChatGPT sign-in only; no API-key substitution. One native session is shared by the three Codex models. Official docs say active sessions refresh automatically; no fixed provider lifetime is exposed. Operational lifetime is Task 2 through Phase 4, with later owner-controlled sign-out. | ChatGPT account/workspace **owner confirmation required**; model availability is account/rollout dependent. No safe provider-issued credential ID is currently documented. | Harness `llm-pi-ai`, provider `openai-codex`, model `gpt-5.6-luna`; candidate native record `llm-pi-ai/openai-codex` in FILE-DEFAULT, shared with Terra and Sol. NATIVE-CODEX surface is missing. | No native configured indicator. Future DISCONNECT-SINK must be verified against the native provider before use. **BLOCKED** on supported login surface, effective store and safe indicator. |
| Codex Terra | Same native ChatGPT session, operational lifetime and owner-confirmed workspace as Codex Luna; exact model `gpt-5.6-terra`. | Same account/workspace confirmation; no second identifier or grant. | Same `openai-codex` provider/native record, shared across all three models. NATIVE-CODEX unavailable. | Same blockers and future provider-level disconnect as Luna. **BLOCKED**. |
| Codex Sol | Same native ChatGPT session, operational lifetime and owner-confirmed workspace as Codex Luna; exact model `gpt-5.6-sol`. | Same account/workspace confirmation; no second identifier or grant. | Same `openai-codex` provider/native record, shared across all three models. NATIVE-CODEX unavailable. | Same blockers and future provider-level disconnect as Luna. **BLOCKED**. |

OpenRouter Auto and Pareto are explicit router IDs; they do not authorize Harness
automatic provider selection. Provider/model selection remains explicit, and
inference, invalid-credential behavior, child attribution and cost behavior remain
Phase 4 NOT PROVEN.

## Post-provenance backup and restore plan

The protected destination is ready but empty. The following commands are a
**NOT RELEASED** exact plan for the installed default candidate only. They may be
used later only after a supported safe surface proves the effective path is
exactly `/home/dsh/.dsh/.credentials.yaml`, the file is newly created by the
approved uninterrupted VM105 entry session, nonsecret issuance/create metadata
correlates with file metadata, and owner/group/modes are `dsh:dsh` 0600 beneath
0700 parents. Any mismatch, symlink or preexisting/provenance-unverified material
blocks these commands and stays untouched.

Planned one-time post-entry backup:

```sh
(
set -eu
umask 077
export LC_ALL=C
source_file=/home/dsh/.dsh/.credentials.yaml
backup_dir=/home/dsh/.dsh/phase-03-provider-backup-20260908T110706
backup_file=$backup_dir/credential-store.post-entry.yaml
receipt_file=$backup_dir/credential-store.live-target.stat
require_dir() {
  [ -d "$1" ] && [ ! -L "$1" ] &&
    [ "$(stat -c '%U:%G:%a:%F' -- "$1")" = "$2" ]
}
require_file() {
  [ -f "$1" ] && [ ! -L "$1" ] &&
    [ "$(stat -c '%U:%G:%a:%F' -- "$1")" = "$2" ]
}
require_absent() { [ ! -e "$1" ] && [ ! -L "$1" ]; }
[ "$(id -un)" = dsh ]
[ "$(id -gn)" = dsh ]
require_dir / 'root:root:755:directory'
require_dir /home 'root:root:755:directory'
require_dir /home/dsh 'dsh:dsh:750:directory'
require_dir /home/dsh/.dsh 'dsh:dsh:700:directory'
require_dir "$backup_dir" 'dsh:dsh:700:directory'
require_file "$source_file" 'dsh:dsh:600:regular file'
require_absent "$backup_file"
require_absent "$receipt_file"
[ -z "$(find "$backup_dir" -mindepth 1 -maxdepth 1 -print -quit)" ]
source_receipt=$(stat -c '%d:%i:%h:%U:%G:%a:%y:%z' -- "$source_file")
install -m 0600 -- "$source_file" "$backup_file"
require_file "$backup_file" 'dsh:dsh:600:regular file'
[ "$(stat -c '%d:%i:%h:%U:%G:%a:%y:%z' -- "$source_file")" = "$source_receipt" ]
printf '%s\n' "$source_receipt" > "$receipt_file"
require_file "$receipt_file" 'dsh:dsh:600:regular file'
[ "$(find "$backup_dir" -mindepth 1 -maxdepth 1 -printf '%f\n' | LC_ALL=C sort)" = "$(printf '%s\n' credential-store.live-target.stat credential-store.post-entry.yaml | LC_ALL=C sort)" ]
)
```

Planned restore, requiring separate authority and a separately proven fresh
VM105-specific backup plus an unchanged target-metadata receipt:

```sh
(
set -eu
umask 077
export LC_ALL=C
live_file=/home/dsh/.dsh/.credentials.yaml
backup_dir=/home/dsh/.dsh/phase-03-provider-backup-20260908T110706
backup_file=$backup_dir/credential-store.post-entry.yaml
receipt_file=$backup_dir/credential-store.live-target.stat
restore_file=/home/dsh/.dsh/.credentials.yaml.restore
require_dir() {
  [ -d "$1" ] && [ ! -L "$1" ] &&
    [ "$(stat -c '%U:%G:%a:%F' -- "$1")" = "$2" ]
}
require_file() {
  [ -f "$1" ] && [ ! -L "$1" ] &&
    [ "$(stat -c '%U:%G:%a:%F' -- "$1")" = "$2" ]
}
require_absent() { [ ! -e "$1" ] && [ ! -L "$1" ]; }
[ "$(id -un)" = dsh ]
[ "$(id -gn)" = dsh ]
require_dir / 'root:root:755:directory'
require_dir /home 'root:root:755:directory'
require_dir /home/dsh 'dsh:dsh:750:directory'
require_dir /home/dsh/.dsh 'dsh:dsh:700:directory'
require_dir "$backup_dir" 'dsh:dsh:700:directory'
require_file "$backup_file" 'dsh:dsh:600:regular file'
require_file "$receipt_file" 'dsh:dsh:600:regular file'
require_file "$live_file" 'dsh:dsh:600:regular file'
require_absent "$restore_file"
[ "$(find "$backup_dir" -mindepth 1 -maxdepth 1 -printf '%f\n' | LC_ALL=C sort)" = "$(printf '%s\n' credential-store.live-target.stat credential-store.post-entry.yaml | LC_ALL=C sort)" ]
[ "$(wc -l < "$receipt_file" | tr -d ' ')" = 1 ]
grep -Eq '^[0-9]+:[0-9]+:[0-9]+:dsh:dsh:600:.+:.+$' "$receipt_file"
recorded_receipt=$(sed -n '1p' "$receipt_file")
[ "$(stat -c '%d:%i:%h:%U:%G:%a:%y:%z' -- "$live_file")" = "$recorded_receipt" ]
install -m 0600 -- "$backup_file" "$restore_file"
require_file "$restore_file" 'dsh:dsh:600:regular file'
[ "$(stat -c '%d:%i:%h:%U:%G:%a:%y:%z' -- "$live_file")" = "$recorded_receipt" ]
mv -fT -- "$restore_file" "$live_file"
require_file "$live_file" 'dsh:dsh:600:regular file'
require_absent "$restore_file"
)
```

Each parenthesized block is one fail-closed invocation: `set -eu` stops at any
failed guard before a later mutation line. Run neither block line by line. No
credential contents or credential/key/secret hash are printed or recorded. The
receipt contains only device, inode, link count, owner, group, mode, modification
time and change time. The restore rechecks that exact live-target receipt after
preparing the temporary file and immediately before replacement; any observed
drift blocks replacement. It is eligible only in the separately controlled
single-executor lane with no concurrent writer.

Backup/restore is forbidden when provenance is uncertain; no copy is made to
manufacture rollback. If the effective path differs, these commands remain
blocked and the packet requires renewed review with the actual path. Restore is
not the routine Rollback: the non-destructive consumer disconnect is.

## Rollback

Before owner approval there is no credential backup to restore and no provider
change to reverse. If a later approved entry fails, stop subsequent providers and
use only the route's DISCONNECT-SINK through the redacted Models UI, leaving all
credential material in its owner-only store. Verify the provider Base URL shows
the loopback sink, port 9 remains without a listener, service/listener/tunnel/UFW
remain at baseline, and no inference is attempted in Phase 3.

Do not delete a provider row, unset a credential, sign out, revoke/delete provider
access, overwrite a store, rotate a shared/global identity, restart the service or
restore a file as routine rollback. Revocation/deletion and any restore are
informational future owner actions requiring separate authority. A consumer whose
settings-only sink cannot be proven must stay BLOCKED before entry.

## Owner gate

Owner gate: **NOT REQUESTED / NOT APPROVED**. Stop before Task 2. Standing routine
approval does not authorize API-access creation, native login/consent or sensitive
entry. The next gate may be presented only after the effective credential path and
all route-specific blockers intended for that finite session are resolved and the
parent accepts this packet. Account/workspace safe labels, OpenRouter workspace and
guardrail, OpenTyphoon permission/lifetime controls, and Codex supported human
sign-in remain owner/surface confirmations.

## Official current sources

Accessed 2026-09-08; account pages and login were not opened.

- OpenRouter API key creation, optional UTC expiry and spending limit:
  https://openrouter.ai/docs/api/api-reference/api-keys/create-keys
- OpenRouter workspaces and workspace-scoped keys:
  https://openrouter.ai/docs/guides/features/workspaces/overview
- OpenRouter guardrail budgets/model restrictions:
  https://openrouter.ai/docs/guides/features/guardrails/overview
- OpenRouter Auto router and explicit `openrouter/auto` ID:
  https://openrouter.ai/docs/guides/routing/routers/auto-router
- OpenRouter Pareto router and explicit `openrouter/pareto-code` ID:
  https://openrouter.ai/docs/guides/routing/routers/pareto-router
- OpenTyphoon authentication, descriptive key labels, minimum-permission and
  rotation guidance: https://docs.opentyphoon.ai/en/authentication/
- OpenTyphoon API base and text request contract:
  https://docs.opentyphoon.ai/en/api-reference/
- OpenTyphoon model IDs: https://docs.opentyphoon.ai/en/models/
- OpenTyphoon OCR helper/file workflow: https://docs.opentyphoon.ai/en/ocr/
- Official OpenAI authentication, browser sign-in, automatic refresh, credential
  storage and sign-out behavior: https://learn.chatgpt.com/docs/auth
- Official OpenAI model IDs and account/rollout availability caveat:
  https://learn.chatgpt.com/docs/models

## Verification boundary

Task 1 establishes a reviewable blocked packet and one empty protected destination.
It does not establish any account identity, credential provenance, OAuth state,
authenticated provider response, model response, fail-closed behavior or CRED-01
PASS. The exact effective store, supported native Codex sign-in surface and safe
native status indicator remain the principal blockers. Six 03-01 route blockers
also remain unchanged. Task 2 must not start from this blocked packet.
