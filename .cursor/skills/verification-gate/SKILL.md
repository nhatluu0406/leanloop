---
name: verification-gate
description: Mechanical completion gate plus Git-safety rules. Apply after every code change, before every commit, and before claiming a step is complete.
---

# Verification Gate

A step is complete only when its declared checks pass and the commit contains only the intended scope.

## Gate order

1. Formatter/linter.
2. Type check when applicable.
3. PLAN step verifier.
4. Impacted tests — never zero for behavior changes unless PLAN explicitly marks HUMAN-VERIFY and explains why.
5. Domain gates when applicable (UI accessibility/screenshots, module-boundary checker, migration dry-run, security/static analysis, etc.).
6. `git diff --check` and focused diff self-review for dead/debug code, contract drift, accidental generated files, and scope creep.

## Git safety

Before implementation: `python3 scripts/leanloop/git_guard.py`.
- Dirty main tree → do not mix agent work with user changes; create an isolated worktree.
- Parallel implementers always use separate worktrees/branches even if their planned files differ.
- Stage/commit an explicit allowlist: `python3 scripts/leanloop/safe_commit.py -m "plan#N: summary" path1 path2 ...`.
- `git add .`, wildcard staging, and committing unrelated pre-staged files are forbidden.

Reviewer approves the worker diff/commit before integration. The orchestrator then runs the combined impacted gate after cherry-picking parallel work.

Gate failure returns to the loop; the same failure three times triggers loop-discipline escalation rather than a fourth guess.
