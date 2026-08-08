#!/usr/bin/env python3
"""LeanLoop self-diagnostics. Stdlib only."""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

from leanloop_common import find_repo_root, load_json

DESC_RE = re.compile(r"^description:\s*(.+)$", re.M)
REQUIRED_LOCK_KEYS = {
    "CCUSAGE_VERSION", "OPENWIKI_VERSION", "CLAUDE_MONITOR_VERSION",
    "UI_UX_PRO_MAX_VERSION", "DEPENDENCY_CRUISER_VERSION",
}


def main() -> int:
    ap = argparse.ArgumentParser(description="Check LeanLoop configuration, skill budget, and propagated drift")
    ap.add_argument("--strict", action="store_true", help="treat warnings as failures")
    args = ap.parse_args()
    root = find_repo_root(Path.cwd())
    framework_mode = (root / "skills.json").exists()
    support = root if framework_mode else root / ".leanloop/kit"
    fails: list[str] = []
    warns: list[str] = []

    config = load_json(support / "skills.json", {})
    tiers = config.get("tiers", {}) if isinstance(config, dict) else {}
    listed: list[str] = [name for tier in tiers.values() for name in tier]
    canonical = sorted(p.parent.name for p in (root / ".agents/skills").glob("*/SKILL.md"))
    if len(listed) != len(set(listed)):
        fails.append("skills.json contains duplicate skill names across tiers")
    unknown = sorted(set(canonical) - set(listed))
    if unknown:
        fails.append(f"canonical skills not declared in skills.json: {', '.join(unknown)}")
    if framework_mode:
        missing = sorted(set(listed) - set(canonical))
        if missing:
            fails.append(f"framework skills missing from canonical tree: {', '.join(missing)}")

    desc_chars = 0
    for name in canonical:
        path = root / ".agents/skills" / name / "SKILL.md"
        text = path.read_text(encoding="utf-8")
        m = DESC_RE.search(text)
        if not m:
            fails.append(f"missing description frontmatter: {path.relative_to(root)}")
        else:
            desc_chars += len(m.group(1).strip())
        lines = text.count("\n") + 1
        if lines > 150:
            warns.append(f"skill body >150 lines: {name} ({lines})")
    rough_tokens = desc_chars // 4
    if rough_tokens > 1500:
        warns.append(f"skill description payload ≈{rough_tokens} rough tokens (>1500 target)")

    for adapter in ("CLAUDE.md", "AGENTS.md", ".cursor/rules/leanloop.mdc"):
        path = root / adapter
        if not path.exists():
            fails.append(f"missing adapter: {adapter}")
            continue
        text = path.read_text(encoding="utf-8")
        if "LEANLOOP:SKILLS:START" in text:
            fails.append(f"duplicated generated skill index still present: {adapter}")
        if framework_mode and adapter == "CLAUDE.md" and text.count("\n") + 1 > 50:
            warns.append("CLAUDE.md exceeds 50 lines")

    lock = {}
    for line in (support / "TOOLS.lock").read_text(encoding="utf-8").splitlines() if (support / "TOOLS.lock").exists() else []:
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1); lock[k.strip()] = v.strip()
    missing_lock = sorted(REQUIRED_LOCK_KEYS - set(lock))
    if missing_lock:
        fails.append("TOOLS.lock missing keys: " + ", ".join(missing_lock))

    sync = subprocess.run([sys.executable, str(root / "scripts/leanloop/sync.py"), "--check"], cwd=root, text=True, capture_output=True)
    if sync.returncode:
        fails.append("propagated skill drift: run `python3 scripts/leanloop/sync.py`\n" + sync.stdout.strip())

    print(f"LeanLoop doctor: {len(canonical)} skills; descriptions ≈{rough_tokens} rough tokens")
    for item in warns: print(f"WARN: {item}")
    for item in fails: print(f"FAIL: {item}")
    if fails or (args.strict and warns):
        return 1
    print("OK: core invariants healthy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
