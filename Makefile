ANSIBLE   = ansible-playbook
INV       = inventory/hosts.yml
BOOT_INV  = inventory/bootstrap.yml
ASK       = --ask-vault-pass

# --- Container ---------------------------------------------------------
# Override on the command line, e.g.
#   make docker-shell INVENTORY_FILE=/path/to/hosts.yml SECRETS_FILE=...
DOCKER         ?= docker
DOCKER_IMAGE   ?= zelos-dgx-ansible
DOCKER_TAG     ?= latest
SSH_DIR        ?= $(HOME)/.ssh
INVENTORY_FILE ?= $(CURDIR)/inventory/hosts.yml
SECRETS_FILE   ?= $(CURDIR)/inventory/group_vars/all/vault.yml

.PHONY: help deps lint syntax ping \
        bootstrap setup site \
        snapshot rollback backup backup-now backup-restore \
        nvidia base remote-desktop ai k3s monitoring tailscale \
        docker-build docker-shell

help:
	@echo "Operator flow on a fresh DGX:"
	@echo "  1. make bootstrap     one-time, interactive (admin user + password)"
	@echo "  2. make setup         one-time, captures clean-baseline snapshot + full borg backup"
	@echo "  3. make site          repeatable, pre-flight snapshot taken each run"
	@echo ""
	@echo "Safety net targets:"
	@echo "  snapshot              take an ad-hoc timeshift snapshot"
	@echo "  rollback              restore latest snapshot (-e snapshot_target=<name> for explicit)"
	@echo "  backup                refresh borg config + systemd timer (no immediate backup)"
	@echo "  backup-now            same as backup, but trigger an immediate run too"
	@echo "  backup-restore        extract a borg archive to /var/restore (pass ARCHIVE=<name>)"
	@echo ""
	@echo "Provisioning targets:"
	@echo "  nvidia                verify NVIDIA driver only"
	@echo "  base                  docker + tailscale"
	@echo "  remote-desktop        virtual_display + sunshine"
	@echo "  ai                    docker + vllm"
	@echo "  monitoring            node_exporter + DCGM exporter"
	@echo "  k3s                   install k3s with NVIDIA runtime (opt-in)"
	@echo "  tailscale             tailscale only"
	@echo ""
	@echo "Repo hygiene:"
	@echo "  deps                  install required collections"
	@echo "  lint                  yamllint + ansible-lint"
	@echo "  syntax                ansible-playbook --syntax-check on every playbook"
	@echo "  ping                  ansible -m ping all hosts"
	@echo ""
	@echo "Container (local dev mirrors the eventual K8s topology):"
	@echo "  docker-build          build $(DOCKER_IMAGE):$(DOCKER_TAG)"
	@echo "  docker-shell          bash in the container with inventory + secrets mounted"
	@echo "                        Overrides: DOCKER_IMAGE, DOCKER_TAG,"
	@echo "                                   INVENTORY_FILE, SECRETS_FILE, SSH_DIR"

deps:
	ansible-galaxy collection install -r requirements.yml

lint:
	yamllint .
	ansible-lint

syntax:
	@for pb in playbooks/*.yml; do \
		echo "syntax: $$pb"; \
		$(ANSIBLE) -i $(INV) $$pb --syntax-check || exit 1; \
	done

ping:
	ansible -i $(INV) all -m ping -b

bootstrap:
	$(ANSIBLE) -i $(BOOT_INV) playbooks/bootstrap.yml --ask-pass --ask-become-pass

setup:
	$(ANSIBLE) -i $(INV) playbooks/setup.yml $(ASK)

site:
	$(ANSIBLE) -i $(INV) playbooks/site.yml $(ASK)

snapshot:
	$(ANSIBLE) -i $(INV) playbooks/snapshot.yml $(ASK)

rollback:
	$(ANSIBLE) -i $(INV) playbooks/rollback.yml $(ASK)

backup:
	$(ANSIBLE) -i $(INV) playbooks/backup.yml $(ASK)

backup-now:
	$(ANSIBLE) -i $(INV) playbooks/backup.yml $(ASK) -e borg_run_now=true

backup-restore:
	$(ANSIBLE) -i $(INV) playbooks/backup_restore.yml $(ASK) -e borg_archive=$(ARCHIVE)

nvidia:
	$(ANSIBLE) -i $(INV) playbooks/nvidia_verify.yml $(ASK)

base:
	$(ANSIBLE) -i $(INV) playbooks/base.yml $(ASK)

remote-desktop:
	$(ANSIBLE) -i $(INV) playbooks/remote_desktop.yml $(ASK)

ai:
	$(ANSIBLE) -i $(INV) playbooks/ai_serving.yml $(ASK)

k3s:
	$(ANSIBLE) -i $(INV) playbooks/k3s.yml $(ASK)

monitoring:
	$(ANSIBLE) -i $(INV) playbooks/monitoring.yml $(ASK)

tailscale:
	$(ANSIBLE) -i $(INV) playbooks/tailscale.yml $(ASK)

# --- Container ---------------------------------------------------------

docker-build:
	$(DOCKER) build \
		--build-arg USER_UID=$$(id -u) \
		--build-arg USER_GID=$$(id -g) \
		-t $(DOCKER_IMAGE):$(DOCKER_TAG) .

docker-shell:
	@test -f "$(INVENTORY_FILE)" || { \
		echo "missing inventory: $(INVENTORY_FILE)"; \
		echo "  copy inventory/hosts.yml and edit, or pass INVENTORY_FILE=..."; \
		exit 1; }
	@test -f "$(SECRETS_FILE)" || { \
		echo "missing secrets file: $(SECRETS_FILE)"; \
		echo "  copy inventory/vault.example.yml to $(SECRETS_FILE),"; \
		echo "  encrypt it with ansible-vault, or pass SECRETS_FILE=..."; \
		exit 1; }
	$(DOCKER) run --rm -it \
		-v $(INVENTORY_FILE):/workspace/inventory/hosts.yml:ro \
		-v $(SECRETS_FILE):/workspace/inventory/group_vars/all/vault.yml:ro \
		-v $(SSH_DIR):/home/ansible/.ssh:ro \
		-w /workspace \
		$(DOCKER_IMAGE):$(DOCKER_TAG) /bin/bash
