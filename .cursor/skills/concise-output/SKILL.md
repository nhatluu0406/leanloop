---
name: concise-output
description: Output discipline for every response and generated document. Always active — apply whenever writing any reply, report, commit message, or doc so length matches value and no token restates what already exists.
---

# Concise Output

Every token in a reply is paid for twice: once now, once every time this conversation is re-sent. Write accordingly.

## Rules

1. **Never restate code you just wrote.** The user can see the file. Reference it: "Added `retry()` in `http.ts:42`."
2. **Return diffs, not whole files**, when modifying existing code — unless the tool requires full content.
3. **No ceremony.** Skip preambles ("Great question!", "I'll now proceed to...") and postambles ("Let me know if..."). Start with substance.
4. **Length scales with decision weight, not effort spent.** A 2-hour investigation with a simple conclusion gets a 3-sentence answer plus a pointer to details on disk.
5. **One idea, one place.** If it's in PLAN.md, don't repeat it in chat. Link/point instead.
6. **Status updates are one line.** "Step 3/7 done, tests green, committing." Not a narrative.
7. **When declining or uncertain, be brief and direct** — long hedging costs more and informs less.

## Anti-patterns (never do)

- Summarizing a file right after writing it
- Bullet-pointing three items that fit in one sentence
- Explaining standard library behavior the reader didn't ask about
- Re-quoting the user's request back to them

## Chat vs documents

These rules govern replies; standalone docs are governed by docs-minimalism. Research/search answers stay conversational prose — no report headers for a 5-line finding.
