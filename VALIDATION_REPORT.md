# Validation Report — Crystal Guild v1.7.0 — Item Usage Copy Hotfix 2

**Result: PASS**

## Release contract

- Runtime/frontend revision: `1.7.0-emporium-annex-a3h2`
- Local DB schema: **15**
- Hosted sync schema: **1**
- Portal Action protocol: **31**
- Twitch command prefix: `!`
- Baseline: Item Recovery Integrity Hotfix 1
- Item values changed: **no**

## Automated regression

- Bot: **664 / 664 PASS**
- Frontend: **544 / 544 PASS**
- Hosted Web/API: **61 / 61 PASS**
- Bot Python parse: **117 / 117 PASS**
- Web Python parse: **15 / 15 PASS**
- JS/MJS syntax: **200 / 200 PASS**
- CSS structural checks: **8 / 8 PASS**
- WebP decode: **843 / 843 PASS**
- Public PNG count: **0**

## Item-usage copy checks

**PASS.** Recover & Equip renders the declared item effect only through the shared item formatter. The UI contains no current-recovery preview line and no explanatory potency/cap note.

**PASS.** Field-use results report the amount/resource restored without technical cap wording or a trailing HP/MP/AP status snapshot.

**PASS.** The restorative-value regression remains intact: Potion **50 HP**, Hi-Potion **200 HP**, Mega-Potion **500 HP**, X-Potion **1,000 HP**, with the existing MP/AP percentage restoratives and revive/full-rest items unchanged.

No database migration, inventory rewrite, player reset, item rebalance, artwork change, or Moogle Emporium Annex behavior change is required.
