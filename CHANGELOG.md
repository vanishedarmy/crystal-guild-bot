# v1.2.0 — Expeditions Alpha 2
- Adds five regional objective chains with 25/50/75/100% exploration milestones.
- Unlocks dedicated Regional Boss Contracts at 75% exploration: Elder Ochu, Inferno Drake, Malboro Sovereign, Frost Behemoth, and Rift Wyrm.
- Adds rare regional encounters at advanced exploration, persistent boss clears, guaranteed boss materials, and 100% Region Mastery.
- Adds five Region Mastery achievements/titles and modest region-specific Expedition bonuses.
- Adds LIVE-only Portal milestone announcements for major discoveries, Mastery, and Regional Boss victories.
- Keeps local DB schema 8, hosted sync schema 1, and Portal Action protocol 20 unchanged.

# Crystal Guild Changelog

## v1.2.0 — Expeditions Alpha 1

- Launches five persistent Chocobo-led Expedition regions with Scout, Journey, and Deep route depths.
- Adds authoritative multi-stage travel, route decisions, combat, treasure/resources/hazards/discoveries, internal Expedition Camp, carried cache, safe return, Chocobo rescue, and region exploration progress.
- Adds schema **7 → 8** migration with `player_expeditions` and `player_region_exploration`, preserving all existing progression behind a verified pre-migration backup.
- Adds seven typed Expedition Portal actions and advances Portal Action protocol **19 → 20**; hosted sync schema remains **1**.
- Locks equipment/Job/Mastery/stance/normal Camp and conflicting adventures while an Expedition is active.
- Extends streamer `!clearadventures` / Portal Clear Adventures to abandon active v1.2 Expeditions without deleting secured region progress.
- Keeps H9 Venture/Raid timing, LIVE field support, Streamer Inventory Admin, persistent Adventure results, dynamic Camp, Relic visuals, and overlay behavior intact.

## v1.1.17 — Arsenal II Hotfix 4

- Rebalances Solo Venture stages to **80% Encounter / 20% Treasure**, reducing the chance that multi-stage runs are dominated by chests while preserving deeper-stage chest quality.
- Publishes structured Hunt resolution summaries with rewards, combat totals, post-Hunt vitals, first-clear information, and timed-Hunt auto-plan usage for the Portal.
- Reworks the Portal Hunt result presentation and removes duplicated Solo/Rally/region information where the same state is already visible.
- Compacts shared action-status areas and increases secondary-text/high-contrast accessibility without hiding functional state.
- Advances Bot/Web runtime to `1.1.17-arsenal-ii-h4` and frontend asset revision to `1.1.17-arsenal-ii1h4`.
- Keeps DB schema 5, hosted sync schema 1, Portal Action protocol 14, Twitch prefix `!`, player data, OAuth scopes, and environment requirements unchanged.

## v1.1.17 — Arsenal II
- Expands Active Battle abilities from 108 to 172; seven core caster Jobs now use a 12-step JLv curve and every other Job gains JLv.12/JLv.35 techniques.
- Reorganizes Moogle Emporium into Buy/Sell plus Weapons/Armor/Items categories and clarifies Blacksmith Recipes/Forge Gear views.
- Adds Camp & Recovery to the Adventure Board and compacts the mobile Portal masthead while preserving scroll-away behavior.
- Moves Hosted Raid Overlay help to the bottom of the Streamer Dashboard.
- Suppresses autonomous Twitch action/result announcements whenever stream status is OFFLINE or UNKNOWN; Portal gameplay continues normally.
- Runtime `1.1.17-arsenal-ii`; frontend `1.1.17-arsenal-ii1h2`; schema 5, hosted sync 1, Portal protocol 14 unchanged.

## v1.1.16 — Arsenal Hotfix 6

- Restricts randomized Daily Guild Provisions to an explicit opt-in catalog of ordinary consumables and approved crafting materials.
- Excludes Chocobo Registration Writs and other special/progression items from Daily rewards.
- Repairs orphaned Writ inventory created by the old Daily pool when no authoritative Stable purchase/timer row exists; legitimate purchased Writs are preserved.
- Adds regression coverage proving low-value/common future special materials cannot enter the Daily pool implicitly.
- Preserves subscriber-tier bonuses, randomized quantities, 24-hour cooldowns, schema 5, hosted sync schema 1, and Portal protocol 14.
- Advances Bot runtime to `1.1.16-arsenal-h6`; Hotfix 5 Web/frontend remains unchanged.

## v1.1.16 — Arsenal Hotfix 4

