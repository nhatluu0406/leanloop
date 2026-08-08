#!/usr/bin/env python3
"""Non-destructive LeanLoop skill synchronization.

Canonical source: .agents/skills/<name>/
Targets: .claude/skills/<name>/ and .cursor/skills/<name>/

Only entries recorded in .leanloop/managed.json are updated or removed. Foreign
skills are never deleted or overwritten. A locally modified managed copy causes
an error until the change is moved back to the canonical source or --force-managed
is explicitly used.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import sys
from pathlib import Path

from leanloop_common import find_repo_root, load_json, write_json_atomic

TARGETS = (Path(".claude/skills"), Path(".cursor/skills"))
MANIFEST = Path(".leanloop/managed.json")
INSTALL_MANIFEST = Path(".leanloop/install.json")
KIT_SKILLS = Path(".leanloop/kit/skills.json")


def digest_tree(path: Path) -> str:
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


def skill_dirs(src: Path) -> dict[str, Path]:
    out: dict[str, Path] = {}
    for child in sorted(src.iterdir() if src.exists() else []):
        if child.is_dir() and (child / "SKILL.md").is_file():
            out[child.name] = child
    return out



def parse_skill_names(value: str | None) -> list[str] | None:
    if value is None:
        return None
    return sorted({name.strip() for name in value.split(",") if name.strip()})


def installed_skill_names(root: Path) -> list[str] | None:
    """Return the LeanLoop-owned skill scope for an installed project.

    A project may keep its own skills in .agents/skills. Those entries are not
    LeanLoop-owned and must never be propagated merely because they share the
    canonical source directory.
    """
    install = load_json(root / INSTALL_MANIFEST, None)
    if not isinstance(install, dict):
        return None
    tiers = install.get("installed_tiers", [])
    cfg = load_json(root / KIT_SKILLS, {})
    tier_map = cfg.get("tiers", {}) if isinstance(cfg, dict) else {}
    if not isinstance(tiers, list) or not isinstance(tier_map, dict):
        return []
    return sorted({
        name
        for tier in tiers
        for name in (tier_map.get(str(tier), []) if isinstance(tier_map.get(str(tier), []), list) else [])
        if isinstance(name, str)
    })


def scoped_skills(all_skills: dict[str, Path], names: list[str] | None) -> tuple[dict[str, Path], list[str]]:
    if names is None:
        return all_skills, []
    missing = [name for name in names if name not in all_skills]
    return {name: all_skills[name] for name in names if name in all_skills}, missing

def safe_remove(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink(missing_ok=True)
    elif path.is_dir():
        shutil.rmtree(path)


def ensure_replaceable(path: Path, previous_digest: str | None, force: bool) -> None:
    if not path.exists() and not path.is_symlink():
        return
    if previous_digest is None:
        raise RuntimeError(f"refusing to overwrite foreign skill: {path}")
    current = digest_tree(path)
    if current != previous_digest and not force:
        raise RuntimeError(
            f"managed copy changed locally: {path}\n"
            "Move the edit to .agents/skills first, or rerun with --force-managed."
        )


def sync_preflight(root: Path, canonical: dict[str, Path], previous_targets: dict, force: bool) -> list[str]:
    """Validate every propagation target before mutating any of them.

    Exact unmanaged copies are safe to adopt. Different same-name unmanaged skills
    remain foreign and block synchronization.
    """
    issues: list[str] = []
    for target_rel in TARGETS:
        key = target_rel.as_posix()
        entry = previous_targets.get(key, {}) if isinstance(previous_targets, dict) else {}
        prev_skills = entry.get("skills", {}) if isinstance(entry, dict) else {}
        if not isinstance(prev_skills, dict):
            prev_skills = {}
        target = root / target_rel

        for name, src in canonical.items():
            dest = target / name
            if not dest.exists() and not dest.is_symlink():
                continue
            expected = digest_tree(src)
            current = digest_tree(dest)
            old_digest = prev_skills.get(name)
            if old_digest is None:
                if current != expected:
                    issues.append(f"foreign skill conflicts with canonical name: {dest}")
            elif current not in {old_digest, expected} and not force:
                issues.append(f"managed copy changed locally: {dest}")

        for name, old_digest in prev_skills.items():
            if name in canonical:
                continue
            dest = target / name
            if (dest.exists() or dest.is_symlink()) and digest_tree(dest) != old_digest and not force:
                issues.append(f"stale managed skill modified locally; not removing: {dest}")
    return issues


def sync_target(root: Path, target_rel: Path, canonical: dict[str, Path], previous: dict,
                mode: str, force: bool, check: bool) -> tuple[dict, list[str]]:
    target = root / target_rel
    target.mkdir(parents=True, exist_ok=True)
    prev_skills = (previous or {}).get("skills", {})
    issues: list[str] = []
    current_manifest: dict[str, str] = {}

    # Remove only previously-managed entries that no longer exist canonically.
    for name, old_digest in sorted(prev_skills.items()):
        if name in canonical:
            continue
        dest = target / name
        if not dest.exists() and not dest.is_symlink():
            continue
        now = digest_tree(dest)
        if now != old_digest and not force:
            issues.append(f"stale managed skill modified locally; not removing: {dest}")
            current_manifest[name] = old_digest
            continue
        if check:
            issues.append(f"stale managed skill present: {dest}")
        else:
            safe_remove(dest)
            print(f"removed  {target_rel / name}")

    for name, src in canonical.items():
        dest = target / name
        expected = digest_tree(src)
        old_digest = prev_skills.get(name)
        if check:
            if not dest.exists() and not dest.is_symlink():
                issues.append(f"missing propagated skill: {dest}")
            elif old_digest is None:
                # Same-name foreign entry is a conflict even if content happens to match.
                issues.append(f"foreign skill conflicts with canonical name: {dest}")
            elif digest_tree(dest) != expected:
                issues.append(f"drift: {dest}")
            current_manifest[name] = expected
            continue

        if (dest.exists() or dest.is_symlink()) and digest_tree(dest) == expected:
            current_manifest[name] = expected
            label = "current" if old_digest is not None else "adopted"
            print(f"{label:<8} {target_rel / name}")
            continue
        ensure_replaceable(dest, old_digest, force)
        safe_remove(dest)
        if mode == "link":
            rel = os.path.relpath(src, dest.parent)
            dest.symlink_to(rel, target_is_directory=True)
            print(f"linked   {target_rel / name} -> {rel}")
        else:
            shutil.copytree(src, dest)
            print(f"copied   {target_rel / name}")
        current_manifest[name] = expected

    return {"mode": mode, "skills": current_manifest}, issues


def main() -> int:
    ap = argparse.ArgumentParser(description="Safely propagate canonical LeanLoop skills")
    ap.add_argument("--link", action="store_true", help="create one symlink per managed skill")
    ap.add_argument("--check", action="store_true", help="report drift without changing files")
    ap.add_argument("--force-managed", action="store_true",
                    help="overwrite only entries already recorded as LeanLoop-managed")
    ap.add_argument("--skills", metavar="NAMES",
                    help="comma-separated LeanLoop-owned skill names to propagate")
    args = ap.parse_args()

    root = find_repo_root(Path(__file__).resolve())
    src = root / ".agents" / "skills"
    if not src.is_dir():
        print(f"error: canonical skill directory not found: {src}", file=sys.stderr)
        return 2
    all_canonical = skill_dirs(src)
    if not all_canonical:
        print("error: no canonical skills found", file=sys.stderr)
        return 2

    requested = parse_skill_names(args.skills)
    if requested is None:
        requested = installed_skill_names(root)
    canonical, missing = scoped_skills(all_canonical, requested)
    if missing:
        print("error: requested LeanLoop skills are missing from .agents/skills: " + ", ".join(missing), file=sys.stderr)
        return 2
    if requested is not None and not canonical:
        print("error: installed/requested LeanLoop skill scope is empty", file=sys.stderr)
        return 2

    manifest_path = root / MANIFEST
    manifest = load_json(manifest_path, {"schema_version": 1, "targets": {}})
    previous_targets = manifest.get("targets", {}) if isinstance(manifest, dict) else {}
    new_targets: dict[str, dict] = {}
    all_issues: list[str] = []
    mode = "link" if args.link else "copy"

    if not args.check:
        preflight_issues = sync_preflight(root, canonical, previous_targets, args.force_managed)
        if preflight_issues:
            for issue in preflight_issues:
                print(f"FAIL: {issue}", file=sys.stderr)
            print("FAIL: synchronization aborted before changing any propagation target", file=sys.stderr)
            return 1

    for target_rel in TARGETS:
        key = target_rel.as_posix()
        entry, issues = sync_target(
            root, target_rel, canonical, previous_targets.get(key, {}), mode,
            args.force_managed, args.check,
        )
        new_targets[key] = entry
        all_issues.extend(issues)

    if args.check:
        if all_issues:
            for issue in all_issues:
                print(f"FAIL: {issue}")
            return 1
        print(f"OK: {len(canonical)} canonical skills are synchronized; foreign skills untouched")
        return 0

    write_json_atomic(manifest_path, {"schema_version": 1, "targets": new_targets})
    if all_issues:
        for issue in all_issues:
            print(f"WARN: {issue}", file=sys.stderr)
    print(f"done: {len(canonical)} skills synchronized non-destructively ({mode})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
