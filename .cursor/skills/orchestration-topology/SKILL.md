---
name: orchestration-topology
description: Choose the cheapest safe topology: inline loop, isolated fan-out, or dependency graph. Use for multi-step or multi-agent workflows, especially before parallelizing implementation.
---

# Orchestration Topology

Use the least structure that makes dependencies and failure ownership explicit.

| Task shape | Topology |
|---|---|
| One goal, iterative refinement | One guarded loop |
| Independent read-only research | Flat fan-out |
| Independent code changes | Flat fan-out **with one Git worktree per worker** |
| Ordered/shared-contract steps | Dependency graph in PLAN.md |
| One-shot lookup/change | No orchestration |

## Graph rules

1. Edges are durable artifacts: contracts, PLAN dependencies, reports, commits — not shared hidden conversation state.
2. Every node has a verifier, iteration budget, risk level, and failure owner.
3. Parallel code nodes never share a working tree/index. Generate isolated worktrees first.
4. Integration is a separate orchestrator responsibility: review worker commit → integrate → run combined gate.
5. Shared generated files or migrations count as shared state even when source files differ; serialize them unless ownership is explicit.

If a proposed graph has no real parallelism, branching, or dependency benefit, use a loop instead.
