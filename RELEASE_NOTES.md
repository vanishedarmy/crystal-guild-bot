# Crystal Guild v1.4.0 — Dungeons & Delves Beta 1

## Beta stabilization / feature freeze

Beta 1 freezes the v1.4 Dungeon feature set at four delves and focuses on reliability, continuity, and player-facing clarity. No fifth Dungeon, new currency, or non-Dungeon balance pass is included.

### Exact Dungeon state binding
- Every Portal Dungeon mutation now carries the persisted Dungeon **state revision** in addition to the run ID and chamber ID.
- Actions are accepted only when run, chamber, and revision all match the authoritative current run.
- This closes the remaining same-room stale-tab case: an older browser tab cannot spend a second combat turn after another tab has already advanced that chamber.
- Continue, Crossroads choice, retreat, normal attack, Defend, Job Ability, and Item actions all use the same exact-state contract.
- Repeated delivery of the **same action ID** remains replay-safe and returns the original receipt rather than advancing again.
- Dungeon revision is persisted with the run and survives Bot restart/reconnect.

### Player-facing Beta cleanup
- Dungeon encounter cards show **Round X / Limit** when a room has a round limit.
- The Dungeon Board remains frozen at Forgotten Ossuary, Emberglass Foundry, Whiteglass Bastion, and Riftglass Observatory.
- What's New and Player Guide copy identify Beta 1 as a stability pass rather than another content expansion.
- High-frequency Adventure state is compacted slightly while preserving all player-usable Dungeon information.

### Compatibility
- Bot/Web/frontend runtime: `1.4.0-dungeons-b1`
- Local DB schema: **10** unchanged
- Hosted sync schema: **1** unchanged
- Portal Action protocol: **25** (24 → 25)
- Twitch prefix: `!`
- Database migration: **none from Alpha 4**
- Player reset: **none**
- OAuth/environment changes: **none**
- New environment variables: **none**
- Gameplay/economy rebalance: **none**

Because the Portal action contract advances to protocol 25, **Beta 1 Web and Bot must be deployed together**.
