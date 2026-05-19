# CLAUDE.md

## Repository

- **Repo:** `kmechlin/ansible-dgx-collection`
- **Collection FQCN:** `zelos.dgx`
- **Purpose:** Provision headless NVIDIA DGX-class workstations (Lenovo PGX,
  DGX Station, DGX Spark) running DGX OS, so the box is reachable remotely
  for (1) Sunshine/Moonlight remote desktop and (2) vLLM AI model serving.
  All access is over Tailscale.
- **State:** v0.1.0 scaffold. **Not yet validated against real hardware.**

## Active Branch

- Work on: `claude/ansible-remote-ai-setup-aLg4U`

## Layout

```
ansible-dgx-collection/
├── ansible.cfg
├── galaxy.yml                 # namespace=zelos, name=dgx, version=0.2.0
├── Makefile                   # make bootstrap / setup / site / snapshot / rollback / backup / ...
├── meta/runtime.yml           # requires_ansible >=2.15
├── requirements.yml           # community.general, ansible.posix, community.docker
├── .yamllint.yml
├── .github/workflows/lint.yml # yamllint + ansible-lint + syntax-check
├── playbooks/
│   ├── site.yml               # imports snapshot.yml + the rest
│   ├── bootstrap.yml          # create the `ansible` user (run once, --ask-pass)
│   ├── setup.yml              # baseline: full borg backup + clean-baseline snapshot
│   ├── snapshot.yml           # timeshift snapshot (pre-site or ad-hoc)
│   ├── rollback.yml           # timeshift restore (reboots host)
│   ├── backup.yml             # borg config + systemd timer
│   ├── backup_restore.yml     # borg extract → /var/restore/<archive>
│   ├── nvidia_verify.yml
│   ├── base.yml               # docker + tailscale
│   ├── remote_desktop.yml     # virtual_display + sunshine
│   ├── ai_serving.yml         # docker + vllm
│   ├── k3s.yml                # opt-in, gated by k3s_install
│   ├── monitoring.yml
│   └── tailscale.yml
├── inventory/
│   ├── hosts.yml              # main inventory (ansible_user=ansible after bootstrap)
│   ├── bootstrap.example.yml  # one-time bootstrap inventory (ansible_user=ubuntu)
│   ├── vault.example.yml      # template -> copy to group_vars/all/vault.yml
│   └── group_vars/
│       └── all/main.yml       # all knobs (incl. snapshot_*, borg_*)
├── docs/
│   ├── openai-client.example.py
│   └── prometheus-scrape.example.yml
└── roles/
    ├── bootstrap/             # creates the `ansible` user + key + NOPASSWD sudo
    ├── snapshot/              # timeshift snapshot (create + rollback tasks)
    ├── backup/                # borg daily backup; ssh/local/nfs/smb repo modes;
    │                          # /etc/borg/{passphrase,excludes}, /usr/local/sbin/borg-backup.sh,
    │                          # /etc/systemd/system/borg-backup.{service,timer}
    ├── nvidia_verify/         # nvidia-smi + driver version assert
    ├── docker/                # docker-ce + compose plugin + nvidia-container-toolkit;
    │                          # writes /etc/docker/daemon.json with nvidia default runtime;
    │                          # smoke-tests `docker run --gpus all nvidia/cuda`
    ├── tailscale/             # apt install + `tailscale up --authkey --ssh` (idempotent)
    ├── virtual_display/       # generates EDID via files/gen_edid.py; installs
    │                          # /etc/X11/xorg.conf.d/10-nvidia-headless.conf;
    │                          # enables lightdm
    ├── sunshine/              # downloads .deb from upstream releases;
    │                          # systemd USER unit (not system) so X session is visible;
    │                          # enables loginctl linger
    ├── vllm/                  # /opt/vllm with docker-compose.yml + .env (vault'd);
    │                          # runs vllm/vllm-openai with runtime: nvidia;
    │                          # health-checks /v1/models for up to 10 minutes
    ├── k3s_gpu/               # opt-in k3s install + optional NVIDIA k8s device plugin
    └── monitoring/            # node_exporter binary + systemd; dcgm-exporter container
```

## Operator flow

```
make bootstrap   # one-time, interactive (admin user + password)
make setup       # one-time: full borg backup + clean-baseline snapshot
make site        # repeatable; pre-flight snapshot taken each run
```

Recovery hierarchy:

- bad `make site` run → `make rollback` (latest pre-flight snapshot)
- cumulative drift → `make rollback ASK='-e snapshot_target=clean-baseline'`
- disk loss → reinstall OS, `make bootstrap`, restore from borg

The two safety nets are deliberately separate. **timeshift** is local
snapshot for in-place rollback; **borg** is off-host
deduplicated/encrypted incremental backup to ssh/local/nfs/smb repo
with a systemd `daily` timer. Lose the disk → borg restore. Break a
config → timeshift rollback.

