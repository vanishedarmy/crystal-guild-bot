# Validation Report — Crystal Guild v1.7.0 — Item Recovery Integrity Hotfix 1

**Result: PASS**

## Release contract

- Runtime/frontend revision: `1.7.0-emporium-annex-a3h1`
- Local DB schema: **15**
- Hosted sync schema: **1**
- Portal Action protocol: **31**
- Twitch command prefix: `!`
- Baseline: verified v1.7.0 Moogle Emporium Annex Alpha 3
- Artwork changes: **none**
- Restorative balance changes: **none**

## Automated regression

- Bot: **663 / 663 PASS**
- Frontend: **543 / 543 PASS**
- Hosted Web/API: **61 / 61 PASS**
- Bot Python parse: **116 / 116 PASS**
- Web Python parse: **15 / 15 PASS**
- JS/MJS syntax: **199 / 199 PASS**
- CSS structural checks: **8 / 8 PASS**
- WebP decode: **843 / 843 PASS**
- Public PNG count: **0**

The source-only Web package does not contain installed `node_modules`; therefore no local Vite production-build result is claimed.

## Restorative integrity audit

**PASS.** Canonical item data and the generated Web guide catalog agree exactly for every restorative item audited.

- Potion: **50 HP**
- Hi-Potion: **200 HP**
- Mega-Potion: **500 HP**
- X-Potion: **1,000 HP**
- Ether / Hi-Ether / Turbo Ether: **40% / 65% / 100% max MP**
- Stamina Draught / Warrior’s Tonic / Hero’s Brew: **40% / 65% / 100% max AP**
- Phoenix Down: **30% max HP revive**
- Tent: **full personal HP/MP/AP outside combat**
- Elixir: **full personal HP/MP/AP**
- Megalixir: **full HP/MP/AP for living Active Battle party members**

Direct resolver probes confirmed Mega-Potion restores a full **500 HP** when at least 500 HP is missing, and raid recovery independently restores the same 500 HP. The shared Active Battle resolver is also used by Solo Venture, Expedition, Dungeon and timed Hunt combat.

## Max-resource cap behavior

**PASS.** Healing and resource restoration never exceed maximum HP/MP/AP. The reported 59-HP Mega-Potion case is reproduced correctly when a hero is exactly 59 HP below maximum: the item retains 500-HP potency, 59 HP is effective, and 441 HP is prevented as overheal.

Recover & Equip now surfaces both values instead of presenting the effective amount as if it were the item’s potency. Capped field-use results likewise identify the nominal potency and the maximum-resource cap.

## Compatibility

No schema or protocol change is required. Existing progression, inventory, equipment, Gil, MGP, Fellowship, Emporium Annex, Retainer state, adventures and combat records remain compatible.
