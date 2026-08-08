---
name: context-lifecycle
description: Preserve only durable task state across compaction, sessions, tools, and parallel worktrees. Apply at phase boundaries, before compaction, and at session start/end.
---

# Context Lifecycle

The transcript is disposable. Decisions, exact in-flight state, and unresolved problems belong on disk.

## Task-scoped state

Start a task with `python3 scripts/leanloop/task.py start <slug>`. LeanLoop then uses `state/tasks/<slug>/` for HANDOFF, CHECKPOINT, and reports; `state/CURRENT_TASK` is local-only. This prevents unrelated tasks from overwriting each other's recovery state. Without an active task, legacy `state/` paths still work.

## In-session

1. Checkpoint at meaningful work boundaries, not only when context is nearly full.
2. Before compaction, record: PLAN step/status, decisions, unresolved error+hypothesis, exact files in flight, and attempts not to repeat.
3. Keep/drop instruction: keep decisions/invariants/paths/errors/task status; drop applied file contents, old tool output, resolved debate.
4. When context pressure becomes visible, finish the smallest safe unit, checkpoint, then compact rather than starting another branch of work.

## Cross-session / cross-tool

- Session end: update active task HANDOFF with status, locked decisions, traps, and exact next action.
- Session start: read STACK.md + PLAN.md + active HANDOFF/CHECKPOINT before asking for repeated context or exploring source.
- Consume only the active task's CHECKPOINT; do not delete another task's recovery state.
- Parallel workers get filesystem isolation through Git worktrees, which also isolates their task-state files.

Only decisions, invariants, open problems, and exact paths earn durable state. Regenerable file contents and process narration do not.
