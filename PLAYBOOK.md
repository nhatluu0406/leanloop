# LeanLoop Playbook — idea → verified commit

LeanLoop optimizes **cost per accepted change**, not tokens in isolation. The cheapest run is the one that reaches a correct, maintainable result with the least rediscovery and rework.

## Phase 0 — establish project law

1. Create/refresh `STACK.md` from `templates/STACK.md`: language/runtime, package manager, canonical commands, structure/module ownership, architecture choices.
2. Generate `state/REPOMAP.md`: `python3 scripts/leanloop/repomap.py .`.
3. Select only skills the project needs. Tier membership is in `skills.json`; propagate with `python3 scripts/leanloop/sync.py`.
4. Run `python3 scripts/leanloop/doctor.py`.

## Phase 1 — turn intent into a small execution graph

1. Capture intent/non-goals in BRIEF.md when the task is not already precise in an issue/spec.
2. Start task-scoped state: `python3 scripts/leanloop/task.py start <slug>`.
3. Create PLAN.md from `templates/PLAN.md`.
4. Every step declares dependency, risk, isolation mode, owned/allowed paths, and a machine verifier.
5. Define shared API/schema/type contracts before implementation steps that depend on them.
6. Review the plan before code. HIGH-risk steps use the strongest available reasoning.

## Phase 2 — choose the cheapest safe topology

- Tiny deterministic change → inline.
- Bulky read-only investigation → scout/read-only worker.
- Normal reviewed implementation → standard implementer.
- Security/data-loss/concurrency/migration/architecture-sensitive work → strong implementer.
- Independent implementation steps → one **Git worktree per worker** (`python3 scripts/leanloop/worktree.py create <slug>`).
- Shared files, migrations, generated outputs, or contract ownership → serialize or declare dependencies.

"Different files" alone does not make shared-worktree parallelism safe: Git index and generated state are shared resources.

## Phase 3 — implement one bounded step

Before edits:

```bash
python3 scripts/leanloop/git_guard.py
```

A dirty main tree is not an invitation to clean/reset someone else's work. Create an isolated worktree instead.

For the step:
1. Read only STACK/PLAN/contracts + source ranges needed for the owned paths.
2. Implement only the declared scope.
3. Failure loop: read complete evidence, make one hypothesis-driven change, run the named check. Same error three times → stop and persist a stuck report in the active task state.
4. Run the verification gate.
5. Commit only explicit paths:

```bash
python3 scripts/leanloop/safe_commit.py -m "plan#N: concise summary" path/to/a path/to/b
```

Never `git add .`; never absorb unrelated staged files.

## Phase 4 — review and integrate

For parallel workers:
1. Worker returns compressed report-contract + commit SHA.
2. Reviewer receives the PLAN step, STACK/contracts, and worker diff/commit — not the entire repo transcript.
3. APPROVE → orchestrator integrates (normally `git cherry-pick <sha>`).
4. REVISE → a scoped follow-up PLAN step or worker correction; no silent "quick fix" on the integration branch.
5. After integrating a parallel group, run the combined impacted gate because individually-green commits can still conflict semantically.

The worker never merges itself into the integration branch.

## Phase 5 — verification gate

Run only checks relevant to the stack, but keep the order mechanical:

1. formatter/linter;
2. typecheck;
3. PLAN verifier;
4. impacted behavior tests;
5. domain gates (accessibility/screenshots, migration dry-run, dependency boundary/security checks, etc.);
6. `git diff --check` + focused diff review.

Machine checks own mechanical correctness; reviewer tokens go to logic, contracts, risk, and architecture.

## Phase 6 — crystallize and hand off

After each green step:
- tick PLAN.md;
- append any new decision once, at its owning file;
- refresh active task checkpoint/handoff if a session boundary or compaction could occur.

End of session: update `state/tasks/<slug>/HANDOFF.md` (or legacy `state/HANDOFF.md` when no active task). Exact status, locked decisions, traps, next action — no narrative history.

Claude Code hooks assist checkpoint/reload. Codex/Cursor use the same disk discipline even without equivalent compaction hooks.

## Phase 7 — measure the optimization

Use the pinned telemetry path:

```bash
python3 scripts/leanloop/token_report.py daily all
python3 scripts/leanloop/token_report.py daily claude
python3 scripts/leanloop/token_report.py daily codex
```

Compare equivalent task shapes. Track accepted outcome, retries/rework, and usage/cost where available. Do not optimize for a lower token number that produces poorer code or another repair session.

## Operating invariants

- Durable state > chat memory.
- Contract before parallel implementation.
- Risk determines model strength.
- Parallel code requires filesystem/Git-index isolation.
- Explicit staging only.
- Three evidence-bearing attempts, then escalation.
- Native skill discovery means adapters do not repeat skill descriptions.
- Optional tools stay pinned and off until justified.
