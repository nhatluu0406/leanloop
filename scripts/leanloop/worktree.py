#!/usr/bin/env python3
"""Create isolated Git worktrees for parallel LeanLoop implementers.

Each worker gets its own working tree, index, branch, task-state marker, and commits.
The orchestrator integrates reviewed commits (normally by cherry-pick) into the main
branch; workers never share a Git index.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from leanloop_common import find_repo_root, validate_slug


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True)


def default_parent(root: Path) -> Path:
    return root.parent / f".{root.name}-leanloop-worktrees"


def list_rows(root: Path) -> list[dict[str, str]]:
    cp = git(root, "worktree", "list", "--porcelain")
    rows: list[dict[str, str]] = []
    row: dict[str, str] = {}
    for line in cp.stdout.splitlines() + [""]:
        if not line:
            if row:
                rows.append(row)
                row = {}
            continue
        key, _, value = line.partition(" ")
        row[key] = value
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="Manage isolated LeanLoop worker worktrees")
    sub = ap.add_subparsers(dest="cmd", required=True)
    create = sub.add_parser("create")
    create.add_argument("slug")
    create.add_argument("--base", default="HEAD")
    create.add_argument("--parent", default=None)
    status = sub.add_parser("status")
    status.add_argument("slug")
    remove = sub.add_parser("remove")
    remove.add_argument("slug")
    remove.add_argument("--force", action="store_true")
    sub.add_parser("list")
    args = ap.parse_args()

    root = find_repo_root(Path.cwd())
    if git(root, "rev-parse", "--is-inside-work-tree").returncode != 0:
        print("FAIL: not inside a Git repository")
        return 2

    if args.cmd == "list":
        for row in list_rows(root):
            print(f"{row.get('worktree','')}\t{row.get('branch','detached')}\t{row.get('HEAD','')[:12]}")
        return 0

    slug = validate_slug(args.slug)
    parent = Path(getattr(args, "parent", None) or default_parent(root)).resolve()
    path = parent / slug
    branch = f"leanloop/{slug}"

    if args.cmd == "create":
        parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            print(f"FAIL: path exists: {path}")
            return 1
        if git(root, "show-ref", "--verify", "--quiet", f"refs/heads/{branch}").returncode == 0:
            print(f"FAIL: branch exists: {branch}")
            return 1
        cp = git(root, "worktree", "add", "-b", branch, str(path), args.base)
        if cp.returncode:
            print(cp.stdout + cp.stderr)
            return cp.returncode
        task = subprocess.run(
            [sys.executable, "scripts/leanloop/task.py", "start", slug], cwd=path, text=True,
            capture_output=True,
        )
        if task.returncode:
            print(f"WARN: worktree created but task-state init failed: {task.stderr.strip()}")
        print(f"WORKTREE={path}")
        print(f"BRANCH={branch}")
        print("Integration rule: review the worker commit, then cherry-pick it from the orchestrator tree.")
        return 0

    if not path.exists():
        # Find by branch in case a custom --parent was used at creation time.
        branch_ref = f"refs/heads/{branch}"
        matches = [r for r in list_rows(root) if r.get("branch") == branch_ref]
        if matches:
            path = Path(matches[0]["worktree"])
        else:
            print(f"FAIL: no worktree found for {branch}")
            return 1

    if args.cmd == "status":
        status_cp = git(path, "status", "--short", "--branch")
        print(status_cp.stdout.rstrip())
        head = git(path, "rev-parse", "HEAD")
        if head.returncode == 0:
            print(f"HEAD={head.stdout.strip()}")
        return status_cp.returncode

    dirty = git(path, "status", "--porcelain=v1", "--untracked-files=all")
    if dirty.stdout.strip() and not args.force:
        print("FAIL: worker worktree is dirty; commit/recover first or pass --force deliberately")
        print(dirty.stdout.rstrip())
        return 1
    rm_args = ["worktree", "remove"]
    if args.force:
        rm_args.append("--force")
    rm_args.append(str(path))
    cp = git(root, *rm_args)
    if cp.returncode:
        print(cp.stdout + cp.stderr)
        return cp.returncode
    print(f"removed {path}; branch {branch} retained for audit until deleted explicitly")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
