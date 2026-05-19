# k3s_gpu

Single-node k3s install. Opt-in via `k3s_install: true` at the playbook
level. K3s 1.27+ with nvidia-container-toolkit on the host auto-detects
the NVIDIA runtime and creates a `nvidia` runtimeclass — so all this role
does is install k3s and (optionally) drop the NVIDIA k8s device plugin
manifest into the auto-apply directory.

## Variables

| Variable | Default | Notes |
|---|---|---|
| `k3s_install` | `false` | Gate the whole role. |
| `k3s_gpu_operator_install` | `false` | Apply the NVIDIA device plugin DaemonSet. |
| `k3s_version` | `v1.30.2+k3s1` | Pinned for reproducibility. |
| `k3s_device_plugin_version` | `v0.15.0` | NVIDIA k8s device plugin manifest tag. |

Vault: `vault_k3s_token` (required when `k3s_install: true`).
