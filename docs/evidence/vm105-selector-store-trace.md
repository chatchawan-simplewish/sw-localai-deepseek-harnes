# VM105 selected-home storage consumer trace

Recorded: 2026-09-08T15:51:46Z; extended source checks completed afterward in the same session. Status: SUPPORTED WITH EXPLICIT CONFIGURATION CONDITIONS; bare whole-profile selector PASS remains NOT PROVEN. Independent review pending.

## Scope and method

Read-only installed-source inspection from Bell-PC2 over strict SSH to dsh@192.168.1.139 using the existing project key and /usr/bin/python3.12. Reused the Inspection class from scripts/inspect-vm105-pnpm-package.py in memory, without executing installed JavaScript. Each dependency was named by its verified parent's package.json; its root-owned logical symlink was resolved only into the canonical /opt/deepseek-harness/node_modules/.pnpm tree. Every canonical ancestor and source was opened no-follow, checked root:root/non-group-or-world-writable, checked against forbidden ACL/capability attributes, held and rechecked for identity/metadata drift. Each consumed source had link count 2 and matching before/after SHA-256.

Initial bound: 15 packages including root dsh; parent explicitly extended it by five named declared packages (agent-presets, session-telemetry-otel, skill-filesystem, skill, persona), all inspected. No generic directory discovery, current-profile traversal, .env/credential-store content read, source execution, inference, service/network mutation or candidate creation. Repeated reads narrowed excerpts and supplied exact line proofs; no rejected source was reread. The first optional dsh-base lib/index.js read was refused before bytes by the original link-count-2 rule. Later metadata-only inspection found root:root regular 0644, link count 253. Its content was not used; its manifest-declared bundle patch supplied composition evidence. After parent/reviewer acceptance, the five-package extension reloaded the current Inspection class with stable positive link counts accepted; the original rejected bundle entry was not reread. All sources actually consumed still had link count 2. The parent-owned inspector was not edited by this lane.

Installed declarations identify every package below as 0.1.1-rc.2. This proves installed default behavior, not the opaque active profile's effective overrides or an executed cutover.

## Concrete storage and non-merge proof

| Consumer | Installed source and line proof | Result and limit |
|---|---|---|
| Home selector | dsh-home-paths lib/index.js:73-75; dshHomePath:82-83 | Explicit configured home, then nonblank DSH_HOME, then OS-home/.dsh; normalized absolute path. Configured overrides can supersede the environment selector. |
| Profile/plugin configuration | dsh-app-boot lib/index.js:318-325,353-368,539-565,575-576 | Profiles resolve under selected home/profiles/name. Missing web profile initializes only selected directory with empty dependencies, shipped base+web bundles and empty user patch. Composition starts from an empty root, with installation bundle patches plus the selected profile patch. No old-home profile merge in this traced path. Module fallback maintenance also targets selected home/profiles/node_modules (409-411). |
| Managed credentials and native records | dsh-credentials-local lib/index.js:57-60,425,648-658,672-688 | Default selected home/.credentials.yaml; config.path/config.dshHome can override. Missing selected file returns without loading another file. Existing flat-layout migration reads/writes only the selected filename. Ref/native-record state shares this managed file. Writes specify 0600 file and 0700 directory modes at557-559. |
| Authentication fallback exception | dsh-credentials-local lib/index.js:427-439; dsh-app-boot lib/index.js:726-748 | Inherited process credentials outrank the managed store; selected-home and cwd .env layers remain fallback inputs. DSH_HOME isolation alone therefore does not prove fresh authentication provenance. No environment values or files were read in this trace. |
| Settings | dsh-settings-file lib/index.js:30-33,133-144,163-172 | Default selected home/settings.yaml with explicit path/home override support. Missing selected file returns empty settings; writes target its selected filename. No old settings read in this path. |
| Session/history JSONL | base cordis.patch.yml:98-101; dsh-session-persistence-jsonl lib/index.js:790-791,805-807,1097-1119,1201-1204 | Composition passes dshHomePath('sessions'); backend derives log paths and writes beneath that configured root. Current profile could override root; a fresh reviewed candidate must preserve this binding. |
| Session search | base patch:117-121; web patch:30-33; dsh-session-query-sqlite lib/index.js:604-605,1073-1076 | Shipped composition is path ':memory:' and openAt never. It is not an old-profile durable database; custom config.path remains independently selectable. |
| Workspace registry | web patch:51-62,73-74; dsh-workspace lib/index.js:224-226,312-315; dsh-storage-domain lib/index.js:345-348; dsh-storage-json lib/index.js:246-262,285-288 | Workspace domain name workspace opens the selected json backend. Backend root is dshHomePath('storages'); each domain unit is stored at root/name.json. Workspace directories themselves are intentionally outside this registry and are not moved/copied by changing profile. |
| Attachment bytes | base patch:103-107; dsh-attachment-local lib/index.js:830-831 | Default selected home/attachments/v1, using resolveDshHome(config.dshHome). |
| Spill output exception | base patch:346-347; dsh-spill-local lib/index.js:27-29,120-121 | Shipped row supplies no root, so default is a private per-process directory under OS tmpdir, not DSH_HOME. Supported config.root can bind a future candidate's spills under its home. The selector alone is not an all-mutable-store boundary. |
| Background jobs | base patch:69-70; dsh-jobs-local lib/index.js:101-106,119-128 | In-memory Maps, not an old persisted job store. This is source evidence, not live job-state observation. |

