---
name: design-review
description: Judging UI output against a scoring rubric and anti-AI-slop checklist, with a screenshot review protocol. Apply when reviewing any built UI, before approving mockups, and whenever output risks "looks AI-generated" — complements frontend-design (process) by judging results.
---

# Design Review

"Looks AI-made" is not vibes — it's a symptom list, and symptom lists are checkable. This skill turns aesthetic review into a repeatable gate. It judges output; frontend-design governs process; generators (ui-ux-pro-max) supply the system being judged against.

## Anti-AI-slop checklist (any hit = REVISE)

- Default purple/blue-pink gradients; neon on dark "because tech"
- Emoji used as icons (use SVG sets: Heroicons/Lucide)
- Everything is a rounded-shadowed card; centered-hero-three-feature-cards template layout
- Uniform spacing everywhere — no rhythm, no intentional density contrast
- Typography without hierarchy contrast (one weight, two sizes)
- Missing states: empty, loading, error, long-content overflow — the loudest "not commercial-grade" tell
- Interaction gaps: no cursor-pointer on clickables, no hover transition (150–300ms), no visible focus states, prefers-reduced-motion ignored
- Contrast below 4.5:1 body text; untested at 375/768/1024/1440px

## Scoring rubric (score each 1–5; any axis ≤2 = REVISE)

1. **Type hierarchy** — clear size/weight contrast; scannable levels
2. **Spacing rhythm** — deliberate scale with density variation, not uniform padding
3. **Color restraint** — one accent doing real work; semantic role per color (per tokens/MASTER.md)
4. **State completeness** — empty/loading/error/edge all designed
5. **Information density** — matches product type (dashboard ≠ landing page)
6. **Distinctiveness** — would pass as the reference product's sibling, not a template demo

## Protocol

1. Inputs: screenshots at 4 breakpoints (Playwright — see verification-gate), the tokens file or `design-system/MASTER.md`, and the project's reference DESIGN.md if one was chosen (see ADOPT.md).
2. Machines first: contrast + a11y via Lighthouse/axe; only then human-judgment axes.
3. Verdict per report-contract: APPROVE / REVISE (max 5 findings, each naming the rubric axis and the token-level fix) / ESCALATE (needs the human's eye — taste ceilings are real; say so instead of guessing).
4. Never approve raw values that bypass tokens — that's a frontend-design violation regardless of how it looks.
