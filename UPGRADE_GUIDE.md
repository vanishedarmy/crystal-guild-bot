# Upgrade Guide — v1.4.0 Dungeons & Delves Alpha 1

Baseline: **v1.3.1 Asset Optimization UI4 Web + v1.3.1 Asset Optimization Bot**. Portal Action protocol advances **22 → 23**, so deploy the matching Alpha 1 Web and Bot together.

1. Back up the current player database and persistent Twitch/token data.
2. Stop the Bot cleanly.
3. Apply the v1.3.1 → v1.4 Alpha 1 Bot patch, or replace the Bot source while preserving `.env`, the live database, token storage, and persistent-disk configuration.
4. Deploy the UI4 → v1.4 Alpha 1 Web patch or the full Alpha 1 Web package.
5. Start the Bot. On first startup, schema **9 → 10** runs automatically and creates a verified pre-schema-10 database backup.
6. Redeploy/restart the hosted Web service.
7. Verify `!cgversion` reports `1.4.0-dungeons-a1` and local schema **10**.
8. Verify `/api/health` reports Web/frontend `1.4.0-dungeons-a1`, hosted sync schema **1**, and Portal Action protocol **23**.
9. Open **Adventure Board → Dungeons & Delves**. Confirm The Forgotten Ossuary is locked until Lv. 10 + 25% Emerald Wilds exploration, then test starting a run on an eligible character.
10. Advance at least one chamber and, if practical, leave an older browser tab open. Confirm an action from the stale tab is rejected and asks for a refresh rather than mutating the newer run/chamber.
11. Confirm HP/MP/AP, Dungeon Cache, and current chamber persist after a Portal refresh. If practical in staging, restart the Bot and confirm the active run resumes intact.
12. Confirm existing player, Fellowship, Airship, Expedition, inventory, Bestiary, achievement, title, and equipment progression remains intact.

No player reset, OAuth change, or new environment variable is required. The schema migration is additive and preserves existing data.
