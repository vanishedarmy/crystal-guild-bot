# Crystal Guild v1.1.14 — Cloud Continuity Hotfix 3c Upgrade

Hotfix 3c is an in-place Bot + Web update for the **Hotfix 3b** baseline. Player progression and runtime state remain compatible.

## Upgrade from Hotfix 3b

1. Stop the local Crystal Guild Bot/Portal sync cleanly.
2. Preserve `.env`, `.tio.tokens.json`, `crystal_guild.db`, `/var/data/twitch_tokens.db` (cloud installs), and other private runtime files.
3. Make the normal verified backup of `crystal_guild.db`.
4. Apply the **Hotfix 3b → Hotfix 3c Update** package over the existing installation. It contains both the Bot economy fix and the Web UI/mobile changes.
5. Deploy the matching Web files to the hosted repository/Render service.
6. Restart the Bot and Portal sync.
7. Verify `!cgversion` / `!health` reports `1.1.14-cloud-continuity-h3c`.
8. Verify Web `/api/health` reports frontend revision `1.1.14-continuity3c`.
9. Open Equipment & Inventory and confirm the **Current Loadout** summary matches the equipped Weapon/Armor/Accessory.
10. On mobile, scroll down to hide the header, then scroll upward and confirm it returns without tapping elsewhere.
11. Check **Stimulating the Economy**; its progress should reflect lifetime negative-Gil transaction history.

## Migration / authorization

- Local DB schema remains **4** — no migration helper runs.
- Hosted sync schema remains **1**.
- Portal Action protocol remains **12**.
- No new Render secret is required.
- No new Twitch OAuth scope is introduced. If subscriber perks already work, do not re-authorize solely for Hotfix 3c.
