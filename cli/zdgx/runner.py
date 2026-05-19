"""Thin wrappers around ansible-playbook / ansible / ansible-galaxy.

The CLI is a shell over Ansible: it builds argv and execs the upstream tool
so signals, TTY, and exit codes are passed through unchanged.
"""

from __future__ import annotations

import os
import shlex
import sys
from pathlib import Path
from typing import Iterable, Sequence


class RunnerState:
    """Holds global CLI options resolved by the Typer root callback."""

    def __init__(self) -> None:
        self.inventory: Path = Path("inventory/hosts.yml")
        self.vault_password_file: Path | None = None
        self.ask_vault_pass: bool = False
        self.limit: str | None = None
        self.check: bool = False
        self.verbose: int = 0
        self.extra_vars: list[str] = []


def _vault_args(state: RunnerState) -> list[str]:
    if state.vault_password_file is not None:
        return ["--vault-password-file", str(state.vault_password_file)]
    if os.environ.get("ANSIBLE_VAULT_PASSWORD_FILE"):
        return []
    if state.ask_vault_pass:
        return ["--ask-vault-pass"]
    return ["--ask-vault-pass"]


def _common_args(state: RunnerState) -> list[str]:
    args: list[str] = []
    args += _vault_args(state)
    if state.limit:
        args += ["--limit", state.limit]
    if state.check:
        args.append("--check")
    if state.verbose:
        args.append("-" + "v" * state.verbose)
    for ev in state.extra_vars:
        args += ["-e", ev]
    return args


def _exec(argv: Sequence[str]) -> None:
    """Replace this process with `argv`. Mirrors what shell-exec does."""
    rendered = " ".join(shlex.quote(a) for a in argv)
    print(f"$ {rendered}", file=sys.stderr, flush=True)
    os.execvp(argv[0], list(argv))


def run_playbook(
    state: RunnerState,
    playbook: str,
    *,
    inventory: Path | None = None,
    extra: Iterable[str] = (),
    ask_pass: bool = False,
    ask_become_pass: bool = False,
    skip_vault: bool = False,
) -> None:
    """Exec `ansible-playbook` for one of the bundled playbooks."""
    inv = inventory if inventory is not None else state.inventory
    argv: list[str] = ["ansible-playbook", "-i", str(inv), f"playbooks/{playbook}"]
    if ask_pass:
        argv.append("--ask-pass")
    if ask_become_pass:
        argv.append("--ask-become-pass")
    if not skip_vault:
        argv += _common_args(state)
    else:
        if state.limit:
            argv += ["--limit", state.limit]
        if state.check:
            argv.append("--check")
        if state.verbose:
            argv.append("-" + "v" * state.verbose)
    argv += list(extra)
    _exec(argv)


def run_ansible_module(state: RunnerState, module: str, *, pattern: str = "all", become: bool = True) -> None:
    argv = ["ansible", "-i", str(state.inventory), pattern, "-m", module]
    if become:
        argv.append("-b")
    if state.limit:
        argv += ["--limit", state.limit]
    if state.verbose:
        argv.append("-" + "v" * state.verbose)
    _exec(argv)


def run_galaxy_install(requirements: Path) -> None:
    _exec(["ansible-galaxy", "collection", "install", "-r", str(requirements)])
