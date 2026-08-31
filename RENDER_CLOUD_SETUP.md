# Crystal Guild v1.6.0 — Gold Saucer Alpha 4 Render Cloud Setup

Preserve the worker's persistent `/var/data` state and all Render environment variables. Do not package or overwrite the live database, token databases, `.env`, or hosted secrets.

Typical persistent paths remain:
```text
/var/data/crystal_guild.db
/var/data/twitch_tokens.db
/var/data/overlay/state.json
```

Deploy the Alpha 4 Bot source and restart the worker. There is **no database migration**: local schema remains **12**, hosted sync remains **1**, and Portal Action protocol advances to **28**.

After deployment verify `!cgversion` reports `1.6.0-gold-saucer-a4`, then open Gold Saucer and confirm the existing balance is unchanged and displayed/reported as **MGP**. Mini Cactpot, Crystal Slots, Monster Toss, and Prize Counter should retain their prior numeric behavior.

Deploy the matching Alpha 4 Web relay with this Bot because `CHOCOBO_RACE` requires Portal protocol 28. Run `python run_cloud_preflight.py` before reconnecting a moved/restored worker. No player reset is required. The hosted raid overlay route remains `/overlay` on the matching Web service.
