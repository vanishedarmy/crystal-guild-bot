# Crystal Guild v1.1.19 — Retro Phase III / RC1 Hotfix 9 — Raid Timing & Field Support

## Timing
- Rally Venture: **60s rally**, **30s rounds**.
- Raid: **90s rally**, **60s rounds**.
- `.env.example` ships those defaults.
- The in-place upgrade helper rewrites only exact prior stock timer values while preserving custom operator overrides.

## Portal-origin Raid rally output
- Authenticated Streamer Portal `Spawn Boss` now stages the same boss/rally `GameResult` for Twitch delivery after the Portal acknowledgement succeeds.
- Delivery is LIVE-only and fails closed if stream state cannot be confirmed.
- Chat `!spawnboss` behavior remains unchanged.

## Field support
- `!use <item>` remains self-targeted outside battle.
- While LIVE, eligible field recovery may target another adventurer with `!use <item> | <username>`, `!use <item> on @username`, or `!use <item> @username`.
- Portal `USE_FIELD_ITEM` may carry a sanitized target username.
- Target-other field use is independently LIVE-gated by the Bot.
- The target cannot currently be in a timed encounter/raid, Hunt, or Solo Venture.
- The user's item is consumed only when a useful field effect succeeds.

## Preserved
- Local DB schema **7**, no migration/reset.
- Persistent Adventure results and Confirm Result.
- Streamer Inventory Admin.
- Dynamic Camp 15m LIVE / 1h OFFLINE.
- Solo Venture maximum monster level is now **player level +5** (minimum selection still begins at roughly player level -2).

## Identity
- Bot runtime: `1.1.19-retro-phase-iii-rc1h9`
- Portal Action protocol: **19**
- Hosted sync schema: **1**
- Prefix: `!`
