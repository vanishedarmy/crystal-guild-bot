# Crystal Guild v1.6.0 — Gold Saucer Render Cloud Setup

Preserve the worker's persistent `/var/data` state and all Render environment variables. Do not package or overwrite the live database, token databases, `.env`, or hosted secrets.

Typical persistent paths remain:
```text
/var/data/crystal_guild.db
/var/data/twitch_tokens.db
/var/data/overlay/state.json
```

Deploy the Alpha 5 Bot source and restart the worker. The additive local database migration advances schema **12 → 13** and creates a verified pre-schema backup. Hosted sync remains **1**, and Portal Action protocol advances to **29**.

After deployment verify `!cgversion` reports `1.6.0-gold-saucer`, then open Gold Saucer and confirm the existing MGP balance is unchanged. Mini Cactpot, Crystal Slots, Monster Toss, Chocobo Racing, and Prize Counter retain their prior numeric behavior.

Deploy the matching Alpha 5 Web relay with this Bot because Triple Triad requires Portal protocol 29. Run `python run_cloud_preflight.py` before reconnecting a moved/restored worker. No player reset is required. The hosted raid overlay route remains `/overlay` on the matching Web service.
