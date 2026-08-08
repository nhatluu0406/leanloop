---
name: database-schema
description: Use a compact current-schema map for database work while preserving migration history for targeted debugging/evolution questions. Apply before queries, models, or schema changes.
---

# Database Schema

Current-state questions should not require replaying every migration, but migration history remains valid evidence when the problem is specifically about migration behavior or evolution.

## Rules

1. **Current schema first:** use `state/SCHEMAMAP.md` (tables, columns/types, relations, indexes; no data). Regenerate from the stack's introspection when missing/stale.
2. **Migrations are the write path:** add a new migration for schema changes; do not silently rewrite already-applied history.
3. **Do not read migration history merely to reconstruct current schema.** Read only the relevant migration ranges when debugging failed migrations, backfills, ordering, rollback behavior, or historical data transformations.
4. Query data narrowly (`COUNT`, filtered samples, aggregates); raw dumps do not enter context.
5. PLAN schema changes together with forced contract/type updates so dependencies are explicit before fan-out.

Schema-map generation is stack-specific; keep the resulting map compact and regenerable.
