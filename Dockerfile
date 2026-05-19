FROM python:3.12-slim

ARG ANSIBLE_VERSION=9.5.1
ARG ANSIBLE_LINT_VERSION=24.2.1
ARG YAMLLINT_VERSION=1.35.1

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    ANSIBLE_HOST_KEY_CHECKING=True \
    ANSIBLE_FORCE_COLOR=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        openssh-client \
        sshpass \
        git \
        make \
        curl \
        ca-certificates \
        gnupg \
        rsync \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
        "ansible==${ANSIBLE_VERSION}" \
        "ansible-lint==${ANSIBLE_LINT_VERSION}" \
        "yamllint==${YAMLLINT_VERSION}" \
        "typer>=0.12" \
        jmespath \
        netaddr \
        passlib

COPY requirements.yml /tmp/requirements.yml
RUN ansible-galaxy collection install -r /tmp/requirements.yml \
        -p /usr/share/ansible/collections \
    && rm /tmp/requirements.yml

ENV ANSIBLE_COLLECTIONS_PATH=/usr/share/ansible/collections

ARG USER_UID=1000
ARG USER_GID=1000
RUN groupadd --gid "${USER_GID}" ansible \
    && useradd --uid "${USER_UID}" --gid "${USER_GID}" \
        --create-home --shell /bin/bash ansible \
    && mkdir -p /home/ansible/.ssh \
    && chown -R ansible:ansible /home/ansible

# /workspace is the runtime root. The inventory/ subtree is pre-created
# so that Kubernetes ConfigMap (inventory/hosts.yml) and Secret
# (inventory/group_vars/all/vault.yml) subPath mounts land at the right
# paths. Locally, `make docker-shell` bind-mounts the same two files
# into the same locations.
RUN mkdir -p /workspace/inventory/group_vars/all \
    && chown -R ansible:ansible /workspace

COPY --chown=ansible:ansible ansible.cfg galaxy.yml requirements.yml Makefile pyproject.toml /workspace/
COPY --chown=ansible:ansible playbooks /workspace/playbooks
COPY --chown=ansible:ansible roles     /workspace/roles
COPY --chown=ansible:ansible meta      /workspace/meta
COPY --chown=ansible:ansible cli       /workspace/cli

# Editable install so `make dev-shell`'s bind mount of $PWD over /workspace
# picks up live CLI edits without a rebuild.
RUN pip install --no-cache-dir -e /workspace

USER ansible
WORKDIR /workspace

ENTRYPOINT ["zdgx"]
CMD ["--help"]
