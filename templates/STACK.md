# STACK
<!-- ≤40 lines. Project decisions only — never general best practices. Agents read this before any code. Deviation requires editing this file first. -->

## Runtime & tooling
- Language: <e.g. TypeScript 5.x>
- Framework: <e.g. Next.js 15 (App Router)>
- Package manager: <pnpm — NOT npm/yarn>
- Node/py version: <>

## Commands (the only ones agents use)
- install: `pnpm i`
- dev: `pnpm dev`
- test: `pnpm test`
- lint+format: `pnpm lint && pnpm format`
- typecheck: `pnpm typecheck`

## Structure & Naming (agents guess wrong without this — fill at init)
- Organization: <feature-folders | layer-folders> ; module map: <module → owned domain, ~1 line each>
- Casing: <components PascalCase.tsx, utils camelCase.ts, routes kebab-case, ...>
- Tests: <co-located *.test.ts | separate tests/ mirror>
- Import aliases: <@/ → src/ ; no deep relative ../../..>

## Binding decisions
1. Validation: <e.g. Zod at all boundaries>
2. Errors: <e.g. Result type, no thrown domain errors>
3. State (FE): <e.g. server components + zustand for client islands>
4. Styling: <e.g. Tailwind + tokens in tailwind.config — no raw values>
5. Auth: <>
6. DB access: <e.g. Drizzle; schema changes via migrations only>
7. API shape: <e.g. contract/openapi.yaml is source of truth; types generated>
8. <...max 10>
