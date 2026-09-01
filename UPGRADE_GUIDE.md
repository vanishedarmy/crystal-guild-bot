# Upgrade Guide — v1.6.0 Gold Saucer RC2

1. Stop the Bot cleanly and keep your existing SQLite database.
2. Back up the database before replacing files.
3. Replace the Bot source with the RC2 Bot package or apply the **RC1 → RC2 Bot patch**.
4. Start the Bot and verify `!cgversion` reports `1.6.0-gold-saucer-rc2`.
5. Deploy the matched RC2 Web build or RC1 → RC2 Web patch in the same maintenance window.
6. Confirm `/api/health` reports runtime/frontend `1.6.0-gold-saucer-rc2`, hosted sync **1**, and Portal protocol **29**.
7. Open Gold Saucer and confirm existing MGP balances, prizes, race records, Triple Triad collection/deck, and active-state persistence are intact.
8. Confirm Mini Cactpot shows the RC2 table (10 MGP ticket, 1,000 MGP sum-6 jackpot) and the Saucer Ledger exposes Cactpot W / D / L.

No schema migration or player reset is introduced by RC2. Existing RC1 Cactpot history remains valid; new tickets use the RC2 payout table.
