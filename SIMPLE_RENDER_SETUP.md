# Simple Render Setup — v1.7.1 Resynthesis Alpha 2 Hotfix 3

1. Preserve `/var/data/crystal_guild.db`, Twitch tokens, and Render environment secrets.
2. Deploy the Hotfix 3 Bot with the existing Alpha 2 Web build.
3. Restart the worker and verify `!cgversion` = `1.7.1-resynthesis-a2h3`.
4. Confirm schema **15**, hosted sync **1**, and Portal protocol **32**.
5. Test one MP↔AP Job switch and confirm inactive resource values are preserved.

No database migration or player reset is required.
