# Crystal Guild v1.3.0 — Guild Expansion Beta 1

## Guild Economy & Progression Balance

Beta 1 is the balance checkpoint for the v1.3 Fellowship/Airship expansion. It does not add a new gameplay system; it tunes the late Guild progression curve so the Airship arrives over meaningful weeks while Tier III remains a long-term goal.

### Airship Dock
- Lv. 1: 60,000 Gil · 25 Ancient Coins · 4 Guild raid wins · Fellowship LVL 7.
- Lv. 2: 100,000 Gil · 35 Ancient Coins · 6 Guild raid wins · Fellowship LVL 8.
- Lv. 3: 170,000 Gil · 55 Ancient Coins · 9 Guild raid wins · Fellowship LVL 9.

### Crystal Guild Airship construction
- 140,000 Gil
- 35 Mythril Ore
- 18 Wyvern Scales
- 20 Elemental Crystals
- 10 Ancient Coins
- 6 Guild raid wins
- Fellowship LVL 8

### Airship upgrade curve
Every upgrade tier now uses 25,000 / 55,000 / 95,000 Gil and 1 / 2 / 2 Guild raid wins. Material quantities are rarity-aware instead of one flat curve:
- Hull — Adamantite: 2 / 4 / 6
- Engine — Magitek Capacitors: 3 / 5 / 8
- Cargo Hold — Mythril Ore: 4 / 7 / 10
- Survey Array — Elemental Crystals: 4 / 7 / 10
- Crystal Core — Dark Matter: 2 / 4 / 6

### Intentionally unchanged
- Weekly Fellowship Order shared and personal rewards.
- Supply Drive and Guild Objective rewards.
- Workshop refining recipes and service fees.
- Fellowship LVL thresholds and personal Guild Rank thresholds.
- Guild Legacy accomplishment targets/rewards.
- Airship mission duration, progress, and reward formulas.

## Fixed-seed balance simulation
The shipping simulator runs 1,000 seasons each for Casual, Core, and Active Guild profiles — 3,000 total. In the conservative Core profile, the median timing is roughly 6.1 weeks to Fellowship LVL 8, 11.1 weeks to Airship Dock Lv. 1, 13.3 weeks to the completed Airship, 24.0 weeks to all five major facilities at Lv. 3, and 33.4 weeks to all Airship upgrade tracks at Tier III. Contribution Renown is intentionally excluded from the model, so real progression can be somewhat faster.

## Compatibility
- Bot/Web runtime: `1.3.0-guild-expansion-b1`
- Frontend asset revision: `1.3.0-guild-expansion-b1`
- Local DB schema: **9** unchanged
- Hosted sync schema: **1** unchanged
- Portal Action protocol: **21** unchanged
- Twitch prefix: `!`
- Database migration: **none**
- Player reset: **none**
- OAuth/environment changes: **none**
