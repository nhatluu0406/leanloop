# OpenWiki setup (optional, large repos only)

1. Read the locked version from `TOOLS.lock` and install that version, not `latest`.
2. Run `bash scripts/install_tools.sh all` or install `openwiki@<OPENWIKI_VERSION>` manually.
3. Initialize OpenWiki for the repository.
4. Copy `templates/WIKI-INSTRUCTIONS.md` to `openwiki/INSTRUCTIONS.md` and tailor only scope/architecture priorities.
5. If enabling CI updates, audit `.agents/skills/wiki-protocol/assets/openwiki-update.yml`, pin any third-party actions it uses, and add only the required provider secrets.

OpenWiki is optional. Use it only when repeated architecture/knowledge questions justify its maintenance and inference cost; source remains truth for exact behavior.