- Adds streamer-only `!clearadventures` (`!clearventures` alias) as an authoritative recovery command for orphaned adventure state.
- Clears the shared field/Rally encounter, all timed Hunt assignments, and all persisted Solo Ventures in one atomic Bot-side operation.
- Preserves raids/world bosses, player progression, inventory, persisted vitals, cooldowns, camps, shops, achievements, and Titles.
- Wakes hosted Portal sync immediately after the command so recovered state is published promptly.
- Advances Bot/Web runtime to `1.1.16-arsenal-h4` and frontend asset revision to `1.1.16-arsenal1h4`; schema 5 and Portal protocol 14 remain unchanged.

## v1.1.16 — Arsenal Hotfix 1

- Rebuilds Hunts as per-player persisted timed assignments: C 15m, B 30m, A 2h, S 5h (S+ currently inherits the S timer until marks are introduced).
- Removes round-by-round Twitch chat interaction from newly accepted Hunts; the daemon resolves them independently at the rank deadline and publishes only the final outcome.
- Keeps timed Hunts outside the shared Active Battle slot so several heroes can Hunt concurrently without blocking Rally Ventures or Raids.
- Adds conservative automatic ability, Defend, healing/cleanse, and resource-use decisions with hard consumable ceilings by rank.
- Adds Adventure Board Hunt countdown/progress/duration presentation and updates player-facing Hunt guidance.
- Applies readability, typography, wrapping, focus, mobile-target, and overflow polish across Portal, Streamer Dashboard, and Player Guide.
- Advances runtime to `1.1.16-arsenal-h1` and frontend asset revision to `1.1.16-arsenal1h1`.
- Keeps DB schema 5, hosted sync schema 1, hosted sync compatibility `1.1.15-wayfarer`, Portal Action protocol 14, and Twitch prefix `!` unchanged.

## v1.1.16 — Arsenal

- Expands every Job to six active Battle Abilities across JLv.1, 8, 15, 22, 30, and 40 for 108 total abilities.
- Adds stronger elemental and special-effect identity using existing Fire/Ice/Lightning/Wind/Water/Holy/Dark and status/resource mechanics.
- Surfaces ability element/effect traits in Job details, Player Guide, and interactive Solo Venture ability selection.
- Adds four C-rank starter Hunts at Lv.2/4/6/8 with new marks, enemy behaviors, rewards, and first-clear Titles.
- Adds four early World Bosses at recommended Lv.6/10/14/18 before Bomb King.
- Adds eight Lv.3–15 consumable-focused crafting recipes.
- Keeps DB schema 5, hosted sync schema 1, hosted sync compatibility `1.1.15-wayfarer`, Portal Action protocol 14, and Twitch prefix `!` unchanged.
- Runtime `1.1.16-arsenal`; frontend asset revision `1.1.16-arsenal1`.
- Requires no database migration, player reset, new Render secret, or new OAuth scope.

## v1.1.15 — Wayfarer Hotfix 3

- Adds authenticated Portal Title equipping for earned Titles.
- Adds strict `SET_TITLE` action validation and authoritative Bot-side unlock revalidation.
- Advances Bot runtime to `1.1.15-wayfarer-h3` and Portal Action protocol **13 → 14**.
- Keeps local DB schema 5, hosted sync schema 1, hosted sync compatibility `1.1.15-wayfarer`, and Twitch prefix `!` unchanged.
- Requires no migration, reset, new secret, or new OAuth scope.

## v1.1.15 — Wayfarer

- Rebuilds Portal-only Solo Venture as a persistent, player-paced three-stage run with Attack, Ability, Use Item, Defend, enemy intent, and no round timer.
- Changes Solo Venture stage odds to **60% Encounter / 40% Treasure**.
- Adds Return / Press On decisions after Stage I and II; encounter reward modifiers increase to +15% at Stage II and +30% at Stage III, while deeper chests receive better rarity weighting.
- Secures encounter XP/JP immediately while holding normal Gil/item spoils until banked; defeat recovers 50% pending Gil and loses loose items, while Retreat abandons pending spoils.
- Keeps Solo Venture state per player so an unattended Portal fight cannot occupy the Guild-wide Rally/Hunt battle slot.
- Reorders Adventurer Portal tabs with Overview first and Adventure Board second, followed by Jobs and Equipment & Inventory.
- Advances local DB schema **4 → 5** with a verified `pre_schema_5_<timestamp>.db` backup before migration.
- Advances Portal Action protocol **12 → 13** for strict typed Solo Venture round/continue/return/retreat actions; hosted sync schema remains 1.
- Runtime: `1.1.15-wayfarer`; frontend asset revision: `1.1.15-wayfarer1`; Twitch prefix remains `!`.

## v1.1.14 — Cloud Continuity — Hotfix 3c

