# DeepSeek Harness Infrastructure Admin MCP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give DeepSeek Harness full, auditable administration of the live Proxmox cluster and its VMs without copying any existing private key into the Harness configuration or browser-visible workspace. Full root administration explicitly trusts the model/caller with potentially sensitive command output; it does not enforce secret isolation.

**Architecture:** A root-owned, loopback-only Streamable HTTP MCP broker on VM105 uses newly generated, host-specific SSH identities to reach the three Proxmox nodes as root. The broker exposes an explicit inventory tool and an intentionally full-admin command tool; DeepSeek Harness authenticates to it with a separate bearer token held only in root-owned environment files.

**Tech Stack:** Node 24, installed MCP SDK 1.30.0, systemd, OpenSSH, DeepSeek Harness `@deepseek-ai/dsh-mcp-client`, Proxmox SSH.

## Global Constraints

- Do not copy, display, commit, log, or place existing SSH private keys, API tokens, OAuth material, or bearer tokens in a DSH workspace.
- The full-admin command may return potentially sensitive output reachable by Proxmox root or its guest-agent access. Treat the model/caller as trusted with that output; key/token exclusion from DSH configuration and workspaces is a provisioning/storage control, not enforced secret isolation.
- Generate three new Ed25519 identities on VM105: one per Proxmox host; use `StrictHostKeyChecking=yes` with verified host keys.
- The broker binds only to `127.0.0.1:8182` and authenticates every MCP request with `MCP_INFRA_ADMIN_TOKEN`.
- Full administration is owner-authorized: the command tool may run arbitrary commands only against the named Proxmox hosts, never against an arbitrary network address.
- Preserve existing DSH MCP entries and all unrelated dirty work; stage exact paths only if a commit is requested.

---

### Task 1: Create the broker and DSH configuration assets

**Files:**
- Create: `ops/dsh/infra-admin/server.mjs`
- Create: `ops/dsh/infra-admin/deepseek-harness-infra-admin.service`
- Modify: `ops/dsh/profiles/web/cordis.patch.yml`

**Interfaces:**
- Consumes: `MCP_INFRA_ADMIN_TOKEN`, `/etc/dsh-infra-admin/ssh_config`, and the three target aliases `prox-01`, `prox-03`, `prox-04`.
- Produces: Streamable HTTP endpoint `http://127.0.0.1:8182/mcp`, tools `infrastructure_inventory` and `run_infrastructure_command`.

- [ ] **Step 1: Write the broker with a failed-auth boundary**

Implement a Node ESM MCP server that returns HTTP 401 unless the exact bearer token matches using `crypto.timingSafeEqual`. Bind it to loopback port 8182; do not add a network listener or reverse proxy.

- [ ] **Step 2: Add the two tools**

`infrastructure_inventory` runs a fixed `pvesh get /cluster/resources --type vm` through each fixed alias. `run_infrastructure_command` accepts `{ target: 'prox-01'|'prox-03'|'prox-04', command: string, timeoutSeconds?: number }`, invokes `/usr/bin/ssh` without a local shell, limits output to 128 KiB, and records only target, exit status, remote outcome, output truncation, and a SHA-256 command digest in journald. `timeoutSeconds` limits the local SSH client only: timeout metadata is `remoteOutcome: unknown`, and callers must inspect remote task state before retrying.

- [ ] **Step 3: Add a hardened systemd unit**

Run as root only because the requested target account is Proxmox root. Use `EnvironmentFile=/etc/dsh-infra-admin/broker.env`, `Restart=on-failure`, `NoNewPrivileges=true`, `PrivateTmp=true`, `ProtectHome=true`, `ProtectSystem=strict`, and `ReadOnlyPaths=/etc/dsh-infra-admin`.

- [ ] **Step 4: Add the DSH MCP client row**

Append one `mcp-infrastructure-admin` client row to the existing profile: `serverName: infrastructure-admin`, `transport: streamable-http`, `url: http://127.0.0.1:8182/mcp`, bearer header `${process.env.MCP_INFRA_ADMIN_TOKEN}`. Keep the value out of YAML.

- [ ] **Step 5: Run local static checks**

Run `node --check ops/dsh/infra-admin/server.mjs` and a text check confirming the profile contains exactly one `mcp-infrastructure-admin` row.

