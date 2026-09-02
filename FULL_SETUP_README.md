# Crystal Guild v1.7.0 — Production Setup

## Existing installation
Preserve the live `crystal_guild.db`, Twitch token storage, `.env`, hosted secrets, and persistent-disk data. Replace the Bot source and restart the worker. Existing schema-15 v1.7.0 candidate deployments do not require a schema migration or player reset.

## Release verification
- `!cgversion` → `1.7.0`
- Local DB schema → **15**
- Hosted sync schema → **1**
- Portal Action protocol → **31**
- Twitch prefix → `!`

## Core v1.7.0 checks
- Retainer dispatch deducts Gil once, commits the haul at dispatch, persists across restart, and collects exactly once.
- Priority procurement remains route-bound and optional.
- The completed Moogle Emporium Annex expands personal shop rotations from 9 to 12 slots.
- Gold Saucer MGP and existing attraction progress remain preserved.
- Startup backup pruning runs before a new Render backup and low disk space cannot abort Bot startup.

## Twitch application and authorization
For fresh installs, register the local callback in the Twitch Developer Console:

https://dev.twitch.tv/console/apps

Redirect URL: `http://localhost:4343/oauth/callback`

The dedicated Bot authorization uses `user:read:chat`, `user:write:chat`, and `user:bot`. The broadcaster authorization includes `channel:bot` and the established subscription scope.

## Hosted Web and secret separation
Manage hosted services from:

https://dashboard.render.com

Keep `PORTAL_PUBLIC_URL` and `PORTAL_SYNC_KEY` in the appropriate environment configuration. Never put `crystal_guild.db`, Twitch token databases, `.env`, OAuth secrets, or live player state into public Web assets or source-control releases.

See `UPGRADE_GUIDE.md`, `RENDER_CLOUD_SETUP.md`, `WEB_SYNC_SETUP.md`, and `VALIDATION_REPORT.md` for production deployment details.
