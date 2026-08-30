# Crystal Guild v1.4.0 — Dungeons & Delves Beta 1

Crystal Guild is a persistent Final Fantasy-inspired Twitch RPG with a companion Adventurer Portal. Beta 1 freezes the Dungeons & Delves feature set and hardens the four existing persistent Dungeons for release-quality testing.

## Beta 1 focus

- Four-Dungeon catalog frozen: Forgotten Ossuary, Emberglass Foundry, Whiteglass Bastion, Riftglass Observatory.
- Exact Portal mutation binding to Dungeon run, chamber, and persisted state revision.
- Same-room stale tabs fail closed after any newer Dungeon mutation.
- Replay-safe action receipts, restart/reconnect persistence, route effects, Event rooms, first-clear bonuses, retreat/defeat settlement, and records remain intact.
- Round-limited encounters expose their current round and limit in the Portal.

## Runtime identity

- Runtime: `1.4.0-dungeons-b1`
- Local DB schema: **10**
- Hosted sync schema: **1**
- Portal Action protocol: **25**
- Twitch command prefix: `!`

Deploy the matching Beta 1 Web and Bot together. See `UPGRADE_GUIDE.md` for the Alpha 4 upgrade path.
