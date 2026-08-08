# Contributing to LeanLoop

LeanLoop changes should improve **cost per accepted change** without weakening correctness, safety, or maintainability.

## Before opening a change

1. Keep the change scoped to one problem.
2. Prefer a mechanical guard/test over adding always-on prose.
3. If changing a skill, edit `.agents/skills/` only and run `python scripts/leanloop/sync.py`.
4. If adding a skill, update `skills.json` and justify why an existing owner skill cannot absorb the rule.
5. If changing an external executable dependency, pin the exact version in `TOOLS.lock` and update `TOOLS.md`.

## Validate

```bash
python scripts/leanloop/sync.py --check
python scripts/leanloop/doctor.py --strict
python -m unittest discover -s tests -v
python -m compileall -q scripts .claude/hooks tests
bash -n scripts/sync.sh scripts/install_tools.sh scripts/token_report.sh
```

For workflow/token optimizations, include a reproducible before/after task shape when making quantitative claims. Do not generalize one local measurement into a universal savings number.

## Release-sensitive changes

Changes to install lifecycle, manifest schemas, adapter markers, or task-state paths are public-contract changes after v1. Follow [`docs/RELEASING.md`](docs/RELEASING.md), update `CHANGELOG.md` when consumers are affected, and add upgrade/uninstall regression tests.

## Pull requests

- One logical change per PR.
- Explain the failure mode being removed and the verifier/test proving it.
- Avoid unrelated formatting or generated-file churn.
- Never include credentials, local transcripts, or private project state.
