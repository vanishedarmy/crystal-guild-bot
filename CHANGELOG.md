# v1.6.0 — Gold Saucer RC1
- Freezes the five-attraction Gold Saucer feature/economy set for release-candidate validation.
- Binds Monster Toss and Triple Triad daily entries to `started_at`, so active same-day sessions count immediately and midnight-crossing sessions remain charged to their entry day.
- Preserves schema 13, hosted sync 1, Portal protocol 29, MGP balances/economics, full Triple Triad card faces/values, and all prior Gold Saucer functionality.

# Crystal Guild v1.6.0 — Gold Saucer Alpha 5 Hotfix 5 — Triple Triad Full Card Face Sync
- Full Triple Triad card faces are now canonical presentation.
- Removes duplicate Web stat overlays and synchronizes five starter-card values to the printed faces.
- No schema, protocol, MGP, collection, or deck reset.

## v1.6.0 — Gold Saucer Alpha 5 — Triple Triad
- Opens persistent Triple Triad with a five-card starter deck, 15-card collection, three NPC tiers, five daily matches, MGP settlement, and collectible card rewards.
- Adds local schema 13 for persistent Triad profile/deck/records and active match state; hosted sync remains 1.
- Advances Portal Action protocol to 29 for `TRIAD_SET_DECK`, `TRIAD_START`, and `TRIAD_PLAY`.
- Adds Triad Tactician and Card Hall Master cosmetic titles and expands the Saucer records contract.
- Matching Web build makes all Gold Saucer content panels collapsible except Mini Cactpot and Crystal Slots.

## v1.6.0 — Gold Saucer Alpha 4 — Chocobo Racing
- Opens Chocobo Racing with the existing registered companion, three daily courses, three pace choices, MGP podium rewards, race records, and two cosmetic titles.
- Runtime `1.6.0-gold-saucer-a4`; schema 12 / hosted sync 1 / Portal protocol 28.

## v1.5.1 — Relic Arsenal Complete
- Completes Relic coverage for all 18 playable Jobs with 10 new three-stage questlines and 30 stage weapon items.
- Adds matching Relic artwork and 18-Job collection progress in the Portal and Player Guide.
- Keeps the Active Hunt scenic layer visible through Hunt resolution/result confirmation.
- Runtime `1.5.1-relic-arsenal-complete`; schema 10 / hosted sync 1 / Portal protocol 25 unchanged.

## v1.5.0 — Trails & Raids
- Promotes the validated RC1 feature set into the final production release.
- Adds production scenic backgrounds for Active Hunt and the collapsed/open Trial & Raid Board.
- Keeps Trial content, rewards, economy, combat, progression, schema 10, hosted sync 1, Portal protocol 25, OAuth, and environment requirements unchanged from RC1.

## v1.5.0 — Trails & Raids RC1
- Freezes the seven-Trial feature set and reward/economy model for release-candidate validation.
- Readiness counts and all-actions-ready checks now use the same exact Raid run + upcoming-round ownership rule as round resolution.
- Malformed/stale action stamps fail closed and fall back to the normal automatic Attack instead of breaking resolution or falsely showing ready.
- Preserves one-time compatibility for an unstamped queued action restored from pre-Beta-3 state.
- Refreshes current release/deployment metadata and the Bot control-panel identity; runtime `1.5.0-trails-raids-rc1`, schema 10 / hosted sync 1 / Portal protocol 25 unchanged.

## v1.5.0 — Trails & Raids Beta 3
- Serializes active Raid mutations against the newest committed runtime revision.
- Scopes queued Raid actions and timer ticks to an exact run/round.
- Preserves Beta 2 exactly-once settlement and accepts one restored unstamped Beta 2 action.
- Adds Round Readiness and richer Last Trial Result presentation through the matching Web build.

## v1.5.0 — Trails & Raids Beta 2
- Adds repeat-clear mastery milestones at 1/3/5/10 clears using the existing clear ledger.
- Retains Last Trial Result and live action-readiness presentation on the Trial & Raid Board.
- Adds exact Raid run identity plus bounded atomic settlement receipts to prevent duplicate rewards from stale/recovered Bot connections.
- Runtime `1.5.0-trails-raids-b2`; schema 10 / hosted sync 1 / Portal protocol 25 unchanged.

