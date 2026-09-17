# Crystal Guild v1.8.0 RC3 — Portal UI Polish

RC3 refines the RC2 visual consistency pass after desktop review. Gameplay is unchanged; this build focuses on readable navigation, cleaner manual refresh behavior, and consistent live-page controls.

## Player-facing improvements

- Reworked Adventurer Profile navigation so normal desktop widths use a roomier 6-column grid instead of forcing 8 narrow buttons across.
- Very wide screens (1600px+) retain the 8-column two-row layout; 901–1279px uses 4 columns; 721–900px uses 2 columns; phones keep the compact section selector.
- Kept navigation labels on one line and inside their buttons without ellipsis/truncation.
- Centered the 4-button final row at common desktop widths so the navigation feels deliberate instead of left-heavy.
- Removed section-specific manual refresh buttons from Adventure Board, Jobs, Inventory/Recovery, Moogle Emporium, Blacksmith, Chocobo Stable, Retainer Service, Hero Merc Service, Gold Saucer, Fellowship, and Daily Reward surfaces.
- Added one shared **Refresh** control at the bottom of live Portal pages: Guild Heroes, Adventurer Profile, Fellowship, and Streamer Dashboard.
- Kept automatic SSE/live updates, focus refreshes, post-action synchronization, and feature state reloads intact.
- Simplified the signed-in Crystal Guild connection strip to passive ONLINE/OFFLINE status only.

## Compatibility

- Runtime/frontend: `1.8.0-merc-rc3`
- Local database schema: **17**
- Hosted sync schema: **1**
- Portal Action protocol: **34**
- No player reset or migration.
- Merc Service pricing, Hero effects, Hunt Seal economy, and deployment lifecycle are unchanged from RC2.
