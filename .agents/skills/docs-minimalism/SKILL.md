---
name: docs-minimalism
description: Keep documentation single-source and reader-driven without deleting operational, security, contributor, or architecture docs that a real project needs. Apply when creating or reviewing docs/comments.
---

# Docs Minimalism

Documentation has maintenance/context cost, but missing operational knowledge also creates rework and risk. Optimize for useful ownership, not an artificially tiny doc count.

## Default docs

- README: what/why, install, quick start, validation, links.
- STACK / PLAN / HANDOFF and contract files: agent/project state owned by their workflows.
- LICENSE, CONTRIBUTING, SECURITY when the repository is shared/public.
- CHANGELOG/release notes when release consumers need them (prefer generation from structured commits/tags).
- Runbooks, ADRs, threat models, compliance/operations docs **when the project's risk/operations require them**.
- Docs explicitly requested by maintainers/users.

## Avoid

- Restating signatures or obvious code.
- Duplicating the same project fact across README, adapters, wiki, and plans.
- Post-task summary files whose only content already exists in commits/PLAN.
- Long architecture walkthroughs when a durable diagram/map/ADR owns the decision better.

A fact should live at the layer that owns it; other docs link rather than copy.
