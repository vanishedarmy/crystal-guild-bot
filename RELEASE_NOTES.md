# Crystal Guild v1.1.19 — Retro Phase III / RC1 Hotfix 7 — Streamer Inventory Admin

## Added
- Owner-only `!additem <player> | <item> | [quantity]` with alias `!giveitem`.
- Owner-only `!removeitem <player> | <item> | [quantity]` with alias `!takeitem`.
- Same two operations exposed through authenticated Streamer Portal controls.
- Exact Twitch username/display-name/ID player resolution and exact item name/ID resolution.
- Quantity guardrail 1–999.
- Normal item transaction ledger entries using `streamer_admin:add` / `streamer_admin:remove`.
- Automatic unequip when the streamer removes the last owned copy of equipped gear.
- Portal replay protection so acknowledgement retries cannot duplicate an inventory mutation.

## Preserved
- Local DB schema remains **7**; no migration or reset.
- Persistent Solo/Hunt results and Confirm Result behavior.
- LIVE-only notable Portal Solo/Hunt/Title announcements.
- 15-minute LIVE / 1-hour OFFLINE base Camp timing.
- Relic Tier 1/2/3 artwork integration.

## Identity
- Bot runtime: `1.1.19-retro-phase-iii-rc1h7`
- Portal Action protocol: **18**
- Hosted sync schema: **1**
- Prefix: `!`
