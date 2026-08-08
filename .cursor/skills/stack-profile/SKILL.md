---
name: stack-profile
description: Every project declares its technical decisions in STACK.md; agents read it before writing any code. Use at project start, when STACK.md is missing, and before the first code change in any session — regardless of language or framework.
---

# Stack Profile

Rework rarely comes from missing knowledge — it comes from missing *decisions*: the agent guesses pnpm vs npm, Zod vs Joi, guesses wrong, and you pay the redo. One 40-line file kills the whole class.

## Protocol

1. **Before writing code, read `STACK.md`** at repo root. Missing? Create it now from `templates/STACK.md` — infer from lockfiles/configs, confirm ambiguities with the user in one batched question.
2. **STACK.md contents** (≤50 lines): language+version, framework, package manager, build/test/lint/run commands, the **Structure & Naming section** (organization scheme, module ownership map, casing, test placement, import aliases — mandatory; every file created in the wrong place is a rework seed), and the 5–10 binding architecture decisions (error-handling style, state management, validation lib, auth approach, styling system...).
3. **STACK.md is law.** Deviating requires updating STACK.md first (with user approval) — never silently drift.
4. New decision made mid-task? Append it immediately. Undocumented decisions get re-litigated every session.

## What does NOT belong

General best practices, style rules a linter enforces, anything the model already knows. Only *this project's choices*.
