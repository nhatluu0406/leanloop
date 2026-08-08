#!/usr/bin/env python3
"""Shared state-path helpers for Claude hooks. Stdlib only."""
from __future__ import annotations

import os
import re
from pathlib import Path

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")


def active_task(root: Path) -> str | None:
    value = os.environ.get("LEANLOOP_TASK", "").strip().lower()
    if not value:
        try:
            value = (root / "state" / "CURRENT_TASK").read_text(encoding="utf-8").strip().lower()
        except OSError:
            return None
    return value if SLUG_RE.fullmatch(value) else None


def state_dir(root: Path) -> Path:
    task = active_task(root)
    return root / "state" / "tasks" / task if task else root / "state"
