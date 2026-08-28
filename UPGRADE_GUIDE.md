# Upgrade Guide — v1.2.0 Expeditions Alpha 2

Baseline: **Expeditions Alpha 1 Hotfix 1 Bot** with the **Alpha 1 Hotfix 3 Web**.

1. Stop the Bot.
2. Back up the current database and persistent Twitch token data as normal.
3. Apply the Alpha 1 Hotfix 1 → Alpha 2 Bot patch, or replace application files with the full Alpha 2 Bot package while preserving `.env`, the database, and token storage.
4. Deploy the matching Alpha 2 Web package (or the Alpha 1 Hotfix 3 → Alpha 2 Web patch).
5. Start the Bot and verify `!cgversion` reports runtime `1.2.0-expeditions-a2`, local schema **8**, and Portal Action protocol **20**.
6. Open the Adventure Board and verify existing region exploration percentages are unchanged.
7. At 75%+ regional exploration, verify the Regional Boss Contract control is available.

**No database migration or player reset is required.** Local schema remains 8, hosted sync schema remains 1, and Portal Action protocol remains 20. Existing Alpha 1 Expedition rows and exploration records are reused directly.
