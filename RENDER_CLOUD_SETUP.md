# Crystal Guild v1.7.0 — Retainer Service Alpha 1 Render Cloud Setup

Preserve the worker's persistent `/var/data` state and all Render environment variables. Do not package or overwrite the live database, token databases, `.env`, or hosted secrets.

Typical persistent paths remain:
```text
/var/data/crystal_guild.db
/var/data/twitch_tokens.db
/var/data/overlay/state.json
```

Deploy the v1.7.0 Alpha 1 Bot source and restart the worker. The additive local database migration advances schema **13 → 14** and creates a verified `pre_schema_14_*.db` backup. Hosted sync remains **1**, and Portal Action protocol advances to **30**.

After deployment verify `!cgversion` reports `1.7.0-retainer-a1`, then open Retainer Service and confirm the existing player Gil/inventory and Gold Saucer MGP balance are unchanged. Retainer dispatch uses Gil; v1.6.0 Gold Saucer attraction balance remains unchanged.

Deploy the matching v1.7.0 Alpha 1 Web relay with this Bot because Retainer Service requires Portal protocol 30. Run `python run_cloud_preflight.py` before reconnecting a moved/restored worker. No player reset is required. The hosted raid overlay route remains `/overlay` on the matching Web service.
