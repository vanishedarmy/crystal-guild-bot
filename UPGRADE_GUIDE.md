# Upgrade Guide — Triple Triad Full Card Face Sync H5

1. Stop the current Bot cleanly.
2. Back up the persistent database as usual.
3. Replace the Bot files with the H5 Bot build or apply the H4→H5 Bot patch.
4. Deploy the matching H5 Web build in the same maintenance window.
5. Start the Bot and verify `!cgversion` reports `1.6.0-gold-saucer-a5h5`.
6. Verify `/api/health` reports runtime/frontend `1.6.0-gold-saucer-a5h5`, hosted sync **1**, and Portal protocol **29**.
7. Open Triple Triad and confirm full card faces are visible with no duplicate upper-left UI numbers.
8. Confirm Chocobo, Moogle, Cactuar, Bomb, and Flan captures follow their printed values.

No database migration or player reset is required.
