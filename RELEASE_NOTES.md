# Crystal Guild v1.3.0 — Guild Expansion Alpha 3
## Guild Services & Workshop

Alpha 3 turns the major Guild facilities into practical day-to-day services while deliberately avoiding large combat-stat bonuses.

## Workshop refining
The Workshop now provides lossy material conversion so surplus common materials can be turned into harder-to-find crafting stock without replacing monster drops, Hunts, Expeditions, or the normal economy.

| Workshop | Service | Cost | Result |
|---|---|---|---|
| Lv. 2+ | Refine Mythril | 5 Iron Ore + 250 Gil | 1 Mythril Ore |
| Lv. 2+ | Temper Dragon Scale | 4 Wyvern Scales + 300 Gil | 1 Dragon Scale |
| Lv. 3 | Press Adamantite | 6 Mythril Ore + 750 Gil | 1 Adamantite |
| Lv. 3 | Condense Dark Matter | 10 Elemental Crystals + 1,000 Gil | 1 Dark Matter |

The existing Workshop forge-fee benefit remains in place: **-2% / -4% / -6%** at major Workshop Lv. 1 / 2 / 3. Refining supports batches while respecting owned materials and Gil. Portal exchanges are replay-safe, and all refining is blocked while the adventurer is committed to active combat or a persistent Adventure.

Players can use Workshop services from their own Portal Fellowship tab or through chat with `!workshop` and `!refine <service> [batches]`.

## Chocobo Stable training
The major Chocobo Stable now increases registered Chocobo XP whenever the companion earns XP:
- **Lv. 1:** +5%
- **Lv. 2:** +10%
- **Lv. 3:** +15%

This improves Bond progression without changing combat stats or replacing normal Chocobo activity.

## Guild Archive research
The Guild Archive now provides a small Expedition research benefit:
- **Lv. 1:** Guild records/Archive foundation
- **Lv. 2:** +0.5 percentage point rare Expedition event chance
- **Lv. 3:** +1.0 percentage point rare Expedition event chance

The bonus feeds the existing Expedition rare-event roll and remains subject to the normal rare-event ceiling.

## Fellowship presentation
- The public Fellowship page now includes a compact **Facility Services** summary.
- A signed-in player's Fellowship tab exposes unlocked Workshop refining services, owned material counts, batch controls, and service fees.
- The Player Guide explains the services in player-facing language.
- Alpha 1 facilities and Alpha 2 Construction, Supply Drives, Guild Objectives, and Weekly Order rewards remain intact.

## Portal compatibility
Alpha 3 adds the typed `WORKSHOP_EXCHANGE` Portal action, so Web and Bot advance together to Portal Action protocol **21**. No new environment variable, OAuth change, or database migration is required.

## Technical identity
- Bot runtime: `1.3.0-guild-expansion-a3`
- Hosted Web runtime: `1.3.0-guild-expansion-a3`
- Frontend asset revision: `1.3.0-guild-expansion-a3`
- Local DB schema: **8** unchanged
- Hosted sync schema: **1** unchanged
- Portal Action protocol: **21**
- Twitch prefix: `!` unchanged
- Database migration: **none**
- Player reset: **none**
- New environment variables: **none**
