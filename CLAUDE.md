# CLAUDE.md

## Repository

- **Repo:** `kmechlin/ansible-dgx-collection`
- **Purpose:** Ansible collection for remote AI / NVIDIA DGX server setup (scope not yet defined).
- **State:** Empty repository — no commits, no files, no scaffolding yet.

## Active Branch

- Work on: `claude/ansible-remote-ai-setup-aLg4U`
- (An earlier branch `claude/ansible-remote-ai-setup-cJZGj` was also created but never used.)

## What Has Been Done

Nothing substantive. Previous session only:
1. Verified the repo is empty.
2. Created and checked out the working branch.

No files written, no commits, nothing pushed.

## What Needs to Be Decided

Before scaffolding, confirm with the user:

- **Target OS:** Ubuntu (which version?), RHEL/Rocky, or both?
- **Scope of the collection:** which of these should it cover?
  - NVIDIA driver install
  - CUDA toolkit
  - NVIDIA Container Toolkit / Docker / containerd
  - DCGM (Data Center GPU Manager)
  - Fabric Manager (for NVSwitch / DGX systems)
  - MIG configuration
  - Networking (InfiniBand, RoCE, MOFED)
  - Storage (NFS, Lustre, GPFS)
  - Slurm / Kubernetes / Run.ai integration
  - User / SSH / security hardening
  - Monitoring (Prometheus node-exporter, DCGM-exporter)
- **Hardware targets:** DGX A100, DGX H100, DGX B200, generic GPU nodes?
- **Deployment model:** standalone playbooks, roles only, or full Ansible collection (galaxy.yml + plugins + roles + playbooks)?

## Standard Ansible Collection Layout (for reference)

```
ansible-dgx-collection/
├── galaxy.yml
├── README.md
├── LICENSE
├── meta/
│   └── runtime.yml
├── plugins/
│   ├── modules/
│   ├── module_utils/
│   ├── inventory/
│   └── filter/
├── roles/
│   └── <role_name>/
│       ├── defaults/main.yml
│       ├── tasks/main.yml
│       ├── handlers/main.yml
│       ├── meta/main.yml
│       └── README.md
├── playbooks/
├── tests/
│   ├── integration/
│   └── unit/
└── docs/
```

## Git / Workflow Conventions

- Develop on `claude/ansible-remote-ai-setup-aLg4U`.
- Commit with clear, descriptive messages.
- Push with `git push -u origin claude/ansible-remote-ai-setup-aLg4U`.
- Do **not** create a PR unless explicitly asked.

## Notes / Blockers from Prior Session

- User shared two `claude.ai/code/session_…` URLs — those are not fetchable from the Claude Code environment. Paste task specs as text, not as session links.
- Repo MCP scope is restricted to `kmechlin/ansible-dgx-collection` only.
