# Upgrade Guide — v1.6.0 Gold Saucer RC1

1. Stop the Bot cleanly.
2. Back up the live SQLite database before replacing files.
3. Replace the Bot source with the RC1 package or apply the H5 → RC1 Bot patch.
4. Preserve your existing `.env`, OAuth/token state, live database, and runtime directories.
5. Start the Bot and verify `!cgversion` reports `1.6.0-gold-saucer-rc1`.
6. Deploy the matched RC1 Web build; Portal Action protocol remains **29**.
7. Confirm `/api/health` reports runtime/frontend `1.6.0-gold-saucer-rc1`, hosted sync **1**, and Portal protocol **29**.
8. Open Gold Saucer and confirm the existing MGP balance, Triple Triad collection/deck, race records, Toss records, and Prize Counter ownership are unchanged.
9. Optional RC verification: start a Monster Toss game or Triple Triad match and confirm the daily remaining count decreases immediately.

No schema migration is required: local schema remains **13**.