## Extended default consumers and supported candidate conditions

| Consumer | Concrete source proof | Candidate condition |
|---|---|---|
| User agent presets | dsh-agent-presets lib/index.js:160,808-814,850-854 appends dshHomePath('.agent-presets'); web patch:441-445 mounts agent-presets with default standard. | Retain default selected-home user root; installation-provided system presets remain code/config, not old-profile state. Actual configured custom roots must not reintroduce old home. |
| Telemetry identity | dsh-session-telemetry-otel lib/index.js:105-116 returns immediately for DISABLED; anonymous identity call appears only later at136. Base patch:148-151 defaults DISABLED unless overridden. | Explicitly pin mode DISABLED in candidate; disabled branch never reaches identity creation or exporter. No need to inspect identity-file contents or its implementation for this candidate. |
| Skill roots | dsh-skill-filesystem lib/index.js:76-85,150-187 defaults to selected-home skills PLUS OS-home/.agents/skills and project .dsh/.agents roots. Schema:33,36 supports includeDefaultRoots and customSkillDirs. | Bare DSH_HOME does not isolate skill inputs. Supported configuration: includeDefaultRoots=false, customSkillDirs containing only selected-home/skills, and no explicit external bundledSkillDir. This disables inherited project/home skill roots while retaining a dedicated skill directory. |
| Skill registry | dsh-skill lib/index.js imports only service/schema/scope helpers and delegates collected candidates to providers; selected filesystem source owns the path roots above. | Keep explicit filesystem provider root policy; no old skill content was inspected. |
| Persona | dsh-persona lib/index.js:37-41 uses config.text and prompt/runtime-context options; no filesystem import in its entry. | Configuration belongs to selected profile/preset. No separate persona file store established or required by this source. |

Supported spill override is exact plugin row id **spill-local**, name **@deepseek-ai/dsh-spill-local** (base patch:346-347), field **config.root** (spill source:116,120-121). Binding root to the new selected home's spills directory is a supported candidate configuration, not a runtime mutation here. The shipped default's private OS-temp path is isolated per process but is not physically within DSH_HOME.

Authentication qualification supplied by the parent, not independently queried by this lane: the service's Environment names are only DSH_HOME/HOME/PATH, EnvironmentFiles and PassEnvironment are empty; initial /proc/829/environ names contain no provider credential variables; cwd /srv/dsh/workspaces/.env is absent. Initial environment metadata does not prove runtime-added credential absence. For a fresh candidate with no .env, these facts address known launch fallback sources at the observed time. Ongoing use still permits a future cwd .env; changing WorkingDirectory to the new home would address that path but departs from the original selector-only cutover contract and needs an explicit plan amendment. Do not claim a directory change is already performed or required by the home selector itself.

## Acceptance limits and exact next proof

