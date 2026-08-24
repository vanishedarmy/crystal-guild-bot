CRYSTAL GUILD v1.1.16 — ARSENAL HOTFIX 6
========================================

Upgrade baseline: v1.1.16 — Arsenal Hotfix 5

Daily Guild Provisions pool hotfix:
- removes Chocobo Registration Writs from all Daily Guild Provision rolls;
- replaces broad type/rarity inference with an explicit opt-in provisions catalog;
- limits Daily rewards to ordinary level-appropriate consumables and approved basic crafting materials;
- prevents future special/progression items from entering Daily rewards unless deliberately approved;
- preserves randomized rewards, subscriber-tier roll counts, Gil bonuses, and the 24-hour cooldown;
- self-heals orphaned Writs that were previously granted without the authoritative Stable timer record, restoring the intended Chocobo purchase path while leaving legitimate purchased Writs untouched.

Bot runtime: 1.1.16-arsenal-h6
Matching Web asset revision: 1.1.16-arsenal1h5 (unchanged)
Local DB schema: 5 (unchanged)
Hosted sync schema: 1 (unchanged)
Portal Action protocol: 14 (unchanged)

This is a Bot-only gameplay hotfix. Replace/redeploy the Bot/worker and leave the Hotfix 5 Web deployment in place. No database migration, player reset, new Render secret, or OAuth change is required.
