# Crystal Guild v1.2.0 — Expeditions Alpha 4

## Regional Discovery
Alpha 4 makes the five Expedition regions feel mechanically and narratively distinct without adding a new progression reset or database migration.

### Permanent landmarks
Each launch region now contains four named landmarks, for **20 total**. Landmarks are permanently charted from existing regional exploration progress and roll into the Expedition Atlas landmark count.

### Regional event identity
Resource, treasure, hazard, traveler, and Chocobo stages now use region-specific event pools. Across the five regions Alpha 4 adds **75 regional normal-event lines** while preserving the established reward/resource rules.

### Rare regional events
Each region gains three rare non-combat discoveries (**15 total**) that may award stronger treasure, materials, recovery, Chocobo Bond progress, or unusually strong survey progress. Base rare-event odds are approximately **2% Safe / 5% Unknown / 9% Push Deeper**, with relevant Chocobo traits and Region Mastery able to improve them modestly.

### Route identity
Safe, Unknown, and Push Deeper now expose risk, event tendencies, rare-event odds, and reward modifiers before the player commits. Push Deeper also increases the weighting of rare regional monster encounters once they are unlocked.

### Expedition Journal
The active Expedition Board now shows a compact saved Journal using the existing persistent run history. Recent combat, discoveries, camps, route events, and rare discoveries remain readable across Portal refreshes.

## Compatibility
- Bot runtime: `1.2.0-expeditions-a4`
- Hosted Web runtime: `1.2.0-expeditions-alpha4`
- Frontend asset revision: `1.2.0-expeditions-a4`
- Local DB schema: **8** (unchanged)
- Hosted sync schema: **1** (unchanged)
- Portal Action protocol: **20** (unchanged)
- Twitch prefix: `!`
- Player reset: **none**
- New environment variables: **none**
