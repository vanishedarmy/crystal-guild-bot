CRYSTAL GUILD v1.1.14 — CLOUD CONTINUITY HOTFIX 3
=================================================

Hotfix 3 fixes three player-facing issues:
  1. Live Rally Venture encounter information now stays inside the Rally Venture panel.
  2. Raid participants can queue !attack, !ability, !defend, and !use for each round.
  3. Portal selectable buttons/filters have clearer labels, contrast, selected states, and focus states.

NO DATA MIGRATION
-----------------
Local DB schema remains 4. Do not replace crystal_guild.db.
Hosted sync schema remains 1 and Portal Action protocol remains 12.

UPGRADING FROM HOTFIX 2
-----------------------
Use the Bot Patch from Hotfix 2 and Web Patch from Hotfix 2, then redeploy both services.
No new Render secret or OAuth scope is introduced by Hotfix 3.

The existing Hotfix 2 subscriber feature still needs channel:read:subscriptions if that broadcaster authorization has not already been completed.

See UPGRADE_GUIDE.md for the deployment sequence and VALIDATION_REPORT.md for test results.