- Adds an at-a-glance Current Loadout summary and stronger equipped-item treatment in the Portal.
- Corrects transaction-derived achievement metrics so `gil_spent` reflects lifetime ledger spending.
- Runs achievement checks immediately after shop purchases, Chocobo Writ purchases, and Fellowship contributions.
- Adds mobile header auto-hide on downward scroll and immediate restore on upward scroll.
- Advances Bot/Web runtime to `1.1.14-cloud-continuity-h3c` and frontend revision to `1.1.14-continuity3c`; DB schema 4, hosted sync schema 1, Portal Action protocol 12, hosted sync compatibility, and Twitch prefix `!` remain unchanged.

## v1.1.14 — Cloud Continuity Hotfix 3

- Restores explicit Raid round actions: `!attack`, `!ability`, `!defend`, and `!use` now queue and resolve for Raid participants; no input still defaults to Attack.
- Applies normal Raid MP/AP costs, item consumption, healing/status effects, Defend mitigation/resource restoration, and winning-round resource persistence.
- Hydrates recovered pre-Hotfix-3 active Raid runtime state without a database migration.
- Embeds live Rally Venture encounter information inside the existing Rally Venture panel instead of rendering a duplicate Active Battle card below Current Region.
- Adds a Portal selectable-control readability/intent pass and updates the Raid Player Guide.
- Advances Bot/Web runtime to `1.1.14-cloud-continuity-h3` and frontend revision to `1.1.14-continuity3`; DB schema 4, hosted sync schema 1, Portal Action protocol 12, hosted snapshot version, and Twitch prefix `!` remain unchanged.

## v1.1.14 — Cloud Continuity Hotfix 2

- Replaces the fixed `Gil + 1 Potion` Daily with randomized level-appropriate provisions plus level-scaled Gil.
- Adds broadcaster-authoritative Twitch subscription-tier lookup using `channel:read:subscriptions`.
- Adds initial Tier 1/2/3 Daily perks and public `!substatus` diagnostics.
- Portal Daily uses the same authoritative tier resolver and 24-hour cooldown as Twitch chat.
- Runtime advances to `1.1.14-cloud-continuity-h2`; DB schema 4, hosted sync schema 1, Portal Action protocol 12, and Twitch prefix `!` remain unchanged.

# v1.1.14 — Cloud Continuity Hotfix 1

- Adds Twitch stream-presence verification using the existing Twitch application credentials and the Get Streams API.
- Gates Twitch Rally Venture, Rally joins, Active Hunt starts, Active Battle actions, and Raid participation/actions to confirmed LIVE stream state.
- Keeps read-only commands, non-stream progression, Portal Solo Venture, and Portal Challenge Hunt available while offline.
- Adds streamer-only `!streamstatus` and includes stream presence in `!health`.
- Uses a short cached status check and fails closed to UNKNOWN after a stale Twitch/API failure.
- Runtime advances to `1.1.14-cloud-continuity-h1`; hosted sync version, DB schema 4, sync schema 1, Portal Action protocol 12, and Twitch prefix `!` remain unchanged.

# Crystal Guild Changelog

## v1.1.14 — Cloud Continuity

- Adds heartbeat self-healing for Fellowship after hosted Web restarts.
- Adds sanitized hosted OBS raid-overlay synchronization and `/overlay` Web companion support.
- Includes Render disk Blueprint compatibility and Python 3.11 Records-string fixes discovered during the v1.1.13 cloud rollout.
- Advances runtime identity to `1.1.14-cloud-continuity`; DB schema 4, hosted sync schema 1, Portal Action protocol 12, gameplay balance, and Twitch prefix `!` are unchanged.

## v1.1.13 — Cloud Runtime

- Adds an optional Render Background Worker runtime with a persistent `/var/data` disk while preserving local Windows operation.
- Adds durable SQLite-backed TwitchIO token storage and safe import of existing `.tio.tokens.json` credentials.
- Adds `prepare_render_migration.py` for consistent private copies of the authoritative player DB and token DB.
- Adds a fail-closed cloud bootstrap guard so a first Render deploy cannot accidentally create an empty authoritative Guild.
- Runs sanitized Portal sync in-process with the Bot in cloud mode; the local standalone sync launcher remains supported.
- Adds persistent cloud logs, rotating startup DB backups, cloud preflight checks, and graceful SIGTERM shutdown.
- Advances runtime identity to `1.1.13-cloud-runtime`. DB schema 4, hosted sync schema 1, Portal Action protocol 12, gameplay balance, and Twitch prefix `!` are unchanged.
- Existing v1.1.12 Adventure Board Web Hotfix 7 remains compatible.

