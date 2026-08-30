# Crystal Guild v1.4.0 — Dungeons & Delves RC1

Crystal Guild is a persistent Final Fantasy-inspired Twitch RPG with a companion Adventurer Portal. RC1 is the release-candidate cleanup and deployment-readiness pass for Dungeons & Delves.

## RC1 focus

- Keeps the feature-frozen four-Dungeon catalog unchanged.
- Carries forward Beta 3 database-level serialization, exact run/chamber/revision stale-state validation, and action-ID replay safety.
- Performs final upgrade/restart/recovery/package drills without changing Dungeon rewards, combat tuning, or progression.
- Removes a shipped runtime overlay-state artifact and aligns package/project version surfaces for release.
- Refreshes setup/deployment documentation that still described older v1.1-era builds.

## Runtime identity

- Bot runtime: `1.4.0-dungeons-rc1`
- Local DB schema: **10**
- Hosted sync schema: **1**
- Portal Action protocol: **25**
- Twitch command prefix: `!`

Deploy the matching RC1 Web + Bot together. No database migration, player reset, OAuth change, new environment variable, or gameplay/economy rebalance is required from Beta 3.
