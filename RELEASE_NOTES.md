# Crystal Guild v1.1.16 — Arsenal Hotfix 1 Release Notes

Arsenal Hotfix 1 rebuilds Hunts as long-form, autonomous assignments instead of Twitch round battles, and applies a readability/accessibility polish pass across the hosted website.

## Timed autonomous Hunts

Starting a Hunt now dispatches that player's hero on a **personal persisted assignment**. The Hunt no longer occupies the shared Active Battle slot and no round-by-round Twitch combat input is required.

Hunt return timers are fixed by rank:

- **C Rank — 5 minutes**
- **B Rank — 15 minutes**
- **A Rank — 30 minutes**
- **S Rank — 1 hour**
- **S+ Rank — 2 hours**

The Hunt timer begins when the mark is accepted. When the deadline arrives, the combat daemon resolves the Hunt independently of chat activity. If the Bot was temporarily offline when the deadline passed, the persisted assignment is recovered and resolved after the runtime returns. Only the resulting Hunt outcome is announced; individual simulated combat rounds are not replayed into Twitch chat.

Several players may have timed Hunts in progress at once, and those assignments do not prevent the Guild's shared Rally Venture or Raid battle state from operating independently.

## Conservative automatic combat

The hunter's combat build and resources are snapshotted when the assignment begins. At resolution Crystal Guild uses the normal combat engine internally, but chooses actions automatically with a survival-first policy:

- learned abilities are used when their damage, elemental advantage, healing, cleansing, control, resource recovery, or defensive value is worthwhile;
- **Defend** may be chosen when conserving resources or surviving incoming pressure is preferable;
- healing and cleansing items are reserved for meaningful danger rather than used merely because they are available;
- expensive emergency items are avoided under normal circumstances;
- MP/AP recovery is reserved for low-resource situations where continued ability use is useful.

Consumable use has a hard per-Hunt ceiling so automatic resolution cannot drain a player's inventory:

- **C / B — at most 1 item**
- **A / S — at most 2 items**
- **S+ — at most 3 items**

The hero remains committed to the assignment until it returns, so recovery/build/resupply actions that would invalidate the accepted combat snapshot are blocked while that Hunt is active.

## Hunt Portal experience

The Adventure Board now treats Hunts as timed assignments rather than live Twitch combat. An active Hunt shows:

- mark and monster;
- Hunt rank;
- expected return countdown;
- assignment length;
- progress indicator;
- autonomous-Hunt status and a plain-language explanation of automatic ability/Defend/item use.

Hunt cards also display their rank duration before dispatch. The page uses local countdown rendering with periodic authoritative refresh rather than requiring constant second-by-second API polling.

Any pre-Hotfix-1 Hunt that was already stored as a legacy Active Battle remains compatible and can finish under the old checkpoint model. Newly accepted Hunts always use the timed autonomous system.

## Website readability and graphical polish

A broad presentation pass covers the **Adventurer Portal, Streamer Dashboard, and Player Guide**:

- stronger secondary-text contrast;
- more consistent body and metadata line heights;
- larger minimum sizes for overly small labels and table metadata;
- reduced excessive letter spacing where it hurt readability;
- safer wrapping for long names, descriptions, commands, and card metadata;
- `min-width: 0` protection in dense grid/card layouts to prevent overflow artifacts;
- clearer keyboard focus outlines;
- tabular numerals for timers and resource values where useful;
- larger mobile action targets and improved narrow-screen spacing;
- dedicated Hunt-progress styling that collapses cleanly on phones.

The pass intentionally preserves the established Crystal Guild visual identity and layout hierarchy rather than redesigning the site.

## Compatibility

- Bot/runtime: `1.1.16-arsenal-h1`
- Frontend asset revision: `1.1.16-arsenal1h1`
- Local DB schema: **5** (unchanged)
- Hosted sync schema: **1** (unchanged)
- Hosted sync compatibility: `1.1.15-wayfarer` (unchanged)
- Portal Action protocol: **14** (unchanged)
- Twitch command prefix: `!`

This is a matching **Bot + Web** update because Hunt runtime behavior and the player-facing Hunt UI both change. It requires **no database migration, player reset, new Render secret, or new Twitch OAuth scope**.
