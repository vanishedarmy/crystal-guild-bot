# Crystal Guild v1.2.0 — Expeditions

Crystal Guild v1.2.0 ships the full Expeditions system and promotes the RC1 feature set unchanged into the final release.

## Expeditions
- Five launch regions: Emerald Wilds, Ashen Highlands, Mistfen Marshes, Frostveil Reach, and the Astral Scar.
- Scout, Journey, Deep Expedition, Regional Boss Contract, and Legendary Contract routes.
- Safe / Unknown / Push Deeper route choices with distinct survival-versus-reward pressure.
- Persistent HP, MP, AP, inventory use, Expedition Cache, Journal, route state, and return/rescue behavior.
- Regional exploration milestones, permanent landmarks, Regional Bosses, Mastery rewards, Expedition Atlas ranks, and Master Cartographer progression.
- Region-specific encounters, hazards, resources, travelers, rare events, and discoveries.

## Chocobo expedition partnership
- Guardian, Scout, Pathfinder, Forager, and Treasure Hunter specialties derive from existing Chocobo traits.
- Specialty effects scale with Bond milestones.
- The Stable records shared Expedition accomplishments.
- Completed routes award restrained Hunt Seal stipends while Hunts remain the primary Hunt Seal activity.

## Player experience
- Adventure Board information is action-first and secondary progression can collapse.
- Detail cards open in the current viewport without moving the background page.
- Portrait-format scenic artwork fills long Solo Venture, Relics, Blacksmith, Chocobo Stable, and Moogle Emporium tabs.
- Mobile layouts, touch targets, keyboard navigation, focus handling, contrast support, reduced-motion support, and device safe areas have been polished.
- The Player Guide Expeditions chapter contains play and usage information only; development and release-engineering history is kept out of player instructions.

## Release hardening
- Persistent Solo/Expedition mutations and replay receipts commit atomically to prevent duplicate rewards after retries.
- Active persistent Adventures block Long Rest and stream-start resource refreshes until the run ends.
- Active Expeditions survive restart/reconnect and schema-7 → schema-8 migration preserves existing player progression.

## Compatibility
- Bot runtime: `1.2.0-expeditions`
- Hosted Web runtime: `1.2.0-expeditions`
- Frontend asset revision: `1.2.0-expeditions`
- Local DB schema: **8**
- Hosted sync schema: **1**
- Portal Action protocol: **20**
- Twitch prefix: `!`
- Player reset: **none**
- New environment variables: **none**
