# Upgrade Guide — v1.6.0 Gold Saucer Alpha 5

Supported source: the canonical v1.6.0 Gold Saucer Alpha 4 / Web H1 baseline.

1. Preserve the live database, `.env`, Twitch token storage, hosted secrets, and persistent-disk state.
2. Replace the Bot source with the Alpha 5 Bot package.
3. Deploy the matching Alpha 5 Web package; protocol 29 is required for Triple Triad actions.
4. Restart/redeploy the services. The Bot performs the additive schema **12 → 13** migration automatically and creates a verified `pre_schema_13_<timestamp>.db` backup before changing a legacy database.
5. Verify `!cgversion` reports `1.6.0-gold-saucer-a5`.
6. Verify the hosted health endpoint reports runtime/frontend `1.6.0-gold-saucer-a5`, hosted sync 1, and Portal protocol 29.
7. Open Gold Saucer and confirm the existing MGP balance is unchanged, Triple Triad grants the starter deck, and existing attractions retain their prior balances and records.

No player reset is required.
