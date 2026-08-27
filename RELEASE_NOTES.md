# Crystal Guild v1.1.19 — Retro Phase III / RC1 Hotfix 6 — Persistent Adventure Results

## Durable Adventure Board result inbox
The authoritative Bot database now stores Portal Adventure results in `portal_adventure_results`. Unacknowledged rows have no time-based expiry. Solo Venture outcomes and timed Hunt resolutions remain available to the signed-in player until that player confirms the individual result.

The new typed `ACK_ADVENTURE_RESULT` Portal action verifies player ownership, marks only the selected result as acknowledged, and returns a refreshed Adventure Board state. The action is replay/idempotency safe through the existing Portal action ledger.

Schema 7 is additive and automatically backed up before migration. Existing characters, progression, equipment, Relics, Chocobos, Camp state, and other player data are preserved.

## Hotfix 5 behavior retained
Owner-authenticated Streamer Control Portal actions remain available. LIVE-only Portal announcements remain limited to notable Solo results, Hunt results, and newly unlocked Titles, while normal Portal combat chatter stays silent. Chat-origin Twitch commands retain their normal chat response path.

## Compatibility
- Bot runtime: `1.1.19-retro-phase-iii-rc1h6`
- Local DB schema: **7**
- Hosted sync schema: **1** unchanged
- Portal Action protocol: **17** (paired Web update required)
- Twitch command prefix: `!` unchanged
- Camp: 15-minute LIVE / 1-hour OFFLINE base timer retained
- No player reset, OAuth change, or new environment variable
