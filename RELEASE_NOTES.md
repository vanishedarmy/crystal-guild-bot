# Crystal Guild v1.9.3 — Guild Initiatives

This incremental source release merges into the already-installed Alpha 13 + v1.9.1 + v1.9.2 codebase. It adds three rotating weekly Fellowship Contracts and three daily plus three weekly optional individual Guild Board objectives. Each verified gameplay event contributes once to all applicable objectives. Completion rewards deliver automatically and are transaction-guarded against duplicates.

**Reset schedule:** Daily 00:00 UTC; weekly and Fellowship Contracts Monday 00:00 UTC. **Eligible events:** combat victories and Hunts, completed craft/forge actions, and completed Ventures/Expeditions. Ore-gathering is intentionally excluded until an authoritative ore-gathering event exists.

**Rewards:** Guild-wide Gil/material payouts to all members present at contract completion; individual Gil/material payouts and weekly optional suitable shop gear, with a two-Mythril-Ore alternative if no level-suitable modest-price gear exists. No manual claiming.

**Migration:** Local Bot schema 25 → 26 adds four objective progress/receipt tables and a small periodic maintenance table. Before upgrading an existing database, the engine creates its normal verified migration backup. Old player progress, inventory, Trading Post transactions, Relics and existing Fellowship projects remain untouched. Expired objective rows are pruned weekly (daily records after 45 days; weekly/communal records after 18 weeks); permanent transaction and Fellowship event audit records remain.

**Protocol:** Existing Portal Action protocol 39, existing sync schema 1. Bot and hosted Web must both deploy v1.9.3. The Guild Board is a new read-only hosted player snapshot module; Fellowship Contracts appear in the existing shared Fellowship snapshot. The server/browser release markers have been updated to invalidate stale assets.

**Distribution:** This is ONE final changed-files merge for an existing Alpha13 installation with subsequent 1.9.1 and 1.9.2 patches already merged. It does NOT include the ~200 MB unchanged public artwork library, an initialized database, private configuration, or a prebuilt frontend bundle. Run `npm ci` and `npm run build` in `Web/frontend/` after merging; see BUILD_GUILD_INITIATIVES_1_9_3.cmd. Do not use the old 1.9.2 compiled frontend. Test on staging, back up the live DB and restart the Bot and hosted Web together.

## Previous Alpha13 release notes (historical)

# Crystal Guild v1.9.0 Alpha 13 — Trading Post QoL

This is a complete source release built on the verified Alpha 12 Camp & Recovery baseline. The archive contains matching Bot, hosted Web, React/Vite frontend and all 954 public assets already correctly nested at `Web/frontend/public/`. No assets need to be downloaded or merged separately.

## New Trading Post features
- Character-bound watchlist of up to **30 tradeable items**, even without active listings; validated at the hosted relay, enforced by the Bot, and persisted in new schema 25.
- Owned quantities visible on browse cards; a Watchlist tab shows live minimum asking price, listing count and owned count for each saved item.
- Recently Sold tab: **completed trades only** over the preceding **30 days**, with a global recent list and per-item last **12** sales; no seller/buyer identity is exposed in public historical summaries.
- Quantity-weighted 30-day sale average with min/max and number of sales. Asking-price indicators appear at more than **±10%** and only after **three completed sales**. Sparse or missing history is labeled as such, not guessed.
- One-click Quick Relist on past sold, expired or cancelled listings when the original quantity is available unequipped and the player can pay the normal 2% new listing fee. Edit & Relist prefills quantity and former price for review. The existing atomic listing endpoint rechecks stock, Gil, combat lock, item eligibility and 24-slot limit; no past items are recreated for free.

## Retained rules
Fixed-price player-to-player trades; 48-hour listings; 2% listing fee and 5% sale tax; 24 active listings; no automatic market purchases, bidding, market-maker processes or price setting. Existing Camp, Records & Moments and Mobile Combat HUD remain unchanged.

## Compatibility and migration
- Both Bot and hosted Web must run `1.9.0-trading-post-qol-alpha13` with Portal Action protocol **39**. The hosted sync schema remains **1**.
- Local Bot SQLite schema automatically upgrades **24 → 25** and writes a verified pre-migration backup under the data mount's `backups/` directory. New table: `trading_post_watchlist`; existing `trading_post_listings` retains every original sale and listing. New sale-ledger indexes support efficient read-only 30-day reports.
- New Portal actions: `TRADING_POST_WATCH` (exact `item_id`, `watched` boolean, idempotent) and read-only `TRADING_POST_HISTORY` (exact `item_id`). Both require the same linked account as other Trading Post controls.

## Build and deploy
This is a **source release**, not a deployed service or prebuilt `dist`. From `Web/frontend/`, use `npm ci` and `npm run build` on a machine with npm registry access and compatible Node, then deploy matching Bot and Web source. Preserve persistent databases, existing credentials, private configuration and live mounts. Do not reuse an old frontend bundle. Check migrations, watch/unwatch after browser reload, current browsing inventory, history after a completed sale, quick relist and payment rules, and mobile category wrapping on staging first.

## Source and assets
`Web/frontend/public/` includes all public assets from Alpha 12 unchanged. Prior lossless Trading Post artwork optimization is preserved. `SOURCE_SHA256.txt` inventories release files, and the archive contains explicit directory entries so standard ZIP viewers show all folders.
