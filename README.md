<div align="center">

# 🔁 LeanLoop

### Spend tokens on decisions — not rediscovery, retries, or accidental rework.

A portable engineering discipline for **Claude Code, OpenAI Codex, and Cursor** that keeps agent context lean while adding planning, verification, Git isolation, durable state, and measurable cost controls.

[![CI](https://github.com/nhatluu0406/leanloop/actions/workflows/ci.yml/badge.svg)](https://github.com/nhatluu0406/leanloop/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/nhatluu0406/leanloop?include_prereleases&sort=semver)](https://github.com/nhatluu0406/leanloop/releases)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/github/license/nhatluu0406/leanloop)](LICENSE)

![Claude Code](https://img.shields.io/badge/Claude_Code-supported-D97757?style=flat-square)
![OpenAI Codex](https://img.shields.io/badge/OpenAI_Codex-supported-111111?style=flat-square&logo=openai&logoColor=white)
![Cursor](https://img.shields.io/badge/Cursor-supported-111111?style=flat-square)
![Core dependencies](https://img.shields.io/badge/core_dependencies-0-2ea44f?style=flat-square)

**21 progressive-disclosure skills · 4 Claude hooks · 4 Claude agents · non-destructive sync · isolated parallel worktrees · explicit-path commits · pinned optional tooling · stdlib-only core**

</div>

---

## Why LeanLoop?

Coding agents become expensive when they repeatedly rediscover the repository, load unnecessary tool/skill context, retry the same failure, or generate parallel changes in one shared working tree. LeanLoop turns those failure modes into a small set of durable artifacts and mechanical guardrails.

The goal is **not minimum tokens at any cost**. The goal is the lowest **cost per accepted, maintainable change**.

| Problem | LeanLoop response |
|---|---|
| Re-reading the same codebase | Compact `REPOMAP.md` + grep/ranged-read discipline |
| Losing decisions after compaction/session changes | Task-scoped CHECKPOINT + HANDOFF on disk |
| Coding before requirements are clear | Verifier-first `PLAN.md` with explicit non-goals |
| Cheap model stuck on a hard reasoning problem | Risk-adaptive model routing |
| Parallel agents corrupting/mixing Git state | One Git worktree + branch per implementation worker |
| `git add .` swallowing unrelated work | Explicit-path `safe_commit.py` |
| Subagent context flooding back | ≤300-token report contract |
| Claude/Cursor skill copies drifting | Canonical `.agents/skills/` + non-destructive managed sync |
| Existing project skills being deleted by sync | Foreign skills are never removed or overwritten |
| Ambient third-party updates | Versions pinned in `TOOLS.lock`; no normal-path `@latest` |
| Optimization claims without evidence | Local telemetry + before/after task comparisons |

## Core idea

```text
Intent / issue
    ↓
STACK.md + PLAN.md + contracts
    ↓
Risk + dependency decision
    ├── small deterministic work → inline
    ├── bulky investigation     → read-only scout
    ├── normal implementation   → standard implementer
    └── high-risk reasoning     → strong implementer
                                   ↓
                 parallel code? separate Git worktrees
                                   ↓
                  verification → reviewer → safe commit
                                   ↓
                       CHECKPOINT / HANDOFF
                                   ↓
                         usage + quality retro
```

The transcript can disappear; the project still knows what is true.

---

## Quick start

> Current release candidate: **v1.0.0-rc.1**. The core requires Python 3.10+. Commands below use `python`; use your local Python 3 launcher if it has another name.

### Use LeanLoop as the project/template itself

```bash
# After cloning/forking the repository
python scripts/leanloop/sync.py
python scripts/leanloop/repomap.py .
python scripts/leanloop/doctor.py --strict
```

Create project state from the templates when needed:

```bash
cp templates/STACK.md STACK.md
cp templates/PLAN.md PLAN.md
python scripts/leanloop/task.py start my-feature
```

### Install into an existing repository

LeanLoop has a conflict-aware installer. It does **not** bulk-copy over your repository.

```bash
# Tier 0 + Tier 1: recommended default for normal code projects
python scripts/leanloop/install.py /path/to/project --tiers 0,1

# Install every built-in skill
python scripts/leanloop/install.py /path/to/project --all
```

The installer:

- preserves existing `AGENTS.md` / `CLAUDE.md` and adds a managed LeanLoop block;
- keeps foreign Claude/Cursor skills untouched;
- installs core Python utilities under the namespaced `scripts/leanloop/` path;
- stores support docs/templates under `.leanloop/kit/`;
- merges Claude hooks without replacing unrelated settings;
- records version, tiers, interpreter choice, and managed-file SHA-256 provenance in `.leanloop/install.json`;
- installs only the requested skill tiers.

After installing:

```bash
cd /path/to/project
python scripts/leanloop/doctor.py --strict
```

### Upgrade, expand tiers, or uninstall

Run the **new release's** `install.py` against the project you want to upgrade:

```bash
# Keep currently installed tiers and upgrade LeanLoop-owned files
python scripts/leanloop/install.py /path/to/project --upgrade

# Keep current tiers and add Tier 2
python scripts/leanloop/install.py /path/to/project --upgrade --add-tiers 2

# Replace the tier selection explicitly
python scripts/leanloop/install.py /path/to/project --upgrade --tiers 0,1,3

# Remove only verified LeanLoop-owned content
python scripts/leanloop/install.py /path/to/project --uninstall
```

Upgrade/uninstall are intentionally conservative. If a tracked LeanLoop-managed file or propagated skill was changed locally, LeanLoop refuses the operation before mutating lifecycle state. Foreign skills, unrelated Claude settings, task state, and user Git changes remain outside LeanLoop ownership.

Version check:

```bash
python scripts/leanloop/doctor.py --version
```

---

## Safe parallel implementation

Parallel workers must never share one Git index, even if the planned source files are different.

```bash
# From the orchestrator tree
python scripts/leanloop/worktree.py create plan-2-auth
python scripts/leanloop/worktree.py create plan-3-ui
```

Each worker receives its own worktree/branch, implements one reviewed PLAN step, verifies it, and commits only explicit paths. The orchestrator reviews and integrates approved commits, normally with `git cherry-pick`.

Before any implementation:

```bash
python scripts/leanloop/git_guard.py
```

A dirty main worktree is treated as user state to preserve — not something an agent may reset, stash, or absorb.

Safe commit:

```bash
python scripts/leanloop/safe_commit.py \
  -m "plan#2: add refresh-token rotation" \
  src/auth/service.ts tests/auth/service.test.ts
```

`git add .` and wildcard staging are deliberately outside the workflow.

---

## Skill system

`.agents/skills/` is the canonical source. Claude and Cursor receive managed copies via:

```bash
python scripts/leanloop/sync.py
python scripts/leanloop/sync.py --check   # CI/drift check
python scripts/leanloop/sync.py --link    # per-skill symlinks, foreign skills preserved
```

Sync tracks only LeanLoop-owned entries in `.leanloop/managed.json`. A foreign skill is never deleted. A locally modified managed copy is refused rather than silently overwritten.

Tier membership lives once in [`skills.json`](skills.json):

| Tier | Purpose | Skills |
|---|---|---|
| **0 — Core** | Always-use workflow discipline | `concise-output`, `spec-and-plan`, `report-contract`, `tool-economics` |
| **1 — Code** | Normal software projects | `codebase-map`, `read-budget`, `delegation-protocol`, `verification-gate`, `loop-discipline`, `context-lifecycle` |
| **2 — Situational** | Larger/longer-lived workflows | `wiki-protocol`, `orchestration-topology`, `docs-minimalism`, `token-telemetry`, `skill-hygiene` |
| **3 — Stack** | Architecture/UI/API/DB concerns | `stack-profile`, `frontend-design`, `design-review`, `api-contract`, `database-schema`, `module-boundaries` |

Adapters intentionally **do not repeat the 21 descriptions**. Native skill discovery owns that context once.

---

## Risk-adaptive model routing

LeanLoop avoids a rigid “one role = one model forever” policy.

| Risk | Typical work | Routing principle |
|---|---|---|
| **LOW** | Mechanical edit, strong verifier, tiny blast radius | Cheapest capable model |
| **MEDIUM** | Normal feature/refactor with clear contracts/tests | Standard implementation model |
| **HIGH** | Security, auth, data loss, migrations, concurrency, public contracts, architecture-sensitive refactors, ambiguous failures | Strongest available reasoning |

Claude Code includes:

- `scout` — mechanically read-only (`Read`, `Grep`, `Glob`; no Bash/write tool);
- `implementer` — normal reviewed PLAN steps;
- `implementer-strong` — high-risk implementation;
- `reviewer` — mechanically read-only quality judgment.

Codex and Cursor follow the same risk/isolation rules through their adapters and native skills.

---

## Durable task state

Start a task:

```bash
python scripts/leanloop/task.py start checkout-retry
```

LeanLoop uses:

```text
state/
├── CURRENT_TASK                 # local-only selector
└── tasks/
    └── checkout-retry/
        ├── CHECKPOINT.md        # ephemeral recovery state
        ├── HANDOFF.md           # durable session handoff
        └── reports/             # stuck/deep-detail reports
```

This prevents unrelated tasks from overwriting a single global checkpoint. Legacy `state/HANDOFF.md` / `state/CHECKPOINT.md` still work when no active task is selected.

Claude Code hooks automatically assist pre-compaction checkpointing, session reload, bounded large-file reads, and context/cost status display. Codex/Cursor rely on the same durable-file discipline without pretending they have identical hook APIs.

---

## Repository map

```bash
python scripts/leanloop/repomap.py .
```

`state/REPOMAP.md` contains a bounded tree, line counts, key symbols, and a small number of likely local dependency hints. Unlike the original implementation, it includes important hidden infrastructure such as `.agents/`, `.claude/`, `.cursor/`, `.github/`, and `.leanloop/` while excluding Git/cache/vendor noise.

The map is a **locator**, not semantic truth. Exact behavior still comes from contracts/source via targeted reads.

---

## Verification and CI

Local health check:

```bash
python scripts/leanloop/doctor.py --strict
python -m unittest discover -s tests -v
```

GitHub Actions validates:

- Python 3.10 minimum support on Linux;
- current stable Python on Linux, Windows, and macOS;
- Python syntax and unit/integration tests;
- propagated-skill drift;
- adapter/skill/tool-lock/version invariants;
- POSIX shell wrapper syntax.

A final job named **`validate`** aggregates the matrix so branch protection can require one stable check name. GitHub Actions dependencies are pinned to full commit SHAs rather than floating tags.

---

## Token / usage telemetry

External tooling is optional and pinned in [`TOOLS.lock`](TOOLS.lock).

```bash
python scripts/leanloop/token_report.py daily all
python scripts/leanloop/token_report.py daily claude
python scripts/leanloop/token_report.py daily codex
```

LeanLoop does not claim a universal “X% token saving.” Different models, caches, tool schemas, and task shapes behave differently. Benchmark representative work before/after a workflow change and include **quality + rework**, not just token count.

Optional tools and their policy live in [`TOOLS.md`](TOOLS.md). Normal install/report paths do not use `@latest`, and optional third-party GitHub repos are never auto-cloned.

---

## Project structure

```text
.agents/skills/                 canonical skill source
.claude/
├── agents/                     scout · implementer · implementer-strong · reviewer
├── hooks/                      checkpoint · session reload · read guard · statusline
└── skills/                     managed generated copies
.cursor/
├── rules/leanloop.mdc          always-on thin adapter
└── skills/                     managed generated copies
.github/workflows/ci.yml        self-validation
.leanloop/managed.json          propagated-skill ownership manifest
.leanloop/install.json          installed-project version/provenance manifest
scripts/leanloop/               stdlib-only core utilities
skills.json                     single tier manifest
VERSION                         framework/release version
CHANGELOG.md                    consumer-visible release history
docs/RELEASING.md               maintainer release contract/checklist
TOOLS.lock                      pinned external versions
templates/                      BRIEF · STACK · PLAN · CHECKPOINT · HANDOFF · wiki instructions
state/                          generated durable project/task memory
AGENTS.md                       Codex adapter
CLAUDE.md                       Claude Code adapter
PLAYBOOK.md                     idea → plan → implement → verify → handoff
ADOPT.md                        external skill/tool adoption policy
```

---

## Design principles

1. **Crystallize expensive knowledge to disk once.**
2. **Advice for judgment; machines for compliance.**
3. **Strong models decide/risk-handle; cheaper models execute deterministic work.**
4. **Parallelism requires isolation, not merely different filenames.**
5. **Foreign project state is sacred.** Sync/install/commit tooling defaults to refusal rather than destructive guessing.
6. **Measure cost per accepted change.** A cheap wrong implementation is expensive.
7. **Progressive disclosure beats giant always-on instruction files.**

See [`PLAYBOOK.md`](PLAYBOOK.md) for the complete operating lifecycle.

---

## Compatibility

| Environment | v1 release-candidate status | Integration |
|---|---|---|
| Linux | Tested in CI | Core + all repository tests |
| Windows | Tested in CI | Core + all repository tests |
| macOS | Tested in CI | Core + all repository tests |
| Claude Code | Supported | Native skills, hooks, predefined subagents |
| OpenAI Codex | Supported | `.agents/skills/` + `AGENTS.md` + disk/Git safety |
| Cursor | Supported | `.cursor/rules/leanloop.mdc` + propagated skills |

**Core requirement:** Python 3.10+ standard library only. Bash is used only by optional POSIX convenience/tool-install wrappers; the core Python lifecycle and tests are cross-platform. The installer auto-selects an available Python hook command instead of hard-coding `python3`.

Tool vendors evolve. Hooks intentionally fail open on unexpected Claude hook payloads so an API change degrades enforcement rather than breaking development; `doctor.py` and CI catch repository-side drift.

## Versioning and releases

LeanLoop uses Semantic Versioning for stable public contracts. See [`CHANGELOG.md`](CHANGELOG.md) for consumer-visible changes and [`docs/RELEASING.md`](docs/RELEASING.md) for the release checklist and compatibility contract.

Before stable `v1.0.0`, `v1.0.0-rc.1` should be dogfooded on at least two real repositories. Only release-blocking fixes should land between the final RC and stable v1.

---

## GitHub topics

Recommended repository topics:

`ai-agents` · `agentic-engineering` · `claude-code` · `codex` · `cursor` · `developer-tools` · `llm` · `multi-agent` · `prompt-engineering` · `token-optimization`

---

## Contributing

Focused improvements are welcome. Please read [`CONTRIBUTING.md`](CONTRIBUTING.md) and keep changes measurable, scoped, and backward-safe.

For security issues, see [`SECURITY.md`](SECURITY.md).

## License

MIT — see [`LICENSE`](LICENSE).

