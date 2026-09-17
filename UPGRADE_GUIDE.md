# v1.8.0 Alpha 2 Upgrade Notes

Alpha 2 upgrades cleanly from v1.8 Alpha 1 Hotfix 3.

- No schema change: remains **17**.
- No hosted sync change: remains **1**.
- No Portal protocol change: remains **34**.
- Existing Hunt/Venture/Raid Merc contracts remain valid.
- No Hunt Seal refund or conversion is needed.
- New fees apply only to future hires; already-paid active contracts are not repriced.
- No player reset is required.

# Upgrade Guide — Merc Service Alpha 1 Batch 4

Batch 4 should be applied on top of **Merc Service Alpha 1 Batch 3 Web** and **Batch 2 Bot**.

- Web: update to the Batch 4 Web package or apply the incremental Web patch.
- Bot: update to the Batch 4 Bot package or apply the small incremental Bot patch for Merc help.
- Preserve live databases, hosted secrets/tokens, and persistent runtime state.
- No player reset is required.
- No new DB migration is introduced beyond schema **17** already established in Batch 1.
- Portal Action protocol remains **34**.
- Merc artwork is not included; integrate the approved art set in Batch 5.


## Schema continuity
Merc Service remains on schema **17**. Upgrading an older schema **16 → 17** database creates the Merc contract tables after the normal verified `pre_schema_17` backup. The currency hotfix does not add another migration.
