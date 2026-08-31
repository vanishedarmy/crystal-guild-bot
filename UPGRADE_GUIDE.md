# Upgrade Guide — v1.6.0 Gold Saucer Alpha 1 Hotfix 2

Supported baseline: **v1.6.0 Gold Saucer Alpha 1 Bot** plus **Alpha 1 Web Hotfix 1 — Visual Treatment**.

1. Stop the Bot worker and hosted Web service.
2. Back up `crystal_guild.db` and preserve `.env`, Twitch token storage, hosted secrets, and persistent-disk data.
3. Apply the Alpha 1 → H2 Bot patch or replace with the full H2 Bot tree.
4. Apply the Alpha 1 Web H1 → H2 Web patch or replace with the full H2 Web tree.
5. Restart/deploy both services.
6. Verify `!cgversion`, `!health`, and `/api/health` report `1.6.0-gold-saucer-a1h2`, hosted sync 1, Portal protocol 26, and local schema 11.
7. Open Gold Saucer and confirm Cactpot reports the UTC daily reset, Slots animate before showing the committed result, and the expanded personal records appear.

No database migration or player reset is required for H2; schema remains 11.
