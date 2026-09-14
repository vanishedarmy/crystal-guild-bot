# Upgrade Guide — Personalized Chat Results + Raid XP Boost

**Deploy Bot and Web together.** Both components changed: the Bot owns Twitch settlement formatting/rewards, while the Web carries the matching Raid XP information.

Current contract: runtime `1.7.1-resynthesis-a2h5`, schema **16**, hosted sync **1**, Portal Action protocol **33**, Twitch prefix `!`.

If **Contextual Quick Help** is currently installed, apply both incremental patches from that baseline. For a clean replacement, use the Complete archive. Preserve your live database, backups, tokens, secrets, and runtime state.

No migration or reset occurs. Existing Raid clears, records, inventory, progression, Fellowship state, Ventures, and all saved player data remain intact. The XP increase applies to Raid victories resolved after this update; historical rewards are not retroactively changed.

Compatibility note: installations that previously completed the schema **15 → 16** Gear Favorites migration keep that database and verified `backups/pre_schema_16_*.db` backup unchanged; this release adds no schema migration.