1. Do not promote the home helper's all-user-data comment into a whole-profile PASS. Actual spill behavior supplies a concrete exception; process credentials supply another independent authentication input.
2. A candidate can use the already-supported spill config.root. It must also avoid explicit settings/credentials/session/storage path overrides to the old home, retain the selected home bindings, and establish inherited-authentication absence/provenance without disclosing values.
3. The named default consumer gaps were resolved by the five-package extension above. Candidate acceptance is conditional on the explicit spill, skill-root, telemetry and path-override policy, plus separately recorded launch-environment facts. This is not a claim that arbitrary later plugin installations or arbitrary user configuration remain confined; those are outside the traced shipped-default composition. No further generic plugin crawl is recommended.
4. Plugin fallback symlinks intentionally point to installation-owned packages; that is code reuse, not current-profile state reuse. Their static eligibility and future runtime writes belong in the separately reviewed candidate/cutover evidence.
5. Parent reports an absent cwd .env and known service DSH_HOME in separate selector evidence; this report does not independently refresh those live facts.
6. No static findings here establish candidate creation, runtime readiness, CRED-01, route success, or cutover authority.

## Minimal supported candidate patch inputs (not applied)

Observed base bundle IDs: spill-local at346, skill-filesystem at240, session-telemetry-otel at148. These exact rows permit the following candidate-only patch; this is configuration guidance, not a cutover command or approval:

```yaml
- id: spill-local
  config:
    root: /home/dsh/.dsh-profiles/vm105-provider-v1/spills
- id: skill-filesystem
  config:
    includeDefaultRoots: false
    customSkillDirs:
      - /home/dsh/.dsh-profiles/vm105-provider-v1/skills
- id: session-telemetry-otel
  config:
    mode: DISABLED
```

This small patch addresses traced non-home defaults; it does not itself establish zero provider routes, ambient-authentication isolation, candidate validation, or later profile-layer changes. Parent separately verified the unchanged explicit service command uses web --host 127.0.0.1 --port 3080, so candidate cutover should preserve that command and SSH-only access.

## Installed source identity ledger

Root logical package: /opt/deepseek-harness/node_modules/@deepseek-ai/dsh.
Root canonical package: /opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh@0.1.1-rc.2_7adf779e9bedfb2e97ced92905792931/node_modules/@deepseek-ai/dsh.
Root manifest SHA-256: dc930c0b18158f49ae3753ceaf6b1b7ae71dc6c8f45c85a2d679b142024addf7.

For every dependency, the logical link and canonical directory below were correlated using the parent's verified dependency declaration, then the dependency manifest name/version and source metadata were verified. All consumed manifest/source hashes identify installed public code, never secret state.

### dsh-base

- Logical: `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh@0.1.1-rc.2_7adf779e9bedfb2e97ced92905792931/node_modules/@deepseek-ai/dsh-base`
- Canonical: `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-base@0.1.1-rc.2_b6700999316794178df1eb7155dc0a46/node_modules/@deepseek-ai/dsh-base`
- Version: 0.1.1-rc.2
- package.json SHA-256: `35d203246e9c2a8e623da058cd9b1527252b6c4b4bf2acc56f5233a70db676df`
- cordis.patch.yml SHA-256: `9870a518274194c0e1ebd870cee2737fbc2ffc04ae36887871ffe6fcf74beac1` (link count 2)

### dsh-web-app

- Logical: `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh@0.1.1-rc.2_7adf779e9bedfb2e97ced92905792931/node_modules/@deepseek-ai/dsh-web-app`
- Canonical: `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-web-app@0.1.1-rc.2_ce3874dffedb66ab726b823cc1dadab8/node_modules/@deepseek-ai/dsh-web-app`
- Version: 0.1.1-rc.2
- package.json SHA-256: `f1ab1f51022e56adae15889764001aed390da0d647db08313d07b571265a27f1`
- cordis.patch.yml SHA-256: `7889b655be3809dd21e3c59023f8510e6e8425f6f37616e4ba20389f2e938dda` (link count 2)

### dsh-credentials-local

- Logical: `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-base@0.1.1-rc.2_b6700999316794178df1eb7155dc0a46/node_modules/@deepseek-ai/dsh-credentials-local`
- Canonical: `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-credentials-local@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai+ds_7bb67d14430a2d1ff3cabd2ed2468913/node_modules/@deepseek-ai/dsh-credentials-local`
- Version: 0.1.1-rc.2
- package.json SHA-256: `db3521c031061dddf4eebbd28cea8063b4dddd4007d530e2e1def5ff86dd757e`
- lib/index.js SHA-256: `1688f17801d5809abace4ef6228b771625a0153c043d7d4dba21b398ec4056eb` (link count 2)

