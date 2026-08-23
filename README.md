# Crystal Guild v1.1.15 — Wayfarer

Wayfarer is the Bot/runtime half of Crystal Guild v1.1.15. It adds persistent per-player interactive Solo Venture state, player-paced Portal combat actions, three-stage risk/reward progression, and the schema-5 migration needed to resume an unfinished Solo Venture safely.

Runtime `1.1.15-wayfarer` · local DB schema **5** · hosted sync schema **1** · Portal Action protocol **13** · Twitch prefix `!`.

Existing schema-4 databases migrate automatically after a verified `pre_schema_5` backup. No player reset, new Render secret, or new Twitch OAuth scope is required. Deploy the matching Web build (`1.1.15-wayfarer1`) so the Adventure Board can use the protocol-13 Solo Venture controls.

See `UPGRADE_GUIDE.md`, `RELEASE_NOTES.md`, and `FULL_SETUP_README.md`.
