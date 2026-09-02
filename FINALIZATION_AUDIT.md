# Finalization Audit — Crystal Guild v1.7.0 Moogle Emporium Annex Alpha 3 — Item Recovery Hotfix 1

**Decision: PASS — canonical Alpha 3 Hotfix 1 baseline.**

## Release contract

- Runtime/frontend: `1.7.0-emporium-annex-a3h1`
- Local database schema: **15**
- Hosted sync: **1**
- Portal Action protocol: **31**
- Prefix: `!`
- Baseline: verified v1.7.0 Moogle Emporium Annex Alpha 3

## Scope freeze

Hotfix 1 makes **no restorative balance changes**. It verifies and regression-locks the existing restorative contract and fixes the misleading Recover & Equip presentation that could show only effective missing-HP recovery (for example +59 HP) without also showing a Mega-Potion’s 500-HP potency.

Field-use messages now explain capped recovery, and the Portal displays declared potency alongside **Effective now** recovery. The Moogle Emporium Annex, Retainer Service, Gold Saucer and all other gameplay remain unchanged.

## Regression gates

- Bot: **663/663 PASS**
- Frontend: **543/543 PASS**
- Hosted Web/API: **61/61 PASS**
- Python parse: **131/131 PASS** (116 Bot + 15 Web)
- JS/MJS syntax: **199/199 PASS**
- CSS structural checks: **8/8 PASS**
- WebP decode: **843/843 PASS**
- Public PNG count: **0**

## Restorative contract

Fixed HP potencies remain 50 / 200 / 500 / 1,000. MP and AP restorative tiers remain 40% / 65% / 100%. Phoenix Down remains 30% max-HP revival. Tent, Elixir and Megalixir retain their existing full-restoration behavior. Maximum-resource capping is intentional and is now explicit in player-facing output.

## Upgrade safety

Schema 15 and Portal protocol 31 are unchanged. No migration, reset, item conversion, inventory mutation or new persisted state is introduced.
