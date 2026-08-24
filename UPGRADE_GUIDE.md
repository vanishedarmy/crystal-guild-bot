# Crystal Guild v1.1.16 — Arsenal Hotfix 1 Upgrade Guide

## Upgrade baseline

This package upgrades **v1.1.16 — Arsenal** to **v1.1.16 — Arsenal Hotfix 1**.

Hotfix 1 changes both Bot Hunt runtime behavior and matching Web presentation. Deploy the Bot and Web portions together.

## Before updating

1. Stop the Crystal Guild Bot/worker cleanly.
2. Keep the normal backup of the authoritative Crystal Guild installation/database.
3. Preserve private/runtime files rather than replacing them from release packages:
   - `.env`
   - `.tio.tokens.json` when used locally
   - `crystal_guild.db`
   - cloud Twitch token database such as `/var/data/twitch_tokens.db`
   - any deployment-specific private runtime state/logs that live outside the tracked release tree

## Apply the update

1. Overlay `CrystalGuild-v1.1.16-Arsenal-Hotfix1-Update-from-Arsenal.zip` onto the existing **v1.1.16 Arsenal** installation.
2. Update/push the matching Web files to GitHub and redeploy the hosted Web service as usual.
3. Restart the Bot/worker.
4. Verify `!cgversion` / `!health` reports runtime **`1.1.16-arsenal-h1`**.
5. Verify Web `/api/health` reports frontend asset revision **`1.1.16-arsenal1h1`**.
6. Open the Adventure Board and confirm Hunt cards show their timed assignment durations.

## Database and protocol

No migration step is required:

- Local DB schema remains **5**.
- Hosted sync schema remains **1**.
- Portal Action protocol remains **14**.
- No player reset is required.
- No new environment variable or Render secret is required.
- No new Twitch OAuth scope or reauthorization is required.

Timed Hunt assignments persist through the existing runtime-state mechanism; they do not add a new database schema.

## Existing Hunts at upgrade time

A Hunt already in progress before Hotfix 1 may still exist as a legacy Active Battle checkpoint. The updated daemon retains compatibility for that state and can finish it safely. Any Hunt accepted after the update uses the new per-player timed assignment model.

## New Hunt timers

- C: **5 minutes**
- B: **15 minutes**
- A: **30 minutes**
- S: **1 hour**
- S+: **2 hours**

Round commands are not needed for new Hunts. At the deadline, Crystal Guild resolves combat autonomously and posts the final outcome.
