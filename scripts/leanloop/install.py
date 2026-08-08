#!/usr/bin/env python3
"""Conflict-aware LeanLoop installer for an existing repository.

It never bulk-overwrites the target. LeanLoop support files live under
`.leanloop/kit/`; only native discovery/adapters/settings touch conventional paths.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from leanloop_common import find_repo_root, load_json

START = "<!-- LEANLOOP:ADAPTER:START -->"
END = "<!-- LEANLOOP:ADAPTER:END -->"
GITIGNORE_START = "# LEANLOOP:IGNORE:START"
GITIGNORE_END = "# LEANLOOP:IGNORE:END"


def preflight_merge_targets(target: Path) -> list[str]:
    """Validate mergeable user-owned files before installation mutates anything."""
    issues: list[str] = []
    for rel, start, end in (
        ("AGENTS.md", START, END),
        ("CLAUDE.md", START, END),
        (".gitignore", GITIGNORE_START, GITIGNORE_END),
    ):
        path = target / rel
        if not path.exists():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            issues.append(f"cannot safely read {rel}: {exc}")
            continue
        if (start in text) != (end in text):
            issues.append(f"malformed LeanLoop managed markers in {rel}")

    settings = target / ".claude/settings.json"
    if settings.exists():
        try:
            data = json.loads(settings.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            issues.append(f"invalid .claude/settings.json: {exc}")
        else:
            if not isinstance(data, dict):
                issues.append(".claude/settings.json must contain a JSON object")
            elif "hooks" in data and not isinstance(data["hooks"], dict):
                issues.append(".claude/settings.json hooks must be a JSON object")
            elif isinstance(data.get("hooks"), dict):
                for event, entries in data["hooks"].items():
                    if not isinstance(entries, list):
                        issues.append(f".claude/settings.json hooks.{event} must be a list")
    return issues


def same_tree(a: Path, b: Path) -> bool:
    if not a.exists() or not b.exists(): return False
    if a.is_file() and b.is_file(): return a.read_bytes() == b.read_bytes()
    if a.is_dir() and b.is_dir():
        ar = sorted(p.relative_to(a) for p in a.rglob("*") if p.is_file())
        br = sorted(p.relative_to(b) for p in b.rglob("*") if p.is_file())
        return ar == br and all((a / r).read_bytes() == (b / r).read_bytes() for r in ar)
    return False


def has_conflict(src: Path, dst: Path) -> bool:
    """Return True when an existing destination differs from LeanLoop's source."""
    return (dst.exists() or dst.is_symlink()) and not same_tree(src, dst)


def copy_safe(src: Path, dst: Path) -> None:
    """Copy a preflight-approved path without overwriting unrelated content."""
    if dst.exists() or dst.is_symlink():
        return  # Preflight already proved it is identical.
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        shutil.copytree(src, dst)
    else:
        shutil.copy2(src, dst)


def transformed_adapter(text: str) -> str:
    return (text
            .replace("`PLAYBOOK.md`", "`.leanloop/kit/PLAYBOOK.md`")
            .replace("`skills.json`", "`.leanloop/kit/skills.json`"))


def merge_block(path: Path, content: str) -> None:
    content = content.strip()
    if path.exists():
        original = path.read_text(encoding="utf-8")
        if START in original and END in original:
            before, rest = original.split(START, 1)
            _, after = rest.split(END, 1)
            merged = before.rstrip() + "\n\n" + START + "\n" + content + "\n" + END + after
        else:
            body = content
            lines = body.splitlines()
            if lines and lines[0].startswith("# "):
                lines[0] = "## " + lines[0][2:]
            merged = original.rstrip() + "\n\n" + START + "\n" + "\n".join(lines) + "\n" + END + "\n"
    else:
        merged = content + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(merged, encoding="utf-8")


def merge_gitignore(path: Path) -> None:
    block = "\n".join([
        GITIGNORE_START,
        "state/CURRENT_TASK", "state/CHECKPOINT.md", "state/reports/",
        "state/tasks/*/CHECKPOINT.md", "state/tasks/*/reports/", "__pycache__/",
        GITIGNORE_END,
    ])
    original = path.read_text(encoding="utf-8") if path.exists() else ""
    if GITIGNORE_START in original and GITIGNORE_END in original:
        before, rest = original.split(GITIGNORE_START, 1); _, after = rest.split(GITIGNORE_END, 1)
        text = before.rstrip() + "\n" + block + after
    else:
        text = original.rstrip() + ("\n\n" if original.strip() else "") + block + "\n"
    path.write_text(text, encoding="utf-8")


