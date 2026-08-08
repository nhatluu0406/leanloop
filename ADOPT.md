# ADOPT — bringing external skills/tools in safely

LeanLoop's default answer to a new integration is **not** "install it". Add external material only when it solves a repeated problem and survives a security/context-cost review.

## Four-question filter

1. **Trigger precision:** is the skill/tool invoked for a concrete recurring task, rather than generic advice the model already knows?
2. **Net value:** does it improve success/rework enough to justify description/tool-schema/runtime overhead?
3. **Supply chain:** have scripts, permissions, network behavior, and credential scope been audited? Pin an exact package version/release/commit before execution.
4. **Freshness/ownership:** who updates or removes it when upstream changes?

## Skills

- Canonical location: `.agents/skills/<name>/`.
- Add only the selected skill, never an entire catalog by default.
- Update `skills.json` only if it should participate in LeanLoop tier installation.
- Run `python3 scripts/leanloop/sync.py`; it updates only LeanLoop-managed copies and never deletes foreign Claude/Cursor skills.
- Run `python3 scripts/leanloop/doctor.py` to inspect skill-description budget and drift.

Third-party skill installers may be used only after you have reviewed what they will write. Prefer downloading/reviewing first over piping remote content directly into the repo.

## External executables

- Record executable dependencies in `TOOLS.md` and exact versions in `TOOLS.lock`.
- Normal setup never uses `@latest` and never auto-clones optional GitHub repos.
- Upgrades are deliberate: review upstream change notes/source, edit `TOOLS.lock`, run verification, then commit the lock change.

## Adoption experiment

For a meaningful addition, compare a representative task before/after: outcome quality, retries/rework, and usage/cost where available. Remove an addition that does not produce a repeatable benefit.

## Adoption log

<!-- date | skill/tool | pinned version/commit | reason | measured effect | owner -->
