#!/usr/bin/env python3
"""Stage an explicit allowlist and commit it -- never `git add .`.

This prevents one worker from accidentally committing another worker's files. It is
not a substitute for worktree isolation; use scripts/leanloop/worktree.py for parallel work.
"""
from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path

from leanloop_common import find_repo_root


def git(root: Path, *args: str, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=check)


def normalized_repo_path(root: Path, value: str) -> str:
    if value in {".", "*", "**"} or any(ch in value for ch in "*?["):
        raise ValueError(f"wildcards/broad staging are forbidden: {value}")
    p = (root / value).resolve() if not os.path.isabs(value) else Path(value).resolve()
    try:
        rel = p.relative_to(root).as_posix()
    except ValueError as exc:
        raise ValueError(f"path outside repo: {value}") from exc
    return rel


def main() -> int:
    ap = argparse.ArgumentParser(description="Commit only explicitly allowed paths")
    ap.add_argument("-m", "--message", required=True)
    ap.add_argument("files", nargs="+")
    args = ap.parse_args()
    root = find_repo_root(Path.cwd())
    if git(root, "rev-parse", "--is-inside-work-tree").returncode != 0:
        print("FAIL: not in a Git worktree")
        return 2
    try:
        allowed = sorted(set(normalized_repo_path(root, f) for f in args.files))
    except ValueError as exc:
        print(f"FAIL: {exc}")
        return 2

    already = [x for x in git(root, "diff", "--cached", "--name-only").stdout.splitlines() if x]
    extra = sorted(set(already) - set(allowed))
    if extra:
        print("FAIL: index already contains paths outside this commit allowlist:")
        for name in extra:
            print(f"  {name}")
        return 1

    add = git(root, "add", "--", *allowed)
    if add.returncode:
        print(add.stderr.strip() or "FAIL: git add failed")
        return add.returncode
    staged = [x for x in git(root, "diff", "--cached", "--name-only").stdout.splitlines() if x]
    unexpected = sorted(set(staged) - set(allowed))
    if unexpected:
        print("FAIL: refusing commit; unexpected staged paths:")
        for name in unexpected:
            print(f"  {name}")
        return 1
    if not staged:
        print("FAIL: nothing staged")
        return 1
    check = git(root, "diff", "--cached", "--check")
    if check.returncode:
        print(check.stdout + check.stderr)
        return check.returncode
    commit = git(root, "commit", "-m", args.message)
    if commit.returncode:
        print(commit.stdout + commit.stderr)
        return commit.returncode
    print(commit.stdout.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
