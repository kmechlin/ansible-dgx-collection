# tailscale

Installs Tailscale from the upstream apt repo and runs `tailscale up` with an
auth key from the vault. Idempotent: skips the `up` call if the daemon is
already logged in.

## Variables

| Variable | Default | Notes |
|---|---|---|
| `tailscale_ssh` | `true` | Enables Tailscale SSH. |
| `tailscale_advertise_routes` | `[]` | List of CIDRs to advertise. |
| `tailscale_extra_args` | `[]` | Reserved for future passthrough flags. |

Required vault variable: `vault_tailscale_auth_key`.
