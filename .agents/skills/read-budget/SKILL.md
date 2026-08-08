---
name: read-budget
description: Reading discipline that caps how file content enters context. Apply on every file read, log inspection, or data exploration — especially before reading any file over ~200 lines or any command output of unknown size.
---

# Read Budget

Everything read is paid for on every subsequent turn. Read the minimum that answers the current question.

## Rules

1. **Grep before read.** Locate the relevant symbol/line first; then read a range around it. (A PreToolUse hook may block un-ranged reads of files >500 lines — this is intentional; comply, don't work around it.)
2. **Ranges, not files.** Read the function, not the module. Widen only if the range proves insufficient.
3. **Head/tail unknown output.** Pipe long command output through `head -50` / `tail -50` / `grep` / `wc -l` first; read fully only when justified.
4. **Never re-read.** If a file was read this session and hasn't changed, use what's in context. If it may have changed, re-read only the changed range (check `git diff` first).
5. **Logs and data files**: sample, aggregate, or query (`grep -c`, `awk`, `jq`, SQL) — never load raw into context. Write extraction scripts; only their small output enters context.
6. **Binary/generated/vendored paths are off-limits** (`node_modules`, `dist`, lockfiles, migrations history) unless the task is explicitly about them.
7. **Delegate bulk reading.** If answering requires reading >3–4 large files, that's a scout subagent's job (delegation-protocol) — not the main context's.