# Changelog

## v1.1.12 — Adventure Board — Hotfix 3

- Moves locked Job **LOCKED** status into the upper-right card header and removes duplicated lock state from the Job body copy.
- Places Current and Mastered Job status in the same header-status group for consistent scanning.
- Keeps locked Job text at full readable contrast while preserving disabled controls and explicit unlock requirements.
- Renames the expandable Job requirement row to **How to unlock**.
- Moves Region Current / Unlocked / Locked status to the upper-right card header, separate from Travel actions.
- Adds responsive card-grid and action-stack rules across desktop, tablet, mobile, and narrow-phone widths for Jobs, Regions, Hunts, Fellowship Facilities/Orders, and character summary cards.
- Preserves Hotfix 2's embedded Solo Venture result UX and mobile LIVE/OFFLINE token.
- Keeps gameplay, DB schema 4, hosted sync schema 1, and Portal Action protocol 12 unchanged.
- Advances runtime identity to `1.1.12-adventure-board-h3` and frontend asset revision to `1.1.12-adventure2h3`.
- Requires no migration, reset, environment-variable change, or OAuth reconfiguration.

## v1.1.12 — Adventure Board — Hotfix 2

- Replaces the generic Portal `Solo Venture resolved.` completion line with an outcome-specific summary for Victory, Treasure, or Defeat.
- Embeds the complete **Last Solo Venture** result inside the Solo Venture panel, reducing page-level card clutter.
- Keeps the structured result breakdown for rounds, rewards, Fellowship Renown, HP, combat totals, loot, progression notes, and cooldown.
- Adds a compact mobile **LIVE/OFFLINE** connection token using the existing Portal heartbeat/live-update state; no second polling loop is added.
- Treats confirmed polling as LIVE and unconfirmed/connecting/error/offline states as OFFLINE on the compact mobile token.
- Keeps Solo Venture gameplay, Rally Venture gameplay, DB schema 4, hosted sync schema 1, and Portal Action protocol 12 unchanged.
- Advances runtime identity to `1.1.12-adventure-board-h2` and frontend asset revision to `1.1.12-adventure2h2`.
- Requires no player reset, migration, environment-variable change, or OAuth reconfiguration.

## v1.1.12 — Adventure Board — Hotfix 1

- Changes Portal-only Solo Venture Encounters from timed autonomous Active Battle to **immediate one-click resolution** inside the Portal request.
- Reuses the existing authoritative combat/reward engine and default no-input action; no second combat system is introduced.
- Clears Solo Encounter state before the Portal action completes, so no Solo round timer or encounter-scheduler wake is required.
- Adds structured Solo result data for Encounter and Treasure outcomes, including rewards, remaining HP, combat totals, loot/level-ups, Fellowship Renown, and cooldown context.
- Adds a dedicated responsive **Solo Venture Result** card on the Adventure Board for readable at-a-glance results.
- Keeps Solo Venture at 50/50 Encounter/Treasure, +3 enemy cap, 7-minute separate cooldown, no rally, 4 Fellowship Renown, and no Twitch output.
- Keeps Rally Venture Twitch-only and otherwise unchanged.
- Keeps local DB schema 4, hosted sync schema 1, and Portal Action protocol 12 unchanged.
- Advances runtime identity to `1.1.12-adventure-board-h1` and frontend asset revision to `1.1.12-adventure2h1`.
- Requires no migration, reset, environment-variable change, or OAuth reconfiguration.

## v1.1.12 — Adventure Board

- Reorders the Adventurer Portal Adventure Board so Solo Venture appears before Rally Venture information and region travel.
- Removes normal/Rally Venture start and rally-join controls from the Portal; Rally Ventures are now Twitch-chat only through `!venture` and `!join`.
- Advances Portal Action protocol 11 → 12 by removing `VENTURE` and `JOIN_ENCOUNTER` from the hosted/worker action contract.
- Keeps Solo Venture Portal-only at 50/50 Encounter/Treasure, +3 enemy cap, separate 7-minute cooldown, no rally, 4 Fellowship Renown, and no automatic Twitch chat output.
- Keeps Rally Venture at 70/30 Encounter/Treasure and a +10 enemy ceiling.
- Adds a Rally risk reward to encounter victories: +5% XP, JP, and Gil per enemy level above each participant, capped at +50%; treasure rewards are unchanged.
- Adds a website wording pass that replaces unnecessary implementation terminology with clearer player-facing language while preserving established game terms.
- Keeps local DB schema 4 and hosted sync schema 1; no migration or reset is required.

# Crystal Guild Changelog

## v1.1.11 — Solo Venture — Hotfix 2

