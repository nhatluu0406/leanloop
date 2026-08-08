<div align="center">

# 🔁 LeanLoop

### Spend tokens on decisions — not rediscovery, retries, or accidental rework.

A portable engineering discipline for **Claude Code, OpenAI Codex, and Cursor** that keeps agent context lean while adding planning, verification, Git isolation, durable state, and measurable cost controls.

![Claude Code](https://img.shields.io/badge/Claude_Code-supported-D97757?style=flat-square)
![Codex](https://img.shields.io/badge/OpenAI_Codex-supported-111111?style=flat-square&logo=openai&logoColor=white)
![Cursor](https://img.shields.io/badge/Cursor-supported-111111?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![Dependencies](https://img.shields.io/badge/core_dependencies-0-2ea44f?style=flat-square)
![CI](https://img.shields.io/badge/CI-GitHub_Actions-2088FF?style=flat-square&logo=githubactions&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)

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

### Use LeanLoop as the project/template itself

```bash
# After cloning/forking the repository
python3 scripts/leanloop/sync.py
python3 scripts/leanloop/repomap.py .
python3 scripts/leanloop/doctor.py
```

Create project state from the templates when needed:

```bash
cp templates/STACK.md STACK.md
cp templates/PLAN.md PLAN.md
python3 scripts/leanloop/task.py start my-feature
```

### Install into an existing repository

LeanLoop has a conflict-aware installer. It does **not** use `cp -r` over your repository.

```bash
# Tier 0 + Tier 1: recommended default for normal code projects
python3 scripts/leanloop/install.py /path/to/project --tiers 0,1

# Install every built-in skill
python3 scripts/leanloop/install.py /path/to/project --all
```

The installer:

- preserves existing `AGENTS.md` / `CLAUDE.md` and adds a managed LeanLoop block;
- keeps foreign Claude/Cursor skills untouched;
- installs core Python utilities under the namespaced `scripts/leanloop/` path;
- stores support docs/templates under `.leanloop/kit/`;
- merges Claude hooks without replacing unrelated settings;
- installs only the requested skill tiers.

After installing:

```bash
cd /path/to/project
python3 scripts/leanloop/doctor.py
```

---

## Safe parallel implementation

Parallel workers must never share one Git index, even if the planned source files are different.

```bash
# From the orchestrator tree
python3 scripts/leanloop/worktree.py create plan-2-auth
python3 scripts/leanloop/worktree.py create plan-3-ui
```

Each worker receives its own worktree/branch, implements one reviewed PLAN step, verifies it, and commits only explicit paths. The orchestrator reviews and integrates approved commits, normally with `git cherry-pick`.

Before any implementation:

```bash
python3 scripts/leanloop/git_guard.py
```

A dirty main worktree is treated as user state to preserve — not something an agent may reset, stash, or absorb.

Safe commit:

```bash
python3 scripts/leanloop/safe_commit.py \
  -m "plan#2: add refresh-token rotation" \
  src/auth/service.ts tests/auth/service.test.ts
```

`git add .` and wildcard staging are deliberately outside the workflow.

---

## Skill system

`.agents/skills/` is the canonical source. Claude and Cursor receive managed copies via:

```bash
python3 scripts/leanloop/sync.py
python3 scripts/leanloop/sync.py --check   # CI/drift check
python3 scripts/leanloop/sync.py --link    # per-skill symlinks, foreign skills preserved
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
python3 scripts/leanloop/task.py start checkout-retry
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
python3 scripts/leanloop/repomap.py .
```

`state/REPOMAP.md` contains a bounded tree, line counts, key symbols, and a small number of likely local dependency hints. Unlike the original implementation, it includes important hidden infrastructure such as `.agents/`, `.claude/`, `.cursor/`, `.github/`, and `.leanloop/` while excluding Git/cache/vendor noise.

The map is a **locator**, not semantic truth. Exact behavior still comes from contracts/source via targeted reads.

---

## Verification and CI

Local health check:

```bash
python3 scripts/leanloop/doctor.py --strict
python3 -m unittest discover -s tests -v
```

GitHub Actions validates:

- Python syntax;
- shell syntax;
- unit/integration tests;
- propagated-skill drift;
- adapter/skill/tool-lock invariants.

The CI workflow uses a full commit SHA for its checkout action rather than a floating tag.

---

## Token / usage telemetry

External tooling is optional and pinned in [`TOOLS.lock`](TOOLS.lock).

```bash
python3 scripts/leanloop/token_report.py daily all
python3 scripts/leanloop/token_report.py daily claude
python3 scripts/leanloop/token_report.py daily codex
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
.leanloop/managed.json          sync ownership manifest
scripts/leanloop/               stdlib-only core utilities
skills.json                     single tier manifest
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

## Compatibility notes

- **Claude Code:** deepest integration — native skills plus hooks and predefined subagents.
- **Codex:** canonical `.agents/skills/` + `AGENTS.md`; workflow safety is disk/Git based rather than Claude-hook dependent.
- **Cursor:** `.cursor/rules/leanloop.mdc` + propagated skills; same durable state and Git isolation discipline.
- **Core:** Python 3.10+ standard library. Bash is used only by optional convenience/tool-install wrappers.

Tool vendors evolve. Hooks intentionally fail open on unexpected Claude hook payloads so an API change degrades enforcement rather than breaking development; `doctor.py` and CI should catch repository-side drift.

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

