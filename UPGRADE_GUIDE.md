# Upgrade Guide — Full Rest & Combat Continuity

Deploy **Bot and Web together** for this correction. The Bot contains the Rest/resource and encounter-continuity fixes; the Web removes obsolete Dungeon round-limit presentation and updates player-facing Guide copy.

Preserve the live player database, token database, environment secrets, and persistent runtime files. Local schema remains **16**, hosted sync remains **1**, and Portal Action protocol remains **33**. No migration or player reset is performed by this correction. If upgrading from a pre-Favorites-authority installation, complete the existing **15 → 16** migration first using its verified `backups/pre_schema_16_*.db` backup path before applying this package.

After deployment, verify:

1. Complete a Camp/Rest while on an MP Job, switch to an AP Job, and confirm AP is at that Job's full maximum. Repeat in the opposite direction.
2. Switch between two Jobs with different maxima for the same resource family after Rest and confirm each resolves at its own maximum.
3. Let a living encounter advance beyond round 12; it must continue while both sides remain alive.
4. Dungeon combat displays `Round N` without a `/ 12` or other defeat-limit denominator.
5. An explicit retreat still resolves through its normal retreat path.
