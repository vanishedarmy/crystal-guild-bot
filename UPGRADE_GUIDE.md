# Upgrade to v1.7.0 Alpha 3 — Item Recovery Integrity Hotfix 1

Upgrade **Bot and Web together** from the Moogle Emporium Annex Alpha 3 build.

- Runtime/frontend: `1.7.0-emporium-annex-a3h1`
- Local DB schema: **15** (unchanged)
- Hosted sync: **1** (unchanged)
- Portal Action protocol: **31** (unchanged)
- Prefix: `!`

Preserve the existing database and live secrets. No migration or player reset is required.

This hotfix does not alter restorative item potency. It clarifies max-resource capping in Recover & Equip and field-use result messages, and adds regression coverage proving the canonical recovery values remain intact.