- Keeps **Solo Venture completely silent in automatic Twitch chat output**.
- Removes the post-ack Twitch notification bridge for Solo Venture start/treasure/encounter results while retaining it for regular Portal Venture, Recruit, joins, and Hunts.
- Suppresses autonomous Twitch publishing for `kind=solo_venture` Active Battle rounds and final results; the existing scheduler still advances combat normally.
- Updates the Adventure Board and Player Guide to explain that Solo Venture remains Portal-side.
- Keeps Hotfix 1 balance unchanged: regular Venture is 70/30 with a +10 enemy cap; Solo Venture is 50/50 with a +3 cap, 7-minute cooldown, no rally, and 4 Fellowship Renown.
- Keeps local DB schema 4, hosted sync schema 1, Portal Action protocol 11, and prefix `!` unchanged.
- Advances runtime identity to `1.1.11-solo-venture-h2` and frontend asset revision to `1.1.11-solo1h2`.
- Requires no migration, player reset, environment-variable change, or OAuth reconfiguration.

## v1.1.11 — Solo Venture — Hotfix 1

- Raises the normal shared Venture encounter ceiling from **player level +5 to +10** to increase live-stream risk.
- Keeps normal Venture at **70% ENCOUNTER / 30% TREASURE**, with its existing cooldown and channel-wide rally.
- Changes Portal-only Solo Venture from **60/40 to 50/50 ENCOUNTER/TREASURE**.
- Keeps Solo Venture at **+3 enemy cap**, separate 7-minute cooldown, no rally, and 4 Fellowship Renown.
- Keeps local DB schema **4**, hosted sync schema **1**, and Portal Action protocol **11** unchanged.
- Advances runtime identity to `1.1.11-solo-venture-h1` and frontend asset revision to `1.1.11-solo1h1`.
- Requires no migration, reset, new environment variables, or OAuth changes.

## v1.1.11 — Solo Venture

- Adds **Solo Venture** exclusively to the authenticated Adventurer Portal Adventure Board; no Twitch `!solo` command is introduced.
- Uses a separate **7-minute** Solo Venture cooldown; normal Venture remains on its existing cooldown and is not consumed by Solo Venture.
- Initial v1.1.11 balance shipped Solo Venture as **60% ENCOUNTER / 40% TREASURE CHEST**.
- Caps Solo Venture encounter selection at no more than **3 levels above** the initiating hero; normal Venture initially retained its +5 cap.
- Solo ENCOUNTER results skip the rally and immediately enter the existing Active Battle engine with only the initiating hero; other players cannot join.
- Completed Solo Ventures award **4 Fellowship Renown**, exactly half the normal Venture completion award of 8.
- Adds strict replay-safe `SOLO_VENTURE` Portal action and advances Portal Action protocol **10 → 11**.
- Runtime identity: `1.1.11-solo-venture`; frontend asset revision: `1.1.11-solo1`.

## v1.1.10 — Chocobo Companions — Hotfix 4

- Makes first-time Portal recruitment explicitly require both Twitch authentication and a positively confirmed live Crystal Guild sync.
- Disables the Recruit button as **Guild Offline** whenever `sync_connected` is not true.
- Makes shared Portal auth refresh fail closed: a failed status refresh clears stale action/recruit availability instead of preserving a previously online state.
- Keeps the hosted action endpoint's existing offline service guard as the final authority if connectivity drops between render and click.
- Recruitment automatically becomes available again when the normal 3-second auth/status refresh observes a restored Bot sync.
- Keeps local DB schema **4**, hosted sync schema **1**, and Portal Action protocol **10** unchanged.
- Advances aligned runtime identity to `1.1.10-chocobo-h4` and frontend asset revision to `1.1.10-chocobo1h4`.
- Requires no migration, player reset, new environment variables, or OAuth reconfiguration.

## v1.1.10 — Chocobo Companions — Hotfix 3

- Adds **Recruit Adventurer** to the Guild Heroes page so first-time players can create their persistent character from the website after signing in with Twitch.
- Adds strict `RECRUIT` Portal action support for authenticated Twitch users who do not yet have a synced Crystal Guild character.
- Keeps every other Portal action blocked until a character exists and syncs back to the hosted Portal.
- Reuses the same authoritative starter state as `!recruit`: Lv.1 Adventurer, 250 Gil, 3 Potions, Fresh Meat title, and Fellowship membership.
- Routes successful Portal recruitment through the existing Twitch announcement dispatcher after hosted acknowledgement, so website-created characters also appear in Twitch chat.
- Commits the new character, starter state, Fellowship membership, and replay receipt together so acknowledgement retries cannot double-create or double-award recruitment.
- Updates the Player Guide quick-start copy to document both Portal and Twitch recruitment paths.
- Advances Portal Action protocol **9 → 10**. Local DB schema remains **4** and hosted sync schema remains **1**.
- Advances runtime identity to `1.1.10-chocobo-h3` and frontend asset revision to `1.1.10-chocobo1h3`.
- Requires no database migration, player reset, new environment variables, or OAuth changes.

