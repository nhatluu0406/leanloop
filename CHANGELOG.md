# Changelog

All notable LeanLoop changes are documented here. LeanLoop follows Semantic Versioning once `v1.0.0` is stable.

## [Unreleased]

### Changed

- Nothing yet.

## [1.0.0-rc.1] - 2026-08-08

### Added

- Conflict-aware install, upgrade, tier expansion, and uninstall lifecycle with managed-file provenance.
- Cross-platform CI coverage for Python 3.10+ on Linux, Windows, and macOS.
- Stable `validate` aggregate CI check for branch protection.
- Release/version contract, release checklist, and GitHub release notes template.
- Installed-project version diagnostics via `doctor.py --version`.

### Changed

- Claude hook installation now chooses an available Python command instead of assuming `python3` exists everywhere.
- README now exposes CI/release/license/Python badges and an explicit compatibility matrix.
- GitHub Actions remain pinned to immutable commit SHAs.

### Safety

- Upgrade refuses locally modified LeanLoop-managed files instead of overwriting them.
- Uninstall removes only verified LeanLoop-owned files, generated skill copies, managed adapter/ignore blocks, and exact hook commands.
- Foreign skills, unrelated Claude settings, project docs, task state, and user-owned Git changes are preserved.

[Unreleased]: https://github.com/nhatluu0406/leanloop/compare/v1.0.0-rc.1...HEAD
[1.0.0-rc.1]: https://github.com/nhatluu0406/leanloop/releases/tag/v1.0.0-rc.1
