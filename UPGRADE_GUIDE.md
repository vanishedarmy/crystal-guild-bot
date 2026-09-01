# Upgrade to v1.7.0 Retainer Service Alpha 1

1. Stop the local Bot cleanly.
2. Back up the existing Crystal Guild directory/database as usual.
3. Apply the Alpha 1 Bot files.
4. Start the Bot. Schema 13 upgrades sequentially to schema **14**; a verified `pre_schema_14_*.db` backup is created before the structural migration.
5. Deploy the matching Alpha 1 Web build because Portal Action protocol is now **30**.
6. Confirm the Portal connection reports protocol 30 and open **Retainer Service** from Guild Services.

No player reset, MGP conversion, or Gold Saucer balance change is required.
