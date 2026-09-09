# Upgrade — Hotfix 5 Gear Favorites Authority Fix

**Deploy Bot and Web together.** This update advances local schema **15 → 16** and Portal Action protocol **32 → 33**. A mismatched Bot/Web pair will intentionally reject Portal actions.

Preserve the live `crystal_guild.db`, token database, persistent storage, and environment secrets. On first Bot startup, Crystal Guild creates and verifies a `backups/pre_schema_16_*.db` backup before applying the additive `player_gear_favorites` migration. Existing players, inventory, progression, Retainers, Fellowship, Gold Saucer, Resynthesis, Ventures, Hunts, Trials/Raids, and Treasure Seekers progress remain intact.

After both components are deployed:
1. Confirm `!cgversion` reports schema **16** and Portal protocol **33**.
2. Open Equipment on a browser that previously held local Favorites; any legacy list is offered for authoritative migration automatically.
3. Favorite or unfavorite one item and allow the Bot to process the queued preference action.
4. Open/return to Equipment on mobile; the same Favorites should appear.
5. Clearing all Favorites on one device must also propagate as an authoritative empty list.

Hosted sync schema remains **1**. No new environment variables or sync keys are required.