## v1.5.0 — Trails & Raids Beta 1
- Freezes the seven scripted Trials and adds Trial Chronicle & Personal Records.
- Existing Trial clears carry forward; new wipes, fastest clears, and contribution bests record through the existing generic record-stat store.
- Runtime `1.5.0-trails-raids-b1`; schema 10 / hosted sync 1 / Portal protocol 25 unchanged.

## v1.5.0 — Trails & Raids Alpha 7
- Bahamut — The Final Coil becomes the first capstone Trial.
- Flare Breath, Akh Morn, Megaflare Towers, and critical-HP Teraflare Charge add multi-phase coordination.
- The Trial Board gives Bahamut a full-width capstone card while preserving the roomy collapsible layout.
- Runtime `1.5.0-trails-raids-a7`; schema 10 / hosted sync 1 / Portal protocol 25 unchanged.

# Changelog

## v1.5.0 — Trails & Raids Alpha 6
- Leviathan — Tidebreak Expanse becomes the sixth flagship Trial.
- Tidal Sweep pressures one marked side and rewards individual Defend responses.
- Undertow adds target resource pressure and party splash when the marked raider does not brace.
- Maelstrom Surge creates a two-round Stability Gauge driven by coordinated Defends; Tidal Wave strength depends on the result.
- Alpha 5's roomy two-column Trial Board, collapse state, earlier Trials, rewards/economy, and four frozen Dungeons remain unchanged.
- Runtime `1.5.0-trails-raids-a6`; schema 10 / hosted sync 1 / Portal protocol 25 unchanged.

# Crystal Guild Changelog

## v1.5.0 — Trails & Raids Alpha 4
- Titan — Heart of the Crag becomes the fourth flagship Trial.
- Landslide uses the existing Defend action as a personal brace check; ignoring it causes knockdown pressure.
- Granite Gaol temporarily restrains one raider until normal boss-directed damage breaks the prison.
- Heart of the Crag creates a two-round damage check that weakens or empowers Earthen Fury.
- Existing Ifrit, Shiva, Ramuh, unscripted raids, and all four Dungeons remain unchanged.
- Runtime `1.5.0-trails-raids-a4`; schema 10 / hosted sync 1 / Portal protocol 25 unchanged.

## v1.5.0 — Trails & Raids Alpha 3
- Ramuh — Judgment Spire adds Rolling Thunder chain pressure, Levinshare stack-sharing, and a two-round Judgment Charge Grounding Gauge driven by existing Defend actions.
- Successful grounding weakens Judgment Bolt; missed grounding empowers the raidwide discharge.
- Adventure Board Trial & Raid Board is now collapsible with the canonical right-hand closed / down-hand open pointer and remembered state.
- Ifrit, Shiva, unscripted raids, rewards/economy, and the four production Dungeons remain unchanged.
- Runtime advances to `1.5.0-trails-raids-a3`; schema 10 / sync 1 / Portal protocol 25 remain unchanged.

## v1.5.0 — Trails & Raids Alpha 2
- Shiva — Diamond Throne adds encounter adds, Break/Stagger, cleave telegraphs, and role-aware contribution display.
- Schema 10 / sync 1 / protocol 25 unchanged; no reset or migration.

# v1.4.0 — Dungeons & Delves

- Promotes the RC1 feature set unchanged into the final v1.4.0 production release.
- Ships four persistent Dungeons with Crossroads, Events, route consequences, first-clear rewards, pressure encounters, and player-paced combat.
- Preserves exact run/chamber/revision stale-state binding, cross-connection SQLite serialization, action-ID replay idempotency, restart/reconnect persistence, and mobile Dungeon Board disclosure placement.
- Keeps local DB schema 10, hosted sync schema 1, Portal Action protocol 25, and Twitch prefix `!` unchanged from RC1.

# v1.4.0 — Dungeons & Delves RC1

- Freezes the four-Dungeon release candidate with no gameplay, reward, economy, schema, or protocol changes.
- Carries forward Beta 3 cross-connection serialization, exact run/chamber/revision stale-state binding, replay idempotency, and restart persistence.
- Cleans release identity/package metadata, removes generated overlay runtime state from shipping, and refreshes stale setup/deployment documentation.
- Re-runs upgrade/recovery/package reconstruction drills for RC deployment readiness.

# v1.4.0 — Dungeons & Delves Beta 1

- Feature-freezes Dungeons & Delves at four persistent delves.
- Binds every Dungeon Portal mutation to exact run + chamber + persisted revision so same-room stale tabs fail closed.
- Preserves action-ID replay safety and restart/reconnect persistence.
- Shows Round X / Limit for pressure encounters and reduces Adventure-state payload size.
- Keeps schema 10 / sync 1 unchanged; Portal Action protocol advances 24 → 25.

