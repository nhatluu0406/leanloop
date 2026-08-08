---
name: codebase-map
description: Navigate repositories from a compact generated map instead of broad exploratory reads. Use on unfamiliar/multi-module codebases and refresh after structural changes.
---

# Codebase Map

Repeated rediscovery is avoidable context cost. Generate a compact navigation artifact, then confirm exact behavior with targeted source reads.

## Workflow

1. Prefer `state/REPOMAP.md` when current enough for the structural question.
2. Missing/stale after module moves/additions? Run `python3 scripts/leanloop/repomap.py .`.
3. Map → targeted grep → ranged read. Do not read adjacent files merely to build intuition.
4. Regenerate after structural changes before handoff.

## What REPOMAP includes

- Compact tree and line counts.
- Key exported/class/function symbols where cheap to extract.
- A few likely local import/dependency hints.
- Important hidden infrastructure directories (`.agents`, `.claude`, `.cursor`, `.github`, `.leanloop`) while skipping caches/VCS metadata.

The map is a locator, not semantic truth. Source/contracts still win. If the repository becomes too large or recurring architecture questions exceed what the map can answer cheaply, graduate to the wiki-protocol rather than inflating REPOMAP indefinitely.
