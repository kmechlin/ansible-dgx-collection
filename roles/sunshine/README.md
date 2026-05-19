# sunshine

Installs Sunshine from the upstream .deb (LizardByte releases) and runs
it as a **user systemd service** under `sunshine_user`, with linger
enabled so the service starts at boot. User-scope is required so Sunshine
can attach to the X session.

## Variables

| Variable | Default | Notes |
|---|---|---|
| `sunshine_user` | `ubuntu` | Owner of the user systemd unit. |
| `sunshine_version` | `0.23.1` | Pin a known-good release. |
| `sunshine_deb_url` | derived | Ubuntu 22.04 or 24.04 .deb from upstream. |

## After install

- Browse to `https://<host>:47990` on first boot, set admin user/password.
- Pair Moonlight clients with the PIN flow.
- If the user service fails on first run, log in interactively as
  `sunshine_user` once (creates `/run/user/$UID`), then re-run.
