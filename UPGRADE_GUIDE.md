# Upgrade — HTTP Response Efficiency

**Deploy Bot and Web together.** The transport changes are coordinated even though runtime, database schema, and Portal protocol numbers remain unchanged.

Current contract: runtime `1.7.1-resynthesis-a2h5`, schema **16**, hosted sync **1**, Portal Action protocol **33**, Twitch command prefix `!`.

If you are currently running **Full Rest & Combat Continuity**, apply both incremental patches. For a clean replacement, use the Complete archive. Preserve `crystal_guild.db`, backups, Twitch/token data, environment secrets, and other persistent runtime files.

No database migration or player reset is performed. `PORTAL_SYNC_HEARTBEAT_SECONDS` now defaults to **60** and the hosted Web stale threshold defaults to **150** seconds; existing explicit environment overrides may be reviewed if you want the packaged defaults.

Existing installations that previously completed the schema **15 → 16** Gear Favorites migration retain that state and its verified `backups/pre_schema_16_*.db` backup; this HTTP-efficiency release adds no further migration.
