# Crystal Guild Changelog

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
