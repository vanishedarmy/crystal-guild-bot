# Upgrade Guide — Crystal Guild v1.4.0 Dungeons & Delves RC1

Baseline: **Dungeons & Delves Beta 3 Web + Bot**.

1. Make the normal verified backup of the live player database and preserve `.env` plus Twitch token storage.
2. Stop the Bot cleanly before replacing source.
3. Apply the **Beta 3 → RC1 Bot patch** or replace the Bot source while preserving persistent/private state.
4. Apply the **Beta 3 → RC1 Web patch** or deploy the full RC1 Web package.
5. Restart/redeploy Web and Bot together.
6. Verify `!cgversion` reports `1.4.0-dungeons-rc1` with local schema **10**.
7. Verify `/api/health` reports Web/frontend `1.4.0-dungeons-rc1`, hosted sync schema **1**, and Portal Action protocol **25**.
8. Open Dungeon Board on desktop and mobile; confirm the disclosure pointer stays on the right, uses right-hand closed / down-hand open, and all four Dungeons are present.
9. Resume or start a Dungeon, confirm current run/chamber/revision state refreshes correctly, and verify normal retreat/result records remain intact.
10. Run `python run_maintenance.py --recovery-drill` if you want the non-destructive local recovery check before going live.

No database migration, player reset, OAuth change, protocol change, new environment variable, or gameplay/economy rebalance is required from Beta 3.
