# Crystal Guild v1.1.14 — Cloud Continuity Hotfix 2

## Daily Guild Provisions — randomized supply bundles

`!daily` and the signed-in Portal Daily Guild Provisions action still share one authoritative 24-hour cooldown, but the fixed `Gil + 1 Potion` reward is retired.

Each successful claim now grants:

- level-scaled Gil;
- at least one randomized, level-appropriate provision roll;
- practical shop consumables available at the hero's level and/or bounded common/uncommon crafting materials;
- inventory + transaction writes for every rolled provision so economy/accounting data remains authoritative.

Rare raid/relic/artifact materials are intentionally excluded from the Daily material pool. Higher-level heroes naturally unlock stronger normal consumables because the Daily pool respects each item's shop level.

## Twitch subscriber tiers + first perks

Crystal Guild now checks the broadcaster's Twitch subscriber list by Twitch user ID and normalizes Twitch tiers `1000`, `2000`, and `3000` to Tier 1, 2, and 3.

Initial subscriber perks apply to **Daily Guild Provisions only**:

| Status | Daily Gil | Provision rolls |
| --- | ---: | ---: |
| Standard / non-sub | 100% | 1 |
| Tier 1 | 110% | 2 |
| Tier 2 | 120% | 3 |
| Tier 3 | 130% | 4 |

Gift subscriptions count at their current Twitch tier. The subscriber service is deliberately reusable by future systems, but Hotfix 2 does not silently alter Venture/Hunt/Raid combat rewards.

`!substatus` lets a viewer check the tier Crystal Guild currently sees and the associated Daily perk.

The Bot caches successful subscriber checks for five minutes per user and can reuse a recent confirmed result for up to fifteen minutes during a temporary Twitch API failure. If verification becomes unavailable beyond that stale window, gameplay continues normally with the standard Daily reward rather than blocking the player.

## Twitch authorization change

Subscriber lookup uses Twitch `GET /helix/subscriptions` with the broadcaster's managed user access token. The broadcaster token must include:

`channel:read:subscriptions`

Existing Bot/chat scopes remain in place. No new Render environment variable is required, but an existing cloud installation must re-authorize the broadcaster once and replace `/var/data/twitch_tokens.db` with the refreshed private token database.

## Compatibility

- Bot runtime: `1.1.14-cloud-continuity-h2`
- Hosted sync version/snapshots: `1.1.14-cloud-continuity`
- Matching Web asset revision: `1.1.14-continuity2`
- Local DB schema: 4
- Hosted sync schema: 1
- Portal Action protocol: 12
- Twitch prefix: `!`
- Database migration: none
- Player reset: none
- New Render secrets: none
- Twitch broadcaster reauthorization: **required once for subscriber perks**
