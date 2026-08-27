# Crystal Guild v1.1.19 — Facility Supply Balance Validation Report

## Automated validation

- Bot unittest suite: **389 / 389 PASS**.
- Facility-material targeted regression tests: **5 / 5 PASS** within the full suite.
- Python source compile sweep: recorded in final package validation.

## Facility supply coverage

The recurring Fellowship facility materials were checked against the authoritative monster catalog.

| Material | Monster sources | Earliest source | Earliest rate |
|---|---:|---|---:|
| Ancient Coin | 4 | Ossuary Knight Lv.10 | 12% |
| Hi-Potion | 3 | Goblin Chieftain Lv.4 | 10% |
| Mythril Ore | 5 | Spriggan Lv.11 | 12% |
| Wyvern Scale | 6 | Cockatrice Lv.7 | 10% |
| Elemental Crystal | 8 | Flan Lv.5 | 10% |
| Demon Horn | 6 | Imp Lv.5 | 10% |

Targeted guards verify that:
- every recurring facility material has at least three monster sources;
- every recurring facility material has an early source at Lv.11 or below;
- the earliest source is not below a 10% practical drop rate;
- no configured facility drop exceeds the 80% upper balance bound;
- all facility material IDs still resolve to valid catalog items;
- project requirement item IDs were not changed, preserving active contribution progress.

## Compatibility

- Bot runtime: `1.1.19-retro-phase-iii-balance1`
- Local DB schema: **5** unchanged
- Hosted sync schema: **1** unchanged
- Hosted sync compatibility identity: `1.1.15-wayfarer` unchanged
- Portal Action protocol: **14** unchanged
- Twitch prefix: `!` unchanged
- Player reset: **none**