## v1.1.10 — Chocobo Companions — Hotfix 2

- Adds a visible **Guild Board · Coming Soon — Expeditions** panel to the public Fellowship page.
- Shows live Expedition Board preparation status as **LOCKED**, **PROJECT AVAILABLE**, **UNDER CONSTRUCTION**, or **BOARD READY** from existing Fellowship state.
- Documents the shared **Expedition Board** prerequisite and the per-adventurer **registered Chocobo** prerequisite without enabling Expedition gameplay early.
- Adds a matching **Expeditions — Coming Soon** preparation panel to the authenticated Chocobo Stable with Chocobo-registration and Guild Board readiness indicators.
- Adds a Player Guide Coming Soon note so the pre-v1.2 preparation path is visible outside the Portal.
- Does not add Expedition destinations, contracts, rewards, action buttons, Portal mutations, or gameplay rules.
- Keeps Hotfix 1's canonical `w d h m s` timer formatting unchanged.
- Keeps local DB schema 4, hosted sync schema 1, and Portal Action protocol 9 unchanged.
- Advances runtime identity to `1.1.10-chocobo-h2` and frontend asset revision to `1.1.10-chocobo1h2`.
- Requires no migration, player reset, new environment variables, or OAuth changes.

## v1.1.10 — Chocobo Companions — Hotfix 1

- Standardizes all player-facing countdown rendering to the canonical weeks/days/hours/minutes/seconds ladder.
- Prevents long timers from displaying unbounded minutes such as `1164m 2s`; the same duration now renders as `19h 24m 2s`.
- Updates Portal Daily, Venture/Hunt/rally, Camp, Chocobo Writ, and Moogle refresh countdowns to the shared formatter.
- Changes Moogle stock refresh from a wall-clock timestamp to a locally ticking duration.
- Updates Player Guide Hunt cooldown formatting and Bot/Twitch cooldown, Camp, shop, raid, and Writ messages to the same unit order.
- Keeps all authoritative cooldown timestamps and durations unchanged.
- Keeps local DB schema 4, hosted sync schema 1, and Portal Action protocol 9 unchanged.
- Advances runtime identity to `1.1.10-chocobo-h1` and frontend asset revision to `1.1.10-chocobo1h1`.
- Requires no migration, player reset, new environment variables, or OAuth changes.

## v1.1.10 — Chocobo Companions

- Moves the Chocobo companion foundation ahead of the planned v1.2 Expedition expansion so Expeditions can require an established companion from day one.
- Adds the shared **Chocobo Stable** Fellowship project/facility at Fellowship LVL 2. The one-tier Stable requires 5,000 Gil, 10 Fellowship Venture completions, and Fellowship LVL 2.
- Adds the personal quest **A Chocobo of Your Own**, requiring Character Lv.10, 10 Ventures, and one C-rank Hunt clear; completing it awards 250 Gil.
- Adds the unsellable **Chocobo Registration Writ** for 500 Gil. The Writ can be purchased only after both the Stable and personal quest are complete, then requires exactly **1 hour** before activation.
- Adds persistent Chocobo registration and naming after an active Writ is consumed. Names support 2–20 characters using letters, numbers, spaces, apostrophes, and hyphens.
- Adds Chocobo Bond progression from Lv.1–20. Registered companions earn Bond XP from Venture treasure (+8), successful Venture encounters (+12), and Hunt victories (C/B/A/S: +15/+25/+40/+60).
- Adds one deterministic starter trait per Chocobo: Steady Strider, Keen Eye, Fleet Feet, Forager, or Lucky Plume. Traits are descriptive Expedition preparation only and grant no combat bonus in v1.1.10.
- Adds Twitch commands `!chocobo`/`!stable`, `!chocoboquest`, `!chocobowrit`/`!writ`, `!registerchocobo <name>`, and `!chocoboname <name>`.
- Adds an authenticated **Chocobo Stable** Adventurer Portal tab with acquisition checklist, quest/Writ controls, local Writ countdown, companion profile, Bond progress, trait display, rename, and Expedition-readiness checklist.
- Adds strict Portal actions `CHOCOBO_STATE`, `COMPLETE_CHOCOBO_QUEST`, `PURCHASE_CHOCOBO_WRIT`, `REGISTER_CHOCOBO`, and `RENAME_CHOCOBO`; resource/progression mutations remain Bot-authoritative and replay-safe.
- Derives future Expedition readiness from both a registered Chocobo and the completed Fellowship Expedition Board. Expedition gameplay itself remains reserved for v1.2.
- Advances local database schema **3 → 4** with additive `player_chocobos` and `player_chocobo_traits` tables plus a verified `pre_schema_4_<timestamp>.db` backup before migrating an existing Guild.
- Advances Portal Action protocol **8 → 9** and frontend asset revision to `1.1.10-chocobo1`; hosted sync schema remains **1** and Twitch prefix remains `!`.
- Preserves existing characters, economy, Adventure/Hunt state, Daily state, inventory/equipment/forging, Fellowship progression, and Portal relay configuration with no player reset, new environment variables, or OAuth reconfiguration.

