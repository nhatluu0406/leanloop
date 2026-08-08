---
name: tool-economics
description: Minimize standing tool-schema/context overhead while preserving required capabilities. Consult before enabling MCP servers, adding external integrations, or expanding the default tool surface.
---

# Tool Economics

Every always-available integration has context, security, maintenance, and failure-surface costs. Prefer capabilities that load only when needed.

## Decision ladder

1. Built-in file/shell/grep tools.
2. Existing project CLI or a narrow one-off script.
3. On-demand external CLI/API client with pinned version/contract.
4. Gateway/adapter when it demonstrably reduces a larger persistent integration surface.
5. Direct always-on MCP/server integration only when stateful sessions, OAuth/user identity, streaming/server push, or vendor-only functionality actually require it.

## Rules

- Default optional integrations off; enable per task and remove when no longer justified.
- For a one-shot lookup, do not install a persistent server.
- Subagents get the narrowest tool permissions that complete their role; read-only roles should be mechanically read-only where the platform permits it.
- Pin executable third-party dependencies in `TOOLS.lock`; normal workflows never use `@latest`.
- Measure your environment instead of repeating universal MCP/token multipliers. Tool schemas and caching behavior vary by platform/version.

If tool definitions dominate startup context, prune before doing work.