## v1.4.0 — Dungeons & Delves Alpha 4
- Added The Riftglass Observatory as the fourth persistent Dungeon.
- Added weighted Dungeon Event chambers and room-specific encounter rules/opening pressure.
- Expanded room outcomes with cache/resource/future-room effects while preserving restart-safe run state.
- Kept schema 10 / sync 1 / Portal protocol 24 unchanged and preserved the 16 KiB Adventure-state guardrail.

## v1.4.0 — Dungeons & Delves Alpha 3
- Adds The Whiteglass Bastion (Lv.26 + 45% Frostveil Reach), the third persistent Dungeon.
- Adds forward Crossroads effects for later hazards/combat and one-time first-clear bonuses.
- Keeps schema 10 / sync 1 / Portal protocol 24 unchanged.
- Keeps Adventure Board payload below its 16 KiB guardrail with all three Dungeons unlocked.

# Crystal Guild Changelog

## v1.4.0 — Dungeons & Delves Alpha 1
- Added the persistent Dungeon foundation and The Forgotten Ossuary proof dungeon.
- Added schema 10 Dungeon run/progress storage and Portal Action protocol 23.
- Added player-paced Dungeon combat, cache banking, retreat/defeat recovery, Bestiary integration, and Adventure Board UI.

## v1.3.1 — Asset Optimization
- Replaces 390 shipped PNG artwork assets with smaller lossless WebP equivalents after exact pixel/transparency verification.
- Reduces raw artwork by roughly 31.9 MiB with no gameplay, schema, protocol, or balance changes.
- Corrects stale current Web package/overlay version surfaces and adds asset-format regression coverage.

## v1.3.0 — Guild Expansion
- Final production release of the complete v1.3 Guild Expansion feature set.
- Public What's New history now lists shipped releases only; Alpha/Beta/RC entries remain only in engineering history.
- Promotes RC2 unchanged for gameplay/economy with final runtime `1.3.0-guild-expansion`; schema 9 / sync 1 / Portal protocol 22 remain unchanged.

## v1.3.0 — Guild Expansion RC2
- Final pre-release packaging and metadata hardening pass.
- Refreshes stale bundled finalization-audit headings and strengthens release-identity checks across Bot/Web package surfaces.
- Preserves RC1 gameplay, Beta 1 balance, Beta 2 UX, Beta 3 shared-state hardening, schema 9, sync schema 1, and Portal protocol 22 unchanged.

## v1.3.0 — Guild Expansion RC1
- Freezes the complete v1.3 Guild Expansion feature set for final release-candidate testing.
- Normalizes release identity, release-readiness assertions, and Player Guide major-facility terminology.
- Preserves Beta 1 balance, Beta 2 UX, Beta 3 shared-state hardening, schema 9, and Portal protocol 22 unchanged.

## v1.3.0 — Guild Expansion Beta 3
- Hardens simultaneous Fellowship contributions, project switching, Portal replay handling, and Airship launch/settlement.
- Binds Portal contributions to the project shown in the submitting tab; stale tabs fail closed after a project change.
- Advances Portal Action protocol 21 → 22; schema 9 and Beta 1 balance remain unchanged.

## v1.3.0 — Guild Expansion Beta 1
- Adds the fixed-seed Guild economy/progression simulator and 3,000-season balance report.
- Tunes Airship Dock, Airship construction, and rarity-aware Airship upgrade requirements.
- Keeps Weekly Order payouts, Supply Drives, Workshop refining, Fellowship thresholds, Legacy milestones, schema 9, and Portal protocol 21 unchanged.

# v1.3.0 — Guild Expansion Alpha 5

- Adds ten permanent Guild Legacy accomplishments with one-time replay-safe shared Renown rewards and named trophies.
- Adds Founding Hall → Bannered Hall → Hall of Heroes → Legendary Guild Hall progression.
- Expands personal Fellowship records with Expedition, Hunt, raid, Workshop and Airship service plus automatic distinctions.
- Adds `!legacy` / `!guildlegacy`.
- Keeps schema 9, hosted sync 1 and Portal Action protocol 21 unchanged.

# v1.3.0 — Guild Expansion Alpha 4

