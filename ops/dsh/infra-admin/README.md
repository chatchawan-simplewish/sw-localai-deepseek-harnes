# DeepSeek Harness infrastructure-admin operations

This broker is local-only: `127.0.0.1:8182`. It is not a LAN or public
listener. The DSH client service is `deepseek-harness`; the broker service is
`deepseek-harness-infra-admin`.

## Trust boundary

`run_infrastructure_command` provides full Proxmox-root administration. The
model/caller is therefore trusted with command output that can be potentially
sensitive, including output reachable from a fixed host through guest-agent
access. This broker does not enforce secret isolation. It does keep the SSH
keys and bearer tokens out of DSH configuration and workspaces; that is a
provisioning/storage boundary, not a restriction on root-command output.

## Fixed SSH targets

| Alias | Host | Authorized-key comment | Public-key fingerprint |
| --- | --- | --- | --- |
| `prox-01` | `192.168.1.201` | `dsh-infra-admin@vm105-prox-01` | `SHA256:MJqvcx/7XTmnlBjADZdQoArip0mEElK2zX1AMR8syV8` |
| `prox-03` | `192.168.1.203` | `dsh-infra-admin@vm105-prox-03` | `SHA256:NuXkgwJQNsr++kk8qQPWysn+xNWIXzwWUnD7GFCmd64` |
| `prox-04` | `192.168.1.204` | `dsh-infra-admin@vm105-prox-04` | `SHA256:2NmLycR3+FAbBuOmtfe6WGfGaPs89+SMx7wVv1Xmyqg` |

The matching private keys live only on VM105 under
`/etc/dsh-infra-admin/keys/`; key material is intentionally not documented.

## Revocation

Perform these steps as an authorized administrator, recording only status:

1. On each target host, remove only the single `/root/.ssh/authorized_keys`
   line whose comment exactly matches the alias above. Do not replace the
   file or remove unrelated keys.
2. Before deleting the VM105 key, prove that the revoked identity fails to
   authenticate to its target using that alias with `BatchMode=yes`,
   `IdentitiesOnly=yes`, and `IdentityAgent=none`; record only the non-zero
   exit status. A successful connection is a stop. Existing sessions and
   remote jobs need separate inspection; removing an authorized-key line
   governs future authentication only.
3. On VM105, delete only the associated key file
   (`/etc/dsh-infra-admin/keys/prox-01_ed25519`, `prox-03_ed25519`, or
   `prox-04_ed25519`).
4. Generate and store a replacement bearer token directly on VM105 in the
   root-owned 0600 `broker.env` and `mcp.env` files without printing or
   sourcing either file. Keep the prior token only in approved protected
   memory/storage long enough to test revocation.
5. Restart both `deepseek-harness-infra-admin` and `deepseek-harness`.
6. Send a valid MCP request through approved secret handling, recording only
   HTTP status codes: the prior bearer token must receive `401`; the
   replacement token must authenticate successfully. Do not print, source,
   or record either token value. Treat any failed check as a stop and keep
   the revoked path unavailable.

## Status-only checks

These commands report status and do not print credentials or key material:

```sh
systemctl is-active deepseek-harness deepseek-harness-infra-admin
curl --silent --show-error --output /dev/null --write-out '%{http_code}\n' http://127.0.0.1:8182/mcp
ssh -F /etc/dsh-infra-admin/ssh_config -o BatchMode=yes prox-01 hostname
ssh -F /etc/dsh-infra-admin/ssh_config -o BatchMode=yes prox-03 hostname
ssh -F /etc/dsh-infra-admin/ssh_config -o BatchMode=yes prox-04 hostname
```

Expected evidence: both services `active`; unauthenticated broker check
`401`; each non-revoked strict SSH check reaches its expected host. For the
revoked target, the identity-specific SSH check above must fail before its
private key is deleted. A DSH UI reload must also be performed and recorded as
PASS/WARN/NOT PROVEN by the operator.
