#!/usr/bin/env bash
# Install/verify optional external tools at versions pinned in TOOLS.lock.
# Usage: bash scripts/install_tools.sh [core|all]
set -euo pipefail
cd "$(dirname "$0")/.."
SCOPE="${1:-core}"
# shellcheck disable=SC1091
source TOOLS.lock
ok(){ printf '✓ %s\n' "$1"; }
skip(){ printf '– %s\n' "$1"; }
fail(){ printf '✗ %s\n' "$1" >&2; }

command -v node >/dev/null 2>&1 || { fail "Node.js is required for npm/npx tools"; exit 1; }

if npx -y "ccusage@${CCUSAGE_VERSION}" --version >/dev/null 2>&1; then
  ok "ccusage ${CCUSAGE_VERSION} (pinned, on-demand)"
else
  fail "ccusage ${CCUSAGE_VERSION} verification failed"
  exit 1
fi

FILECOUNT=$(git ls-files 2>/dev/null | wc -l | tr -d ' ' || printf '0')
if [ "${FILECOUNT:-0}" -gt 300 ] || [ "$SCOPE" = "all" ]; then
  npm install -g "openwiki@${OPENWIKI_VERSION}" >/dev/null
  ok "openwiki ${OPENWIKI_VERSION}"
else
  skip "openwiki (repo has ${FILECOUNT:-0} tracked files; install with 'all' if desired)"
fi

if [ "$SCOPE" = "all" ]; then
  if npx -y "ui-ux-pro-max-cli@${UI_UX_PRO_MAX_VERSION}" --help >/dev/null 2>&1; then
    ok "ui-ux-pro-max-cli ${UI_UX_PRO_MAX_VERSION} available; run init manually for the assistants you actually use"
  else
    skip "ui-ux-pro-max-cli verification failed (optional)"
  fi

  if command -v uv >/dev/null 2>&1; then
    uv tool install "claude-monitor==${CLAUDE_MONITOR_VERSION}" >/dev/null
    ok "claude-monitor ${CLAUDE_MONITOR_VERSION} (uv)"
  elif command -v pipx >/dev/null 2>&1; then
    pipx install "claude-monitor==${CLAUDE_MONITOR_VERSION}" >/dev/null
    ok "claude-monitor ${CLAUDE_MONITOR_VERSION} (pipx)"
  else
    skip "claude-monitor ${CLAUDE_MONITOR_VERSION}: install uv or pipx first"
  fi

  skip "code-executor-mcp is intentionally NOT auto-cloned; audit and pin an exact commit before adoption"
  skip "dependency-cruiser belongs in the target project's devDependencies; pinned reference=${DEPENDENCY_CRUISER_VERSION}"
fi

printf 'done. Versions: TOOLS.lock; rationale: TOOLS.md\n'
