## v1.9.4 — Crafting Reforged

- Expand the recipe catalog from 26 to 183, adding 157 recipes spanning field items, weapons, armor, and accessories; original recipes and earned discoveries remain intact.
- Rebuild the signed-in Crafting Workbench with category filters, ingredient search, source hints, batch previews, favorite recipes, compact/comfortable text, high contrast, keyboard support, and phone-friendly layout.
- Keep server-authoritative, replay-safe inventory spending and the existing 20-batch cap. Equipped last copies are reserved from crafting consumption.
- Preserve the existing Forge, resynthesis and 1.9.3 Guild Initiatives systems. Legacy Portal clients continue receiving the original small recipe payload; only the new Workbench requests the expanded catalog.
- Update Guide recipe data and release labels. No schema or Portal Action protocol migration is required (schema 26, protocol 39).
- Source-only merge: Web/frontend must be rebuilt with `npm ci && npm run build` after applying.

## v1.9.3 — Guild Initiatives

- Shared, verified objective accounting on Fellowship event receipts, with unique payout records, bounded progress storage and schema 26 migration with verified backup.
- Three independently rotating weekly Fellowship Contracts, with contribution reports and one-time guild-wide rewards for the membership present at completion.
- Three daily and three weekly optional personal Guild Board objectives; earned Gil/material rewards and occasional level-suitable shop equipment (Mythril Ore fallback).
- Hosted Web Guild Board player module, public Fellowship Contracts cards, mobile styling, release identity/cache revision and Player Guide update.
- Existing Trading Post, Relic Arsenal and What's New hotfixes retained. Source-only merge; rebuild Web/frontend after applying.

# Changelog

## v1.9.0 Alpha 13 — Trading Post QoL
Character-saved 30-item watchlist, completed-sales 30-day weighted-price history, owned counts while browsing, price context after at least three sales, and a stock- and fee-checked quick relist. Schema 25 / Portal protocol 39.

## v1.9.0 Alpha 12 — Camp & Recovery
- Trail Rations: purchasable or craftable one-run +10% Solo Venture damage, 45-minute departure timer, once-only consumption.
- One saved free pre-Venture plan: scout (+10% XP/JP), gear check (+8% damage), or supplies (+10% post-combat HP/MP/AP).
- Camp interface offers direct Potion/Tent recovery and retains original timed Camp. No new equipment durability.
- Local schema 24 with verified backup, hosted sync 1 unchanged, Portal Action protocol 38; matching Bot/Web releases, Player Guide and tests updated.

## v1.9.0 Alpha 11 — Mobile Combat HUD
- Mobile-only presentation hardening: viewport-anchored quick combat actions and dynamically measured Ability/Item drawers across Solo Ventures, Dungeons, Expeditions, stream Ventures, Raids and World Events.
- Live HP/resource readouts and existing authoritative action callbacks are unchanged; no combat balance, player records, schema, hosted sync or Portal Action protocol changes.
- Previous Alpha 10 Records & Moments features and all artwork carry forward.

## v1.9.0 Alpha 10 — Records & Moments

- Expanded Personal Records and 12 once-only Moments, seven secret Titles, two Hall trophies and 16 individually packaged game images.
- Persisted schema 23 achievement/event receipts with replay protection and verified historical backfill.
- Spoiler-safe hosted/Portal projection, discovery notifications, responsive Records UI and new Player Guide chapter.
- Existing Bestiary, career/Trial records, trophy ownership and previous gameplay progression are preserved.

# Crystal Guild — Release History (Condensed)

Only major release milestones appear here. Historical hotfix reports and obsolete per-version audits are omitted from deployable source packages; original released archives remain available separately.

## v1.9.0 Alpha 9 — Bestiary Discovery
164 scoped Bestiary records, research stages and one-time permanent core mastery rewards; schema **22**, no sync/protocol change. Five standalone Expedition boss portraits and responsive research UI.

## v1.9.0 Alpha 8 — Seasonal Event Framework
Reusable, initially disabled event editions and the first Halloween event, **Night of the Hollow Crystal**. Four seasonal monsters, Hollow Warden World Event, Moonlit Tokens, daily objectives, temporary shop, and four permanent trophies. Schema **21**; Portal Action protocol **37**.

## v1.9.0 Alpha 7 — Hall of Trophies
30 permanent trophies, artwork and participant/contributor-aware reconciliation; schema **20**.

## v1.9.0 Alphas 1–6
Moogle Trading Post and economy adjustments; Titles/navigation improvements; World Events and mobile combat controls. Schema **19**.

## v1.8.0–1.8.2 — Merc Service
Hero Mercs, recruitment and Elite Merc roster; schema **17–18**.

## v1.7.0–1.7.1
Moogle Retainer, Moogle Emporium Annex, Gold Saucer refinements and Gear Resynthesis.

## Alpha 8 package cleanup Hotfix 1
Documentation/duplicate-asset maintenance only: consolidated release history, corrected current setup guides and removed retired Triple Triad asset generations. **Runtime, schema, protocol, rewards and gameplay remain unchanged.**