### Task 2: Provision dedicated VM105-to-Proxmox identities

**Files:**
- Create remotely: `/etc/dsh-infra-admin/keys/prox-01_ed25519`, `/etc/dsh-infra-admin/keys/prox-03_ed25519`, `/etc/dsh-infra-admin/keys/prox-04_ed25519`
- Create remotely: `/etc/dsh-infra-admin/known_hosts`
- Create remotely: `/etc/dsh-infra-admin/ssh_config`

**Interfaces:**
- Consumes: verified Proxmox host keys and one existing operator credential only for initial public-key installation.
- Produces: three distinct root SSH paths from VM105 with `IdentitiesOnly=yes` and `StrictHostKeyChecking=yes`.

- [ ] **Step 1: Verify each existing management path read-only**

Run `hostname` through the current strict operator path to each Proxmox host before changing authorization. Stop if an expected host key or identity fails.

- [ ] **Step 2: Generate host-specific keys on VM105**

Create the key directory mode 0700, generate each Ed25519 key mode 0600 as root, and write a root-owned SSH config that maps the three fixed aliases to their verified hosts and dedicated key files.

- [ ] **Step 3: Install public keys on the matching Proxmox root account**

Append a uniquely commented key to the matching `/root/.ssh/authorized_keys` entry, never replacing the file. Verify the public-key fingerprint and a strict VM105-to-host `hostname` command.

- [ ] **Step 4: Verify the SSH configuration has no arbitrary-network route**

Confirm the generated SSH config includes only the three fixed aliases and no wildcard Host block. Broker-side malformed-target rejection is verified after the broker exists in Task 3.

### Task 3: Deploy, connect, and verify the broker

**Files:**
- Create remotely: `/opt/dsh-infra-admin/server.mjs`
- Create remotely: `/etc/systemd/system/deepseek-harness-infra-admin.service`
- Modify remotely: `/etc/deepseek-harness/mcp.env`
- Modify remotely: `/home/dsh/.dsh/profiles/web/cordis.patch.yml`

**Interfaces:**
- Consumes: broker assets and the dedicated root-owned bearer token.
- Produces: active `deepseek-harness-infra-admin.service` and an active DSH configuration containing the admin MCP client.

- [ ] **Step 1: Deploy code, wire the pinned SDK, and generate one new broker bearer token**

Copy source/unit without secrets. Create `/opt/dsh-infra-admin/node_modules/@modelcontextprotocol/sdk` as a symlink to the installed pinned SDK and `/opt/dsh-infra-admin/node_modules/zod` as a symlink to its installed Zod dependency; do not run `npm install`. Generate a new random token directly on VM105, and write it to both root-owned environment files with mode 0600. Do not source either file with a shell.

- [ ] **Step 2: Start the broker before changing DSH**

Run `node --check`, `systemctl daemon-reload`, start the broker, and make an unauthenticated loopback request that returns 401. This is the failing-auth regression check.

- [ ] **Step 3: Enable the DSH MCP entry**

Deploy the profile patch, restart `deepseek-harness`, and verify both services are active. Preserve the existing Cloudflare and Coolify MCP entries.

- [ ] **Step 4: Verify end-to-end capability without changing infrastructure**

Use the broker's `infrastructure_inventory` tool to return the Proxmox VM inventory and verify a malformed `run_infrastructure_command.target` is rejected before SSH is spawned. Do not run state-changing VM commands as the acceptance test.

### Task 4: Record revocation and recovery information

**Files:**
- Create: `ops/dsh/infra-admin/README.md`

- [ ] **Step 1: Document non-secret target and revoke procedure**

Record aliases, service names, public-key comments/fingerprints, broker port, and exact revocation steps: remove the matching authorized-key line from each Proxmox host; prove that exact key now fails before deleting its VM105 private key; rotate the bearer token; prove the old token gets `401` while the replacement authenticates; and restart the two services. Do not print or source secrets.

- [ ] **Step 2: Run final checks**

Run `systemctl is-active deepseek-harness deepseek-harness-infra-admin`, loopback broker authentication checks, strict SSH checks to all three aliases, and a DSH UI reload. Report only PASS/WARN/NOT PROVEN evidence.
