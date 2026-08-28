# Upgrade Guide — Crystal Guild v1.2.0 Expeditions Alpha 4

## Supported direct baseline
Alpha 4 includes direct patches from **Expeditions Alpha 3** Web and Bot.

1. Stop the Alpha 3 Bot.
2. Back up the database and persistent token data as normal.
3. Apply the **A3 → A4 Bot patch** or replace application files with the full Alpha 4 Bot package, preserving `.env`, database files, and token storage.
4. Deploy the **A3 → A4 Web patch** or full Alpha 4 Web package.
5. Start the Bot and confirm `!cgversion` reports `1.2.0-expeditions-a4`, schema **8**, and protocol **20**.
6. Hard-refresh the Portal once. Confirm the Expedition Atlas shows landmark totals and route choices show rare-event odds.

No database migration, player reset, OAuth reconfiguration, hosted-sync change, or new environment variable is required. Existing Alpha 3 Atlas, boss-clear, Mastery, and Legendary Contract progression is preserved.
