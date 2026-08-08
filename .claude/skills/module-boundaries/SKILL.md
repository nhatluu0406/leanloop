---
name: module-boundaries
description: Backend modularity rules that prevent spaghetti — module ownership map, one-way dependencies, size-as-signal budgets, and mechanical boundary enforcement. Apply when creating backend features, adding modules, or whenever a file/function is growing past budget.
---

# Module Boundaries

AI spaghetti isn't a knowledge gap — it's completion pressure: logic lands in the nearest file, controllers become god-files, cross-imports creep in "just this once". These rules make boundaries explicit and machine-enforced.

## Rules

1. **Ownership map first.** STACK.md's Structure section names each module and the domain it owns (~10 lines). A new feature's first PLAN decision: which module owns it — or the explicit case for a new one. Never "wherever is closest".
2. **One-way dependencies, public surface only.** Modules import other modules solely through their public interface (index/facade). Reaching into another module's internals is a defect, not a shortcut. Cycles are always a REVISE.
3. **Size is a signal, not a style rule.** File >~300 lines or function >~50 lines: split it, or record the one-line justification in PLAN.md ## Decisions. Ignoring the signal silently is the violation.
4. **Transport is thin.** Routes/controllers/handlers orchestrate: validate (at the boundary, per STACK's validation choice), call domain logic, shape the response. Business rules never live in the transport layer.
5. **Shared code is extracted deliberately** into a named shared module with an owner — never via util-dumping or copy-paste between modules.

## Mechanical enforcement (zero model tokens)

Bundle `assets/dependency-cruiser.sample.cjs` into the project (copy + adapt module names), add `depcruise src` to verification-gate. Boundary violations then fail the gate like failing tests — no memory required. For non-JS stacks use the equivalent (import-linter for Python, ArchUnit for JVM, internal/ convention for Go); the rule set transfers, the tool changes.

## Review hook

Reviewer checks diffs for: new cross-module imports, transport-layer logic, and size-budget breaches without a Decisions entry.
