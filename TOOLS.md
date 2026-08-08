# TOOLS — external tool policy

`TOOLS.lock` is the executable version lock. Normal LeanLoop scripts use pinned versions; upgrades are deliberate review events, not ambient `@latest` downloads.

| Tool | Purpose | Pinned key | Installation policy |
|---|---|---|---|
| ccusage | Local usage/cost reports for supported coding agents | `CCUSAGE_VERSION` | `npx` on demand at the locked version |
| OpenWiki | Optional large-repo agent wiki | `OPENWIKI_VERSION` | Install only when repo/question volume justifies it |
| Claude Code Usage Monitor | Optional live Claude usage monitor | `CLAUDE_MONITOR_VERSION` | `uv`/`pipx`, locked version |
| ui-ux-pro-max-cli | Optional design-system helper | `UI_UX_PRO_MAX_VERSION` | Verify pinned CLI; initialize explicitly per assistant |
| dependency-cruiser | JS/TS module-boundary gate | `DEPENDENCY_CRUISER_VERSION` | Prefer target-project devDependency, not global install |
| code-executor-mcp | Optional gateway pattern | n/a | **Never auto-cloned.** Audit source and pin an exact commit before adoption |

## Supply-chain rules

- No `@latest` in normal install/report paths.
- Review release notes and source/permissions before changing `TOOLS.lock`.
- Third-party repos are not vendored or executed automatically by LeanLoop.
- A tool absent from a project costs zero context and zero supply-chain surface; keep optional tools optional.
- If a skill requires a new external executable, add it here + `TOOLS.lock` before depending on it.
