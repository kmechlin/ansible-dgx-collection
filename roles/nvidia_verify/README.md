# nvidia_verify

Verifies that `nvidia-smi` runs and the installed driver meets a minimum
major version. DGX OS ships with a driver — this role does not reinstall it.

## Variables

| Variable | Default | Notes |
|---|---|---|
| `nvidia_verify_min_driver` | `"550"` | Major version. Fails if older. |
