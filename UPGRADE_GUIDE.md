# Crystal Guild v1.1.17 — Arsenal II Hotfix 4 Upgrade Guide

Upgrade baseline: **v1.1.17 — Arsenal II Hotfix 3**.

Hotfix 4 is a **paired Bot + Web update** because the Solo Venture encounter/treasure balance is authoritative on the Bot while the Hunt-result/accessibility pass is presented by the Web client.

1. Stop/redeploy the Bot worker as you normally do for a paired update.
2. Preserve private/runtime files and persistent data: `.env`, Twitch token storage, `crystal_guild.db`, and Render persistent-disk paths.
3. Apply the **Bot Patch from Hotfix 3** to the Bot source, or replace it with the full Hotfix 4 Bot package.
4. Apply the **Web Patch from Hotfix 3** to the hosted Web source, or replace it with the full Hotfix 4 Web package.
5. Redeploy both services.
6. Verify `!cgversion` reports `1.1.17-arsenal-ii-h4`.
7. Verify hosted `/api/health` reports runtime `1.1.17-arsenal-ii-h4` and frontend revision `1.1.17-arsenal-ii1h4`.
8. Open Adventure Board and confirm Solo Venture displays **80 / 20 Encounter / Treasure**.
9. Resolve a Hunt and confirm the Portal shows a structured Last Hunt Result card rather than raw chat-style lines.
10. Check desktop and phone widths for compact status blocks, readable disabled controls, and Hunt result reflow.

No schema migration or manual SQLite edit is required. Player progression is preserved.
