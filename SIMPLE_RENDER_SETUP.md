# Simple Render Setup — v1.9.0 Alpha 7 Hall of Trophies

1. Preserve the existing Render persistent disk, live `crystal_guild.db`, Twitch token storage, and secrets.
2. Deploy the matching v1.9.0 Alpha 7 Bot and Web packages together.
3. Restart the Web service and Bot worker. Schema 19 migrates automatically to schema 20 with a verified `pre_schema_20_*.db` backup.
4. Confirm runtime `1.9.0-hall-of-trophies-alpha7`, schema **20**, hosted sync **1**, and Portal protocol **36**.
5. Open **Adventurer Profile → Hall of Trophies** and verify all 30 Trophy cards and art load.
6. Confirm existing provable trophies reconcile and that new World Event/Raid trophies only award participating players.
