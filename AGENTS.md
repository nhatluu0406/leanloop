# LeanLoop — Codex adapter

**Spend tokens on decisions, not repetition.** Treat chat context as disposable; crystallize decisions and task state to disk.

## Start every task
1. Read `STACK.md` / `PLAN.md` when present, plus active task state (`python3 scripts/leanloop/task.py path`). Create missing planning files from templates before non-trivial work.
2. Use `state/REPOMAP.md` before exploratory reads; grep first, then ranged reads.
3. Run `python3 scripts/leanloop/git_guard.py` before editing. If the main tree is dirty, isolate the task in a Git worktree rather than touching existing changes.

## Hard rules
- Non-trivial code requires PLAN.md with per-step machine verifiers and explicit non-goals.
- STACK.md is project law; contracts are the source of truth for boundaries; DB changes use migrations.
- Parallel implementation is allowed only across isolated Git worktrees/branches. Never let workers share a working tree or Git index.
- Use risk-adaptive model routing: cheap execution for deterministic low-risk work; strongest available reasoning for security, concurrency, data loss, migrations, architecture-sensitive refactors, or ambiguous failures.
- Same error 3 times → stop, persist a stuck report under active task state, escalate.
- Gate every step: formatter/lint → typecheck → step verifier → impacted tests → domain gates → `git diff --check` → diff review.
- Commit only explicit paths (`python3 scripts/leanloop/safe_commit.py ...`); `git add .`, wildcard staging, and mixed-scope commits are forbidden.
- After a green step: commit → tick PLAN.md → refresh task checkpoint/handoff. Session end: write HANDOFF.
- Replies and delegated reports stay compressed; details belong in files, not repeated chat.

## Skills
Codex discovers canonical skills from `.agents/skills/`. Do not duplicate their descriptions here. Tier membership is defined once in `skills.json`; use only skills relevant to the project/task.

Full workflow: `PLAYBOOK.md`.
