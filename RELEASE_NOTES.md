# Crystal Guild v1.9.0 Alpha 6 — World Events

Alpha 6 adds spontaneous **World Events** to live streams: powerful Notorious Monster variants can appear while Twitch is live, open a short public rally, and resolve through the existing Active Battle engine without starting a Raid.

## World Event encounters
- The autonomous combat director watches for World Events only while the configured Twitch stream is live.
- A new stream begins with a **15-minute grace period** before the first roll. Afterward, eligible checks occur every **8–12 minutes** with a **25% spawn chance**.
- After a World Event ends or passes unanswered, another cannot appear for **30–45 minutes**.
- Only one Guild-wide encounter can be active at once. Existing Ventures, World Events, or Raids block a new World Event from spawning.
- World Event rallies remain open for **90 seconds** and can be joined from Twitch chat or Stream Activities.
- World Events never create, consume, or transform into a Raid.

## Scaling and rewards
- Every World Event starts from the Guild's **highest current character level**.
- Each monster has its own danger band between **+3 and +10**, with a hard maximum of **highest character +10**.
- World Event levels are not artificially capped at 99; a level-99 Guild can encounter threats up to level 109.
- Enhanced HP, combat stats, and XP/JP/Gil rewards keep the encounters more dangerous and more rewarding than their familiar base monsters while remaining below Raid-scale reward pools.
- World Events do not consume the normal Venture cooldown or increment a player's Venture count.

## Opening roster
The first ten Notorious Monster variants are:
- Notorious Behemoth
- Tainted Malboro
- Dark Iron Giant
- Elder Adamantoise
- Cursed Tonberry King
- Savage Coeurl
- Dread Bomb King
- Twisted Ahriman
- Ravenous Dragon
- Bloodied Deathclaw

## Stream Activities Portal
- Stream Activities now has a dedicated **World Events** area.
- The Portal includes all ten boss portraits plus World Event header, active, idle, and defeated-state artwork.
- Active events show the variant portrait, threat label, level, HP, rally timer/round, party state, and authenticated battle controls.
- The roster is responsive from five columns on wide desktop down to compact single-row cards on narrow mobile screens.
- High-frequency Adventure State snapshots keep the long-standing **16 KiB payload ceiling** by shipping only live authoritative World Event state; the matching Web build carries the versioned display catalog.

## Reliability hardening
- Fixed the autonomous World Event scan so it runs on the combat director rather than the outbound notification dispatcher.
- Hosted Portal validation, Portal action relay, and Bot worker now all accept `world_event` for live join/action requests.
- Twitch `!encounter` / battle-log presentation uses the World Event variant identity and a safe `The Realm` location label.
- Unanswered rallies close without creating a Raid and safely enter the normal post-event cooldown.

## Compatibility
- Runtime/frontend: `1.9.0-world-events-alpha6`
- Local schema: **19**
- Hosted sync schema: **1**
- Portal Action protocol: **36**
- No database migration or player reset is required.
- Alpha 2 economy balance, Alpha 3 Title Expansion, Alpha 4 Navigation Accessibility, and Alpha 5 Title Status Hardening remain unchanged.
