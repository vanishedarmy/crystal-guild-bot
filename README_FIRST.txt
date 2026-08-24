CRYSTAL GUILD v1.1.16 — ARSENAL HOTFIX 1
========================================

Upgrade baseline: v1.1.16 — Arsenal

Hotfix 1 changes Hunts into timed autonomous assignments:
- C = 5m, B = 15m, A = 30m, S = 1h, S+ = 2h;
- new Hunts do not use round-by-round Twitch chat combat;
- each player's Hunt persists independently and does not occupy the shared Active Battle slot;
- learned abilities, Defend, and limited survival consumables are chosen automatically at resolution;
- hard consumable limits prevent excessive automatic item use;
- Adventure Board shows Hunt countdown/progress and assignment duration;
- Portal, Streamer Dashboard, and Player Guide receive a readability/typography/overflow/mobile polish pass.

Runtime: 1.1.16-arsenal-h1
Frontend: 1.1.16-arsenal1h1
Local DB schema: 5 (unchanged)
Hosted sync schema: 1 (unchanged)
Hosted sync compatibility: 1.1.15-wayfarer (unchanged)
Portal Action protocol: 14 (unchanged)
Twitch prefix: !

PRESERVE: .env, .tio.tokens.json, crystal_guild.db, Twitch token database, and private deployment/runtime files.

This is a matching Bot + Web update. It runs NO database migration and requires NO player reset, new Render secret, or new OAuth scope.
