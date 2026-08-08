---
name: report-contract
description: Fixed compressed return format for scouts, reviewers, and delegated workers. Apply to any subagent result so isolated context does not flood back into the orchestrator.
---

# Report Contract

Delegation saves context only when the return path is compressed.

Return exactly:

```text
VERDICT: <answer/status in one line>
KEY FACTS:
- <max 5 evidence-backed facts>
FILES: <paths actually relevant>
RISKS:
- <max 2>
NEXT: <one concrete action>
DETAILS: <path or none>
```

## Rules

1. Target ≤300 tokens. If evidence needs more space, persist details under the **active task state's** `reports/` directory (`python3 scripts/leanloop/task.py path`) and point DETAILS there.
2. Do not return raw file contents, long logs, full diffs, search diaries, or generic explanation.
3. VERDICT comes first so the parent can stop reading early.
4. FILES lists only evidence-bearing paths; no exhaustive touched-file inventory.
5. A worker that changed code includes its commit SHA in KEY FACTS.
