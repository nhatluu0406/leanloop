#!/usr/bin/env python3
"""PreToolUse hook on Read: nudge-block un-ranged reads of big files.
Enforces read-budget mechanically: grep first, then ranged read.
Fails open on any error."""
import json, sys, os

LIMIT_LINES = 500
ALWAYS_ALLOW_BASENAMES = {"PLAN.md", "STACK.md", "HANDOFF.md", "CHECKPOINT.md",
                          "REPOMAP.md", "SCHEMAMAP.md", "BRIEF.md", "SKILL.md"}

def main():
    try:
        data = json.load(sys.stdin)
        tool = data.get("tool_name", "")
        if tool != "Read":
            sys.exit(0)
        ti = data.get("tool_input", {}) or {}
        path = ti.get("file_path") or ""
        # Ranged read or special file: allow
        if ti.get("offset") is not None or ti.get("limit") is not None:
            sys.exit(0)
        if os.path.basename(path) in ALWAYS_ALLOW_BASENAMES:
            sys.exit(0)
        if not path or not os.path.isfile(path):
            sys.exit(0)
        with open(path, "rb") as f:
            n = sum(1 for _ in f)
        if n <= LIMIT_LINES:
            sys.exit(0)
        reason = (f"read-budget: {os.path.basename(path)} has {n} lines. "
                  f"Grep for the symbol first, then Read with offset/limit around it. "
                  f"(Ranged reads pass this guard.)")
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason}}))
        sys.exit(0)
    except Exception:
        sys.exit(0)  # fail open

if __name__ == "__main__":
    main()