## v1.1.9 — Fellowship — Hotfix 1

- Fixes the Adventure Board Venture countdown so the headline and disabled-reason countdown use the same authoritative deadline and local browser clock instead of mixing a live timer with stale snapshot text.
- Routes successful Portal gameplay announcements through the existing Twitch notification dispatcher after hosted action acknowledgement.
- Portal-started Encounter Ventures now post the normal **ENCOUNTER / RALLY OPEN** announcement to Twitch chat.
- Portal Treasure Ventures, new Portal rally joins, and Portal Hunt starts share the same cross-surface announcement bridge.
- Explicitly wakes the autonomous encounter scheduler when a Portal Venture starts a rally or a Portal Hunt starts combat.
- Preserves replay safety: an acknowledgement-loss retry mutates gameplay once and emits the Twitch announcement once.
- Keeps local DB schema 3, hosted sync schema 1, and Portal Action protocol 8 unchanged.
- Advances runtime identity to `1.1.9-fellowship-h1` and frontend asset revision to `1.1.9-portalactions8h1`.
- Requires no migration, player reset, new environment variables, or OAuth changes.

## v1.1.9 — Fellowship — Portal Actions Phase 9: Adventure Board

- Adds a live authenticated **Adventure Board** to each signed-in player's own Adventurer profile, replacing the old read-only Hunts tab while preserving other players' read-only Hunt records.
- Adds strict `ADVENTURE_STATE`, `TRAVEL_REGION`, `VENTURE`, `JOIN_ENCOUNTER`, and `CHALLENGE_HUNT` Portal actions.
- Reuses the existing authoritative travel, Venture, shared encounter, Hunt, cooldown, reward, Bestiary, loot, and combat engines rather than adding a parallel Web ruleset.
- Adds current-region and travel eligibility, Venture cooldown and +10-level enemy-risk display, live shared rally/party state, recent battle results, and a ranked Hunt Board with rewards/requirements/cooldowns.
- Portal-started Ventures and Portal rally joins share the exact same channel-wide encounter with Twitch-chat participants.
- Adventure countdowns tick locally; the Portal performs bounded live refresh only while an encounter is active and otherwise refreshes on explicit actions, visibility return, or authoritative deadlines.
- Makes travel, Venture, rally join, and Hunt acceptance replay-safe so lease retries cannot double-consume cooldowns, duplicate treasure, create a second encounter, or accept a Hunt twice.
- Keeps Active Battle turn actions and raids Twitch-first; no `ATTACK`, ability, raid, streamer-only, or arbitrary command relay is exposed through player sessions.
- Adds a subtle site-density refinement: slightly smaller base Portal type, modestly reduced panel/header/card padding, tighter quick actions, and matching Guide/Streamer spacing while preserving Phase 8 touch targets, focus visibility, wrapping, and reduced-motion behavior.
- Advances Portal Action protocol **7 → 8** and frontend asset revision to `1.1.9-portalactions8`.
- Keeps local DB schema **3**, hosted sync schema **1**, canonical Twitch prefix `!`, and all existing player progression intact with no reset or new environment variables.

## v1.1.8 — Fellowship — Phase 8 UI/UX Pass & Polish

- Reframes Adventurer Portal Overview as a home screen with direct shortcuts to the highest-use management areas.
- Adds a mobile Profile section selector while retaining the established desktop tab rail.
- Adds explicit tab/tabpanel accessibility semantics and improved keyboard focus visibility.
- Compacts the Crystal Guild connection panel so connection health remains visible without dominating the profile.
- Standardizes touch targets, action hierarchy, spacing, panel/card treatment, loading/status feedback, and reduced-motion behavior.
- Polishes Equipment & Inventory, Recovery, Moogle, Blacksmith, Jobs, Fellowship, Bestiary, Achievements, Records, Player Guide, and Streamer Dashboard presentation.
- Keeps all gameplay rules, economy paths, Portal action types, and security boundaries unchanged.
- Keeps local DB schema 3, hosted sync schema 1, and Portal Action protocol 7 unchanged.
- Advances frontend asset revision to `1.1.8-uiux1` and retains the canonical Twitch command prefix `!`.
- Requires no player reset, new environment values, OAuth reconfiguration, or database migration.

