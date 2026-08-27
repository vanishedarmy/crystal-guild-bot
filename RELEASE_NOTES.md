# Crystal Guild v1.1.19 — Retro Phase III / Facility Supply Balance

This paired Bot + Web balance checkpoint removes Fellowship facility progression bottlenecks caused by materials that were previously tied to a single late-game monster or had no monster source at all.

## Facility supply rebalance

The six recurring Fellowship facility materials keep their existing item IDs and project requirements so active project progress is preserved. Instead of changing the projects, monster drop tables now provide multiple level-appropriate acquisition paths.

| Material | New / reinforced monster sources |
|---|---|
| Ancient Coin | Ossuary Knight Lv.10 12% · Mimic Lv.14 18% · Magic Pot Lv.25 24% · Ancient Mimic Lv.49 40% |
| Hi-Potion | Goblin Chieftain Lv.4 10% · Mimic Lv.14 26% · Tonberry Lv.16 16% |
| Mythril Ore | Spriggan Lv.11 12% · Gigas Lv.12 10% · Mimic Lv.14 16% · Iron Giant Lv.32 35% · Ancient Adamantoise Lv.60 80% |
| Wyvern Scale | Cockatrice Lv.7 10% · Basilisk Lv.12 12% · Sea Serpent Lv.25 16% · Red Dragon Lv.45 20% · Blue Dragon Lv.46 28% · Wyrm Lv.52 28% |
| Elemental Crystal | Flan Lv.5 10% · Bomb Lv.7 8% · Black Flan Lv.21 14% · Magic Pot Lv.25 18% · Crystal Wolf Lv.42 16% · Crystal Golem Lv.45 25% · Elemental Archon Lv.47 35% · Dark Element Lv.87 30% |
| Demon Horn | Imp Lv.5 10% · Gargoyle Lv.15 12% · Piscodemon Lv.20 14% · Abaddon Lv.64 30% · Archeodemon Lv.76 40% · Demonolith Lv.82 28% |

The early sources are intentionally modest rather than guaranteed. Higher-level thematic enemies remain more efficient farming targets, so progression becomes available early without erasing the value of later regions.

## Player Guide / Bestiary

The hosted Player Guide publishes the same updated drop tables as the authoritative Bot. Bestiary drop listings therefore show the new material sources and percentages instead of leaving players to discover an inaccessible requirement by trial and error.

## Compatibility

- Bot runtime: `1.1.19-retro-phase-iii-balance1`
- Hosted Web runtime: `1.1.19-retro-phase-iii`
- Frontend asset revision: `1.1.19-retro-phase-iii12`
- Local DB schema: **5** unchanged
- Hosted sync schema: **1** unchanged
- Portal Action protocol: **14** unchanged
- Twitch prefix: `!` unchanged
- Player reset: **none**
- OAuth / environment changes: **none**

Existing inventories, Fellowship facility tiers, active project progress, contributed materials, and all player progression are preserved.
