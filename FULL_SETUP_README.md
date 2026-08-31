# Crystal Guild v1.6.0 — Gold Saucer Alpha 3 Setup

Alpha 3 is an in-place Bot update from the **Gold Saucer Alpha 2 Hotfix 2 canonical baseline**. It changes the canonical Gold Saucer currency name to **MGP** without changing the stored balance, schema, payout tables, or Portal action protocol.

## Existing installation
Preserve the live `crystal_guild.db`, `.env`, Twitch token storage, hosted secrets, and persistent-disk data. Replace the Bot source and restart the worker. No schema migration, player reset, OAuth reauthorization, or new environment variable is required.

## Gold Saucer verification
- First visit still grants **500 MGP** once.
- On later UTC days, the first Saucer request still grants the **50 MGP** floor allowance once.
- Mini Cactpot remains **10 MGP** per ticket.
- Crystal Slots remains **15 MGP** per spin.
- Monster Toss remains **20 MGP** per game, 5 throws, maximum 3 completed games per UTC day.
- Prize Counter values are unchanged.
- Ordinary Gil remains separate.
- An existing Gold Saucer balance must be identical before and after upgrading.

## Release verification
- `!cgversion` → `1.6.0-gold-saucer-a3`
- Local DB schema → **12**
- Hosted sync schema → **1**
- Portal Action protocol → **27**
- Twitch prefix → `!`

See `UPGRADE_GUIDE.md`, `WEB_SYNC_SETUP.md`, and `VALIDATION_REPORT.md` for the Alpha 3-specific contract and validation scope.

## Twitch application and authorization
For fresh installs, register the local callback in the Twitch Developer Console:

https://dev.twitch.tv/console/apps

Redirect URL: `http://localhost:4343/oauth/callback`

The dedicated Bot authorization uses `user:read:chat`, `user:write:chat`, and `user:bot`. The broadcaster authorization includes `channel:bot` and the established subscription scope. Existing Alpha 2 installs do not need to reauthorize for Alpha 3.

## Hosted Web and secret separation
Manage the hosted services from:

https://dashboard.render.com

Keep `PORTAL_PUBLIC_URL` and `PORTAL_SYNC_KEY` in the appropriate environment configuration. Never put `crystal_guild.db`, Twitch token databases, `.env`, OAuth secrets, or live player state into public Web assets or source-control releases.
