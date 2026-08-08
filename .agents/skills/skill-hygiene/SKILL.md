---
name: skill-hygiene
description: Keep the skill system itself small, non-destructive, and measurable. Use when adding/removing/editing skills, changing tier membership, or syncing tool-specific copies.
---

# Skill Hygiene

The system that saves context must not become a standing context tax.

## Budgets

- Description: concrete triggers, normally ≤2 sentences.
- Body: ≤80 lines target; move detail to references/scripts when useful only on demand.
- Whole installed set: keep description payload within an explicit project budget; `scripts/leanloop/doctor.py` reports the rough size.

## Canonical source and tiers

- Canonical skills: `.agents/skills/<name>/`.
- Tier membership exists once in root `skills.json`.
- Tool copies are generated; never edit `.claude/skills/` or `.cursor/skills/` directly.
- Install only tiers/skills the project needs. A dormant description still occupies discovery context.

## Safe synchronization

`python3 scripts/leanloop/sync.py` synchronizes one skill directory at a time. It records only LeanLoop-managed entries in `.leanloop/managed.json`, never deletes foreign skills, and refuses to overwrite a locally modified managed copy unless `--force-managed` is deliberate. `--check` is CI-safe drift detection; `--link` creates per-skill symlinks without replacing the destination directory.

## Bar for a new skill

Add a skill only when the rule repeatedly changes outcomes, no existing skill owns it, and it encodes project/workflow judgment rather than generic programming knowledge. Prefer extending an owner skill over creating a near-duplicate.

If a rule can be enforced cheaply by tests, linters, permissions, hooks, or scripts, enforce it there and shorten the prose.
