# Upgrade Guide — v1.3.0 Guild Expansion Beta 3

Baseline: **Beta 2 Web + Beta 1 Bot**.

1. Back up the current player database and persistent Twitch/token data.
2. Stop the Bot.
3. Apply the Beta 1 → Beta 3 Bot patch, or replace Bot source with the full Beta 3 Bot package while preserving `.env`, the live database, token storage, and persistent-disk configuration.
4. Deploy the Beta 2 → Beta 3 Web patch or full Beta 3 Web package.
5. Restart the Bot.
6. Verify `!cgversion` reports `1.3.0-guild-expansion-b3`.
7. Verify `/api/health` reports Web/frontend `1.3.0-guild-expansion-b3`, hosted sync schema **1**, and Portal Action protocol **22**.
8. Open your Fellowship tab and refresh once. Test one Guild contribution against the currently displayed project.
9. If practical, change the active project while an older browser tab is still open and confirm the stale tab asks for a refresh instead of donating to the new project.
10. Check the Guild Airship and confirm its current Ready/mission state survived deployment.

No database migration is required from Beta 1/Beta 2; schema **9** remains current. Existing facilities, projects, contribution progress, Weekly Orders, Workshop services, Airship state/upgrades/history, Guild Legacy, Expeditions, and player progression are preserved. No player reset, OAuth change, or new environment variable is required.
