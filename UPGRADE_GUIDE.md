# Upgrade Guide — v1.1.19 Retro Phase III RC1 Hotfix 6

1. Stop the current Bot cleanly.
2. Preserve the existing database and `.env`. Do not replace or reset player data.
3. Deploy the RC1H6 Bot package or apply the Bot patch.
4. Start the Bot. On first launch from schema 6, Crystal Guild creates a verified `pre_schema_7_*.db` backup and adds the `portal_adventure_results` table.
5. Deploy the paired RC1H6 Web package/patch. Both sides must use Portal Action protocol **17**.
6. Verify `!cgversion` reports `1.1.19-retro-phase-iii-rc1h6` and Portal Action protocol 17.
7. Verify the database schema reports **7** and `PRAGMA quick_check` passes.
8. Test a Portal-origin timed Hunt: leave the Portal before it resolves, return after resolution, verify the result remains, then use **Confirm Result**.

No player reset, OAuth change, or new environment variable is required.
