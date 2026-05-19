ANSIBLE   = ansible-playbook
INV       = inventory/hosts.yml
ASK       = --ask-vault-pass

.PHONY: help deps lint syntax ping site nvidia base remote-desktop ai k3s monitoring tailscale

help:
	@echo "Targets:"
	@echo "  deps             install required collections"
	@echo "  lint             yamllint + ansible-lint"
	@echo "  syntax           ansible-playbook --syntax-check on every playbook"
	@echo "  ping             ansible -m ping all hosts"
	@echo "  site             full provision (all playbooks)"
	@echo "  nvidia           verify NVIDIA driver only"
	@echo "  base             docker + tailscale"
	@echo "  remote-desktop   virtual_display + sunshine"
	@echo "  ai               docker + vllm"
	@echo "  k3s              install k3s with NVIDIA runtime (opt-in via k3s_install)"
	@echo "  monitoring       node_exporter + DCGM exporter"
	@echo "  tailscale        tailscale only"

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

site:
	$(ANSIBLE) -i $(INV) playbooks/site.yml $(ASK)

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
