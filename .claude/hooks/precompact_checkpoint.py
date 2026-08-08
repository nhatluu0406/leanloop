#!/usr/bin/env python3
"""PreCompact: persist a task-scoped checkpoint and inject keep/drop guidance.
Fails open; never blocks compaction.
"""
from __future__ import annotations

import datetime
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
        state.mkdir(parents=True, exist_ok=True)
        cp = state / "CHECKPOINT.md"
        stamp = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
        trigger = data.get("trigger", "unknown")
        task = active_task(root)
        stub = (
            f"# CHECKPOINT ({trigger} compact @ {stamp})\n\n"
            f"- Task: {task or 'default'}\n"
            "- PLAN step: \n- Decisions: \n- Open problem: \n"
            "- Files in flight: \n- Do NOT redo: \n"
        )
        if not cp.exists() or cp.stat().st_size < 60:
            cp.write_text(stub, encoding="utf-8")
        rel = cp.relative_to(root).as_posix()
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreCompact",
            "customInstructions": (
                "KEEP: architectural decisions, exact paths in flight, unresolved errors, "
                "PLAN step status, contract changes. DROP: file contents already applied, old "
                f"tool output, resolved discussion. Durable checkpoint: {rel}."
            ),
        }}))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
