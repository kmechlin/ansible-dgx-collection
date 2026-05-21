# CLAUDE.md

## Repository

- **Repo:** `kmechlin/zelos.dgx`
- **Collection FQCN:** `zelos.dgx`
- **Purpose:** Provision headless NVIDIA DGX-class workstations (Lenovo PGX,
  DGX Station, DGX Spark) running DGX OS, so the box is reachable remotely
  for (1) Sunshine/Moonlight remote desktop and (2) vLLM AI model serving.
  All access is over Tailscale.
- **State:** v0.1.0 scaffold. **Not yet validated against real hardware.**

## Layout

```
zelos.dgx/
├── ansible.cfg
├── galaxy.yml                 # namespace=zelos, name=dgx, version=0.2.0
├── pyproject.toml             # zdgx CLI package (host-installable + container ENTRYPOINT)
├── Dockerfile                 # python:3.12-slim + ansible + the zdgx CLI baked in
├── Makefile                   # make build / run-shell / dev-shell (container only)
├── cli/zdgx/                  # Typer CLI source (app.py, runner.py)
├── meta/runtime.yml           # requires_ansible >=2.15
├── requirements.yml           # community.general, ansible.posix, community.docker
├── .yamllint.yml
├── .github/workflows/         # lint.yml + release-tag.yml
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
│   ├── k3s.yml                # opt-in, gated by k3s_gpu_install
│   ├── monitoring.yml
│   └── tailscale.yml
├── inventory/
│   ├── hosts.yml              # main inventory (ansible_user=ansible after bootstrap)
│   ├── bootstrap.example.yml  # one-time bootstrap inventory (ansible_user=ubuntu)
│   ├── vault.example.yml      # template -> copy to group_vars/all/vault.yml
│   └── group_vars/
│       └── all/main.yml       # all knobs (incl. snapshot_*, backup_*)
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

All operator actions go through the `zdgx` CLI (a Typer app installed
into the container as ENTRYPOINT, also installable on the host via
`pip install -e .`). The Makefile is now just for the container image:
`make build`, `make run-shell`, `make dev-shell`.

```
zdgx bootstrap   # one-time, interactive (admin user + password)
zdgx setup       # one-time: full borg backup + clean-baseline snapshot
zdgx site        # repeatable; pre-flight snapshot taken each run
```

`zdgx --help` lists every subcommand. Common global options:
`-i/--inventory`, `--vault-password-file`, `--limit`, `--check`, `-v`,
`-e/--extra-vars`.

Recovery hierarchy:

- bad `zdgx site` run → `zdgx rollback` (latest pre-flight snapshot)
- cumulative drift → `zdgx rollback --target clean-baseline`
- disk loss → reinstall OS, `zdgx bootstrap`, restore with `zdgx backup-restore --archive <name>`

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
- `k3s_gpu_install` (opt-in), `k3s_gpu_operator_install`
- `monitoring_bind` (loopback by default; flip to Tailscale IP for remote scraping)
- `tailscale_ssh`
- `snapshot_enabled`, `snapshot_excludes`, `snapshot_retention`
- `backup_repo_mode` (ssh|local|nfs|smb), `backup_repo`,
  `backup_nfs_share` / `backup_smb_share`, `backup_schedule`,
  `backup_encryption`, `backup_compression`

Vault secrets in `inventory/group_vars/all/vault.yml` (gitignored, encrypt
with `ansible-vault`):

- `vault_tailscale_auth_key`
- `vault_hf_token` (for gated HF models like Llama)
- `vault_vllm_api_key`
- `vault_k3s_token` (only if `k3s_gpu_install: true`)
- `vault_borg_passphrase` (back this up off-host — lose it = lose the backups)
- `vault_borg_smb_password` (only if `backup_repo_mode: smb`)

## How to run it

There are three equivalent workflows: host-installed CLI, prod-like
container shell (`run-shell`), and live-edit container shell
(`dev-shell`). The container is the recommended path because it pins
Ansible + dependencies; the host install is convenient for ad-hoc work.

### Setup (one-time)

```bash
git clone https://github.com/kmechlin/zelos.dgx.git
cd zelos.dgx

# Inventory + vault (always required, however you run zdgx)
cp inventory/bootstrap.example.yml inventory/bootstrap.yml
vim inventory/bootstrap.yml            # admin user, host, key path
vim inventory/hosts.yml                # confirm ansible_host
cp inventory/vault.example.yml inventory/group_vars/all/vault.yml
ansible-vault encrypt inventory/group_vars/all/vault.yml
```

### Workflow A: host-installed CLI

```bash
python3 -m venv venv && source venv/bin/activate
pip install -e .                       # installs the zdgx CLI
pip install ansible ansible-lint yamllint
zdgx deps                              # community.general / posix / docker

