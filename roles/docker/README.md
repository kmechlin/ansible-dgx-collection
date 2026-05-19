# docker

Installs docker-ce, the compose v2 plugin, and the NVIDIA container toolkit,
then writes `/etc/docker/daemon.json` with `nvidia` as the default runtime.
Runs a smoke test (`docker run --rm --gpus all nvidia/cuda nvidia-smi`).

## Variables

| Variable | Default | Notes |
|---|---|---|
| `docker_users` | `[]` | Usernames to add to the `docker` group. |
| `docker_default_runtime` | `nvidia` | Set to `runc` to keep nvidia opt-in via `--gpus all`. |
| `docker_smoke_image` | `nvidia/cuda:12.4.1-base-ubuntu22.04` | Image used for the post-install smoke test. |
| `docker_install_smoke_test` | `true` | Skip the smoke test in air-gapped envs. |
