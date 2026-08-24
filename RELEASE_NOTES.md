# Crystal Guild v1.1.16 — Arsenal Hotfix 4 Release Notes

Arsenal Hotfix 4 adds an authoritative streamer recovery path for adventure state that cannot be cleared from the player Portal.

## New streamer recovery command

### `!clearadventures`

Streamer-only emergency command. Alias: `!clearventures`.

The command atomically abandons all currently active non-raid adventure activity:

- the shared field / Rally Venture encounter, if one is active;
- every timed Hunt assignment currently waiting to resolve;
- every persisted Wayfarer Solo Venture row, including an orphaned/stuck Solo Venture that the Portal can no longer render.

The command operates directly against the authoritative Bot/runtime state and schema-5 `solo_expeditions` table. It therefore does not depend on an Adventure Board request succeeding first.

After a successful clear, the Bot wakes its in-process hosted Portal sync worker immediately when available so the cleared activity state is published without waiting for the normal sync interval.

## What the command intentionally preserves

`!clearadventures` is a recovery command, not a player reset. It leaves these untouched:

- player level, XP, JP, Gil and progression;
- inventory and equipment;
- the player's last successfully persisted HP / MP / AP state;
- achievements and Titles;
- Chocobo/Fellowship progression;
- Venture, Solo Venture, Daily and Hunt cooldowns;
- camp timers and personal shop rotations;
- active raids / world bosses and raid rosters.

Unbanked Solo Venture spoils and unresolved Hunt rewards are abandoned when those activities are cleared. If the streamer also wants to clear cooldowns afterward, `!resettimers` remains the separate explicit recovery tool.

## Streamer Dashboard

The Streamer Dashboard now lists `!clearadventures` under Player Recovery and explains its scope. The dashboard now documents 13 streamer-only commands.

## Compatibility

- Bot runtime: `1.1.16-arsenal-h4`
- Hosted Web runtime: `1.1.16-arsenal-h4`
- Frontend asset revision: `1.1.16-arsenal1h4`
- Local DB schema: **5** (unchanged)
- Hosted sync schema: **1** (unchanged)
- Hosted sync compatibility: `1.1.15-wayfarer` (unchanged)
- Portal Action protocol: **14** (unchanged)
- Twitch command prefix: `!`

No database migration, player reset, new Render secret, or new Twitch OAuth authorization is required.

This is a matching **Bot + Web** hotfix because the authoritative recovery command is implemented in the Bot and its streamer-facing command reference is updated on the Web dashboard.