## What has been verified

- `gen_edid.py` outputs a valid 128-byte EDID 1.3 (header OK, checksum OK,
  preferred timing for 4K60 produces correct CVT-RB 533.25 MHz pixel clock).
- `yamllint .` is clean.
- 5/8 playbooks pass `--syntax-check` locally. The 3 that import the `docker`
  or `vllm` roles can't be verified in the scaffold session because
  `community.docker` couldn't be fetched (galaxy was firewalled). CI runs
  full syntax-check + ansible-lint on every push.

## What has NOT been verified

- **Nothing has run against a real DGX host.** Expect to iterate on the
  first `make site`.
- Sunshine first-boot may need an interactive login as `sunshine_user`
  before the user systemd service starts cleanly (documented in role README).
- The EDID generator produces a structurally valid EDID but isn't
  bit-accurate to any real panel. If the NVIDIA driver rejects it, swap
  in a known-good EDID dump from a Dell U2718Q or similar 4K panel.
- For DGX A100/H100 datacenter cards with no display outputs, the
  virtual_display approach won't work — use Xvfb/VirtualGL instead.

## Configuration surface (most likely tweaks)

All knobs in `inventory/group_vars/all/main.yml`:

- `vllm_model`, `vllm_served_model_name`, `vllm_tensor_parallel_size`,
  `vllm_max_model_len`, `vllm_gpu_memory_utilization`
- `virtual_display_width/height/refresh`
- `sunshine_version`, `sunshine_user`
- `k3s_install` (opt-in), `k3s_gpu_operator_install`
- `monitoring_bind` (loopback by default; flip to Tailscale IP for remote scraping)
- `tailscale_ssh`
- `snapshot_enabled`, `snapshot_excludes`, `snapshot_retention`
- `borg_repo_mode` (ssh|local|nfs|smb), `borg_repo`,
  `borg_nfs_share` / `borg_smb_share`, `borg_schedule`,
  `borg_encryption`, `borg_compression`

Vault secrets in `inventory/group_vars/all/vault.yml` (gitignored, encrypt
with `ansible-vault`):

- `vault_tailscale_auth_key`
- `vault_hf_token` (for gated HF models like Llama)
- `vault_vllm_api_key`
- `vault_k3s_token` (only if `k3s_install: true`)
- `vault_borg_passphrase` (back this up off-host — lose it = lose the backups)
- `vault_borg_smb_password` (only if `borg_repo_mode: smb`)

## How to run it

```bash
git clone https://github.com/kmechlin/ansible-dgx-collection.git
cd ansible-dgx-collection
python3 -m venv venv && source venv/bin/activate
pip install ansible ansible-lint yamllint
make deps                              # installs community.general/posix/docker

# --- One-time bootstrap (interactive) ---
cp inventory/bootstrap.example.yml inventory/bootstrap.yml
vim inventory/bootstrap.yml            # admin user, host, key path
make bootstrap                         # prompts for admin SSH + sudo password

# --- Vault + baseline (one-time) ---
vim inventory/hosts.yml                # confirm ansible_host
cp inventory/vault.example.yml inventory/group_vars/all/vault.yml
ansible-vault encrypt inventory/group_vars/all/vault.yml
make ping                              # SSH + become smoke test as `ansible`
make setup                             # baseline snapshot + first full borg backup

# --- Provision (repeatable) ---
make site                              # snapshots pre-flight, then full provision
```

## Git / Workflow

- Develop on the session branch printed in the harness system prompt
  (the one starting with `claude/ansible-remote-ai-setup-`).
- Commit with clear, descriptive messages.
- Push with `git push -u origin <session-branch>`.
- Do **not** create a PR unless explicitly asked.

## Good next-iteration prompts

- "Add an `open_webui` role that runs Open WebUI on `:3000` pointed at the
  local vLLM, and add it to `ai_serving.yml`."
- "Add a `caddy` role that fronts vLLM + Open WebUI with HTTPS (Caddy
  local CA or Tailscale serve)."
- "Add a `make smoke` target that runs `nvidia-smi`, `docker run --gpus all`,
  a vLLM `/v1/chat/completions` call, and a Sunshine `:47990` reachability
  check against an already-provisioned host."
- "Write molecule tests for the `docker` and `nvidia_verify` roles."
- "Generalize the inventory to a `dgx` group; convert single-host
  references in templates."
- "Add a `restic` role as an alternative `backup_backend` to borg." 

## Notes / Blockers

- `claude.ai/code/session_…` URLs are NOT fetchable from this environment.
  Paste task specs as text.
- Repo MCP scope is restricted to `kmechlin/ansible-dgx-collection`.
- This collection is at `0.1.0`. Bump in `galaxy.yml` on each material
  change; tag releases as `v0.1.0`, `v0.2.0`, etc.
