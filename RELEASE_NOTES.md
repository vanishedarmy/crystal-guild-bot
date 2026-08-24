# Crystal Guild v1.1.17 — Arsenal II Release Notes

**Upgrade baseline:** v1.1.16 — Arsenal Hotfix 6

Arsenal II is a paired Bot + Web feature release focused on deeper Job combat progression and a cleaner day-to-day Portal experience.

## Ability Tree Expansion

- Active Battle abilities increase from **108 to 172** across the 18 Jobs.
- Core caster Jobs — **Black Mage, White Mage, Red Mage, Summoner, Blue Mage, Time Mage, and Sage** — now use a **12-step JLv ability curve** at JLv. **1 / 5 / 8 / 12 / 15 / 18 / 22 / 26 / 30 / 35 / 40 / 45**.
- Every other Job now has **8 active abilities**, adding new JLv.12 and JLv.35 techniques without moving the abilities players already learned.
- New spells and techniques continue to use the existing single-target combat model; Arsenal II does **not** introduce multi-target enemy selection.
- Elemental and status identity is expanded through Fire, Ice, Lightning, Wind, Water, Holy, Dark, healing, cleansing, protection, regeneration, resource recovery, Poison, Slow, Stun, Blind, Weaken, Vulnerable, Focus, and other existing combat effects.
- Representative additions include **Water, Fira, Blizzara, Thundara, Bio, Ultima, Dia, Cure II, Regen, Banish, Benediction, Veraero, Verholy, Verflare, Leviathan's Favor, Garuda's Favor, Bahamut's Favor, White Wind, Glower, Meteor, Diagnosis, Toxikon, and Taurochole**.
- Player Guide / Job Details / Solo Venture ability data are kept on the same shared catalog.

## Moogle Emporium

The Emporium has been reorganized into first-class transaction views:

- **Buy** / **Sell**
- **Weapons** / **Armor** / **Items** inside either transaction mode

Accessories remain grouped with Armor for shopping purposes. Existing stat comparisons, ownership, price checks, quantities, and authoritative transaction validation remain unchanged.

## Blacksmith

- **Recipes** and **Forge Gear** are now presented as a stronger segmented view switch.
- The active section is explicitly identified in both text and styling.
- Recipe and forge cards retain their existing requirements and authoritative cost validation.

## Adventure Board Camp

- Camp & Recovery is now available directly from the **Adventure Board**.
- The panel shows current HP and applicable MP/AP, normal Camp duration, current resting state, and any reason Camp cannot start.
- `Set Up Camp` uses the existing authoritative `START_REST` Portal action; no second recovery system was created.
- Existing Camp restrictions and Fellowship Camp-duration bonuses remain authoritative.

## Mobile / Site UI & UX

- The mobile Portal masthead is substantially more compact while retaining its existing **scroll down to hide / scroll up to return** behavior.
- Brand artwork, navigation, auth controls, build information, and LIVE/OFFLINE status use a denser layout on small screens.
- General card hierarchy, secondary text contrast, wrapping, spacing, and narrow-screen layouts received an additional readability pass.

## Streamer Dashboard

- **Hosted Raid Overlay** setup has been moved to the bottom of the Streamer Dashboard as ordinary reference material.
- It is no longer part of the top/fixed operational reference area.

## Off-Stream Twitch Stopgate

Portal gameplay remains available while the Twitch channel is offline, but **autonomous Crystal Guild chat announcements are now gated by Twitch live status**.

- When Twitch is confirmed **LIVE**, autonomous Portal / timed activity announcements are delivered normally.
- When Twitch is **OFFLINE** or live status cannot be verified, autonomous announcements are suppressed rather than posted into chat.
- Normal Twitch commands that already require the stream to be live continue to reject the action with their existing player-facing offline message.
- Gameplay state and Portal action results are still processed normally; only automated Twitch-chat delivery is suppressed.

## Compatibility

- Bot runtime: `1.1.17-arsenal-ii`
- Hosted Web runtime: `1.1.17-arsenal-ii`
- Frontend asset revision: `1.1.17-arsenal-ii1`
- Local DB schema: **5** (unchanged)
- Hosted sync schema: **1** (unchanged)
- Portal Action protocol: **14** (unchanged)
- Twitch command prefix: `!` (unchanged)

There is **no database migration, player reset, new OAuth scope, or new environment variable** in this release.
