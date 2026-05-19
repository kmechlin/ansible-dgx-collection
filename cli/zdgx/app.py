"""`zdgx` Typer CLI — operator entrypoint for the zelos.dgx collection."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer

from zdgx.runner import (
    RunnerState,
    run_ansible_module,
    run_galaxy_install,
    run_playbook,
)

app = typer.Typer(
    name="zdgx",
    help="Operator CLI for the zelos.dgx Ansible collection.",
    no_args_is_help=True,
    add_completion=True,
)

_state = RunnerState()


@app.callback()
def _root(
    ctx: typer.Context,
    inventory: Path = typer.Option(
        Path("inventory/hosts.yml"),
        "-i",
        "--inventory",
        help="Ansible inventory file.",
    ),
    vault_password_file: Optional[Path] = typer.Option(
        None,
        "--vault-password-file",
        help="Path to a file containing the vault password (non-interactive).",
    ),
    ask_vault_pass: bool = typer.Option(
        False,
        "--ask-vault-pass",
        help="Prompt for the vault password (default if no file is given).",
    ),
    limit: Optional[str] = typer.Option(
        None,
        "--limit",
        help="Limit execution to a host/group pattern.",
    ),
    check: bool = typer.Option(
        False,
        "--check",
        help="Dry run (ansible --check).",
    ),
    verbose: int = typer.Option(
        0,
        "-v",
        "--verbose",
        count=True,
        help="Increase ansible verbosity (-v / -vv / -vvv / -vvvv).",
    ),
    extra_var: list[str] = typer.Option(
        [],
        "-e",
        "--extra-vars",
        help='Extra vars passed to ansible-playbook (repeatable). e.g. -e "key=value".',
    ),
) -> None:
    """Shared options for every subcommand."""
    _state.inventory = inventory
    _state.vault_password_file = vault_password_file
    _state.ask_vault_pass = ask_vault_pass
    _state.limit = limit
    _state.check = check
    _state.verbose = verbose
    _state.extra_vars = list(extra_var)


# --- Workflow ---------------------------------------------------------------


@app.command(help="One-time bootstrap of the `ansible` user on a fresh DGX (interactive).")
def bootstrap(
    bootstrap_inventory: Path = typer.Option(
        Path("inventory/bootstrap.yml"),
        "--bootstrap-inventory",
        help="Bootstrap inventory file (defaults to inventory/bootstrap.yml).",
    ),
) -> None:
    run_playbook(
        _state,
        "bootstrap.yml",
        inventory=bootstrap_inventory,
        ask_pass=True,
        ask_become_pass=True,
        skip_vault=True,
    )


@app.command(help="Baseline: clean-baseline timeshift snapshot + first full borg backup.")
def setup() -> None:
    run_playbook(_state, "setup.yml")


@app.command(help="Full repeatable provision (snapshot + all roles).")
def site() -> None:
    run_playbook(_state, "site.yml")


# --- Safety net -------------------------------------------------------------


@app.command(help="Take an ad-hoc timeshift snapshot.")
def snapshot() -> None:
    run_playbook(_state, "snapshot.yml")


@app.command(help="Roll back to a timeshift snapshot (default: latest).")
def rollback(
    target: Optional[str] = typer.Option(
        None,
        "-t",
        "--target",
        help="Snapshot name to restore (default: latest).",
    ),
) -> None:
    extra = [f"-e", f"snapshot_target={target}"] if target else []
    run_playbook(_state, "rollback.yml", extra=extra)


@app.command(help="Refresh borg backup config + systemd timer. Use --now to also run a backup immediately.")
def backup(
    now: bool = typer.Option(False, "--now", help="Run a backup immediately after configuring."),
) -> None:
    extra = ["-e", "backup_run_now=true"] if now else []
    run_playbook(_state, "backup.yml", extra=extra)


@app.command("backup-restore", help="Extract a borg archive into /var/restore/<archive> on the host.")
def backup_restore(
    archive: str = typer.Option(..., "-a", "--archive", help="Borg archive name to restore."),
) -> None:
    run_playbook(_state, "backup_restore.yml", extra=["-e", f"backup_archive={archive}"])


# --- Individual provisioning roles -----------------------------------------


@app.command(help="Verify NVIDIA driver only.")
def nvidia() -> None:
    run_playbook(_state, "nvidia_verify.yml")


@app.command(help="Docker + Tailscale base layer.")
def base() -> None:
    run_playbook(_state, "base.yml")


@app.command("remote-desktop", help="Virtual display + Sunshine remote desktop.")
def remote_desktop() -> None:
    run_playbook(_state, "remote_desktop.yml")


@app.command(help="Docker + vLLM AI serving.")
def ai() -> None:
    run_playbook(_state, "ai_serving.yml")


@app.command(help="K3s with NVIDIA runtime (opt-in via k3s_gpu_install).")
def k3s() -> None:
    run_playbook(_state, "k3s.yml")


@app.command(help="node_exporter + DCGM exporter monitoring stack.")
def monitoring() -> None:
    run_playbook(_state, "monitoring.yml")


@app.command(help="Tailscale only.")
def tailscale() -> None:
    run_playbook(_state, "tailscale.yml")


# --- Hygiene ---------------------------------------------------------------


@app.command(help="ansible -m ping against every host in inventory.")
def ping() -> None:
    run_ansible_module(_state, "ping", pattern="all", become=True)


@app.command(help="Install required Ansible collections from requirements.yml.")
def deps(
    requirements: Path = typer.Option(
        Path("requirements.yml"),
        "--requirements",
        help="Path to the requirements.yml.",
    ),
) -> None:
    run_galaxy_install(requirements)


@app.command(help="Run yamllint and ansible-lint over the collection.")
def lint() -> None:
    yl = subprocess.run(["yamllint", "."])
    al = subprocess.run(["ansible-lint"])
    sys.exit(yl.returncode or al.returncode)


@app.command(help="ansible-playbook --syntax-check every playbook in playbooks/.")
def syntax() -> None:
    playbooks_dir = Path("playbooks")
    rc = 0
    for pb in sorted(playbooks_dir.glob("*.yml")):
        print(f"syntax: {pb}", flush=True)
        result = subprocess.run(
            ["ansible-playbook", "-i", str(_state.inventory), str(pb), "--syntax-check"]
        )
        if result.returncode != 0:
            rc = result.returncode
            break
    sys.exit(rc)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