### dsh-settings-file

- Logical: `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-base@0.1.1-rc.2_b6700999316794178df1eb7155dc0a46/node_modules/@deepseek-ai/dsh-settings-file`
- Canonical: `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-settings-file@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai+dsh-at_07dac851674f547bcb0fed2f2776d133/node_modules/@deepseek-ai/dsh-settings-file`
- Version: 0.1.1-rc.2
- package.json SHA-256: `2221515504477467b2a0b26a1c64522426b269a0dcd955e198363fb333ea3399`
- lib/index.js SHA-256: `524d02699bc9ce5b5db89aac944a5a4ea3b8e9daf89b298f02e1eb805673a339` (link count 2)

### dsh-session-persistence-jsonl

- Logical: `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-base@0.1.1-rc.2_b6700999316794178df1eb7155dc0a46/node_modules/@deepseek-ai/dsh-session-persistence-jsonl`
- Canonical: `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-session-persistence-jsonl@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepse_14f57a8dc717fa4ab0d46db3acee4cf9/node_modules/@deepseek-ai/dsh-session-persistence-jsonl`
- Version: 0.1.1-rc.2
- package.json SHA-256: `c4214db638bacee636f777e2b4cbc4940bf78deaa892037934e42392d83e279d`
- lib/index.js SHA-256: `8b6ebc4509a3e969ab3ad6e0dfb553ae4861e5b101831afed23e593d148d97f3` (link count 2)

### dsh-session-query-sqlite

- Logical: `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-base@0.1.1-rc.2_b6700999316794178df1eb7155dc0a46/node_modules/@deepseek-ai/dsh-session-query-sqlite`
- Canonical: `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-session-query-sqlite@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai_8ad53b91c340c6b558e2b3a4406f8efa/node_modules/@deepseek-ai/dsh-session-query-sqlite`
- Version: 0.1.1-rc.2
- package.json SHA-256: `1af230f33d67c93e69af9f50fa421ec635b074ade08ce138a183fe86cc2d3d7a`
- lib/index.js SHA-256: `d35c13881eeb9d393fa3a21acaafa6277692e77f90e579ea62a95d6ea0cf370a` (link count 2)

### dsh-attachment-local

- Logical: `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-base@0.1.1-rc.2_b6700999316794178df1eb7155dc0a46/node_modules/@deepseek-ai/dsh-attachment-local`
- Canonical: `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-attachment-local@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai+dsh_48db1ca9b536b07a9b9b8a3fb21f8dd4/node_modules/@deepseek-ai/dsh-attachment-local`
- Version: 0.1.1-rc.2
- package.json SHA-256: `207ac2fb21254ba93ad585b147bd80a6ff869f28cbf731abcfdbc3a0645fa0f6`
- lib/index.js SHA-256: `2d2be7d22cf89895e281489158a2f4c9984497dfcb880ad88b8740e2afec7e76` (link count 2)

### dsh-spill-local

- Logical: `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-base@0.1.1-rc.2_b6700999316794178df1eb7155dc0a46/node_modules/@deepseek-ai/dsh-spill-local`
- Canonical: `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-spill-local@0.1.1-rc.2_7314b9cfa55168b22f8f6fda35aa8983/node_modules/@deepseek-ai/dsh-spill-local`
- Version: 0.1.1-rc.2
- package.json SHA-256: `27707cc1e7746ccf97fb292cc82dd6d14c74f4b5613d8710e320f25f2a6d4e95`
- lib/index.js SHA-256: `ae92f47942cf63e656c409b3729fe5bdf22e232ec5d05fd14bc9f642b2eb2b0b` (link count 2)

### dsh-storage-json

- Logical: `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-web-app@0.1.1-rc.2_ce3874dffedb66ab726b823cc1dadab8/node_modules/@deepseek-ai/dsh-storage-json`
- Canonical: `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-storage-json@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai+dsh-inv_59f569bce1a393f7830e8147447e2db0/node_modules/@deepseek-ai/dsh-storage-json`
- Version: 0.1.1-rc.2
- package.json SHA-256: `ad83e2b0a6389bb685e74ade1dfe5b4c55a4fb5f2ad94ab12c62f814eee3edd9`
- lib/index.js SHA-256: `563bf17d4060fd280b746b13a03b9b843bf702e4229be73a4397657f75bc0db1` (link count 2)

