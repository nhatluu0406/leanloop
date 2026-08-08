#!/usr/bin/env python3
"""Cheap Git preflight for agent work.

Default policy is intentionally strict: implementation starts from a clean worktree
and empty index. If the user's main tree is dirty, create an isolated LeanLoop
worktree instead of mixing agent changes with existing work.
"""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from leanloop_common import find_repo_root


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="Check Git safety before agent implementation")
    ap.add_argument("--allow-dirty", action="store_true", help="diagnostic only; does not make commits safe")
    args = ap.parse_args()
    root = find_repo_root(Path.cwd())
    if git(root, "rev-parse", "--is-inside-work-tree").returncode != 0:
        print("FAIL: not inside a Git worktree")
        return 2

    status = git(root, "status", "--porcelain=v1", "--untracked-files=all")
    staged = git(root, "diff", "--cached", "--name-only")
    if status.returncode or staged.returncode:
        print("FAIL: git status failed")
        return 2
    dirty = [line for line in status.stdout.splitlines() if line.strip()]
    staged_files = [line for line in staged.stdout.splitlines() if line.strip()]
    if (dirty or staged_files) and not args.allow_dirty:
        print("FAIL: worktree is not clean. Do not mix agent work with existing changes.")
        for line in dirty[:20]:
            print(f"  {line}")
        if len(dirty) > 20:
            print(f"  … +{len(dirty)-20} more")
        print("Use scripts/leanloop/worktree.py create <task-slug> to get an isolated clean worktree.")
        return 1
    print("OK: Git worktree/index clean" if not dirty else "WARN: dirty tree explicitly allowed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
