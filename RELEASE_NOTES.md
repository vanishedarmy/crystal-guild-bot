**Includes Moogle Emporium Regional Rework.** Regional counters hold up to 12–18 listings; Guild construction now grants purchase discounts and market perks. Bot schema 27 adds regional caches with a verified migration backup. See `README_MOOGLE_EMPORIUM_REWORK.md`.

# Crystal Guild v1.9.6 — Triple Triad Expanded

Complete Bot + Web release based on the latest valid Seasonal Player Sync Fix Bot/Web packages and the completed Triple Triad rework. The abandoned Living World 1A/1B and site-wide Accessibility update are excluded. Apply Bot and Web together.

## Install or upgrade

1. Extract the ZIP once. It contains `Bot/` and `Web/` directly, alongside these instructions.
2. For an existing installation, stop the Bot and Web services and back up your current installation and live databases. Merge the corresponding complete folders into their existing locations, preserving your private configuration, environment variables, OAuth/session secrets, live databases, backups and persistent data mounts. No live data or configured secrets are bundled here.
3. If Bot and Web have separate hosting roots, use the contents of `Bot/` as the Bot deployment root and the contents of `Web/` as the Web deployment root. The Web Dockerfiles are inside `Web/`.
4. The frontend is already built in `Web/frontend/dist/`. **No npm rebuild is required to use it.** `Web/Dockerfile.prebuilt` uses the included output without npm; the normal `Web/Dockerfile` rebuilds source as part of its usual hosting flow. Development dependencies are defined in `package-lock.json`; `node_modules` is intentionally not bundled.
5. For a new installation, follow `Bot/FULL_SETUP_README.md`, `Bot/RENDER_CLOUD_SETUP.md`, `Bot/WEB_SYNC_SETUP.md` and `Web/HOSTING_GUIDE.md` for configuration. Historical feature guides describe their named releases; the current release identity is **v1.9.6 — Triple Triad Expanded**.
6. Restart matching Bot and Web and refresh the Portal. Verify the header and Overview What's New show v1.9.6, then open Gold Saucer → Triple Triad.
7. When merging into an older installation, old files can remain even though this ZIP excludes them. After verifying the update and closing/refreshing old Portal tabs, review them with `python cleanup_v1_9_6.py --root PATH_TO_INSTALL`; add `--apply` to remove only audited files whose hashes still match. For separate service roots, use `--bot-root BOT_PATH --web-root WEB_PATH`. A fresh extraction already contains no retired files.

Bot database schema 27 adds regional shop caches with a verified automatic migration backup. Hosted sync schema 1 and Portal Action protocol 39 remain unchanged. Your existing cards, valid decks, records, trophies and active matches remain compatible.

The full package includes release notes, a SHA-256 package inventory, validation results, the obsolete-file audit and the cleanup helper. It does not include local caches, npm-installed dependencies, generated source PNGs, earlier downloads or live state. All required card artwork is included in both the source and built static trees.

## Included

- 45 cards across five rarities: 15 Common, 10 Uncommon, 8 Rare, 7 Epic, 5 Legendary.
- All 30 new approved card illustrations, encoded as WebP at 1060 × 1484 without cropping or resizing. The original 15 cards and their side values are preserved byte-for-byte.
- Ten starter cards, five-card unique decks, ten opponents and five progression circuits with one-time MGP bonuses.
- Gentler novice opponents, visible hands, deterministic per-match responses, missing-card priority, duplicate quantities, and a guaranteed drop after three wins without a card at the same table.
- Play, Deck, Collection, Opponents and Rules sections; search, ownership/rarity filters, reward sources and opponent deck previews.
- Matching Bot, hosted Web and frontend release/cache labels, current package versions, release notes and Overview What's New.
- Existing valid collections, decks, records, trophies and active matches remain compatible. Bot database schema is 27; hosted sync schema stays 1 and Portal Action protocol stays 39. The regional cache migration preserves existing progression.
- Latest pre-expansion Retainer, Overview, Chocobo Stable, Seasonal Event and player-toggle synchronization fixes remain included in the baseline. Ordinary Git/repository source and runtime files are preserved.

## File audit

`CLEANUP_AUDIT_v1_9_6.json` lists each obsolete file, reason and expected SHA-256. Confirmed obsolete groups: the interim 30 SVG card faces; 15 older a5h5 faces (the card back remains); 54 v1 Relic weapon illustrations; six v2 scene backgrounds; old compiled frontend chunks; and the superseded v1.9.4.7 deployment note. Source and built static copies are covered where applicable.

Dynamic asset paths were checked before removal. Raid mechanic icons, monster/Boss portraits, Retainer and Merc service artwork, Chocobo race artwork, Gold Saucer result/opponent art, the card back and board, active Relic v2 artwork, and current Camp scenes remain. The historical changelogs, setup guides and relevant tests are retained; stale top-level release summaries and package inventories are refreshed. Test caches and build dependencies are excluded from the merge package. User databases, secrets, logs and backups are not cleanup targets.

The cleanup helper defaults to review-only and requires the exact v1.9.6 files to be installed before `--apply`. Fresh extractions are already clean. It refuses symlink escapes, verifies file hashes and skips locally modified files. Unknown files are never deleted. Savings reported by the audit are gross obsolete bytes, not the net size change after adding the new art.

## Validation

See `VALIDATION_v1_9_6.json` for the production build, targeted backend and hosted-Web checks, artwork/catalogue integrity, compiled import graph, cleanup-helper checks, desktop/mobile browser checks, and retained prior ladder simulations. Historical suites contain obsolete version/layout expectations; no claim is made that every historical assertion passes.

This complete package is ready to install; no live deployment has been performed.
