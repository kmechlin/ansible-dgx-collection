#!/usr/bin/env python3
"""Force-mirror this repo (all branches, tags, history) into another remote.

Usage:
    scripts/mirror_push.py <target-remote-url> [--source <path>] [--yes]

Examples:
    scripts/mirror_push.py git@github.com:other-org/ansible-dgx-collection.git
    scripts/mirror_push.py https://github.com/other-org/repo.git --yes

This uses `git push --mirror --force`, which makes the target a byte-for-byte
copy of the source: every local branch and tag is pushed, and any ref on the
target that does not exist locally is DELETED. Use with care.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import uuid
from pathlib import Path


def run(cmd: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    print(f"$ {' '.join(cmd)}", flush=True)
    return subprocess.run(cmd, cwd=cwd, check=check)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("target", help="Target remote URL (ssh or https)")
    parser.add_argument("--source", default=".", help="Path to the source repo (default: cwd)")
    parser.add_argument("--yes", action="store_true", help="Skip the interactive confirmation")
    args = parser.parse_args()

    source = Path(args.source).resolve()
    if not (source / ".git").exists():
        print(f"error: {source} is not a git repository", file=sys.stderr)
        return 1

    print(f"source: {source}")
    print(f"target: {args.target}")
    print()
    print("This will run `git push --mirror --force`, which OVERWRITES the target.")
    print("Any branches or tags on the target that do not exist locally will be DELETED.")
    if not args.yes:
        reply = input("Type 'yes' to continue: ").strip().lower()
        if reply != "yes":
            print("aborted.")
            return 1

    remote_name = f"mirror-{uuid.uuid4().hex[:8]}"
    try:
        run(["git", "remote", "add", remote_name, args.target], cwd=source)
        run(["git", "fetch", "--tags", "--prune", "origin"], cwd=source, check=False)
        run(["git", "push", "--mirror", "--force", remote_name], cwd=source)
    finally:
        run(["git", "remote", "remove", remote_name], cwd=source, check=False)

    print("done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
