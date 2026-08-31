# Crystal Guild v1.6.0 — Gold Saucer Alpha 1 Simplified Render Setup

**Existing cloud install:** preserve `/var/data` and all Render environment variables, stop any duplicate/local Bot, deploy the v1.6.0 Alpha 1 Bot, then deploy the matching Web source.

1. Back up or snapshot persistent state before deployment.
2. Deploy the Bot and allow the verified **schema 10 → 11** migration to complete.
3. Confirm `!cgversion` = `1.6.0-gold-saucer-a1h2` and `!health` is clean.
4. Deploy/restart the matching v1.6.0 Alpha 1 Web service.
5. Confirm `/api/health` reports runtime/frontend `1.6.0-gold-saucer-a1h2`, hosted sync **1**, protocol **26**.
6. Open **Gold Saucer** on your own character and test Mini Cactpot plus one Crystal Slots spin.

Gold Saucer Alpha 1 adds no environment variables and requires no player reset or OAuth reauthorization.
