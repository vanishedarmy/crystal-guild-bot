# Crystal Guild — Halloween 2026 Seasonal Event Live Hotfix

**Event:** Night of the Hollow Crystal  
**Target:** Current Crystal Guild 1.9.4 Bot baseline  
**Web rebuild:** Not required

## Changes

- Night of the Hollow Crystal is now configured as the live **scheduled** seasonal edition.
- Live window: **October 1, 2026 00:00 UTC through November 2, 2026 23:59:59 UTC**.
- Moonlit Emporium redemption remains available through **November 5, 2026 23:59:59 UTC** after the combat/event window closes.
- Existing databases that still contain the original disabled/manual Halloween row are promoted **once** to the live scheduled configuration. A config revision marker prevents later owner `off`, `pause`, `manual`, or other control choices from being silently overwritten after the migration has run.
- Off-stream / Solo Venture seasonal replacement chance increases from **25% to 35% of eligible combat encounters**.
- Stream / Rally Venture seasonal replacement chance increases from **30% to 40%** so the live mode retains its existing modest five-point advantage.
- Solo Venture's independent **80% Encounter / 20% Treasure** stage branch is unchanged. With an eligible seasonal pool, the new seasonal replacement rate therefore corresponds to roughly **28% of all Solo Venture stages** before level gating (`80% × 35%`).
- Level gating, Moonlit Token rewards/caps, daily objectives, trophies, the Hollow Warden rules, and all non-seasonal encounter balance are unchanged.

## Deployment

### Merge package
Extract the merge ZIP at the Crystal Guild project root, alongside the existing `Bot/` and `Web/` folders. Allow the included Bot files to overwrite their matching paths.

### Full Bot package
The full deploy ZIP is a complete current Bot root. Use it only when replacing/deploying the Bot service itself.

After either method, **restart the Bot / Portal Action worker**. No npm/Vite rebuild and no Web service restart are required.

## Validation

- Seasonal configuration/event migration tests pass.
- Seasonal Solo/Stream Venture tests pass with the new 35% / 40% rates.
- Generic World Event tests explicitly isolate the normal World Event catalog from the now-live seasonal director and pass.
- **23/23 focused seasonal + world-event tests pass.**
- A broader 124-test gameplay/action run had **122 passes**. The only two failures are pre-existing Merc release-contract assertions that still expect the older `1.9.3-guild-initiatives` version string while the current source correctly reports `1.9.4-crafting-reforged`; they are unrelated to this hotfix.
- Modified Python files compile successfully.

## Files changed

- `Bot/crystal_guild/seasonal_events.py`
- `Bot/tests/test_seasonal_events_alpha8.py`
- `Bot/tests/test_seasonal_venture_1946.py`
- `Bot/tests/test_world_events_alpha6.py`

No database schema or Portal protocol migration is introduced.
