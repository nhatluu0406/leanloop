---
name: loop-discipline
description: Bound debugging and generative loops with a verifier, iteration budget, progress signal, and escalation. Apply whenever retrying the same goal or error.
---

# Loop Discipline

An unbounded retry loop consumes context while reducing signal. Declare what counts as progress and stop when the approach is no longer learning.

## Loop contract

- Goal + verifier.
- Iteration budget (default 3 for the same debugging error; set deliberately for generative refinement).
- Progress signal: what evidence must differ between attempts.

## 3-strikes debugging rule

After three failed attempts at the same error:
1. Stop — no cosmetic variant #4.
2. Persist a compact stuck report under the active task's `reports/`: exact error, three materially different attempts, evidence from each, current hypothesis.
3. Escalate to a stronger reasoner/reviewer or human as PLAN.md specifies.

If an attempt reproduces the identical error without new evidence, or re-applies a just-reverted change, treat it as no progress and reconsider the approach early.

Each attempt begins from the complete relevant error/trace/assertion, not only its first line. Generative loops likewise need an acceptance bar (spec, examples, design tokens, metrics) before iteration begins.
