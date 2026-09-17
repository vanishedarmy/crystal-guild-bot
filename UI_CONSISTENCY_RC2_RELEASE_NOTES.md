# Crystal Guild v1.8.0 RC2 — UI Consistency

RC2 is a desktop/mobile presentation hardening pass built directly from the sealed v1.8.0 RC1 Complete baseline. It does not add or rebalance gameplay.

## Player-facing improvements

- Reworked the Adventurer Profile navigation into a deliberate responsive grid: 8 columns on wide desktop, 4 columns across compact desktop/tablet widths, and the existing compact selector on phones.
- Removed the awkward free-form tab wrapping that could leave Trophy Hall stranded on its own row.
- Added shared min-width and overflow guardrails so panels, grids, headings, badges, controls, and long player-facing copy cannot force the Portal wider than the viewport.
- Added shared artwork/media containment so authored images remain inside cards and figures without distorting surrounding layout.
- Tightened mobile selector spacing, touch height, panel gutters, and title-row behavior for a more consistent phone presentation.
- Preserved feature-specific visual identities and all existing Merc Service artwork.

## Compatibility

- Runtime/frontend: `1.8.0-merc-rc2`
- Local database schema: **17**
- Hosted sync schema: **1**
- Portal Action protocol: **34**
- No player reset or migration.
- Merc Service balance, Hero effects, Hunt Seal costs, and mission lifecycle are unchanged from RC1.
