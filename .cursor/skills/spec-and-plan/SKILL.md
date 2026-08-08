---
name: spec-and-plan
description: Produce a reviewed PLAN.md with scope, dependencies, risk, isolation, and machine-verifiable done criteria before non-trivial implementation. Use for features, refactors, and bugfix batches.
---

# Spec and Plan

Planning is a rework-control mechanism. Keep it short enough to review and precise enough that implementation does not need to rediscover decisions.

## Protocol

1. Read BRIEF.md when present, STACK.md, existing PLAN.md, active HANDOFF, and relevant contracts.
2. Write PLAN.md from `templates/PLAN.md`. Every step declares:
   - exact outcome and non-goals;
   - dependencies;
   - risk: LOW / MEDIUM / HIGH;
   - isolation: inline / sequential / worktree;
   - allowed files or owned module/contract;
   - machine-checkable verifier (or explicit HUMAN-VERIFY with reason).
3. Define shared contracts/interfaces before parallel implementations.
4. Review the plan before coding. Trivial local edits may use a tiny inline plan, but still obey Git safety and verification.
5. Treat PLAN.md as live state: tick completed steps and append decisions rather than re-litigating them in chat.

## Parallel-safety check

Two steps are parallel-safe only when they do not share source files, generated outputs, migrations, contract ownership, or mutable workspace state. Parallel code still requires separate Git worktrees because the Git index itself is shared otherwise.

## Routing

Planning and HIGH-risk steps use the strongest available reasoning. LOW/MEDIUM execution can use cheaper models when contracts and verifiers make the task deterministic.
