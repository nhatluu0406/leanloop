---
name: frontend-design
description: Token-based UI development that prevents visual rework loops. Apply to any UI work — components, pages, styling, themes — before writing the first component and whenever aesthetics are being decided.
---

# Frontend Design (rework-proof)

UI is the most expensive rework surface: each "doesn't look right" round trip costs screenshots, descriptions, and regeneration. Freeze aesthetic decisions early and compose from them.

## The three locks

1. **Design tokens first.** Colors, spacing scale, typography, radii live in one theme file (CSS vars / Tailwind config / tokens.ts), created and approved before any component. If the ui-ux-pro-max generator is installed (see TOOLS.md), seed tokens by generating `design-system/MASTER.md` (+ `pages/*.md` overrides — page file wins over Master) and derive the theme file from it. Components **compose tokens; inventing raw values (`#3b82f6`, `13px`) is a defect** the reviewer flags.
2. **One approved mockup before N screens.** Optionally pick ONE reference DESIGN.md (awesome-design-md, see ADOPT.md — adapt, never clone a brand). Build a single representative static screen; get explicit user approval on the look (judged via design-review rubric); only then replicate the language across screens.
3. **Library before bespoke.** Check STACK.md's component library (shadcn, MUI, in-house...) — extend/configure existing components before writing new ones; new components get added to the library, not duplicated per page.

## Iteration rules

- UI polish loops follow loop-discipline: the acceptance bar is the approved mockup + tokens, not vibes.
- Visual changes reference tokens in the report ("bumped spacing 4→6"), enabling review without screenshots when possible.
- Accessibility basics (contrast from token pairs, focus states, semantic elements) are part of the gate, not a later pass — retrofitting a11y is a rework loop.
