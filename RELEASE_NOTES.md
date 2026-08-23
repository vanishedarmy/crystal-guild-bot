# Crystal Guild v1.1.14 — Cloud Continuity Hotfix 1

## Stream-presence gate

Because the Bot now runs continuously on Render, Twitch chat remains available even when the broadcaster is not streaming. Hotfix 1 separates **Bot online** from **stream live** and prevents live-show gameplay from being started or played through Twitch chat while the channel is offline.

The gate covers Rally Venture, Rally joins, Active Hunt starts, Active Battle actions, and Raid participation/actions. Read-only/reference commands and normal non-stream progression remain available. Portal Solo Venture and Portal Challenge Hunt remain intentionally available off-stream.

The check uses Twitch `GET /helix/streams?user_id=<broadcaster>` with an app access token generated from the already-configured Twitch application credentials. No new Twitch authorization is required.

A short status cache prevents chat traffic from creating excessive Twitch API requests. A temporary API failure can reuse a recent confirmed state, but after the configured stale window the state becomes UNKNOWN and live-only gameplay fails closed.

Streamer-only `!streamstatus` forces a fresh presence check. `!health` now reports the cached stream state.

## Compatibility

- Bot runtime: `1.1.14-cloud-continuity-h1`
- Hosted sync version/snapshots: `1.1.14-cloud-continuity` (unchanged for Web compatibility)
- Local DB schema: 4
- Hosted sync schema: 1
- Portal Action protocol: 12
- Twitch prefix: `!`
- Database migration: none
- Player reset: none
- Required new Render secrets: none
- Matching v1.1.14 Web remains compatible; no Web redeploy is required
