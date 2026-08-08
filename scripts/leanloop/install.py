#!/usr/bin/env python3
"""Safe LeanLoop install / upgrade / uninstall lifecycle.

The installer treats project state as user-owned by default. Files copied by LeanLoop
are tracked with SHA-256 provenance in `.leanloop/install.json`; upgrades overwrite
only unchanged managed files, and uninstall removes only unchanged managed files plus
exact managed adapter/settings fragments.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable

from leanloop_common import find_repo_root, load_json, write_json_atomic

START = "<!-- LEANLOOP:ADAPTER:START -->"
END = "<!-- LEANLOOP:ADAPTER:END -->"
GITIGNORE_START = "# LEANLOOP:IGNORE:START"
GITIGNORE_END = "# LEANLOOP:IGNORE:END"
INSTALL_MANIFEST = Path(".leanloop/install.json")
SYNC_MANIFEST = Path(".leanloop/managed.json")
INSTALL_SCHEMA = 1
SKIP_PARTS = {"__pycache__", ".pytest_cache"}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_digest(path: Path) -> str:
    try:
        return sha256_bytes(path.read_bytes())
    except OSError:
        return "missing"


def tree_digest(path: Path) -> str:
    """Digest a skill tree using the same format as sync.py."""
    h = hashlib.sha256()
    if path.is_symlink():
        target = path.resolve()
        if not target.exists():
            return "broken-symlink"
        path = target
    if not path.exists():
        return "missing"
    for item in sorted(p for p in path.rglob("*") if p.is_file()):
        rel = item.relative_to(path).as_posix().encode()
        h.update(rel + b"\0")
        h.update(item.read_bytes())
        h.update(b"\0")
    return h.hexdigest()


def read_version(source: Path) -> str:
    try:
        value = (source / "VERSION").read_text(encoding="utf-8").strip()
    except OSError:
        return "0+unknown"
    return value or "0+unknown"


def preflight_merge_targets(target: Path) -> list[str]:
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


def extract_block(text: str, start: str, end: str) -> str | None:
    if start not in text or end not in text:
        return None
    _, rest = text.split(start, 1)
    body, _ = rest.split(end, 1)
    return body.strip("\n")


def managed_block_hash(path: Path, start: str, end: str) -> str | None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    body = extract_block(text, start, end)
    return sha256_bytes(body.encode("utf-8")) if body is not None else None


def transformed_adapter(text: str) -> str:
    return (
        text.replace("`PLAYBOOK.md`", "`.leanloop/kit/PLAYBOOK.md`")
        .replace("`skills.json`", "`.leanloop/kit/skills.json`")
    )


def merge_block(path: Path, content: str, start: str = START, end: str = END) -> None:
    content = content.strip()
    if path.exists():
        original = path.read_text(encoding="utf-8")
        if start in original and end in original:
            before, rest = original.split(start, 1)
            _, after = rest.split(end, 1)
            merged = before.rstrip() + "\n\n" + start + "\n" + content + "\n" + end + after
        else:
            merged = original.rstrip() + "\n\n" + start + "\n" + content + "\n" + end + "\n"
    else:
        merged = start + "\n" + content + "\n" + end + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(merged, encoding="utf-8")


def remove_block(path: Path, start: str, end: str) -> None:
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    if start not in text or end not in text:
        return
    before, rest = text.split(start, 1)
    _, after = rest.split(end, 1)
    merged = (before.rstrip() + "\n\n" + after.lstrip()).strip("\n")
    path.write_text((merged + "\n") if merged else "", encoding="utf-8")


def gitignore_block() -> str:
    return "\n".join([
        "state/CURRENT_TASK",
        "state/CHECKPOINT.md",
        "state/reports/",
        "state/tasks/*/CHECKPOINT.md",
        "state/tasks/*/reports/",
        "__pycache__/",
    ])


def merge_gitignore(path: Path) -> None:
    merge_block(path, gitignore_block(), GITIGNORE_START, GITIGNORE_END)


def command_exists(words: list[str]) -> bool:
    if not words:
        return False
    exe = words[0]
    if os.path.isabs(exe):
        return Path(exe).exists()
    return shutil.which(exe) is not None


def choose_python_command(explicit: str | None = None) -> str:
    if explicit:
        words = shlex.split(explicit, posix=os.name != "nt")
        if not command_exists(words):
            raise ValueError(f"Python command not found: {explicit}")
        return explicit

    candidates = (["python"], ["py", "-3"], ["python3"]) if os.name == "nt" else (["python3"], ["python"])
    for words in candidates:
        if command_exists(list(words)):
            return " ".join(words)

    # The installer itself is running under Python, so this is the final safe local fallback.
    return subprocess.list2cmdline([sys.executable]) if os.name == "nt" else shlex.quote(sys.executable)


def desired_hook_commands(python_command: str, hook_prefix: str) -> dict[str, tuple[str, str]]:
    return {
        "PreCompact": ("", f"{python_command} {hook_prefix}/precompact_checkpoint.py"),
        "SessionStart": ("", f"{python_command} {hook_prefix}/session_start.py"),
        "PreToolUse": ("Read", f"{python_command} {hook_prefix}/read_guard.py"),
    }


def remove_hook_commands(data: dict, commands: Iterable[str]) -> None:
    wanted = set(commands)
    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        return
    for event in list(hooks):
        entries = hooks[event]
        if not isinstance(entries, list):
            continue
        new_entries = []
        for entry in entries:
            if not isinstance(entry, dict):
                new_entries.append(entry)
                continue
            raw_hooks = entry.get("hooks")
            if not isinstance(raw_hooks, list):
                new_entries.append(entry)
                continue
            kept = [h for h in raw_hooks if not (isinstance(h, dict) and h.get("command") in wanted)]
            if kept:
                clone = dict(entry)
                clone["hooks"] = kept
                new_entries.append(clone)
        if new_entries:
            hooks[event] = new_entries
        else:
            hooks.pop(event, None)
    if not hooks:
        data.pop("hooks", None)


def merge_claude_settings(
    target: Path,
    python_command: str,
    previous_meta: dict | None = None,
) -> tuple[list[str], dict]:
    warnings: list[str] = []
    path = target / ".claude/settings.json"
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    previous_meta = previous_meta or {}
    old_commands = previous_meta.get("hook_commands", [])
    if isinstance(old_commands, list):
        remove_hook_commands(data, [x for x in old_commands if isinstance(x, str)])

    hooks = data.setdefault("hooks", {})
    desired = desired_hook_commands(python_command, ".leanloop/kit/.claude/hooks")
    installed_commands: list[str] = []
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
        installed_commands.append(command)

    desired_status = f"{python_command} .leanloop/kit/.claude/hooks/statusline.py"
    previous_status = previous_meta.get("status_line_command")
    previous_installed = bool(previous_meta.get("status_line_installed"))
    current_status = data.get("statusLine")
    status_installed = False
    if previous_installed and isinstance(current_status, dict) and current_status.get("command") == previous_status:
        data["statusLine"] = {"type": "command", "command": desired_status}
        status_installed = True
    elif "statusLine" not in data:
        data["statusLine"] = {"type": "command", "command": desired_status}
        status_installed = True
    elif isinstance(current_status, dict) and current_status.get("command") == desired_status:
        status_installed = True
    else:
        warnings.append("existing/user-modified Claude statusLine preserved; LeanLoop statusline not installed")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return warnings, {
        "hook_commands": installed_commands,
        "status_line_command": desired_status,
        "status_line_installed": status_installed,
    }


def uninstall_claude_settings(target: Path, meta: dict) -> None:
    path = target / ".claude/settings.json"
    if not path.exists():
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    commands = meta.get("hook_commands", []) if isinstance(meta, dict) else []
    if isinstance(commands, list):
        remove_hook_commands(data, [x for x in commands if isinstance(x, str)])
    if isinstance(meta, dict) and meta.get("status_line_installed"):
        current = data.get("statusLine")
        if isinstance(current, dict) and current.get("command") == meta.get("status_line_command"):
            data.pop("statusLine", None)
    if data:
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    else:
        path.write_text("{}\n", encoding="utf-8")


def should_skip(path: Path) -> bool:
    return any(part in SKIP_PARTS for part in path.parts) or path.suffix in {".pyc", ".pyo"}


def add_source_files(desired: dict[str, bytes], src: Path, dst_rel: Path) -> None:
    if src.is_file():
        desired[dst_rel.as_posix()] = src.read_bytes()
        return
    for item in sorted(p for p in src.rglob("*") if p.is_file() and not should_skip(p.relative_to(src))):
        desired[(dst_rel / item.relative_to(src)).as_posix()] = item.read_bytes()


def build_desired_files(source: Path, selected: list[str]) -> dict[str, bytes]:
    desired: dict[str, bytes] = {}
    kit = Path(".leanloop/kit")
    for name in ("PLAYBOOK.md", "ADOPT.md", "TOOLS.md", "TOOLS.lock", "skills.json", "VERSION"):
        add_source_files(desired, source / name, kit / name)
    for src, dst in (
        (source / "templates", kit / "templates"),
        (source / "scripts", kit / "scripts"),
        (source / ".claude/hooks", kit / ".claude/hooks"),
        (source / "scripts/leanloop", Path("scripts/leanloop")),
        (source / ".claude/agents", Path(".claude/agents")),
    ):
        add_source_files(desired, src, dst)
    add_source_files(desired, source / ".cursor/rules/leanloop.mdc", Path(".cursor/rules/leanloop.mdc"))
    for name in selected:
        add_source_files(desired, source / ".agents/skills" / name, Path(".agents/skills") / name)
    desired["state/tasks/.gitkeep"] = b""
    return desired


def managed_file_conflicts(target: Path, desired: dict[str, bytes], previous: dict[str, str]) -> list[str]:
    issues: list[str] = []
    for rel, old_digest in sorted(previous.items()):
        path = target / rel
        if not path.exists():
            continue
        if not path.is_file():
            issues.append(f"managed path changed type: {rel}")
            continue
        current = file_digest(path)
        desired_digest = sha256_bytes(desired[rel]) if rel in desired else None
        if current != old_digest and current != desired_digest:
            issues.append(f"managed file modified locally: {rel}")
    for rel, content in sorted(desired.items()):
        if rel in previous:
            continue
        path = target / rel
        if path.exists() or path.is_symlink():
            if not path.is_file() or file_digest(path) != sha256_bytes(content):
                issues.append(f"new LeanLoop-managed path conflicts with existing content: {rel}")
    return issues


def block_conflicts(target: Path, previous_blocks: dict, desired_blocks: dict[str, tuple[str, str, str]]) -> list[str]:
    issues: list[str] = []
    for rel, (start, end, desired_body) in desired_blocks.items():
        path = target / rel
        old_digest = previous_blocks.get(rel) if isinstance(previous_blocks, dict) else None
        current_digest = managed_block_hash(path, start, end)
        desired_digest = sha256_bytes(desired_body.encode("utf-8"))
        if old_digest is not None and current_digest not in {old_digest, desired_digest}:
            issues.append(f"managed block modified locally: {rel}")
        elif old_digest is None and current_digest is not None and current_digest != desired_digest:
            issues.append(f"untracked LeanLoop-style managed block conflicts with install: {rel}")
    return issues


def write_managed_files(target: Path, desired: dict[str, bytes], previous: dict[str, str]) -> dict[str, str]:
    # Remove stale files only after preflight has proven they are unchanged.
    for rel in sorted(set(previous) - set(desired), reverse=True):
        path = target / rel
        if path.is_file() or path.is_symlink():
            path.unlink(missing_ok=True)
            remove_empty_parents(path.parent, target)
    for rel, content in sorted(desired.items()):
        path = target / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    return {rel: sha256_bytes(content) for rel, content in sorted(desired.items())}


def remove_empty_parents(path: Path, stop: Path) -> None:
    current = path
    while current != stop and stop in current.parents:
        try:
            current.rmdir()
        except OSError:
            break
        current = current.parent


def selected_tiers(cfg: dict, args: argparse.Namespace, existing: dict | None) -> tuple[list[str], list[str]]:
    tiers = cfg.get("tiers", {}) if isinstance(cfg, dict) else {}
    if args.all:
        chosen = sorted(tiers)
    elif args.tiers:
        chosen = [x.strip() for x in args.tiers.split(",") if x.strip()]
    elif args.upgrade and existing:
        chosen = [str(x) for x in existing.get("installed_tiers", [])]
    else:
        chosen = ["0", "1"]
    if args.add_tiers:
        chosen.extend(x.strip() for x in args.add_tiers.split(",") if x.strip())
    chosen = sorted(set(chosen))
    unknown = [x for x in chosen if x not in tiers]
    if unknown:
        raise ValueError("unknown tiers: " + ", ".join(unknown))
    selected = sorted({name for tier in chosen for name in tiers[tier]})
    return chosen, selected



def propagation_preflight(target: Path, selected: list[str]) -> list[str]:
    """Mirror sync ownership checks before lifecycle writes anything."""
    manifest = load_json(target / SYNC_MANIFEST, {})
    targets = manifest.get("targets", {}) if isinstance(manifest, dict) else {}
    issues: list[str] = []
    for target_rel in (".claude/skills", ".cursor/skills"):
        entry = targets.get(target_rel, {}) if isinstance(targets, dict) else {}
        previous = entry.get("skills", {}) if isinstance(entry, dict) else {}
        if not isinstance(previous, dict):
            previous = {}
        for name in selected:
            dest = target / target_rel / name
            old_digest = previous.get(name)
            if old_digest is None and (dest.exists() or dest.is_symlink()):
                issues.append(f"foreign skill conflicts with selected LeanLoop skill: {(Path(target_rel) / name).as_posix()}")
            elif old_digest is not None and (dest.exists() or dest.is_symlink()) and tree_digest(dest) != old_digest:
                issues.append(f"propagated managed skill modified locally: {(Path(target_rel) / name).as_posix()}")
        for name, old_digest in previous.items():
            if name in selected:
                continue
            dest = target / target_rel / name
            if (dest.exists() or dest.is_symlink()) and tree_digest(dest) != old_digest:
                issues.append(f"stale propagated managed skill modified locally: {(Path(target_rel) / name).as_posix()}")
    return issues


def sync_ownership_hash(path: Path) -> str:
    """Fingerprint only sync ownership, not copy-vs-link mode."""
    manifest = load_json(path, {})
    targets = manifest.get("targets", {}) if isinstance(manifest, dict) else {}
    normalized: dict[str, dict[str, str]] = {}
    if isinstance(targets, dict):
        for target_rel, entry in sorted(targets.items()):
            skills = entry.get("skills", {}) if isinstance(entry, dict) else {}
            if isinstance(skills, dict):
                normalized[target_rel] = {str(k): str(v) for k, v in sorted(skills.items())}
    payload = json.dumps({"schema_version": manifest.get("schema_version") if isinstance(manifest, dict) else None, "targets": normalized}, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(payload)

def propagated_conflicts(target: Path) -> list[str]:
    manifest = load_json(target / SYNC_MANIFEST, {})
    targets = manifest.get("targets", {}) if isinstance(manifest, dict) else {}
    issues: list[str] = []
    for target_rel, entry in targets.items():
        if not isinstance(entry, dict):
            continue
        skills = entry.get("skills", {})
        if not isinstance(skills, dict):
            continue
        for name, digest in skills.items():
            path = target / target_rel / name
            if (path.exists() or path.is_symlink()) and tree_digest(path) != digest:
                issues.append(f"propagated managed skill modified locally: {(Path(target_rel) / name).as_posix()}")
    return issues


def remove_propagated_skills(target: Path) -> None:
    manifest = load_json(target / SYNC_MANIFEST, {})
    targets = manifest.get("targets", {}) if isinstance(manifest, dict) else {}
    for target_rel, entry in targets.items():
        skills = entry.get("skills", {}) if isinstance(entry, dict) else {}
        if not isinstance(skills, dict):
            continue
        for name in skills:
            path = target / target_rel / name
            if path.is_symlink() or path.is_file():
                path.unlink(missing_ok=True)
            elif path.is_dir():
                shutil.rmtree(path)
            remove_empty_parents(path.parent, target)


def lifecycle_manifest(
    version: str,
    tiers: list[str],
    managed_files: dict[str, str],
    managed_blocks: dict[str, str],
    python_command: str,
    claude_meta: dict,
    previous: dict | None,
    sync_hash: str,
) -> dict:
    previous = previous or {}
    return {
        "schema_version": INSTALL_SCHEMA,
        "leanloop_version": version,
        "installed_tiers": tiers,
        "python_command": python_command,
        "managed_files": managed_files,
        "managed_blocks": managed_blocks,
        "claude": claude_meta,
        "sync_ownership_hash": sync_hash,
        "created_merge_files": previous.get("created_merge_files", {}),
    }


def install_or_upgrade(source: Path, target: Path, args: argparse.Namespace) -> int:
    manifest_path = target / INSTALL_MANIFEST
    existing = load_json(manifest_path, None)
    if args.upgrade and not isinstance(existing, dict):
        print("FAIL: --upgrade requires an existing .leanloop/install.json provenance manifest")
        return 1
    if not args.upgrade and isinstance(existing, dict):
        print("FAIL: LeanLoop is already installed; use --upgrade")
        return 1
    if isinstance(existing, dict) and existing.get("schema_version") != INSTALL_SCHEMA:
        print(f"FAIL: unsupported install manifest schema: {existing.get('schema_version')}")
        return 1

    cfg = load_json(source / "skills.json", {})
    try:
        tiers, selected = selected_tiers(cfg, args, existing if isinstance(existing, dict) else None)
        python_command = choose_python_command(args.python_command or (existing or {}).get("python_command"))
    except ValueError as exc:
        print(f"FAIL: {exc}")
        return 2

    merge_issues = preflight_merge_targets(target)
    if merge_issues:
        print("FAIL: target merge files are not safe to modify; installation did not start and no lifecycle changes were made:")
        for item in merge_issues:
            print(f"  {item}")
        return 1

    desired = build_desired_files(source, selected)
    previous_files = existing.get("managed_files", {}) if isinstance(existing, dict) else {}
    if not isinstance(previous_files, dict):
        previous_files = {}

    adapter_agents = transformed_adapter((source / "AGENTS.md").read_text(encoding="utf-8")).strip()
    adapter_claude = transformed_adapter((source / "CLAUDE.md").read_text(encoding="utf-8")).strip()
    desired_blocks = {
        "AGENTS.md": (START, END, adapter_agents),
        "CLAUDE.md": (START, END, adapter_claude),
        ".gitignore": (GITIGNORE_START, GITIGNORE_END, gitignore_block()),
    }
    previous_blocks = existing.get("managed_blocks", {}) if isinstance(existing, dict) else {}

    conflicts = managed_file_conflicts(target, desired, previous_files)
    conflicts.extend(block_conflicts(target, previous_blocks, desired_blocks))
    conflicts.extend(propagation_preflight(target, selected))
    if isinstance(existing, dict) and existing.get("sync_ownership_hash"):
        if sync_ownership_hash(target / SYNC_MANIFEST) != existing.get("sync_ownership_hash"):
            conflicts.append("propagated-skill ownership manifest changed outside the tracked lifecycle")
    if conflicts:
        print("FAIL: locally modified/conflicting LeanLoop-managed content; installation did not start and no lifecycle changes were made:")
        for item in conflicts:
            print(f"  {item}")
        print("Move intentional edits out of managed paths (or restore them) before retrying.")
        return 1

    created_merge = dict(existing.get("created_merge_files", {})) if isinstance(existing, dict) else {}
    if not existing:
        for rel in desired_blocks:
            created_merge[rel] = not (target / rel).exists()

    managed_files = write_managed_files(target, desired, previous_files)
    merge_block(target / "AGENTS.md", adapter_agents)
    merge_block(target / "CLAUDE.md", adapter_claude)
    merge_gitignore(target / ".gitignore")
    warnings, claude_meta = merge_claude_settings(
        target, python_command, existing.get("claude", {}) if isinstance(existing, dict) else None
    )

    sync = subprocess.run([sys.executable, str(target / "scripts/leanloop/sync.py")], cwd=target, text=True)
    if sync.returncode:
        print("FAIL: managed files updated but skill propagation failed; inspect sync output before retrying")
        return sync.returncode

    managed_blocks = {
        rel: sha256_bytes(body.encode("utf-8"))
        for rel, (_, _, body) in desired_blocks.items()
    }
    manifest = lifecycle_manifest(
        read_version(source), tiers, managed_files, managed_blocks, python_command,
        claude_meta, existing if isinstance(existing, dict) else None,
        sync_ownership_hash(target / SYNC_MANIFEST),
    )
    manifest["created_merge_files"] = created_merge
    write_json_atomic(manifest_path, manifest)

    verb = "Upgraded" if args.upgrade else "Installed"
    print(f"{verb} LeanLoop {manifest['leanloop_version']} tiers {','.join(tiers)} ({len(selected)} skills).")
    print("Foreign skills/files and unrelated project configuration were preserved.")
    for warning in warnings:
        print(f"WARN: {warning}")
    print("Next: run `python scripts/leanloop/doctor.py --strict`.")
    return 0


def uninstall(target: Path) -> int:
    manifest_path = target / INSTALL_MANIFEST
    manifest = load_json(manifest_path, None)
    if not isinstance(manifest, dict):
        print("FAIL: no .leanloop/install.json provenance manifest; refusing untracked uninstall")
        return 1
    if manifest.get("schema_version") != INSTALL_SCHEMA:
        print(f"FAIL: unsupported install manifest schema: {manifest.get('schema_version')}")
        return 1
    merge_issues = preflight_merge_targets(target)
    if merge_issues:
        print("FAIL: target merge files are not safe to modify; uninstall did not start:")
        for item in merge_issues:
            print(f"  {item}")
        return 1

    managed_files = manifest.get("managed_files", {})
    conflicts: list[str] = []
    if isinstance(managed_files, dict):
        for rel, digest in managed_files.items():
            path = target / rel
            if path.exists() and (not path.is_file() or file_digest(path) != digest):
                conflicts.append(f"managed file modified locally: {rel}")
    expected_sync_hash = manifest.get("sync_ownership_hash")
    if expected_sync_hash and sync_ownership_hash(target / SYNC_MANIFEST) != expected_sync_hash:
        conflicts.append("propagated-skill ownership manifest changed outside the tracked lifecycle")
    conflicts.extend(propagated_conflicts(target))

    blocks = manifest.get("managed_blocks", {})
    for rel, digest in blocks.items() if isinstance(blocks, dict) else []:
        start, end = (GITIGNORE_START, GITIGNORE_END) if rel == ".gitignore" else (START, END)
        current = managed_block_hash(target / rel, start, end)
        if current is not None and current != digest:
            conflicts.append(f"managed block modified locally: {rel}")

    if conflicts:
        print("FAIL: locally modified LeanLoop-managed content; uninstall did not start:")
        for item in conflicts:
            print(f"  {item}")
        return 1

    remove_propagated_skills(target)
    if isinstance(managed_files, dict):
        for rel in sorted(managed_files, reverse=True):
            path = target / rel
            if path.is_file() or path.is_symlink():
                path.unlink(missing_ok=True)
                remove_empty_parents(path.parent, target)

    remove_block(target / "AGENTS.md", START, END)
    remove_block(target / "CLAUDE.md", START, END)
    remove_block(target / ".gitignore", GITIGNORE_START, GITIGNORE_END)
    uninstall_claude_settings(target, manifest.get("claude", {}))

    (target / SYNC_MANIFEST).unlink(missing_ok=True)
    manifest_path.unlink(missing_ok=True)
    for candidate in (
        target / ".leanloop/kit",
        target / ".leanloop",
        target / "scripts/leanloop",
        target / ".agents/skills",
        target / ".claude/skills",
        target / ".cursor/skills",
    ):
        if candidate.exists() and candidate.is_dir():
            try:
                candidate.rmdir()
            except OSError:
                pass

    print("Uninstalled tracked LeanLoop files/config fragments; foreign files, task state, and user Git state were preserved.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Install, upgrade, or uninstall LeanLoop without destructive guessing")
    ap.add_argument("target")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--upgrade", action="store_true", help="upgrade an installation tracked by .leanloop/install.json")
    mode.add_argument("--uninstall", action="store_true", help="remove only verified LeanLoop-managed content")
    ap.add_argument("--tiers", default=None, help="comma-separated tiers; install default is 0,1; upgrade default keeps current tiers")
    ap.add_argument("--add-tiers", default=None, help="add tiers to the current/default selection")
    ap.add_argument("--all", action="store_true", help="select every built-in skill tier")
    ap.add_argument("--python-command", default=None, help="hook interpreter command (auto-detected by default)")
    args = ap.parse_args()

    source = find_repo_root(Path(__file__).resolve())
    target = Path(args.target).expanduser().resolve()
    if not target.is_dir():
        print(f"FAIL: target directory not found: {target}")
        return 2
    if args.uninstall:
        if args.tiers or args.add_tiers or args.all or args.python_command:
            print("FAIL: tier/python options cannot be used with --uninstall")
            return 2
        return uninstall(target)
    return install_or_upgrade(source, target, args)


if __name__ == "__main__":
    raise SystemExit(main())
