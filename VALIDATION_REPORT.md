# Validation Report — Personalized Chat Results + Raid XP Boost

**PASS — final shipping archives validated after extraction.**

## Release contract
- Runtime/frontend: `1.7.1-resynthesis-a2h5`
- Local DB schema: **16**
- Hosted sync schema: **1**
- Portal Action protocol: **33**
- Twitch prefix: `!`
- New migration: **none**
- Player reset: **none**
- Required deployment from Contextual Quick Help: **Bot + Web together**

## Extracted shipping regression
- Bot: **709 / 709 PASS**
- Frontend: **620 / 620 PASS**
- Hosted Web/API: **76 / 76 PASS**

## Focused behavior coverage
- Two-player Rally Venture settlement emits one distinct `@username` result per participant.
- Raid completion through the normal `raid_round()` path preserves participant result payloads.
- Owner/admin Raid resolution preserves the same personalized settlement behavior.
- Twitch senders keep participant lines separate and pace them instead of packing them together.
- Venture personal lines carry contribution stats and personal rewards/spoils.
- Raid personal lines carry contribution stats plus personal XP/Gil/drop allocations.
- Defeat/wipe participants still receive contribution lines without victory spoils.
- All 37 configured Raid/Trial boss Victory XP values are increased by exactly **50%** in Bot and Portal data.
- Existing participation/contribution Raid allocation math remains unchanged.

## Package integrity
- Bot incremental patch reconstruction: **PASS**
- Web incremental patch reconstruction: **PASS**
- Full Bot tree match: **PASS**
- Full Web tree match: **PASS**
- Complete Bot tree match: **PASS**
- Complete Web tree match: **PASS**
- ZIP CRC/integrity checks: **PASS**

## Source / asset gates
- Bot Python AST: **124 / 124 PASS**
- Web Python AST: **16 / 16 PASS**
- Web JS/MJS syntax: **218 / 218 PASS**
- CSS structural checks: **9 / 9 PASS**
- Public WebP decode: **843 / 843 PASS**
- Public PNG count: **0**