### dsh-workspace

- Logical: `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-web-app@0.1.1-rc.2_ce3874dffedb66ab726b823cc1dadab8/node_modules/@deepseek-ai/dsh-workspace`
- Canonical: `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-workspace@0.1.1-rc.2_ca1aef6913f66bb64a14405a8170db89/node_modules/@deepseek-ai/dsh-workspace`
- Version: 0.1.1-rc.2
- package.json SHA-256: `0dbf7f622e4b7d930734135368907ed8256a707fab6f990582444772a78e790f`
- lib/index.js SHA-256: `d53e71d931937066ff20440afcff911ced09cefb8a0f3d024348b0e5248d4c74` (link count 2)

### dsh-storage-domain

- Logical: `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-web-app@0.1.1-rc.2_ce3874dffedb66ab726b823cc1dadab8/node_modules/@deepseek-ai/dsh-storage-domain`
- Canonical: `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-storage-domain@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai+dsh-i_1dd5e89577ac0f175d4162432caf3a24/node_modules/@deepseek-ai/dsh-storage-domain`
- Version: 0.1.1-rc.2
- package.json SHA-256: `bce55a9b0118d795e950e5aed10cbae55b407b491f7d85d909a0410d0f97a182`
- lib/index.js SHA-256: `604703d7f461001c95be48536a0f2b76ed8174dec4cba5bf1456a200c47ee72b` (link count 2)

### dsh-home-paths

- Logical: `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh@0.1.1-rc.2_7adf779e9bedfb2e97ced92905792931/node_modules/@deepseek-ai/dsh-home-paths`
- Canonical: `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-home-paths@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai+dsh-invar_260f8dde1d5adbe84fd51b779f4f83da/node_modules/@deepseek-ai/dsh-home-paths`
- Version: 0.1.1-rc.2
- package.json SHA-256: `736ff71c95173d31fb53ebe68451eff978c11b5b747cca6621d86a4504f78e9c`
- lib/index.js SHA-256: `b82aa631aa4bfdd5b02c67d48fce455b2ca73cbf66d2b7096a336b3800914340` (link count 2)

### dsh-app-boot

- Logical: `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh@0.1.1-rc.2_7adf779e9bedfb2e97ced92905792931/node_modules/@deepseek-ai/dsh-app-boot`
- Canonical: `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-app-boot@0.1.1-rc.2_d7ed335ddbfb7670edc51bd2c8928580/node_modules/@deepseek-ai/dsh-app-boot`
- Version: 0.1.1-rc.2
- package.json SHA-256: `ccf455c20e4b20687429dc33cac6857630bce5fe76be483bf2871952ae725c47`
- lib/index.js SHA-256: `9d4b7f214cd35b3e8ce4e027b12cca34a416d355577aeacbf08a5b324f0cabb6` (link count 2)

### dsh-jobs-local

- Logical: `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-base@0.1.1-rc.2_b6700999316794178df1eb7155dc0a46/node_modules/@deepseek-ai/dsh-jobs-local`
- Canonical: `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-jobs-local@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai+dsh-agent_fa0dcc68596217609c256ec409a4fd14/node_modules/@deepseek-ai/dsh-jobs-local`
- Version: 0.1.1-rc.2
- package.json SHA-256: `d281a711241b290de8e63952c91556db1e69c242768116f9f84c51e3b397d317`
- lib/index.js SHA-256: `fa4d847d0e7d99364ba875c97f45c2f8b81e51d8a33de0fe6af54acdeb1936a2` (link count 2)

### dsh-session-telemetry-otel

