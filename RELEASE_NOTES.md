# LeanLoop v1.0.0-rc.1

LeanLoop's first release candidate hardens the project from a good agent-engineering kit into a versioned, upgrade-safe workflow layer for Claude Code, OpenAI Codex, and Cursor.

## Highlights

- Safe install, upgrade, tier expansion, and uninstall lifecycle.
- Provenance hashes prevent upgrades from overwriting locally modified LeanLoop-managed files.
- Foreign project skills/configuration and user state remain untouched.
- Cross-platform Linux, Windows, and macOS CI while retaining Python 3.10 minimum coverage.
- Stable aggregate `validate` status check for branch protection.
- Version/changelog/release contract for the path to stable `v1.0.0`.

## Recommended RC validation

Dogfood `v1.0.0-rc.1` on at least two real repositories:

1. install Tier 0+1;
2. run `doctor --strict`;
3. perform one normal feature and one parallel worktree task;
4. upgrade the same installation from a copied RC source;
5. verify a deliberately modified managed file blocks upgrade;
6. verify uninstall preserves a foreign skill, unrelated adapter text, task state, and user Git changes.

Only release-blocking fixes should be added between this RC and `v1.0.0`.
