# Upgrade Guide — Crystal Guild v1.2.0 Expeditions Alpha 5

## Supported direct baseline
Alpha 5 includes direct patches from **Expeditions Alpha 4** Web and Bot.

1. Stop the Alpha 4 Bot.
2. Back up the current database and persistent token data as normal.
3. Apply the **A4 → A5 Bot patch** or replace application files with the full Alpha 5 Bot package, preserving `.env`, database files, and token storage.
4. Deploy the **A4 → A5 Web patch** or full Alpha 5 Web package.
5. Start the Bot and confirm `!cgversion` reports `1.2.0-expeditions-a5`, schema **8**, and protocol **20**.
6. Hard-refresh the Portal once. In the Chocobo Stable, confirm the registered companion shows a specialty derived from its existing trait and a Bond tier derived from its current Chocobo level.
7. Complete a Scout Expedition and confirm the result shows a **2 Hunt Seal** Guild stipend.

No database migration, player reset, OAuth reconfiguration, hosted-sync change, new environment variable, or new currency is required. Existing Alpha 4 Atlas, landmarks, Journal, Regional Boss, Mastery, Legendary Contract, Chocobo trait, and Bond progression are preserved.
