---
name: delegation-protocol
description: Decide when delegation actually saves context, how to isolate parallel workers, and when a stronger model is worth the cost. Consult before spawning subagents or parallel implementation.
---

# Delegation Protocol

Subagents buy context isolation, not free labor. Spawn only when the isolated work would otherwise pollute the orchestrator context more than the startup/report overhead.

## Decision table

| Situation | Action |
|---|---|
| Multi-file read-only investigation | Scout / cheap read-only worker |
| Simple shell/git op or small single-file tweak | **Inline** |
| Reviewed deterministic implementation | Standard implementer |
| Security, data-loss, concurrency, migration, architecture-sensitive change | Strong implementer / strongest available reasoning |
| Independent implementation steps | Parallel only in **separate Git worktrees/branches** |
| Shared files, shared generated artifacts, or ordering | Sequential or explicit dependency graph |
| Diff/plan judgment | Reviewer / strongest available reasoning |

## Risk-adaptive routing

Model choice follows risk, not job title:
- **LOW** — mechanical change, strong verifier, tiny blast radius → cheaper model.
- **MEDIUM** — normal feature/refactor with clear contracts/tests → standard model.
- **HIGH** — auth/security, irreversible data changes, concurrency, migrations, public contracts, architecture-sensitive refactors, or ambiguous failures → strongest model.

Escalate a low/medium worker when uncertainty becomes high; do not let a cheap model burn retries on a reasoning problem.

## Parallel isolation is mandatory

"Different files" is not enough: workers can still collide through the Git index, generated files, PLAN.md, or shared state. For parallel implementation:
1. Orchestrator creates one worktree per worker: `python3 scripts/leanloop/worktree.py create <slug>`.
2. Each worker commits only inside its assigned worktree using explicit-path staging.
3. Reviewer judges the worker commit/diff.
4. Orchestrator integrates approved commits (normally cherry-pick) in dependency order.
5. Workers never merge into the integration branch themselves.

## Brief contract

Every delegated brief contains: exact PLAN step, risk level, worktree path when applicable, allowed files/interfaces, verifier, non-goals, and report-contract. Cap fan-out at what the orchestrator can actually review.
