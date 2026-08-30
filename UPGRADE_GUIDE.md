# Upgrade Guide — Crystal Guild v1.4.0 Dungeons & Delves

Baseline: **Dungeons & Delves RC1 Web + Bot**.

1. Preserve the existing database, `.env`, Twitch token storage, hosted secrets, and persistent-disk data.
2. Apply the RC1 → v1.4.0 Bot patch or deploy the full production Bot package.
3. Apply the RC1 → v1.4.0 Web patch or deploy the full production Web package.
4. Redeploy/restart Web and Bot together.
5. Verify `/api/health` reports Web/frontend `1.4.0-dungeons-delves`, hosted sync schema **1**, and protocol **25**.
6. Verify `!cgversion` reports Bot `1.4.0-dungeons-delves` and local schema **10**.
7. Resume an existing Dungeon if one was active and confirm chamber, HP/MP/AP, Cache, route effects, and controls remain intact.
8. Spot-check the Dungeon Board on desktop/mobile, including right-aligned disclosure placement on narrow screens.

No DB migration, player reset, OAuth/environment change, new environment variable, protocol change, or gameplay/economy rebalance is required from RC1.