- Logical: `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-base@0.1.1-rc.2_b6700999316794178df1eb7155dc0a46/node_modules/@deepseek-ai/dsh-session-telemetry-otel`
- Canonical: `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-session-telemetry-otel@0.1.1-rc.2_0e329a50b6fe6a15de6a41bb5c1b84f9/node_modules/@deepseek-ai/dsh-session-telemetry-otel`
- Version: 0.1.1-rc.2
- package.json SHA-256: `ac1484a557fc10f8d0598e2d754895e1b5143edaac7a73c022da639c3e04256d`
- lib/index.js SHA-256: `22f031eccb0add4265b719a1ce50ae5a4c01d61c0ee3229fa3ebe7158e5e161a` (link count 2)

### dsh-skill-filesystem

- Logical: `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-base@0.1.1-rc.2_b6700999316794178df1eb7155dc0a46/node_modules/@deepseek-ai/dsh-skill-filesystem`
- Canonical: `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-skill-filesystem@0.1.1-rc.2_48868494a4b9bcea1966f12a762e8376/node_modules/@deepseek-ai/dsh-skill-filesystem`
- Version: 0.1.1-rc.2
- package.json SHA-256: `f0a4bd7e17b72ad22d03509d954acbe1119862363f032d4faa79b02ce3e72f83`
- lib/index.js SHA-256: `1aea87781ba5b4d44c7cfd6184d933a1c171a3fd2791456b65ebfc8b255f1221` (link count 2)

### dsh-skill

- Logical: `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-base@0.1.1-rc.2_b6700999316794178df1eb7155dc0a46/node_modules/@deepseek-ai/dsh-skill`
- Canonical: `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-skill@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai+dsh-invariants_59a2d92d9f246f83337b4268751f40ea/node_modules/@deepseek-ai/dsh-skill`
- Version: 0.1.1-rc.2
- package.json SHA-256: `be09a8c49f4a38be29be3b30258c1c0455b5fabc27622f1bb6d5ab317db5adb1`
- lib/index.js SHA-256: `5402787cbc95b4586e2c3aa4b0129e91094ad368b428aa19bcbbd8553bbfa9d7` (link count 2)

### dsh-agent-presets

- Logical: `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-web-app@0.1.1-rc.2_ce3874dffedb66ab726b823cc1dadab8/node_modules/@deepseek-ai/dsh-agent-presets`
- Canonical: `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-agent-presets@0.1.1-rc.2_5200ead8959daeaefdf3dd69ba905368/node_modules/@deepseek-ai/dsh-agent-presets`
- Version: 0.1.1-rc.2
- package.json SHA-256: `2074d078b3945c3a75d9483ce3aaec5ce28c377a6a27d63aef16e12fbd0907ee`
- lib/index.js SHA-256: `a0b417514e3d285ad5fef74867e8049af333ebdec6e4d7639e388aa0903e0039` (link count 2)

### dsh-persona

- Logical: `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh@0.1.1-rc.2_7adf779e9bedfb2e97ced92905792931/node_modules/@deepseek-ai/dsh-persona`
- Canonical: `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-persona@0.1.1-rc.2_c46449525c16bef5ec3490eab6722d56/node_modules/@deepseek-ai/dsh-persona`
- Version: 0.1.1-rc.2
- package.json SHA-256: `a84fbb0919c92b6a3e04b099cf4dc82587445c901eeab6845ad078e417176bf6`
- lib/index.js SHA-256: `37a223d0c44fac7fd9d69f55b972828b177db7092fc45302c8b1938e595b9ace` (link count 2)

## Zero-route follow-up and correction of skill-input scope

This later section supersedes the earlier proposed requirement to restrict host skill-filesystem roots. Web bundle lines342-353 disable the host skill-filesystem row; the selected standard agent preset independently mounts its own skill-filesystem row at83-84 with defaults. The exact composition file is `config/agent-presets/standard/agent.cordis.yml`, derived from web default standard, the installed shipped-preset root and agent-presets' COMPOSITION_FILE constant at146 (`agent.cordis.yml`). Canonical root is the dsh package listed above; file SHA-256 `fa14feb98daef20b810fef30bb7239a89a786de3c45c602b37743f7100d9a5af`, link count2.

The standard preset skill provider resolves its Harness home through current DSH_HOME (skill-filesystem:77,172), not a literal old Harness-home path. Project/OS .agents skill roots are intentional read-only inputs, not migrated mutable profile stores. Its source imports access/lstat/readFile/readdir/stat and watcher operations; its watcher/cache state is in-memory Maps. Thus those external inputs do not by themselves require feature removal for mutable-profile isolation. Remove the earlier host skill-filesystem patch from candidate inputs; it neither controls the standard preset nor supplies additional necessary mutable-store isolation. Arbitrary later profile overrides remain outside this static claim.

