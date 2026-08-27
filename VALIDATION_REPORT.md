# Validation Report — RC1 Hotfix 6 Persistent Adventure Results

## Identity
- Runtime: `1.1.19-retro-phase-iii-rc1h6`
- Local DB schema: 7
- Hosted sync schema: 1
- Portal Action protocol: 17
- Twitch prefix: `!`

## Automated validation
- Bot Python tests: **400 / 400 PASS**
- Hosted Web / Portal Python tests: **47 / 47 PASS**
- Frontend Node tests: **291 / 291 PASS**
- Python `compileall`: **PASS**

## Persistence and migration checks
- Schema 6 → 7 is additive.
- Existing databases receive a verified automatic `pre_schema_7_*.db` backup before the new table is created.
- `portal_adventure_results` uses player foreign keys and retains unacknowledged rows without time expiry.
- Confirmed rows are retained only as short diagnostic history and may be pruned after 30 days; unconfirmed rows are never auto-pruned.
- Solo result persistence survives loss of the old in-memory recent-result cache.
- Timed Hunt result persistence survives loss of transient battle history.
- `ACK_ADVENTURE_RESULT` is player-scoped and replay safe.

## Continuity
Streamer Controls, LIVE-only notable Portal announcements, refreshed Relic artwork, and LIVE/OFFLINE Camp timing remain intact.
