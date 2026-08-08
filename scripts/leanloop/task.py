#!/usr/bin/env python3
"""Select a task-scoped durable state directory.

The active task is stored in state/CURRENT_TASK (local-only). Durable files live
under state/tasks/<slug>/ so checkpoints/reports from unrelated tasks never collide.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from leanloop_common import active_task, find_repo_root, validate_slug


def main() -> int:
    ap = argparse.ArgumentParser(description="Manage LeanLoop task-scoped state")
    sub = ap.add_subparsers(dest="cmd", required=True)
    start = sub.add_parser("start")
    start.add_argument("slug")
    sub.add_parser("current")
    sub.add_parser("path")
    sub.add_parser("end")
    args = ap.parse_args()

    root = find_repo_root(Path.cwd())
    state = root / "state"
    marker = state / "CURRENT_TASK"
    state.mkdir(parents=True, exist_ok=True)

    if args.cmd == "start":
        slug = validate_slug(args.slug)
        task_dir = state / "tasks" / slug
        (task_dir / "reports").mkdir(parents=True, exist_ok=True)
        marker.write_text(slug + "\n", encoding="utf-8")
        print(task_dir.relative_to(root).as_posix())
        return 0
    if args.cmd == "end":
        slug = active_task(root)
        marker.unlink(missing_ok=True)
        print(f"ended {slug}" if slug else "no active task")
        return 0

    slug = active_task(root)
    if args.cmd == "current":
        print(slug or "")
    else:
        print((Path("state/tasks") / slug).as_posix() if slug else "state")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
