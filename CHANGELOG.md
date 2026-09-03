# Crystal Guild Changelog

## v1.7.1 — Resynthesis Alpha 1
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
