# Crystal Guild Changelog

## v1.8.0 Final — Merc Service
- Promotes the hardened RC3 feature set to the production v1.8 release.
- Hero Merc Service uses Hunt Seals with independent Hunt, Venture, and Raid assignment slots.
- Includes deployed-state recovery, full Merc artwork, responsive Portal hardening, readable navigation, and one shared page-bottom Refresh control.
- Runtime `1.8.0-merc-final`; schema 17, hosted sync 1, Portal Action protocol 34; no player reset.

## v1.8.0 RC3 — Portal UI Polish
- Roomier desktop profile navigation with 6/8/4/2-column responsive tiers and no label overflow.
- Removed section-specific manual refresh controls; one shared Refresh button now sits at the bottom of live Portal pages.
- Simplified the connection strip to passive status only while preserving automatic live updates.
- No gameplay, schema, economy, or Merc Service balance changes.

## v1.8.0 RC2 — UI Consistency
- Balanced Adventurer Profile navigation and responsive breakpoints across the Portal.
- Added global layout/media containment guardrails for desktop and mobile consistency.
- No gameplay, schema, economy, or Merc Service balance changes.

# v1.8.0 Alpha 2 — Merc Service Balance & UX

- Added visual three-slot deployment board.
- Added exact per-mission Hero availability reasons.
- Rebalanced Merc Hunt Seal fees to 5/6/5/7/9/12.
- Preserved signature effects, schema 17, sync 1, and protocol 34.

# Crystal Guild Changelog

## v1.7.1 — Resynthesis Alpha 2 Hotfix 5 — Treasure Seekers Solo Progress

- Solo Venture treasure discoveries now emit canonical Fellowship `treasure` activity.
- Treasure Seekers weekly-order progress and Treasure Hunters deed progress now include Solo treasure chests.
- Run/stage-scoped event keys make the correction replay-safe and prevent double counting.
- Rally remains 100% Encounter / 0% Treasure Chest; Solo remains 80% Encounter / 20% Treasure.
- No schema, hosted sync, Portal protocol, or player-data migration changes.

## v1.7.1 — Resynthesis Alpha 2 Hotfix 3 — Job Resource Persistence

- Fixes inactive MP/AP pools being overwritten with zero during refresh or equipment normalization.
- Preserves MP and AP independently across Job-family switches.
- Adds a one-time receipt-protected compatibility repair for inactive zeros written by older builds.
- Legitimately depleted zero pools remain zero after the repair receipt exists, preventing swap-refill exploits.
- Runtime `1.7.1-resynthesis-a2h3`; schema 15 and Portal protocol 32 unchanged.

## v1.7.1 — Resynthesis Alpha 2 Hotfix 2 — Job Quest Unlock Repair

- Job-unlock quests self-reconcile automatically when all existing requirements are met.
- Retroactive progress is honored; no requirement must be repeated.
- Quest Gil/title/achievement rewards are exactly-once across repeated refreshes.
- Portal Jobs state, `!job`, `!jobinfo`, and `!quests` all trigger reconciliation.
- Runtime `1.7.1-resynthesis-a2h2`; schema 15 and Portal protocol 32 unchanged.

## v1.7.1 — Resynthesis Alpha 2 Hotfix 1 — Encounter Variety

- Fixes narrow Solo Venture/Expedition level bands that could collapse to a single monster.
- Widens eligible pools to five candidates when available.
- Suppresses immediate repeats and blocks a third identical encounter when alternatives exist.
- Caps one monster at ~45% effective weight when 3+ choices exist.
- No reward, drop, schema, protocol, or Web changes.

## v1.7.1 — Resynthesis Alpha 2
- Added Blacksmith Resynthesize Gear for weapons and armor.
- Added deterministic recovery previews and replay-safe Portal mutation.
- Protected accessories, Relic/Artifact gear, and last equipped copies.
- Added bounded final-copy forge recovery and forge-state cleanup.
- Portal Action protocol advances to 32; schema remains 15.


## v1.7.0 — Moogle Retainer

- Adds the complete Retainer Service with timed crafting-material procurement, rank/EXP progression, priority targeting, recent-haul history, and final artwork/UI.
- Adds the shared Moogle Emporium Annex, expanding personal shop rotations from 9 to 12 stock slots after construction.
- Carries forward the production Gold Saucer feature set and verified restorative-item balance.
- Hardens Render startup backups against low-disk restart loops and keeps routine file logs off persistent database storage.
- Finalizes responsive/mobile layout, compact UI presentation, text spacing, lazy loading, bounded static-art streaming, and ETag revalidation.
- Production contract: runtime `1.7.0`, schema **15**, hosted sync **1**, Portal Action protocol **31**, Twitch prefix `!`.

Development-phase notes are intentionally excluded from the production package. Repository history remains the source of record for pre-release iteration details.