### Zero usable inference routes

Actual base defaults are not zero-route: agent-default-model row63-67 selects deepseek-official/deepseek-v4-flash, llm-deepseek row450-451 registers an adapter, and web-search-deepseek row409-412 supplies a separate auxiliary model request path. Empty credentials is not evidence of zero usable routes.

A minimal candidate-only configuration is supported by installed source:

```yaml
- id: llm-deepseek
  disabled: true
- id: web-search-deepseek
  disabled: true
- id: llm-pi-ai
  config:
    providers: {}
```

Keep the llm registry and dormant llm-pi-ai plugin mounted. Pi-ai schema line966 defaults providers to {}; resolveProfiles996-998 enumerates only configured entries; ensureRegistrationFacts2461-2467 returns before registerAdapter when no routes exist. Its configurable-provider directory and model-discovery registrations remain available (2437,2455), so later owner configuration has its native surface. This requires a fresh empty settings document; a later settings entry can intentionally activate a route.

The LLM registry initializes an empty adapter Map (1137-1140), lists only registered adapters (1240-1241), and resolves only the explicitly named route: registration1527-1530 throws NO_ADAPTER when absent. There is no alternate-provider fallback in that lookup/dispatch path; prepareCall1496-1498 and streamWithRegistration1562-1568 use it. This is static zero-route/fail-closed evidence, not a black-box invalid-credential test or Phase4 attribution PASS.

Direct DeepSeek registers deepseek-official unconditionally at lib/index.js:1591,1801, confirming why disabling its row is necessary. The auxiliary web-search provider is disabled separately because it does not depend on LLM adapter registration. No invented global fallback setting is proposed.

### No provider/model selection is a separate condition

The agent-default-model service schema requires provider/model (lib/index.js:33-35); it has no documented null/none switch. Disabling exact row agent-default-model removes this composition's default service, but that provider's own source cannot prove every Web consumer tolerates absence. Do not equate zero registered routes with no configured default selection or claim complete UI readiness until the relevant gateway consumer is checked. No candidate or service was changed in this follow-up.

A first SSH invocation had a local key-path typographical error and failed authentication before any remote source execution; the corrected invocation used the already approved exact key path. No credential values were involved.

### Additional installed-source ledger

- dsh-llm: logical `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-base@0.1.1-rc.2_b6700999316794178df1eb7155dc0a46/node_modules/@deepseek-ai/dsh-llm`; canonical `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-llm@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai+dsh-attachment@0_de8559ed89b7370843bac1bad71a6196/node_modules/@deepseek-ai/dsh-llm`; version0.1.1-rc.2; manifest SHA-256 `252de11f9af2a92e2e2eb26dc4e80f7b6313586a96ffce16069435b536952cf6`; lib/index.js SHA-256 `90de54c106866d9333ddc312176e14df75e7c5ee1d6e54443174a827302276fd`.
- dsh-llm-pi-ai: logical `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-base@0.1.1-rc.2_b6700999316794178df1eb7155dc0a46/node_modules/@deepseek-ai/dsh-llm-pi-ai`; canonical `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-llm-pi-ai@0.1.1-rc.2_236ec8963c16cce3286da2b293de8170/node_modules/@deepseek-ai/dsh-llm-pi-ai`; version0.1.1-rc.2; manifest SHA-256 `b50f77d01dbdffbee612f9969903952c131956e5b28d806c7c82a7f715753f89`; lib/index.js SHA-256 `e183a9cdde703b47485410bd68d247c8becdb277c390f0f91c6dd28718d350e2`.
- dsh-llm-deepseek: logical `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-base@0.1.1-rc.2_b6700999316794178df1eb7155dc0a46/node_modules/@deepseek-ai/dsh-llm-deepseek`; canonical `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-llm-deepseek@0.1.1-rc.2_a4f32a8d2888fcc753211ed9471efdc6/node_modules/@deepseek-ai/dsh-llm-deepseek`; version0.1.1-rc.2; manifest SHA-256 `4d919cec96dd511db44bfc9eee26bdba19dfaaf9eb2ef5cd2788e6d385be1cd3`; lib/index.js SHA-256 `eed9492246cc6451f060de211768d3128388046478deae7f1959de7cde56ea82`.
- dsh-agent-default-model: logical `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-base@0.1.1-rc.2_b6700999316794178df1eb7155dc0a46/node_modules/@deepseek-ai/dsh-agent-default-model`; canonical `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-agent-default-model@0.1.1-rc.2_cffd0b3811dd3fb50ded7f3d23c3fd53/node_modules/@deepseek-ai/dsh-agent-default-model`; version0.1.1-rc.2; manifest SHA-256 `584001c0295a60b907c6118eb7f5da29ed85095d563e19669736d87536d08cd0`; lib/index.js SHA-256 `3f9ec5b953658fa1d0b3684b404a8da62ed61b5770ca8dd6b72ce937bae21ecf`.

