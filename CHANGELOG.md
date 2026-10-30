# Crystal Guild v1.9.97.1 — Daily Resets, Regional Shops & Relic Quests

- Daily Guild Provisions now share Gold Saucer's 00:00 UTC calendar reset. Existing rolling 24-hour cooldowns are superseded by the daily settlement ledger, avoiding midnight lockouts and duplicate claims.
- Moogle Emporium shows every eligible regional consumable and a limited rotating selection of ordinary equipment. Added Turbo Ether, Hero's Brew, Panacea, and Shadow Gem to appropriate shop stock; restricted gear and rare Elixir/Megalixir stay exclusive. Twitch shop now pages results.
- Relic Arsenal gains Begin Relic Quest per Job, with server-validated matching Job and quest acceptance required before first new weapon-stage reward. Existing Relics and player equipment are preserved; subsequent Relic stages use the normal requirements. Ultimate quests additionally enforce level and Classic Zenith prerequisites.
- Portal action, guide, and What's New are updated. Preserves all v1.9.97 elite artwork.

---

# Crystal Guild v1.9.97 — Elite Hunts & World Events

- Six high-level Hunt assignments: three S+ (Character Lv.80, 86, 92) and three SS (Lv.95, 99, 99).
- Existing automatic personal Hunt simulation retained. S+ duration 5 hours; SS 6 hours. Lower ranks unchanged.
- Unlock rules use unique clears in prior rank; Hunt first-clears award existing material + new exclusive title. Repeat wins have a chance to award a bonus rare endgame material (30–50% by mark).
- Three new stream-only Elite World Event variants (eligible when highest Guild character reaches 80/85/95); normal variants remain available below that threshold. Shared event schedule and join flow unchanged.
- Elite event victories award an extra guaranteed themed rare item and use a 45% premium drop chance; normal World Events retain their previous 20% premium chance and 4x XP/3x JP/2x Gil calculation.
- Portal Hunt ranks and World Event roster, What's New, and public Player Guide updated. Guild Town and standalone Ascension Trials remain intact.
- Existing player data, titles, trophies, progress, old events and database schema remain unchanged. No original Web art should be deleted.

---

## v1.9.96 — Sovereign Encounters
- Three new six-room high-level Dungeons: Abyssal Foundry (Lv.65), Void Cathedral (Lv.85), Throne of Eternity (Lv.99). The existing Lv.55/75/95 Ascension Dungeons remain fully playable and now include advanced guardians.
- Advanced guardian combat in six Ascension Dungeons and JLv.75/90/99 Job Trials: phase shifts at 60% and 25% HP change elemental weaknesses/resistances and raise enemy pressure. Matching elemental attacks receive a 40% weakness bonus or 35% resistance penalty against these bosses; existing normal monster elemental logic is preserved.
- Telegraph heavy attacks before the acting hero chooses their next turn. Defend provides normal protection plus an additional special guard counter (40% reduced power) for the marked strike. Statuses (including stun) still interact with monster turns.
- Portal combat displays phase name, current elemental weaknesses/resistances and a prominent DEFEND warning. Public Player Guide and What's New now include this release. Existing player saves, Job Trials, Limit Break unlocks, equipment and item fixes remain intact; no SQL schema or protocol migration.
- Validation: dedicated advanced encounter regression suite and focused combat/Portal tests; production frontend compilation and live Twitch/Portal E2E require staging validation.

## v1.9.95 — Trials of Ascension
- Introduces 72 unique Job Ascension Trials (18 Jobs × JLv.60/75/90/99), using persistent Dungeon combat, guardian-seal objectives, job/character level gates, and prerequisite clears.
- First clears award XP/JP/Gil and high-level materials, milestone passives at 60/90/99, and permanent Job titles at 75/99. Existing JLv.50 Mastery and Limit Breaks are retained.
- Opens Forgotten Crystal Sanctum (Lv.55), Celestial Spire (Lv.75), and Astral Crucible (Lv.95), with route decisions and six-room progression.
- Portal Adventure Board shows current Job's trial path and live objective progress; Twitch `!ascension`, `!ascend`, `!trialaction`, `!trialretreat` work through the same authoritative game system. Player Guide and What's New updated.

## v1.9.94 — Battle & Rewards Hotfix
- More rewarding World Events (XP, JP, Gil, themed rare/premium loot), reliable `!revive` during group live combat, mobile enemy HP visibility and consumable effect audit.

## v1.9.91 — Equipment Expansion
- Integrated all 173 item illustrations (119 regular gear; 54 Ultimate forms) into Web and refreshed Player Guide. Gameplay catalogs and player state remain unchanged.

## v1.9.10 — Ultimate Relics and Equipment Beyond Lv.65

