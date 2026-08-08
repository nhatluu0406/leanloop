#!/usr/bin/env python3
"""SessionStart: point the new session at durable task state before exploration."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from _leanloop_state import active_task, state_dir


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        data = {}
    try:
        root = Path(data.get("cwd") or os.getcwd()).resolve()
        state = state_dir(root)
        candidates = [state / "HANDOFF.md", state / "CHECKPOINT.md", root / "PLAN.md", root / "STACK.md"]
        found = [p.relative_to(root).as_posix() for p in candidates if p.exists() and p.stat().st_size > 0]
        if not found:
            return 0
        task = active_task(root)
        cp_rel = (state / "CHECKPOINT.md").relative_to(root).as_posix()
        ctx = (
            f"LeanLoop durable state{' for task ' + task if task else ''}: {', '.join(found)}. "
            "Read it before asking the user to repeat context or exploring the repo. "
            f"If {cp_rel} exists, consume it, resume the described step, then delete only that checkpoint."
        )
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ctx}}))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
