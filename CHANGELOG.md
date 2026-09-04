# Crystal Guild Changelog

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
