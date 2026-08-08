# LeanLoop — Claude Code adapter
<!-- Keep this file tiny: it is loaded into every Claude Code session/subagent. -->

Philosophy: **spend tokens on decisions, not rediscovery or rework.** Durable state lives on disk; the transcript is disposable.

## Start
1. Read `STACK.md` / `PLAN.md` when present, plus the active task's HANDOFF/CHECKPOINT (`python3 scripts/leanloop/task.py path`). Create missing planning files from templates before non-trivial work.
2. Navigate from `state/REPOMAP.md`; regenerate with `python3 scripts/leanloop/repomap.py .` only when missing/stale.
3. Before implementation, run `python3 scripts/leanloop/git_guard.py`. Dirty main tree → use `scripts/leanloop/worktree.py create <slug>` instead of mixing changes.

## Work
- Non-trivial code requires PLAN.md with machine-checkable verifiers.
- Use scout for bulky read-only investigation; implementer for low/medium-risk reviewed steps; implementer-strong for security/data/concurrency/migration/architecture-sensitive steps; reviewer for judgment.
- Parallel implementers **must** use separate Git worktrees/branches. Integrate reviewed worker commits from the orchestrator tree; never share a Git index.
- Contracts precede cross-boundary implementations. DB changes use migrations. UI follows project design tokens.
- Debug same error at most 3 times; then persist a stuck report and escalate.
- Before "done": formatter/lint → typecheck → named verifier → impacted tests → domain gates → diff review.
- Commit only explicit paths via `scripts/leanloop/safe_commit.py`; never `git add .`.
- After each green plan step, tick PLAN.md and refresh task state. End a session with HANDOFF.

## Skills
Canonical skills live in `.agents/skills/`; Claude copies live in `.claude/skills/`. Native skill discovery supplies descriptions, so this adapter intentionally does **not** duplicate the skill index. Edit canonical skills only, then run `python3 scripts/leanloop/sync.py`.

Lifecycle: `PLAYBOOK.md`.
