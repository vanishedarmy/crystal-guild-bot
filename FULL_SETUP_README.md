# Crystal Guild v1.7.0 — Retainer Service Alpha 1 Setup

Alpha 1 is an in-place upgrade from the **v1.6.0 Gold Saucer production baseline**. It adds the personal Retainer procurement service, advances local schema 13→14, and advances Portal Action protocol 29→30.

## Existing installation
Preserve the live `crystal_guild.db`, `.env`, Twitch token storage, hosted secrets, and persistent-disk data. Replace the Bot source and restart the worker. The schema migration creates and verifies `backups/pre_schema_14_*.db` before adding Retainer tables. No player reset, MGP conversion, OAuth reauthorization, or new environment variable is required.

## Retainer Service verification
- Every recruited player can open one personal **Guild Retainer** from their own Adventurer Portal.
- Only one procurement assignment can be active/returned-awaiting-collection at a time.
- Dispatch deducts the listed Gil exactly once.
- The crafting-material haul is committed at dispatch and cannot be rerolled by refresh/reconnect.
- Returned materials and Retainer EXP are collected exactly once.
- Rank/EXP unlocks longer procurement routes; Alpha 1 pools exclude Relic and Artifact materials.
- Routine Retainer activity remains Portal-only and does not post to Twitch chat.

## Existing Gold Saucer verification
- Existing MGP balances remain unchanged.
- Mini Cactpot, Crystal Slots, Monster Toss, Chocobo Racing, Triple Triad, Prize Counter, and RC2 production balance remain unchanged.
- Ordinary Gil remains separate from MGP; Retainer dispatch uses Gil only.

## Release verification
- `!cgversion` → `1.7.0-retainer-a1`
- Local DB schema → **14**
- Hosted sync schema → **1**
- Portal Action protocol → **30**
- Twitch prefix → `!`

See `UPGRADE_GUIDE.md`, `WEB_SYNC_SETUP.md`, and `VALIDATION_REPORT.md` for the Alpha 1 contract and validation scope.

## Twitch application and authorization
For fresh installs, register the local callback in the Twitch Developer Console:

https://dev.twitch.tv/console/apps

Redirect URL: `http://localhost:4343/oauth/callback`

The dedicated Bot authorization uses `user:read:chat`, `user:write:chat`, and `user:bot`. The broadcaster authorization includes `channel:bot` and the established subscription scope. Existing v1.6.0 installs do not need to reauthorize for Retainer Service Alpha 1.

## Hosted Web and secret separation
Manage the hosted services from:

https://dashboard.render.com

Keep `PORTAL_PUBLIC_URL` and `PORTAL_SYNC_KEY` in the appropriate environment configuration. Never put `crystal_guild.db`, Twitch token databases, `.env`, OAuth secrets, or live player state into public Web assets or source-control releases.
