# Crystal Guild v1.1.16 — Arsenal Render Cloud Setup

## Existing v1.1.15 Wayfarer Hotfix 3 cloud deployment

This is an in-place source upgrade. Keep the worker's persistent state exactly where it is:

```text
/var/data/crystal_guild.db
/var/data/twitch_tokens.db
```

Update the private Bot GitHub repository, let Render redeploy, verify `!cgversion` / `!health`, then deploy the **matching v1.1.16 Web** source. No player reset, private-state transfer, or database migration is required: Wayfarer Hotfix 3 is already schema 5 and Arsenal remains schema 5. The existing Render secrets remain valid.

After the Web deploy, the Bot heartbeat republishes Fellowship and hosted overlay state automatically. OBS should use `https://YOUR-SITE/overlay`.

## Fresh Render deployment

The worker is created from `render.yaml` as `crystal-guild-bot`, Python 3.11, Starter plan, with a 1 GB persistent disk mounted at `/var/data`. Required Render secrets are `TWITCH_CLIENT_ID`, `TWITCH_CLIENT_SECRET`, `TWITCH_BOT_ID`, `TWITCH_OWNER_ID`, `PORTAL_PUBLIC_URL`, and `PORTAL_SYNC_KEY`.

Prepare private state locally using the included migration/token tools. Transfer the resulting databases to:

```text
/var/data/crystal_guild.db
/var/data/twitch_tokens.db
```

Then run in the Render Shell:

```bash
python run_cloud_preflight.py
```

Continue only after `ALL CLOUD PREFLIGHT CHECKS PASSED.` Keep the old local Bot and standalone Portal sync stopped before the cloud worker connects.

The worker safely waits with `CLOUD BOOTSTRAP REQUIRED` rather than creating a blank Guild if either required database is absent.

The matching v1.1.16 Web deployment is required to use the hosted `/overlay` route and the Cloud Continuity website pass.
