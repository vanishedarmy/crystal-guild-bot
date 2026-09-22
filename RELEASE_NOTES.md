# Crystal Guild v1.9.0 Alpha 8 — Seasonal Event Framework

Alpha 8 builds one reusable seasonal/event rotation system and ships **Night of the Hollow Crystal** as the first event edition. Seasonal content is a layer over existing Ventures, Hunts, World Events, rewards, profiles, and the Hall rather than a second combat system.

## Reusable seasonal framework
- Persistent event editions with **manual**, **scheduled**, **paused**, **redemption**, and archived/disabled presentation states.
- Event definitions carry their own monster variants, World Event additions, objectives, currency, shop catalog, artwork, and permanent event trophies.
- The Halloween 2026 edition is installed **disabled by default**; deployment alone never starts seasonal content.
- Streamer Control Center can enable/disable, pause/resume, switch manual/scheduled operation, and inspect current event status.

## Night of the Hollow Crystal
- Four FF-styled seasonal monster variants: **Jack-o’-Bomb, Graveyard Coeurl, Lantern Tonberry, and Wraith Ahriman**.
- Eligible seasonal variants supplement ordinary encounters at a controlled replacement rate and use the existing encounter engine.
- **The Hollow Warden** joins the normal World Event selection while Halloween is active, without increasing the overall World Event spawn rate.
- Seasonal monster kills, eligible Ventures/Hunts, and the Warden feed rotating daily personal/Guild objectives.
- **Moonlit Tokens** fund the temporary **Moonlit Emporium**. Ordinary monster token rewards are daily-capped, while objective claims and first-clear Warden credit are replay-safe.

## Rewards and permanent collection
- **Spooky Supply Cache** — repeatable ordinary supplies.
- **Nightwatcher** — permanent character Title.
- **Haunted Candle** — permanent seasonal keepsake.
- **Hollow Crystal Display** — permanent seasonal display collectible.
- Four permanent seasonal trophies: **A Light in the Dark, Things That Go Bump, The Warden’s Seal, and Keeper of the Hollow**.
- Seasonal trophies do not alter the original Hall of Trophies 30/30 Phase-1 completion contract.

## Persistence and compatibility
- Local schema: **21**, automatic migration from schema 20 with verified `pre_schema_21_<timestamp>.db` backup.
- Hosted sync schema: **1**.
- Portal Action protocol: **37**.
- No player reset, normal economy rebalance, ordinary combat/reward rebalance, or Gold Saucer rebalance.

## Package cleanup Hotfix 1 (same Alpha 8 runtime)
- Consolidated prior release/hotfix reports into `CHANGELOG.md`.
- Removed superseded Triple Triad `a5h3` and `a5h4` asset trees; current `a5h5` routes are unchanged.
- Removed byte-identical legacy Hunt/Raid background aliases and updated the scene manifest to the existing live `h4` routes.
- Updated stale root README and deployment guides to schema 21/protocol 37.
- Preserved all migrations, gameplay assets, runtime code and permanent player data. No economy, combat or event changes.
