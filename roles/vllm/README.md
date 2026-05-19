# vllm

Drops a `docker-compose.yml` + `.env` into `vllm_dir` and brings up the
`vllm/vllm-openai` container on `vllm_port`. Health-checks `/v1/models`
with the vault'd API key, retrying up to `vllm_health_retries`
× `vllm_health_delay` seconds (default = 10 minutes, enough for a cold
HF model download).

Requires the `docker` role (for `nvidia` default runtime + the
`python3-docker` / `python3-yaml` deps used by `community.docker.docker_compose_v2`).

## Variables

| Variable | Default | Notes |
|---|---|---|
| `vllm_dir` | `/opt/vllm` | Project directory; holds compose + env. |
| `vllm_image` | `vllm/vllm-openai:latest` | Pin a tag for reproducibility. |
| `vllm_model` | `meta-llama/Meta-Llama-3.1-8B-Instruct` | Any HF model vLLM supports. |
| `vllm_served_model_name` | `llama-3.1-8b` | Clients use this as `model=`. |
| `vllm_port` | `8000` | Host port. |
| `vllm_tensor_parallel_size` | `1` | Shard across GPUs. |
| `vllm_max_model_len` | `8192` | Context length. |
| `vllm_gpu_memory_utilization` | `0.90` | Fraction of VRAM. |
| `vllm_hf_cache` | `/opt/vllm/hf-cache` | Bind-mounted into the container. |
| `vllm_health_retries` | `60` | × `vllm_health_delay` seconds. |
| `vllm_health_delay` | `10` | Seconds between health checks. |

Vault: `vault_vllm_api_key` (required), `vault_hf_token` (gated models).
