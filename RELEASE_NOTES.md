# Crystal Guild v1.4.0 — Dungeons & Delves Alpha 3

## Dungeon Depth & Reward Identity

Alpha 3 builds on Alpha 2 with a third higher-level delve, route consequences that can carry into later chambers, and one-time first-clear rewards. The persistence, replay protection, stale-tab binding, retreat/defeat settlement, and existing economy outside Dungeons remain intact.

### The Whiteglass Bastion
- Adds a third persistent Dungeon: **The Whiteglass Bastion**.
- Unlock: character **Lv. 26** plus **45% Frostveil Reach** Expedition exploration.
- Recommended level: **30**.
- Nine chambers with two Crossroads decisions, a miniboss, sanctuary, and final boss.
- Dungeon identity: **Endurance & Wards**.

### Choices that echo forward
- Crossroads can now affect later rooms rather than resolving only immediately.
- Route effects can reduce the next hazard, strengthen or weaken the next foe, and boost the next combat payout.
- Active Dungeon state exposes pending route effects so the player can plan around them.
- Forward effects persist with the run, survive restart/reconnect, and are consumed only by the applicable later room.

### First-clear identity
- Each current Dungeon has a one-time first-clear bonus using existing XP, JP, Gil, and materials.
- First-clear eligibility is derived from the existing Dungeon progress record; no new table or migration is required.
- Dungeon cards identify their reward theme and show first-clear material rewards when unlocked.

### Payload and release hardening
- The high-frequency Adventure Board Hunt payload omits empty cooldown/reason fields, preserving the existing Web defaults while keeping an all-three-Dungeons-unlocked state below the 16 KiB transport guardrail.
- Restores the canonical `crystal_guild/token_store.py` module to the shipping Bot archive after it was omitted from the Alpha 2 archive. No token files or secrets are packaged.

### Compatibility
- Bot runtime: `1.4.0-dungeons-a3`
- Hosted Web runtime: `1.4.0-dungeons-a3`
- Frontend asset revision: `1.4.0-dungeons-a3`
- Local DB schema: **10** unchanged
- Hosted sync schema: **1** unchanged
- Portal Action protocol: **24** unchanged
- Twitch prefix: `!`
- Database migration: **none from Alpha 2**
- Player reset: **none**
- OAuth/environment changes: **none**
- Non-Dungeon gameplay/economy rebalance: **none**
