#!/usr/bin/env python3
"""LeanLoop self-diagnostics. Stdlib only."""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

from leanloop_common import find_repo_root, load_json

DESC_RE = re.compile(r"^description:\s*(.+)$", re.M)
REQUIRED_LOCK_KEYS = {
    "CCUSAGE_VERSION", "OPENWIKI_VERSION", "CLAUDE_MONITOR_VERSION",
    "UI_UX_PRO_MAX_VERSION", "DEPENDENCY_CRUISER_VERSION",
}
MIN_PYTHON = (3, 10)
INSTALL_SCHEMA = 1


def sha256_file(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return "missing"


def read_version(support: Path) -> str:
    try:
        return (support / "VERSION").read_text(encoding="utf-8").strip() or "0+unknown"
    except OSError:
        return "0+unknown"


def command_available(command: str) -> bool:
    try:
        words = shlex.split(command, posix=os.name != "nt")
    except ValueError:
        return False
    if not words:
        return False
    exe = words[0].strip('"')
    if os.path.isabs(exe):
        return Path(exe).exists()
    return shutil.which(exe) is not None



def sync_ownership_hash(path: Path) -> str:
    manifest = load_json(path, {})
    targets = manifest.get("targets", {}) if isinstance(manifest, dict) else {}
    normalized: dict[str, dict[str, str]] = {}
    if isinstance(targets, dict):
        for target_rel, entry in sorted(targets.items()):
            skills = entry.get("skills", {}) if isinstance(entry, dict) else {}
            if isinstance(skills, dict):
                normalized[target_rel] = {str(k): str(v) for k, v in sorted(skills.items())}
    import json
    payload = json.dumps({"schema_version": manifest.get("schema_version") if isinstance(manifest, dict) else None, "targets": normalized}, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()

def main() -> int:
    ap = argparse.ArgumentParser(description="Check LeanLoop version, configuration, skill budget, provenance, and propagated drift")
    ap.add_argument("--strict", action="store_true", help="treat warnings as failures")
    ap.add_argument("--version", action="store_true", help="print LeanLoop version and exit")
    args = ap.parse_args()

    root = find_repo_root(Path.cwd())
    framework_mode = (root / "skills.json").exists()
    support = root if framework_mode else root / ".leanloop/kit"
    version = read_version(support)
    if args.version:
        print(version)
        return 0

    fails: list[str] = []
    warns: list[str] = []
    if sys.version_info < MIN_PYTHON:
        fails.append(f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ required; running {sys.version_info.major}.{sys.version_info.minor}")
    if version == "0+unknown":
        fails.append("missing/empty VERSION file")

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
        match = DESC_RE.search(text)
        if not match:
            fails.append(f"missing description frontmatter: {path.relative_to(root)}")
        else:
            desc_chars += len(match.group(1).strip())
        lines = text.count("\n") + 1
        if lines > 150:
            warns.append(f"skill body >150 lines: {name} ({lines})")
    rough_tokens = desc_chars // 4
    if rough_tokens > 1500:
        warns.append(f"skill description payload ~{rough_tokens} rough tokens (>1500 target)")

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
            key, value = line.split("=", 1)
            lock[key.strip()] = value.strip()
    missing_lock = sorted(REQUIRED_LOCK_KEYS - set(lock))
    if missing_lock:
        fails.append("TOOLS.lock missing keys: " + ", ".join(missing_lock))

    if not framework_mode:
        install = load_json(root / ".leanloop/install.json", None)
        if not isinstance(install, dict):
            fails.append("installed project missing .leanloop/install.json provenance manifest")
        else:
            if install.get("schema_version") != INSTALL_SCHEMA:
                fails.append(f"unsupported install manifest schema: {install.get('schema_version')}")
            if install.get("leanloop_version") != version:
                fails.append(f"install manifest version {install.get('leanloop_version')} != kit VERSION {version}")
            managed = install.get("managed_files", {})
            if not isinstance(managed, dict):
                fails.append("install manifest managed_files must be an object")
            else:
                changed = [rel for rel, digest in managed.items() if not (root / rel).is_file() or sha256_file(root / rel) != digest]
                if changed:
                    fails.append("missing/modified LeanLoop-managed files: " + ", ".join(changed[:8]) + (" ..." if len(changed) > 8 else ""))
            expected_sync = install.get("sync_ownership_hash")
            if expected_sync and sync_ownership_hash(root / ".leanloop/managed.json") != expected_sync:
                fails.append("propagated-skill ownership manifest changed outside the tracked lifecycle")
            python_command = install.get("python_command")
            if not isinstance(python_command, str) or not command_available(python_command):
                fails.append(f"configured hook Python command is unavailable: {python_command!r}")

    sync_script = root / "scripts/leanloop/sync.py"
    if not sync_script.exists():
        fails.append("missing scripts/leanloop/sync.py")
    else:
        sync = subprocess.run([sys.executable, str(sync_script), "--check"], cwd=root, text=True, capture_output=True)
        if sync.returncode:
            fails.append("propagated skill drift: run `python scripts/leanloop/sync.py`\n" + sync.stdout.strip())

    print(f"LeanLoop {version} doctor: {len(canonical)} skills; descriptions ~{rough_tokens} rough tokens")
    for item in warns:
        print(f"WARN: {item}")
    for item in fails:
        print(f"FAIL: {item}")
    if fails or (args.strict and warns):
        return 1
    print("OK: core invariants healthy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
