#!/usr/bin/env python3
"""Statusline: model | active task | context fill | cost. Degrades gracefully."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from _leanloop_state import active_task


def main() -> int:
    try:
        d = json.load(sys.stdin)
    except Exception:
        print("LeanLoop")
        return 0
    model = (d.get("model") or {}).get("display_name") or "?"
    parts = [model]
    task = active_task(Path(d.get("cwd") or os.getcwd()).resolve())
    if task:
        parts.append(f"task {task}")
    cw = d.get("context_window") or d.get("context") or {}
    used = cw.get("used_tokens")
    size = cw.get("context_window_size") or cw.get("size")
    if used and size:
        pct = round(100 * used / size)
        marker = "!" if pct >= 85 else ("~" if pct >= 70 else "")
        parts.append(f"ctx {pct}%{marker}")
    cost = (d.get("cost") or {}).get("total_cost_usd")
    if cost is not None:
        parts.append(f"${cost:.2f}")
    print(" | ".join(parts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
