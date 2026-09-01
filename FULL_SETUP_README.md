# Crystal Guild v1.7.0 — Retainer Service Alpha 2 Setup

Alpha 2 is an in-place upgrade from the verified **v1.7.0 Retainer Service Alpha 1** baseline. It adds targeted material procurement and recent-haul history, advances local schema 14→15, and advances Portal Action protocol 30→31.

## Existing installation
Preserve the live `crystal_guild.db`, `.env`, Twitch token storage, hosted secrets, and persistent-disk data. Replace the Bot source and restart the worker. The schema migration creates and verifies `backups/pre_schema_15_*.db` before adding Retainer tables. No player reset, MGP conversion, OAuth reauthorization, or new environment variable is required.

## Retainer Service verification
- Every recruited player can open one personal **Guild Retainer** from their own Adventurer Portal.
- Only one procurement assignment can be active/returned-awaiting-collection at a time.
- Dispatch deducts the listed Gil exactly once.
- The crafting-material haul is committed at dispatch and cannot be rerolled by refresh/reconnect.
- Returned materials and Retainer EXP are collected exactly once.
- Rank/EXP unlocks longer procurement routes; Alpha 2 keeps Relic and Artifact materials excluded and adds optional route-bound priority requests.
- Routine Retainer activity remains Portal-only and does not post to Twitch chat.

## Existing Gold Saucer verification
- Existing MGP balances remain unchanged.
- Mini Cactpot, Crystal Slots, Monster Toss, Chocobo Racing, Triple Triad, Prize Counter, and RC2 production balance remain unchanged.
- Ordinary Gil remains separate from MGP; Retainer dispatch uses Gil only.

## Release verification
- `!cgversion` → `1.7.0-retainer-a2`
- Local DB schema → **15**
- Hosted sync schema → **1**
- Portal Action protocol → **31**
- Twitch prefix → `!`

See `UPGRADE_GUIDE.md`, `WEB_SYNC_SETUP.md`, and `VALIDATION_REPORT.md` for the Alpha 2 contract and validation scope.

## Twitch application and authorization
For fresh installs, register the local callback in the Twitch Developer Console:

https://dev.twitch.tv/console/apps

Redirect URL: `http://localhost:4343/oauth/callback`

The dedicated Bot authorization uses `user:read:chat`, `user:write:chat`, and `user:bot`. The broadcaster authorization includes `channel:bot` and the established subscription scope. Existing v1.6.0 installs do not need to reauthorize for Retainer Service Alpha 2.

## Hosted Web and secret separation
Manage the hosted services from:

https://dashboard.render.com

Keep `PORTAL_PUBLIC_URL` and `PORTAL_SYNC_KEY` in the appropriate environment configuration. Never put `crystal_guild.db`, Twitch token databases, `.env`, OAuth secrets, or live player state into public Web assets or source-control releases.
