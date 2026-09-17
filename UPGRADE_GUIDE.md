# Upgrade Guide — Merc Service Alpha 1 Batch 4

Batch 4 should be applied on top of **Merc Service Alpha 1 Batch 3 Web** and **Batch 2 Bot**.

- Web: update to the Batch 4 Web package or apply the incremental Web patch.
- Bot: update to the Batch 4 Bot package or apply the small incremental Bot patch for Merc help.
- Preserve live databases, hosted secrets/tokens, and persistent runtime state.
- No player reset is required.
- No new DB migration is introduced beyond schema **17** already established in Batch 1.
- Portal Action protocol remains **34**.
- Merc artwork is not included; integrate the approved art set in Batch 5.
