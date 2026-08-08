#!/usr/bin/env python3
"""Small shared helpers for LeanLoop scripts. Stdlib only."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")


def find_repo_root(start: str | os.PathLike[str] | None = None) -> Path:
    p = Path(start or os.getcwd()).resolve()
    if p.is_file():
        p = p.parent
    for candidate in (p, *p.parents):
        if (candidate / ".agents" / "skills").is_dir() or (candidate / ".git").exists():
            return candidate
    return p


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


def write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def validate_slug(slug: str) -> str:
    slug = slug.strip().lower()
    if not SLUG_RE.fullmatch(slug):
        raise ValueError("slug must match [a-z0-9][a-z0-9._-]{0,63}")
    return slug


def active_task(root: Path) -> str | None:
    env = os.environ.get("LEANLOOP_TASK", "").strip().lower()
    if env:
        try:
            return validate_slug(env)
        except ValueError:
            return None
    marker = root / "state" / "CURRENT_TASK"
    try:
        value = marker.read_text(encoding="utf-8").strip().lower()
    except OSError:
        return None
    try:
        return validate_slug(value)
    except ValueError:
        return None


def active_state_dir(root: Path) -> Path:
    task = active_task(root)
    return root / "state" / "tasks" / task if task else root / "state"
