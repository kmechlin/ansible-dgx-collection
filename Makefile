# --- Container ---------------------------------------------------------
# All operator actions (bootstrap, setup, site, ...) now live in the zdgx
# CLI. The Makefile only manages the Docker image and shells into it.
#
# Override on the command line, e.g.
#   make run-shell INVENTORY_FILE=/path/to/hosts.yml SECRETS_FILE=...
DOCKER         ?= docker
DOCKER_IMAGE   ?= zelos-dgx-ansible
DOCKER_TAG     ?= latest
SSH_DIR        ?= $(HOME)/.ssh
INVENTORY_FILE ?= $(CURDIR)/inventory/hosts.yml
SECRETS_FILE   ?= $(CURDIR)/inventory/group_vars/all/vault.yml

# Path inside the container where the collection is installed so FQCN
# refs (zelos.dgx.docker, zelos.dgx.vllm, ...) resolve.
COLLECTION_PATH = /usr/share/ansible/collections/ansible_collections/zelos/dgx

.PHONY: help build run-shell dev-shell

help:
	@echo "Container targets:"
	@echo "  build         build $(DOCKER_IMAGE):$(DOCKER_TAG)"
	@echo "  run-shell     bash in the container with RO inventory + secrets mounted"
	@echo "                (prod-like; zdgx ENTRYPOINT is overridden)"
	@echo "  dev-shell     bash in the container with the CURRENT REPO bind-mounted"
	@echo "                over /workspace and the collection path, plus RW inventory"
	@echo "                + secrets. Live edits to roles/playbooks/cli take effect."
	@echo ""
	@echo "Overrides (both shells):"
	@echo "  DOCKER_IMAGE, DOCKER_TAG, INVENTORY_FILE, SECRETS_FILE, SSH_DIR"
	@echo ""
	@echo "Everything else lives in the CLI:"
	@echo "  zdgx --help                          (host: pip install -e . ; or via the shells)"
	@echo "  docker run --rm $(DOCKER_IMAGE):$(DOCKER_TAG) <command>"

build:
	$(DOCKER) build \
		--build-arg USER_UID=$$(id -u) \
		--build-arg USER_GID=$$(id -g) \
		-t $(DOCKER_IMAGE):$(DOCKER_TAG) .

run-shell:
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
		--entrypoint /bin/bash \
		$(DOCKER_IMAGE):$(DOCKER_TAG)

dev-shell:
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
		-v $(CURDIR):/workspace \
		-v $(CURDIR):$(COLLECTION_PATH) \
		-v $(INVENTORY_FILE):/workspace/inventory/hosts.yml \
		-v $(SECRETS_FILE):/workspace/inventory/group_vars/all/vault.yml \
		-v $(SSH_DIR):/home/ansible/.ssh:ro \
		-w /workspace \
		--entrypoint /bin/bash \
		$(DOCKER_IMAGE):$(DOCKER_TAG)
