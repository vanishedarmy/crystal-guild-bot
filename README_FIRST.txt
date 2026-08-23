CRYSTAL GUILD v1.1.15 — WAYFARER HOTFIX 3
==========================================

Baseline: v1.1.15 — Wayfarer Hotfix 2

Hotfix 3 adds authoritative Adventurer Portal Title management:
- earned Titles can be equipped directly from Achievements & Titles → Title Collection;
- the currently equipped Title is clearly marked;
- locked Titles remain view-only;
- public/read-only profiles never receive Title mutation controls;
- the Bot re-validates that the requested Title is actually unlocked before applying it.

Runtime: 1.1.15-wayfarer-h3
Frontend: 1.1.15-wayfarer1h3
DB schema: 5 (unchanged)
Hosted sync schema: 1 (unchanged)
Hosted sync compatibility: 1.1.15-wayfarer
Portal Action protocol: 14
Twitch prefix: !

PRESERVE: .env, .tio.tokens.json, crystal_guild.db, Twitch token database, and private runtime state.

Hotfix 3 does NOT run a database migration and does NOT reset players. It does require matching Bot + Web files because Portal Action protocol advances 13 → 14.