### Gateway follow-up result

The exact base-declared dsh-api-gateway entry has static inject ['typert'] at50 and optional connection injection at61; its complete entry contains no agentDefaultModel/defaultModel/currentSelection reference. Disabling the default-model service does not remove a dependency of this gateway wrapper. The wrapper dispatches generated Remote methods, so this observation is not a proof that every remote/UI consumer tolerates the absent service.

An additional candidate row `id: agent-default-model; disabled: true` removes the shipped default selection at composition level. Combined with disabled llm-deepseek and web-search-deepseek, dormant pi-ai and an empty fresh settings layer, this provides static no-selection/zero-route intent through supported row disabling. It does not warrant a Web readiness PASS until startup and relevant settings/selection consumers are verified. There is no supported null/none provider/model value established by the inspected schema.

- dsh-api-gateway logical: `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-base@0.1.1-rc.2_b6700999316794178df1eb7155dc0a46/node_modules/@deepseek-ai/dsh-api-gateway`
- canonical: `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-api-gateway@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai+dsh-clie_589a9bcbaefa93b267d467a3607f6172/node_modules/@deepseek-ai/dsh-api-gateway`
- version: 0.1.1-rc.2; manifest SHA-256 `2fa7595b121c14805a4fc1e83c0cc0ceff5660f21c995a93a30e1dd5ea543652`
- lib/index.js SHA-256: `266fd319e360e9237382be7c180f83b60e1706740b652df768189bae8fc87798`; link count 2

### Final no-selection candidate recommendation

The web-declared dsh-api-remotes entry also contains no agentDefaultModel/defaultModel/currentSelection/saveSelection reference. Its observed integration is ctx.inject(['typert']) at155; together with the gateway wrapper above, this consumer chain has no mandatory default-model-service dependency. No known boot-blocking dependency was found in this bounded chain. This is sufficient to recommend static preparation with the exact supported row disables below while retaining runtime readiness NOT PROVEN until the separate cutover test.

```yaml
- id: agent-default-model
  disabled: true
- id: llm-deepseek
  disabled: true
- id: web-search-deepseek
  disabled: true
- id: llm-pi-ai
  config:
    providers: {}
```

Keep llm, settings, credentials, provider UI and dormant pi-ai mounted. Retain the supported spill-root and telemetry-DISABLED candidate overrides; omit the earlier host skill-filesystem restriction. A later owner-selected provider must explicitly restore/configure the required model-selection surface; no automatic inference or fallback is enabled by preparation. Empty adapters still enforce NO_ADAPTER rather than choosing another route. No fabricated fallback:false or empty-string model configuration is used.

- dsh-api-remotes logical: `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-web-app@0.1.1-rc.2_ce3874dffedb66ab726b823cc1dadab8/node_modules/@deepseek-ai/dsh-api-remotes`
- canonical: `/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-api-remotes@0.1.1-rc.2_0037c360ed8ef45e74e856e82932995e/node_modules/@deepseek-ai/dsh-api-remotes`
- version: 0.1.1-rc.2; manifest SHA-256 `c659c35186ac4503ff34264ae09b89986cc8fa8351330b9089f5b0a3d6ce698e`
- lib/index.js SHA-256: `5406e17c29e42b81ebb8c36030a67de3db19d4d94bace10052b924d72a10e756`; link count 2
