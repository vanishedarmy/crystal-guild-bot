# Crystal Guild v1.9.0 Alpha 1 — Moogle Trading Post Setup

**Current Alpha 1 note:** The Moogle Trading Post adds Fellowship-built player commerce to the Moogle Emporium. Deploy the matching Bot and Web together. The Bot performs an automatic schema **18 → 19** migration after creating a verified `pre_schema_19_*.db` backup. No player reset occurs.

## Existing installation
Preserve the live `crystal_guild.db`, Twitch token storage, `.env`, hosted secrets, and persistent-disk data. Deploy the matching Bot and Web source together, then restart the worker. The additive schema 18 → 19 migration is automatic.

## Release verification
- Bot runtime → `1.9.0-trading-post-alpha1`
- Paired Web → `1.9.0-trading-post-alpha1`
- Local DB schema → **19**
- Hosted sync schema → **1**
- Portal Action protocol → **36**
- Twitch prefix → `!`

## Trading Post verification
- Fellowship Level 1 service building; construction requires 25,000 Gil, 3 Mythril Ore, and 15 completed Expeditions.
- Fixed-price player listings last 48 hours.
- Listing fee is 2%; completed-sale tax is 5%.
- Purchases/listings/cancellations use authoritative replay-safe Portal Actions.
- Relics, quest/key items, and the last equipped copy of gear cannot be listed.

## Carried-forward systems
Elite Mercs, Merc Service progression, Resynthesis, Moogle Retainer, Emporium Annex, Gold Saucer, Expeditions, Fellowship projects, equipment favorites, and existing player progression remain intact.

See `UPGRADE_GUIDE.md`, `RENDER_CLOUD_SETUP.md`, `WEB_SYNC_SETUP.md`, and `VALIDATION_REPORT.md` for deployment details.

## Twitch application and authorization
For fresh installs, register the local callback in the Twitch Developer Console:

https://dev.twitch.tv/console/apps

Redirect URL: `http://localhost:4343/oauth/callback`

The dedicated Bot authorization uses `user:read:chat`, `user:write:chat`, and `user:bot`. The broadcaster authorization includes `channel:bot`, `channel:read:subscriptions`, and the established subscription scope.

## Hosted Web and secret separation
Manage hosted services from:

https://dashboard.render.com

Keep `PORTAL_PUBLIC_URL` and `PORTAL_SYNC_KEY` in the appropriate environment configuration. Never put `crystal_guild.db`, Twitch token databases, `.env`, OAuth secrets, or live player state into public Web assets or source-control releases.
