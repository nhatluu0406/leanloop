---
name: wiki-protocol
description: Rules for using an agent wiki (OpenWiki) on large repos — when to consult it vs read source, and how to keep the wiki itself lean. Use on repos >~300 files, when a wiki/ or openwiki/ directory exists, or when setting one up.
---

# Wiki Protocol

A wiki amortizes exploration cost across sessions — but only if it stays short and current. A stale or bloated wiki is worse than none.

## When this applies

Repo >~300 files with recurring "how does subsystem X work" questions. Smaller repos: codebase-map alone is cheaper — do not set up a wiki.

## Consulting order

1. Architecture/flow/why questions → wiki first (`openwiki/` index).
2. Exact current behavior/signatures → source is truth; wiki only locates where to look.
3. Wiki contradicts code → **code wins**; note the drift for the next wiki update. Never implement against wiki claims without spot-checking the code.

## Setup (once — full steps: `references/setup.md` in this skill)

1. Install the version pinned in `TOOLS.lock` (`bash scripts/install_tools.sh all`), then initialize OpenWiki. Never use ambient `@latest` in the reproducible path.
2. `cp templates/WIKI-INSTRUCTIONS.md openwiki/INSTRUCTIONS.md` — enforces brevity: architecture, invariants, cross-module contracts only; no code walkthroughs, hard page budgets.
3. `cp .agents/skills/wiki-protocol/assets/openwiki-update.yml .github/workflows/` + add provider secret — updates run in **CI**, never in an interactive session; wiki maintenance must not burn session tokens.

## Budget rule

If a wiki page can't be read in ~1 minute, it's too long — that's an INSTRUCTIONS.md fix, not a reading strategy.
