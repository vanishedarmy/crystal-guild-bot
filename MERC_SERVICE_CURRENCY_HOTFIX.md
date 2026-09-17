# Crystal Guild v1.8 Merc Service Alpha 1 — Hunt Seal Currency Hotfix

- Hero Merc contracts now spend the existing **Hunt Seals** balance.
- Hunts no longer award a second Merc-only currency.
- Hunt rewards continue to grant their normal configured Hunt Seals.
- Merc fees remain unchanged numerically; only the currency source is corrected.
- Cancelling a Merc contract remains non-refundable.
- Existing schema 17 databases require no reset or new migration.
- A legacy `hunt_marks` column may remain in databases created by an earlier Alpha 1 batch, but it is no longer used by the game.
