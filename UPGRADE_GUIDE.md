# Crystal Guild v1.1.16 — Arsenal Hotfix 6 Upgrade Guide

Upgrade baseline: **v1.1.16 — Arsenal Hotfix 5**.

1. Stop/restart the Bot worker as you normally would for a Bot update.
2. Preserve runtime/private files such as `.env`, Twitch token databases, and `crystal_guild.db`.
3. Overlay the Hotfix 6 Bot/update files onto the existing installation.
4. Leave the deployed Hotfix 5 Web files in place; no Web change is required.
5. Start/redeploy the Bot worker.
6. Verify `!cgversion` reports `1.1.16-arsenal-h6`.
7. Claim/test Daily Guild Provisions when eligible. Chocobo Registration Writs and other unapproved special/progression items must never appear.
8. If a player previously received an orphaned Daily Writ, opening/checking Chocobo state will remove only that invalid Writ so the normal purchase path is available again.

No schema migration is performed; local DB schema remains 5.
