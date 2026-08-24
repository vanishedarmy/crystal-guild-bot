# Crystal Guild v1.1.17 — Arsenal II Upgrade Guide

Upgrade baseline: **v1.1.16 — Arsenal Hotfix 6**.

Arsenal II is a **paired Bot + Web update**. Database schema remains 5 and Portal Action protocol remains 14, so there is no migration step.

## Upgrade

1. Stop the Crystal Guild Bot/worker cleanly.
2. Keep your normal private/runtime files in place, especially `.env`, Twitch token files, the live `crystal_guild.db`, and any Render persistent-disk token/database paths.
3. Make your normal manual database backup as an extra safeguard.
4. Apply the Arsenal II update over the existing v1.1.16 Hotfix 6 installation, or replace Bot/Web source from the full packages while preserving private/runtime state.
5. Push the matching Arsenal II Web source to GitHub and redeploy the hosted Web service.
6. Restart/redeploy the Bot worker.
7. Verify `!cgversion` reports `1.1.17-arsenal-ii`.
8. Verify hosted `/api/health` reports runtime `1.1.17-arsenal-ii` and frontend revision `1.1.17-arsenal-ii1`.
9. Open the Player Guide and confirm it identifies **v1.1.17 — Arsenal II**.

## No migration required

Arsenal II keeps:

- local DB schema **5**
- hosted sync schema **1**
- Portal Action protocol **14**
- Twitch prefix `!`

Do not reset players or manually edit SQLite for this update.

## Quick functional checks

- Open Jobs and confirm caster Jobs show the deeper ability catalog in View Details.
- Open Moogle Emporium and switch between Buy/Sell and Weapons/Armor/Items.
- Open Blacksmith and verify Recipes / Forge Gear has a clear active state.
- Open Adventure Board and verify Camp & Recovery appears.
- On mobile, scroll down/up and confirm the compact header hides and returns normally.
- Verify Hosted Raid Overlay help is at the bottom of the Streamer Dashboard.
- While Twitch is offline, use a Portal action and verify gameplay completes without an automated Twitch chat announcement.
