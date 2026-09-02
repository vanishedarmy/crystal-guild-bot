# Upgrade to v1.7.0 Moogle Emporium Annex Alpha 3

Upgrade **Bot and Web together** from the verified v1.7.0 Retainer Service Alpha 2 Mobile Visual Hotfix 3 baseline.

Alpha 3 uses runtime `1.7.0-emporium-annex-a3`, local schema **15**, hosted sync **1**, and Portal Action protocol **31**. No database schema migration is required. The existing `fellowship_facilities` table receives the new `emporium_annex` facility row through the normal idempotent static-row seeding path, so existing player progression, inventory, Gil, MGP, Fellowship state, Retainer state/history, active adventures, and shop data are preserved.

The Annex is a one-time Fellowship construction project unlocked at Fellowship LVL 3. It requires **20,000 Gil**, **12 Mythril Ore**, **20 crafted items**, and the LVL 3 requirement. After completion, each personal Moogle Emporium rotation expands from **9 to 12 stock slots**. Existing nine-slot cached rotations are automatically invalidated when the Annex becomes active and are rebuilt using the established shop rules.

Prices, sell values, shop refresh timing, level/job eligibility, and the existing weighted item selection model are unchanged. Preserve your existing database and secrets; do not overwrite live environment files with packaged examples.