zdgx bootstrap                         # prompts for admin SSH + sudo password
zdgx ping                              # smoke test as `ansible`
zdgx setup                             # baseline snapshot + first full borg backup
zdgx site                              # repeatable full provision
```

### Workflow B: container, prod-like (`make run-shell`)

```bash
make build
make run-shell                         # bash inside the container, RO inventory + vault
# inside the container:
zdgx site
```

`make run-shell` mounts your inventory + vault read-only at the
container paths Ansible expects. Override `INVENTORY_FILE` /
`SECRETS_FILE` / `SSH_DIR` on the make line to point elsewhere.

### Workflow C: container, live edits (`make dev-shell`)

```bash
make build                             # only when image deps change
make dev-shell
# inside the container:
zdgx --help                            # reflects any change you make on the host
zdgx setup --check                     # dry run
```

`dev-shell` bind-mounts the current repo over `/workspace` *and* over
the collection install path (`/usr/share/ansible/collections/...`), so
role/playbook/CLI edits on the host take effect immediately without a
rebuild.

### One-shot (no shell)

The container's ENTRYPOINT is `zdgx`:

```bash
docker run --rm \
  -v $PWD/inventory/hosts.yml:/workspace/inventory/hosts.yml:ro \
  -v $PWD/inventory/group_vars/all/vault.yml:/workspace/inventory/group_vars/all/vault.yml:ro \
  -v $HOME/.ssh:/home/ansible/.ssh:ro \
  zelos-dgx-ansible:latest setup --check
```

## Git / Workflow

### Branch model

- `main` is the protected release line. Every merge to `main` is a
  release and gets tagged `v<major>.<minor>.<patch>` automatically
  by `.github/workflows/release-tag.yml`, which reads the version
  from `galaxy.yml`. The version field in `galaxy.yml` is the
  source of truth — never tag manually.
- `develop` is the integration line. Features land here continuously.
- Feature branches are named `feature/<plan-name>` and are cut from
  the live tip of `origin/develop`. `<plan-name>` is the plan-file
  slug under `/home/kmechlin/.claude/plans/<slug>.md` when a plan
  exists, otherwise a kebab-case slug derived from the task. Never
  reuse a feature branch from a previous plan.

### Starting a plan

```
git fetch origin
git checkout -b feature/<plan-name> origin/develop
```

Never start work directly on `develop` or `main`.

### Completing a plan (feature → develop)

1. Commit with clear, descriptive messages.
2. Push: `git push -u origin feature/<plan-name>`.
3. Open a PR into `develop` with a meaningful title and a
   Summary + Test plan body. Do this without waiting to be asked —
   the PR is part of "plan complete."
4. Enable auto-merge with squash:
   `gh pr merge --auto --squash --delete-branch`.
   This waits for the required `lint` check (yamllint +
   ansible-lint + syntax-check) to pass green, then squash-merges
   and deletes the remote branch. The user does **not** need to
   review feature → develop PRs.
5. If CI fails, fix the issue on the same branch and let auto-merge
   retry. Do not force-merge.

### Cutting a release (develop → main)

Only when the user explicitly asks ("cut a release", "ship develop",
etc.). Never proactive.

1. Inspect what's landed: `git log v<last-tag>..origin/develop`
   (or `main..develop` if no tags yet).
2. Propose a semver bump from `galaxy.yml`'s current `version:`:
   - **patch** — bug fixes, doc updates, internal cleanup
   - **minor** — new roles, new playbooks, new configuration knobs
   - **major** — breaking changes to inventory variables, role
     interfaces, or operator-facing commands
3. Branch `release/v<X.Y.Z>` from `origin/develop`, bump
   `galaxy.yml`'s `version:`, PR into `develop`, and auto-merge it
   (same as any feature). This keeps develop and main in sync on
   versioning.
4. Then PR `develop` → `main`. Title: `Release v<X.Y.Z>`. Body:
   summary of changes since the last release. **Never auto-merge.**
   The user reviews and merges.
5. Use a *merge commit* (not squash) for develop → main so the
   release boundary is a single visible merge on main.
6. The `release-tag` workflow runs on the resulting push to `main`,
   creates the `v<X.Y.Z>` tag, and publishes a GitHub Release with
   auto-generated notes.

### Hard rules

- Never PR a feature branch directly into `main`.
- Never push directly to `develop` or `main`.
- Never auto-merge anything into `main`.
- If `develop` does not exist on the remote, create it from `main`
  before opening the first feature PR.

## Relation to the Zelos suite

`zelos.dgx` is the first of N planned `zelos.<hosttype>` Ansible collections
that bring bare-metal hosts into the [Zelos suite](https://github.com/ZelosAI/zelosai).
Each collection has two responsibilities: (1) **provision the host** (drivers,
container runtime, Tailscale, inference runtime, optional k3s, observability,
safety nets), and (2) **deliver a [`zelosclient`](https://github.com/ZelosAI/zelosclient)
container onto the host** wired to the local inference runtime and to the
suite's [`zelosbackplane`](https://github.com/ZelosAI/zelosbackplane) endpoint.
That container is **not a Kubernetes workload** — it runs as a plain
docker-compose or systemd unit, regardless of whether `k3s_install: true` is set.

Architecture context:
- [zelosai/docs/architecture/03-provisioning.md](https://github.com/ZelosAI/zelosai/blob/main/docs/architecture/03-provisioning.md) — the provisioning story.
- [zelosai/docs/architecture/04-components/zelos.dgx.md](https://github.com/ZelosAI/zelosai/blob/main/docs/architecture/04-components/zelos.dgx.md) — this collection's role in the suite.
- [zelosai/docs/architecture/00-overview.md](https://github.com/ZelosAI/zelosai/blob/main/docs/architecture/00-overview.md) — suite overview.

The collection currently lives at `kmechlin/ansible-dgx-collection`; migration
to `ZelosAI/zelos.dgx` is on the roadmap but out of scope for the first-pass
bootstrap.

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
- Repo MCP scope is restricted to `kmechlin/zelos.dgx`.
- This collection is at `0.1.0`. Bump in `galaxy.yml` on each material
  change; tag releases as `v0.1.0`, `v0.2.0`, etc.
