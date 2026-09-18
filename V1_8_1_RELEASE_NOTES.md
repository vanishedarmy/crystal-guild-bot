# Crystal Guild v1.8.1 — Merc Recruitment

v1.8.1 expands Hero Merc Service into a permanent recruitment system and includes a repair for Dungeon Portal actions.

## Merc Recruitment

- Adds **Auron, Vivi, Cecil, Terra, Tidus, and Ramza** to the Hero Merc roster.
- The original **Aerith, Tifa, Zidane, Yuna, Balthier, and Cloud** remain the founding roster and keep their existing progression unlocks.
- Expansion Heroes begin locked and must be permanently recruited before they can be hired for assignments.
- Auron, Vivi, Cecil, and Ramza use progression/quest recruitment requirements.
- Terra and Tidus use one-time Gil contracts after their required Character Level is reached.
- Permanent recruitment is separate from deployment: individual Hunt, Venture, and Raid contracts continue to spend the established **Hunt Seal** currency.
- The Portal adds **Hire Heroes**, **Recruitment**, and **Merc Registry** views.
- The Merc Registry tracks the full 12-Hero roster and uses silhouette artwork for unrecruited expansion Heroes.
- Expansion Heroes ship with dedicated **Locked**, **Available**, and **Unavailable** SNES/FF-style card artwork.

## New Hero specialties

- **Auron — Bushido:** heavy opening damage suited to elite and boss targets.
- **Vivi — Elemental Burst:** powerful opening magic damage.
- **Cecil — Paladin's Guard:** strong opening protection.
- **Terra — Arcane Burst:** high-powered magical opening damage.
- **Tidus — Quick Hit:** opening Haste and combat momentum.
- **Ramza — Shout:** coordinated offensive and defensive support.

## Dungeon Portal repair

The hosted Portal now preserves the authoritative room `revision` on `DUNGEON_ACTION`, `DUNGEON_CHOICE`, `DUNGEON_CONTINUE`, and `DUNGEON_RETREAT`. This fixes cases where Continue Deeper, Retreat, route choices, or combat actions were rejected by the Web gateway before reaching the Bot.

Existing active Dungeon runs do not need to be intentionally cleared for this repair.

## Release contract

- Runtime/frontend: `1.8.1-merc-recruitment`
- Frontend package: `1.8.1`
- Local database schema: **18**
- Hosted sync schema: **1**
- Portal Action protocol: **35**
- Existing schema-17 databases migrate automatically with a verified `pre_schema_18_<timestamp>.db` backup.
- No player reset.
