# PLAN: <task name>
<!-- Live task graph. Keep steps independently verifiable/committable. -->

Input: <BRIEF.md or issue> | Stack: STACK.md | Contract: <path or none>
Task slug: <slug> (`python3 scripts/leanloop/task.py start <slug>`)

## Non-goals
- <explicit scope firewall>

## Steps
<!-- risk: LOW|MEDIUM|HIGH ; isolation: inline|sequential|worktree -->
- [ ] 1. <outcome>
  - depends: —
  - risk: <LOW|MEDIUM|HIGH>
  - isolation: <inline|sequential|worktree>
  - owns/allows: <paths, module, contract>
  - verifier: `<machine-checkable command>`
- [ ] 2. <outcome>
  - depends: 1
  - risk: <...>
  - isolation: <...>
  - owns/allows: <...>
  - verifier: `<command>`

## Parallel groups
<!-- Only group steps with separate worktrees and no shared files/generated outputs/migrations/contracts. -->
- <none | [2,3] after 1>

## Decisions
<!-- append-only: date | decision | reason -->

## Escalation
- Same error 3 times: <reviewer/strong model/human>
- Failed branch owner: <orchestrator/reviewer>
