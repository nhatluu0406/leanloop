# Security Policy

LeanLoop executes local Git/Python/shell commands and can integrate optional third-party developer tools, so supply-chain and repository-state safety are part of the project boundary.

## Reporting

For a public repository, report vulnerabilities through GitHub's **Private vulnerability reporting** feature when enabled. Do not publish exploit details in a public issue before maintainers have had a reasonable chance to investigate.

## Security expectations

- LeanLoop core uses the Python standard library only.
- Optional executable versions are pinned in `TOOLS.lock`; normal workflows avoid floating `@latest` execution.
- Optional third-party Git repositories are not auto-cloned/executed.
- Parallel implementation uses separate Git worktrees/branches.
- Safe commits stage explicit path allowlists and refuse unrelated staged files.
- Sync tracks LeanLoop-managed skill entries and does not delete foreign skills.
- Read-only Claude roles intentionally lack Bash/write tools.

Secrets, tokens, `.env` files, and user-owned uncommitted changes must never be collected into reports or commits unless the user explicitly makes them part of the task and the project policy allows it.
