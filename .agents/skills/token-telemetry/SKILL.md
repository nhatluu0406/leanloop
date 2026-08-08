---
name: token-telemetry
description: Measure agent usage/cost before and after workflow changes across sources the local telemetry tool supports. Use for cost questions, optimization experiments, and project retrospectives.
---

# Token Telemetry

Optimization claims need comparable measurements.

## Tooling

- `python3 scripts/leanloop/token_report.py [daily|weekly|monthly|session] [all|claude|codex]` uses the **pinned** ccusage version from `TOOLS.lock`.
- Current ccusage releases can aggregate multiple supported coding-agent data sources; LeanLoop explicitly supports Claude and Codex reporting here. Cursor is recorded separately when its local/exported usage data is available rather than pretending telemetry is unified when it is not.
- In-tool usage indicators remain useful for live context pressure but are not substitutes for a comparable before/after experiment.

## Protocol

1. Capture baseline on representative task shapes.
2. Change one workflow variable at a time (map discipline, skill tier, model routing, tool choice, fan-out width...).
3. Compare success/quality **and** usage. A cheaper run that creates rework is not an optimization.
4. Retrospective fields: task class, tool/model, outcome, retries, usage/cost available, and one-line attribution.

Do not publish universal token-savings multipliers from anecdotal runs. Keep project-specific benchmarks reproducible if you want to make quantitative claims.
