# Crystal Guild v1.9.0 Alpha 8 — Setup

For an existing deployment, preserve `crystal_guild.db`, the Twitch token store, `.env`, hosted secrets and all persistent-disk files; deploy the paired Bot and Web source. Schema **20 → 21** migrates automatically after a verified `pre_schema_21_<timestamp>.db` backup. Current Alpha 8 users applying the cleanup hotfix need **no database migration**.

The Bot and Web must both report runtime `1.9.0-seasonal-events-alpha8`; local database schema **21**, hosted sync **1**, and Portal Action protocol **37**. The Halloween edition installs **disabled by default**. Activate or schedule it from the Streamer Control Center.

Manage hosted services at https://dashboard.render.com.

For a new Twitch application, register `http://localhost:4343/oauth/callback` in the [Twitch Developer Console](https://dev.twitch.tv/console/apps). The Bot scopes are `user:read:chat`, `user:write:chat`, and `user:bot`; the broadcaster authorization includes `channel:bot` and its existing subscription/channel scopes.

Keep `PORTAL_PUBLIC_URL`, `PORTAL_SYNC_KEY`, OAuth secrets and any database/token paths private. Never put the live DB, `.env`, or Twitch token databases in the public Web directory or release archives. See `RENDER_CLOUD_SETUP.md`, `WEB_SYNC_SETUP.md` and `UPGRADE_GUIDE.md`.
