# Infrastructure administration handoff

Use the `infrastructure-admin` MCP for Proxmox and VM administration. It is
already authenticated; do not look for, request, read, copy, or display SSH
keys, bearer tokens, environment files, or `authorized_keys`.

## Choose the target

- `infrastructure_inventory` is the first tool to use for VM location or
  current-state questions.
- `run_infrastructure_command` accepts only these fixed Proxmox aliases:
  `prox-01`, `prox-03`, and `prox-04`.
- The broker selects the dedicated host identity automatically. There is no
  key name, file path, or credential value for a DSH session to choose.
- Manage guests through their current Proxmox host. Do not assume a VM stays
  on the same host; inspect inventory first.

## Safe operating rules

- This is owner-approved **full Proxmox-root administration**. Treat all tool
  output as potentially sensitive and never intentionally retrieve or repeat
  credentials, tokens, private keys, or secret files.
- Start with a narrow read-only command such as `qm list`, `qm status <vmid>`,
  or a documented `pvesh get` query. Explain an intended state-changing
  command before running it.
- Use only the fixed aliases. A target outside the list is rejected.
- `timeoutSeconds` stops waiting for the local SSH client only. If it times
  out, the remote result is unknown: inspect Proxmox task or VM state before
  retrying.
- Do not use this MCP for Cloudflare or Coolify; use their separate MCP tools.

## Recovery and revocation

If this MCP is unavailable, report the alias, requested operation, and error
without attempting to recover credentials. The human operator can use the
project runbook at `ops/dsh/infra-admin/README.md` to revoke or repair access.
