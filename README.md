# Crystal Guild v1.1.14 — Cloud Continuity Hotfix 2

Hotfix 2 keeps the v1.1.14 cloud runtime and adds two player-facing improvements:

1. **Randomized Daily Guild Provisions** — Daily is no longer permanently `1 Potion + Gil`; it rolls level-appropriate consumables/basic crafting supplies plus Gil.
2. **Twitch subscriber tiers** — Crystal Guild can verify Tier 1/2/3 from the broadcaster-authoritative Twitch subscription list and use that tier for perks.

Current subscriber perks are deliberately limited to Daily Guild Provisions:

- Tier 1: +10% Daily Gil, 2 provision rolls.
- Tier 2: +20% Daily Gil, 3 provision rolls.
- Tier 3: +30% Daily Gil, 4 provision rolls.

Use `!substatus` to check the detected tier.

Existing cloud installations must re-authorize the broadcaster once with `channel:read:subscriptions` and replace the private `/var/data/twitch_tokens.db`. See `UPGRADE_GUIDE.md`.

Runtime `1.1.14-cloud-continuity-h2` · DB schema 4 · hosted sync schema 1 · Portal Action protocol 12 · Twitch prefix `!`.