def merge_claude_settings(target: Path, hook_prefix: str) -> list[str]:
    warnings: list[str] = []
    path = target / ".claude/settings.json"
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    hooks = data.setdefault("hooks", {})
    desired = {
        "PreCompact": ("", f"python3 {hook_prefix}/precompact_checkpoint.py"),
        "SessionStart": ("", f"python3 {hook_prefix}/session_start.py"),
        "PreToolUse": ("Read", f"python3 {hook_prefix}/read_guard.py"),
    }
    for event, (matcher, command) in desired.items():
        entries = hooks.setdefault(event, [])
        found = any(
            command == hook.get("command")
            for entry in entries if isinstance(entry, dict)
            for hook in entry.get("hooks", []) if isinstance(entry.get("hooks", []), list)
            if isinstance(hook, dict)
        )
        if not found:
            entries.append({"matcher": matcher, "hooks": [{"type": "command", "command": command}]})
    if "statusLine" not in data:
        data["statusLine"] = {"type": "command", "command": f"python3 {hook_prefix}/statusline.py"}
    else:
        warnings.append("existing Claude statusLine preserved; LeanLoop statusline not installed")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return warnings


def main() -> int:
    ap = argparse.ArgumentParser(description="Install LeanLoop into an existing repository without destructive copying")
    ap.add_argument("target")
    ap.add_argument("--tiers", default="0,1", help="comma-separated tiers (default: 0,1)")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()

    source = find_repo_root(Path(__file__).resolve())
    target = Path(args.target).expanduser().resolve()
    if not target.is_dir():
        print(f"FAIL: target directory not found: {target}")
        return 2
    cfg = load_json(source / "skills.json", {})
    tiers = cfg.get("tiers", {})
    chosen_tiers = sorted(tiers) if args.all else [x.strip() for x in args.tiers.split(",") if x.strip()]
    unknown = [x for x in chosen_tiers if x not in tiers]
    if unknown:
        print("FAIL: unknown tiers: " + ", ".join(unknown)); return 2
    selected = sorted({name for tier in chosen_tiers for name in tiers[tier]})

    merge_issues = preflight_merge_targets(target)
    if merge_issues:
        print("FAIL: target merge files are not safe to modify; installation did not start:")
        for item in merge_issues:
            print(f"  {item}")
        return 1

    kit = target / ".leanloop/kit"
    copies: list[tuple[Path, Path]] = []
    for name in ("PLAYBOOK.md", "ADOPT.md", "TOOLS.md", "TOOLS.lock", "skills.json"):
        copies.append((source / name, kit / name))
    copies.extend([
        (source / "templates", kit / "templates"),
        (source / "scripts", kit / "scripts"),
        (source / "scripts/leanloop", target / "scripts/leanloop"),
        (source / ".claude/hooks", kit / ".claude/hooks"),
    ])
    copies.extend(
        (source / ".agents/skills" / name, target / ".agents/skills" / name)
        for name in selected
    )
    copies.extend(
        (source / ".claude/agents" / agent, target / ".claude/agents" / agent)
        for agent in ("scout.md", "implementer.md", "implementer-strong.md", "reviewer.md")
    )
    copies.append((source / ".cursor/rules/leanloop.mdc", target / ".cursor/rules/leanloop.mdc"))

    # Transactional preflight for owned paths: fail before creating any LeanLoop file
    # if the target already contains a different file/tree at one of those paths.
    conflicts = [dst.as_posix() for src, dst in copies if has_conflict(src, dst)]
    if conflicts:
        print("FAIL: target contains conflicting LeanLoop-owned paths; installation did not start:")
        for item in conflicts:
            print(f"  {item}")
        print("Resolve/rename conflicts and rerun. Existing user files were preserved.")
        return 1

    for src, dst in copies:
        copy_safe(src, dst)

    merge_block(target / "AGENTS.md", transformed_adapter((source / "AGENTS.md").read_text(encoding="utf-8")))
    merge_block(target / "CLAUDE.md", transformed_adapter((source / "CLAUDE.md").read_text(encoding="utf-8")))
    warnings = merge_claude_settings(target, ".leanloop/kit/.claude/hooks")
    merge_gitignore(target / ".gitignore")
    (target / "state/tasks").mkdir(parents=True, exist_ok=True)
    (target / "state/tasks/.gitkeep").touch(exist_ok=True)

    sync = subprocess.run([sys.executable, str(target / "scripts/leanloop/sync.py")], cwd=target, text=True)
    if sync.returncode:
        print("FAIL: support kit installed but skill propagation failed")
        return sync.returncode
    print(f"Installed LeanLoop tiers {','.join(chosen_tiers)} ({len(selected)} skills) without overwriting foreign skills/files.")
    for w in warnings: print(f"WARN: {w}")
    print("Next: create STACK.md/PLAN.md from .leanloop/kit/templates as needed; run `python3 scripts/leanloop/doctor.py`.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
