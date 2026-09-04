# Encounter Variety Audit — v1.7.1 Resynthesis Alpha 2 Hotfix 1

**Result: PASS**

## Root cause

The shipped region rarity tables were not making Magic Pot common. Across the eight normal Venture regions there are **101 encounter-table entries**, and Magic Pot carries a base weight of **1** in both regions where it appears.

The pathological streak came from the Solo Venture selector's hard lower level bound (`player level - 2`). When a player out-levelled most monsters in an older region, the preferred near-level pool could shrink to one monster even though many other valid monsters still existed below that narrow band.

The audit found **14 region/player-level states** where the old preferred Solo Venture pool contained exactly one monster while the region had alternatives. The most visible case was Whispering Caverns: at **Lv. 24–27**, Magic Pot became the only preferred candidate and therefore had an effective **100%** encounter rate.

Other old single-candidate windows included Spriggan, Garuda, Tonberry King, Brachosaur, Machea, and Omega Sentinel. This confirms the issue was systemic rather than Magic Pot-specific.

## Hotfix rules

- Base `data/regions.json` encounter weights remain unchanged.
- Solo Venture preserves its +5 enemy cap and stage difficulty bias.
- If the preferred Solo Venture band has fewer than **5** candidates and the region has more valid monsters, the selector widens to the closest valid monsters until it reaches five.
- Expeditions use the same minimum-candidate protection.
- Rally Venture, Solo Venture, and Expeditions share a per-player/per-region recent-encounter bias.
- An immediate repeat receives **10%** of its normal effective weight.
- If the same monster has appeared twice consecutively, a third consecutive roll receives **0 weight** whenever another valid candidate exists.
- With three or more candidates, one monster is capped to approximately **45%** of the effective roll weight.

## Magic Pot verification

For a Lv.25 Solo Venture in Whispering Caverns, the former pool was Magic Pot alone. Hotfix 1 expands the Stage 1 pool to five monsters. With no recent-history suppression applied, the effective Stage 1 shares are approximately:

- Black Flan: **31.3%**
- Piscodemon: **28.2%**
- Magic Pot: **19.0%**
- Mindflayer: **18.5%**
- Tonberry: **3.1%**

Stage 2 keeps Magic Pot around **27.4%**, and Stage 3 around **38.5%** before recent-repeat suppression. The global Solo Venture audit found no 3+-candidate state above approximately **45%** effective share after the new cap.

## Preserved balance

No monster level, XP, JP, Gil, item drop, treasure chance, region unlock level, Rally +10 cap, Solo +5 cap, Hunt table, Dungeon encounter, or boss encounter is changed by this hotfix. No database migration is required.
