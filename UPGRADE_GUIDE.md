# Upgrade Guide — Crystal Guild v1.3.0 Guild Expansion Alpha 4

Baseline: **v1.3.0 Guild Expansion Alpha 3**.

Alpha 4 advances the local Bot database from **schema 8 → 9**. The migration is additive and creates a verified pre-schema-9 database backup before the new Airship tables are added. Portal Action protocol remains **21**.

1. Back up the current player database and persistent Twitch/token data as usual.
2. Stop the Bot cleanly.
3. Apply the **Alpha 3 → Alpha 4 Bot patch**, or replace the Bot application files with the full Alpha 4 Bot package while preserving `.env`, database files, and token storage.
4. Start the Alpha 4 Bot once and allow the normal migration to complete. Confirm the local DB reports schema **9**.
5. Deploy the matching **Alpha 3 → Alpha 4 Web patch** or full Alpha 4 Web package.
6. Confirm `!cgversion` reports `1.3.0-guild-expansion-a4`.
7. Confirm `/api/health` reports runtime/frontend revision `1.3.0-guild-expansion-a4`, hosted sync schema **1**, and Portal Action protocol **21**.
8. Open Fellowship and confirm the Airship Dock is buildable rather than marked as future construction.
9. If the Guild already meets the requirements, verify Airship Dock Lv. 1 exposes the **Crystal Guild Airship** construction project.
10. After the Airship is built, confirm `!airship` and the Fellowship page show the mission catalog and upgrade tracks.
11. From the Streamer Dashboard or chat, launch a test mission with `!airshipmission <mission>` and confirm matching normal Guild activity advances its progress.
12. Verify existing Fellowship facilities/projects, Weekly Orders, Workshop services, Chocobos, Expeditions, inventories, and character progression remain intact.

No player reset, OAuth change, or new environment variables are required. Existing progress is preserved by the schema-9 migration.
