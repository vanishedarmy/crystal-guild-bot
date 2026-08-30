# Crystal Guild v1.4.0 — Dungeons & Delves

Crystal Guild is a persistent Final Fantasy-inspired Twitch RPG with a companion Adventurer Portal. **Dungeons & Delves** is the final v1.4.0 production release.

## Dungeons & Delves

- Four persistent delves: Forgotten Ossuary, Emberglass Foundry, Whiteglass Bastion, and Riftglass Observatory.
- Player-paced Dungeon combat with persistent HP, MP/AP, items, chamber state, discoveries, route effects, and Dungeon Cache.
- Crossroads, weighted Events, hazards, treasure, sanctuaries, minibosses, and bosses with room-specific pressure mechanics.
- One-time first-clear rewards, personal Dungeon records, and Expedition-exploration unlocks.
- Exact run/chamber/revision state binding, cross-connection write serialization, replay-safe action receipts, and restart/reconnect persistence.
- Desktop/mobile Dungeon Board UX with the disclosure pointer fixed to the right on narrow screens.

## Runtime identity

- Bot runtime: `1.4.0-dungeons-delves`
- Local DB schema: **10**
- Hosted sync schema: **1**
- Portal Action protocol: **25**
- Twitch command prefix: `!`

Deploy the matching v1.4.0 Web + Bot together. RC1 promotes directly with no database migration, player reset, OAuth change, new environment variable, or gameplay/economy rebalance.
