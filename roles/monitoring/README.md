# monitoring

Installs:

- `node_exporter` (binary release pinned to `node_exporter_version`) as a
  system service running under a dedicated `node_exporter` user.
- `dcgm-exporter` (NVIDIA's GPU exporter) as a container managed by a
  systemd wrapper unit, with `--gpus all`.

Both bind to `monitoring_bind` so by default they're loopback-only.
Flip `monitoring_bind` to the Tailscale IP (or `0.0.0.0`) if you scrape
from a remote Prometheus.

## Variables

| Variable | Default | Notes |
|---|---|---|
| `monitoring_bind` | `127.0.0.1` | Bind address for both exporters. |
| `node_exporter_version` | `1.8.1` | Pinned. |
| `node_exporter_port` | `9100` | Standard. |
| `dcgm_exporter_image` | `nvcr.io/nvidia/k8s/dcgm-exporter:3.3.7-3.5.0-ubuntu22.04` | NVIDIA-hosted image. |
| `dcgm_exporter_port` | `9400` | Standard. |
