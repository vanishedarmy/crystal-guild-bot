# Crystal Guild v1.2.0 — Expeditions RC1
## Release Candidate 1

RC1 freezes the v1.2 Expeditions feature set and prepares the branch for final release. No new gameplay systems are added in this checkpoint.

### Player Guide cleanup
- Removes Beta 1–4 release-engineering/history blocks from the Expeditions chapter.
- Removes implementation language such as schema, SQLite/replay receipts, authoritative timers, Bot restarts, simulation details, and feature-freeze notes from player instructions.
- Keeps the information players actually need: unlock requirements, regions, route lengths, risk signals, Cache/return rules, landmarks, regional bosses, Mastery, Atlas/Legendary Contracts, Chocobo specialties, Hunt Seal stipends, and active-run restrictions.
- Rewords saved-run behavior in player language: journeys and pending decisions remain available when the player leaves and returns.

### RC verification
- Beta 4 persistence, duplicate-reward protection, Long Rest/stream-refresh safeguards, restart recovery, and schema-7 → schema-8 migration coverage remain intact.
- Beta 3 mobile/accessibility behavior and Beta 2 viewport-preserving detail cards remain intact.
- Explicit routed artwork and portrait scenic backgrounds are audited before packaging.
- Release packages exclude live databases, tokens, `.env`, logs, bytecode, caches, and other runtime-private files.

### Compatibility
- Bot runtime: `1.2.0-expeditions-rc1`
- Hosted Web runtime: `1.2.0-expeditions-rc1`
- Frontend asset revision: `1.2.0-expeditions-rc1`
- Local DB schema: **8**
- Hosted sync schema: **1**
- Portal Action protocol: **20**
- Twitch prefix: `!`
- Player reset: **none**
- New environment variables: **none**
