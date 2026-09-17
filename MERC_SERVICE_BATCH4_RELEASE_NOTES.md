# Crystal Guild v1.8.0 Alpha 1 — Merc Service — Batch 4

## Player Guide, Quick Help & responsive polish

Batch 4 completes the code-only player-facing Merc Service layer before artwork integration.

### Web / Portal
- Visible Web identity is now **v1.8.0 Alpha 1 — Merc Service** (`1.8.0-merc-a1`).
- Player Guide adds a dedicated **Hero Merc Service** chapter and navigation entry.
- Guide documents the separate Hunt Seals economy: **C 1 / B 2 / A 3 / S 5** per successful Hunt.
- Guide documents all six Heroes, real unlock requirements, Hunt Mark fees, eligible mission types, and signature assists.
- Merc Service page now includes contextual `?` Quick Help and an inline **How Merc Contracts Work** briefing.
- Mobile adds an in-page Current / Roster / How It Works navigator, one-column roster behavior, touch-safe controls, and overflow protection.
- What’s New now leads with the v1.8 Merc Service Alpha 1 summary.
- Raid overlay asset cache-bust follows the v1.8 asset revision.
- Merc artwork remains intentionally absent until Batch 5.

### Bot help
- `!guild mercs` and `!guild merc` explain the Portal-first Merc Service, Hunt Seals, contract consumption, and cancellation rules.
- No new Twitch gameplay command is introduced; hiring remains authoritative through the Adventurer Portal.

### Release contract
- Runtime/frontend: `1.8.0-merc-a1`
- Local DB schema: **17**
- Hosted sync schema: **1**
- Portal Action protocol: **34**
- Player reset: **none**
- New migration in Batch 4: **none**
