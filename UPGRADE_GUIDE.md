# Upgrade Guide — Crystal Guild v1.6.0 Gold Saucer

## From RC2

1. Stop the Bot cleanly.
2. Keep your existing persistent database, secrets, and hosted environment values.
3. Replace the Bot source with the v1.6.0 production Bot or apply the RC2→v1.6.0 patch.
4. Start the Bot and verify `!cgversion` reports `1.6.0-gold-saucer`.
5. Deploy the matching v1.6.0 Web build.
6. Confirm `/api/health` reports runtime/frontend `1.6.0-gold-saucer`, hosted sync **1**, and Portal protocol **29**.
7. Open Gold Saucer and confirm the existing MGP balance, Triple Triad collection/deck, and active persistent state remain intact.

No schema migration is required from RC2; schema remains **13**.
