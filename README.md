# kmechlin.dgx

Ansible collection for provisioning headless NVIDIA DGX-class workstations
(Lenovo PGX, DGX Station, DGX Spark) running DGX OS, so the box is reachable
remotely for two workloads:

1. **Remote desktop** — Sunshine (host) + Moonlight (clients), with a virtual
   X display so the headless GPU has something to capture.
2. **AI model serving** — vLLM running under Docker Compose, exposing an
   OpenAI-compatible API on `:8000`.

Both are reached over **Tailscale** (no port forwarding). The collection also
sets up Docker + nvidia-container-toolkit, optional single-node k3s with the
NVIDIA runtime + device plugin, and Prometheus monitoring (node_exporter +
DCGM exporter).

## Requirements

- Target: DGX OS (Ubuntu 22.04 jammy or 24.04 noble base), NVIDIA driver
  already installed (DGX OS ships with it).
- Control node: Ansible >= 2.15, Python 3.10+.
- SSH access as a sudo-capable user.

## Quickstart

```bash
git clone https://github.com/kmechlin/ansible-dgx-collection.git
cd ansible-dgx-collection

python3 -m venv venv && source venv/bin/activate
pip install ansible ansible-lint yamllint

make deps                   # ansible-galaxy collection install

# Edit inventory/hosts.yml so ansible_host / ansible_user point at the DGX.
vim inventory/hosts.yml

# Create the encrypted vault file:
cp inventory/vault.example.yml inventory/group_vars/all/vault.yml
ansible-vault encrypt inventory/group_vars/all/vault.yml
# Fill in real secrets, save+exit.

make ping                   # SSH + become smoke test
make site                   # full provision
```

Piecemeal:

```bash
make remote-desktop         # virtual_display + sunshine
make ai                     # docker + vllm
make tailscale
make monitoring
make k3s                    # after flipping k3s_install: true
```

## Configuration

All knobs live in `inventory/group_vars/all/main.yml`. The most likely tweaks:

| Variable | Default | Notes |
|---|---|---|
| `vllm_model` | `meta-llama/Meta-Llama-3.1-8B-Instruct` | Llama is gated — set `vault_hf_token`. |
| `vllm_served_model_name` | `llama-3.1-8b` | What clients pass as `model=`. |
| `vllm_tensor_parallel_size` | `1` | Bump to shard across multiple GPUs. |
| `vllm_max_model_len` | `8192` | Long context costs VRAM. |
| `vllm_gpu_memory_utilization` | `0.90` | Lower if you want headroom. |
| `virtual_display_width/height/refresh` | `3840/2160/60` | Match what your Moonlight client can decode. |
| `sunshine_version` | `0.23.1` | Pinned; bump deliberately from upstream releases. |
| `k3s_install` | `false` | Opt-in. Set `k3s_gpu_operator_install: true` for device plugin. |
| `monitoring_bind` | `127.0.0.1` | Flip to the Tailscale IP if scraping remotely. |
| `tailscale_ssh` | `true` | When confirmed working, disable port-22 exposure. |

Vault secrets (`inventory/group_vars/all/vault.yml`, gitignored):

- `vault_tailscale_auth_key` — https://login.tailscale.com/admin/settings/keys
- `vault_hf_token` — for gated HF models
- `vault_vllm_api_key` — long random string; gates `/v1/*`
- `vault_k3s_token` — only if `k3s_install: true`

## After it's up

- **Moonlight:** browse to `https://<tailscale-name>:47990`, set admin
  user + password, then pair from any Moonlight client using the PIN flow.
- **vLLM:** any OpenAI SDK works. Set `OPENAI_BASE_URL=http://<tailscale-name>:8000/v1`
  and `OPENAI_API_KEY=<vault_vllm_api_key>`. See `docs/openai-client.example.py`.
- **Prometheus:** scrape `:9100` (host) and `:9400` (GPU). See
  `docs/prometheus-scrape.example.yml`. Grafana DCGM dashboard:
  https://grafana.com/grafana/dashboards/12239

## Roles

| Role | Purpose |
|---|---|
| `nvidia_verify` | `nvidia-smi` + minimum-driver assertion. |
| `docker` | docker-ce + compose plugin + nvidia-container-toolkit, `nvidia` default runtime, GPU smoke test. |
| `tailscale` | apt install + `tailscale up --authkey --ssh`. |
| `virtual_display` | Generated EDID, `/etc/X11/xorg.conf.d` snippet, lightdm enabled. |
| `sunshine` | Upstream .deb install + user systemd unit + linger. |
| `vllm` | `/opt/vllm` docker compose stack, vault'd `.env`, `/v1/models` health-check. |
| `k3s_gpu` | k3s with NVIDIA runtime, optional NVIDIA k8s device plugin. |
| `monitoring` | node_exporter binary + systemd, dcgm-exporter container. |

## Status

Fresh scaffold — **not yet validated against real hardware.** Expect to
iterate on the first `make site` run. Known caveats:

- Sunshine first-boot may need an interactive login as `sunshine_user`
  before the user systemd service starts cleanly.
- The EDID generator produces a valid 128-byte EDID 1.3 blob but is not
  bit-accurate to any real panel. If the NVIDIA driver rejects it, ship a
  known-good EDID binary from a Dell U2718Q or similar 4K panel.
- For DGX A100/H100 datacenter cards with no display outputs, the virtual
  display approach won't work — you'd need Xvfb/VirtualGL instead.

## License

Apache-2.0
