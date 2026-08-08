# Wiki brief (for OpenWiki — copy to openwiki/INSTRUCTIONS.md)

Audience: coding agents locating context fast. Optimize for lookup speed, not completeness.

Scope — document ONLY:
- Architecture: subsystems, responsibilities, boundaries (1 page each, hard cap)
- Cross-module contracts and invariants ("X assumes Y is already validated")
- Data flow for the 3–5 critical paths
- Why-decisions that code can't express

Never document:
- Per-file or per-function walkthroughs (code is truth; agents read source for behavior)
- Anything a generated map already shows (tree, symbols)
- Style/conventions (STACK.md owns those)
- Tutorials, marketing prose, changelogs

Style: terse declarative sentences. Every page readable in ~1 minute. When updating, DELETE stale content — do not append corrections.
