CRYSTAL GUILD v1.1.15 — WAYFARER
=================================

Baseline: v1.1.14 — Cloud Continuity Hotfix 3c

Wayfarer includes:
- interactive, player-paced Solo Venture combat in the Adventurer Portal;
- up to 3 Solo Venture stages with Return / Press On risk-reward choices;
- 60% Encounter / 40% Treasure odds per stage;
- Attack, Ability, Use Item, and Defend Portal combat actions with enemy intent;
- persistent per-player Solo Venture state that does not occupy the shared Twitch battle slot;
- Portal profile tabs reordered around the most-used player actions.

Runtime: 1.1.15-wayfarer
Frontend: 1.1.15-wayfarer1
DB schema: 5
Hosted sync schema: 1
Portal Action protocol: 13

PRESERVE: .env, .tio.tokens.json, crystal_guild.db, Twitch token database, and private runtime state.

IMPORTANT: Existing schema-4 Guild databases are upgraded automatically to schema 5 on first open.
Crystal Guild creates and verifies backups/pre_schema_5_<timestamp>.db BEFORE the migration.
No player reset is required. No new Render secret or Twitch OAuth scope is required.