## v1.1.7 — Fellowship — Portal Actions Phase 7

- Adds a dedicated authenticated **Guild Blacksmith** tab to each player's own Adventurer profile.
- Adds strict `CRAFTING_STATE`, `CRAFT_RECIPE`, and `FORGE_ITEM` Portal actions.
- Reuses existing crafting/forging economy rules, including known recipes, level requirements, materials, Gil/Hunt Seal costs, +1 through +5 upgrades, and Fellowship Workshop discounts.
- Adds live material/cost comparisons, craftable quantity calculations, current forge level, next-upgrade previews, and immediate refreshed state.
- Makes Portal craft/forge mutations replay-safe so acknowledgement loss cannot double-spend or duplicate an upgrade.
- Keeps Blacksmith mutations unavailable while committed to active encounter/raid combat.
- Adds **Daily Guild Provisions** to the signed-in player's Overview through strict `DAILY_STATE` and `CLAIM_DAILY` actions.
- Portal Daily uses the existing 24-hour `!daily` cooldown, existing level-scaled Gil reward, and one-Potion reward; it adds no second reward track.
- Daily countdown uses the authoritative absolute next-claim timestamp with local browser ticking instead of per-second server polling.
- Makes Daily claiming replay-safe so lease retries cannot award a second Daily.
- Keeps other players read-only and does not add Venture, Hunt, Raid, Web combat, streamer actions, or arbitrary command relay.
- Advances Portal Action protocol **6 → 7** while keeping local DB schema **3** and hosted sync schema **1** unchanged.
- Advances frontend asset revision to `1.1.7-portalactions7` and retains canonical Twitch prefix `!`.

## v1.1.6 — Fellowship — Portal Actions Phase 6

- Adds a live authenticated Fellowship contribution workspace to each player's own Fellowship tab.
- Adds strict `FELLOWSHIP_STATE`, `CONTRIBUTE_GIL`, and `CONTRIBUTE_ITEM` Portal actions.
- Reuses the existing transactional Fellowship engine for balance/inventory validation, project progress, ledgers, personal donation totals, Renown, and project completion.
- Preserves automatic over-contribution capping so excess resources remain with the player.
- Adds Bot-side replay receipts around Fellowship contribution mutations to prevent duplicate spending after lease retries.
- Keeps gameplay/LVL requirements read-only and progressing through normal play.
- Keeps other players' Fellowship views read-only.
- Does not add Venture, Hunt, Raid, Web combat, streamer actions, or arbitrary command relay.
- Advances Portal Action protocol **5 → 6** while keeping local DB schema **3** and hosted sync schema **1** unchanged.
- Advances product identity to **v1.1.6 — Fellowship** and frontend asset revision to `1.1.6-portalactions6`.
- Retains the canonical Twitch command prefix `!` and the defensive abandoned-test prefix repair.

## v1.1.5 — Fellowship — Portal Actions Phase 5

- Rebuilt Phase 5 from the verified v1.1.0 Phase 4 baseline.
- Retains the canonical Twitch command prefix `!`; no `&` command migration is included.
- Adds live Portal recovery/inventory state for the authenticated player's own profile.
- Adds structured `RECOVERY_STATE`, `USE_FIELD_ITEM`, and `START_REST` Portal actions.
- Adds field-item recovery, KO recovery options, Tent handling, and Start Camp from the Portal.
- Camp uses the authoritative completion timestamp and a local browser countdown; it does not poll the server every second.
- Adds usable-now filtering, effective recovery/waste previews, smart recovery suggestions, and explicit disabled reasons.
- Adds immediate state refresh after successful recovery actions.
- Adds replay/idempotency protection for recovery mutations.
- Keeps Active Battle status cures battle-only; no Web combat is introduced.
- Advances Portal Action protocol 4 → 5.
- Advances product identity to v1.1.5 while leaving local DB schema 3 and hosted sync schema 1 unchanged.
- Frontend asset revision: `1.1.5-portalactions5r1`.

## v1.1.0 — Fellowship

- Introduced shared Fellowship LVL/Renown, personal Guild Ranks, projects, facilities, Orders, Deeds, Founding Members, dedicated Fellowship pages, and Portal Actions Phases 1–4.
