# Crystal Guild v1.8.1 — Live Stream Controls Hotfix 3

Hotfix 3 turns the signed-in Portal into a visual controller for active Stream Ventures and Trials/Raids while keeping Twitch chat commands fully supported.

## Live Stream Portal controls

- A Stream Venture opened in Twitch chat now appears on **Stream Activities** with a Portal **Join Stream Venture** action for eligible signed-in players.
- Raid rally state exposes the same Portal join path for eligible players.
- Once a joined player reaches live combat, the Portal renders their current HP and MP/AP plus **Attack**, **Defend**, unlocked **Abilities**, and owned battle **Consumables**.
- Ability controls are grouped into **Offense**, **Restoration**, and **Support** for faster scanning.
- Consumables are grouped into **Healing**, **Support**, and **Damage**, with item artwork and owned quantities visible before use.
- Ally targeting is available for support, recovery, and revive actions. KO state is shown when selecting revive targets.
- Queuing another action in the same round replaces the previous queued action, matching existing timed Twitch battle behavior.
- Portal actions execute through the same authoritative Venture/Raid combat engine as Twitch commands; no duplicate combat rules are maintained in the frontend.
- Successful Portal joins/actions are announced back into live Twitch chat by Crystal Guild after the hosted action has been acknowledged.
- Stale event/round protection rejects outdated Portal clicks after the live battle advances.
- When the stream is offline, live join/combat controls are not exposed.
- During a live stream the Stream Activities state uses a short fallback refresh interval in addition to existing live revision/focus updates, so chat-started rallies become visible promptly.

## Mobile recovery inventory

- Usable recovery items now render as a compact **two-column grid on phones**.
- Item artwork, effect copy, and Owned/Use metadata are tightened without removing information.

## Compatibility

- Runtime/frontend remains `1.8.1-merc-recruitment`.
- Local database schema remains **18**.
- Hosted sync schema remains **1**.
- Portal Action protocol remains **35**.
- No player reset or migration.
- No Venture/Raid balance, reward, combat-math, or item-effect changes.
- Includes Dungeon Portrait Hotfix 1 and Mobile Context Help Hotfix 2.
- **Deploy the Web and Bot portions together** to enable Portal live-event controls.
