# Crystal Guild v1.9.0 Alpha 4 — Navigation Accessibility Upgrade Guide

## From v1.9.0 Alpha 3
Deploy the matching Alpha 4 Bot and Web packages together and restart the services. Existing player data, MGP, titles, achievements, Trading Post listings, inventories, Fellowship state, Mercs, and Gold Saucer records are preserved.

No database migration is required for Alpha 3 → Alpha 4. The release continues to use:
- Runtime/frontend: `1.9.0-navigation-accessibility-alpha4`
- Local schema: **19**
- Hosted sync: **1**
- Portal Action protocol: **36**

## Existing migration history
Older installations still upgrade through the existing verified migrations. v1.8.1 introduced schema **17 → 18** for Merc recruitment. v1.9.0 Alpha 1 introduced schema **18 → 19** for the Moogle Trading Post, creating a verified `pre_schema_19_*.db` backup before migration.

## After deployment
1. Confirm `!cgversion` reports `1.9.0-navigation-accessibility-alpha4`.
2. Open any player profile and confirm the section navigation has subtle color identities with readable icon + text labels.
3. Check a compact desktop/tablet width and confirm the grid reflows without clipping.
4. Check mobile and confirm the profile sections remain a two-column touch grid rather than collapsing to the old dropdown.
5. Verify keyboard focus is clearly visible and the active tab remains obvious without relying on color alone.
6. Keep the live database at its existing persistent path (for Render, normally `/var/data/crystal_guild.db`).

No player reset is required.