- Added 7 regular equipment tiers: Lv.70, 75, 80, 85, 90, 95, and crafted-only Lv.99 Paragon; 119 new equipment choices and 119 new recipes.
- Added 18 new Ultimate Relic lines, one per Job, with Lv.90/95/99 forms (54 new weapons).
- Ultimate starting objective requires the Job’s existing Zenith Relic, a mastered JLv.50 Job, and character Lv.90.
- Eternal completion requires an Eclipse Sovereign raid clear and final-world materials.
- Moogle Emporium and Twitch quick-buy use normal level and Job restrictions for new stock.
- Portal Relic Arsenal adds Classic and Ultimate filters; Ultimate visuals fall back to already existing Zenith artwork.
- No changes to stored equipment schema or existing Relic progression IDs.

## v1.9.8 Stream Mist Party Support — Ventures & Raids

Twitch `!healparty`/`!healparty 1` (100 Gil), `!healparty 2` (250 Gil),
`!healparty 3` (500 Gil), and `!healparty 4` (1,000 Gil) instantly apply
Mist Potion + Mist Ether, Mist Hi-Potion + Mist Ether,
Mist Mega-Potion + Mist Hi-Ether, or Mist X-Potion + Mist Hi-Ether,
respectively, across the **living active Venture or Raid party**.
Each joined player may sponsor one successful use **per Venture and per Raid**;
this resets with the next run. Costs are Gil-only; no owned items are consumed.
Insufficient funds, KO'd actors, unjoined users, full-health/full-MP parties,
and rally-only battles do not spend Gil or consume an allowance. Recovery and
charge are committed together in the persisted runtime state, protecting
restarts and multiple Bot connections. Raid support contributes to the
supporting hero's healing total. No Web changes or schema migration.

# v1.9.8 — Airship Expedition

The Crystal Guild Airship is now the Fellowship's shared unlock for individual remote Expeditions. The old 24–48-hour passive mission **launches are retired**; any mission already in flight can finish and settle using its original persisted rules, and mission history and construction/upgrades remain intact.

- Three Airship-only regions: **The Shattered Sky Isles** (Lv.25+, Crystal Core 0), **The Aetherstorm Expanse** (Lv.35+, Core 1), and **The Forgotten Dominion** (Lv.45+, Core 2). The original five Chocobo regions are unchanged.
- Three new regional bosses and three sky-exclusive salvage materials, with persistent regional exploration, milestones and boss contracts.
- Per-player Airship Expeditions reuse the regular Expedition persistence, routing, combat and rewards; a Chocobo is not required for flying. Multiple members may travel independently.
- Airship upgrades: Hull lowers hazards and improves rescue retention; Engine shortens travel; Cargo increases gathered materials; Survey improves rare-event odds and exploration gains; Crystal Core gates distant regions. Tiers are copied when a flight launches so mid-flight guild upgrades cannot change its conditions.
- Airship-specific events: aerial ambushes, aetherstorms, emergency landings and floating ruins.
- Twitch chat: `!airshipregions`, `!airshipexpedition <region_id> [scout|journey|deep|boss|legendary]`, `!airshipstage`, `!airshiproute [safe|unknown|deep]`, `!airshipcamp`, `!airshipreturn`, `!airshipattack`, `!airshipdefend`, `!airshipretreat`. Existing `!airship` reports Guild construction and unlocked destinations. `!airshipmission` is disabled.
- Portal Expedition Board has separate Chocobo and Guild Airship routes. Fellowship page focuses on upgrades and remote regions, while prior mission history stays visible.
- No database migration required; persistent schema remains **27**, hosted sync schema **1**, Portal Action protocol **39**.
- **v1.9.7 Quick Gear Twitch chat commands remain present** in the full Bot.

**Deployment:** Always back up live Bot/Web databases, volumes and configuration before updating. Merge `Bot/` and `Web/` source patch into the existing tree; keep all image assets and secrets unchanged. Restart Bot, and rebuild Web/frontend through the source-build Dockerfile or normal `npm ci && npm run build`. The static v1.9.7 `frontend/dist` is not a v1.9.8 UI build; do not deploy with `Dockerfile.prebuilt` until the new bundle has been compiled. Do not wipe either database.

---

# v1.9.7 — Queen’s Blood

48 approved card portraits, 14-opponent solo circuit, live and correspondence invitations, compact illustrated Card Hall, server clocks and reconnect handling. Existing progression and saved matches are preserved. See RELEASE_NOTES.md.

## v1.9.6 — Triple Triad Expanded

- Expand Triple Triad to 45 cards, ten opponents and five circuits, with gentler novice play and five dedicated UI sections.
- Integrate all thirty approved card faces; preserve the original fifteen cards, saved decks, records and active matches.
- Align Bot, hosted Web and Portal release labels; refresh Overview What's New and include rebuilt frontend output.
- Remove audited superseded static files and provide hash-checked incremental-install cleanup.
- Database schema 26, hosted sync 1 and Portal Action protocol 39 stay unchanged.

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
