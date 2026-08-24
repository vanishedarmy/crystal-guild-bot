CRYSTAL GUILD v1.1.16 — ARSENAL
===============================

Upgrade baseline: v1.1.15 — Wayfarer Hotfix 3

Arsenal expands the combat/content curve:
- 18 Jobs × 6 active Battle Abilities = 108 abilities;
- active ability progression at JLv.1 / 8 / 15 / 22 / 30 / 40;
- richer elemental and special-effect identity;
- element/effect information on Job details, Player Guide, and Solo Venture ability selection;
- four new C-rank starter Hunts at Lv.2 / 4 / 6 / 8;
- four new early World Bosses at recommended Lv.6 / 10 / 14 / 18;
- eight new Lv.3–15 consumable crafting recipes;
- Arsenal featured in the Portal What's New panel.

Runtime: 1.1.16-arsenal
Frontend: 1.1.16-arsenal1
Local DB schema: 5 (unchanged)
Hosted sync schema: 1 (unchanged)
Hosted sync compatibility: 1.1.15-wayfarer (unchanged)
Portal Action protocol: 14 (unchanged)
Twitch prefix: !

PRESERVE: .env, .tio.tokens.json, crystal_guild.db, Twitch token database, and private runtime state.

Arsenal requires matching Bot + Web files but runs NO database migration and requires NO player reset, new Render secret, or new OAuth scope.
