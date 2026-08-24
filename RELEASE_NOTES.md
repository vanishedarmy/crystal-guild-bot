# Crystal Guild v1.1.17 — Arsenal II Hotfix 4 Release Notes

Hotfix 4 is a paired Bot + Web balance and presentation update focused on the Adventure Board.

## Solo Venture balance

- Solo Venture stage odds change from **60% Encounter / 40% Treasure** to **80% Encounter / 20% Treasure**.
- The lower chest rate applies independently at every stage. A full three-stage run now has a **48.8%** chance of seeing at least one chest instead of **78.4%**.
- Deeper stages still improve chest quality when a chest does appear; the Stage II/III reward multipliers and risk/banking rules are unchanged.
- The Adventure Board and Player Guide now read the published odds from the same authoritative gameplay state/reference values.

## Hunt result presentation

- Finished Hunts now publish a structured result summary to the Portal instead of relying on chat-style resolution lines.
- Victory results separate XP, JP, Gil, and Hunt Seals into readable reward blocks and surface loot, first-clear rewards, level-ups, achievements, post-Hunt condition, combat totals, and the automatic action plan when available.
- Failed Hunts show the mark's remaining HP, the hero's post-Hunt condition, combat totals, and failure reason.
- Legacy Hunt results still have a compact fallback presentation.

## Lower visual noise

- Repeated Solo Venture result copy is removed; the detailed result card is now the single source of the last Solo Venture outcome.
- Region selection no longer repeats the current region description above the same region card. The section is simply **Regions** with the current region identified in the header.
- Rally Venture explanatory copy is condensed where the same reward rules were already displayed immediately above it.
- Shared Portal action-status blocks use a more compact horizontal presentation on wider screens while remaining stacked on mobile.

## Accessibility

- Secondary text contrast is increased.
- Disabled controls remain visibly disabled without fading important labels excessively.
- Hunt outcomes use explicit text labels in addition to color.
- Hunt reward/combat data reflows to two columns on smaller screens and one-column detail rows on narrow phones.
- High-contrast preferences receive stronger borders and secondary-text contrast.

## Compatibility

- Bot runtime: `1.1.17-arsenal-ii-h4`
- Hosted Web runtime: `1.1.17-arsenal-ii-h4`
- Frontend asset revision: `1.1.17-arsenal-ii1h4`
- Local DB schema: **5** unchanged
- Hosted sync schema: **1** unchanged
- Portal Action protocol: **14** unchanged
- Twitch command prefix: `!` unchanged

No database migration, player reset, OAuth change, or new environment variable is required.
