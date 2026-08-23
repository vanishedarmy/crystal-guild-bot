# Crystal Guild v1.1.14 — Cloud Continuity Hotfix 3c

Hotfix 3c moves forward from the certified Hotfix 3b baseline and combines one equipment-clarity update, one economy/achievement correctness fix, and one mobile navigation correction.

## Equipment & Inventory — current loadout clarity

- Adds a dedicated **Current Loadout** summary at the top of Equipment & Inventory.
- Weapon, Armor, and Accessory are visible together with the effective stat bonuses currently applied.
- Empty slots are explicit instead of visually disappearing.
- Equipped items are sorted to the top of their equipment group.
- Equipped inventory cards receive a stronger highlight and an **Equipped now** marker.
- Existing replacement comparison, eligibility checks, equip/unequip actions, recovery controls, and item details are preserved.

## “Stimulating the Economy” — Gil-spent correction

- The `gil_spent` achievement metric now reads the authoritative lifetime transaction ledger, matching the Records page.
- Existing historical spending is therefore recognized without a migration or manual player-data repair.
- Shop purchases now run the achievement check immediately after a successful purchase.
- Chocobo Registration Writ purchases and Fellowship Gil contributions also check achievements immediately.
- Crafting, forging, Relic costs, and other transaction-backed sinks continue to count through the same ledger.

## Mobile Portal header

- At widths up to 720px, downward scrolling automatically tucks the sticky Portal header away.
- Scrolling upward restores the header immediately.
- Near the top of the page, the header is always shown.
- Keyboard focus inside the header forces it visible so navigation cannot become inaccessible.
- Reduced-motion users get the same behavior without the transition animation.

## Compatibility

- Bot/Web runtime: `1.1.14-cloud-continuity-h3c`
- Frontend asset revision: `1.1.14-continuity3c`
- Local DB schema: **4**
- Hosted sync schema: **1**
- Hosted sync compatibility: `1.1.14-cloud-continuity`
- Portal Action protocol: **12**
- Twitch prefix: `!`

No database migration, player reset, new Render secret, new OAuth scope, hosted sync schema change, or Portal protocol change is required. The `channel:read:subscriptions` broadcaster authorization remains the inherited Hotfix 2 requirement for subscriber perks.