- Makes Airship Dock Lv. 1–3 part of the live Guild facility path and adds one-time Crystal Guild Airship construction.
- Adds six timed shared Airship Missions whose progress comes from Ventures, Hunts/combat, Expeditions, crafting/forging/treasure, and raids.
- Adds five Tier I–III Airship upgrade tracks: Hull, Engine, Cargo Hold, Survey Array, and Crystal Core.
- Adds `!airship` / `!guildairship` for shared status plus owner-only `!airshipmission <mission>`.
- Adds persistent Airship mission state, contributor tracking, mission history, return-time settlement, and replay-safe contributor rewards.
- Advances local DB schema **8 → 9** through an additive verified-backup migration; hosted sync schema 1 and Portal protocol 21 remain unchanged.

# v1.3.0 — Guild Expansion Alpha 3

- Adds Workshop material refining at major Workshop Lv. 2/3, with lossy conversion recipes and Gil service fees.
- Adds automatic Chocobo XP bonuses from major Chocobo Stable Lv. 1–3 (+5% / +10% / +15%).
- Adds small Guild Archive rare-Expedition-event bonuses at Lv. 2–3 (+0.5 / +1.0 percentage point).
- Adds Portal Fellowship Workshop controls plus `!workshop` / `!refine`.
- Advances Portal Action protocol **20 → 21** for typed `WORKSHOP_EXCHANGE`; schema 8 and sync schema 1 remain unchanged.

# v1.3.0 — Guild Expansion Alpha 2

- Adds Guild Projects II: Supply Drives and gameplay-driven Guild Objectives.
- Adds direct Weekly Fellowship Order contributor rewards and the full-week personal participation bonus.
- Adds completed-Expedition Fellowship activity tracking.
- Schema 8 / sync 1 / protocol 20 remain unchanged.

# v1.3.0 — Guild Expansion Alpha 1
- Added the five-facility Guild Hall Foundation board.
- Major facilities present as Lv. 0–3; Airship Dock is visible but locked.
- Preserved existing v1.2 support-facility tiers/benefits and contribution progression.
- Schema 8 / sync 1 / protocol 20 remain unchanged.

# Crystal Guild v1.2.0 — Expeditions

Crystal Guild v1.2.0 ships the full Expeditions system and promotes the RC1 feature set unchanged into the final release.

## Expeditions
- Five launch regions: Emerald Wilds, Ashen Highlands, Mistfen Marshes, Frostveil Reach, and the Astral Scar.
- Scout, Journey, Deep Expedition, Regional Boss Contract, and Legendary Contract routes.
- Safe / Unknown / Push Deeper route choices with distinct survival-versus-reward pressure.
- Persistent HP, MP, AP, inventory use, Expedition Cache, Journal, route state, and return/rescue behavior.
- Regional exploration milestones, permanent landmarks, Regional Bosses, Mastery rewards, Expedition Atlas ranks, and Master Cartographer progression.
- Region-specific encounters, hazards, resources, travelers, rare events, and discoveries.

## Chocobo expedition partnership
- Guardian, Scout, Pathfinder, Forager, and Treasure Hunter specialties derive from existing Chocobo traits.
- Specialty effects scale with Bond milestones.
- The Stable records shared Expedition accomplishments.
- Completed routes award restrained Hunt Seal stipends while Hunts remain the primary Hunt Seal activity.

## Player experience
- Adventure Board information is action-first and secondary progression can collapse.
- Detail cards open in the current viewport without moving the background page.
- Portrait-format scenic artwork fills long Solo Venture, Relics, Blacksmith, Chocobo Stable, and Moogle Emporium tabs.
- Mobile layouts, touch targets, keyboard navigation, focus handling, contrast support, reduced-motion support, and device safe areas have been polished.
- The Player Guide Expeditions chapter contains play and usage information only; development and release-engineering history is kept out of player instructions.

## Release hardening
- Persistent Solo/Expedition mutations and replay receipts commit atomically to prevent duplicate rewards after retries.
- Active persistent Adventures block Long Rest and stream-start resource refreshes until the run ends.
- Active Expeditions survive restart/reconnect and schema-7 → schema-8 migration preserves existing player progression.

## Compatibility
- Bot runtime: `1.2.0-expeditions`
- Hosted Web runtime: `1.2.0-expeditions`
- Frontend asset revision: `1.2.0-expeditions`
- Local DB schema: **8**
- Hosted sync schema: **1**
- Portal Action protocol: **20**
- Twitch prefix: `!`
- Player reset: **none**
- New environment variables: **none**
