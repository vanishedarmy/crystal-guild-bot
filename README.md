# Crystal Guild v1.4.0 — Dungeons & Delves Beta 3

Crystal Guild is a persistent Final Fantasy-inspired Twitch RPG with a companion Adventurer Portal. Beta 3 is the final shared-state, restart, replay, and concurrency hardening pass for Dungeons & Delves before release-candidate work.

## Beta 3 focus

- Keeps the feature-frozen four-Dungeon catalog unchanged.
- Serializes authoritative state-guarded mutations at the SQLite write boundary before reading live Dungeon state.
- Prevents two separate Bot/database connections from spending the same run/chamber/revision concurrently.
- Preserves exact action-ID replay: duplicate delivery returns the committed receipt rather than resolving again.
- Retains Beta 1 run/chamber/revision stale-tab protection, restart persistence, route effects, Events, first clears, settlement, and records.
- Keeps the Adventure-state payload below the 16 KiB guardrail.

## Runtime identity

- Runtime: `1.4.0-dungeons-b3`
- Local DB schema: **10**
- Hosted sync schema: **1**
- Portal Action protocol: **25**
- Twitch command prefix: `!`

Deploy the matching Beta 3 Web and Bot together to receive the complete hardening pass. See `UPGRADE_GUIDE.md` for the Beta 2 Web + Beta 1 Bot upgrade path.
