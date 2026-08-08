# Releasing LeanLoop

LeanLoop uses Semantic Versioning for its public workflow and on-disk contracts.

## Compatibility contract

A breaking change to any of the following requires a new major version after `v1.0.0`:

- `skills.json` schema or skill discovery layout;
- `.leanloop/install.json` or `.leanloop/managed.json` compatibility;
- adapter managed markers;
- task-state paths used by CHECKPOINT/HANDOFF workflows;
- install/upgrade/uninstall safety semantics.

Adding backward-compatible skills/features is normally minor. Backward-compatible fixes are patch releases.

## Release checklist

1. Update `VERSION` and `CHANGELOG.md`.
2. Run `python scripts/leanloop/sync.py` if canonical skills changed.
3. Run `python scripts/leanloop/doctor.py --strict`.
4. Run `python -m unittest discover -s tests -v`.
5. Run `python -m compileall -q scripts .claude/hooks tests`.
6. Run shell syntax checks on a POSIX environment.
7. Merge only after the Linux/Windows/macOS CI matrix and aggregate `validate` check are green.
8. For a major/stable release, dogfood the release candidate on at least two real repositories.
9. Tag the exact green commit (`vX.Y.Z` or prerelease tag).
10. Create the GitHub Release from `RELEASE_NOTES.md`; attach checksumed archives when publishing custom assets.

Do not move an existing release tag. Publish a new version instead.
