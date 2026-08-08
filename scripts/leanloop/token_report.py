#!/usr/bin/env python3
"""Cross-platform wrapper for pinned ccusage reporting."""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from leanloop_common import find_repo_root


def load_version(root: Path) -> str:
    candidates = [root / "TOOLS.lock", root / ".leanloop/kit/TOOLS.lock"]
    for path in candidates:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("CCUSAGE_VERSION="):
                return line.split("=", 1)[1].strip()
    raise SystemExit("CCUSAGE_VERSION not found in TOOLS.lock")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", nargs="?", default="daily", choices=["daily", "weekly", "monthly", "session"])
    ap.add_argument("source", nargs="?", default="all", choices=["all", "claude", "codex"])
    args = ap.parse_args()
    root = find_repo_root(Path.cwd())
    version = load_version(root)
    cmd = ["npx", "-y", f"ccusage@{version}"]
    cmd += [args.mode] if args.source == "all" else [args.source, args.mode]
    print(f"== ccusage {version}: {args.source}/{args.mode} ==")
    try:
        return subprocess.run(cmd, cwd=root).returncode
    except FileNotFoundError:
        print("npx not found; install Node.js first")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
