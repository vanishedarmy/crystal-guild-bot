# Upgrade Guide — v1.3.1 Asset Optimization

Baseline: **v1.3.0 Guild Expansion Web + Bot**.

1. Back up the current player database and persistent Twitch/token data.
2. Stop the Bot cleanly.
3. Apply the v1.3.0 → v1.3.1 Bot patch, or replace the Bot source while preserving `.env`, the live database, token storage, and persistent-disk configuration.
4. For the Web component, the **full v1.3.1 Web package is the simplest option** because this release intentionally removes the superseded PNG artwork.
5. If using the Web patch instead, extract it and run the included `apply_patch.py <path-to-current-web-root>` so the old PNG files are removed as well as the new WebP files copied in. A plain overlay copy will work visually but will not reclaim the old PNG disk space.
6. Restart/redeploy the Bot and hosted Web service.
7. Verify `!cgversion` reports `1.3.1-asset-optimization`.
8. Verify `/api/health` reports Web/frontend `1.3.1-asset-optimization`, hosted sync schema **1**, and Portal Action protocol **22**.
9. Open the Portal and spot-check Overview, Adventure Board, Fellowship, Equipment/Inventory, Bestiary/Hunts, Chocobo Stable, Relic Arsenal, Moogle Emporium, Blacksmith, and Player Guide artwork.
10. Confirm existing player/Fellowship/Airship/Expedition state remains intact.

No database migration is required; local schema **9** remains current. No player reset, OAuth change, environment-variable change, or gameplay rebalance is included.
