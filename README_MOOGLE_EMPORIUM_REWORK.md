# Moogle Emporium — Regional Rework

This update extends the current v1.9.6 — Triple Triad Expanded package. It includes the Triple Triad progression fix and shared lock icons. No new official release number is assigned.

## Regional counters

The current world-map region controls your Moogle counter. Compatible gear follows the local tier and your character level/Job. Potion, Antidote, Echo Herbs and Trail Rations remain available everywhere. Each region has featured supplies, and the strongest available local compatible weapon, armor and accessory are included before alternate goods are selected.

| World-map region | Counter | Maximum listings | Local weapon/armor tier |
| --- | --- | ---: | --- |
| Greenwind Plains | Trailside Counter | 12 | 1–7 |
| Whispering Caverns | Lantern Counter | 14 | 5–15 |
| Sable Coast | Harbor Counter | 16 | 12–27 |
| Magitek Wastes | Salvager's Counter | 18 | 20–41 |
| Crystal Expanse | Crystal Counter | 18 | 30–54 |
| Riftlands | Wayfarer's Counter | 18 | 40–69 |
| Interdimensional Rift | Astral Counter | 18 | 50–81 |
| Omega Ruins | Last Light Counter | 18 | 55–99 |

Limits are capacities, not a promise of unavailable merchandise. Fresh recruits may see fewer listings. Existing item definitions remain intact: a late counter's tier range does not introduce new endgame gear. Accessories and supplies remain eligible up to the counter's upper tier so recovery and utility goods do not disappear later in the game.

Each region and Job keeps its own cached rotation. Returning before the restock deadline preserves it. Level changes and expired or malformed rotations are refreshed. The default restock is 30 minutes; Quartermaster upgrades retain their existing 3% reduction per tier. Guild construction changes prices immediately without rerolling stock.

## Guild commerce perks

- Emporium Annex: 10% off counter purchases everywhere. The discount applies identically to chat and Portal purchases, rounded down to whole Gil. Inventory resale values stay unchanged.
- Trading Post: the player market starts open in every region. Base service offers 6 active listings, a 2% posting fee and 5% completed-sale tax. Construction improves this to 10 listings, a 1% posting fee and 3% sale tax. Listings still last 48 hours. The minimum posting fee remains 1 Gil.
- Existing construction, contributions, trophies, inventories and Gil carry forward. Existing market listings above the new allowance remain active, can sell or be cancelled, and return normally when expired. New listings wait until the active count drops below the allowance.
- The Trading Post remains a single Guild-wide market. Regional storefront stock does not divide the player market.

## Portal

A regional landscape and counter name replace the old Annex stock panel. Guild perks fold into one disclosure, with accessible lock symbols for unbuilt benefits. Browse All, Weapons, Armor & Accessories or Supplies; search by name/description and sort by recommended stock, price or name. Cards retain item artwork, uses, equipment stat comparisons, quantity controls and current transaction totals. Guild prices show the original price beside the discounted amount. Travel, Job and level changes refresh the counter when the updated profile arrives; Check counter also refreshes it without forcing a reroll.

## Install

1. Stop the Bot and Web. Back up your live database and installation; preserve private configuration, tokens, persistent mounts and secrets.
2. Merge the patch's `Bot/` and `Web/` folders into the corresponding installed folders, or use the complete combined download. Both sides should be updated together.
3. The Bot automatically migrates schema 26 to 27 on startup, creating and verifying `pre_schema_27_<timestamp>.db` before adding regional shop caches. Historical personal shop rows remain untouched by migration. Hosted sync schema 1 and action protocol 39 remain unchanged.
4. Restart the services and refresh the Portal. The frontend is already built in `Web/frontend/dist`; no npm rebuild or dependency change is required. Source builds use the existing lockfile and `npm ci --include=dev` followed by `npm run build`.
5. Visit Moogle Emporium, travel to a different region, and check the counter. Completed Annex/Trading Post construction should display the new benefits immediately.
6. Optional: after the merge, review superseded frontend chunks using the included `cleanup_v1_9_6.py`. It checks current installation hashes before removing only audited, unchanged retired files. Never delete live databases or the automatic migration backup.

## Validation

The production build and 18 focused frontend checks pass. Bot regression coverage includes regional stock across all eight regions and every Job, sparse/corrupt cache repair, revisits, Job changes, expiry, discounted chat/Portal purchases, replay protection, market fees and limits, existing over-limit listings, migration preservation and resale/crafting economy checks. Production browser checks at 1280, 536, 390 and 320 pixels use an isolated actual Bot engine/database for purchases, stock reads and travel; there is no live account or deployment involved.

The broad engine suite has seven existing failures on this date (six seasonal encounter fixture lookups and one incomplete raid fixture); the untouched baseline reproduces the same seven. Historical release-specific version/schema assertions elsewhere are outside the focused validation. See `VALIDATION_MOOGLE_EMPORIUM_REWORK.json` for exact results.
