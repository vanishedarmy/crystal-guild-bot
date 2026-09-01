# Crystal Guild v1.6.0 — Gold Saucer RC2 Setup

Alpha 4 is an in-place upgrade from the **Gold Saucer Alpha 3 MGP canonical baseline**. It adds Chocobo Racing without changing stored MGP balances or the local schema; Portal Action protocol advances from 27 to 28.

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
- `!cgversion` → `1.6.0-gold-saucer-rc2`
- Local DB schema → **12**
- Hosted sync schema → **1**
- Portal Action protocol → **27**
- Twitch prefix → `!`

See `UPGRADE_GUIDE.md`, `WEB_SYNC_SETUP.md`, and `VALIDATION_REPORT.md` for the Alpha 4-specific contract and validation scope.

## Twitch application and authorization
For fresh installs, register the local callback in the Twitch Developer Console:

https://dev.twitch.tv/console/apps

Redirect URL: `http://localhost:4343/oauth/callback`

The dedicated Bot authorization uses `user:read:chat`, `user:write:chat`, and `user:bot`. The broadcaster authorization includes `channel:bot` and the established subscription scope. Existing Alpha 3 installs do not need to reauthorize for Alpha 4.

## Hosted Web and secret separation
Manage the hosted services from:

https://dashboard.render.com

Keep `PORTAL_PUBLIC_URL` and `PORTAL_SYNC_KEY` in the appropriate environment configuration. Never put `crystal_guild.db`, Twitch token databases, `.env`, OAuth secrets, or live player state into public Web assets or source-control releases.
